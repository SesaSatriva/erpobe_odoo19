from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_compare


class ErpObeBobotCpmkMk(models.Model):
    _name = "erpobe.bobot.cpmk.mk"
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
    _bobot_range_constraint = models.Constraint('CHECK(bobot_cpmk_mk >= 0 AND bobot_cpmk_mk <= 100)', 'Bobot harus di antara 0 dan 100 persen.')


    prodi_id = fields.Many2one(
        related="rps_id.prodi_id", store=True, readonly=True, index=True
    )

    fakultas_id = fields.Many2one(
        related="prodi_id.fakultas_id", store=True, readonly=True, index=True
    )

    @api.constrains("bobot_cpmk_mk", "rps_id")
    def _check_total_bobot_cpmk_per_mk(self):
        for rec in self:
            rps = rec.rps_id
            if not rps:
                continue

            lines = rps.bobot_cpmk_mk_ids

            # jika ada bobot 0 → belum selesai, JANGAN validasi
            if any(float_compare(l.bobot_cpmk_mk, 0.0, precision_digits=2) <= 0 for l in lines):
                continue

            # semua sudah diisi → baru cek total
            total = sum(lines.mapped("bobot_cpmk_mk"))

            if float_compare(total, 100.0, precision_digits=2) != 0:
                raise ValidationError(
                    f"Total bobot CPMK untuk mata kuliah "
                    f"'{rps.matakuliah_id.display_name}' harus 100%. "
                    f"Saat ini {total:.2f}%."
                )

    @api.constrains("rps_id", "cpmk_id")
    def _check_cpmk_faculty(self):
        for record in self:
            if record.cpmk_id.prodi_id != record.rps_id.prodi_id:
                raise ValidationError(
                    "Bobot CPMK harus berada di prodi mata kuliah RPS."
                )

