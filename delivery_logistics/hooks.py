app_name = "delivery_logistics"
app_title = "Delivery Logistics"
app_publisher = "Delvin"
app_description = "Logistics/TMS-style extension for ERPNext Delivery Trip"
app_email = "dev@example.com"
app_license = "mit"
required_apps = ["erpnext"]

after_install = "delivery_logistics.setup.install.after_install"
after_migrate = "delivery_logistics.setup.install.after_migrate"

doc_events = {
    "Delivery Trip": {
        "validate": "delivery_logistics.events.delivery_trip.validate",
        "before_update_after_submit": "delivery_logistics.events.delivery_trip.validate",
    }
}
