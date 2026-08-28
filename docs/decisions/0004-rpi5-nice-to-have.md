# ADR 0004 — RPi5 host demoted to nice-to-have

Date: 2026-08-28 · Status: **accepted** (GATE 1, owner)

SPEC §4 listed RPi5 + Waveshare Key-B HAT as secondary target; owner demoted
it to **nice-to-have** (no design decision may be blocked by it, no dedicated
hardware provisions beyond what Mallow needs). Rationale: the Waveshare
"PCIe TO 4G/5G M.2 USB3.2 HAT+" officially fits 3042/3052 only, publishes no
schematic, and its sideband wiring is unknown (docs/risks.md R4).

What survives for RPi5 compatibility at zero cost: standard Key-B pinout
usage, USB 2.0 on pins 7/9, EN/BOOT/UART0/3V3/GND test points for flying-lead
recovery, diode isolation making unknown sideband drivers safe.

SPEC success criterion 6 ("same result on RPi5") is now best-effort.
