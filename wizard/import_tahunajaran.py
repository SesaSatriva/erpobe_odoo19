from odoo import models


class ErpObeImportTahunAjaranWizard(models.TransientModel):
    _name = "erpobe.wizard.import.tahunajaran"
    _description = "Impor dan Ekspor Tahun Ajaran"
    _inherit = ["erpobe.import.export.mixin"]

    _import_export_model = "erpobe.akademik.tahunajaran"
    _import_export_identity = ("tahun_ajaran", "semester")
    _import_export_columns = (
        {
            "name": "tahun_ajaran",
            "label": "Tahun Ajaran",
            "type": "char",
            "required": True,
            "example": "2025/2026",
            "description": "Contoh format tahun ajaran: 2025/2026.",
        },
        {
            "name": "semester",
            "label": "Semester",
            "type": "selection",
            "selection": [
                ("ganjil", "Ganjil"),
                ("genap", "Genap"),
                ("pendek", "Antara/Pendek"),
            ],
            "required": True,
            "example": "Ganjil",
            "description": "Nilai: Ganjil, Genap, atau Antara/Pendek.",
        },
        {
            "name": "aktif",
            "label": "Sedang Berjalan",
            "type": "boolean",
            "required": False,
            "example": "Tidak",
            "description": "Maksimal satu tahun ajaran dapat aktif.",
        },
    )
