from odoo import models, fields

class ErpObeAkademikCpl(models.Model):
    _name = "erpobe.akademik.cpl"
    _description = "Capaian Pembelajaran Lulusan (CPL)"
    _rec_name = "kode_cpl"  

    name = fields.Text(string="Deskripsi CPL", required=True)
    kode_cpl = fields.Char(string="Kode CPL", required=True, index=True)
    prodi_id = fields.Many2one(
        "erpobe.master.prodi", required=True, ondelete="restrict", index=True
    )

    # Relasi balik untuk kemudahan tracing
    cpmk_mapping_ids = fields.One2many(
        "erpobe.akademik.cpl.mk.cpmk", "cpl_id", string="Mapping CPMK"
    )

    _uniq_kode_cpl_constraint = models.Constraint(
        "unique(prodi_id, kode_cpl)", "Kode CPL harus unik dalam prodi."
    )
