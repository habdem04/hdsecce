import frappe
@frappe.whitelist()
def get_permission_query_conditions(user=None):
    if not user:
        user = frappe.session.user

    roles = frappe.get_roles(user)
    
    # Full access for Administrator and System Manager
    if "Administrator" in roles or "System Manager" in roles:
        return ""
    
    # Full access for Stock Manager and Accounts User
    if "Stock Manager" in roles or "Accounts User" in roles:
        return ""
    
    # Sales roles can only access records with purpose 'Delivery'
    if "Sales User" in roles or "Sales Manager" in roles:
        return """(`tabPick List`.purpose = 'Delivery')"""
    
    # Manufacturing roles can access all records EXCEPT 'Delivery'
    if "Manufacturing User" in roles or "Manufacturing Manager" in roles:
        return """(`tabPick List`.purpose != 'Delivery')"""
    
    # Stock User can access all records EXCEPT 'Delivery'
    if "Stock User" in roles:
        return """(`tabPick List`.purpose != 'Delivery')"""
    
    # No access for all other roles
    return "1=0"