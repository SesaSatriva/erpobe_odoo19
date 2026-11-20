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
