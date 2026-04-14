import frappe
import re
from frappe import _
from frappe.model.document import Document


class MDMOrgHeader(Document):

    # -----------------------------
    # MAIN VALIDATION
    # -----------------------------
    def validate(self):
        self.validate_duplicate_code()
        self.validate_required_fields()
        self.validate_email_format()
        self.is_valid = 1

    # -----------------------------
    # VALIDATIONS
    # -----------------------------
    def validate_duplicate_code(self):
        """E9012 - Duplicate Code Check"""
        if not self.code:
            frappe.throw(_("Organization Code is required"))

        existing = frappe.db.exists(
            "MDM Org Header",
            {"code": self.code, "name": ["!=", self.name]}
        )

        if existing:
            frappe.throw(_("E9012 - Organization Code already exists"))

    def validate_required_fields(self):
        """Required Address Fields"""
        required_fields = [
            "oad_address1",
            "oad_city",
            "oad_state",
            "oad_country_code"
        ]

        for field in required_fields:
            if not self.get(field):
                frappe.throw(_(f"{field} is required"))

    def validate_email_format(self):
        """Email Validation"""
        if self.oad_email:
            pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
            if not re.match(pattern, self.oad_email):
                frappe.throw(_("Invalid Email Format"))

    # -----------------------------
    # BEFORE SAVE
    # -----------------------------
    def before_save(self):
        self.set_modified_details()
        self.generate_ogno()
        self.format_phone()

    def set_modified_details(self):
        self.modified_datetime = frappe.utils.now()
        self.modified_by_user = frappe.session.user

    # -----------------------------
    # BUSINESS LOGIC
    # -----------------------------
    def generate_ogno(self):
        """Auto-generate organization number"""
        if not self.ogno:
            self.ogno = "ORG-" + frappe.utils.now_datetime().strftime("%Y%m%d%H%M%S")

    def format_phone(self):
        """Simple phone formatting"""
        if self.oad_phone:
            self.oad_phone = self.oad_phone.replace(" ", "").replace("-", "")

    # -----------------------------
    # HIERARCHY LOGIC
    # -----------------------------
    def get_parent_chain(self):
        chain = [self.name]
        parent = self.self_fk

        while parent:
            chain.append(parent)
            parent = frappe.db.get_value("MDM Org Header", parent, "self_fk")

        return chain
