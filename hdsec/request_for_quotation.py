# hdsec/hdsec/request_for_quotation.py

import frappe
from frappe import _
from frappe.utils import now

def on_submit_rfq_update_fp_status(doc, method):
    """
    On RFQ Submit:
    - Correctly handles field names in parent vs child table
    - Uses 'status_name' for child table rows
    - Uses 'current_status' for parent document
    """
    try:
        # ✅ 1. Get RFQ name
        rfq_name = doc.name
        frappe.log_error(f"|1| RFQ: {rfq_name}", "FP Tracking Debug")

        # ✅ 2. Fetch custom_purchase_type
        custom_purchase_type = frappe.db.get_value(
            "Request for Quotation", 
            rfq_name, 
            "custom_purchase_type"
        )
        frappe.log_error(f"|2| custom_purchase_type: {custom_purchase_type}", "FP Tracking Debug")

        # ✅ 3. Verify it's a Foreign Purchase
        if not custom_purchase_type:
            frappe.log_error("|3| No custom_purchase_type set", "FP Tracking Debug")
            return
            
        purchase_type_name = frappe.db.get_value("Purchase Type", custom_purchase_type, "name")
        if not purchase_type_name or purchase_type_name != "Foreign":
            frappe.log_error(f"|4| Not Foreign Purchase (found: {purchase_type_name})", "FP Tracking Debug")
            return

        # ✅ 4. Get material_request from ITEMS
        material_request = None
        items = frappe.get_all(
            "Request for Quotation Item",
            filters={"parent": rfq_name},
            fields=["material_request"],
            limit=1
        )
        
        if items and items[0].material_request:
            material_request = items[0].material_request
            frappe.log_error(f"|5| Found material_request from items: {material_request}", "FP Tracking Debug")
        else:
            frappe.throw(
                _("No Material Request linked in RFQ items for {0}").format(rfq_name),
                title=_("Missing Link")
            )

        # ✅ 5. Find FP Status Tracking
        fp_tracking_name = frappe.db.exists(
            "FP Status Tracking",
            {"requisition_reference": material_request}
        )
        
        frappe.log_error(f"|6| FP Tracking lookup: requisition_reference={material_request} → Found={fp_tracking_name}", "FP Tracking Debug")
        
        if not fp_tracking_name:
            frappe.throw(
                _("No FP Status Tracking found for Material Request {0}").format(material_request),
                title=_("Tracking Missing")
            )

        # ✅ 6. Load and update FP Status Tracking
        fp_tracking = frappe.get_doc("FP Status Tracking", fp_tracking_name)
        
        # ✅ Set new status
        new_status = "RFQ/RFP Issued"
        stage_value = frappe.db.get_value(
            "Foreign Purchase Status Item",
            {"status_name": new_status},
            "stage"
        )
        
        if not stage_value:
            frappe.throw(
                _("No stage configured for status '{0}'").format(new_status),
                title=_("Configuration Error")
            )
        
        frappe.log_error(f"|7| Setting status: {new_status} | stage: {stage_value}", "FP Tracking Debug")

        # ✅ Update PARENT document fields
        fp_tracking.current_status = new_status  # ✅ Parent field
        fp_tracking.current_stage = stage_value
        fp_tracking.rfq_reference = rfq_name

        # ✅ CORRECTED: Check for duplicates using CHILD table field name
        duplicate = False
        for row in fp_tracking.status_history:
            # ✅ CHILD table uses 'status_name', NOT 'status'
            if row.status_name == new_status:
                duplicate = True
                break
                
        if duplicate:
            frappe.log_error(f"|8| Duplicate status skipped: {new_status}", "FP Tracking Debug")
            return
            
        # Get user info
        current_user = frappe.session.user
        user_roles = frappe.get_roles(current_user)
        role_priority = ["Purchase Manager", "Procurement Officer", "System Manager", "Administrator"]
        responsible_role = next((r for r in role_priority if r in user_roles), "User")
        
        # ✅ CORRECTED: Use 'status_name' for child table field
        fp_tracking.append("status_history", {
            "status_name": new_status,  # ✅ Correct child field name
            "stage": stage_value,
            "action_datetime": now(),
            "updated_on": now(),
            "updated_by": current_user,
            "acting_user": current_user,
            "responsible_role": responsible_role
        })
        
        frappe.log_error(f"|9| Added status history row", "FP Tracking Debug")

        # ✅ Save the update
        fp_tracking.save(ignore_permissions=True)
        frappe.log_error(f"|10| SUCCESS: FP Status Tracking updated", "FP Tracking Debug")

        # ✅ Success message
        frappe.msgprint(
            _(
                "FP Status Tracking updated:<br>"
                "- Status: <b>{0}</b><br>"
                "- RFQ Reference: <b>{1}</b><br>"
                "- Tracking Doc: {2}"
            ).format(
                new_status,
                rfq_name,
                frappe.utils.get_link_to_form("FP Status Tracking", fp_tracking.name)
            ),
            title=_("Foreign Purchase Updated"),
            indicator="green"
        )

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "|🚨 FP Tracking Update Failed")
        frappe.throw(
            _("Failed to update FP Status Tracking: {0}").format(str(e)),
            title=_("Update Error")
        )