import frappe
import re
from frappe import _
from frappe.model.document import Document


class MDMOrgHeader(Document):

    def validate(self):
        """Main validation entry"""
        self.validate_duplicate_code()
        self.validate_email()
        self.validate_required_fields()
        self.is_valid = 1

    # -----------------------------
    # VALIDATIONS
    # -----------------------------

    def validate_duplicate_code(self):
        """Check duplicate organization code (E9012)"""
        if not self.code:
            frappe.throw(_("Organization Code is required"))

        existing = frappe.db.exists(
            "MDM Org Header",
            {"code": self.code, "name": ["!=", self.name]}
        )

        if existing:
            frappe.throw(_("E9012 - Duplicate Organization Code"))

    def validate_required_fields(self):
        """Basic required fields validation"""
        required_fields = [
            "oad_address1",
            "oad_city",
            "oad_state",
            "oad_country_code"
        ]

        for field in required_fields:
            if not self.get(field):
                frappe.throw(_(f"{field} is required"))

    def validate_email(self):
        """Email format validation"""
        if self.oad_email:
            pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
            if not re.match(pattern, self.oad_email):
                frappe.throw(_("Invalid Email Format"))

    # -----------------------------
    # BEFORE SAVE
    # -----------------------------

    def before_save(self):
        """Executed before insert/update"""
        self.set_modified_info()
        self.generate_ogno()
        self.format_phone()

    def set_modified_info(self):
        """Set timestamps"""
        self.modified_datetime = frappe.utils.now()
        self.modified_by_user = frappe.session.user

    # -----------------------------
    # BUSINESS LOGIC
    # -----------------------------

    def generate_ogno(self):
        """Auto generate organization number"""
        if not self.ogno:
            self.ogno = "ORG-" + frappe.utils.now_datetime().strftime("%Y%m%d%H%M%S")

    def format_phone(self):
        """Simple phone formatting"""
        if self.oad_phone:
            self.oad_phone = self.oad_phone.replace(" ", "").replace("-", "")

    # -----------------------------
    # HIERARCHY METHODS
    # -----------------------------

    def get_parent_chain(self):
        """Get parent hierarchy"""
        chain = [self.name]
        parent = self.self_fk

        while parent:
            chain.append(parent)
            parent = frappe.db.get_value("MDM Org Header", parent, "self_fk")

        return chain
