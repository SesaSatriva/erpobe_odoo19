from odoo import models, fields

class ErpObeAkademikCplMkCpmk(models.Model):
    _name = "erpobe.akademik.cpl.mk.cpmk"
    _description = "Mapping CPL - CPMK"
    _rec_name = "cpmk_id"

    # PERBAIKAN: Hapus akhiran _ids pada Many2one
    cpl_id = fields.Many2one("erpobe.akademik.cpl", required=True, ondelete="cascade")
    cpmk_id = fields.Many2one("erpobe.akademik.cpmk", required=True, ondelete="cascade")

    # Field MK diambil via related dari CPMK untuk mencegah inkonsistensi
    mk_id = fields.Many2one(
        related="cpmk_id.mk_id", store=True, readonly=True, string="Mata Kuliah"
    )

    _uniq_mapping_constraint = models.Constraint('unique(cpl_id, cpmk_id)', 'Relasi CPL dan CPMK ini sudah didefinisikan.')
