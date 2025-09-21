import frappe
from frappe import _

def update_sales_order_deposited_amount(doc, method):
    """
    Updates custom_deposited_amount in Sales Order based on linked Payment Entries
    """
    for ref in doc.references:
        if ref.reference_doctype == "Sales Order":
            so_name = ref.reference_name

            # Get total paid amount from all submitted Payment Entries linked to this Sales Order
            total_paid = frappe.db.sql("""
                SELECT SUM(allocated_amount)
                FROM `tabPayment Entry Reference`
                WHERE reference_name = %s
                  AND reference_doctype = 'Sales Order'
                  AND docstatus = 1
            """, so_name)

            deposited = total_paid[0][0] if total_paid and total_paid[0][0] else 0.0

            # Update Sales Order
            so = frappe.get_doc("Sales Order", so_name)
            so.db_set("custom_deposited_amount", deposited, commit=False)

    frappe.db.commit()
    frappe.msgprint(_("Deposited amount updated in linked Sales Order(s)."), alert=True)