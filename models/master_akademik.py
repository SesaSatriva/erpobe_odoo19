import datetime

from odoo import models, fields, api
from odoo.exceptions import ValidationError

from .faculty_access import _check_prodi_write_access


class ErpObeMasterMataKuliah(models.Model):
    _name = "erpobe.master.matakuliah"
    _description = "Master Mata Kuliah"
    _rec_name = "name"

    name = fields.Char(string="Nama Mata Kuliah", required=True)
    kode_mk = fields.Char(string="Kode MK", required=True, index=True)
    sks = fields.Integer(required=True)
    semester = fields.Integer(required=True)

    tipe_mk = fields.Selection([("T", "Teori"), ("P", "Praktikum"), ("L", "Lapangan")])
    jenis_mk = fields.Selection(
        [("B", "Basic Science"), ("I", "Inti"), ("P", "Pilihan"), ("U", "Umum")]
    )
    bahasa = fields.Selection(
        [("I", "Indonesia"), ("E", "English")], required=True, default="I"
    )
    deskripsi_mk = fields.Text()

    # Relasi
    koordinator_id = fields.Many2one(
        "erpobe.master.dosen", ondelete="restrict", string="Koordinator"
    )
    tim_pengampu_ids = fields.Many2many("erpobe.master.dosen", string="Tim Pengampu")
    mk_prasyarat_ids = fields.Many2many(
        "erpobe.master.matakuliah", "mk_prasyarat_rel", "mk_id", "prasyarat_id"
    )

    # CPMK langsung link ke MK (Parent-Child)
    cpmk_ids = fields.One2many("erpobe.akademik.cpmk", "mk_id", string="Daftar CPMK")

    _kode_mk_unique = models.Constraint(
        "UNIQUE (prodi_id, kode_mk)", "Kode Mata Kuliah harus unik dalam prodi."
    )
    rombel_ids = fields.Many2many(
        "erpobe.master.rombel",
        "erpobe_rombel_matakuliah_rel",
        "matakuliah_id",
        "rombel_id",
        string="Rombel",
    )

    prodi_id = fields.Many2one(
        "erpobe.master.prodi",
        required=True,
        ondelete="restrict",
        index=True,
    )
    fakultas_id = fields.Many2one(
        related="prodi_id.fakultas_id", store=True, readonly=True, index=True
    )

    @api.constrains(
        "prodi_id",
        "koordinator_id",
        "tim_pengampu_ids",
        "rombel_ids",
        "mk_prasyarat_ids",
    )
    def _check_related_faculties(self):
        for record in self:
            if (
                record.koordinator_id
                and record.prodi_id not in record.koordinator_id.prodi_ids
            ):
                raise ValidationError(
                    "Koordinator harus terdaftar pada prodi mata kuliah."
                )
            if any(
                record.prodi_id not in dosen.prodi_ids
                for dosen in record.tim_pengampu_ids
            ):
                raise ValidationError(
                    "Tim pengampu harus terdaftar pada prodi mata kuliah."
                )
            if any(
                rombel.prodi_id != record.prodi_id
                for rombel in record.rombel_ids
            ):
                raise ValidationError(
                    "Rombel dan mata kuliah harus berada di prodi yang sama."
                )
            if any(
                mk.prodi_id != record.prodi_id for mk in record.mk_prasyarat_ids
            ):
                raise ValidationError(
                    "Mata kuliah prasyarat harus berasal dari prodi yang sama."
                )

    def write(self, vals):

        _check_prodi_write_access(self, vals)

        return super().write(vals)

    @api.model_create_multi
    def create(self, vals_list):
        seen_codes = set()
        for vals in vals_list:
            code = vals.get("kode_mk")
            pair = (code, vals.get("prodi_id"))
            if code and (
                pair in seen_codes
                or self.search_count(
                    [("kode_mk", "=", code), ("prodi_id", "=", pair[1])]
                )
            ):
                raise ValidationError("Kode Mata Kuliah harus unik dalam prodi.")
            seen_codes.add(pair)
        return super().create(vals_list)


class ErpObeMasterRombel(models.Model):
    _name = "erpobe.master.rombel"
    _description = "Rombongan Belajar"
    _order = "angkatan desc, name asc"

    name = fields.Char(string="Nama Kelas", required=True)

    # PERBAIKAN DI SINI:
    angkatan = fields.Integer(
        string="Angkatan",
        required=True,
        default=lambda self: datetime.date.today().year,
        aggregator=None,
        help="Contoh: 2023, 2024",
    )

    mahasiswa_ids = fields.One2many(
        "erpobe.master.mahasiswa", "rombel_id", string="Mahasiswa"
    )

    matakuliah_ids = fields.Many2many(
        "erpobe.master.matakuliah",
        "erpobe_rombel_matakuliah_rel",
        "rombel_id",
        "matakuliah_id",
        string="Paket Mata Kuliah",
    )

    _name_angkatan_unique = models.Constraint(
        "UNIQUE (name, angkatan, prodi_id)",
        "Kelas ini sudah ada di angkatan tersebut pada prodi ini!",
    )

    prodi_id = fields.Many2one(
        "erpobe.master.prodi",
        required=True,
        ondelete="restrict",
        index=True,
    )
    fakultas_id = fields.Many2one(
        related="prodi_id.fakultas_id", store=True, readonly=True, index=True
    )

    @api.constrains("angkatan")
    def _check_angkatan(self):
        for rec in self:
            if rec.angkatan < 2000 or rec.angkatan > 2100:
                raise ValidationError(
                    "Tahun angkatan tidak valid (harus antara 2000-2100)."
                )

    @api.constrains("prodi_id", "matakuliah_ids")
    def _check_matakuliah_faculty(self):
        for record in self:
            if any(mk.prodi_id != record.prodi_id for mk in record.matakuliah_ids):
                raise ValidationError(
                    "Rombel dan mata kuliah harus berada di prodi yang sama."
                )

    @api.model_create_multi
    def create(self, vals_list):
        seen_pairs = set()
        for vals in vals_list:
            pair = (vals.get("name"), vals.get("angkatan"), vals.get("prodi_id"))
            if pair[0] and pair[1] and (
                pair in seen_pairs
                or self.search_count(
                    [
                        ("name", "=", pair[0]),
                        ("angkatan", "=", pair[1]),
                        ("prodi_id", "=", pair[2]),
                    ]
                )
            ):
                raise ValidationError(
                    "Kelas ini sudah ada di angkatan tersebut!"
                )
            seen_pairs.add(pair)
        return super().create(vals_list)

    def action_generate_mahasiswa_user(self):
        mahasiswa_no_user = self.mapped("mahasiswa_ids").filtered(
            lambda mahasiswa: not mahasiswa.user_id
        )
        mahasiswa_no_user._create_or_update_user()

    def write(self, vals):
        # Validasi cakupan ekstensi berjalan sebelum logika utama.
        _check_prodi_write_access(self, vals)

        result = super().write(vals)
        if "prodi_id" in vals:
            self.mapped("mahasiswa_ids.user_id")._sync_user_type()
        return result

    @api.depends("name", "angkatan")
    def _compute_display_name(self):
        for record in self:
            record.display_name = f"{record.angkatan} - {record.name}"