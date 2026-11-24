from odoo import models, fields

ASSESSMENT_TYPE_SELECTION = [
    ("attendance", "Kehadiran"),
    ("quiz", "Kuis"),
    ("assignment", "Tugas"),
    ("midterm", "UTS"),
    ("final_exam", "UAS"),
    ("presentation", "Presentasi"),
    ("practicum", "Praktikum"),
    ("case_study", "Studi Kasus"),
    ("project", "Proyek"),
    ("tbp", "TBP"),
    ("other", "Lainnya"),
]


class ErpObeAkademikKomponen(models.Model):
    _name = "erpobe.akademik.komponen"
    _inherit = ["erpobe.audit.mixin"]
    _description = "Komponen Penilaian"
    _rec_name = "name"

    name = fields.Char(
        string="Nama Komponen",
        required=True,
        help="Untuk tipe Lainnya, isi nama aktivitas penilaian yang digunakan.",
    )
    tipe = fields.Selection(
        ASSESSMENT_TYPE_SELECTION,
        string="Jenis Aktivitas Penilaian",
        required=True,
    )
    description = fields.Text(
        string="Deskripsi",
        help="Jelaskan aktivitas apabila jenis komponen adalah Lainnya.",
    )

    aktif = fields.Boolean(default=True)
    color = fields.Integer(string="Color Index")
    