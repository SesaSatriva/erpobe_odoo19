from odoo import models


class ErpObeImportProdiWizard(models.TransientModel):
    _name = "erpobe.wizard.import.prodi"
    _description = "Impor dan Ekspor Program Studi"
    _inherit = ["erpobe.import.export.mixin"]

    _import_export_model = "erpobe.master.prodi"
    _import_export_identity = ("fakultas_id", "kode")
    _import_export_columns = (
        {
            "name": "fakultas_id",
            "label": "Kode Fakultas",
            "type": "many2one",
            "relation": "erpobe.master.fakultas",
            "lookup_field": "kode",
            "required": True,
            "example": "FK-01",
            "description": "Kode fakultas harus sudah terdaftar.",
        },
        {
            "name": "kode",
            "label": "Kode Prodi",
            "type": "char",
            "required": True,
            "example": "PR-01",
            "description": "Unik di dalam fakultas.",
        },
        {
            "name": "name",
            "label": "Nama Prodi",
            "type": "char",
            "required": True,
            "example": "Program Studi Contoh",
            "description": "Nama program studi.",
        },
        {
            "name": "active",
            "label": "Aktif",
            "type": "boolean",
            "required": False,
            "example": "Ya",
            "description": "Terima Ya/Tidak, True/False, atau 1/0.",
        },
    )
