from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

STOP_STATUSES = "Pending\nArrived\nDelivered\nFailed\nRescheduled"


def _f(fieldname, label, fieldtype, **kw):
    d = dict(fieldname=fieldname, label=label, fieldtype=fieldtype)
    d.update(kw)
    return d


def get_custom_fields():
    aos = dict(allow_on_submit=1)
    aos_ro = dict(allow_on_submit=1, read_only=1, no_copy=1)
    return {
        "Delivery Trip": [
            _f("custom_logistics_section", "Logistics Summary", "Section Break",
               insert_after="delivery_stops", collapsible=1),
            _f("custom_dispatcher", "Dispatcher", "Link", options="User",
               default="__user", insert_after="custom_logistics_section", **aos),
            _f("custom_return_time", "Return Time", "Datetime",
               insert_after="custom_dispatcher", **aos),
            _f("custom_actual_duration", "Actual Duration", "Duration",
               insert_after="custom_return_time", **aos_ro),
            _f("custom_logistics_col", "", "Column Break", insert_after="custom_actual_duration"),
            _f("custom_total_stops", "Total Stops", "Int",
               insert_after="custom_logistics_col", **aos_ro),
            _f("custom_delivered_stops", "Delivered Stops", "Int",
               insert_after="custom_total_stops", **aos_ro),
            _f("custom_failed_stops", "Failed Stops", "Int",
               insert_after="custom_delivered_stops", **aos_ro),
            _f("custom_cost_section", "Trip Expenses", "Section Break",
               insert_after="custom_failed_stops"),
            _f("custom_expenses", "Expenses", "Table", options="Delivery Trip Expense",
               insert_after="custom_cost_section", **aos),
            _f("custom_total_expenses", "Total Trip Cost", "Currency",
               insert_after="custom_expenses", **aos_ro),
            _f("custom_cost_per_delivery", "Cost per Delivered Stop", "Currency",
               insert_after="custom_total_expenses", **aos_ro),
        ],
        "Delivery Stop": [
            _f("custom_stop_status", "Stop Status", "Select", options=STOP_STATUSES,
               default="Pending", in_list_view=1, insert_after="customer", **aos),
            _f("custom_failure_reason", "Failure Reason", "Link",
               options="Delivery Failure Reason", insert_after="custom_stop_status", **aos),
            _f("custom_attempt_no", "Attempt No.", "Int", default="1",
               insert_after="custom_failure_reason", **aos),
            _f("custom_arrived_at", "Arrived At", "Datetime",
               insert_after="custom_attempt_no", **aos),
            _f("custom_completed_at", "Completed At", "Datetime",
               insert_after="custom_arrived_at", **aos),
            _f("custom_receiver_name", "Received By", "Data",
               insert_after="custom_completed_at", **aos),
            _f("custom_pod_signature", "Signature", "Signature",
               insert_after="custom_receiver_name", **aos),
            _f("custom_pod_image", "Delivery Photo", "Attach Image",
               insert_after="custom_pod_signature", **aos),
            _f("custom_pod_latitude", "POD Latitude", "Float", precision="9",
               insert_after="custom_pod_image", **aos),
            _f("custom_pod_longitude", "POD Longitude", "Float", precision="9",
               insert_after="custom_pod_latitude", **aos),
            _f("custom_stop_remarks", "Remarks", "Small Text",
               insert_after="custom_pod_longitude", **aos),
        ],
        "Delivery Note": [
            _f("custom_delivery_section", "Delivery Status", "Section Break", collapsible=1),
            _f("custom_delivery_status", "Delivery Status", "Data", **aos_ro),
            _f("custom_received_by", "Received By", "Data", **aos_ro),
            _f("custom_delivered_on", "Delivered On", "Datetime", **aos_ro),
        ],
    }


def create_fields():
    create_custom_fields(get_custom_fields(), update=True)


def after_install():
    create_fields()


def after_migrate():
    create_fields()
