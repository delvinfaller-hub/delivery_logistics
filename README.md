# Delivery Logistics

Logistics/TMS-style extension for ERPNext V16 Delivery Trip, built on Custom Fields (no forked doctypes).

## Install
    bench get-app /path/to/delivery_logistics
    bench --site yoursite install-app delivery_logistics
    bench --site yoursite migrate

## What it adds
- **Delivery Stop**: stop status (Pending/Arrived/Delivered/Failed/Rescheduled), failure reason, attempt no., arrival/completion time, receiver, signature, photo, GPS, remarks
- **Delivery Trip**: dispatcher, return time, actual duration, stop counts, Trip Expenses table, total trip cost, cost per delivered stop
- **Delivery Note**: delivery status / received by / delivered on, written back from the stop
- **Doctypes**: Delivery Failure Reason, Delivery Trip Expense (child), Vehicle Location (GPS log)
- **Driver page**: `/driver_trips` (mobile-friendly; Navigate / Arrived / Delivered with POD / Failed)
- **API**: `delivery_logistics.api.*` (mark_arrived, mark_delivered, mark_failed, log_vehicle_location, get_latest_location)

## Setup
- Create Delivery Failure Reason records (Customer Closed, Customer Unavailable, Wrong Address, Refused Delivery, Damaged Goods, Vehicle Problem...).
- Driver users: set `user_id` on the Employee linked to the Driver, and give them read/write on Delivery Trip (e.g. Stock User). Only the assigned driver (or Stock/System/Delivery Manager) can update a trip's stops.
- GPS tracker: create a user with the "Delivery Tracker" role, generate API keys, and POST to `/api/method/delivery_logistics.api.log_vehicle_location`.
