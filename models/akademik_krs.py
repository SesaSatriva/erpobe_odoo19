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
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("submitted", "Menunggu Persetujuan"),
            ("approved", "Disetujui"),
            ("rejected", "Perlu Perbaikan"),
        ],
        string="Status Persetujuan",
        default="draft",
        required=True,
        tracking=True,
    )
    advisor_note = fields.Text(string="Catatan Dosen Wali", tracking=True)

    total_sks = fields.Integer(compute="_compute_total_sks", store=True)
    max_sks_allowed = fields.Integer(default=24, string="Max SKS", tracking=True)

    prodi_id = fields.Many2one(
        related="mahasiswa_id.prodi_id", store=True, readonly=True, index=True
    )

    fakultas_id = fields.Many2one(
        related="prodi_id.fakultas_id", store=True, readonly=True, index=True
    )

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

    @api.constrains("mahasiswa_id", "penawaran_id")
    def _check_krs_faculty(self):
        for record in self:
            if not record.mahasiswa_id or not record.penawaran_id:
                continue
            rombels = record.penawaran_id.rombel_ids
            if (
                record.mahasiswa_id.rombel_id not in rombels
                or any(rombel.prodi_id != record.prodi_id for rombel in rombels)
            ):
                raise ValidationError(
                    "Penawaran KRS harus mencakup rombel dan prodi mahasiswa."
                )

    _uniq_mhs_penawaran_constraint = models.Constraint('unique(mahasiswa_id, penawaran_id)', 'Mahasiswa ini sudah memiliki KRS untuk Penawaran tersebut!')

    def _check_student_owner(self):
        if self.env.user.has_group("erpobe.group_mahasiswa"):
            if any(record.mahasiswa_id.user_id != self.env.user for record in self):
                raise ValidationError("Anda hanya dapat mengakses KRS milik sendiri.")

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._check_student_owner()
        return records

    def write(self, vals):
        self._check_student_owner()
        if (
            self.env.user.has_group("erpobe.group_mahasiswa")
            and "state" in vals
            and not self.env.context.get("allow_krs_state_change")
        ):
            raise ValidationError(
                "Status KRS hanya dapat diubah melalui alur pengajuan."
            )
        if (
            self.env.user.has_group("erpobe.group_mahasiswa")
            and any(record.state not in ("draft", "rejected") for record in self)
            and any(key in vals for key in ("line_ids", "penawaran_id", "max_sks_allowed"))
        ):
            raise ValidationError(
                "KRS yang sudah diajukan tidak dapat diubah sebelum dikembalikan."
            )
        return super().write(vals)

    def action_submit(self):
        self._check_student_owner()
        for record in self:
            if record.state not in ("draft", "rejected"):
                raise ValidationError("KRS ini tidak berada dalam status yang dapat diajukan.")
            if not record.line_ids:
                raise ValidationError("Tambahkan mata kuliah sebelum mengajukan KRS.")
            if record.total_sks > record.max_sks_allowed:
                raise ValidationError("Total SKS melebihi batas yang diizinkan.")
            record.sudo().with_context(allow_krs_state_change=True).write(
                {"state": "submitted", "advisor_note": False}
            )
        return True

    def _check_advisor_access(self):
        if self.env.user.has_group("erpobe.group_admin") or self.env.user.has_group(
            "erpobe.group_superadmin"
        ) or self.env.user.has_group("base.group_system"):
            return
        if not self.env.user.has_group("erpobe.group_dosen"):
            raise ValidationError("Hanya dosen wali yang dapat memproses persetujuan KRS.")
        advisor = self.env["erpobe.master.dosen"].search(
            [("user_id", "=", self.env.user.id)], limit=1
        )
        if not advisor or any(
            record.mahasiswa_id.dosen_wali_id != advisor
            for record in self.sudo()
        ):
            raise ValidationError("KRS ini bukan milik mahasiswa bimbingan Anda.")

    def action_approve(self):
        self._check_advisor_access()
        if any(record.state != "submitted" for record in self):
            raise ValidationError("Hanya KRS yang menunggu persetujuan yang dapat disetujui.")
        self.sudo().with_context(allow_krs_state_change=True).write(
            {"state": "approved"}
        )
        return True

    def action_reject(self, note):
        self._check_advisor_access()
        if any(record.state != "submitted" for record in self):
            raise ValidationError("Hanya KRS yang menunggu persetujuan yang dapat dikembalikan.")
        if not note or not note.strip():
            raise ValidationError("Catatan penolakan wajib diisi.")
        self.sudo().with_context(allow_krs_state_change=True).write(
            {"state": "rejected", "advisor_note": note.strip()}
        )
        return True

    def action_ambil_paket(self):
        self.ensure_one()
        self._check_student_owner()
        if self.state not in ("draft", "rejected"):
            raise ValidationError("KRS yang sudah diajukan tidak dapat diubah.")
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

    prodi_id = fields.Many2one(
        related="mahasiswa_id.prodi_id", store=True, readonly=True, index=True
    )

    fakultas_id = fields.Many2one(
        related="prodi_id.fakultas_id", store=True, readonly=True, index=True
    )

    @api.constrains("krs_id", "penawaran_line_id")
    def _check_krs_line_faculty(self):
        for record in self:
            if (
                record.penawaran_line_id
                and record.penawaran_line_id.prodi_id != record.prodi_id
            ):
                raise ValidationError(
                    "Mata kuliah KRS dan mahasiswa harus berada di prodi yang sama."
                )

    @api.constrains("krs_id", "penawaran_line_id", "status_pengambilan")
    def _check_prerequisite_and_schedule(self):
        for record in self:
            student = record.mahasiswa_id
            course = record.matakuliah_id
            if not student or not course:
                continue
            if record.status_pengambilan != "ulang":
                threshold = float(
                    self.env["ir.config_parameter"].sudo().get_param(
                        "erpobe.krs.minimum_passing_score", "60"
                    )
                )
                for prerequisite in course.mk_prasyarat_ids:
                    prior_grade = self.env["erpobe.grade.mk"].search(
                        [
                            ("mahasiswa_id", "=", student.id),
                            ("mk_id", "=", prerequisite.id),
                        ],
                        limit=1,
                    )
                    if not prior_grade or prior_grade.nilai_mk < threshold:
                        raise ValidationError(
                            f"Prasyarat {prerequisite.display_name} belum lulus."
                        )

            offer_line = record.penawaran_line_id
            day = offer_line.jadwal_hari
            start = offer_line.jam_mulai
            end = offer_line.jam_selesai
            if not day or start is False or end is False:
                continue
            conflict = self.search(
                [
                    ("id", "!=", record.id),
                    ("mahasiswa_id", "=", student.id),
                    ("penawaran_line_id.jadwal_hari", "=", day),
                    (
                        "penawaran_line_id.tahun_ajaran_id",
                        "=",
                        offer_line.tahun_ajaran_id.id,
                    ),
                    ("penawaran_line_id.jam_mulai", "<", end),
                    ("penawaran_line_id.jam_selesai", ">", start),
                ],
                limit=1,
            )
            if conflict:
                raise ValidationError(
                    f"Jadwal bentrok dengan {conflict.matakuliah_id.display_name}."
                )

    @api.model_create_multi
    def create(self, vals_list):
        if self.env.user.has_group("erpobe.group_mahasiswa"):
            student = self.env["erpobe.master.mahasiswa"].search(
                [("user_id", "=", self.env.user.id)], limit=1
            )
            if not student or any(
                self.env["erpobe.akademik.krs"].browse(vals.get("krs_id")).mahasiswa_id
                != student
                for vals in vals_list
            ):
                raise ValidationError("Anda hanya dapat menambah mata kuliah pada KRS sendiri.")
        records = super().create(vals_list)
        for rec in records:
            if rec.penawaran_line_id and rec.mahasiswa_id:
                rec.penawaran_line_id.write(
                    {"mahasiswa_ids": [Command.link(rec.mahasiswa_id.id)]}
                )
        return records

    def write(self, vals):
        if self.env.user.has_group("erpobe.group_mahasiswa"):
            if any(record.mahasiswa_id.user_id != self.env.user for record in self):
                raise ValidationError("Anda hanya dapat mengubah KRS milik sendiri.")
            if any(record.krs_id.state not in ("draft", "rejected") for record in self):
                raise ValidationError("KRS yang sudah diajukan tidak dapat diubah.")
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
        if self.env.user.has_group("erpobe.group_mahasiswa"):
            if any(record.mahasiswa_id.user_id != self.env.user for record in self):
                raise ValidationError("Anda hanya dapat mengubah KRS milik sendiri.")
            if any(record.krs_id.state not in ("draft", "rejected") for record in self):
                raise ValidationError("KRS yang sudah diajukan tidak dapat diubah.")
        for rec in self:
            if rec.penawaran_line_id and rec.mahasiswa_id:
                rec.penawaran_line_id.write(
                    {"mahasiswa_ids": [Command.unlink(rec.mahasiswa_id.id)]}
                )
        return super().unlink()
