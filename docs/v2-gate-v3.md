# v2.0 Rev A — GATE V3 package (layout)

Status: **approved 2026-10-10 (owner)** · Previous gate: `docs/v2-gate-v2.md` (approved 2026-10-07)

SPEC A3 §9: *GATE V3 = placement + routing of all new nets DRC-clean, then layout DRC-clean
(`make drc`).*

## Result

| Check | Result |
|---|---|
| `make drc` | **0 violations, 0 unconnected**, 1 excluded (U2 library serialization, since rev B) |
| `make check` | ERC clean · BOM · **`check_v2_netlist.py` PASS (76 nets)** |
| Footprint ↔ library parity | clean (DRC `lib_footprint_*`) |
| Module | ESP32-S3-WROOM-1-**N8R2** kept (owner, 2026-10-10) |

## Review artifacts

| File | What it is for |
|---|---|
| `docs/review/v2_reva_connections.md` | **Per-block connection tables** (every pin → net → other pins, tagged by block) + net index. This answers the GATE V2 remark that the label-only schematic is slow to review. |
| `docs/review/v2_reva_drawings.pdf` | Assembly (top + bottom, 4:1, pad numbers, polarity) + fab sheet |
| `docs/review/v2_reva_label_inventory.md` | Every silkscreen text, refdes visibility, polarity markers, connector pinouts, test points |
| `docs/review/v2_reva_schematic.pdf` | Generated schematic (unchanged since V2, regenerated) |
| `docs/stackup.md` § v2 | 6-layer stackup, routing rules as built, per-layer copper images |
| `docs/img/board_*.png`, `view_*.png`, `docs/3d/` | Renders, labelled views, 3D (GLB/STEP/STL, HTML viewer) |
| `hardware/kicad/esp32_m2_companion.kicad_pcb` | Source of truth — open in the PCB Editor |

## Placement (bottom side; the top carries the module, J3/J4)

| Area | Parts | Note |
|---|---|---|
| Switch strip | U3–U5 TMUX1511 + C10–C12 | above their EXP finger groups; the rev-B test-point row was freed for them |
| MCU side of the switches | RN1–RN3 220 Ω, R20/R21 I²C pull-ups | MCU-side pad column faces the module's IO pads |
| Carrier detect | Q1, R22–R26, C13 | near CONFIG_2/3 sense |
| Host sidebands | Q2, Q3, R27–R30 | near module pads 24/33/35 |
| eFuse | U6 + C14 (IN) + FB1 (OUT) + R31/R32 (OVLO) + R33 (EN) + R34 (ILM) | above fingers 70/72/74, out of the J1 courtyard; FB1 right at the OUT strip |
| Bulk | C1/C2 22 µF | moved next to the module 3V3 pin (were in the eFuse area) |

## Routing (6 layers JLC06081H-2116: F / In1 GND / In2 / In3 / In4 +3V3 / B)

- **Hand-routed + locked** (scripts, explicit geometry):
  - MCU-side USB pair on In2 over the In1 GND plane, via-in-pad into the module (`v2_usb_route.py`).
  - +3V3_M2 input trunk 0.35 mm (fingers → C14 → eFuse IN) and the eFuse OUT → FB1 hop (`v2_power_route.py`).
  - EXP_7 / EXP_10 / LED_1_n finger fan-ins (`v2_fanin_route.py`).
  - USBH3_D_N finger-9 via moved off finger 10 (`v2_usbh3_dn_reroute.py`).
- **Grid router** (`v2_route.py`) for the rest, net group by net group, then hand-finished.
- **Vias:** 213 in total.
  - 79 × 0.45/0.3 and 44 × 0.45/0.2.
  - **90 × 0.35/0.2**, the paid small-via option (see decisions). They are on every EXP net plus the crowded module and sideband nets.
- **Rules:** track/space 0.127 mm; hole-to-copper 0.2 mm (JLC inner-layer value); copper-to-edge 0.3 mm.
- **Gold fingers:** no copper between fingers; every GND finger is tied to the plane.

## Decisions taken during V3 (owner)

1. Test points: TP1/TP2 (EN/BOOT) kept, TP3–TP6 removed.
2. R5/R6, C8/C9, R7/R8 removed (DNP provisions + 0 Ω links); U1 connects straight to the module.
3. TI land patterns for U3–U5 (RSV) and U6 (RPW).
4. **Smaller vias: JLC "0.2mm/(0.3/0.35mm)"** — quote 2026-10-10:

   | Option | 100 pcs | 5 pcs |
   |---|---|---|
   | baseline | $156.80 | $48.80 |
   | with 0.35/0.2 vias | **$207.49** (+$0.51/board) | $85.39 |
   | 8 layers instead | $202.60 | +$149 engineering fee per order |

   The option adds a 4-wire Kelvin test and FR4 TG155. **It must be selected at order time.**
5. USBH3_D_N finger-9 via moved (+0.2 mm on a full-speed pair).
6. Silkscreen and branding: name on top, logo + version + "Designed in Italy" + samnium.tech on the back. Reference labels adjusted by you.

## Waivers and rule changes (please confirm)

| Item | Why |
|---|---|
| Hole-to-copper 0.25 → **0.2 mm** | JLC capabilities "Inner layer via hole to copper clearance 0.2mm" (checked 2026-10-10) |
| DRU `gnd_single_spoke_pads`: R28.2, C11.2, Q1.4, J1.21 may resolve to 1 thermal spoke | the three are via-backed; J1.21 has no room for a via at the 0.25 mm finger pitch |
| Rule areas `GND11_STRIP` / `GND11_BAND` (F.Cu, no tracks/vias) | keep GND finger 11's only pour path |
| 17 refdes hidden on silk | no legal 0.8 mm spot; all are in the assembly drawing |
| Pre-route gate tool | SPEC names `v2/probe/gridprobe.py`; it grew into `hardware/tools/v2_route.py` (same obstacle model). Gate evidence = `make drc`. |

## Open items for GATE V4 (fab)

1. **U6 RPW footprint vs TI's CAD model.** V2 asked for it from the CAD model; it was drawn from the
   datasheet land and stencil drawings, cross-checked against every labelled dimension.
2. **JLC rotations (`gen_fab.py` `JLC_ROT`)** for the new polarized parts U3–U6, Q1–Q3 and RN1–RN3,
   verified in JLC's placement preview (ORDER BLOCKED until dated).
3. **`fab/README.md` order settings for v2:**
   - 6 layers, stackup JLC06081H-2116
   - min via 0.2/(0.3/0.35)
   - ENIG, gold fingers, epoxy filled & capped vias
   - no bevel
4. **DATASHEET.md:** the v2 edge pins have no "Function" text yet (generator needs v2 descriptions).
5. 3D models of U3–U5 are a generated body box (no stock model) and U6 uses TI RUN0010A.
   Both are visual only.

## Amendment 2026-10-13 — side-view LEDs (after GATE B3) · awaiting owner review

- **Finding (JLC engineering, Rev B final DFM, physical parts):** the TJ-S1706 lens/electrode
  arrangement is the mirror image of our footprint. Correct polarity came with the lens inward.
- **Fix (owner-approved):**
  - footprint pads renumbered (cathode = pad at +x with the lens toward the emit arrow);
  - D3/D4 re-placed from the library at the same pose;
  - R3/R4 rotated 180°;
  - the three LED nets and their local plane vias re-routed;
  - CPL offset +180 → **+0**.
- **Checks:** `make drc` 0 violations / 0 unconnected; `make check` PASS. `polarity_report.py`
  asserts each LED's emit arrow points away from its resistor; the LED checklist rows ask for lens
  AND polarity.
- **Still to confirm:** lens + polarity in JLC's final DFM on the physical part (GATE V4).
- **Other directional parts in v2:** none. J3/J4 take the Rev B verified offsets (J4 +180).

