from odoo import models

from ..models.akademik_komponen import ASSESSMENT_TYPE_SELECTION


class ErpObeImportKomponenWizard(models.TransientModel):
    _name = "erpobe.wizard.import.komponen"
    _description = "Impor dan Ekspor Komponen Penilaian"
    _inherit = ["erpobe.import.export.mixin"]

    _import_export_model = "erpobe.akademik.komponen"
    _import_export_identity = ("name", "tipe")
    _import_export_columns = (
        {
            "name": "name",
            "label": "Nama Komponen",
            "type": "char",
            "required": True,
            "example": "Tugas",
            "description": "Nama komponen penilaian.",
        },
        {
            "name": "tipe",
            "label": "Jenis Aktivitas Penilaian",
            "type": "selection",
            "selection": ASSESSMENT_TYPE_SELECTION,
            "required": True,
            "example": "quiz",
            "description": "Pilih aktivitas penilaian; untuk Lainnya, jelaskan nama aktivitas pada kolom Nama Komponen.",
        },
        {
            "name": "aktif",
            "label": "Aktif",
            "type": "boolean",
            "required": False,
            "example": "Ya",
            "description": "Status aktif komponen.",
        },
        {
            "name": "color",
            "label": "Warna",
            "type": "integer",
            "required": False,
            "example": 0,
            "description": "Indeks warna opsional.",
        },
    )
