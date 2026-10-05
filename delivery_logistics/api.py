import base64
import re

import frappe
from frappe import _
from frappe.utils import cint, flt, getdate, now_datetime, nowdate

FINAL = ("Delivered", "Failed", "Rescheduled")
MANAGER_ROLES = {"System Manager", "Stock Manager", "Delivery Manager"}
STOP_KEYS = (
    "name", "idx", "customer", "customer_address", "address", "customer_contact",
    "delivery_note", "grand_total", "estimated_arrival", "distance",
    "custom_stop_status", "custom_failure_reason", "custom_receiver_name",
    "custom_arrived_at", "custom_completed_at", "custom_attempt_no",
)


def _is_manager():
    return frappe.session.user == "Administrator" or bool(MANAGER_ROLES & set(frappe.get_roles()))


def _my_employee():
    return frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "name")


def _load(trip, stop):
    doc = frappe.get_doc("Delivery Trip", trip)
    if doc.docstatus != 1:
        frappe.throw(_("Delivery Trip {0} must be submitted").format(trip))
    if not _is_manager():
        emp = _my_employee()
        if not emp or emp != doc.get("employee"):
            frappe.throw(_("You are not the assigned driver for this trip"), frappe.PermissionError)
    row = next((r for r in doc.delivery_stops if r.name == stop), None)
    if not row:
        frappe.throw(_("Stop {0} not found on {1}").format(stop, trip))
    return doc, row


def _finish(doc, row):
    """Save the child-row changes, then sync the trip status and Delivery Note."""
    doc.flags.ignore_permissions = True
    doc.save()

    if row.custom_stop_status in ("Arrived", "Delivered", "Failed"):
        frappe.db.set_value("Delivery Stop", row.name, "visited", 1, update_modified=False)

    statuses = [(r.get("custom_stop_status") or "Pending") for r in doc.delivery_stops]
    if all(s in FINAL for s in statuses):
        status = "Completed"
    elif any(s != "Pending" for s in statuses):
        status = "In Transit"
    else:
        status = doc.status
    if status != doc.status:
        doc.db_set("status", status, update_modified=False)

    if row.get("delivery_note"):
        label = {"Arrived": "Arrived at customer", "Delivered": "Delivered",
                 "Failed": "Delivery failed", "Rescheduled": "Rescheduled"}[row.custom_stop_status]
        frappe.db.set_value("Delivery Note", row.delivery_note, {
            "custom_delivery_status": label,
            "custom_received_by": row.get("custom_receiver_name"),
            "custom_delivered_on": row.get("custom_completed_at")
            if row.custom_stop_status == "Delivered" else None,
        }, update_modified=False)
        frappe.get_doc("Delivery Note", row.delivery_note).add_comment(
            "Info", _("{0} on trip {1} (stop {2})").format(label, doc.name, row.idx))
    return {"trip_status": doc.status if status == doc.status else status,
            "stop_status": row.custom_stop_status}


def _save_photo(trip, data_url):
    m = re.match(r"^data:image/(png|jpeg|jpg);base64,(.+)$", data_url or "", re.S)
    if not m:
        frappe.throw(_("Invalid photo data"))
    content = base64.b64decode(m.group(2))
    if len(content) > 5 * 1024 * 1024:
        frappe.throw(_("Photo is too large (max 5 MB)"))
    ext = "png" if m.group(1) == "png" else "jpg"
    f = frappe.get_doc({
        "doctype": "File",
        "file_name": f"pod-{frappe.generate_hash(length=8)}.{ext}",
        "attached_to_doctype": "Delivery Trip",
        "attached_to_name": trip,
        "content": content,
        "is_private": 1,
    }).insert(ignore_permissions=True)
    return f.file_url


@frappe.whitelist()
def get_my_trips(date=None):
    date = str(getdate(date or nowdate()))
    filters = {
        "docstatus": 1,
        "status": ["!=", "Cancelled"],
        "departure_time": ["between", [date + " 00:00:00", date + " 23:59:59"]],
    }
    if not _is_manager():
        filters["employee"] = _my_employee() or "__none__"

    out = []
    for name in frappe.get_all("Delivery Trip", filters=filters, pluck="name", order_by="departure_time"):
        t = frappe.get_doc("Delivery Trip", name)
        out.append({
            "name": t.name, "status": t.status, "driver_name": t.get("driver_name"),
            "vehicle": t.get("vehicle"), "departure_time": t.get("departure_time"),
            "stops": [{k: r.get(k) for k in STOP_KEYS} for r in t.delivery_stops],
        })
    return out


@frappe.whitelist()
def get_failure_reasons():
    return frappe.get_all("Delivery Failure Reason", filters={"disabled": 0},
                          fields=["name", "allow_reschedule"], order_by="name")


@frappe.whitelist()
def mark_arrived(trip, stop, latitude=None, longitude=None):
    doc, row = _load(trip, stop)
    row.custom_stop_status = "Arrived"
    row.custom_arrived_at = now_datetime()
    if latitude and longitude:
        row.custom_pod_latitude, row.custom_pod_longitude = flt(latitude), flt(longitude)
    return _finish(doc, row)


@frappe.whitelist()
def mark_delivered(trip, stop, receiver_name, signature=None, photo=None,
                   latitude=None, longitude=None, remarks=None):
    if not (receiver_name or "").strip():
        frappe.throw(_("Received By is required"))
    doc, row = _load(trip, stop)
    row.custom_stop_status = "Delivered"
    row.custom_failure_reason = None
    row.custom_completed_at = now_datetime()
    row.custom_receiver_name = receiver_name.strip()
    row.custom_stop_remarks = remarks
    if signature:
        if not signature.startswith("data:image/"):
            frappe.throw(_("Invalid signature data"))
        row.custom_pod_signature = signature
    if photo:
        row.custom_pod_image = _save_photo(trip, photo)
    if latitude and longitude:
        row.custom_pod_latitude, row.custom_pod_longitude = flt(latitude), flt(longitude)
    return _finish(doc, row)


@frappe.whitelist()
def mark_failed(trip, stop, reason, remarks=None, reschedule=0, latitude=None, longitude=None):
    if not reason:
        frappe.throw(_("Failure Reason is required"))
    doc, row = _load(trip, stop)
    row.custom_stop_status = "Rescheduled" if cint(reschedule) else "Failed"
    row.custom_failure_reason = reason
    row.custom_completed_at = now_datetime()
    row.custom_stop_remarks = remarks
    if latitude and longitude:
        row.custom_pod_latitude, row.custom_pod_longitude = flt(latitude), flt(longitude)
    return _finish(doc, row)


@frappe.whitelist()
def log_vehicle_location(vehicle, latitude, longitude, speed=0, timestamp=None):
    """Endpoint for the GPS tracker (authenticate with an API key/secret of a 'Delivery Tracker' user)."""
    doc = frappe.get_doc({
        "doctype": "Vehicle Location",
        "vehicle": vehicle,
        "latitude": flt(latitude),
        "longitude": flt(longitude),
        "speed": flt(speed),
        "timestamp": timestamp or now_datetime(),
    }).insert()
    return doc.name


@frappe.whitelist()
def get_latest_location(vehicle):
    rows = frappe.get_all("Vehicle Location", filters={"vehicle": vehicle},
                          fields=["latitude", "longitude", "speed", "timestamp"],
                          order_by="timestamp desc", limit=1)
    return rows[0] if rows else None
