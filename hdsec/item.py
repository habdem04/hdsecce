import frappe
from frappe import _

@frappe.whitelist()
def get_next_item_code(item_group):
    """
    Generates next item code for given Item Group using custom_item_group_id.
    Format: {custom_item_group_id}-{serial:04d}, e.g., 100-0001
    Checks if custom_item_group_id is set; throws error if missing.
    """
    if not item_group:
        frappe.throw(_("Item Group is required"))

    # Fetch custom_item_group_id from Item Group
    custom_group_id = frappe.db.get_value("Item Group", item_group, "custom_item_group_id")

    if not custom_group_id:
        frappe.throw(_(
            "Cannot generate Item Code: 'Custom Item Group ID' is not set for Item Group '{0}'. "
            "Please go to the Item Group document and set the 'Custom Item Group ID' field."
        ).format(frappe.bold(item_group)))

    custom_group_id = str(custom_group_id).strip()

    if not custom_group_id:
        frappe.throw(_("Invalid Custom Item Group ID (empty) for Item Group '{0}'").format(item_group))

    # Find last used item with code like '100-%'
    last_item = frappe.db.sql("""
        SELECT name
        FROM `tabItem`
        WHERE name LIKE %s
        ORDER BY CAST(SUBSTRING_INDEX(name, '-', -1) AS UNSIGNED) DESC
        LIMIT 1
    """, (f"{custom_group_id}-%",))

    next_num = 1
    if last_item and last_item[0][0]:
        try:
            parts = last_item[0][0].split('-')
            if len(parts) == 2 and parts[0] == custom_group_id:
                next_num = int(parts[1]) + 1
        except (ValueError, IndexError):
            pass  # fallback to 1

    return f"{custom_group_id}-{next_num:04d}"