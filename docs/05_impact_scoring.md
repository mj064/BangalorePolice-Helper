# Impact Scoring

## Purpose

Estimate congestion risk caused by illegal parking.

---

## Inputs

* violation density
* parking severity
* peak-hour concentration
* repeat violations

---

## Outputs

Parking Impact Index (PII)

Range:

0 - 100

---

## Formula

PII =
0.4 × Violation Density +
0.3 × Main Road Violations +
0.2 × Peak Hour Violations +
0.1 × Repeat Violations

---

## Categories

0-45 Low

46-55 Medium

56-65 High

66-100 Critical

> Thresholds recalibrated 2026-06-21 to reflect the actual PII distribution
> (Min=31, Max=75, Mean=48.8) and provide balanced operational prioritisation.
> Previous thresholds (Low ≤40, Medium 41-60, High 61-80, Critical ≥81)
> produced 382 Medium / 23 High / 0 Critical across 421 hotspots.
> New thresholds produce 147 Low / 213 Medium / 56 High / 5 Critical.

---

## Success Criteria

Locations with higher parking disruption receive higher scores.

---

## Future Improvements

Replace proxy score with actual traffic impact metrics.
