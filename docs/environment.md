# Environment log

Machine: Stefano's Mac (Darwin 25.5.0, zsh) — note: SPEC §8 mentions server
`m920x`; this session actually runs on macOS. Flag if tooling must live on
m920x instead.

| Date | Tool / package | How | Why |
|---|---|---|---|
| 2026-08-28 | python3 3.9.6 + pypdf | pre-existing | datasheet text extraction |
| 2026-08-28 | `cryptography` (pip3 --user) | `pip3 install --user cryptography` | pypdf AES support (Quectel PDF is encrypted) |
| 2026-08-28 | poppler (pdftoppm/pdftotext) | `brew install poppler` | render PDF pages for visual inspection of mechanical drawings |

Network notes (this machine/sandbox):
- `st.com` and `mouser.com` downloads blocked → USBLC6 datasheet fetched from
  a mirror (UMW clone doc); see docs/datasheets/README.md.
- Waveshare wiki reachable via curl with browser UA (plain fetch gets 403).

Still to install (Phase 1): KiCad 9 + kicad-cli, atopile (or SKiDL), ESP-IDF.
