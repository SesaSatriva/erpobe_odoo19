from odoo import api, fields, models

class ErpObeAkademikCpl(models.Model):
    _name = "erpobe.akademik.cpl"
    _description = "Capaian Pembelajaran Lulusan (CPL)"
    _rec_name = "kode_cpl"  

    name = fields.Text(string="Deskripsi CPL", required=True)
    kode_cpl = fields.Char(string="Kode CPL", required=True, index=True)
    indikator_capaian = fields.Text(string="Indikator Capaian")
    target_nilai = fields.Float(string="Target Nilai", default=70.0, required=True)
    jenis_cpl = fields.Selection(
        [
            ("sikap", "Sikap"),
            ("pengetahuan", "Pengetahuan"),
            ("keterampilan_umum", "Keterampilan Umum"),
            ("keterampilan_khusus", "Keterampilan Khusus"),
            ("lainnya", "Lainnya"),
        ],
        string="Jenis CPL",
        default="lainnya",
        required=True,
        index=True,
    )
    prodi_id = fields.Many2one(
        "erpobe.master.prodi", required=True, ondelete="restrict", index=True
    )
    fakultas_id = fields.Many2one(
        related="prodi_id.fakultas_id", store=True, readonly=True, index=True
    )

    # Relasi balik untuk kemudahan tracing
    cpmk_mapping_ids = fields.One2many(
        "erpobe.akademik.cpl.mk.cpmk", "cpl_id", string="Mapping CPMK"
    )
    mk_mapping_ids = fields.One2many(
        "erpobe.akademik.mk.cpl", "cpl_id", string="Mapping Mata Kuliah"
    )

    _uniq_kode_cpl_constraint = models.Constraint(
        "unique(prodi_id, kode_cpl)", "Kode CPL harus unik dalam prodi."
    )

    @api.depends("kode_cpl", "name")
    def _compute_display_name(self):
        for record in self:
            record.display_name = (
                f"{record.kode_cpl}: {record.name}"
                if record.name
                else record.kode_cpl
            )
