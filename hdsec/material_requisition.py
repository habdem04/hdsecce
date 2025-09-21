# hdsec/hdsec/material_requisition.py

import frappe
from frappe import _
from frappe.utils import now

def on_submit_material_requisition(doc, method):
    """
    Creates FP Status Tracking when a Material Requisition (Purchase + Foreign) is submitted.
    - Sets current_status and current_stage
    - Logs the status in FP Status History child table
    - Sets action_datetime, acting_user, and responsible_role
    """
    if doc.material_request_type == "Purchase" and doc.custom_purchase_type == "Foreign":
        # Check if FP Status Tracking already exists
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
            # Get current user and their roles
            current_user = frappe.session.user
            user_roles = frappe.get_roles(current_user)

            # Choose a responsible role (you can customize logic)
            # Example: Prefer "Purchase Manager", else take first role
            role_priority = [
                "Purchase Manager",
                "Procurement Officer",
                "System Manager",
                "Administrator"
            ]

            responsible_role = None
            for role in role_priority:
                if role in user_roles:
                    responsible_role = role
                    break

            # Fallback to first role if no match
            if not responsible_role and user_roles:
                responsible_role = user_roles[0]

            # Create new FP Status Tracking document
            fp_tracking = frappe.new_doc("FP Status Tracking")
            fp_tracking.requisition_reference = doc.name
            fp_tracking.naming_series = "FPRT-.YYYY.-"

            # Set current status
            current_status = "Material Requisition Completed"
            fp_tracking.current_status = current_status

            # Fetch stage from Foreign Purchase Status Item
            stage_value = frappe.db.get_value(
                "Foreign Purchase Status Item",
                {"status_name": current_status},
                "stage"
            )
            fp_tracking.current_stage = stage_value if stage_value else None

            fp_tracking.request_initiated_date = now()

            # ✅ Append to FP Status History child table
            fp_tracking.append("status_history", {
                "status": current_status,
                "stage": stage_value,
                "status_name": current_status,           # if field exists and is used
                "action_datetime": now(),
                "updated_on": now(),
                "updated_by": current_user,
                "acting_user": current_user,             # ✅ Currently logged-in user
                "responsible_role": responsible_role     # ✅ Role of the user
            })

            # Insert document
            fp_tracking.insert(ignore_permissions=True)

            # Success message
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