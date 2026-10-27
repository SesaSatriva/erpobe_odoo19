from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_compare


class ErpObeBobotKomponenCpmk(models.Model):
    _name = "erpobe.bobot.komponen.cpmk"
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

    # ===== Helper status untuk UI =====
    valid_cpmk = fields.Boolean(
        compute="_compute_validitas",
        store=False,
    )
    valid_komponen = fields.Boolean(
        compute="_compute_validitas",
        store=False,
    )

    _bobot_range_constraint = models.Constraint('CHECK(bobot_komponen_cpmk >= 0 AND bobot_komponen_cpmk <= 100)', 'Bobot harus 0–100%')
    _uniq_matrix_constraint = models.Constraint('UNIQUE(rps_id, komponen_penilaian, cpmk_id)', 'Kombinasi Komponen–CPMK tidak boleh duplikat.')

    prodi_id = fields.Many2one(
        related="rps_id.prodi_id", store=True, readonly=True, index=True
    )

    fakultas_id = fields.Many2one(
        related="prodi_id.fakultas_id", store=True, readonly=True, index=True
    )

    def _compute_validitas(self):
        for rec in self:
            lines_cpmk = self.search(
                [
                    ("rps_id", "=", rec.rps_id.id),
                    ("cpmk_id", "=", rec.cpmk_id.id),
                ]
            )
            total_cpmk = sum(lines_cpmk.mapped("bobot_komponen_cpmk"))

            lines_komp = self.search(
                [
                    ("rps_id", "=", rec.rps_id.id),
                    ("komponen_penilaian", "=", rec.komponen_penilaian.id),
                ]
            )
            total_komp = sum(lines_komp.mapped("bobot_komponen_cpmk"))

            rec.valid_cpmk = float_compare(total_cpmk, 100.0, 2) == 0
            rec.valid_komponen = float_compare(total_komp, 100.0, 2) == 0

    @api.constrains("bobot_komponen_cpmk")
    def _check_bobot_dua_arah(self):
        for rec in self:
            if not rec.rps_id:
                continue

            # per CPMK
            lines_cpmk = self.search(
                [
                    ("rps_id", "=", rec.rps_id.id),
                    ("cpmk_id", "=", rec.cpmk_id.id),
                ]
            )
            total_cpmk = sum(lines_cpmk.mapped("bobot_komponen_cpmk"))
            if float_compare(total_cpmk, 100.0, 2) == 1:
                raise ValidationError(
                    f"Total bobot komponen CPMK {rec.cpmk_id.kode_cpmk} "
                    f"melebihi 100% ({total_cpmk:.2f}%)."
                )

            # per Komponen
            lines_komp = self.search(
                [
                    ("rps_id", "=", rec.rps_id.id),
                    ("komponen_penilaian", "=", rec.komponen_penilaian.id),
                ]
            )
            total_komp = sum(lines_komp.mapped("bobot_komponen_cpmk"))
            if float_compare(total_komp, 100.0, 2) == 1:
                raise ValidationError(
                    f"Total distribusi komponen {rec.komponen_penilaian.name} "
                    f"melebihi 100% ({total_komp:.2f}%)."
                )

    @api.constrains("rps_id", "cpmk_id")
    def _check_cpmk_faculty(self):
        for record in self:
            if record.cpmk_id.prodi_id != record.rps_id.prodi_id:
                raise ValidationError(
                    "Bobot CPMK harus berada di prodi mata kuliah RPS."
                )

