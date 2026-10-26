from odoo import models, fields, api


class ErpObeAkademikCpmk(models.Model):
    _name = "erpobe.akademik.cpmk"
    _description = "Capaian Pembelajaran Mata Kuliah"
    _rec_name = "kode_cpmk"

    mk_id = fields.Many2one(
        "erpobe.master.matakuliah", required=True, ondelete="cascade"
    )
    kode_cpmk = fields.Char(required=True)
    name = fields.Text(string="Deskripsi CPMK", required=True)

    # Relasi ke CPL via Bridge Table
    cpl_mapping_ids = fields.One2many(
        "erpobe.akademik.cpl.mk.cpmk", "cpmk_id", string="Relasi CPL"
    )
    cpl_ids = fields.Many2many(
        "erpobe.akademik.cpl", 
        string="CPL Terkait", 
        compute="_compute_cpl_ids",
        store=False
    )

    @api.depends('cpl_mapping_ids.cpl_id')
    def _compute_cpl_ids(self):
        for rec in self:
            # Menggunakan operator OR dengan recordset kosong untuk mencegah RPC_ERROR
            rec.cpl_ids = rec.cpl_mapping_ids.mapped('cpl_id') or self.env['erpobe.akademik.cpl']
    _uniq_cpmk_mk_constraint = models.Constraint('unique(mk_id, kode_cpmk)', 'Kode CPMK tidak boleh kembar dalam satu MK.')
