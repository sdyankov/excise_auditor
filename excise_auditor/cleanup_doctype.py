"""
Cleanup script to remove old Truth Source Settings DocType from production.

This script removes the Truth Source Settings DocType that was left behind
from a previous installation, allowing clean migration when reinstalling
the excise_auditor app.

Run this on production using:
    bench --site <sitename> execute excise_auditor.cleanup_doctype.cleanup
"""

import frappe


def cleanup():
    """Remove old Truth Source Settings DocType, Pages, and related data from previous installation"""

    doctype_name = "Truth Source Settings"

    try:
        # First, remove any Page documents from excise_auditor module
        # This prevents the "Not in Developer Mode" error during migration
        print("🔍 Checking for leftover Page documents from previous installation...")
        pages = frappe.db.sql("""
            SELECT name FROM `tabPage`
            WHERE module = 'Excise Auditor'
        """, as_dict=True)

        if pages:
            for page in pages:
                print(f"🗑️  Removing Page: {page.name}")
                frappe.db.sql("DELETE FROM `tabPage` WHERE name = %s", (page.name,))
            print(f"✅ Removed {len(pages)} Page document(s)")
        else:
            print("ℹ️  No Page documents found")

        # Check if DocType exists
        if not frappe.db.exists("DocType", doctype_name):
            print(f"ℹ️  {doctype_name} DocType not found - skipping DocType cleanup")
            if pages:
                # Commit if we removed pages
                frappe.db.commit()
                print(f"\n✅ Cleanup complete - removed Page documents")
                print(f"✅ You can now run: bench --site <sitename> migrate")
            return

        print(f"🔍 Found {doctype_name} DocType - proceeding with cleanup...")

        # Step 1: Delete the Single document record (if any)
        frappe.db.sql(f"""
            DELETE FROM `tabSingles`
            WHERE doctype = %s
        """, (doctype_name,))
        print(f"✅ Removed Single document data")

        # Step 2: Delete DocField records
        frappe.db.sql(f"""
            DELETE FROM `tabDocField`
            WHERE parent = %s
        """, (doctype_name,))
        print(f"✅ Removed DocField records")

        # Step 3: Delete DocPerm records
        frappe.db.sql(f"""
            DELETE FROM `tabDocPerm`
            WHERE parent = %s
        """, (doctype_name,))
        print(f"✅ Removed DocPerm records")

        # Step 4: Delete Property Setter records
        frappe.db.sql(f"""
            DELETE FROM `tabProperty Setter`
            WHERE doc_type = %s
        """, (doctype_name,))
        print(f"✅ Removed Property Setter records")

        # Step 5: Delete Custom Field records (if any)
        frappe.db.sql(f"""
            DELETE FROM `tabCustom Field`
            WHERE dt = %s
        """, (doctype_name,))
        print(f"✅ Removed Custom Field records")

        # Step 6: Delete the DocType record itself
        frappe.db.sql(f"""
            DELETE FROM `tabDocType`
            WHERE name = %s
        """, (doctype_name,))
        print(f"✅ Removed DocType record")

        # Step 7: Drop the table if it exists (Singles don't have tables, but check anyway)
        table_name = f"tab{doctype_name}"
        if frappe.db.table_exists(table_name):
            frappe.db.sql(f"DROP TABLE `{table_name}`")
            print(f"✅ Dropped table {table_name}")

        # Commit all changes
        frappe.db.commit()

        print(f"\n✅ Successfully cleaned up {doctype_name} DocType")
        print(f"✅ You can now run: bench --site <sitename> migrate")

    except Exception as e:
        frappe.db.rollback()
        print(f"\n❌ Error during cleanup: {str(e)}")
        raise


if __name__ == "__main__":
    cleanup()
