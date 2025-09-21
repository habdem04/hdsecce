import frappe
from frappe.utils import now

def update_workflow_fields(doc, method):
    """
    Update Material Request custom fields based on the current workflow state.
    All status fields are derived from doc.workflow_state.
    The currently logged-in employee is loaded from the Employee Signature doctype,
    and both the full name and signature are used to update the document.
    """
    current_user = frappe.session.user
    current_datetime = now()

    # Load the Employee Signature record for the current user.
    try:
        employee_signature = frappe.get_doc("Employee Signature", {"user": current_user})
    except Exception as e:
        frappe.throw("Employee Signature record not found for the current user.")

    # Retrieve employee details
    employee_full_name = employee_signature.get("full_name") or current_user
    employee_user_signature = employee_signature.get("signature")  # Ensure this field exists in your Employee Signature doctype

    user_roles = frappe.get_roles(current_user)

    # Helper function to check if the current user has one of the required roles
    def has_role(required_roles):
        return any(role in user_roles for role in required_roles)

    # 1. Draft – require "Material Requestor"
    if doc.workflow_state == "MR Requested":
        if has_role(["Material Requestor"]):
            doc.set("custom_mr_prepared_by_status", doc.workflow_state)
            doc.set("custom_mr_prepared_date", current_datetime)
            doc.set("custom_mr_requested_by", employee_full_name)
            doc.set("custom_mr_requested_by_signature", employee_user_signature)
        else:
            frappe.msgprint("Draft state update skipped: You must have the 'Material Requestor' role.")
            return

    # 2. Material Request Approved – require "Material Requestor Approver"
    elif doc.workflow_state == "Material Request Approved":
        if has_role(["Material Requestor Approver"]):
            doc.set("custom_mr_request_approval_status", doc.workflow_state)
            doc.set("custom_mr_request_approval_date", current_datetime)
            doc.set("custom_mr_request_approved_by_", employee_full_name)
            doc.set("custom_mr_request_approved_by_signature", employee_user_signature)
            if not doc.get("custom_mr_requested_by"):
                doc.set("custom_mr_requested_by", employee_full_name)
                doc.set("custom_mr_requested_by_signature", employee_user_signature)
        else:
            frappe.msgprint("Update skipped for 'Material Request Approved': Insufficient role (requires Material Requestor Approver).")
            return

    # 3. Material Request Rejected – require "Material Requestor Approver"
    elif doc.workflow_state == "Material Request Rejected":
        if has_role(["Material Requestor Approver"]):
            doc.set("custom_mr_request_approval_status", doc.workflow_state)
            doc.set("custom_mr_request_approval_date", current_datetime)
            doc.set("custom_mr_request_approved_by_", employee_full_name)
            doc.set("custom_mr_request_approved_by_signature", employee_user_signature)
        else:
            frappe.msgprint("Update skipped for 'Material Request Rejected': Insufficient role.")
            return
        

    # 2. Material Request Approved – require By Chinese After Ethiopian Approved the request
    elif doc.workflow_state == "MR Approved(物料申请已批准)":
        if has_role(["Chinese MR Approver"]):
            doc.set("custom_mr_request_approval_status_ch", doc.workflow_state)
            doc.set("custom_mr_request_approval_date_ch", current_datetime)
            doc.set("custom_mr_request_approved_by_ch", employee_full_name)
            doc.set("custom_mr_request_approved_by_signature_ch", employee_user_signature)
            if not doc.get("custom_mr_request_approved_by_ch"):
                doc.set("custom_mr_request_approved_by_ch", employee_full_name)
                doc.set("custom_mr_request_approved_by_signature_ch", employee_user_signature)
        else:
            frappe.msgprint("Update skipped for 'Material Request Approved by Chinese': Insufficient role (requires Material Chinese MR Approver ).")
            return

    # 3. Material Request Rejected – require "Material Requestor Approver"
    elif doc.workflow_state == "MR Rejected (物料申请已拒绝)":
        if has_role(["Chinese MR Approver"]):
            doc.set("custom_mr_request_approval_status_ch", doc.workflow_state)
            doc.set("custom_mr_request_approval_date_ch", current_datetime)
            doc.set("custom_mr_request_approved_by_ch", employee_full_name)
            doc.set("custom_mr_request_approved_by_signature_ch", employee_user_signature)
        else:
            frappe.msgprint("Update skipped for 'Material Request Rejected': Insufficient role.")
            return
        
    # 4. MR Reviewed by Requestor – require "Material Requestor"
    elif doc.workflow_state == "MR Reviewed by Requestor":
        if has_role(["Material Requestor"]):
            doc.set("custom_mr_prepared_by_status", doc.workflow_state)
            doc.set("custom_mr_prepared_date", current_datetime)
            doc.set("custom_mr_requested_by", employee_full_name)
            doc.set("custom_mr_requested_by_signature", employee_user_signature)
        else:
            frappe.msgprint("Update skipped for 'MR Reviewed by Requestor': Insufficient role.")
            return

    # 5. Stock Verification – require ("Stock User" or "Store Checker")
    elif doc.workflow_state in ["MR Request Verified and Accepted", "MR Request Verified and Not Accepted", "MR Reviewed By Stock Cheker"]:
        if has_role(["Stock User", "Store Checker"]):
            doc.set("custom_mr_stock_verification_status", doc.workflow_state)
            doc.set("custom_mr_stock_verification_date", current_datetime)
            doc.set("custom_mr_stock_verified_by", employee_full_name)
            doc.set("custom_mr_stock_verified_by_signature", employee_user_signature)
        else:
            frappe.msgprint("Update skipped for stock verification: Insufficient role (requires Stock User or Store Checker).")
            return

    # 6. Stock Approval – require ("Property Head" or "Stock Manager")
    elif doc.workflow_state in ["MR Approved By Property Head", "PR Approved By Property Head"]:
        if has_role(["Property Head", "Stock Manager"]):
            doc.set("custom_mr_stock_approval_status", doc.workflow_state)
            doc.set("custom_mr_stock_approval_date", current_datetime)
            doc.set("custom_mr_stock_approved_by", employee_full_name)
            doc.set("custom_mr_stock_approved_by_signature", employee_user_signature)
        else:
            frappe.msgprint("Update skipped for stock approval: Insufficient role (requires Property Head or Stock Manager).")
            return

    # 7. Stock Rejection – require ("Property Head" or "Stock Manager")
    elif doc.workflow_state in ["MR Rejected By Property Head", "PR Rejected By Property Head"]:
        if has_role(["Property Head", "Stock Manager"]):
            doc.set("custom_mr_stock_approval_status", doc.workflow_state)
            doc.set("custom_mr_stock_approval_date", current_datetime)
            doc.set("custom_mr_stock_approved_by", employee_full_name)
            doc.set("custom_mr_stock_approved_by_signature", employee_user_signature)
        else:
            frappe.msgprint("Update skipped for stock rejection: Insufficient role.")
            return

    # # 8. Approved/Rejected PR – require "Purchase Manager"
    # elif doc.workflow_state in ["Approved PR", "Rejected PR"]:
    #     if has_role(["Purchase Manager"]):
    #         doc.set("custom_pr_approval_status", doc.workflow_state)
    #         doc.set("custom_pr_approval_date", current_datetime)
    #         doc.set("custom_pr_approved_by", employee_full_name)
    #         doc.set("custom_pr_approved_by_signature", employee_user_signature)
    #     else:
    #         frappe.msgprint("Update skipped for PR approval/rejection: Insufficient role (requires Purchase Manager).")
    #         return
 # 8. Approved/Rejected PR – require "Purchase Manager"
    elif doc.workflow_state in ["Budget Approved", "Budget Rejected"]:
        if has_role(["Budget Control"]):
            doc.set("custom_pr_approval_status", doc.workflow_state)
            doc.set("custom_pr_approval_date", current_datetime)
            doc.set("custom_pr_approved_by", employee_full_name)
            doc.set("custom_pr_approved_by_signature", employee_user_signature)
        else:
            frappe.msgprint("Update skipped for PR approval/rejection: Insufficient role (requires Purchase Manager).")
            return
    # 9. Authorized/Unauthorized PR – require "GM"
    elif doc.workflow_state in ["Authorized PR", "Unauthorized PR"]:
        if has_role(["GM"]):
            doc.set("custom_authorization_status", doc.workflow_state)
            doc.set("custom_pr_authorization_date", current_datetime)
            doc.set("custom_pr_authorized_by", employee_full_name)
            doc.set("custom_pr_authorized_by_signature", employee_user_signature)
        else:
            frappe.msgprint("Update skipped for PR authorization: Insufficient role (requires GM).")
            return

    frappe.logger().info(
        f"[Workflow Update] Document '{doc.name}' updated to state '{doc.workflow_state}' by employee {employee_full_name}"
    )





def update_SE_workflow_fields(doc, method):
    """
    Update Stock Entry  custom fields based on the current workflow state,
    using only allowed roles defined in the workflow image/table.
    
    Workflow States & Allowed Roles:
      - Approved:                Allowed Role: Stock User
      - Rejected:                Allowed Role: Purchase Manager
      - Pending Approval (Review): Allowed Role: Stock User
      - Unreceived By Requestor: Allowed Role: Requester
      - Received By Requestor:   Allowed Roles: Requester or Report Manager
      - Cancelled:               Allowed Role: Purchase Manager
    """
    current_user = frappe.session.user
    current_datetime = now()

    # Load the Employee Signature record for the current user.
    try:
        employee_signature_doc = frappe.get_doc("Employee Signature", {"user": current_user})
    except Exception as e:
        frappe.throw("Employee Signature record not found for the current user.")

    # Retrieve employee details.
    employee_full_name = employee_signature_doc.get("full_name") or current_user
    employee_signature = employee_signature_doc.get("signature")  # Ensure this field exists

    # Get the current user's roles.
    user_roles = frappe.get_roles(current_user)
    
    # Helper function to check if the current user has any of the required roles.
    def has_role(required_roles):
        return any(role in user_roles for role in required_roles)
    
     # Process based on workflow state.
    if has_role(["Stock User","Material Request Issuer"]):
        if doc.workflow_state == "Pending Approval" or doc.workflow_state == "MR Issued by Store" :
        # Row 1: From Pending Approval to Approved requires Stock User.
        
            doc.set("custom_prepared_by_document_status", doc.workflow_state)
            doc.set("custom_prepared_by", employee_full_name)
            doc.set("custom_prepared_date", current_datetime)
            doc.set("custom_prepared_by_signature", employee_signature)
        # else:
        #     frappe.msgprint("Update skipped for 'Pending Approval': Insufficient role (requires Stock User).")
        #     return


 # Process based on workflow state.
    if doc.workflow_state == "Checked By (Store Supervisor)" or doc.workflow_state == "Rejected By (Store Supervisor)":
        # Row 1: From Pending Approval to Approved requires Stock User.
        if has_role(["Stock Manager","Store Checker"]):
            doc.set("custom_checked_by_document_status", doc.workflow_state)
            doc.set("custom_checked_by", employee_full_name)
            doc.set("custom_checked_by_date", current_datetime)
            doc.set("custom_checked_by_signature", employee_signature)
        else:
            frappe.msgprint("Update skipped for 'Approved': Insufficient role (requires Stock User).")
            return

    elif doc.workflow_state == "Rejected By (Prop Head)":
        # Row 2: From Pending Approval to Rejected requires Purchase Manager.
        if has_role(["Property Head"]):
            doc.set("custom_approval_document_status", doc.workflow_state)
            doc.set("custom_document_approved_by", employee_full_name)
            doc.set("custom_approval_date", current_datetime)
            doc.set("custom_approver_signature", employee_signature)
        else:
            frappe.msgprint("Update skipped for 'Rejected': Insufficient role (requires Purchase Manager).")
            return

    # Process based on workflow state.
    if doc.workflow_state == "Approved By (Prop Head)":
        # Row 1: From Pending Approval to Approved requires Stock User.
        if has_role(["Property Head"]):
            doc.set("custom_approval_document_status", doc.workflow_state)
            doc.set("custom_document_approved_by", employee_full_name)
            doc.set("custom_approval_date", current_datetime)
            doc.set("custom_approver_signature", employee_signature)
        else:
            frappe.msgprint("Update skipped for 'Approved': Insufficient role (requires Stock User).")
            return

     # Process based on workflow state.
    if doc.workflow_state == "Pending Approval":
        # Row 1: From Pending Approval to Approved requires Stock User.
        if has_role(["Manufacturing User"]):
            doc.set("custom_prepared_by_mfg_user_document_status", doc.workflow_state)
            doc.set("custom_prepared_by_mfg", employee_full_name)
            doc.set("custom_prepared_mfg_date", current_datetime)
            doc.set("custom_prepared_by_mfg_signature", employee_signature)
        else:
            frappe.msgprint("Update skipped for 'Approved': Insufficient role (requires Stock User).")
            return

    if doc.workflow_state == "Approved (Mfg)" or doc.workflow_state == "Rejected (Mfg)":
        # Row 1: From Pending Approval to Approved requires Stock User.
        if has_role(["Manufacturing Manager"]):
            doc.set("custom_approved_by_mfg_user_document_status", doc.workflow_state)
            doc.set("custom_approved_by_mfg", employee_full_name)
            doc.set("custom_approved_mfg_date", current_datetime)
            doc.set("custom_approver_signature_mfg", employee_signature)
        else:
            frappe.msgprint("Update skipped for 'Approved': Insufficient role (requires Stock User).")
            return






    

def update_PO_workflow_fields(doc, method):
    """
    Update PO  custom fields based on the current workflow state,
    using only allowed roles defined in the workflow image/table.
    
    Workflow States & Allowed Roles:
      - Approved:                Allowed Role: GM
      - Rejected:                Allowed Role: GM
      - Pending Approval (Review): Allowed Role: Stock Manager
      - Cancelled:               Allowed Role: GM
    """
    current_user = frappe.session.user
    current_datetime = now()

    # Load the Employee Signature record for the current user.
    try:
        employee_signature_doc = frappe.get_doc("Employee Signature", {"user": current_user})
    except Exception as e:
        frappe.throw("Employee Signature record not found for the current user.")

    # Retrieve employee details.
    employee_full_name = employee_signature_doc.get("full_name") or current_user
    employee_signature = employee_signature_doc.get("signature")  # Ensure this field exists

    # Get the current user's roles.
    user_roles = frappe.get_roles(current_user)
    
    # Helper function to check if the current user has any of the required roles.
    def has_role(required_roles):
        return any(role in user_roles for role in required_roles)
    
     # Process based on workflow state.
    if doc.workflow_state == "Pending Approval":
        # Row 1: From Pending Approval to Approved requires Stock User.
        if has_role(["Purchase Manager"]):
            doc.set("custom_prepared_by_document_status", doc.workflow_state)
            doc.set("custom_prepared_by", employee_full_name)
            doc.set("custom_prepared_date", current_datetime)
            doc.set("custom_prepared_by_signature", employee_signature)
        else:
            frappe.msgprint("Update skipped for 'Pending Approved': Insufficient role (requires Purchase User).")
            return


    # Process based on workflow state.
    if doc.workflow_state == "Approved" or doc.workflow_state == "Rejected":
        # Row 1: From Pending Approval to Approved requires Purchase User.
        if has_role(["GM"]):
            doc.set("custom_approval_document_status", doc.workflow_state)
            doc.set("custom_document_approved_by", employee_full_name)
            doc.set("custom_approval_date", current_datetime)
            doc.set("custom_approver_signature", employee_signature)
        else:
            frappe.msgprint("Update skipped for 'Approved': Insufficient role (requires Purchase Manager.")
            return

    



def update_GRN_workflow_fields(doc, method):
    """
    Update Stock Entry  custom fields based on the current workflow state,
    using only allowed roles defined in the workflow image/table.
    
    Workflow States & Allowed Roles:
      - Approved:                Allowed Role: Stock User
      - Rejected:                Allowed Role: Purchase Manager
      - Pending Approval (Review): Allowed Role: Stock User
      - Unreceived By Requestor: Allowed Role: Requester
      - Received By Requestor:   Allowed Roles: Requester or Report Manager
      - Cancelled:               Allowed Role: Purchase Manager
    """
    current_user = frappe.session.user
    current_datetime = now()

    # Load the Employee Signature record for the current user.
    try:
        employee_signature_doc = frappe.get_doc("Employee Signature", {"user": current_user})
    except Exception as e:
        frappe.throw("Employee Signature record not found for the current user.")

    # Retrieve employee details.
    employee_full_name = employee_signature_doc.get("full_name") or current_user
    employee_signature = employee_signature_doc.get("signature")  # Ensure this field exists

    # Get the current user's roles.
    user_roles = frappe.get_roles(current_user)
    
    # Helper function to check if the current user has any of the required roles.
    def has_role(required_roles):
        return any(role in user_roles for role in required_roles)
    
     # Process based on workflow state.
    if has_role(["Stock User","Material Request Issuer"]):
        if doc.workflow_state == "Purchase Received（采购收货)" :
        # Row 1: From Pending Approval to Approved requires Stock User.
        
            doc.set("custom_received_by_document_status", doc.workflow_state)
            doc.set("custom_received_by", employee_full_name)
            doc.set("custom_received_by_date", current_datetime)
            doc.set("custom_received_by_signature", employee_signature)
        # else:
        #     frappe.msgprint("Update skipped for 'Purchase Reipt or GRN': Insufficient role (requires Stock User).")
        #     return

    if has_role(["Purchase User","Purchase Manager"]):
        if doc.workflow_state == "Purchase Delivered【采购交付】" :
        # Row 1: From Pending Approval to Approved requires Stock User.
        
            doc.set("custom_delivered_by_document_status", doc.workflow_state)
            doc.set("custom_delivered_by", employee_full_name)
            doc.set("custom_delivered_date", current_datetime)
            doc.set("custom_delivered_by_signature", employee_signature)
        # else:
        #     frappe.msgprint("Update skipped for 'Purchase Receipt or GRN Delivery': Insufficient role (requires Stock User).")
        #     return

 # Process Approveed by Store Head/Store Checker Role
    if doc.workflow_state == "✅Purchase Receiving Approved（采购收货已批准)" or doc.workflow_state == "❌ Purchase Receiving Rejected (采购收货被拒绝)":
        # Row 1: From Pending Approval to Approved requires Stock User.
        if has_role(["Stock Manager","Store Checker"]):
            frappe.msgprint("test")
            doc.set("custom_approved_by_document_status", doc.workflow_state)
            doc.set("custom_approved_by", employee_full_name)
            doc.set("custom_approved_by_date", current_datetime)
            doc.set("custom_approved_by_signature", employee_signature)
        # else:
        #     frappe.msgprint("Update skipped for 'Approval': Insufficient role (requires Stock User).")
        #     return

   

   
def update_Sales_Order_workflow_fields(doc, method):
    """
    Update Stock Entry  custom fields based on the current workflow state,
    using only allowed roles defined in the workflow image/table.
    
    Workflow States & Allowed Roles:
      - Approved:                Allowed Role: Stock User
      - Rejected:                Allowed Role: Purchase Manager
      - Pending Approval (Review): Allowed Role: Stock User
      - Unreceived By Requestor: Allowed Role: Requester
      - Received By Requestor:   Allowed Roles: Requester or Report Manager
      - Cancelled:               Allowed Role: Purchase Manager
    """
    current_user = frappe.session.user
    current_datetime = now()

    # Load the Employee Signature record for the current user.
    try:
        employee_signature_doc = frappe.get_doc("Employee Signature", {"user": current_user})
    except Exception as e:
        frappe.throw("Employee Signature record not found for the current user.")

    # Retrieve employee details.
    employee_full_name = employee_signature_doc.get("full_name") or current_user
    employee_signature = employee_signature_doc.get("signature")  # Ensure this field exists

    # Get the current user's roles.
    user_roles = frappe.get_roles(current_user)
    
    # Helper function to check if the current user has any of the required roles.
    def has_role(required_roles):
        return any(role in user_roles for role in required_roles)
    
     # Process based on workflow state.
    if has_role(["Sales User","Sales Manager"]):
        if doc.workflow_state == "⏰Pending Checking/待校验" :     
            doc.set("custom_prepared_by", employee_full_name)
            doc.set("custom_prepared_by_date", current_datetime)
            doc.set("custom_prepared_by_signature", employee_signature)
        # else:
        #     frappe.msgprint("Update skipped for 'Purchase Reipt or GRN': Insufficient role (requires Stock User).")
        #     return

    if has_role(["Sales Manager"]):
        if doc.workflow_state == "👤Pending Verification/核准" :
            doc.set("custom_checked_by", employee_full_name)
            doc.set("custom_checked_by_date", current_datetime)
            doc.set("custom_checked_by_signature", employee_signature)
        # else:
        #     frappe.msgprint("Update skipped for 'Purchase Receipt or GRN Delivery': Insufficient role (requires Stock User).")
        #     return

 # Process Approveed by Store Head/Store Checker Role
    if has_role(["Chinese Authorizer","GM"]):
        if doc.workflow_state == "🔄Verified/已验证" or doc.workflow_state == "❌Did Not Pass Verification/未通过验证":    
            doc.set("custom_verified_by_chinese", employee_full_name)
            doc.set("custom_verified_by_chinese_date", current_datetime)
            doc.set("custom_verified_by_chinese_signature", employee_signature)
        # else:
        #     frappe.msgprint("Update skipped for 'Approval': Insufficient role (requires Stock User).")
        #     return

    if has_role(["GM"]):
        if doc.workflow_state == "✅Approved/已批准" or doc.workflow_state == "❌Rejected/已拒绝"  :
            doc.set("custom_approved_by", employee_full_name)
            doc.set("custom_approved_by_date", current_datetime)
            doc.set("custom_approved_by_signature", employee_signature)
