from odoo import models


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
            "label": "Tipe Komponen",
            "type": "selection",
            "selection": [
                ("kognitif", "Kognitif"),
                ("partisipatif", "Partisipatif"),
            ],
            "required": True,
            "example": "Kognitif",
            "description": "Pilih Kognitif atau Partisipatif.",
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
