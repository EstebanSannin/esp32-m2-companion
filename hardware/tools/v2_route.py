"""v2 GATE V3 router: power fan-out + sequential grid routing on the real
board (derived from v2/probe/gridprobe.py; same obstacle model, same
rules). Writes tracks/vias into hardware/kicad/esp32_m2_companion.kicad_pcb
(backup in build/pre_route.kicad_pcb). KiCad DRC is the judge (make drc).

Method (docs/routing-method.md): critical USB pair already hand-routed +
locked (kept from rev B); this tool does ONE pass over the rest, then the
leftovers are finished by hand. It is never looped to chase DRC errors.

Layers (ADR 0008, JLC06081H-2116): signals on F.Cu / In2.Cu / In3.Cu / B.Cu;
In1.Cu = GND plane, In4.Cu = +3V3 plane (no tracks).
Rules: track 0.127 mm (power nets wider), clearance 0.127 mm,
via 0.45/0.3 mm, hole clearance 0.25 mm, copper-to-edge 0.3 mm.

Stages:
  1. power fan-out: every SMD pad on GND / +3V3 gets a via to its plane
     (via-in-pad when legal - 6-layer JLC vias are epoxy-filled & capped -
     else the shortest legal stub). J1 fingers connect through the outer
     GND pours / their own nets instead.
  2. wide power nets (+3V3_M2, +3V3_EFUSE) at 0.5 mm, full width checked.
  3. all remaining signal nets, longest first, sequential (no rip-up).

  $KPY tools/v2_route.py
"""

import heapq
import math
import shutil
import sys
from array import array
from pathlib import Path

import pcbnew

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / "tools"))
PCB = HERE / "kicad" / "esp32_m2_companion.kicad_pcb"
BACKUP = HERE / "build" / "pre_route.kicad_pcb"

G = 0.05
X0, Y0, X1, Y1 = 88.9, 107.9, 111.1, 150.1
NX, NY = int((X1 - X0) / G) + 1, int((Y1 - Y0) / G) + 1
TW, CLR = 0.127, 0.127
VD, VDR = 0.45, 0.3
EDGE = 0.3
SAFE = 0.02
HOLE_CLR, HOLE_HOLE = 0.25, 0.25
INF_T = CLR + TW / 2 + SAFE
INF_V = max(VD / 2 + CLR, VDR / 2 + HOLE_CLR) + SAFE
VIA_KEEP_T = max(VD / 2 + CLR, VDR / 2 + HOLE_CLR) + TW / 2 + SAFE
VIA_KEEP_V = max(VD + CLR, VDR + HOLE_HOLE, VD / 2 + VDR / 2 + HOLE_CLR) + SAFE
VIA_COST = 16
BLOCK = 0xFFFF

PLANE_NETS = {"GND", "+3V3"}
KEEP_NETS = {"USBH3_D_P", "USBH3_D_N", "USB_D_P_ESD", "USB_D_N_ESD",
             "USB_D_P", "USB_D_N"}
WIDE = {"+3V3_M2": 0.5, "+3V3_EFUSE": 0.5}
# MCU-side EXP nets (docs/pinmap.md §6.2) - routed with the EXP chain
EXP_MCU = {"IO39", "IO41", "IO1", "IO2", "IO18", "IO4", "IO5", "IO6", "IO7",
           "IO15", "IO16", "IO17"}

T = pcbnew.ToMM
mm = pcbnew.FromMM
SQ2 = math.sqrt(2)
MOVES = [(1, 0, 1.0), (-1, 0, 1.0), (0, 1, 1.0), (0, -1, 1.0),
         (1, 1, SQ2), (1, -1, SQ2), (-1, 1, SQ2), (-1, -1, SQ2)]


def idx(ix, iy):
    return iy * NX + ix


def cell_xy(ix, iy):
    return X0 + ix * G, Y0 + iy * G


def mark(arr, i, owner):
    cur = arr[i]
    if cur == 0:
        arr[i] = owner
    elif cur != owner:
        arr[i] = BLOCK


def raster(arrs, owner, dist_fn, bbox, r):
    x1, y1, x2, y2 = bbox
    ix1 = max(0, int((x1 - r - X0) / G)); ix2 = min(NX - 1, int((x2 + r - X0) / G) + 1)
    iy1 = max(0, int((y1 - r - Y0) / G)); iy2 = min(NY - 1, int((y2 + r - Y0) / G) + 1)
    for iy in range(iy1, iy2 + 1):
        y = Y0 + iy * G
        base = iy * NX
        for ix in range(ix1, ix2 + 1):
            if dist_fn(X0 + ix * G, y) <= r:
                for a in arrs:
                    mark(a, base + ix, owner)


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
    shutil.copy(PCB, BACKUP)
    board = pcbnew.LoadBoard(str(PCB))
    sig = [pcbnew.F_Cu, pcbnew.In2_Cu, pcbnew.In3_Cu, pcbnew.B_Cu]
    lidx = {l: i for i, l in enumerate(sig)}
    nl = len(sig)
    gt = [array("H", [0]) * (NX * NY) for _ in sig]
    gv = array("H", [0]) * (NX * NY)
    owner_of = lambda code: (code + 1) if code > 0 else BLOCK

    # ---- obstacles -------------------------------------------------------
    for t in board.GetTracks():
        own = owner_of(t.GetNetCode())
        if t.Type() == pcbnew.PCB_VIA_T:
            c = (T(t.GetX()), T(t.GetY())); r = T(t.GetWidth(pcbnew.F_Cu)) / 2
            dr = T(t.GetDrillValue()) / 2
            f = seg_dist(c, c); bb = (c[0] - r, c[1] - r, c[0] + r, c[1] + r)
            raster(gt, own, f, bb, max(r + CLR, dr + HOLE_CLR) + TW / 2 + SAFE)
            raster([gv], own, f, bb, max(r + CLR + VD / 2, dr + HOLE_HOLE + VDR / 2,
                                         r + HOLE_CLR + VDR / 2, dr + HOLE_CLR + VD / 2) + SAFE)
        else:
            a = (T(t.GetStart().x), T(t.GetStart().y)); b = (T(t.GetEnd().x), T(t.GetEnd().y))
            w = T(t.GetWidth()) / 2
            f = seg_dist(a, b)
            bb = (min(a[0], b[0]) - w, min(a[1], b[1]) - w, max(a[0], b[0]) + w, max(a[1], b[1]) + w)
            if t.GetLayer() in lidx:
                raster([gt[lidx[t.GetLayer()]]], own, lambda x, y: f(x, y) - w, bb, INF_T)
            raster([gv], own, lambda x, y: f(x, y) - w, bb, INF_V)
    pads_by_net = {}
    cu_all = board.GetEnabledLayers().CuStack()
    for fp in board.GetFootprints():
        for p in fp.Pads():
            bbo = p.GetBoundingBox()
            bb = (T(bbo.GetLeft()), T(bbo.GetTop()), T(bbo.GetRight()), T(bbo.GetBottom()))
            own = owner_of(p.GetNetCode())
            f = box_dist(bb)
            on = [l for l in sig if p.IsOnLayer(l)]
            raster([gt[lidx[l]] for l in on], own, f, bb, INF_T)
            if any(p.IsOnLayer(l) for l in cu_all):
                raster([gv], own, f, bb, INF_V)
            if p.GetNetname() and p.GetNumber():
                pads_by_net.setdefault(p.GetNetname(), []).append((fp.GetReference(), p, on, bb))
    for z in list(board.Zones()) + [z for fp in board.GetFootprints() for z in fp.Zones()]:
        if not z.GetIsRuleArea():
            continue
        bbo = z.GetBoundingBox()
        bb = (T(bbo.GetLeft()), T(bbo.GetTop()), T(bbo.GetRight()), T(bbo.GetBottom()))
        f = box_dist(bb)
        if z.GetDoNotAllowTracks():
            raster(gt, BLOCK, f, bb, TW / 2 + CLR + SAFE)
        if z.GetDoNotAllowVias():
            raster([gv], BLOCK, f, bb, VD / 2 + SAFE)
    outline = pcbnew.SHAPE_POLY_SET()
    board.GetBoardPolygonOutlines(outline)
    for iy in range(NY):
        for ix in range(NX):
            x, y = cell_xy(ix, iy)
            if not outline.Contains(pcbnew.VECTOR2I(mm(x), mm(y))):
                i = idx(ix, iy)
                for a_ in gt:
                    a_[i] = BLOCK
                gv[i] = BLOCK
    ch = outline.Outline(0)
    pts = [(T(ch.CPoint(k).x), T(ch.CPoint(k).y)) for k in range(ch.PointCount())]
    for pa, pb in zip(pts, pts[1:] + pts[:1]):
        f = seg_dist(pa, pb)
        bb = (min(pa[0], pb[0]), min(pa[1], pb[1]), max(pa[0], pb[0]), max(pa[1], pb[1]))
        raster(gt, BLOCK, f, bb, EDGE + TW / 2)
        raster([gv], BLOCK, f, bb, EDGE + VD / 2)
    print(f"grid {NX}x{NY}x{nl} ready")

    def pad_cells(on, bb):
        out = []
        for iy in range(max(0, int((bb[1] - Y0) / G)), min(NY - 1, int((bb[3] - Y0) / G) + 1) + 1):
            for ix in range(max(0, int((bb[0] - X0) / G)), min(NX - 1, int((bb[2] - X0) / G) + 1) + 1):
                x, y = cell_xy(ix, iy)
                if bb[0] <= x <= bb[2] and bb[1] <= y <= bb[3]:
                    for l in on:
                        out.append((lidx[l], ix, iy))
        return out

    def offsets(radius_mm):
        r = int(math.ceil(radius_mm / G))
        return [(dx, dy) for dx in range(-r, r + 1) for dy in range(-r, r + 1)
                if math.hypot(dx, dy) * G <= radius_mm]

    NECKZ = {}   # own -> set of (l, ix, iy) cells inside the neck zone

    def ok_cell(l, ix, iy, own, offs, allowed):
        if (l, ix, iy) in allowed:
            return True
        arr = gt[l]
        if len(offs) > 1 and (l, ix, iy) in NECKZ.get(own, ()):
            return arr[idx(ix, iy)] in (0, own)
        for dx, dy in offs:
            jx, jy = ix + dx, iy + dy
            if not (0 <= jx < NX and 0 <= jy < NY):
                return False
            if arr[idx(jx, jy)] not in (0, own):
                return False
        return True

    def search(own, srcs, is_target, h, win, offs, via_ok=True):
        wx1, wy1, wx2, wy2 = win
        allowed = set(srcs)
        dist, prev, pq = {}, {}, []
        for s in srcs:
            dist[s] = 0.0
            heapq.heappush(pq, (h(s), 0.0, s))
        while pq:
            f, g, s = heapq.heappop(pq)
            if g > dist.get(s, 1e18):
                continue
            if is_target(s):
                path = [s]
                while s in prev:
                    s = prev[s]
                    path.append(s)
                return path[::-1]
            l, ix, iy = s
            for dx, dy, c in MOVES:
                jx, jy = ix + dx, iy + dy
                if not (wx1 <= jx <= wx2 and wy1 <= jy <= wy2):
                    continue
                st = (l, jx, jy)
                tgt = is_target(st)
                if not tgt and not ok_cell(l, jx, jy, own, offs, allowed):
                    continue
                if dx and dy and not tgt:
                    if not (ok_cell(l, ix + dx, iy, own, offs, allowed)
                            and ok_cell(l, ix, iy + dy, own, offs, allowed)):
                        continue
                ng = g + c
                if ng < dist.get(st, 1e18):
                    dist[st] = ng
                    prev[st] = s
                    heapq.heappush(pq, (ng + h(st), ng, st))
            if via_ok and gv[idx(ix, iy)] in (0, own):
                for m in range(nl):
                    if m == l:
                        continue
                    st = (m, ix, iy)
                    if not is_target(st) and not ok_cell(m, ix, iy, own, offs, allowed):
                        continue
                    ng = g + VIA_COST
                    if ng < dist.get(st, 1e18):
                        dist[st] = ng
                        prev[st] = s
                        heapq.heappush(pq, (ng + h(st), ng, st))
        return None

    def compress(path):
        out = [path[0]]
        for k in range(1, len(path)):
            a, b = out[-1], path[k]
            if len(out) >= 2:
                p0 = out[-2]
                if p0[0] == a[0] == b[0]:
                    d1 = (a[1] - p0[1], a[2] - p0[2]); d2 = (b[1] - a[1], b[2] - a[2])
                    if d1 != (0, 0) and d1[0] * d2[1] == d1[1] * d2[0] and d1[0] * d2[0] + d1[1] * d2[1] > 0:
                        out[-1] = b
                        continue
            out.append(b)
        return out

    items = []   # ("via", own, (x, y)) | ("seg", own, (layer, pa, pb, width))

    def put_via(own, x, y):
        f = seg_dist((x, y), (x, y))
        bb = (x, y, x, y)
        raster(gt, own, f, bb, VIA_KEEP_T)
        raster([gv], own, f, bb, VIA_KEEP_V)
        items.append(("via", own, (x, y)))

    NECK = 0.6   # mm: wide nets neck down to TW this close to their own pads

    def commit(own, path, width, end_via=False, neck=None):
        path = compress(path)
        if neck:
            # split runs so segments inside the neck zone get width TW
            fine = []
            for a, b in zip(path, path[1:]):
                if a[0] != b[0]:
                    fine += [a, b]
                    continue
                n = max(abs(b[1] - a[1]), abs(b[2] - a[2]))
                for k in range(n + 1):
                    c = (a[0], a[1] + (b[1] - a[1]) * k // max(n, 1),
                         a[2] + (b[2] - a[2]) * k // max(n, 1))
                    if not fine or fine[-1] != c:
                        fine.append(c)
            path = fine
        for a, b in zip(path, path[1:]):
            if a[0] != b[0]:
                put_via(own, *cell_xy(a[1], a[2]))
            else:
                pa, pb = cell_xy(a[1], a[2]), cell_xy(b[1], b[2])
                w = width
                if neck and (neck(a) or neck(b)):
                    w = TW
                f = seg_dist(pa, pb)
                bb = (min(pa[0], pb[0]), min(pa[1], pb[1]), max(pa[0], pb[0]), max(pa[1], pb[1]))
                raster([gt[a[0]]], own, f, bb, w / 2 + INF_T)
                raster([gv], own, f, bb, w / 2 + max(VD / 2 + CLR, VDR / 2 + HOLE_CLR) + SAFE)
                items.append(("seg", own, (sig[a[0]], pa, pb, w)))
        if end_via:
            put_via(own, *cell_xy(path[-1][1], path[-1][2]))

    code2net = {}

    # ---- 1. power fan-out --------------------------------------------------
    fan_ok = fan_fail = 0
    fan_failed = []
    for pn in sorted(PLANE_NETS):
        ni = board.FindNet(pn)
        own = ni.GetNetCode() + 1
        code2net[own] = ni
        for ref, p, on, bb in pads_by_net.get(pn, []):
            if ref == "J1" or p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH or not on:
                continue
            srcs = pad_cells(on, bb)
            if not srcs:
                continue
            cx = sum(s[1] for s in srcs) / len(srcs); cy = sum(s[2] for s in srcs) / len(srcs)
            win = (int(cx) - 50, int(cy) - 50, int(cx) + 50, int(cy) + 50)

            def is_t(s, own=own):
                return gv[idx(s[1], s[2])] in (0, own) and s[0] == srcs[0][0]

            path = search(own, srcs, is_t, lambda s: 0.0, win, [(0, 0)], via_ok=False)
            if path:
                commit(own, path, 0.2, end_via=True)
                fan_ok += 1
            else:
                fan_fail += 1
                fan_failed.append(f"{ref}.{p.GetNumber()}({pn})")
    print(f"fan-out: {fan_ok} vias, {fan_fail} failed {fan_failed}")

    # ---- 2./3. nets -------------------------------------------------------
    nets = [n for n, ps in pads_by_net.items()
            if n not in PLANE_NETS and n not in KEEP_NETS and len(ps) >= 2]

    def span(n):
        bbs = [b for *_, b in pads_by_net[n]]
        return (max(b[2] for b in bbs) - min(b[0] for b in bbs)
                + max(b[3] for b in bbs) - min(b[1] for b in bbs))
    import re as _re
    def prio(n):
        if n in WIDE:
            return 0
        if _re.match(r"^EXP_\d+(_S)?$", n) or n in EXP_MCU:
            return 1
        return 2
    order = sorted(nets, key=lambda n: (prio(n), -span(n)))
    results = {}
    for n in order:
        ni = board.FindNet(n)
        own = ni.GetNetCode() + 1
        code2net[own] = ni
        width = WIDE.get(n, TW)
        offs = offsets(max(0.0, (width - TW) / 2))
        neck = None
        if n in WIDE:
            zone = set()
            for _r, _p, on, bb in pads_by_net[n]:
                grown = (bb[0] - 0.6, bb[1] - 0.6, bb[2] + 0.6, bb[3] + 0.6)
                zone.update(pad_cells(on if on else sig, grown))
                for c in pad_cells(on, grown):
                    zone.update((m, c[1], c[2]) for m in range(nl))
            NECKZ[own] = zone
            neck = lambda c, zone=zone: c in zone
        terms = [pad_cells(on, bb) for _r, _p, on, bb in pads_by_net[n]]
        terms = [t for t in terms if t]
        tree = list(terms[0])
        todo = terms[1:]
        ok = True
        while todo:
            tgt = set(c for t in todo for c in t)
            pts_ = [((min(c[1] for c in t) + max(c[1] for c in t)) / 2,
                     (min(c[2] for c in t) + max(c[2] for c in t)) / 2) for t in todo]

            def h(s, pts_=pts_):
                return min(math.hypot(s[1] - tx, s[2] - ty) for tx, ty in pts_)
            allc = tree + list(tgt)
            path = None
            for margin in (80, 200, 10 ** 6):
                win = (max(0, min(c[1] for c in allc) - margin), max(0, min(c[2] for c in allc) - margin),
                       min(NX - 1, max(c[1] for c in allc) + margin), min(NY - 1, max(c[2] for c in allc) + margin))
                path = search(own, tree, lambda s, tgt=tgt: s in tgt, h, win, offs)
                if path:
                    break
            if not path:
                ok = False
                break
            commit(own, path, width, neck=neck)
            end = path[-1]
            hit = next(t for t in todo if end in t)
            todo.remove(hit)
            tree += path + hit
        results[n] = ok
        print(f"  {n:18s} {'ok' if ok else 'FAILED'}")

    # ---- write back ------------------------------------------------------
    for kind, own, data in items:
        if kind == "via":
            v = pcbnew.PCB_VIA(board)
            v.SetPosition(pcbnew.VECTOR2I(mm(data[0]), mm(data[1])))
            v.SetWidth(mm(VD)); v.SetDrill(mm(VDR)); v.SetNet(code2net[own])
            board.Add(v)
        else:
            layer, pa, pb, width = data
            t = pcbnew.PCB_TRACK(board)
            t.SetStart(pcbnew.VECTOR2I(mm(pa[0]), mm(pa[1])))
            t.SetEnd(pcbnew.VECTOR2I(mm(pb[0]), mm(pb[1])))
            t.SetWidth(mm(width)); t.SetLayer(layer); t.SetNet(code2net[own])
            board.Add(t)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(str(PCB), board)
    nok = sum(results.values())
    print(f"ROUTED {nok}/{len(results)} nets; fan-out {fan_ok}/{fan_ok + fan_fail}; "
          f"{len(items)} items -> {PCB}")
    print("FAILED:", [n for n, v in results.items() if not v])


if __name__ == "__main__":
    from kicad_exit import run
    run(main)
