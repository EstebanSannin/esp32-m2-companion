# References — power_3v3
- SPEC §6.2; Espressif HDG power sections
- FB: Sunlord GZ2012D101TF (LCSC C1015, Basic) 100R@100MHz, 800 mA, 150 mR.
  Chosen over GZ2012D601TF (C1017): that one is 500 mA — too close to
  ESP32-S3 TX bursts. Alternative if bead rejected at GATE 2: 0R link.
