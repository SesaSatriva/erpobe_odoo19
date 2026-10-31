from odoo import models, fields, api
from odoo.exceptions import ValidationError

from .weight_validation import _weight_status

class ErpObeBobotCpmkCpl(models.Model):
    _name = "erpobe.bobot.cpmk.cpl"
    _inherit = ["erpobe.rps.lock.mixin"]
    _description = "Bobot CPMK terhadap CPL"
    _rec_name = "cpmk_id"

    rps_id = fields.Many2one(
        "erpobe.akademik.rps",
        required=True,
        ondelete="cascade",
    )

    cpl_id = fields.Many2one(
        "erpobe.akademik.cpl",
        string="CPL",
        required=True,
    )

    cpmk_id = fields.Many2one(
        "erpobe.akademik.cpmk",
        string="CPMK",
        required=True,
    )

    bobot_cpmk_cpl = fields.Float(
        string="Bobot CPMK terhadap CPL (%)",
    )
    total_cpmk = fields.Float(
        string="Total CPMK → CPL (%)", compute="_compute_group_totals", digits=(5, 2)
    )
    remaining_cpmk = fields.Float(
        string="Sisa CPMK → CPL (%)",
        compute="_compute_group_totals",
        digits=(5, 2),
    )
    total_cpl = fields.Float(
        string="Total CPL ← CPMK (%)", compute="_compute_group_totals", digits=(5, 2)
    )
    remaining_cpl = fields.Float(
        string="Sisa CPL ← CPMK (%)",
        compute="_compute_group_totals",
        digits=(5, 2),
    )
    weight_status_cpmk = fields.Selection(
        [
            ("complete", "Lengkap"),
            ("under", "Kurang"),
            ("over", "Melebihi"),
        ],
        compute="_compute_group_totals",
    )
    weight_status_cpl = fields.Selection(
        [
            ("complete", "Lengkap"),
            ("under", "Kurang"),
            ("over", "Melebihi"),
        ],
        compute="_compute_group_totals",
    )

    _uniq_rps_cpmk_cpl_constraint = models.Constraint('unique(rps_id, cpl_id, cpmk_id)', 'Relasi CPMK dan CPL ini sudah ada di RPS ini.')
    _bobot_range_constraint = models.Constraint('CHECK(bobot_cpmk_cpl >= 0 AND bobot_cpmk_cpl <= 100)', 'Bobot harus di antara 0 dan 100 persen.')

    prodi_id = fields.Many2one(
        related="rps_id.prodi_id", store=True, readonly=True, index=True
    )

    fakultas_id = fields.Many2one(
        related="prodi_id.fakultas_id", store=True, readonly=True, index=True
    )

    @api.depends(
        "bobot_cpmk_cpl",
        "rps_id.bobot_cpmk_cpl_ids.bobot_cpmk_cpl",
        "rps_id.bobot_cpmk_cpl_ids.cpmk_id",
        "rps_id.bobot_cpmk_cpl_ids.cpl_id",
    )
    def _compute_group_totals(self):
        for rec in self:
            cpmk_lines = rec.rps_id.bobot_cpmk_cpl_ids.filtered(
                lambda line: line.cpmk_id == rec.cpmk_id
            )
            cpl_lines = rec.rps_id.bobot_cpmk_cpl_ids.filtered(
                lambda line: line.cpl_id == rec.cpl_id
            )
            rec.total_cpmk = sum(cpmk_lines.mapped("bobot_cpmk_cpl"))
            rec.remaining_cpmk = 100.0 - rec.total_cpmk
            rec.total_cpl = sum(cpl_lines.mapped("bobot_cpmk_cpl"))
            rec.remaining_cpl = 100.0 - rec.total_cpl
            rec.weight_status_cpmk = _weight_status(rec.total_cpmk)[0]
            rec.weight_status_cpl = _weight_status(rec.total_cpl)[0]

    @api.constrains("rps_id", "cpmk_id")
    def _check_cpmk_faculty(self):
        for record in self:
            if record.cpmk_id.mk_id != record.rps_id.matakuliah_id:
                raise ValidationError(
                    "CPMK bobot CPL harus berasal dari mata kuliah pada RPS."
                )
            if record.cpl_id.prodi_id != record.rps_id.prodi_id:
                raise ValidationError("CPL bobot harus berasal dari prodi RPS.")
