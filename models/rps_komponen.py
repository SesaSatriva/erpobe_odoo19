from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ErpObeAkademikRpsKomponen(models.Model):
    _name = "erpobe.akademik.rps.komponen"
    _description = "Snapshot Komponen Penilaian RPS"
    _inherit = ["erpobe.rps.lock.mixin"]
    _order = "sequence, id"

    rps_id = fields.Many2one(
        "erpobe.akademik.rps", required=True, ondelete="cascade", index=True
    )
    komponen_id = fields.Many2one(
        "erpobe.akademik.komponen", ondelete="set null", index=True
    )
    name = fields.Char(string="Nama Komponen", required=True)
    description = fields.Text(string="Deskripsi")
    bobot = fields.Float(string="Bobot Mata Kuliah (%)", default=0.0)
    aktif = fields.Boolean(string="Aktif", default=True)
    sequence = fields.Integer(default=10)
    source = fields.Selection(
        [
            ("catalog", "Katalog"),
            ("custom", "Kustom RPS"),
            ("legacy", "Migrasi Legacy"),
        ],
        default="catalog",
        required=True,
    )
    allocation_ids = fields.One2many(
        "erpobe.bobot.komponen.cpmk", "rps_komponen_id", string="Alokasi CPMK"
    )

    _bobot_range_constraint = models.Constraint(
        "CHECK(bobot >= 0 AND bobot <= 100)",
        "Bobot komponen harus berada pada rentang 0–100.",
    )
    _uniq_rps_catalog_constraint = models.Constraint(
        "UNIQUE(rps_id, komponen_id)",
        "Komponen katalog tidak boleh duplikat dalam satu RPS.",
    )

    @api.constrains("bobot", "rps_id")
    def _check_bobot_and_rps_course(self):
        for record in self:
            if record.bobot < 0 or record.bobot > 100:
                raise ValidationError("Bobot komponen harus berada pada rentang 0–100.")
