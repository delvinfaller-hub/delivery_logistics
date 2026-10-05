import frappe
from frappe import _
from frappe.utils import flt, time_diff_in_seconds


def validate(doc, method=None):
    stops = doc.get("delivery_stops") or []

    for s in stops:
        if not s.get("custom_stop_status"):
            s.custom_stop_status = "Pending"
        if s.custom_stop_status in ("Failed", "Rescheduled") and not s.get("custom_failure_reason"):
            frappe.throw(_("Row {0}: Failure Reason is required for a {1} stop").format(
                s.idx, s.custom_stop_status))

    delivered = sum(1 for s in stops if s.custom_stop_status == "Delivered")
    total_cost = sum(flt(e.amount) for e in (doc.get("custom_expenses") or []))

    doc.custom_total_stops = len(stops)
    doc.custom_delivered_stops = delivered
    doc.custom_failed_stops = sum(1 for s in stops if s.custom_stop_status == "Failed")
    doc.custom_total_expenses = total_cost
    doc.custom_cost_per_delivery = flt(total_cost / delivered) if delivered else 0

    if doc.get("departure_time") and doc.get("custom_return_time"):
        secs = time_diff_in_seconds(doc.custom_return_time, doc.departure_time)
        if secs < 0:
            frappe.throw(_("Return Time cannot be earlier than Departure Time"))
        doc.custom_actual_duration = int(secs)
