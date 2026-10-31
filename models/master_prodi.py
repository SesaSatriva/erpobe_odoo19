from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class ErpObeMasterProdi(models.Model):
    _name = "erpobe.master.prodi"
    _description = "Master Program Studi"
    _order = "name"

    name = fields.Char(required=True, index=True)
    kode = fields.Char(required=True, index=True)
    active = fields.Boolean(default=True)
    fakultas_id = fields.Many2one(
        "erpobe.master.fakultas", required=True, ondelete="restrict", index=True
    )
    cpl_ids = fields.One2many("erpobe.akademik.cpl", "prodi_id", string="CPL")
    cpmk_ids = fields.One2many(
        "erpobe.akademik.cpmk", "prodi_id", string="CPMK"
    )
    dosen_ids = fields.Many2many(
        "erpobe.master.dosen",
        "erpobe_prodi_dosen_rel",
        "prodi_id",
        "dosen_id",
        string="Dosen",
    )
    user_ids = fields.Many2many(
        "res.users",
        "res_users_erpobe_prodi_rel",
        "prodi_id",
        "user_id",
        string="Pengguna ERP OBE",
    )
    mahasiswa_ids = fields.One2many(
        "erpobe.master.mahasiswa", "prodi_id", string="Mahasiswa"
    )
    matakuliah_ids = fields.One2many(
        "erpobe.master.matakuliah", "prodi_id", string="Mata Kuliah"
    )
    rombel_ids = fields.One2many(
        "erpobe.master.rombel", "prodi_id", string="Rombel"
    )
    rps_ids = fields.One2many("erpobe.akademik.rps", "prodi_id", string="RPS")
    penawaran_line_ids = fields.One2many(
        "erpobe.akademik.penawaran.line",
        "prodi_id",
        string="Penawaran Mata Kuliah",
    )
    metode_ids = fields.One2many(
        "erpobe.akademik.metode.pembelajaran",
        "prodi_id",
        string="Metode Pembelajaran",
    )
    referensi_ids = fields.One2many(
        "erpobe.akademik.referensi", "prodi_id", string="Referensi Akademik"
    )

    _kode_unique = models.Constraint(
        "UNIQUE (fakultas_id, kode)", "Kode prodi harus unik dalam fakultas."
    )
    _name_unique = models.Constraint(
        "UNIQUE (fakultas_id, name)", "Nama prodi harus unik dalam fakultas."
    )

    @api.depends("kode", "name")
    def _compute_display_name(self):
        for record in self:
            record.display_name = f"{record.kode} - {record.name}"

    def action_open_weight_monitor(self):
        self.ensure_one()
        monitor = self.env["erpobe.weight.monitor"].create({"prodi_id": self.id})
        monitor.action_refresh()
        return {
            "type": "ir.actions.act_window",
            "name": "Kelengkapan Bobot",
            "res_model": "erpobe.weight.monitor",
            "res_id": monitor.id,
            "view_mode": "form",
            "target": "current",
        }

    def action_open_penawaran(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Penawaran Mata Kuliah",
            "res_model": "erpobe.akademik.penawaran",
            "view_mode": "list,form",
            "domain": [("prodi_id", "=", self.id)],
            "context": {"default_prodi_id": self.id},
        }

    def action_open_tahun_ajaran(self):
        return {
            "type": "ir.actions.act_window",
            "name": "Tahun Ajaran",
            "res_model": "erpobe.akademik.tahunajaran",
            "view_mode": "list,form",
        }

    @api.model_create_multi
    def create(self, vals_list):
        seen_pairs = set()
        for vals in vals_list:
            faculty_id = vals.get("fakultas_id")
            for field_name in ("kode", "name"):
                value = vals.get(field_name)
                pair = (faculty_id, field_name, value)
                if value and (
                    pair in seen_pairs
                    or self.search_count(
                        [
                            ("fakultas_id", "=", faculty_id),
                            (field_name, "=", value),
                        ]
                    )
                ):
                    label = "Kode" if field_name == "kode" else "Nama"
                    raise ValidationError(
                        f"{label} prodi harus unik dalam fakultas."
                    )
                seen_pairs.add(pair)
        return super().create(vals_list)

    @api.constrains("fakultas_id", "kode", "name")
    def _check_unique_values(self):
        for record in self:
            duplicate = self.search(
                [
                    ("id", "!=", record.id),
                    ("fakultas_id", "=", record.fakultas_id.id),
                    "|",
                    ("name", "=", record.name),
                    ("kode", "=", record.kode),
                ],
                limit=1,
            )
            if duplicate:
                raise ValidationError("Nama dan kode prodi harus unik dalam fakultas.")

    @api.ondelete(at_uninstall=False)
    def _unlink_if_used(self):
        if (
            self.mapped("cpl_ids")
            or self.mapped("dosen_ids")
            or self.mapped("user_ids")
            or self.mapped("mahasiswa_ids")
            or self.mapped("matakuliah_ids")
            or self.mapped("rombel_ids")
        ):
            raise UserError(
                "Prodi yang masih digunakan pengguna atau memiliki data akademik "
                "tidak dapat dihapus."
            )
