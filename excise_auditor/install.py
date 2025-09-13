import frappe

def after_install():
    if not frappe.db.exists("Role", "Excise Auditor"):
        frappe.get_doc({
            "doctype": "Role",
            "role_name": "Excise Auditor",
            "desk_access": 1
        }).insert(ignore_permissions=True)
