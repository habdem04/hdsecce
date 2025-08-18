# hdsec/hdsec/material_requisition.py

import frappe
from frappe import _
from frappe.utils import now

def on_submit_material_requisition(doc, method):
    """
    Creates FP Status Tracking after Material Requisition submission
    if: material_request_type == "Purchase" and custom_purchase_type == "Foreign"
    """
    if doc.material_request_type == "Purchase" and doc.custom_purchase_type == "Foreign":
        # Check if already exists
        existing = frappe.db.exists(
            "FP Status Tracking",
            {"requisition_reference": doc.name}
        )
        if existing:
            frappe.msgprint(
                _("FP Status Tracking already exists: {0}").format(
                    frappe.utils.get_link_to_form("FP Status Tracking", existing)
                ),
                title=_("Already Exists"),
                alert=True,
                indicator="orange"
            )
            return

        try:
            fp_tracking = frappe.new_doc("FP Status Tracking")
            fp_tracking.requisition_reference = doc.name

            # ✅ Set the correct naming series
            # fp_tracking.naming_series = "FPRT-.YYYY.-"

            fp_tracking.current_status = "Material Requisition Completed"
            fp_tracking.request_initiated_date = now()

            # Insert the document
            fp_tracking.insert(ignore_permissions=True)

            # Success message with link
            frappe.msgprint(
                _("FP Status Tracking created: {0}").format(
                    frappe.utils.get_link_to_form("FP Status Tracking", fp_tracking.name)
                ),
                title=_("Success"),
                alert=True,
                indicator="green"
            )

        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "FP Status Tracking Creation Failed")
            frappe.throw(
                _("Failed to create FP Status Tracking: {0}").format(str(e)),
                title=_("Error")
            )