from odoo import models


class ErpObeImportMahasiswaWizard(models.TransientModel):
    _name = "erpobe.wizard.import.mahasiswa"
    _description = "Impor dan Ekspor Mahasiswa"
    _inherit = ["erpobe.import.export.mixin"]

    _import_export_model = "erpobe.master.mahasiswa"
    _import_export_identity = ("nim",)
    _import_export_columns = (
        {
            "name": "nim",
            "label": "NIM",
            "type": "char",
            "required": True,
            "example": "000123456",
            "description": "Nomor identitas; kolom diperlakukan sebagai teks.",
        },
        {
            "name": "name",
            "label": "Nama Mahasiswa",
            "type": "char",
            "required": True,
            "example": "Nama Mahasiswa Contoh",
            "description": "Nama kontak mahasiswa.",
        },
        {
            "name": "email",
            "label": "Email",
            "type": "char",
            "required": True,
            "example": "mahasiswa@example.test",
            "description": "Dipakai sebagai login pengguna.",
        },
        {
            "name": "_import_prodi_id",
            "field": "_import_prodi_id",
            "label": "Kode Prodi",
            "type": "many2one",
            "relation": "erpobe.master.prodi",
            "lookup_field": "kode",
            "export_field": "rombel_id.prodi_id",
            "required": True,
            "example": "PR-01",
            "description": "Kode prodi tempat rombel terdaftar.",
        },
        {
            "name": "_import_angkatan",
            "field": "_import_angkatan",
            "label": "Angkatan",
            "type": "integer",
            "export_field": "rombel_id.angkatan",
            "required": True,
            "example": 2025,
            "description": "Tahun angkatan rombel, antara 2000 sampai 2100.",
        },
        {
            "name": "_import_rombel_name",
            "field": "_import_rombel_name",
            "label": "Nama Rombel",
            "type": "char",
            "export_field": "rombel_id.name",
            "required": True,
            "example": "A",
            "description": "Nama rombel pada prodi dan angkatan tersebut.",
        },
    )

    def _prepare_import_values(self, row_values):
        values = super()._prepare_import_values(row_values)
        prodi_id = values.pop("_import_prodi_id")
        angkatan = values.pop("_import_angkatan")
        rombel_name = values.pop("_import_rombel_name")
        rombels = self.env["erpobe.master.rombel"].search(
            [
                ("prodi_id", "=", prodi_id),
                ("angkatan", "=", angkatan),
                ("name", "=", rombel_name),
            ],
            limit=2,
        )
        if not rombels:
            raise ValueError(
                f"Rombel {rombel_name} angkatan {angkatan} tidak ditemukan "
                "pada prodi tersebut."
            )
        if len(rombels) > 1:
            raise ValueError(
                f"Rombel {rombel_name} angkatan {angkatan} tidak unik."
            )
        values["rombel_id"] = rombels.id
        return values

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
