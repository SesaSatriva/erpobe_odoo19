from odoo import models


class ErpObeImportDosenWizard(models.TransientModel):
    _name = "erpobe.wizard.import.dosen"
    _description = "Impor dan Ekspor Dosen"
    _inherit = ["erpobe.import.export.mixin"]

    _import_export_model = "erpobe.master.dosen"
    _import_export_identity = ("nip",)
    _import_export_columns = (
        {
            "name": "nip",
            "label": "NIP",
            "type": "char",
            "required": True,
            "example": "00012345",
            "description": "Nomor identitas; kolom diperlakukan sebagai teks.",
        },
        {
            "name": "name",
            "label": "Nama Dosen",
            "type": "char",
            "required": True,
            "example": "Nama Dosen Contoh",
            "description": "Nama kontak dosen.",
        },
        {
            "name": "email",
            "label": "Email",
            "type": "char",
            "required": True,
            "example": "dosen@example.test",
            "description": "Dipakai sebagai login pengguna.",
        },
        {
            "name": "prodi_ids",
            "label": "Kode Prodi",
            "type": "many2many",
            "relation": "erpobe.master.prodi",
            "lookup_field": "kode",
            "required": True,
            "example": "PR-01",
            "description": "Satu atau lebih kode prodi, dipisahkan dengan titik koma.",
        },
    )

    def _create_record(self, values, dry_run=False):
        values = values.copy()
        partner_values = {
            "name": values.pop("name"),
            "email": values.pop("email"),
        }
        context = {"no_reset_password": True} if dry_run else {}
        partner = self.env["res.partner"].with_context(**context).create(
            partner_values
        )
        values["partner_id"] = partner.id
        return self._get_target_model().with_context(**context).create(values)
