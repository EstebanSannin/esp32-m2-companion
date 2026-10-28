# LESSONS
- 2026-10-28 (v2 RC1 review mcu_io-1): check every card-side pull-up on a
  standard M.2 pin against the spec's range, not just "a pull-up exists":
  W_DISABLE# wants 100–200 kΩ on the card (§3.1.11.3); 1 MΩ let a host
  pull-down hold the FET off (false radio kill). R29 → 100 kΩ.
- 2026-10-28 (v2 RC1 review contract_test-1): a spare FET half + a pull-up
  on a reset-safe GPIO (IE-only, no pull, no power-up glitch) gives a free
  "held off until firmware says so" gate (Q3b on EXP_OE, IO38 + R35 100k).
  Use it whenever an enable must cover MCU reset and ROM boot.
