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

    prodi_id = fields.Many2one(
        related="mk_id.prodi_id", store=True, readonly=True, index=True
    )
    weight_status = fields.Selection(
        [
            ("missing", "Belum Ada RPS Aktif"),
            ("incomplete", "Bobot Belum Lengkap"),
            ("complete", "Bobot Lengkap"),
        ],
        string="Status Bobot",
        compute="_compute_weight_status",
    )

    fakultas_id = fields.Many2one(
        related="prodi_id.fakultas_id", store=True, readonly=True, index=True
    )

    @api.depends('cpl_mapping_ids.cpl_id')
    def _compute_cpl_ids(self):
        for rec in self:
            # Menggunakan operator OR dengan recordset kosong untuk mencegah RPC_ERROR
            rec.cpl_ids = rec.cpl_mapping_ids.mapped('cpl_id') or self.env['erpobe.akademik.cpl']

    @api.depends(
        "mk_id.rps_ids.weight_status",
        "mk_id.rps_ids.tahun_ajaran_id.aktif",
        "mk_id.rps_ids.bobot_cpmk_cpl_ids.bobot_cpmk_cpl",
        "mk_id.rps_ids.bobot_cpmk_mk_ids.bobot_cpmk_mk",
        "mk_id.rps_ids.bobot_komponen_cpmk_ids.bobot_komponen_cpmk",
    )
    def _compute_weight_status(self):
        validator = self.env["erpobe.weight.validation"]
        for cpmk in self:
            active_rps = cpmk.mk_id.rps_ids.filtered(
                lambda rps: rps.tahun_ajaran_id.aktif and cpmk in rps.cpmk_ids
            )
            if not active_rps:
                cpmk.weight_status = "missing"
                continue
            status = "complete"
            for rps in active_rps:
                groups = validator.get_rps_summary(rps)
                if any(
                    group.get("cpmk_id") == cpmk.id
                    and group["status"] != "complete"
                    for group in groups
                    if group["relation"] in ("cpmk_cpl", "komponen_cpmk")
                ):
                    status = "incomplete"
                    break
                mk_group = next(
                    (group for group in groups if group["relation"] == "cpmk_mk"),
                    None,
                )
                if mk_group and mk_group["status"] != "complete":
                    status = "incomplete"
                    break
            cpmk.weight_status = status
    _uniq_cpmk_mk_constraint = models.Constraint('unique(mk_id, kode_cpmk)', 'Kode CPMK tidak boleh kembar dalam satu MK.')
