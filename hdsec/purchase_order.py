# hdsec/hdsec/purchase_order.py

import frappe
from frappe import _
from frappe.utils import now

def on_submit_po_update_fp_status(doc, method):
    """
    On Purchase Order Submit:
    - Uses EXACT field naming pattern from working RFQ hook
    - Parent: current_status
    - Child table: status_name
    - No more attribute errors
    """
    try:
        # ✅ 1. Get PO name
        po_name = doc.name
        frappe.log_error(f"|PO| Purchase Order: {po_name}", "PO Tracking Debug")

        # ✅ 2. Fetch custom_purchase_type
        custom_purchase_type = frappe.db.get_value(
            "Purchase Order", 
            po_name, 
            "custom_purchase_type"
        )
        frappe.log_error(f"|PO| custom_purchase_type: {custom_purchase_type}", "PO Tracking Debug")

        # ✅ 3. Verify it's a Foreign Purchase
        if not custom_purchase_type:
            frappe.log_error("|PO| No custom_purchase_type set", "PO Tracking Debug")
            return
            
        purchase_type_name = frappe.db.get_value("Purchase Type", custom_purchase_type, "name")
        if not purchase_type_name or purchase_type_name != "Foreign":
            frappe.log_error(f"|PO| Not Foreign Purchase (found: {purchase_type_name})", "PO Tracking Debug")
            return

        # ✅ 4. Get material_request from ITEMS
        material_request = None
        items = frappe.get_all(
            "Purchase Order Item",
            filters={"parent": po_name},
            fields=["material_request"],
            limit=1
        )
        
        if items and items[0].material_request:
            material_request = items[0].material_request
            frappe.log_error(f"|PO| Found material_request from items: {material_request}", "PO Tracking Debug")
        else:
            frappe.throw(
                _("No Material Request linked in PO items for {0}").format(po_name),
                title=_("Missing Link")
            )

        # ✅ 5. Find FP Status Tracking
        fp_tracking_name = frappe.db.exists(
            "FP Status Tracking",
            {"requisition_reference": material_request}
        )
        
        frappe.log_error(f"|PO| FP Tracking lookup: requisition_reference={material_request} → Found={fp_tracking_name}", "PO Tracking Debug")
        
        if not fp_tracking_name:
            frappe.throw(
                _("No FP Status Tracking found for Material Request {0}").format(material_request),
                title=_("Tracking Missing")
            )

        # ✅ 6. Load and update FP Status Tracking
        fp_tracking = frappe.get_doc("FP Status Tracking", fp_tracking_name)
        
        # ✅ Set new status
        new_status = "Purchase Order Created"
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
        
        frappe.log_error(f"|PO| Setting status: {new_status} | stage: {stage_value}", "PO Tracking Debug")

        # ✅ Update PARENT document fields
        fp_tracking.current_status = new_status  # ✅ Parent field
        fp_tracking.current_stage = stage_value
        fp_tracking.po_reference = po_name

        # ✅ CORRECTED: Check for duplicates using CHILD table field name
        # Based on your working RFQ hook, child table uses 'status_name'
        duplicate = False
        for row in fp_tracking.status_history:
            # ✅ CHILD table uses 'status_name' (NOT 'current_status')
            if row.status_name == new_status:
                duplicate = True
                break
                
        if duplicate:
            frappe.log_error(f"|PO| Duplicate status skipped: {new_status}", "PO Tracking Debug")
            return
            
        # Get user info
        current_user = frappe.session.user
        user_roles = frappe.get_roles(current_user)
        role_priority = ["Purchase Manager", "Procurement Officer", "System Manager", "Administrator"]
        responsible_role = next((r for r in role_priority if r in user_roles), "User")
        
        # ✅ CORRECTED: Use 'status_name' for child table field
        fp_tracking.append("status_history", {
            "status_name": new_status,  # ✅ Child table field name
            "stage": stage_value,
            "action_datetime": now(),
            "updated_on": now(),
            "updated_by": current_user,
            "acting_user": current_user,
            "responsible_role": responsible_role
        })
        
        frappe.log_error(f"|PO| Added status history row", "PO Tracking Debug")

        # ✅ Save update
        fp_tracking.save(ignore_permissions=True)
        frappe.log_error(f"|PO| SUCCESS: FP Status Tracking updated", "PO Tracking Debug")

        # ✅ Success message
        frappe.msgprint(
            _(
                "FP Status Tracking updated:<br>"
                "- Status: <b>{0}</b><br>"
                "- PO Reference: <b>{1}</b><br>"
                "- Tracking Doc: {2}"
            ).format(
                new_status,
                po_name,
                frappe.utils.get_link_to_form("FP Status Tracking", fp_tracking.name)
            ),
            title=_("Foreign Purchase Updated"),
            indicator="green"
        )

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "|🚨 PO Tracking Update Failed")
        frappe.throw(
            _("Failed to update FP Status Tracking: {0}").format(str(e)),
            title=_("Update Error")
        )