from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ErpObeAcademicCurriculum(models.Model):
    _name = "erpobe.akademik.kurikulum"
    _description = "Kurikulum Program Studi"
    _order = "angkatan_mulai desc, name"

    name = fields.Char(required=True)
    kode = fields.Char(required=True, index=True)
    prodi_id = fields.Many2one(
        "erpobe.master.prodi", required=True, ondelete="restrict", index=True
    )
    fakultas_id = fields.Many2one(
        related="prodi_id.fakultas_id", store=True, readonly=True, index=True
    )
    angkatan_mulai = fields.Integer(required=True, default=2022)
    source_type = fields.Selection(
        [
            ("official", "Rujukan Resmi"),
            ("mixed", "Rujukan dan Simulasi"),
            ("dummy", "Simulasi"),
        ],
        required=True,
        default="dummy",
    )
    source_note = fields.Text()
    source_url = fields.Char()
    active = fields.Boolean(default=True)
    matakuliah_ids = fields.One2many(
        "erpobe.master.matakuliah", "kurikulum_id", string="Mata Kuliah"
    )
    mahasiswa_ids = fields.One2many(
        "erpobe.master.mahasiswa", "kurikulum_id", string="Mahasiswa"
    )

    _unique_curriculum_code = models.Constraint(
        "UNIQUE(prodi_id, kode)", "Kode kurikulum harus unik dalam prodi."
    )


class ErpObeAcademicSubCpmk(models.Model):
    _name = "erpobe.akademik.subcpmk"
    _description = "Sub-CPMK"
    _order = "rps_id, minggu, id"

    rps_id = fields.Many2one(
        "erpobe.akademik.rps", required=True, ondelete="cascade", index=True
    )
    cpmk_id = fields.Many2one(
        "erpobe.akademik.cpmk", required=True, ondelete="cascade", index=True
    )
    kode = fields.Char(required=True, index=True)
    name = fields.Text(string="Rumusan Sub-CPMK", required=True)
    indikator = fields.Text(required=True)
    minggu = fields.Integer(required=True)
    target_nilai = fields.Float(default=70.0, required=True)
    prodi_id = fields.Many2one(
        related="rps_id.prodi_id", store=True, readonly=True, index=True
    )
    fakultas_id = fields.Many2one(
        related="prodi_id.fakultas_id", store=True, readonly=True, index=True
    )

    _unique_subcpmk_code = models.Constraint(
        "UNIQUE(rps_id, kode)", "Kode Sub-CPMK harus unik dalam RPS."
    )
    _unique_subcpmk_week = models.Constraint(
        "UNIQUE(rps_id, minggu)", "Setiap minggu RPS hanya dapat memiliki satu Sub-CPMK."
    )
    _subcpmk_week_range = models.Constraint(
        "CHECK(minggu BETWEEN 1 AND 16)",
        "Minggu Sub-CPMK harus berada pada rentang 1–16.",
    )

    @api.constrains("rps_id", "cpmk_id")
    def _check_subcpmk_course(self):
        for record in self:
            if record.cpmk_id.mk_id != record.rps_id.matakuliah_id:
                raise ValidationError(
                    "Sub-CPMK dan RPS harus menggunakan CPMK dari mata kuliah yang sama."
                )


class ErpObeGradeSubCpmk(models.Model):
    _name = "erpobe.grade.subcpmk"
    _description = "Hasil Pengukuran Sub-CPMK"
    _order = "mahasiswa_id, subcpmk_id"

    krs_line_id = fields.Many2one(
        "erpobe.akademik.krs.line",
        required=True,
        ondelete="cascade",
        index=True,
    )
    subcpmk_id = fields.Many2one(
        "erpobe.akademik.subcpmk",
        required=True,
        ondelete="cascade",
        index=True,
    )
    source_grade_komponen_ids = fields.Many2many(
        "erpobe.grade.komponen",
        relation="erpobe_grade_subcpmk_component_rel",
        column1="result_id",
        column2="grade_component_id",
        string="Sumber Penilaian",
    )
    mahasiswa_id = fields.Many2one(
        related="krs_line_id.mahasiswa_id", store=True, readonly=True, index=True
    )
    matakuliah_id = fields.Many2one(
        related="subcpmk_id.rps_id.matakuliah_id",
        store=True,
        readonly=True,
        index=True,
    )
    nilai = fields.Float(
        compute="_compute_nilai",
        store=True,
        digits=(16, 2),
        string="Nilai Sub-CPMK",
    )
    target_nilai = fields.Float(
        related="subcpmk_id.target_nilai", store=True, readonly=True
    )
    status_capaian = fields.Selection(
        [("tercapai", "Tercapai"), ("belum", "Belum Tercapai")],
        compute="_compute_status_capaian",
        store=True,
        string="Status Capaian",
    )
    prodi_id = fields.Many2one(
        related="mahasiswa_id.prodi_id", store=True, readonly=True, index=True
    )
    fakultas_id = fields.Many2one(
        related="prodi_id.fakultas_id", store=True, readonly=True, index=True
    )

    _unique_subcpmk_result = models.Constraint(
        "UNIQUE(krs_line_id, subcpmk_id)",
        "Hasil Sub-CPMK untuk KRS ini sudah tersedia.",
    )

    @api.depends("source_grade_komponen_ids.nilai")
    def _compute_nilai(self):
        for record in self:
            scores = record.source_grade_komponen_ids.mapped("nilai")
            record.nilai = sum(scores) / len(scores) if scores else 0.0

    @api.depends("nilai", "target_nilai")
    def _compute_status_capaian(self):
        for record in self:
            record.status_capaian = (
                "tercapai" if record.nilai >= record.target_nilai else "belum"
            )

    @api.constrains("krs_line_id", "subcpmk_id")
    def _check_subcpmk_student_course(self):
        for record in self:
            if (
                record.krs_line_id.matakuliah_id
                != record.subcpmk_id.rps_id.matakuliah_id
            ):
                raise ValidationError(
                    "Hasil Sub-CPMK harus berasal dari mata kuliah pada KRS."
                )

    @api.constrains("source_grade_komponen_ids", "krs_line_id")
    def _check_assessment_sources(self):
        for record in self:
            if any(
                grade.krs_line_id != record.krs_line_id
                for grade in record.source_grade_komponen_ids
            ):
                raise ValidationError(
                    "Sumber penilaian Sub-CPMK harus berasal dari KRS yang sama."
                )


class ErpObeAcademicFixtureSource(models.Model):
    _name = "erpobe.akademik.fixture.source"
    _description = "Sumber Data Fixture Akademik"
    _order = "record_model, name"

    name = fields.Char(required=True)
    fixture_key = fields.Char(required=True, index=True)
    record_model = fields.Char(required=True, index=True)
    record_id = fields.Integer(required=True, index=True)
    source_type = fields.Selection(
        [
            ("official", "Rujukan Resmi"),
            ("mixed", "Rujukan dan Simulasi"),
            ("dummy", "Simulasi"),
            ("derived", "Hasil Perhitungan"),
        ],
        required=True,
    )
    source_note = fields.Text(required=True)
    source_url = fields.Char()

    _unique_fixture_source = models.Constraint(
        "UNIQUE(fixture_key)", "Penanda sumber fixture harus unik."
    )
    _unique_record_source = models.Constraint(
        "UNIQUE(record_model, record_id)",
        "Setiap record fixture hanya dapat memiliki satu penanda sumber.",
    )
