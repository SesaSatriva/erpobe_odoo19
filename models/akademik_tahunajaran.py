from odoo import models, fields, api


class ErpObeTahunAjaran(models.Model):
    # NAMA MODEL SESUAI PERMINTAAN ANDA (Tanpa titik)
    _name = "erpobe.akademik.tahunajaran"
    _description = "Tahun Ajaran"
    _rec_name = "name"
    _order = "name desc"

    name = fields.Char(
        string="Nama Tahun Ajaran",
        compute="_compute_name",
        store=True,
    )

    tahun_ajaran = fields.Char(
        string="Tahun (Contoh: 2025/2026)",
        required=True,
    )

    semester = fields.Selection(
        [
            ("ganjil", "Ganjil"),
            ("genap", "Genap"),
            ("pendek", "Antara/Pendek"),
        ],
        string="Semester Akademik",
        required=True,
    )

    # Field Aktif (Wajib ada untuk Portal)
    aktif = fields.Boolean(
        string="Sedang Berjalan",
        default=False,
        help="Tahun ajaran aktif yang akan muncul di Portal Dosen.",
    )

    _unique_tahun_semester_constraint = models.Constraint('unique(tahun_ajaran, semester)', 'Kombinasi Tahun dan Semester ini sudah ada!')

    @api.depends("tahun_ajaran", "semester")
    def _compute_name(self):
        for rec in self:
            if rec.tahun_ajaran and rec.semester:
                rec.name = f"{rec.tahun_ajaran} - {rec.semester.capitalize()}"
            else:
                rec.name = False

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            if rec.aktif:
                rec._deactivate_others()
        return records

    def write(self, vals):
        res = super().write(vals)
        if vals.get("aktif"):
            for rec in self:
                rec._deactivate_others()
        return res

    def _deactivate_others(self):
        """Memastikan hanya satu tahun ajaran yang aktif"""
        domain = [("id", "!=", self.id), ("aktif", "=", True)]
        others = self.search(domain)
        if others:
            others.write({"aktif": False})
