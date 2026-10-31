from odoo import models, fields, api
from odoo.exceptions import ValidationError

from .weight_validation import _weight_status

class ErpObeBobotCpmkMk(models.Model):
    _name = "erpobe.bobot.cpmk.mk"
    _inherit = ["erpobe.rps.lock.mixin"]
    _description = "Bobot CPMK terhadap Mata Kuliah"

    rps_id = fields.Many2one(
        "erpobe.akademik.rps",
        required=True,
        ondelete="cascade",
    )

    mk_id = fields.Many2one(
        "erpobe.master.matakuliah",
        related="rps_id.matakuliah_id",
        readonly=True,
    )

    cpmk_id = fields.Many2one(
        "erpobe.akademik.cpmk",
        required=True,
        readonly=True,
    )

    bobot_cpmk_mk = fields.Float(
        string="Bobot CPMK (%)",
    )
    total_bobot = fields.Float(
        string="Total bobot mata kuliah (%)",
        compute="_compute_total_bobot",
        digits=(5, 2),
    )
    remaining_bobot = fields.Float(
        string="Sisa bobot (%)", compute="_compute_total_bobot", digits=(5, 2)
    )
    weight_status = fields.Selection(
        [
            ("complete", "Lengkap"),
            ("under", "Kurang"),
            ("over", "Melebihi"),
        ],
        compute="_compute_total_bobot",
    )
    _bobot_range_constraint = models.Constraint('CHECK(bobot_cpmk_mk >= 0 AND bobot_cpmk_mk <= 100)', 'Bobot harus di antara 0 dan 100 persen.')


    prodi_id = fields.Many2one(
        related="rps_id.prodi_id", store=True, readonly=True, index=True
    )

    fakultas_id = fields.Many2one(
        related="prodi_id.fakultas_id", store=True, readonly=True, index=True
    )

    @api.depends("bobot_cpmk_mk", "rps_id.bobot_cpmk_mk_ids.bobot_cpmk_mk")
    def _compute_total_bobot(self):
        for rec in self:
            total = sum(rec.rps_id.bobot_cpmk_mk_ids.mapped("bobot_cpmk_mk"))
            rec.total_bobot = total
            rec.remaining_bobot = 100.0 - total
            rec.weight_status = _weight_status(total)[0]

    @api.constrains("rps_id", "cpmk_id")
    def _check_cpmk_faculty(self):
        for record in self:
            if record.cpmk_id.mk_id != record.rps_id.matakuliah_id:
                raise ValidationError(
                    "CPMK bobot harus berasal dari mata kuliah pada RPS."
                )
