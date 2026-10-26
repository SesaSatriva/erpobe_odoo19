from odoo import models, fields

class ErpObeAkademikKomponen(models.Model):
    _name = "erpobe.akademik.komponen"
    _description = "Komponen Penilaian (Paten)"
    _rec_name = "name"

    name = fields.Char(string="Nama Komponen", required=True, readonly=True)
    tipe = fields.Selection(
        [
            ("kognitif", "Kognitif"),
            ("partisipatif", "Partisipatif"),
        ],
        required=True,
        readonly=True,
    )

    aktif = fields.Boolean(default=True, readonly=True)
    color = fields.Integer(string="Color Index")
    