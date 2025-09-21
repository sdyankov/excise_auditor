import frappe

def has_app_permission(*args, **kwargs):
    """Tile visible for System Manager or Excise Auditor."""
    roles = set(frappe.get_roles(frappe.session.user))
    return bool({"System Manager", "Excise Auditor"} & roles)
