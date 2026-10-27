from odoo import models


class ErpObeImportCplWizard(models.TransientModel):
    _name = "erpobe.wizard.import.cpl"
    _description = "Impor dan Ekspor CPL"
    _inherit = ["erpobe.import.export.mixin"]

    _import_export_model = "erpobe.akademik.cpl"
    _import_export_identity = ("prodi_id", "kode_cpl")
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
            "name": "kode_cpl",
            "label": "Kode CPL",
            "type": "char",
            "required": True,
            "example": "CPL-01",
            "description": "Kode unik di dalam prodi.",
        },
        {
            "name": "name",
            "label": "Deskripsi CPL",
            "type": "text",
            "required": True,
            "example": "Deskripsi CPL contoh.",
            "description": "Deskripsi capaian pembelajaran lulusan.",
        },
    )
