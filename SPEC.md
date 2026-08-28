# ESP32-S3 M.2 Companion Card — Project Specification (v1.0)

Project codename: `esp32-m2-companion`
Owner: Stefano · Design agent: Claude (Claude Code session)
Status: spec frozen for v1 — changes require owner approval

---

## 1. Concept

A small M.2 Key-B 2242 card carrying an ESP32-S3 module, acting as a
**companion microcontroller** for embedded Linux hosts. The host talks to it
over the USB 2.0 lines available on the M.2 connector; the card offloads
realtime / GPIO / sensor work the Linux side is bad at. WiFi/BLE come for free
from the module.

Design philosophy: **hardware-as-code**. Schematic captured in a code-based
tool, verified with headless ERC/DRC, versioned in git, reviewed by the owner
at defined gates before any money is spent.

## 2. Goals (v1)

- G1. Enumerate as a USB CDC device on the host immediately after insertion.
- G2. Firmware fully replaceable **from the host**, including recovery of a
  bricked card, with no physical button access.
- G3. Expose usable IO on a card-edge header: GPIO, I2C, UART, SPI-capable pins.
- G4. Status LED controllable from firmware + power indicator LED.
- G5. WiFi/BLE functional via the module's integrated antenna (best-effort in
  v1: correct keep-out and placement, no formal RF validation).
- G6. Fully assembled by JLCPCB (SMT service); owner only plugs it in.
- G7. Reusable block structure so a radio-less RP2350 sibling card can be
  derived later by swapping only the MCU block.

## 3. Non-goals (v1)

- No PCIe, no SATA, no SIM interface.
- No battery, no external power input: card is powered only from M.2 3.3V.
- No RF certification work, no antenna tuning.
- No enclosure / thermal design.
- No level shifting beyond 3.3V IO (hosts with 1.8V GPIO banks interact via
  USB, not via the header).

## 4. Target hosts

| Host | Slot | Status |
|---|---|---|
| Toradex Mallow carrier (Verdin family) | On-board M.2 Key-B, 30/42/52 mm cards, intended for modems | Primary target. **Verify from datasheet** which pins carry USB 2.0 and which sideband signals (W_DISABLE#, RESET#, FULL_CARD_POWER_OFF#, …) are wired to SoM GPIOs. Datasheet: https://docs.toradex.com/113873-mallow-carrier-board-datasheet.pdf |
| Raspberry Pi 5 + third-party Key-B modem HAT (e.g. Waveshare "PCIe to M.2 4G/5G + USB 3.2 HAT") | Key-B slot with USB wired (modem slot) | Secondary target. Official RPi M.2 HAT+ is M-key/PCIe-only → NOT compatible, document this clearly in README. **Verify** the chosen HAT provides USB 2.0 (not only USB 3) on the socket and has a standoff position at 42 mm. |

## 5. Form factor & fabrication constraints

- M.2 module, **Key B**, size **2242** (22 × 42 mm), single-sided component
  placement on top preferred (bottom side allowed for passives if needed —
  check socket clearance class in M.2 spec).
- PCB thickness **0.8 mm** (M.2 requirement — not 1.6 mm!).
- Edge connector: gold fingers per M.2 spec geometry, **ENIG/hard-gold finger
  option + 45° edge bevel** must be selected at JLCPCB order time. Confirm
  JLCPCB supports gold fingers on 0.8 mm 4-layer — adjust stackup if not.
- Layer count: 4 layers (SIG / GND / PWR / SIG) — makes USB diff-pair
  referencing and RF keep-out trivial; cost difference at JLCPCB is small.
- Design rules: JLCPCB standard capability (≥ 5/5 mil trace/space to be safe,
  ≥ 0.3 mm drill, their published rules imported into KiCad as DRC profile).
- All components chosen from **LCSC catalog**, preferring JLCPCB **Basic
  parts**; every Extended part must be flagged in the BOM with justification.
- Card mounting notch centered at top edge per M.2 mechanical drawing.

## 6. Hardware architecture

### 6.1 MCU
- **ESP32-S3-WROOM-1-N8R2** (8 MB flash, 2 MB PSRAM). If N8R2 has poor LCSC
  stock, N8 or N16R8 acceptable — flag for approval.
- Module PCB antenna located at the **top card edge** (away from the M.2
  connector), with copper/ground keep-out under the antenna area per
  Espressif's hardware design guidelines. Antenna may overhang the 42 mm edge
  only if the mounting standoff geometry still works — otherwise inboard with
  keep-out.

### 6.2 Power
- 3.3V taken directly from M.2 3.3V rail (rated for modem-class loads —
  budget ≥ 1 A available; ESP32-S3 WiFi TX bursts ~500 mA peak).
- **No regulator in v1.** Input filtering: ferrite bead or 0Ω + bulk
  (≥ 2 × 22 µF ceramic or 47–100 µF) + per-pin 100 nF decoupling per
  Espressif guidelines.
- Power LED (green) on 3.3V rail with suitable series resistor.

### 6.3 USB
- M.2 USB 2.0 D+/D− routed directly to ESP32-S3 native USB pins
  (GPIO19/GPIO20). Pin numbers of USB on the Key-B edge connector must be
  taken from the **M.2 specification pinout, verified against the Mallow
  datasheet** — never from memory.
- 90 Ω differential pair routing, length-matched, solid ground reference,
  no stubs. USB-FS (12 Mbps) is forgiving but do it properly.
- ESD protection: USBLC6-2SC6 or equivalent LCSC-stocked TVS array on D+/D−,
  placed close to the edge connector.

### 6.4 Host-controlled recovery (critical requirement)
- ESP32-S3 **EN** and **GPIO0 (BOOT)** each wired to an M.2 sideband pin
  (candidates: RESET#, W_DISABLE1#, FULL_CARD_POWER_OFF# — final choice
  driven by what Mallow actually wires to SoM GPIOs and what the RPi HAT
  exposes; document the mapping).
- Sideband inputs treated as open-drain with on-card pull-ups to 3.3V, so an
  unconnected sideband = normal boot. RC on EN per Espressif reset timing.
- Resulting recovery flow (document in README):
  `host gpioset BOOT=0, pulse EN` → ROM bootloader → `esptool.py` over the
  same USB → flash → release. Normal flow: esptool auto-reset over
  USB-Serial-JTAG, no GPIO needed.

### 6.5 Status LED
- One firmware-controlled LED on a module GPIO (active-low, series resistor).
  Optional (owner may approve): WS2812B-2020 instead, single data GPIO.

### 6.6 IO header
- 2.54 mm pitch, single row, along the long card edge (top side), **unpopulated**
  (JLCPCB assembles SMD; owner can solder a header when needed — or select
  their through-hole assembly if trivial).
- Signals (~12 pins): 3.3V, GND, 1× I2C (SDA/SCL with footprints for optional
  pull-ups, DNP by default), 1× UART (TX/RX), 4–6 × GPIO chosen so that at
  least one full SPI set is available among them. Choose GPIOs avoiding
  strapping pins and octal-PSRAM-reserved pins (GPIO35-37 on R8 variants —
  check per chosen module variant).
- Silkscreen label every pin.

### 6.7 Things deliberately absent
- No USB-C debug connector (host USB is the debug port). If layout has spare
  room, test points for EN/BOOT/TX/RX/3V3/GND are welcome.

## 7. Firmware (v1 bring-up)

ESP-IDF (latest stable) project in `firmware/`:
- USB CDC console (USB-Serial-JTAG) with a trivial command shell:
  `led on|off|blink`, `gpio read|write <n>`, `i2cdetect`, `info` (chip ID,
  reset reason, firmware version).
- Blink task on the status LED as heartbeat.
- WiFi station connect + `ping` demo behind a config flag (proves radio).
- Makefile/justfile targets: `build`, `flash` (esptool over /dev/ttyACMx),
  `recover-flash` (gpioset sequence documented per host).

## 8. Toolchain & environment

- Work happens on the owner's server (`m920x`), account already provisioned.
  Claude may install tools (apt/pip) as needed — keep an
  `docs/environment.md` log of everything installed.
- **KiCad 9** + `kicad-cli` for headless ERC/DRC/exports.
- Schematic-as-code: **atopile** preferred; fall back to **SKiDL** if atopile's
  component/footprint availability blocks progress. Decision documented in
  `docs/decisions/0001-hdl-tool.md` (keep ADRs for major choices).
- Layout: interactive work is the owner's; Claude prepares placement
  suggestions, net classes (USB diff pair 90 Ω), DRC profile, and reviews the
  routed board by parsing the `.kicad_pcb` file.
- JLCPCB DRC rule set imported; CI (even a simple `make check`) runs
  ERC + DRC + BOM-vs-LCSC availability check on every commit.
- Outputs for ordering: Gerbers (JLCPCB naming), drill files, BOM (LCSC part
  numbers), CPL/pick-and-place, assembly drawings.

## 9. Workflow & review gates

Claude works autonomously **within a phase**, stops at every gate for owner
review. Never proceed past a gate without explicit approval.

- **Phase 0 — Groundwork.** Fetch and store in `docs/datasheets/`: Mallow
  datasheet, ESP32-S3-WROOM-1 datasheet, ESP32-S3 hardware design guidelines,
  M.2 (NGFF) Key-B pinout reference, USBLC6 datasheet, candidate RPi5 HAT
  wiki/schematic. Produce `docs/pinmap.md`: full M.2 edge-pin table (pin,
  M.2 spec function, Mallow wiring, our usage) + ESP32-S3 pin allocation
  table (pin, function, strapping notes). → **GATE 1: owner reviews pinmap.**
- **Phase 1 — Schematic-as-code.** Implement blocks: `m2_connector`, `power`,
  `usb_esd`, `mcu`, `recovery`, `leds`, `header`. ERC clean. Netlist + BOM
  (all LCSC-resolved) + human-readable schematic PDF export.
  → **GATE 2: owner reviews schematic + BOM.**
- **Phase 2 — Layout.** Claude: board outline with exact M.2 2242 mechanical
  geometry + gold-finger footprint, placement proposal, net classes, DRC
  profile. Owner routes / adjusts in KiCad GUI; Claude reviews the result
  (DRC, diff-pair check, antenna keep-out check, silkscreen review).
  → **GATE 3: owner approves layout.**
- **Phase 3 — Fab package.** Gerbers/BOM/CPL, JLCPCB order checklist
  (0.8 mm, 4-layer, gold fingers + bevel, assembly side, part substitutions).
  → **GATE 4: owner places order.**
- **Phase 4 — Firmware & bring-up plan.** Firmware ready before boards
  arrive; `docs/bringup.md` = step-by-step first-power checklist (visual
  inspection, resistance checks on 3.3V, first insertion in Mallow, dmesg
  expectations, flash, LED, I2C scan, WiFi test).

## 10. Success criteria

1. Card inserted in Mallow → host `dmesg` shows Espressif USB-Serial-JTAG
   CDC device.
2. `esptool.py` flashes firmware over that port.
3. Bricked-firmware simulation (flash garbage) → recovered purely via host
   GPIO sequence + esptool.
4. Status LED heartbeat; `i2cdetect` finds a sensor wired to the header.
5. WiFi demo connects to an AP.
6. Same result on RPi5 + chosen Key-B HAT (best effort).

## 11. Known risks / open questions (track in `docs/risks.md`)

- R1. Mallow B-key USB wiring & sideband→SoM GPIO mapping unconfirmed until
  datasheet is read. (Blocks pinmap.)
- R2. JLCPCB gold fingers + bevel on 0.8 mm 4-layer: confirm capability/cost.
- R3. Antenna performance flat against a carrier board: accepted risk in v1.
- R4. 2242 card mechanical fit in 3042-oriented RPi HATs (standoff position).
- R5. GPIO choice vs. octal-PSRAM reservations on the exact WROOM variant.

## 12. Knowledge management (added 2026-08-28, owner)

1. `docs/review-findings.md` is an **append-only** log. Every finding from any
   review gate — owner's, an external senior HW designer's, or self-caught —
   gets one entry: date, phase, finding, severity, and a classification:
   - **BLOCK**: bug/improvement in a reusable circuit block → fix the block
     source and add a line to that block's `LESSONS.md`
   - **PROCESS**: workflow/tooling/fab gap → flag to owner as a candidate rule
     for the shared hardware-design skill
   - **PROJECT**: specific to this board → note it in `CLAUDE.md`
2. Schematic sources are organized as self-contained reusable blocks
   (`m2_keyb_edge`, `esp32s3_companion`, `usb_esd`, `power_3v3`, `leds`,
   `io_header`) — each block in its own directory with sources, datasheet
   references, and a `LESSONS.md` (empty is fine; the file must exist). At
   project end, stable blocks are promoted to a shared hw-blocks repo.
3. `CLAUDE.md` stays current with project conventions: net names follow the
   M.2 / Verdin datasheet naming verbatim, tool choices, DRC profile, gate
   protocol.
4. When the owner relays findings from an external senior designer review,
   their categorization ("wrong" / "works but unprofessional" / "fragile at
   scale") is preserved in the log — never flattened.

---

# Kickoff prompt for the Claude Code session

Copy-paste the following as the first message (with SPEC file placed in the
repo root as `SPEC.md`):

```
You are the hardware design engineer for this project. Read SPEC.md fully
before doing anything — it is the contract; do not deviate from it without
asking me.

Context: we are designing an M.2 Key-B 2242 card with an ESP32-S3 acting as
a USB companion MCU for embedded Linux hosts (details in SPEC.md). I am an
experienced embedded engineer; talk to me as a peer, be concise, and
challenge the spec if you find a real problem in it.

Ground rules:
1. Work phase by phase as defined in SPEC.md §9. STOP at every GATE and ask
   for my review. Within a phase, work autonomously.
2. Never trust memory for pinouts, footprints or electrical values. Every
   pin assignment must be traceable to a datasheet stored in
   docs/datasheets/. If a document can't be fetched, tell me and I'll
   provide it.
3. Everything in git: small commits, meaningful messages. Record notable
   choices as short ADRs in docs/decisions/.
4. You may install any tools you need on this machine (KiCad 9, kicad-cli,
   atopile, skidl, esp-idf, python packages). Log installs in
   docs/environment.md.
5. Every BOM line must carry an LCSC part number and Basic/Extended status.
6. After any change to schematic sources, run ERC headlessly and show me
   the result. Set this up as `make check` early.
7. If you are uncertain between two design options, present both with a
   recommendation instead of silently picking one.

Start now with Phase 0: create the repo skeleton, fetch the datasheets
listed in SPEC.md §9 Phase 0, and produce docs/pinmap.md for GATE 1 review.
```
