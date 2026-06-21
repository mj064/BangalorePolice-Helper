# Prediction Engine

## Purpose

Predict future hotspot formation.

---

## Inputs

Temporal:

* hour
* weekday
* month

Spatial:

* junction
* hotspot
* h3 cell

Historical:

* violation counts

---

## Outputs

Hotspot risk probability.

---

## Model

LightGBM

---

## Example Output

KR Market

Risk:

92%

---

## Evaluation

Metrics:

* Precision
* Recall
* F1
* ROC AUC

---

## Future Improvements

Time-series forecasting.

Event-aware predictions.
