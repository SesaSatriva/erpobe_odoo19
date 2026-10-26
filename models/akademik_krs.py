from odoo import models, fields, api, Command
from odoo.exceptions import ValidationError


class ErpObeAkademikKrs(models.Model):
    _name = "erpobe.akademik.krs"
    _description = "Kartu Rencana Studi"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _rec_name = "mahasiswa_id"
    _order = "tahun_ajaran desc, id desc"

    mahasiswa_id = fields.Many2one(
        "erpobe.master.mahasiswa",
        required=True,
        tracking=True,
    )
    rombel_id = fields.Many2one(
        related="mahasiswa_id.rombel_id", store=True, readonly=True
    )

    # Filter: Penawaran harus memiliki Rombel Mahasiswa di dalam tags 'rombel_ids'
    penawaran_id = fields.Many2one(
        "erpobe.akademik.penawaran",
        string="Penawaran / Periode",
        required=True,
        tracking=True,
        domain="[('rombel_ids', 'in', rombel_id), ('tahun_ajaran.aktif', '=', True)]",
    )

    tahun_ajaran = fields.Many2one(related="penawaran_id.tahun_ajaran", store=True)
    semester_akademik = fields.Selection(
        related="penawaran_id.semester_akademik", store=True
    )

    line_ids = fields.One2many(
        "erpobe.akademik.krs.line", "krs_id", string="Mata Kuliah Diambil"
    )

    total_sks = fields.Integer(compute="_compute_total_sks", store=True)
    max_sks_allowed = fields.Integer(default=24, string="Max SKS", tracking=True)

    @api.depends("line_ids.sks")
    def _compute_total_sks(self):
        for rec in self:
            rec.total_sks = sum(rec.line_ids.mapped("sks"))

    @api.constrains("total_sks", "max_sks_allowed")
    def _check_max_sks(self):
        for rec in self:
            if rec.total_sks > rec.max_sks_allowed:
                raise ValidationError(
                    f"Total SKS ({rec.total_sks}) melebihi batas ({rec.max_sks_allowed})."
                )

    _uniq_mhs_penawaran_constraint = models.Constraint('unique(mahasiswa_id, penawaran_id)', 'Mahasiswa ini sudah memiliki KRS untuk Penawaran tersebut!')

    def action_ambil_paket(self):
        self.ensure_one()
        if not self.penawaran_id or not self.rombel_id:
            raise ValidationError("Pastikan Penawaran dan Mahasiswa sudah terisi.")

        # Cari line penawaran dimana rombel_id mahasiswa ada di dalam tags rombel_ids
        kelas_tersedia = self.env["erpobe.akademik.penawaran.line"].search(
            [
                ("penawaran_id", "=", self.penawaran_id.id),
                ("rombel_ids", "in", [self.rombel_id.id]),  # Fix: search inside M2M
            ]
        )

        if not kelas_tersedia:
            raise ValidationError(
                f"Tidak ada kelas paket untuk Rombel {self.rombel_id.name}. Silakan input manual."
            )

        mk_sudah_diambil = self.line_ids.mapped("matakuliah_id.id")
        new_lines = []

        for kelas in kelas_tersedia:
            if kelas.matakuliah_id.id in mk_sudah_diambil:
                continue

            new_lines.append(
                Command.create(
                    {"penawaran_line_id": kelas.id, "status_pengambilan": "baru"}
                )
            )

        if new_lines:
            self.line_ids = new_lines  # Assignment langsung list of commands

        return True
class ErpObeAkademikKrsLine(models.Model):
    _name = "erpobe.akademik.krs.line"
    _description = "Detail Mata Kuliah KRS"
    _rec_name = "matakuliah_id"

    krs_id = fields.Many2one("erpobe.akademik.krs", required=True, ondelete="cascade")

    # Otomatis filter kelas yang sesuai rombel mahasiswa saja
    penawaran_line_id = fields.Many2one(
        "erpobe.akademik.penawaran.line",
        string="Mata Kuliah / Kelas",
        required=True,
        domain="[('penawaran_id', '=', parent.penawaran_id), ('rombel_ids', 'in', parent.rombel_id)]",
    )

    mahasiswa_id = fields.Many2one(related="krs_id.mahasiswa_id", store=True)
    matakuliah_id = fields.Many2one(
        related="penawaran_line_id.matakuliah_id", store=True
    )
    sks = fields.Integer(related="matakuliah_id.sks", store=True)
    rombel_kelas = fields.Many2many(
        related="penawaran_line_id.rombel_ids",
        string="Kelas Rombel",
        readonly=True,
    )

    status_pengambilan = fields.Selection(
        [("baru", "Baru"), ("ulang", "Mengulang")], default="baru", required=True
    )

    _unique_krs_mk_constraint = models.Constraint('unique(krs_id, matakuliah_id)', 'Mata kuliah ini sudah diambil! Tidak boleh mengambil MK yang sama.')

    # SYNC MAHASISWA KE KELAS (Insert/Delete/Update)
    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            if rec.penawaran_line_id and rec.mahasiswa_id:
                rec.penawaran_line_id.write(
                    {"mahasiswa_ids": [Command.link(rec.mahasiswa_id.id)]}
                )
        return records

    def write(self, vals):
        # Snapshot kelas lama sebelum update
        old_kelas_map = {}
        if "penawaran_line_id" in vals:
            for rec in self:
                old_kelas_map[rec.id] = rec.penawaran_line_id

        res = super().write(vals)

        # Jika user pindah kelas
        if "penawaran_line_id" in vals:
            for rec in self:
                old_kelas = old_kelas_map.get(rec.id)
                new_kelas = rec.penawaran_line_id
                mhs_id = rec.mahasiswa_id.id

                if old_kelas and old_kelas != new_kelas:
                    # Hapus dari kelas lama
                    old_kelas.write({"mahasiswa_ids": [Command.unlink(mhs_id)]})

                if new_kelas:
                    # Masukkan ke kelas baru
                    new_kelas.write({"mahasiswa_ids": [Command.link(mhs_id)]})

        return res

    def unlink(self):
        for rec in self:
            if rec.penawaran_line_id and rec.mahasiswa_id:
                rec.penawaran_line_id.write(
                    {"mahasiswa_ids": [Command.unlink(rec.mahasiswa_id.id)]}
                )
        return super().unlink()
