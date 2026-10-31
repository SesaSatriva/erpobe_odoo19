from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class ErpObeMasterFakultas(models.Model):
    _name = "erpobe.master.fakultas"
    _description = "Master Fakultas"
    _order = "name"

    name = fields.Char(required=True, index=True)
    kode = fields.Char(required=True, index=True)
    active = fields.Boolean(default=True)
    prodi_ids = fields.One2many(
        "erpobe.master.prodi", "fakultas_id", string="Program Studi"
    )
    metode_pembelajaran_ids = fields.One2many(
        "erpobe.akademik.metode.pembelajaran",
        "fakultas_id",
        string="Metode Pembelajaran",
    )
    referensi_akademik_ids = fields.One2many(
        "erpobe.akademik.referensi", "fakultas_id", string="Referensi Akademik"
    )
    dosen_ids = fields.Many2many(
        "erpobe.master.dosen",
        compute="_compute_dosen_ids",
        string="Dosen",
    )
    mahasiswa_ids = fields.One2many(
        "erpobe.master.mahasiswa", "fakultas_id", string="Mahasiswa"
    )
    matakuliah_ids = fields.One2many(
        "erpobe.master.matakuliah", "fakultas_id", string="Mata Kuliah"
    )
    rombel_ids = fields.One2many(
        "erpobe.master.rombel", "fakultas_id", string="Rombel"
    )

    akademik_cpl_ids = fields.One2many(
        "erpobe.akademik.cpl", "fakultas_id", string="CPL"
    )
    cpl_cpmk_ids = fields.One2many(
        "erpobe.akademik.cpl.mk.cpmk", "fakultas_id", string="Pemetaan CPL-CPMK"
    )
    cpmk_ids = fields.One2many(
        "erpobe.akademik.cpmk", "fakultas_id", string="CPMK"
    )
    krs_ids = fields.One2many(
        "erpobe.akademik.krs", "fakultas_id", string="KRS"
    )
    krs_line_ids = fields.One2many(
        "erpobe.akademik.krs.line", "fakultas_id", string="Baris KRS"
    )
    penawaran_line_ids = fields.One2many(
        "erpobe.akademik.penawaran.line",
        "fakultas_id",
        string="Penawaran Mata Kuliah",
    )
    penawaran_ids = fields.One2many(
        "erpobe.akademik.penawaran", "fakultas_id", string="Penawaran"
    )
    rps_ids = fields.One2many(
        "erpobe.akademik.rps", "fakultas_id", string="RPS"
    )
    kegiatan_perkuliahan_ids = fields.One2many(
        "erpobe.akademik.kegiatan.perkuliahan",
        "fakultas_id",
        string="Kegiatan Perkuliahan",
    )
    rubrik_penilaian_ids = fields.One2many(
        "erpobe.akademik.rubrik.penilaian",
        "fakultas_id",
        string="Rubrik Penilaian",
    )
    kriteria_ids = fields.One2many(
        "erpobe.akademik.kriteria", "fakultas_id", string="Kriteria"
    )

    bobot_cpmk_cpl_ids = fields.One2many(
        "erpobe.bobot.cpmk.cpl", "fakultas_id", string="Bobot CPMK-CPL"
    )
    bobot_cpmk_mk_ids = fields.One2many(
        "erpobe.bobot.cpmk.mk", "fakultas_id", string="Bobot CPMK-MK"
    )
    bobot_komponen_cpmk_ids = fields.One2many(
        "erpobe.bobot.komponen.cpmk",
        "fakultas_id",
        string="Bobot Komponen-CPMK",
    )

    input_nilai_ids = fields.One2many(
        "erpobe.input.nilai", "fakultas_id", string="Input Nilai"
    )
    grade_komponen_ids = fields.One2many(
        "erpobe.grade.komponen", "fakultas_id", string="Nilai Komponen"
    )
    grade_cpmk_ids = fields.One2many(
        "erpobe.grade.cpmk", "fakultas_id", string="Nilai CPMK"
    )
    cpmk_rombel_ids = fields.One2many(
        "erpobe.cpmk.rombel", "fakultas_id", string="CPMK per Rombel"
    )
    cpmk_angkatan_ids = fields.One2many(
        "erpobe.cpmk.angkatan", "fakultas_id", string="CPMK per Angkatan"
    )
    grade_cpl_ids = fields.One2many(
        "erpobe.grade.cpl", "fakultas_id", string="Nilai CPL"
    )
    grade_cpl_rombel_ids = fields.One2many(
        "erpobe.grade.cpl.rombel", "fakultas_id", string="CPL per Rombel"
    )
    grade_cpl_angkatan_ids = fields.One2many(
        "erpobe.grade.cpl.angkatan", "fakultas_id", string="CPL per Angkatan"
    )
    grade_mk_ids = fields.One2many(
        "erpobe.grade.mk", "fakultas_id", string="Nilai Mata Kuliah"
    )
    grade_mk_rombel_ids = fields.One2many(
        "erpobe.grade.mk.rombel", "fakultas_id", string="Mata Kuliah per Rombel"
    )
    grade_mk_angkatan_ids = fields.One2many(
        "erpobe.grade.mk.angkatan",
        "fakultas_id",
        string="Mata Kuliah per Angkatan",
    )

    report_khs_ids = fields.One2many(
        "erpobe.report.khs", "fakultas_id", string="KHS"
    )
    report_khs_mk_ids = fields.One2many(
        "erpobe.report.khs.mk", "fakultas_id", string="KHS Mata Kuliah"
    )
    report_khs_cpmk_ids = fields.One2many(
        "erpobe.report.khs.cpmk", "fakultas_id", string="KHS CPMK"
    )
    report_khs_cpl_ids = fields.One2many(
        "erpobe.report.khs.cpl", "fakultas_id", string="KHS CPL"
    )
    summary_mk_ids = fields.One2many(
        "erpobe.summary.mk", "fakultas_id", string="Analisis Mata Kuliah"
    )
    summary_cpmk_ids = fields.One2many(
        "erpobe.summary.cpmk", "fakultas_id", string="Analisis CPMK"
    )
    summary_cpl_ids = fields.One2many(
        "erpobe.summary.cpl", "fakultas_id", string="Analisis CPL"
    )
    summary_komponen_ids = fields.One2many(
        "erpobe.summary.komponen", "fakultas_id", string="Analisis Komponen"
    )

    _kode_unique = models.Constraint("UNIQUE (kode)", "Kode fakultas harus unik.")
    _name_unique = models.Constraint("UNIQUE (name)", "Nama fakultas harus unik.")

    @api.depends("kode", "name")
    def _compute_display_name(self):
        for record in self:
            record.display_name = f"{record.kode} - {record.name}"

    @api.depends("prodi_ids.dosen_ids")
    def _compute_dosen_ids(self):
        for record in self:
            record.dosen_ids = record.prodi_ids.mapped("dosen_ids")

    @api.constrains("name", "kode")
    def _check_unique_values(self):
        for record in self:
            duplicate = self.search(
                [
                    ("id", "!=", record.id),
                    "|",
                    ("name", "=", record.name),
                    ("kode", "=", record.kode),
                ],
                limit=1,
            )
            if duplicate:
                raise ValidationError("Nama dan kode fakultas harus unik.")

    @api.ondelete(at_uninstall=False)
    def _unlink_if_used(self):
        if self.mapped("prodi_ids"):
            raise UserError(
                "Fakultas yang masih memiliki program studi tidak dapat dihapus."
            )
