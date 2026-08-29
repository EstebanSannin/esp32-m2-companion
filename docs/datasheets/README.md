# Datasheet provenance

All pin assignments in `docs/pinmap.md` trace to these files. Fetched
2026-08-28 unless noted.

| File | Source URL | Version | Used for |
|---|---|---|---|
| `mallow-carrier-board-datasheet.pdf` | https://docs.toradex.com/113873-mallow-carrier-board-datasheet.pdf | Mallow V1.1 datasheet | **Primary host.** M.2 X17 pin table (Table 10, pp. 15–17), X16 secondary extension header (Table 22, pp. 27–28), USB hub topology (§2.5.2), power rails (Table 4) |
| `esp32-s3-wroom-1_wroom-1u_datasheet_en.pdf` | https://www.espressif.com/sites/default/files/documentation/esp32-s3-wroom-1_wroom-1u_datasheet_en.pdf | v1.8 | Module pin definitions (Table 3-1, pp. 11–12), strapping pins (§4, pp. 13–14), variant comparison (Table 1-1, p. 3) |
| `esp32-s3_hardware_design_guidelines_en.pdf` | https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32s3/esp-hardware-design-guidelines-en-master-esp32s3.pdf | release `master` (rolling) | EN/CHIP_PU reset timing + RC (10 kΩ/1 µF) §1.3.3, decoupling & 4-layer power layout, antenna keep-out |
| `quectel_rm50xq_hardware_design_v1.2.pdf` | https://sixfab.com/wp-content/uploads/2022/05/Quectel_RM50xQ_Series_Hardware_Design_V1.2.pdf | V1.2 (2022-01-27) | **M.2 Key-B WWAN socket pinout reference** (Figure 2 p. 22, Table 8 pp. 23+). The PCI-SIG M.2 EM spec is paywalled; this is the canonical WWAN-card usage of the socket, cross-checked pin-for-pin against Mallow Table 10 |
| `usblc6-2sc6.pdf` | https://media.digikey.com/pdf/Data%20Sheets/UTD%20Semi%20PDFs/USBLC6-2SC6.pdf | UMW (友台) clone datasheet | USBLC6-2SC6 pinout/ratings. **NOT the ST original** — st.com and mouser.com are blocked from this machine. Pin-compatible; UMW part is itself an LCSC BOM candidate (C323793). Owner to supply ST original if ST part (LCSC C7519) is chosen |
| `waveshare_pcie-to-4g5g-m2-usb32-hatplus_wiki_snapshot.html` | https://www.waveshare.com/wiki/PCIe_TO_4G/5G_M.2_USB3.2_HAT+ | wiki snapshot | Secondary host (RPi5 HAT). **No board schematic is published.** Wiki confirms: 3042/3052 module support (no 2242 standoff mentioned), onboard reset button, SIM7600-M.2 (USB2-only modem) supported ⇒ USB 2.0 D+/D− wired to socket |

## Missing / unobtainable

- **TOGIALED TJ-S1706SW6T side-view LED drawing** — LCSC datasheet mirror
  blocks direct download from this machine. Needed at GATE 3 for the land
  pattern + emitting-face orientation (currently 0603 placeholder). Grab it
  from the LCSC product pages (C273612 / C273616) in a browser.

- **ST USBLC6-2 original datasheet** — st.com unreachable from here.
- **Waveshare HAT+ schematic** — not published; M.2 sideband wiring on that
  board is unknown (recovery there is best-effort per SPEC §10.6).
- **PCI-SIG M.2 (NGFF) electromechanical spec** — paywalled; mechanical
  card-outline data for Phase 2 will need a licensed copy or a derived
  reference (flagged for GATE 1).

## Added during Phase 2 (2026-08-28)

| File | Source URL | Used for |
|---|---|---|
| `amphenol_mdt420b01001_m2_socket.pdf` | via JLCPCB part page C4594496 (Amphenol ICC product brief) | Mallow's M.2 socket: ratings, durability. NOTE: no mating-card drawing — product brief only |
| `m2_em_spec_rev1.0_2013_archive.pdf` | archive.org copy (via timonsku/M.2-Card-Footprints README) of PCI-SIG "PCIe M.2 Electromechanical Spec Rev 1.0" (2013) | Card mechanical geometry: 2242 outline, gold-finger dimensions, notch position, bevel. Rev 1.0 (current spec is newer) — fine for mechanical card data; resolves risk R8 |
