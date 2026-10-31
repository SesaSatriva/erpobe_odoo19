from odoo import models, fields, api
from odoo.exceptions import ValidationError

from .weight_validation import _weight_status

class ErpObeBobotKomponenCpmk(models.Model):
    _name = "erpobe.bobot.komponen.cpmk"
    _inherit = ["erpobe.rps.lock.mixin"]
    _description = "Bobot Komponen terhadap CPMK"
    _order = "komponen_penilaian, cpmk_id"

    rps_id = fields.Many2one(
        "erpobe.akademik.rps",
        required=True,
        ondelete="cascade",
    )

    cpmk_id = fields.Many2one(
        "erpobe.akademik.cpmk",
        required=True,
        ondelete="cascade",
    )

    komponen_penilaian = fields.Many2one(
        "erpobe.akademik.komponen",
        required=True,
        ondelete="restrict",
    )

    bobot_komponen_cpmk = fields.Float(
        string="Bobot (%)",
        required=True,
    )

    total_bobot = fields.Float(
        string="Total bobot CPMK (%)", compute="_compute_validitas", digits=(5, 2)
    )
    remaining_bobot = fields.Float(
        string="Sisa bobot CPMK (%)",
        compute="_compute_validitas",
        digits=(5, 2),
    )
    weight_status = fields.Selection(
        [
            ("complete", "Lengkap"),
            ("under", "Kurang"),
            ("over", "Melebihi"),
        ],
        compute="_compute_validitas",
    )

    _bobot_range_constraint = models.Constraint('CHECK(bobot_komponen_cpmk >= 0 AND bobot_komponen_cpmk <= 100)', 'Bobot harus 0–100%')
    _uniq_matrix_constraint = models.Constraint('UNIQUE(rps_id, komponen_penilaian, cpmk_id)', 'Kombinasi Komponen–CPMK tidak boleh duplikat.')

    prodi_id = fields.Many2one(
        related="rps_id.prodi_id", store=True, readonly=True, index=True
    )

    fakultas_id = fields.Many2one(
        related="prodi_id.fakultas_id", store=True, readonly=True, index=True
    )

    @api.depends(
        "bobot_komponen_cpmk",
        "rps_id.bobot_komponen_cpmk_ids.bobot_komponen_cpmk",
        "rps_id.bobot_komponen_cpmk_ids.cpmk_id",
    )
    def _compute_validitas(self):
        for rec in self:
            lines_cpmk = rec.rps_id.bobot_komponen_cpmk_ids.filtered(
                lambda line: line.cpmk_id == rec.cpmk_id
            )
            total_cpmk = sum(lines_cpmk.mapped("bobot_komponen_cpmk"))
            rec.total_bobot = total_cpmk
            rec.remaining_bobot = 100.0 - total_cpmk
            rec.weight_status = _weight_status(total_cpmk)[0]

    @api.constrains("rps_id", "cpmk_id")
    def _check_cpmk_faculty(self):
        for record in self:
            if record.cpmk_id.mk_id != record.rps_id.matakuliah_id:
                raise ValidationError(
                    "CPMK bobot harus berasal dari mata kuliah pada RPS."
                )
