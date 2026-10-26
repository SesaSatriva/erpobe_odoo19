from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_compare


class ErpObeBobotCpmkCpl(models.Model):
    _name = "erpobe.bobot.cpmk.cpl"
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

    _uniq_rps_cpmk_cpl_constraint = models.Constraint('unique(rps_id, cpl_id, cpmk_id)', 'Relasi CPMK dan CPL ini sudah ada di RPS ini.')
    _bobot_range_constraint = models.Constraint('CHECK(bobot_cpmk_cpl >= 0 AND bobot_cpmk_cpl <= 100)', 'Bobot harus di antara 0 dan 100 persen.')

    @api.constrains("bobot_cpmk_cpl", "cpl_id")
    def _check_total_bobot_per_cpl_global(self):
        for rec in self:
            if not rec.cpl_id:
                continue

            # Mencari semua mapping yang menggunakan CPL yang sama di seluruh sistem
            all_mappings = self.search([
                ("cpl_id", "=", rec.cpl_id.id)
            ])

            # Cek jika masih ada bobot yang belum diisi (0.0)
            if any(float_compare(line.bobot_cpmk_cpl, 0.0, precision_digits=2) <= 0 for line in all_mappings):
                continue

            total_bobot = sum(all_mappings.mapped("bobot_cpmk_cpl"))

            # Validasi apakah total tepat 100%
            if float_compare(total_bobot, 100.0, precision_digits=2) != 0:
                raise ValidationError(
                    f"Validasi Global: Total kontribusi CPMK terhadap CPL "
                    f"'{rec.cpl_id.kode_cpl}' harus berjumlah 100%.\n"
                    f"Total saat ini di seluruh mata kuliah: {total_bobot:.2f}%."
                )
