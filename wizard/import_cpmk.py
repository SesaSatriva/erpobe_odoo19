from odoo import models


class ErpObeImportCpmkWizard(models.TransientModel):
    _name = "erpobe.wizard.import.cpmk"
    _description = "Impor dan Ekspor CPMK"
    _inherit = ["erpobe.import.export.mixin"]

    _import_export_model = "erpobe.akademik.cpmk"
    _import_export_identity = ("mk_id", "kode_cpmk")
    _import_export_columns = (
        {
            "name": "mk_id",
            "label": "Kode Mata Kuliah",
            "type": "many2one",
            "relation": "erpobe.master.matakuliah",
            "lookup_field": "kode_mk",
            "required": True,
            "example": "MK-001",
            "description": "Kode mata kuliah yang sudah terdaftar.",
        },
        {
            "name": "kode_cpmk",
            "label": "Kode CPMK",
            "type": "char",
            "required": True,
            "example": "CPMK-01",
            "description": "Kode CPMK unik dalam mata kuliah.",
        },
        {
            "name": "name",
            "label": "Deskripsi CPMK",
            "type": "text",
            "required": True,
            "example": "Deskripsi CPMK contoh.",
            "description": "Deskripsi capaian pembelajaran mata kuliah.",
        },
    )
