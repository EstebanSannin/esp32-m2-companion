"""Generate a real KiCad schematic (.kicad_sch) from the SKiDL design.

Replaces the netlistsvg renders as the human-readable schematic (ADR 0001
fallback, activated after owner feedback on netlistsvg label collisions).
Style: no routed wires - every pin carries a global net label, so nothing
ever crosses. Parts are grouped by SPEC §12 block with a group heading.

Run: uv run python tools/gen_sch.py   (or `make sch`)
Outputs: build/esp32_m2_companion.kicad_sch + PDF via kicad-cli.
"""

import os
import re
import subprocess
import sys
import uuid
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))

SYM_DIR = os.path.expanduser(
    "~/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols")
KICAD_CLI = os.path.expanduser(
    "~/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli")

import sexpdata  # noqa: E402
from sexpdata import Symbol as S  # noqa: E402


def u():
    return str(uuid.uuid4())


# ---------------------------------------------------------------- lib symbols

def _find_symbol(sexp, name):
    for item in sexp[1:]:
        if (isinstance(item, list) and item and item[0] == S("symbol")
                and item[1] == name):
            return item
    return None


_lib_cache = {}


def load_symbol(lib, name):
    """Return the symbol s-expr from a KiCad lib, renamed to lib:name."""
    key = (lib, name)
    if key in _lib_cache:
        return _lib_cache[key]
    path = Path(SYM_DIR) / f"{lib}.kicad_sym"
    text = path.read_text()
    tree = sexpdata.loads(text)
    sym = _find_symbol(tree, name)
    if sym is None:
        raise KeyError(f"{name} not in {lib}")
    # resolve 'extends' (aliases) by merging parent drawing
    for item in sym[1:]:
        if isinstance(item, list) and item and item[0] == S("extends"):
            parent = load_symbol(lib, item[1])
            merged = [e for e in parent[1:] if not (
                isinstance(e, list) and e and e[0] == S("property"))]
            props = [e for e in sym[1:] if isinstance(e, list) and e
                     and e[0] != S("extends")]
            sym = [S("symbol"), sym[1]] + props + merged[1:]
            # rename inner units parent_X_Y -> name_X_Y (parent[1] is the
            # cached, lib-prefixed name - strip the prefix)
            parent_base = str(parent[1]).split(":")[-1]
            sym = _rename_units(sym, parent_base, name)
            break
    sym = list(sym)
    sym[1] = f"{lib}:{name}"
    _lib_cache[key] = sym
    return sym


def _rename_units(sym, old, new):
    def walk(node):
        if isinstance(node, list):
            out = []
            for i, e in enumerate(node):
                if (i == 1 and out and out[0] == S("symbol")
                        and isinstance(e, str) and e.startswith(old + "_")):
                    out.append(new + e[len(old):])
                else:
                    out.append(walk(e))
            return out
        return node
    return walk(sym)


def symbol_pins(sym):
    """[(number, x, y, angle, length)] from a lib symbol s-expr (unit 1)."""
    pins = []

    def walk(node):
        if isinstance(node, list) and node and node[0] == S("pin"):
            at = num = length = None
            for e in node:
                if isinstance(e, list) and e:
                    if e[0] == S("at"):
                        at = (float(e[1]), float(e[2]),
                              float(e[3]) if len(e) > 3 else 0.0)
                    elif e[0] == S("number"):
                        num = str(e[1])
                    elif e[0] == S("length"):
                        length = float(e[1])
            pins.append((num, at[0], at[1], at[2], length or 2.54))
        elif isinstance(node, list):
            for e in node:
                walk(e)
    walk(sym)
    return pins


def symbol_bbox(sym):
    """Rough bbox of the symbol drawing incl. pins (lib coords)."""
    xs, ys = [0.0], [0.0]

    def walk(node):
        if isinstance(node, list):
            if node and node[0] == S("xy"):
                xs.append(float(node[1])); ys.append(float(node[2]))
            elif node and node[0] in (S("at"), S("start"), S("end"),
                                      S("mid"), S("center")):
                try:
                    xs.append(float(node[1])); ys.append(float(node[2]))
                except (ValueError, TypeError):
                    pass
            for e in node:
                walk(e)
    walk(sym)
    return min(xs), min(ys), max(xs), max(ys)


def make_edge_symbol():
    """Custom lib symbol for the 67-pin M.2 edge (odd left, even right)."""
    from blocks.m2_keyb_edge.m2_keyb_edge import _PINS
    odd = [p for p in _PINS if p[0] % 2 == 1]
    even = [p for p in _PINS if p[0] % 2 == 0]
    rows = max(len(odd), len(even))
    h = (rows + 1) * 2.54
    w = 66.04
    body = [S("symbol"), "esp32m2:M2_KEYB_2242_EDGE",
            [S("pin_names"), [S("offset"), 1.02]],
            [S("exclude_from_sim"), S("no")],
            [S("in_bom"), S("yes")], [S("on_board"), S("yes")],
            [S("property"), "Reference", "J", [S("at"), 0, h / 2 + 2.54, 0],
             [S("effects"), [S("font"), [S("size"), 1.27, 1.27]]]],
            [S("property"), "Value", "M2_KEYB_2242_EDGE",
             [S("at"), 0, -h / 2 - 2.54, 0],
             [S("effects"), [S("font"), [S("size"), 1.27, 1.27]]]]]
    unit = [S("symbol"), "M2_KEYB_2242_EDGE_1_1",
            [S("rectangle"), [S("start"), -w / 2, h / 2],
             [S("end"), w / 2, -h / 2],
             [S("stroke"), [S("width"), 0.254], [S("type"), S("default")]],
             [S("fill"), [S("type"), S("background")]]]]
    for i, (num, name, _f) in enumerate(odd):
        y = h / 2 - (i + 1) * 2.54
        unit.append([S("pin"), S("passive"), S("line"),
                     [S("at"), -w / 2 - 2.54, y, 0], [S("length"), 2.54],
                     [S("name"), name, [S("effects"), [S("font"), [S("size"), 1.27, 1.27]]]],
                     [S("number"), str(num), [S("effects"), [S("font"), [S("size"), 1.27, 1.27]]]]])
    for i, (num, name, _f) in enumerate(even):
        y = h / 2 - (i + 1) * 2.54
        unit.append([S("pin"), S("passive"), S("line"),
                     [S("at"), w / 2 + 2.54, y, 180.0], [S("length"), 2.54],
                     [S("name"), name, [S("effects"), [S("font"), [S("size"), 1.27, 1.27]]]],
                     [S("number"), str(num), [S("effects"), [S("font"), [S("size"), 1.27, 1.27]]]]])
    body.append(unit)
    return body


# ----------------------------------------------------------------- schematic

def build_schematic():
    import design
    design.build()
    import builtins
    circuit = builtins.default_circuit

    git_rev = subprocess.run(
        ["git", "describe", "--always", "--dirty"], cwd=HERE.parent,
        capture_output=True, text=True).stdout.strip() or "dev"

    lib_symbols = {}
    placed = []      # symbol instances
    labels = []      # global labels
    texts = []       # block headings

    # block per part via the stable explicit designators (skidl 2.3 has no
    # usable hierarchy attribute)
    BLOCK_REFS = {
        "m2_keyb_edge": {"J1"},
        "power_3v3": {"FB1", "C1", "C2", "C3"},
        "usb_esd": {"U1", "C4", "R7", "R8", "C8", "C9"},
        "sideband_recovery": {"R1", "R2", "C5", "D1", "D2", "TP1", "TP2"},
        "esp32s3_companion": {"U2", "C6", "C7", "TP3", "TP4"},
        "leds": {"R3", "R4", "D3", "D4"},
        "io_header": {"J3", "J4", "R5", "R6", "TP5", "TP6"},
    }

    def block_of(part):
        for b, refs in BLOCK_REFS.items():
            if part.ref in refs:
                return b
        return "misc"

    groups = {}
    for part in circuit.parts:
        groups.setdefault(block_of(part), []).append(part)

    # deterministic order inside groups
    def refkey(p):
        m = re.match(r"([A-Z]+)(\d+)", p.ref)
        return (m.group(1), int(m.group(2)))
    for g in groups.values():
        g.sort(key=refkey)

    ORDER = ["m2_keyb_edge", "power_3v3", "usb_esd", "sideband_recovery",
             "esp32s3_companion", "leds", "io_header"]
    TITLES = {
        "m2_keyb_edge": "M.2 KEY-B 2242 EDGE",
        "power_3v3": "POWER 3V3 (SPEC 6.2)",
        "usb_esd": "USB + ESD (SPEC 6.3)",
        "sideband_recovery": "SIDEBAND RECOVERY (ADR 0002)",
        "esp32s3_companion": "ESP32-S3 MODULE",
        "leds": "LEDS (ADR 0003)",
        "io_header": "IO CONNECTORS (ADR 0005)",
    }

    def place_part(part, x, y, rot=0):
        """Place symbol with left edge ~x and top edge ~y; label all pins.
        rot=90 lays 2-pin passives horizontal (labels read horizontally).
        Returns (width, height) of the cell used."""
        if part.ref == "J1":
            sym = make_edge_symbol()
            lib_id = "esp32m2:M2_KEYB_2242_EDGE"
        else:
            lib = part.lib.filename if hasattr(part.lib, "filename") else str(part.lib)
            lib = Path(str(lib)).stem
            sym = load_symbol(lib, part.name)
            lib_id = f"{lib}:{part.name}"
        if lib_id not in lib_symbols:
            lib_symbols[lib_id] = sym
        pins = symbol_pins(sym)
        x0, y0, x1, y1 = symbol_bbox(sym)
        if rot == 90:
            # screen-CCW rotation: lib (px,py) -> sheet offset (-py,-px)
            # bbox transforms accordingly (height<->width)
            x = x + y1
            y = y + x1
        else:
            x = x - x0
            y = y + y1

        value = str(part.value)
        if part.fields.get("DNP"):
            value += " [DNP]"
        inst = [S("symbol"), [S("lib_id"), lib_id], [S("at"), x, y, rot],
                [S("unit"), 1],
                [S("exclude_from_sim"), S("no")], [S("in_bom"), S("yes")],
                [S("on_board"), S("yes")], [S("dnp"),
                 S("yes") if part.fields.get("DNP") else S("no")],
                [S("uuid"), u()],
                [S("property"), "Reference", part.ref,
                 [S("at"), x, y - (y1 + 2.0), 0],
                 [S("effects"), [S("font"), [S("size"), 1.27, 1.27]]]],
                [S("property"), "Value", value,
                 [S("at"), x, y - (y0 - 2.0), 0],
                 [S("effects"), [S("font"), [S("size"), 1.27, 1.27]]]],
                [S("property"), "Footprint", str(part.footprint or ""),
                 [S("at"), x, y, 0],
                 [S("effects"), [S("font"), [S("size"), 1.27, 1.27]],
                  [S("hide"), S("yes")]]],
                ]
        for num, *_rest in pins:
            inst.append([S("pin"), str(num), [S("uuid"), u()]])
        proj = [S("instances"),
                [S("project"), "esp32_m2_companion",
                 [S("path"), f"/{ROOT_UUID}",
                  [S("reference"), part.ref], [S("unit"), 1]]]]
        inst.append(proj)
        placed.append(inst)

        # net labels at pin endpoints
        netmap = {str(pin.num): pin.nets[0].name
                  for pin in part.pins if pin.nets}
        for num, px, py, ang, _l in pins:
            net = netmap.get(str(num))
            if not net:
                continue
            if rot == 90:
                sx, sy = x - py, y - px
            else:
                sx, sy = x + px, y - py        # lib Y is inverted on sheet
            # label direction from the pin's outward position vs center
            dx, dy = sx - x, sy - y
            if abs(dx) >= abs(dy):
                la = 180.0 if dx < 0 else 0.0
            else:
                la = 90.0 if dy > 0 else 270.0
            labels.append([S("global_label"), net,
                           [S("shape"), S("passive")],
                           [S("at"), round(sx, 3), round(sy, 3), la],
                           [S("effects"), [S("font"), [S("size"), 1.27, 1.27]],
                            [S("justify"),
                             S("right") if la == 180.0 else S("left")]],
                           [S("uuid"), u()]])
        return (x1 - x0), (y1 - y0) + 13.0

    # ---- layout: columns of blocks
    global ROOT_UUID
    ROOT_UUID = u()
    x_cursor = 55.0
    PAGE_H = 380.0
    for block in ORDER:
        parts = groups.get(block, [])
        if not parts:
            continue
        y_cursor = 42.0
        texts.append([S("text"), TITLES[block],
                      [S("exclude_from_sim"), S("no")],
                      [S("at"), x_cursor, y_cursor - 8.0, 0],
                      [S("effects"), [S("font"), [S("size"), 2.2, 2.2],
                                      [S("bold"), S("yes")]]],
                      [S("uuid"), u()]])
        col_w = 30.0
        for part in parts:
            # lay 2-pin parts horizontal: rotate only those whose lib
            # symbol has vertically-arranged pins (R/C/FB are vertical in
            # the KiCad lib; LED is already horizontal)
            rot = 0
            if len(part.pins) == 2 and part.ref != "J1":
                lib = Path(str(part.lib.filename if hasattr(part.lib, "filename")
                                else str(part.lib))).stem
                try:
                    ps = symbol_pins(load_symbol(lib, part.name))
                    if len(ps) == 2 and abs(ps[0][2] - ps[1][2]) > abs(ps[0][1] - ps[1][1]):
                        rot = 90
                except KeyError:
                    pass
            w, h = place_part(part, x_cursor, y_cursor, rot)
            y_cursor += h
            col_w = max(col_w, w)
            if y_cursor > PAGE_H and part is not parts[-1]:
                y_cursor = 42.0
                x_cursor += col_w + 24.0
                col_w = 30.0
        x_cursor += col_w + 26.0

    tb = [S("title_block"),
          [S("title"), "ESP32 M.2 Companion - Key-B 2242 USB companion MCU"],
          [S("date"), date.today().isoformat()],
          [S("rev"), git_rev],
          [S("company"), "(c) 2026 Stefano Viola - open source hardware"],
          [S("comment"), 1, "License: CERN-OHL-P v2 (see LICENSE)"],
          [S("comment"), 2, "Schematic generated from SKiDL sources - do not edit by hand"],
          [S("comment"), 3, "Design: Stefano Viola, with Claude (Anthropic)"],
          [S("comment"), 4, "github: esp32-m2-companion"]]

    sch = [S("kicad_sch"),
           [S("version"), 20250114],
           [S("generator"), "gen_sch"],
           [S("generator_version"), "9.0"],
           [S("uuid"), ROOT_UUID],
           [S("paper"), "A2"],
           tb,
           [S("lib_symbols")] + list(lib_symbols.values())]
    sch += texts + placed + labels
    sch.append([S("sheet_instances"), [S("path"), "/",
                [S("page"), "1"]]])

    out = HERE / "build" / "esp32_m2_companion.kicad_sch"
    out.write_text(sexpdata.dumps(sch))
    print("wrote", out)

    pdf = HERE / "build" / "esp32_m2_companion_schematic.pdf"
    r = subprocess.run([KICAD_CLI, "sch", "export", "pdf", "--output",
                        str(pdf), str(out)], capture_output=True, text=True)
    print(r.stdout.strip() or r.stderr.strip())
    return out, pdf


if __name__ == "__main__":
    build_schematic()
