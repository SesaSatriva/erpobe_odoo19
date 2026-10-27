from odoo import models


class ErpObeImportRombelWizard(models.TransientModel):
    _name = "erpobe.wizard.import.rombel"
    _description = "Impor dan Ekspor Rombel"
    _inherit = ["erpobe.import.export.mixin"]

    _import_export_model = "erpobe.master.rombel"
    _import_export_identity = ("prodi_id", "angkatan", "name")
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
            "name": "name",
            "label": "Nama Rombel",
            "type": "char",
            "required": True,
            "example": "A",
            "description": "Nama kelas/rombel.",
        },
        {
            "name": "angkatan",
            "label": "Angkatan",
            "type": "integer",
            "required": True,
            "example": 2025,
            "description": "Tahun angkatan, antara 2000 sampai 2100.",
        },
    )
