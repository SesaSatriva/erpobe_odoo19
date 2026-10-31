from odoo import models


class ErpObeImportFakultasWizard(models.TransientModel):
    _name = "erpobe.wizard.import.fakultas"
    _description = "Impor dan Ekspor Fakultas"
    _inherit = ["erpobe.import.export.mixin"]

    _import_export_model = "erpobe.master.fakultas"
    _import_export_identity = ("kode",)
    _import_export_columns = (
        {
            "name": "kode",
            "label": "Kode Fakultas",
            "type": "char",
            "required": True,
            "example": "FK-01",
            "description": "Kode fakultas unik.",
        },
        {
            "name": "name",
            "label": "Nama Fakultas",
            "type": "char",
            "required": True,
            "example": "Fakultas Contoh",
            "description": "Nama fakultas.",
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
