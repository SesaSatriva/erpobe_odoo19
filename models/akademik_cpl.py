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

    @api.model
    def classify_type(self, kode_cpl=None, name=None, indikator=None):
        text = " ".join(
            value for value in (kode_cpl or "", name or "", indikator or "")
            if value
        ).casefold()
        sikap = (
            "etika", "jujur", "mandiri", "sikap", "tanggung jawab",
            "kerja sama", "kolaborasi", "disiplin", "nasionalisme",
            "kewarganegaraan", "social", "sosial",
        )
        umum = (
            "komunikasi", "komunikatif", "tim", "belajar sepanjang hayat",
            "pengambilan keputusan", "kelompok", "multidisiplin",
            "manajemen", "pemikiran", "inovasi",
        )
        khusus = (
            "merancang", "menganalisis", "menggunakan alat",
            "perancangan", "analisis", "rekayasa", "teknik",
            "komputasi", "memodelkan", "mengimplementasikan",
            "eksperimen", "laboratorium", "aplikasi",
        )
        pengetahuan = (
            "pengetahuan", "memahami", "menerapkan konsep", "ilmu",
            "prinsip", "teori", "matematika", "sains",
        )
        for kind, keywords in (
            ("sikap", sikap),
            ("keterampilan_umum", umum),
            ("keterampilan_khusus", khusus),
            ("pengetahuan", pengetahuan),
        ):
            if any(keyword in text for keyword in keywords):
                return kind
        return "lainnya"

    @api.model_create_multi
    def create(self, vals_list):
        for values in vals_list:
            if not values.get("jenis_cpl") or values.get("jenis_cpl") == "lainnya":
                values["jenis_cpl"] = self.classify_type(
                    values.get("kode_cpl"),
                    values.get("name"),
                    values.get("indikator_capaian"),
                )
        return super().create(vals_list)

    def write(self, vals):
        for record in self:
            if any(field in vals for field in ("kode_cpl", "name", "indikator_capaian")):
                values = {
                    "kode_cpl": vals.get("kode_cpl", record.kode_cpl),
                    "name": vals.get("name", record.name),
                    "indikator_capaian": vals.get(
                        "indikator_capaian", record.indikator_capaian
                    ),
                }
                if not vals.get("jenis_cpl") or vals.get("jenis_cpl") == "lainnya":
                    vals = dict(vals)
                    vals["jenis_cpl"] = self.classify_type(
                        values["kode_cpl"], values["name"], values["indikator_capaian"]
                    )
        return super().write(vals)

    @api.depends("kode_cpl", "name")
    def _compute_display_name(self):
        for record in self:
            record.display_name = (
                f"{record.kode_cpl}: {record.name}"
                if record.name
                else record.kode_cpl
            )
