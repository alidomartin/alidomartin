# N1 Performance Lab — Glossary

Canonical metric labels and terminology for all N1 reports and dashboards.
Use these terms verbatim. No substitutions.

---

## Performance Metrics

| Term | Label (use this) | Unit | Definition |
|---|---|---|---|
| Total Score of Athleticism | TSA | dimensionless | Sum of Z-scores across three CMJ metrics: Relative Peak Power, RSImod, and Vertical Jump Height. Higher values indicate greater overall athletic output. |
| Relative Peak Power | Relative Peak Power | W/kg | Peak propulsive power normalized to body mass. Derived from the propulsive phase of the CMJ. |
| Modified Reactive Strength Index | RSImod | m/s | Vertical Jump Height divided by time to takeoff. Measures explosive-reactive capacity from a standing start. |
| Vertical Jump Height | Vertical Jump Height | m | Jump height calculated from takeoff velocity during the CMJ propulsive phase. Industry standard (not flight time). |
| Ground Reaction Force | GRF | N | Vertical force applied to the force plate by the athlete. |
| Body Weight | Body Weight | N | System weight measured during the quiet phase (minimum 1 second of stillness). |
| Center of Mass Velocity | COM Velocity | m/s | Velocity of the athlete's center of mass, derived from numerical integration of the force-time curve. |
| Reactive Strength Index (Modified) | RSImod | m/s | See RSImod above. Do not use "RSI" alone. |
| Landing Performance Index | LPI | m/s | Jump Height divided by total landing time. Reflects landing efficiency. |

---

## Z-Score Normalization

TSA uses session-relative Z-scores:

```
Z = (x - mean(x)) / sd(x)
TSA = Z(Relative Peak Power) + Z(RSImod) + Z(Vertical Jump Height)
```

- Positive TSA: above average relative to the current group
- Negative TSA: below average relative to the current group
- Range is unbounded; typical session range is approximately -3 to +3

---

## Roster Positions

Use full position names in all outputs. No abbreviations in tables, labels, or report text.

| Full Name | Short Code (internal only) |
|---|---|
| Setter | S |
| Libero | L |
| Outside Hitter | OH |
| Opposite Hitter | OPP |
| Middle Blocker | MB |
| Defensive Specialist | DS |

---

## Units Reference

| Quantity | Unit | Symbol |
|---|---|---|
| Force | Newtons | N |
| Power (absolute) | Watts | W |
| Power (relative) | Watts per kilogram | W/kg |
| Velocity | Metres per second | m/s |
| Height / displacement | Metres | m |
| Time | Milliseconds (landing) / Seconds (jump) | ms / s |
| Sampling frequency | Hertz | Hz |

---

## Report Conventions

- All values rounded to two decimal places unless stated otherwise.
- Relative Peak Power displayed to one decimal place (e.g., 52.3 W/kg).
- TSA displayed with sign prefix (e.g., +1.84, -0.72).
- Session mean and SD used for Z-score calculation. Cross-session comparisons require normative database.
- Force plate sampling frequency: 500 Hz standard.
- Body weight constant used in simulations: 700 N.

---

## Reference

McMahon, J. J., Suchomel, T. J., Lake, J. P., & Comfort, P. (2018).
Understanding the Key Phases of the Countermovement Jump Force-Time Curve.
*Strength & Conditioning Journal, 40*(4), 96-106.
https://doi.org/10.1519/ssc.0000000000000375
