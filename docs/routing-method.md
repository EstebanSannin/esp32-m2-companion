# Routing method — hard-won, do NOT repeat the rabbit hole

The v1 board's routing cost ~28 full autorouter runs over a night because of
a bad method, not a hard board. This document is the method to use from the
start next time (RP2350 sibling, any revision). It is a candidate rule for
the shared hardware-design skill (SPEC §12 PROCESS).

## The one-line lesson

**Route the hard/critical nets by hand ONCE and lock them; run the
autorouter ONCE for the easy nets; finish leftovers by hand WITHOUT
re-running the autorouter.** Never loop the global autorouter to chase
individual DRC violations.

## Why the rabbit hole happened

1. **Re-running freerouting for every fix.** Each run is ~12 min AND
   reshuffles all auto-routed nets, so it invalidated the previous hand-fix
   and created new collisions elsewhere. 28 × 12 min ≈ one wasted night.
   The per-fix feedback loop must be **seconds** (edit tracks → DRC), which
   means *not* re-invoking the autorouter.
2. **Guessing coordinates blind** instead of reading actual pad extents.
   A pad is 1.475 mm wide; "x99.0" looked between two parts but was *inside*
   a pad. Always read `pad.GetPosition()`/`GetSize()` and compute the real
   gap before placing a track.
3. **Silent edit drift.** Python `str.replace()` no-ops when the text has
   moved, so "fixes" silently didn't apply and I re-fixed non-problems. Use
   an editor that ERRORS on mismatch, or `assert old in text`, every time.
4. **Letting the autorouter use the plane layers.** freerouting treated
   In1(GND)/In2(+3V3) as signal layers and slotted them, leaving gaps.
5. **Over-constraining.** A 2 mm intra-pair skew assert fired on a USB-**FS**
   pair where 10 mm (≈67 ps) is invisible. Match effort to the signal.

## The efficient method (use this order)

### 0. Estimate congestion BEFORE choosing a method
- Card usable width minus the dominant component footprint = routing budget.
  Here: 22 mm card − 18 mm module ≈ 2 mm side strips + the module underside.
  That density means **plan for interactive routing of the dense corner from
  the start** — don't expect any autorouter to nail it.

### 1. Hand-route + LOCK the critical and congested nets, once
- USB/diff pairs, recovery straps, power entry, anything in a pinch point.
- Read pad coordinates from the board; compute gaps; place tracks; lock them
  (`track.SetLocked(True)`).
- For diff pairs: prioritise impedance continuity + solid reference, not
  length-matching, for FS/LS USB.

### 2. Run the autorouter ONCE, for the easy nets only
- Mark plane layers as power in the DSN so the autorouter can't slot them
  — BUT verify it can still route the remaining signals on 2 layers; if the
  board needs inner-layer routing, leave them signal and accept it. (On this
  board, forbidding inner layers left 67 nets unroutable — so here the inner
  layers ARE needed, i.e. it is not a clean SIG/GND/PWR/SIG board.)
- Use few passes (`-mp 5`) for "routed, not optimal"; high passes only for a
  final polish.
- Pre-routed locked tracks are exported as `(type fix)` and are respected.

### 3. Stitch power deterministically, don't rely on the autorouter
- Every SMD pad on a plane-only net (e.g. +3V3 on In2 with no outer pour)
  needs its OWN via to the plane. But place vias where they DON'T collide:
  check neighbouring pad extents; do NOT blindly offset a fixed distance
  (that shorted EN/USB pads here). Prefer via-in-pad on the pad itself
  (same net → no clearance issue; JLC fills it).

### 4. Finish leftovers by hand, NO autorouter re-run
- Load the routed board, add the few missing connections as locked tracks,
  re-pour, DRC. Iterate this in **seconds**. This is where convergence
  actually happens.

### 5. The genuinely impossible corner → interactive GUI
- A 0.5 mm-pitch, 3-conductor interleave where 2 conductors need
  layer-change vias (vias 0.6 mm > 0.5 mm pitch) cannot be placed blindly.
  On this board that was M.2 pins 7/8/9 (USB D+/W_DISABLE/USB D−). Route it
  in pcbnew interactively (fan the pair's vias apart a few mm south first),
  or accept it as an owner GUI task. Do NOT script-iterate it.

## Tooling notes (this repo)

- `hardware/tools/route.py`: `preroute_usb` + `preroute_fixups`/`more_fixups`
  (hand-routed locked tracks), `run_freerouting` (once), `pour_planes`.
- Regenerate placement: `tools/gen_pcb.py` (rebuilds board from netlist —
  **destroys routing**; only for pre-route placement changes).
- Once routing starts, switch to KiCad "Update PCB from netlist" for
  schematic tweaks so tracks survive.
- DRC headless: `kicad-cli pcb drc --severity-error ...`.
- Ratsnest count (real unrouted): `board.GetConnectivity().GetUnconnectedCount(True)`.
- Known-benign DRC on this board: 3 J1 footprint-internal artifacts
  (mounting-pad/keepout/silk polygons on the edge connector).
