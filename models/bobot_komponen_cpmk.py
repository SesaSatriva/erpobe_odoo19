from odoo import models, fields, api
from odoo.exceptions import ValidationError

from .weight_validation import _weight_status

class ErpObeBobotKomponenCpmk(models.Model):
    _name = "erpobe.bobot.komponen.cpmk"
    _inherit = ["erpobe.rps.lock.mixin", "erpobe.audit.mixin"]
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
        required=False,
        ondelete="restrict",
    )
    rps_komponen_id = fields.Many2one(
        "erpobe.akademik.rps.komponen",
        string="Snapshot Komponen RPS",
        ondelete="cascade",
        index=True,
    )

    bobot_komponen_cpmk = fields.Float(
        string="Bobot (%)",
        required=True,
    )

    total_bobot = fields.Float(
        string="Total alokasi (%)", compute="_compute_validitas", digits=(5, 2)
    )
    remaining_bobot = fields.Float(
        string="Sisa alokasi (%)",
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
        "rps_komponen_id",
        "rps_id.bobot_komponen_cpmk_ids.bobot_komponen_cpmk",
        "rps_id.bobot_komponen_cpmk_ids.cpmk_id",
        "rps_id.bobot_komponen_cpmk_ids.rps_komponen_id",
    )
    def _compute_validitas(self):
        for rec in self:
            if rec.rps_komponen_id:
                allocations = rec.rps_komponen_id.allocation_ids.filtered(
                    lambda line: line.rps_id == rec.rps_id
                )
            else:
                allocations = rec.rps_id.bobot_komponen_cpmk_ids.filtered(
                    lambda line: line.cpmk_id == rec.cpmk_id
                )
            total = sum(allocations.mapped("bobot_komponen_cpmk"))
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
            if record.rps_komponen_id and (
                record.rps_komponen_id.rps_id != record.rps_id
                or (
                    record.rps_komponen_id.komponen_id
                    and record.rps_komponen_id.komponen_id
                    != record.komponen_penilaian
                )
            ):
                raise ValidationError(
                    "Alokasi harus mengacu pada snapshot komponen dan RPS yang sama."
                )

    @api.constrains("rps_id", "rps_komponen_id", "cpmk_id")
    def _check_unique_snapshot_allocation(self):
        for record in self.filtered("rps_komponen_id"):
            duplicates = self.search_count(
                [
                    ("id", "!=", record.id),
                    ("rps_komponen_id", "=", record.rps_komponen_id.id),
                    ("cpmk_id", "=", record.cpmk_id.id),
                ]
            )
            if duplicates:
                raise ValidationError(
                    "Kombinasi snapshot komponen–CPMK tidak boleh duplikat."
                )
