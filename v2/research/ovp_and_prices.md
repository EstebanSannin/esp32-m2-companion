# 3V3/VBAT overvoltage protection options + price check (2026-10-07)

Sources: JLCPCB parts API (`selectSmtComponentList`, `componentLibraryType` base=Basic / expand=Extended),
LCSC `wmsc` product API (cross-check), datasheets fetched as PDF and grepped (TI tps25947, tps2595,
tps2596, tlv758p, tlv755p; Awinic AW329xx via LCSC; local ESP32-S3-WROOM-1 v1.8).
Prices are USD JLC assembly unit prices on 2026-10-07; stock moves daily.

## Constraints (verified)
- ESP32-S3-WROOM-1 v1.8 Table 6-1: VDD33 abs max **3.6 V**; Table 6-2: recommended **3.0–3.6 V**,
  supply must deliver **≥ 0.5 A**.
- Current series element: FB1 GZ2012D101TF (C1015) DCR **150 mΩ** (JLC param) → 75 mV at 0.5 A.
  Budget today at a 3.135 V host: 3.135 − 0.075 = 3.06 V at the module. Any extra series element
  must stay under ~60 mV at 0.5 A (i.e. ≤ ~120 mΩ) unless FB1 is removed/replaced.
- M.2 3.3 V nominal max 3.465 V (3.3 V +5 %); ESP max 3.6 V → an OVLO trip window must sit inside
  3.465–3.6 V (±1.9 %) to be both nuisance-free and fully protective. Only a tight-reference part
  can approach that.

## A) eFuse / OVP switch (cut-off) — RECOMMENDED family

| Part | LCSC | Type | Pkg | Stock | @10 | @100 | OV mechanism (datasheet) | RON (datasheet) |
|---|---|---|---|---|---|---|---|---|
| **TPS259470ARPWR** (auto-retry, FLT/AUXOFF) | C3662799 | Ext | VQFN-10 2×2 | 1215 | 1.055 | 0.797 | Adjustable OVLO pin, VOV(R) 1.183/1.20/1.223 V, falling 1.09 V, tOVLO 1.2 µs | 28.2 mΩ typ; **45 mΩ max** (2.7–23 V, −40..125 °C) |
| TPS259474LRPWR (latch on OC, PG/PGTH) | C2864845 | Ext | VQFN-10 2×2 | 3611 | 1.06 | 0.789 | same OVLO | same |
| TPS259470LRPWR | C3662793 | Ext | VQFN-10 2×2 | 2664 | 1.192 | 0.899 | same OVLO | same |
| TPS259472LRPWR (OVC clamp) | C2870148 | Ext | VQFN-10 2×2 | 92 | 1.43 | 1.09 | OVCSEL=GND: VOVC 3.65–4.1 V, Vclamp 3.2–4.2 V | same |
| TPS259521DSGR (3.8 V clamp) | C882749 | Ext | WSON-8 2×2 | 2850 | 0.558 | 0.418 | fixed OVC: VOVC 3.65/3.87/4.1 V, VCLAMP **3.4/3.6/3.8 V** | 36 typ / 51 (85 °C) / 58 mΩ max at VIN 2.7–4 V |
| TPS259573DSGR (EN/OVLO, active-low EN) | C2653844 | Ext | WSON-8 2×2 | 129 | 0.564 | 0.437 | adjustable OVLO, VOVLO 1.13/1.20/1.27 V (±5.8 %) | as above |
| AW32901FCR (Awinic) | C407920 | Ext | FCQFN-12 1.3×1.8 | 4180 | 0.325 | 0.274 | default OVP 5.95 V; OVLO pin adjustable **4–20 V only** | 27 typ / 37 mΩ max @5 V |
| TPS259631DDAR | C2155778 | Ext | SO-8 PowerPAD | 4330 | 0.587 | 0.441 | adjustable OVLO | 89 mΩ typ (too big a package / RON) |

Rejected in A:
- **TPS2595x3 (TPS259573)**: OVLO reference ±5.8 % → with 1 % divider set to 3.55 V the window is
  ~3.32–3.79 V: can both nuisance-trip on a 3.35 V host and let 3.79 V through. Also only 129 in stock.
- **TPS25952x / TPS259472 clamp**: VCLAMP max 3.8 V (TPS2595) / 4.2 V (TPS25947) exceeds 3.6 V abs max,
  and TI (TPS2595 §8.3.2.2 + abs-max note 1) says nominal input should be limited to the clamp voltage;
  sustained clamping heats the FET and can end in thermal shutdown. Not a design for a legit 4.4 V host.
- **AW32901 & other phone OVP switches** (AW329xx family): adjustable OVLO floor is 4 V (datasheet:
  "OVP threshold adjustable range: 4V to 20V"); UVLO rising 2.9–3.0 V, VIN min 3 V. 4 V > 3.6 V → useless here.
  AW35206 (C5125877): plain load switch, no OVP.
- **AP22802 (C211404), RT9742 (C250547 etc.), SGM2554 (C183309), SY6288 (C111830), AP2192**: current-limited
  USB power switches, UVLO only, no OVP (JLC params / descriptions; datasheets not fetched — unverified
  beyond "no OVP feature listed").
- TPS25921 (VIN min 4.5 V) — can't run from 3.3 V. TCKE805/TCKE712 — no stock.

### Recommended circuit (TPS259470ARPWR, alt. TPS259474LRPWR same footprint)
- IN = M.2 3.3V/VBAT pins; OUT = module 3V3 (before/after FB1).
- EN/UVLO tied to IN (recommended EN ≤ 5 V, abs max 6.5 V — OK up to a 5 V mistake; for > 5 V use
  a divider). Internal IN UVP 2.44–2.64 V rising, fine at 3.135 V.
- OVLO divider IN→OVLO→GND: **Rtop 100 kΩ (C25741, Basic) / Rbot 51 kΩ (C25794, Basic)**, 1 %:
  trip (rising) typ 3.553 V, worst-case 3.457–3.670 V (ref ±1.7 % + 1 % resistors). Release (falling,
  1.09 V ref) typ ~3.23 V. Pin leakage ±0.1 µA × 34 kΩ = 3.4 mV, negligible. 0.1 % resistors (Extended)
  would tighten it to ~3.47–3.63 V. No Basic E24 pair centres better (200k/100k → 3.60 V typ, too high).
- ILM: 3.3 kΩ (C25890, Basic) → ILIM 0.85/1.007/1.15 A (datasheet row RILM = 3.32 kΩ); transients
  up to 2×ILIM are allowed before action, so 0.5 A WiFi bursts are well clear.
- DVDT open (fastest), ITIMER open (fastest OC response), FLT/AUXOFF (or PG/PGTH on the 474 —
  PGTH termination per §7.3.11, not checked) left open / not used. CIN 100 nF.
- Drop at 0.5 A: 14 mV typ, **22.5 mV max** → module sees ≥ 3.135 − 0.0225 − 0.075 (FB1) = **3.04 V**
  worst case. OK.
- Back-to-back FETs → reverse blocking (datasheet).
- Fault behaviour (datasheet Table 7-3): input overvoltage → shutdown, **not latched** → output returns
  automatically when VIN drops below the OVLO falling threshold. Abs max IN 28 V → survives 5 V and more.
- **On a 4.4 V VBAT host: card stays OFF safely** (ESP unpowered, no USB enumeration), nothing damaged;
  comes back by itself if the rail returns to 3.3 V. (Sideband/USB lines from a powered host into an
  unpowered ESP are a separate back-powering concern — this is what the TMUX1511 isolation addresses.)
- Cost: IC $0.80 @100 / $1.06 @10; 3 resistors + 1 cap ≈ $0.013. **≈ $0.81/board @100, $1.07 @10.**
  New BOM lines: IC (Extended) + 100k, 51k, 3.3k (the BOM is 0603 today; any value not already present
  is a new line) → up to 4 new lines × ~€1.38 ≈ €5.5 per order (+ JLC's per-order Extended-part loading
  fee — not re-verified in this pass).
- Area: VQFN-10 2×2 mm + 3 resistors + 1 cap ≈ **4×4 mm (~16 mm²)** placed.

## B) LDO — fails the 3.135 V corner and/or 0.5 A limit
- Best candidate found: **TLV75801PDBVR** (C2877852, Ext, SOT-23-5, stock 163 978, $0.090 @10 / $0.071 @100).
  Datasheet: VIN 1.5–6.0 V (abs 6.5 V), dropout at 500 mA, −40..125 °C, Vout ≥ 3.3 V: **95 typ / 130 mV max**;
  **current limit ICL 530 / 720 / 865 mA** (min/typ/max).
- Fixed 3.3 V TLV75533P (C404027, $0.113 @100): dropout 238 mV @ 500 mA (JLC param) — worse.
  RT9080-33 (C841192): 360 mV @ 600 mA; ME6211C33 (C82942): 120 mV @ 100 mA (→ ~0.5 V @ 500 mA);
  XC6220B331MR (C3040644): 400 mV @ 800 mA; AP7361C (C500795, SOT-223): 340 mV @ 1 A. (JLC params, unverified.)
- Quantified at 3.135 V in, 0.5 A, 100 mV dropout: LDO out ≈ 3.035 V; minus FB1 (75 mV) → **2.96 V**
  (below 3.0 V rec. min). With TLV758P max dropout 130 mV and FB1 removed: **3.005 V** — zero margin, and
  0.5 A is only 30 mA under the 530 mA min current limit.
- An LDO **set to 3.0 V** is not acceptable: ±1–2 % accuracy puts it at ~2.94–2.97 V, below the 3.0 V
  WROOM-1 recommended minimum; 3.1 V setpoint still drops into dropout at a 3.135 V host anyway.
- Upside: on a 4.4 V host it *regulates* (card works); dissipation 1.1 V × 0.1 A avg = 0.11 W, 0.55 W during
  TX bursts (SOT-23-5 thermal not checked). Survives 5 V (6.0 V operating).
- Verdict: cheapest and keeps working at 4.4 V, but violates ESP min voltage / current spec at the
  low-host corner. Reject unless spec relaxation (e.g. host rail ≥ 3.25 V guaranteed) is accepted.

## C) Crowbar / clamp (TVS or zener + PTC/fuse) — not acceptable
- 4.4 V is a *legitimate* VBAT host rail: any clamp low enough to protect the ESP (< 3.6 V) would
  conduct amps from a healthy host rail → host OCP trip, battery drain, or PTC/fuse trip and thermal
  stress on a 22×42 mm card. PTCs take 0.1–seconds to trip and still leave the rail at clamp voltage.
- Real TVS parts don't fit anyway: SMBJ3.3A (e.g. C362089, $0.049): standoff 3.3 V, breakdown ~4.1 V,
  clamp 7.3 V @ Ipp, leakage 100 µA–2 mA at 3.3 V depending on vendor (JLC params). Zeners at 3.6 V have a
  soft knee — they leak mA at 3.3 V and don't hold 3.6 V at amps.
- A one-shot fuse would turn a correct-but-unexpected host into a dead card.

## D) Buck-boost — works, costs more area
- TPS63802DLAR (C2845237, Ext, VSON-10 2×3, stock 16 545, $0.813 @10 / $0.615 @100): 1.3–5.5 V in,
  regulated 3.3 V out, 2 A (JLC params; datasheet not fetched). TPS63020DSJR (C15483, VSON-14 3×4,
  $0.79 / $0.60). + 0.47–1 µH inductor (~$0.05–0.15) + 3–4 caps + FB divider.
- Area ~35–50 mm², switching noise next to the antenna keep-out, extra 4–6 BOM lines. Card *works* at
  4.4 V. VIN 5.5 V max → a 5 V mistake is at the edge, not reliably survivable without an OVP in front.
- Only worth it if "works on 4.4 V VBAT hosts" becomes a requirement.

## Recommendation
**A: TPS259470ARPWR (C3662799)** — or the pin/footprint-compatible TPS259474LRPWR (C2864845, more stock)
— with 100k/51k OVLO divider and 3.3k ILM. ~$0.81/board @100 (~$1.07 @10), ~16 mm², ≤ 22.5 mV extra
drop at 0.5 A, survives 28 V. Behaviour on a 4.4 V host: **stays off safely**, recovers automatically.
Residual risk: worst-case trip point 3.67 V (70 mV above abs max) with Basic 1 % resistors; use 0.1 %
resistors (Extended) to tighten to ~3.63 V if desired.

## Requested price check (JLC, USD)
| Part | LCSC | Basic/Ext | Pkg | Stock | @10 | @100 |
|---|---|---|---|---|---|---|
| TMUX1511RSVR | C2673275 | Ext | UTQFN-16 1.8×2.6 | 4161 | 0.5235 | 0.4000 |
| TMUX1511PWR | C2866750 | Ext | TSSOP-14 | 9608 | 0.3756 | 0.2878 |
| SSM6N56FE,LM | C146449 | Ext | SOT-563 | 7293 | 0.2036 | 0.1628 |
| 1 MΩ 0402 1 % (0402WGF1004TCE) | C26083 | Basic | 0402 | 2.44 M | 0.0026 | 0.0026 |
| 100 kΩ 0402 1 % (0402WGF1003TCE) | C25741 | Basic | 0402 | 8.1 M | 0.0024 | 0.0024 |
| 220 Ω 0402 1 % (0402WGF2200TCE) | C25091 | Basic | 0402 | 1.39 M | 0.0034 | 0.0034 |
| 100 nF 0402 16 V X7R (CL05B104KO5NNNC) | C1525 | Basic | 0402 | 22 M | 0.0045 | 0.0045 |
| (for OVP) 51 kΩ 0402 1 % | C25794 | Basic | 0402 | 1.89 M | 0.0019 | 0.0019 |
| (for OVP) 3.3 kΩ 0402 1 % | C25890 | Basic | 0402 | 2.07 M | 0.0035 | 0.0035 |

LCSC direct cross-check: TMUX1511RSVR $0.5286 @10; TPS259470ARPWR $1.0647 @10 / $0.8039 @100;
TPS259474LRPWR $1.0707 / $0.7965; TPS259521DSGR $0.5638 / $0.4224.
Note: the current BOM uses 0603 passives (e.g. 10k C25804); 0402 values above are new lines unless the
board moves to 0402.
