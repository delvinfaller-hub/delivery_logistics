import frappe
from frappe import _

no_cache = 1


def get_context(context):
    if frappe.session.user == "Guest":
        frappe.throw(_("Please log in to view your deliveries"), frappe.PermissionError)
    context.no_cache = 1
    context.title = _("My Deliveries")
