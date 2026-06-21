# Recommendation Engine

## Purpose

Convert analytics into actionable police deployment recommendations.

---

## Inputs

* impact score
* hotspot trend
* hotspot probability

---

## Outputs

Recommended:

* officers
* tow vehicles
* deployment windows

---

## Rule Example

IF

Impact Score > 90

AND

Risk > 80

THEN

Deploy:

* 2 officers
* 1 tow unit

---

## Success Criteria

Recommendations should be simple and operationally useful.

---

## Future Improvements

Optimization-based deployment planning.
