# Branding — silkscreen label

Bottom-side silk label placed in the top strip of the card (under the M.2
mounting hole, above C6/C7 — a component-free area).

- `logo_samnium_tech.png` — source logo (samnium.tech, `logo_samnium_tech_no_bg_no_name.png`,
  3167×1255, fetched 2026-08-30). Owner-supplied company logo.
- `gen_logo_silk.py` — crops the gear logomark (drops the wordmark), thresholds
  to 1-bit, emits `logo_silk_rects.json` (run-length silk rectangles, ~3.8×4 mm).
  Run: `uv run --no-project --with pillow python hardware/branding/gen_logo_silk.py`
- `logo_silk_rects.json` — committed so the silk is regenerable without Pillow.
- Applied to the board by `../tools/add_silk.py` (grouped as `silk_label`,
  idempotent — safe to re-run; never touches copper/routing).

Text lines: `ESP32-M2-COMPANION` / `v1.0  Stefano Viola` / `2026-08` (0.8 mm).

Note: the diagonal brand slash is ~0.1–0.15 mm at 3.8 mm — at silk's limit, may
print faint. The gear teeth and `</>` are above the 0.15 mm floor.
