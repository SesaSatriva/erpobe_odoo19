from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ErpObeMasterGrade(models.Model):
    _name = "erpobe.master.grade"
    _description = "Master Grade (Global)"
    _rec_name = "name"

    name = fields.Char(string="Grade", required=True)  # A, B, C
    nilai_min = fields.Float(required=True)
    nilai_max = fields.Float(required=True)
    bobot = fields.Float(string="Bobot IPK")  # Opsional: 4.0, 3.0

    # Deskripsi Standar (Template)
    keterangan_standar = fields.Text(string="Keterangan Default")

    @api.constrains("nilai_min", "nilai_max")
    def _check_grade_range(self):
        for grade in self:
            if grade.nilai_min > grade.nilai_max:
                raise ValidationError("Batas minimum grade tidak boleh lebih besar dari batas maksimum.")
            overlapping = self.search([
                ("id", "!=", grade.id),
                ("nilai_min", "<=", grade.nilai_max),
                ("nilai_max", ">=", grade.nilai_min),
            ], limit=1)
            if overlapping:
                raise ValidationError(
                    f"Rentang grade tumpang tindih dengan grade {overlapping.name}."
                )

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._recompute_dependent_grades()
        return records

    def write(self, vals):
        result = super().write(vals)
        if {"nilai_min", "nilai_max", "bobot", "name"} & set(vals):
            self._recompute_dependent_grades()
        return result

    def unlink(self):
        result = super().unlink()
        self.env["erpobe.report.khs.mk"].sudo().search([])._compute_grade()
        return result

    def _recompute_dependent_grades(self):
        report_lines = self.env["erpobe.report.khs.mk"].sudo().search([])
        if report_lines:
            report_lines._compute_grade()
