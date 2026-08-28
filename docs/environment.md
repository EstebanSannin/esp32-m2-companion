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

| 2026-08-28 | uv 0.9.x | `brew install uv` | python project/venv management |
| 2026-08-28 | KiCad 9.0.9 (kicad-cli + libs) | official DMG → `~/Applications/KiCad` (brew cask needs sudo → hand-install; SPEC pins v9, brew only has v10) | headless ERC/DRC/exports, symbol/footprint libs |
| 2026-08-28 | atopile 0.15.8 | `uv tool install atopile` | evaluated & REJECTED (ADR 0001); kept installed for reference |
| 2026-08-28 | skidl 2.3.0 + pypdf | `uv add` in hardware/ | schematic-as-code (ADR 0001), PDF merge |
| 2026-08-28 | node 26 + graphviz (incl. rsvg-convert) | `brew install node graphviz` | netlistsvg rendering, SVG→PDF |
| 2026-08-28 | netlistsvg | `npm install -g netlistsvg` | schematic-style SVG from netlists |

Still to install (Phase 4): ESP-IDF.
