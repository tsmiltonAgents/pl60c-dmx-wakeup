# Design review (senior EE pass), 2026-09-02

Scope: rev A (`hw/design.py`) and MINI (`hw/design_mini.py`). Method: every pin mapping checked against the
LCSC-hosted datasheet of the exact ordered part, not the KiCad symbol; supply/thermal/drive margins
calculated; manufacturing rules re-checked against JLCPCB capability. Findings are ordered by severity.
Everything marked **fixed** is in the current files and both boards were rebuilt and re-verified
(ERC 0, netlist match, DRC 0 errors, stock check) after the fixes.

| # | Sev | Finding | Evidence | Status |
|---|---|---|---|---|
| 1 | **Critical** | Buzzer transistor Q1 (S8050, SOT-23) was wired with KiCad's *TO-92* S8050 symbol (E-B-C = 1-2-3). The ordered SOT-23 part (C2146, marking J3Y) is **B-E-C = 1-2-3**. As built, GPIO drove the emitter and the base sat on GND: buzzer would never sound, and the base-emitter junction would be reverse-biased to 3.3 V (VEBO 5 V, survives, but wrong). | C2146 datasheet p.1 pin diagram | **Fixed**: symbol changed to the SOT-23 B-E-C symbol (`Transistor_BJT:BC817` with value S8050), nets pad1=base, pad2=GND, pad3=collector. Both boards. |
| 2 | Major | Rev A RGB LED WS2812B-B/T (5050, C2761795) run from 3.3 V: datasheet VDD 3.7–5.3 V, VIH 2.7 V min. Would usually work, but out of spec on two parameters. | C2761795 datasheet, "Power supply voltage +3.7~+5.3 V", "VIH 2.7 V" | **Fixed**: both boards now use WS2812B-2020-V6 (C52917434), whose datasheet states VDD +3.3 to +5.3 V, VIH 0.55·VDD, "supports a 3.3 V power supply". |
| 3 | Major | Buzzer MLT-8530 driven straight from 5 V: rated 3.6 V, operating 2.5–4.5 Vo-p; coil 16 Ω → ~290 mA peaks, above the 95 mA rated. | C94599 datasheet p.2 | **Fixed**: 10 Ω 1206 (C17903, 250 mW) in series (R10): ~180 mA peak, 2.9 V across the coil, 0.16 W in the resistor at 50 % duty. Base resistor 1 kΩ → 470 Ω (datasheet drive circuit; forced β ≈ 35 with hFE ≥ 120). Mini: R10 is on board, buzzer external on BZ+/BZ−. |
| 4 | Major | MINI LDO AP2112K-3.3 (SOT-23-5) thermal: θJA 184 °C/W. Continuous Wi-Fi TX average ≈ 0.3 A × 1.7 V = 0.5 W → +92 °C; in a warm enclosure this approaches the 150 °C junction / 160 °C shutdown. Normal wake-up-lamp duty (modem sleep, short bursts) is 50–150 mA → +15–45 °C, fine. | C51118 datasheet, thermal table; ESP32-S3 datasheet current figures | **Open, mitigated**: the GND pad has a stitching via into the ground plane; firmware must keep Wi-Fi power-save on and avoid long continuous TX (OTA at night is fine). If the firmware needs sustained full-power Wi-Fi, use rev A (AMS1117, 1 A, SOT-223) or a buck. Documented in README/pins.h. |
| 5 | Minor | AMS1117 (rev A) output capacitor: datasheet asks for ≥ 22 µF; design had 10 µF. Ceramic 10 µF works on countless boards, but no reason to run below the datasheet value. | AMS1117 datasheet | **Fixed**: C2 = 22 µF 0805 (C45783). |
| 6 | Minor | MINI PTC 0805 0.75 A hold, 6 V: hold current derates ~20 % at 50 °C and Wi-Fi peaks (0.5 A) + LED + buzzer can approach it. | Littelfuse 0805L derating curves | **Fixed**: MINI now uses the same 1 A / 1.8 A 1206 PTC as rev A (C5358568). |
| 7 | Minor | MINI 3V3 decoupling (C4 10 µF, C5 100 nF) was ~14 mm from module pin 3. | Espressif hardware design guidelines: decoupling close to 3V3 pin | **Fixed**: C4/C5 now sit on the bottom directly under module pin 3 (2 mm away, via to the plane). |
| 8 | Minor | SP3485 RO output is high-impedance whenever DE=1 (DE and /RE are tied), so GPIO18 floats while transmitting. | SP3485 datasheet | **Documented**: firmware enables the GPIO18 internal pull-up (or ignores RX). No hardware change; a 10 k pull-up can be added on rev A's spare area if RDM is ever used. |
| 9 | Info | I2C expansion (GPIO8/9) has no on-board pull-ups. | — | Documented: pull-ups belong on the peripheral board; ESP32 internal pull-ups (~45 k) suffice for short wires at 100 kHz. |
| 10 | Info | DMX port is not galvanically isolated; XLR shell (pad G) left floating. | ANSI E1.11 allows non-isolated for short local links | Documented (README). Fit an isolated variant if the light is on a different mains circuit far away. |
| 11 | Info | JLCPCB rotation convention for polarised parts differs from KiCad; MINI bottom-side parts additionally mirrored. | — | Documented: check the JLCPCB placement preview; two CPL files provided. |
| 12 | Info | ESP32-S3 strapping: GPIO0 pulled up + button; GPIO3/45/46 left floating as Espressif allows (internal pull defaults select normal boot); EN 10 k + 1 µF. USB D+/D− direct to GPIO20/19 (native USB-Serial/JTAG needs no external parts). | ESP32-S3 datasheet §strapping pins; MINI-1 datasheet pin table (pins 3, 4, 9, 10, 12, 13, 20–24, 30, 45 verified) | OK |
| 13 | Info | RS-485 polarity: SP3485 A (pin 6) → XLR pin 3 (Data+), B (pin 7) → XLR pin 2 (Data−), XLR pin 1 → GND. PSM712 pin 3 = common (datasheet: "for 12 V, pins 1 and 2 are positive"). USB-C: 5.1 k CC pull-downs, USBLC6 pairs 1↔6 / 3↔4, VBUS on pin 5. | datasheets | OK |
| 14 | Info | MINI land pattern: KiCad `ESP32-S2-MINI-1` footprint vs ESP32-S3-MINI-1 datasheet figure 10: 60 × 0.4 × 0.8 pads at 0.85 mm, 4 × 0.8 corner pads, 3 × 3 centre pads 1.2 mm at 1.65 mm with thermal vias, 15.4 × 20.5 mm, pin 1 top-left below the antenna. | MINI-1 datasheet p.30 | OK (identical) |

## Margins checked

* 5 V rail: USB-C source ≥ 0.5 A (CC pull-downs advertise default USB), PTC 1 A hold. Load: ESP32-S3 peak 0.5 A
  for ms bursts, average 0.05–0.25 A; LED ≤ 0.06 A; buzzer 0.09 A average. OK.
* 3.3 V rail: rev A AMS1117 1 A, dropout 1.1–1.3 V from 4.8 V (after PTC) → fine. MINI: see #4.
* Reset: EN RC 10 ms. GPIO0 10 k pull-up. USB-Serial/JTAG can reset/boot the chip without buttons.
* DMX drive: SP3485 differential output ≥ 1.5 V into 27 Ω (two terminators); TVS PSM712 +12/−7 V; common-mode −7…+12 V.
* Buzzer driver: Ib 5.1 mA, Ic 180 mA, forced β 35 (hFE min 120 at 50 mA); flyback B5819W 1 A.
* PCB: rev A 0.25/0.15 mm track/clearance, 0.7/0.3 vias; MINI 0.25/0.15 (0.1 min), 0.7/0.3 vias, 0.5 mm
  hole-to-hole; both inside JLCPCB standard capability. GND stitching and inner planes verified by DRC
  connectivity (0 unconnected items).

## Still recommended before a production run

1. Build one, measure 3V3 ripple during Wi-Fi TX and the LDO temperature (MINI).
2. Scope the DMX output with the light connected: BREAK ≥ 92 µs, MAB ≥ 12 µs, 250 kbaud, ≥ 40 Hz refresh.
3. Confirm the PL60C actually accepts the frame (mode channel 0 = CCT, intensity on channel 2).
