import frappe

class TruthSourceSettings:
    """
    This is a "Single" so we don’t subclass Document — we hook via events.
    """

@frappe.whitelist()
def sync_permissions_now():
    _sync_permissions()

def on_update(doc, method=None):
    # If someone edits the settings from Desk, keep permissions in sync
    _sync_permissions()

def _sync_permissions():
    """Give every user with 'Excise Auditor' role the warehouses
    defined in Truth Source Settings (or the default if empty).
    """
    settings = frappe.get_single("Truth Source Settings")
    whs = []

    if settings.limit_to_selected:
        # Table MultiSelect stores names in child records under .get("warehouses")
        # but for MultiSelect Link it stores in .warehouses as CSV; we handle both.
        if getattr(settings, "warehouses", None):
            if isinstance(settings.warehouses, list):
                whs = [w.warehouse for w in settings.warehouses if getattr(w, "warehouse", None)]
            elif isinstance(settings.warehouses, str) and settings.warehouses.strip():
                whs = [x.strip() for x in settings.warehouses.split(",")]
    if not whs and settings.default_warehouse:
        whs = [settings.default_warehouse]

    # Get all Excise Auditor users
    users = frappe.get_all(
        "Has Role",
        fields=["parent as user"],
        filters={"role": "Excise Auditor"}
    )
    users = [u.user for u in users]

    # Clear existing User Permission to avoid duplicates
    for u in users:
        frappe.db.delete("User Permission", {
            "user": u,
            "allow": "Warehouse"
        })

        for wh in whs:
            if not wh:
                continue
            up = frappe.new_doc("User Permission")
            up.user = u
            up.allow = "Warehouse"
            up.for_value = wh
            up.apply_to_all_doctypes = 1
            up.insert(ignore_permissions=True)

    frappe.db.commit()
