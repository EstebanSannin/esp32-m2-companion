"""Grid-search routing feasibility probe (repo method: "one-net feasibility
probe", docs/routing-method.md §5), extended to all new v2 nets.

Input : probe_<L>L.kicad_pcb from `probe.py --layers L --no-route`
        (rev-B copper locked, new parts placed, power vias in place,
        outer pours stripped, inner planes kept).
Output: probe_<L>L_grid.kicad_pcb with the found tracks/vias + outer GND
        pours, then judged by **KiCad DRC** (not by this router).

Rules (JLC standard, CLAUDE.md): track 0.127 mm, clearance 0.127 mm,
via 0.45/0.3 mm, copper-to-edge 0.3 mm. Signal layers: 4L = F/B,
6L = F/In3/In4/B (In1 GND / In2 +3V3 stay planes; vias pass them).
Sequential, no rip-up: pessimistic. A net that routes here routes for real.

  $KPY v2/probe/gridprobe.py --layers 4|6
"""

import heapq
import math
import re
import sys
from array import array
from pathlib import Path

import pcbnew

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "hardware" / "tools"))

LAYERS = int(sys.argv[sys.argv.index("--layers") + 1]) if "--layers" in sys.argv else 4
SRC = HERE / f"probe_{LAYERS}L.kicad_pcb"
OUT = HERE / f"probe_{LAYERS}L_grid.kicad_pcb"

G = 0.05                      # grid pitch, mm
X0, Y0, X1, Y1 = 88.9, 107.9, 111.1, 150.1
NX, NY = int((X1 - X0) / G) + 1, int((Y1 - Y0) / G) + 1
TW, CLR = 0.127, 0.127
VD, VDR = 0.45, 0.3
EDGE = 0.3
SAFE = 0.02
INF_T = CLR + TW / 2 + SAFE                 # foreign copper edge -> my centerline
INF_V = max(VD / 2 + CLR, VDR / 2 + 0.25) + SAFE  # (hole clearance included)  # foreign copper edge -> my via centre
VIA_COST = 16
HOLE_CLR, HOLE_HOLE = 0.25, 0.25          # .kicad_pro min_hole_clearance / min_hole_to_hole
VIA_KEEP_T = max(VD / 2 + CLR, VDR / 2 + HOLE_CLR) + TW / 2 + SAFE  # via centre -> track centreline
VIA_KEEP_V = max(VD + CLR, VDR + HOLE_HOLE, VD / 2 + VDR / 2 + HOLE_CLR) + SAFE  # via centre -> via centre
BLOCK = 0xFFFF
DEBUG = set(sys.argv[sys.argv.index('--debug') + 1].split(',')) if '--debug' in sys.argv else set()

ROUTE_RE = re.compile(r"^(EXP_\d+(_MCU|_EDGE)?|EXP_OE|CONFIG_[23]_SENSE|CFG[23]_G|LED_1_n|"
                      r"WAKE_ON_WWAN_n|W_DISABLE2_n|IO42|IO47|IO1)$")

T = pcbnew.ToMM
mm = pcbnew.FromMM


def idx(ix, iy):
    return iy * NX + ix


def cell_xy(ix, iy):
    return X0 + ix * G, Y0 + iy * G


class Grid:
    def __init__(self, nlayers):
        self.t = [array("H", [0]) * (NX * NY) for _ in range(nlayers)]
        self.v = array("H", [0]) * (NX * NY)

    @staticmethod
    def mark(arr, i, owner):
        cur = arr[i]
        if cur == 0:
            arr[i] = owner
        elif cur != owner:
            arr[i] = BLOCK


def raster(arrs, owner, dist_fn, bbox, r):
    """mark every cell whose centre has dist_fn(x, y) <= r"""
    x1, y1, x2, y2 = bbox
    ix1 = max(0, int((x1 - r - X0) / G)); ix2 = min(NX - 1, int((x2 + r - X0) / G) + 1)
    iy1 = max(0, int((y1 - r - Y0) / G)); iy2 = min(NY - 1, int((y2 + r - Y0) / G) + 1)
    for iy in range(iy1, iy2 + 1):
        y = Y0 + iy * G
        base = iy * NX
        for ix in range(ix1, ix2 + 1):
            if dist_fn(X0 + ix * G, y) <= r:
                for a in arrs:
                    Grid.mark(a, base + ix, owner)


def seg_dist(a, b):
    (ax, ay), (bx, by) = a, b
    dx, dy = bx - ax, by - ay
    L = dx * dx + dy * dy

    def f(x, y):
        u = 0.0 if L == 0 else max(0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / L))
        return math.hypot(x - (ax + u * dx), y - (ay + u * dy))
    return f


def box_dist(bx):
    x1, y1, x2, y2 = bx

    def f(x, y):
        return math.hypot(max(x1 - x, 0.0, x - x2), max(y1 - y, 0.0, y - y2))
    return f


def main():
    board = pcbnew.LoadBoard(str(SRC))
    sig_layers = [pcbnew.F_Cu, pcbnew.B_Cu] if LAYERS == 4 else \
        [pcbnew.F_Cu, pcbnew.In3_Cu, pcbnew.In4_Cu, pcbnew.B_Cu]
    lidx = {l: i for i, l in enumerate(sig_layers)}
    grid = Grid(len(sig_layers))
    owner_of = lambda netcode: (netcode + 1) if netcode > 0 else BLOCK

    # ---- obstacles ---------------------------------------------------------
    terminals = {}   # netname -> list of (layers, bbox) pads
    for t in board.GetTracks():
        own = owner_of(t.GetNetCode())
        if t.Type() == pcbnew.PCB_VIA_T:
            c = (T(t.GetX()), T(t.GetY())); r = T(t.GetWidth(pcbnew.F_Cu)) / 2
            dr = T(t.GetDrillValue()) / 2
            f = seg_dist(c, c); bb = (c[0] - r, c[1] - r, c[0] + r, c[1] + r)
            raster(grid.t, own, f, bb, max(r + CLR, dr + HOLE_CLR) + TW / 2 + SAFE)
            raster([grid.v], own, f, bb, max(r + CLR + VD / 2, dr + HOLE_HOLE + VDR / 2,
                                             r + HOLE_CLR + VDR / 2, dr + HOLE_CLR + VD / 2) + SAFE)
        else:
            a = (T(t.GetStart().x), T(t.GetStart().y)); b = (T(t.GetEnd().x), T(t.GetEnd().y))
            w = T(t.GetWidth()) / 2
            f = seg_dist(a, b)
            bb = (min(a[0], b[0]) - w, min(a[1], b[1]) - w, max(a[0], b[0]) + w, max(a[1], b[1]) + w)
            L = t.GetLayer()
            if L in lidx:
                raster([grid.t[lidx[L]]], own, lambda x, y: f(x, y) - w, bb, INF_T)
            raster([grid.v], own, lambda x, y: f(x, y) - w, bb, INF_V)
    for fp in board.GetFootprints():
        for p in fp.Pads():
            bbo = p.GetBoundingBox()
            bb = (T(bbo.GetLeft()), T(bbo.GetTop()), T(bbo.GetRight()), T(bbo.GetBottom()))
            own = owner_of(p.GetNetCode())
            f = box_dist(bb)
            on = [l for l in sig_layers if p.IsOnLayer(l)]
            raster([grid.t[lidx[l]] for l in on], own, f, bb, INF_T)
            if any(p.IsOnLayer(l) for l in board.GetEnabledLayers().CuStack()):
                raster([grid.v], own, f, bb, INF_V)
            if p.GetNetname() and ROUTE_RE.match(p.GetNetname()):
                terminals.setdefault(p.GetNetname(), []).append((on, bb))
    fp_zones = [z for fp in board.GetFootprints() for z in fp.Zones()]
    for z in list(board.Zones()) + fp_zones:
        if not z.GetIsRuleArea():
            continue
        bbo = z.GetBoundingBox()
        bb = (T(bbo.GetLeft()), T(bbo.GetTop()), T(bbo.GetRight()), T(bbo.GetBottom()))
        f = box_dist(bb)
        if z.GetDoNotAllowTracks():
            raster(grid.t, BLOCK, f, bb, TW / 2 + CLR + SAFE)
        if z.GetDoNotAllowVias():
            raster([grid.v], BLOCK, f, bb, VD / 2 + SAFE)
    # board edge (outline polygon incl. J1 notches): outside = blocked,
    # edge band rasterized from the outline's own segments
    outline = pcbnew.SHAPE_POLY_SET()
    board.GetBoardPolygonOutlines(outline)
    for iy in range(NY):
        for ix in range(NX):
            x, y = cell_xy(ix, iy)
            if not outline.Contains(pcbnew.VECTOR2I(mm(x), mm(y))):
                i = idx(ix, iy)
                for a_ in grid.t:
                    a_[i] = BLOCK
                grid.v[i] = BLOCK
    ch = outline.Outline(0)
    pts = [(T(ch.CPoint(k).x), T(ch.CPoint(k).y)) for k in range(ch.PointCount())]
    for pa, pb in zip(pts, pts[1:] + pts[:1]):
        f = seg_dist(pa, pb)
        bb = (min(pa[0], pb[0]), min(pa[1], pb[1]), max(pa[0], pb[0]), max(pa[1], pb[1]))
        raster(grid.t, BLOCK, f, bb, EDGE + TW / 2)
        raster([grid.v], BLOCK, f, bb, EDGE + VD / 2)
    print(f"grid {NX}x{NY}x{len(sig_layers)} ready; nets to route: {len(terminals)}")
    if "--peek" in sys.argv:
        ref = sys.argv[sys.argv.index("--peek") + 1]
        fp = board.FindFootprintByReference(ref)
        bbo = fp.GetBoundingBox(False, False)
        x1, y1, x2, y2 = T(bbo.GetLeft()) - 0.4, T(bbo.GetTop()) - 0.4, T(bbo.GetRight()) + 0.4, T(bbo.GetBottom()) + 0.4
        for p_ in fp.Pads():
            pb = p_.GetBoundingBox()
            print("pad", p_.GetNumber(), p_.GetNetname(), p_.GetNetCode() + 1, [round(T(v), 3) for v in (pb.GetLeft(), pb.GetTop(), pb.GetRight(), pb.GetBottom())])
        L = lidx[pcbnew.B_Cu]
        sym = {}
        for iy in range(int((y1 - Y0) / G), int((y2 - Y0) / G) + 1):
            row = ""
            for ix in range(int((x1 - X0) / G), int((x2 - X0) / G) + 1):
                v = grid.t[L][idx(ix, iy)]
                if v == 0: row += "."
                elif v == BLOCK: row += "#"
                else: row += sym.setdefault(v, "abcdefghijklmnopqrstuvwxyz"[len(sym) % 26])
            print(row)
        print(sym)
    if "--dump" in sys.argv:  # obstacle maps as PGM: black = blocked for all, grey = owned by a net
        for name, arr in [(f"L{k}", a_) for k, a_ in enumerate(grid.t)] + [("V", grid.v)]:
            with open(HERE / f"grid_{LAYERS}L_{name}.pgm", "wb") as fh:
                fh.write(f"P5 {NX} {NY} 255\n".encode())
                fh.write(bytes(0 if v == BLOCK else (150 if v else 255) for v in arr))

    # pad cells are always enterable by their own net (they may sit in the
    # edge band: J1 fingers)
    def pad_cells(on, bb):
        out = []
        for iy in range(max(0, int((bb[1] - Y0) / G)), min(NY - 1, int((bb[3] - Y0) / G) + 1) + 1):
            for ix in range(max(0, int((bb[0] - X0) / G)), min(NX - 1, int((bb[2] - X0) / G) + 1) + 1):
                x, y = cell_xy(ix, iy)
                if bb[0] <= x <= bb[2] and bb[1] <= y <= bb[3]:
                    for l in on:
                        out.append((lidx[l], ix, iy))
        return out

    # ---- routing -------------------------------------------------------------
    netcode = {n: board.FindNet(n).GetNetCode() for n in terminals}
    order = sorted(terminals, key=lambda n: -(
        max(b[2] for _, b in terminals[n]) - min(b[0] for _, b in terminals[n]) +
        max(b[3] for _, b in terminals[n]) - min(b[1] for _, b in terminals[n])))
    nl = len(sig_layers)
    results, new_items = {}, []
    SQ2 = math.sqrt(2)
    moves = [(1, 0, 1.0), (-1, 0, 1.0), (0, 1, 1.0), (0, -1, 1.0),
             (1, 1, SQ2), (1, -1, SQ2), (-1, 1, SQ2), (-1, -1, SQ2)]

    def astar(n, own, srcs, tgt_set, tgt_pts, win):
        wx1, wy1, wx2, wy2 = win
        allowed = set(srcs) | tgt_set
        def h(ix, iy):
            return min(math.hypot(ix - tx, iy - ty) for tx, ty in tgt_pts)
        dist = {}
        prev = {}
        pq = []
        for s in srcs:
            dist[s] = 0.0
            heapq.heappush(pq, (h(s[1], s[2]), 0.0, s))
        settled = [0] * nl; vias_seen = 0
        while pq:
            f, g, s = heapq.heappop(pq)
            if g > dist.get(s, 1e18):
                continue
            if s in tgt_set:
                path = [s]
                while s in prev:
                    s = prev[s]; path.append(s)
                return path[::-1]
            l, ix, iy = s
            settled[l] += 1
            if grid.v[idx(ix, iy)] in (0, own):
                vias_seen += 1
            for dx, dy, c in moves:
                jx, jy = ix + dx, iy + dy
                if not (wx1 <= jx <= wx2 and wy1 <= jy <= wy2):
                    continue
                st = (l, jx, jy)
                o = grid.t[l][idx(jx, jy)]
                if o not in (0, own) and st not in allowed:
                    continue
                if dx and dy:  # no corner cutting
                    if grid.t[l][idx(ix + dx, iy)] not in (0, own) or grid.t[l][idx(ix, iy + dy)] not in (0, own):
                        if st not in allowed:
                            continue
                ng = g + c
                if ng < dist.get(st, 1e18):
                    dist[st] = ng; prev[st] = s
                    heapq.heappush(pq, (ng + h(jx, jy), ng, st))
            vo = grid.v[idx(ix, iy)]
            if nl > 1 and vo in (0, own):
                for m in range(nl):
                    if m == l:
                        continue
                    st = (m, ix, iy)
                    o = grid.t[m][idx(ix, iy)]
                    if o not in (0, own) and st not in allowed:
                        continue
                    ng = g + VIA_COST
                    if ng < dist.get(st, 1e18):
                        dist[st] = ng; prev[st] = s
                        heapq.heappush(pq, (ng + h(ix, iy), ng, st))
        if DEBUG and n in DEBUG:
            print(f"  [{n}] window {win} settled/layer {settled} via-legal cells reached {vias_seen}")
        return None

    def compress(path):
        """merge collinear 1-cell steps into runs (same layer, same direction)"""
        out = [path[0]]
        for k in range(1, len(path)):
            a, b = out[-1], path[k]
            if len(out) >= 2:
                p0 = out[-2]
                if p0[0] == a[0] == b[0] and (a[1] - p0[1], a[2] - p0[2]) != (0, 0):
                    d1 = (a[1] - p0[1], a[2] - p0[2]); d2 = (b[1] - a[1], b[2] - a[2])
                    if d1[0] * d2[1] == d1[1] * d2[0] and d1[0] * d2[0] + d1[1] * d2[1] > 0:
                        out[-1] = b
                        continue
            out.append(b)
        return out

    def commit(own, path):
        """rasterize the new copper as an obstacle for the other nets"""
        path = compress(path)
        for a, b in zip(path, path[1:]):
            if a[0] != b[0]:
                x, y = cell_xy(a[1], a[2])
                f = seg_dist((x, y), (x, y))
                bb = (x, y, x, y)
                raster(grid.t, own, f, bb, VIA_KEEP_T)
                raster([grid.v], own, f, bb, VIA_KEEP_V)
                new_items.append(("via", own, (x, y)))
            else:
                pa, pb = cell_xy(a[1], a[2]), cell_xy(b[1], b[2])
                f = seg_dist(pa, pb)
                bb = (min(pa[0], pb[0]), min(pa[1], pb[1]), max(pa[0], pb[0]), max(pa[1], pb[1]))
                raster([grid.t[a[0]]], own, f, bb, TW / 2 + INF_T)
                raster([grid.v], own, f, bb, TW / 2 + max(VD / 2 + CLR, VDR / 2 + HOLE_CLR) + SAFE)
                new_items.append(("seg", own, (sig_layers[a[0]], pa, pb)))

    for n in order:
        own = netcode[n] + 1
        terms = [pad_cells(on, bb) for on, bb in terminals[n]]
        terms = [t for t in terms if t]
        if len(terms) < 2:
            results[n] = "single terminal"
            continue
        tree = list(terms[0]); todo = terms[1:]
        ok = True
        while todo:
            tgt = set(c for t in todo for c in t)
            pts = [((min(c[1] for c in t) + max(c[1] for c in t)) / 2,
                    (min(c[2] for c in t) + max(c[2] for c in t)) / 2) for t in todo]
            allc = tree + list(tgt)
            path = None
            for margin in (80, 200, 10 ** 6):  # cells: 4 mm, 10 mm, whole board
                win = (max(0, min(c[1] for c in allc) - margin), max(0, min(c[2] for c in allc) - margin),
                       min(NX - 1, max(c[1] for c in allc) + margin), min(NY - 1, max(c[2] for c in allc) + margin))
                path = astar(n, own, tree, tgt, pts, win)
                if path:
                    break
            if not path:
                ok = False
                break
            commit(own, path)
            end = path[-1]
            hit = next(t for t in todo if end in t)
            todo.remove(hit)
            tree += path + hit
        results[n] = "ok" if ok else f"FAILED ({len(todo)} terminal(s) left)"
        print(f"{n:16s} {results[n]}")

    # ---- write copper back, merge collinear runs --------------------------
    count = 0
    segs = [it for it in new_items if it[0] == "seg"]
    for kind, own, data in new_items:
        net = board.FindNet(own - 1) if False else None
    code2net = {netcode[n] + 1: board.FindNet(n) for n in netcode}
    for kind, own, data in new_items:
        if kind == "via":
            v = pcbnew.PCB_VIA(board)
            v.SetPosition(pcbnew.VECTOR2I(mm(data[0]), mm(data[1])))
            v.SetWidth(mm(VD)); v.SetDrill(mm(VDR)); v.SetNet(code2net[own])
            board.Add(v)
        else:
            layer, pa, pb = data
            t = pcbnew.PCB_TRACK(board)
            t.SetStart(pcbnew.VECTOR2I(mm(pa[0]), mm(pa[1])))
            t.SetEnd(pcbnew.VECTOR2I(mm(pb[0]), mm(pb[1])))
            t.SetWidth(mm(TW)); t.SetLayer(layer); t.SetNet(code2net[own])
            board.Add(t)
        count += 1
    # outer GND pours (same parameters as hardware/tools/route.py)
    gnd = board.FindNet("GND")
    for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
        z = pcbnew.ZONE(board)
        z.SetLayer(layer); z.SetNet(gnd); z.SetLocalClearance(mm(0.2))
        z.SetMinThickness(mm(0.15)); z.SetThermalReliefGap(mm(0.25))
        z.SetThermalReliefSpokeWidth(mm(0.3))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
        z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
        o = z.Outline(); o.NewOutline()
        for (x, y) in [(89.2, 108.2), (110.8, 108.2), (110.8, 149.8), (89.2, 149.8)]:
            o.Append(mm(x), mm(y))
        board.Add(z)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(str(OUT), board)
    nok = sum(1 for v in results.values() if v == "ok")
    print(f"ROUTED {nok}/{len(results)} nets; {count} items written -> {OUT}")


if __name__ == "__main__":
    from kicad_exit import run
    run(main)
