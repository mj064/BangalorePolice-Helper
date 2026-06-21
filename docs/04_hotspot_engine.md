# Hotspot Detection Engine

## Purpose

Identify recurring parking violation clusters.

---

## Inputs

* latitude
* longitude
* timestamp

---

## Outputs

* hotspot_id
* centroid
* violation_count
* trend

---

## MVP Logic

DBSCAN clustering

Parameters:

* eps = 100m
* min_samples = 20

---

## Production Logic

H3 indexing

Advantages:

* scalable
* fast aggregation
* real-time friendly

---

## Success Criteria

Hotspots should clearly identify the most violation-prone locations.

---

## Future Improvements

Dynamic hotspot detection using streaming events.
