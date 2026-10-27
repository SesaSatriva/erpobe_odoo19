from odoo import models


class ErpObeImportMataKuliahWizard(models.TransientModel):
    _name = "erpobe.wizard.import.matakuliah"
    _description = "Impor dan Ekspor Mata Kuliah"
    _inherit = ["erpobe.import.export.mixin"]

    _import_export_model = "erpobe.master.matakuliah"
    _import_export_identity = ("prodi_id", "kode_mk")
    _import_export_columns = (
        {
            "name": "prodi_id",
            "label": "Kode Prodi",
            "type": "many2one",
            "relation": "erpobe.master.prodi",
            "lookup_field": "kode",
            "required": True,
            "example": "PR-01",
            "description": "Kode prodi yang sudah terdaftar.",
        },
        {
            "name": "kode_mk",
            "label": "Kode Mata Kuliah",
            "type": "char",
            "required": True,
            "example": "MK-001",
            "description": "Kode unik di dalam prodi.",
        },
        {
            "name": "name",
            "label": "Nama Mata Kuliah",
            "type": "char",
            "required": True,
            "example": "Mata Kuliah Contoh",
            "description": "Nama mata kuliah.",
        },
        {
            "name": "sks",
            "label": "SKS",
            "type": "integer",
            "required": True,
            "example": 3,
            "description": "Jumlah satuan kredit semester.",
        },
        {
            "name": "semester",
            "label": "Semester Kurikulum",
            "type": "integer",
            "required": True,
            "example": 1,
            "description": "Semester pada kurikulum.",
        },
        {
            "name": "bahasa",
            "label": "Bahasa",
            "type": "selection",
            "selection": [("I", "Indonesia"), ("E", "English")],
            "required": True,
            "example": "Indonesia",
            "description": "Nilai yang diizinkan: Indonesia atau English.",
        },
        {
            "name": "tipe_mk",
            "label": "Tipe Mata Kuliah",
            "type": "selection",
            "selection": [
                ("T", "Teori"),
                ("P", "Praktikum"),
                ("L", "Lapangan"),
            ],
            "required": False,
            "example": "Teori",
            "description": "Opsional: Teori, Praktikum, atau Lapangan.",
        },
        {
            "name": "jenis_mk",
            "label": "Jenis Mata Kuliah",
            "type": "selection",
            "selection": [
                ("B", "Basic Science"),
                ("I", "Inti"),
                ("P", "Pilihan"),
                ("U", "Umum"),
            ],
            "required": False,
            "example": "Inti",
            "description": "Opsional: Basic Science, Inti, Pilihan, atau Umum.",
        },
        {
            "name": "deskripsi_mk",
            "label": "Deskripsi",
            "type": "text",
            "required": False,
            "example": "Deskripsi mata kuliah.",
            "description": "Deskripsi bebas.",
        },
        {
            "name": "koordinator_id",
            "label": "NIP Koordinator",
            "type": "many2one",
            "relation": "erpobe.master.dosen",
            "lookup_field": "nip",
            "required": False,
            "example": "",
            "description": "NIP dosen yang terdaftar pada prodi tersebut.",
        },
        {
            "name": "tim_pengampu_ids",
            "label": "NIP Tim Pengampu",
            "type": "many2many",
            "relation": "erpobe.master.dosen",
            "lookup_field": "nip",
            "required": False,
            "example": "",
            "description": "Daftar NIP dipisahkan dengan titik koma.",
        },
    )
