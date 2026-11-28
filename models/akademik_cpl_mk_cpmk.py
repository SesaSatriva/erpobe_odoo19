from odoo import api, models, fields
from odoo.exceptions import ValidationError

class ErpObeAkademikCplMkCpmk(models.Model):
    _name = "erpobe.akademik.cpl.mk.cpmk"
    _inherit = ["erpobe.audit.mixin"]
    _description = "Mapping CPL - CPMK"
    _rec_name = "cpmk_id"

    # PERBAIKAN: Hapus akhiran _ids pada Many2one
    cpl_id = fields.Many2one("erpobe.akademik.cpl", required=True, ondelete="cascade")
    cpmk_id = fields.Many2one("erpobe.akademik.cpmk", required=True, ondelete="cascade")
    bobot_cpl_cpmk = fields.Float(
        string="Bobot CPL-CPMK (%)",
        default=0.0,
        help="Bobot kontribusi CPMK terhadap CPL sesuai dokumen kurikulum.",
    )

    # Field MK diambil via related dari CPMK untuk mencegah inkonsistensi
    mk_id = fields.Many2one(
        related="cpmk_id.mk_id", store=True, readonly=True, string="Mata Kuliah"
    )

    _uniq_mapping_constraint = models.Constraint('unique(cpl_id, cpmk_id)', 'Relasi CPL dan CPMK ini sudah didefinisikan.')

    prodi_id = fields.Many2one(
        related="mk_id.prodi_id", store=True, readonly=True, index=True
    )

    fakultas_id = fields.Many2one(
        related="prodi_id.fakultas_id", store=True, readonly=True, index=True
    )

    @api.constrains("cpl_id", "cpmk_id")
    def _check_cpl_prodi(self):
        for record in self:
            if record.cpl_id.prodi_id != record.prodi_id:
                raise ValidationError(
                    "CPL dan CPMK harus berasal dari prodi yang sama."
                )

    def _sync_rps_weights(self, cpmks):
        rps_records = self.env["erpobe.akademik.rps"].search(
            [("matakuliah_id", "in", cpmks.mapped("mk_id").ids)]
        )
        rps_records._sync_bobot_tables()

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._sync_rps_weights(records.mapped("cpmk_id"))
        return records

    def write(self, vals):
        affected_cpmks = self.mapped("cpmk_id")
        result = super().write(vals)
        affected_cpmks |= self.mapped("cpmk_id")
        self._sync_rps_weights(affected_cpmks)
        return result

    def unlink(self):
        affected_cpmks = self.mapped("cpmk_id")
        result = super().unlink()
        self._sync_rps_weights(affected_cpmks)
        return result


class ErpObeAkademikMkCpl(models.Model):
    _name = "erpobe.akademik.mk.cpl"
    _inherit = ["erpobe.audit.mixin"]
    _description = "Matriks Pemetaan Mata Kuliah terhadap CPL"
    _rec_name = "cpl_id"

    mk_id = fields.Many2one(
        "erpobe.master.matakuliah",
        string="Mata Kuliah",
        required=True,
        ondelete="cascade",
        index=True,
    )
    cpl_id = fields.Many2one(
        "erpobe.akademik.cpl",
        string="CPL",
        required=True,
        ondelete="cascade",
        index=True,
    )
    prodi_id = fields.Many2one(
        related="mk_id.prodi_id",
        store=True,
        readonly=True,
        index=True,
    )

    _uniq_mk_cpl_constraint = models.Constraint(
        "UNIQUE(mk_id, cpl_id)",
        "Pemetaan Mata Kuliah-CPL tidak boleh duplikat.",
    )

    @api.constrains("mk_id", "cpl_id")
    def _check_mk_cpl_prodi(self):
        for record in self:
            if record.mk_id.prodi_id != record.cpl_id.prodi_id:
                raise ValidationError(
                    "Mata kuliah dan CPL harus berasal dari prodi yang sama."
                )
