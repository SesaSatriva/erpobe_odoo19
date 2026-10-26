from odoo import models, fields


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
