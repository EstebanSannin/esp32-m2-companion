# Kick-off prompt — M.2 dev carrier (paste into a new session in the new repo)

---

Context: I'm designing a **development carrier board** for my ESP32-S3 M.2
Key-B companion card (repo `<workspace>/esp32-m2-companion`,
v2 work in the worktree `<workspace>/esp32-m2-companion-v2`).
I'm an experienced embedded engineer; talk to me as a peer, be concise, ask
when something is ambiguous instead of guessing.

## Goal

A **cheap, simple dev/test carrier**:
- An M.2 Key-B socket that takes the companion card.
- USB-C to power the card, flash it and talk to it.
- Every pin the v2 card uses brought out to **2.54 mm pin headers** that I
  solder by hand.
- It also doubles as the **v2 host-safety test fixture**: the carrier-signature
  pins are jumper-selectable, so I can prove the card's expansion switch
  stays OFF when it sees a "foreign host".

It must work with **all card revisions**:
- v1.0 / Rev B: no expansion bus, CONFIG pins NC.
- v2.0 Rev A, in design: expansion bus + CONFIG state 6.

Nothing on the carrier may harm a Rev-B card.

## Read first (read-only — never edit files in the companion repos)

- `<workspace>/esp32-m2-companion/CLAUDE.md` and `SPEC.md` —
  my workflow (SPEC as contract, GATEs, findings log, LESSONS per block,
  naming rules). Reuse the same methodology and tooling here.
- `<workspace>/esp32-m2-companion/docs/pinmap.md` — Rev-B M.2
  pinout (§1) and the BOOT/EN sideband scheme (§3).
- `<workspace>/esp32-m2-companion/docs/routing-method.md` and
  `hardware/blocks/*/LESSONS.md` — layout lessons (most of them are
  board-independent).
- `<workspace>/esp32-m2-companion-v2/v2/edge-expansion-brainstorm.md`
  — the v2 edge-bus design. Must-read sections:
  - §5–§6: signature logic and carrier design rules
  - §11: research results
  - §14: decisions
  - `v2/research/m2_pins_research.md` for what every Key-B pin means on
    real hosts.
- `<workspace>/esp32-m2-companion-v2/docs/decisions/0006-*.md`,
  `0007-*.md`, `0008-*.md` — the v2 decisions behind the contract.
- Toradex Mallow datasheet (`docs/datasheets/` in the companion repo) as a
  reference host design for the M.2 Key-B socket.

## Pin contract — authoritative source

**`<workspace>/esp32-m2-companion-v2/docs/carrier-interface.md`**
is the contract (card revisions, mechanics, power, every edge pin, the
carrier-signature logic, the EXP_0..11 mapping, carrier design rules).

- Put this line in this repo's `CLAUDE.md` so every session loads it:
  `@<workspace>/esp32-m2-companion-v2/docs/carrier-interface.md`
  (after v2 merges, the path becomes `…/esp32-m2-companion/docs/carrier-interface.md`).
- Rely only on items marked **fixed**.
- Items marked *proposed* (EXP → ESP GPIO table, ID EEPROM format) may
  change. Design so they don't matter: label headers by M.2 pin number + EXP
  name, never by GPIO.
- If the contract is unclear or insufficient for a design decision, **stop
  and tell me what's missing**. Don't fill the gap from memory. Improving the
  contract is part of this exercise.

Dev-carrier specifics on top of the contract:

| M.2 pin(s) | Dev carrier does |
|---|---|
| 2, 4, 70, 72, 74 | 3.3 V from the on-board regulator, or from the bench-supply input via jumper (see Power) |
| 7 / 9 | USB-C D+ / D− |
| 50 | RESET button to GND + header pin |
| 20 + 8 | BOOT button to GND on both + header pins |
| 21, 69 | 100 k pull-ups to 3V3 + header pins (read the card type: v2 = both low) |
| 75, 1 | **per pin jumper:** GND (our carrier, default) / open / 10 k to 1.8 V / 10 k to 3.3 V — the host-safety test. Needs a small 1.8 V reference |
| EXP_0..11 (30, 32, 34, 36, 40, 59–65) | straight to 2.54 mm headers |
| 10 | LED + resistor to 3V3 + header pin |
| 23 | 10 k pull-up to 3V3 + header pin (+ optional LED) |
| 26 | jumper/switch to GND + header pin |
| all others | NC |

## Board requirements

- **Outline:** Raspberry Pi 4/5 size **85 × 56 mm**, the same **4 × M2.5
  mounting holes** (58 × 49 mm pattern) and corner radius. Verify against the
  official Raspberry Pi mechanical drawing; don't trust memory.
- **M.2 Key-B socket:**
  - JLC/LCSC stocked, height chosen so the card's **bottom-side components**
    clear the carrier.
  - The Rev-B card has parts on both sides; measure from its 3D/STEP in
    `docs/3d/` of the companion repo.
  - No carrier components under the card.
- **Standoffs:** card lengths **2242, 2252 and 2260**. An SMT/press-fit M.2
  standoff/nut at each position (or one + footprints for the others). The
  screw keeps the card down.
- **Power:**
  - USB-C 5 V → 3.3 V regulator. Prefer a JLC Basic part. Size it for the
    card: ESP32-S3 WiFi bursts ~0.5 A, v2 eFuse current limit ~1 A.
  - Power LED.
  - **Test option:** a jumper that disconnects the regulator from the M.2
    3.3 V pins and feeds them from a screw/2-pin bench-supply input instead.
    This is for testing the v2 overvoltage protection (trips 3.44–3.57 V) and
    brown-out.
  - Default position = regulator. Big silkscreen warning: Rev-B cards have
    NO overvoltage protection, so never exceed 3.6 V with a Rev-B card
    inserted.
- **USB-C:**
  - USB 2.0 receptacle (16-pin), CC 5.1 k pull-downs (sink), D+/D− straight
    to M.2 7/9.
  - The card already has a USBLC6 ESD array; decide whether the carrier
    needs its own (cheap TVS on VBUS at least).
- **Headers:**
  - 2.54 mm, THT, hand-soldered (not assembled by JLC).
  - GND pins interleaved, 3V3 and 5V available.
  - Every pin silkscreened with M.2 pin number + net name.
- **Buttons:** RESET (PERST#) and BOOT. Recovery flow = hold BOOT, tap RESET.
- **Carrier ID EEPROM:** DNP footprint, wired per the contract's *proposed*
  §4.3 (24C02 @ 0x50 on EXP_0/EXP_1). Add jumpers or 0 Ω links so it can be
  disconnected if the proposal changes.
- **Fab:**
  - JLCPCB, 2 layers, 1.6 mm, HASL OK (no gold fingers on the carrier).
  - JLC SMT assembly for the SMD parts; Basic parts strongly preferred.
    Every Extended part needs a one-line justification.
  - Headers and jumpers hand-soldered.
  - Target: as cheap as possible. Give me a cost estimate (5 pcs) at GATE 1.

## Process (same as the companion)

1. **Bootstrap the repo.** In this new directory create:
   - `CLAUDE.md` (adapted from the companion's)
   - `SPEC.md` (this prompt turned into a contract, with GATEs)
   - `docs/`, `hardware/` with uv + SKiDL 2.3, KiCad 9.0.9, `make check` / `make drc` / `make fab`

   Reuse the companion's tooling where it applies; copy it, don't link it.
   → **GATE 0: I review SPEC.md.**
2. **Datasheets + pinmap + BOM** (LCSC #, Basic/Extended, stock), board
   outline/hole positions verified against the RPi drawing, M.2 socket and
   standoff choice, cost estimate. → **GATE 1.**
3. **Schematic** (SKiDL, ERC clean, every net named, `make sch` PDF). → **GATE 2.**
4. **Layout** (2-layer, DRC clean via `make drc`, routing method from the
   companion's `docs/routing-method.md`, silkscreen review). → **GATE 3.**
5. **Fab package + polarity checklist** (`make fab`). → **GATE 4.**

Rules:
- Never cross a GATE without my explicit OK.
- Never trust memory for pinouts, footprints or mechanical dimensions — cite
  a datasheet stored in `docs/datasheets/`.
- Log findings at each gate in `docs/review-findings.md` (append-only).

**Questions I already answered:**
- Test-fixture jumpers: yes.
- Headers: v2 set + sidebands.
- Pi 4/5 full size.
- Standoffs 2242/2252/2260.

**Ask me anything else before GATE 0.**
