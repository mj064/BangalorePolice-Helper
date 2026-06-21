# Dataset

## Purpose

Describe the parking violation dataset used by the platform.

---

## Source

Bangalore Traffic Police parking violation records.

Approximate records:

~300,000 violations

---

## Available Fields

Spatial:

* latitude
* longitude
* location
* junction_name
* police_station

Temporal:

* created_datetime

Violation:

* violation_type
* offence_code

Vehicle:

* vehicle_type
* vehicle_number (used for repeat-offender scoring)

---

## Derived Features

Temporal:

* hour
* weekday
* month

Spatial:

* h3_cell

Historical:

* violations_last_hour
* violations_last_day
* violations_last_week

---

## Limitations

Dataset does not contain:

* traffic speed
* travel time
* traffic volume
* signal timing

Congestion must therefore be estimated indirectly.

---

## Future Improvements

Integrate:

* Google Traffic
* CCTV feeds
* Road network data
* Event schedules
