from odoo import models, fields, api, Command
from odoo.exceptions import UserError, ValidationError

class ErpObeAkademikRps(models.Model):
    _name = "erpobe.akademik.rps"
    _description = "Rencana Pembelajaran Semester (RPS)"
    _rec_name = "matakuliah_id"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    # === 1. Header & Identitas MK ===
    matakuliah_id = fields.Many2one(
        "erpobe.master.matakuliah", string="Mata Kuliah", required=True, tracking=True
    )
    penawaran_line_id = fields.Many2one(
        "erpobe.akademik.penawaran.line",
        string="Penawaran Mata Kuliah",
        ondelete="restrict",
        index=True,
        tracking=True,
    )
    tahun_ajaran_id = fields.Many2one(
        related="penawaran_line_id.tahun_ajaran_id",
        string="Tahun Ajaran",
        store=True,
        readonly=True,
        index=True,
    )
    semester_akademik = fields.Selection(
        related="tahun_ajaran_id.semester",
        string="Semester Akademik",
        store=True,
        readonly=True,
    )
    version = fields.Integer(string="Versi", default=1, required=True, readonly=True)
    source_rps_id = fields.Many2one(
        "erpobe.akademik.rps",
        string="Disalin dari RPS",
        readonly=True,
        ondelete="set null",
        index=True,
    )
    status = fields.Selection(
        [
            ("draft", "Draft"),
            ("review", "Perlu Ditinjau"),
            ("final", "Final"),
        ],
        string="Status RPS",
        default="draft",
        required=True,
        tracking=True,
    )
    weight_status = fields.Selection(
        [
            ("complete", "Bobot Lengkap"),
            ("incomplete", "Bobot Belum Lengkap"),
        ],
        string="Kelengkapan Bobot",
        compute="_compute_weight_status",
    )
    weight_issue_count = fields.Integer(
        string="Jumlah Bobot Bermasalah", compute="_compute_weight_status"
    )
    _unique_offer_version = models.Constraint(
        "UNIQUE(penawaran_line_id, version)",
        "Nomor versi RPS harus unik dalam satu penawaran.",
    )

    # Field Related Wajib Store=True untuk Report/Search
    kode_mk = fields.Char(related="matakuliah_id.kode_mk", store=True)
    matakuliah_name = fields.Char(
        related="matakuliah_id.name", store=True, index=True
    )
    sks = fields.Integer(related="matakuliah_id.sks", store=True)
    semester = fields.Integer(related="matakuliah_id.semester", store=True)
    deskripsi_mk = fields.Text(
        related="matakuliah_id.deskripsi_mk",
        string="Deskripsi Mata Kuliah",
        readonly=False,
    )

    # Related Info (Sesuai kode asli Anda)
    mk_prasyarat_ids = fields.Many2many(
        related="matakuliah_id.mk_prasyarat_ids", readonly=True
    )
    tipe_mk = fields.Selection(related="matakuliah_id.tipe_mk", store=True)
    jenis_mk = fields.Selection(related="matakuliah_id.jenis_mk", store=True)
    bahasa = fields.Selection(related="matakuliah_id.bahasa", store=True)
    koordinator_id = fields.Many2one(related="matakuliah_id.koordinator_id", store=True)
    tim_pengampu_ids = fields.Many2many(
        related="matakuliah_id.tim_pengampu_ids", readonly=True
    )
    media_software = fields.Char(string="Media software")
    media_hardware = fields.Char(string="Media Hardware")
    tujuan_pembelajaran = fields.Text(string="Tujuan Pembelajaran")
    materi_pembelajaran = fields.Text(string="Materi Pembelajaran")
    sumber_belajar = fields.Text(string="Sumber Belajar")
    referensi_ids = fields.Many2many(
        "erpobe.akademik.referensi",
        "erpobe_rps_referensi_rel",
        "rps_id",
        "referensi_id",
        string="Referensi Utama dan Pendukung",
    )
    mk_cpl_mapping_ids = fields.One2many(
        related="matakuliah_id.cpl_mapping_ids",
        string="Kontribusi Mata Kuliah terhadap CPL",
        readonly=True,
    )

    # === 2. Komponen & CPMK ===
    # Komponen Penilaian yang dipakai di RPS ini
    komponen_ids = fields.Many2many(
        "erpobe.akademik.komponen",
        string="Komponen Penilaian",
        help="Pilih komponen penilaian yang digunakan dalam semester ini.",
    )
    rps_komponen_ids = fields.One2many(
        "erpobe.akademik.rps.komponen",
        "rps_id",
        string="Snapshot Komponen",
        copy=True,
    )

    cpmk_ids = fields.Many2many(
        "erpobe.akademik.cpmk",
        string="CPMK yang Diajarkan",
        compute="_compute_cpmk_ids",
        store=True,
        readonly=False,
        precompute=True, 
    )

    prodi_id = fields.Many2one(
        related="matakuliah_id.prodi_id", store=True, readonly=True, index=True
    )

    fakultas_id = fields.Many2one(
        related="prodi_id.fakultas_id", store=True, readonly=True, index=True
    )

    @api.depends(
        "matakuliah_id",
        "tahun_ajaran_id",
        "version",
        "status",
        "create_date",
    )
    def _compute_display_name(self):
        for record in self:
            course = record.matakuliah_id.display_name or ""
            year = record.tahun_ajaran_id.display_name
            suffix = f" - {year}" if year else ""
            created = (
                f", {record.create_date.date()}" if record.create_date else ""
            )
            record.display_name = (
                f"{record.kode_mk or ''} - {course}{suffix} "
                f"(v{record.version}, {record.status or 'draft'}{created})"
            )

    @api.constrains("matakuliah_id", "penawaran_line_id")
    def _check_offer_course(self):
        for rps in self:
            if (
                rps.penawaran_line_id
                and rps.penawaran_line_id.matakuliah_id != rps.matakuliah_id
            ):
                raise ValidationError(
                    "Mata kuliah RPS harus sama dengan mata kuliah pada penawaran."
                )

    @api.depends("matakuliah_id")
    def _compute_cpmk_ids(self):
        for rec in self:
            if rec.matakuliah_id:
                # Mengambil semua CPMK master milik MK ini
                cpmks = self.env["erpobe.akademik.cpmk"].search(
                    [("mk_id", "=", rec.matakuliah_id.id)]
                )
                rec.cpmk_ids = [Command.set(cpmks.ids)]
            else:
                rec.cpmk_ids = [Command.clear()]

    cpl_ids = fields.Many2many(
        "erpobe.akademik.cpl",
        string="CPL Terkait",
        compute="_compute_cpl_ids",
        store=True,
        readonly=False
    )

    @api.depends("cpmk_ids", "cpmk_ids.cpl_mapping_ids")
    def _compute_cpl_ids(self):
        for rec in self:
            rec.cpl_ids = rec.cpmk_ids.mapped("cpl_mapping_ids.cpl_id")

    @api.depends(
        "cpmk_ids",
        "cpl_ids",
        "bobot_cpmk_mk_ids.cpmk_id",
        "bobot_cpmk_mk_ids.bobot_cpmk_mk",
        "bobot_komponen_cpmk_ids.cpmk_id",
        "bobot_komponen_cpmk_ids.bobot_komponen_cpmk",
        "rps_komponen_ids.aktif",
        "rps_komponen_ids.bobot",
        "rps_komponen_ids.allocation_ids.bobot_komponen_cpmk",
        "komponen_ids",
    )
    def _compute_weight_status(self):
        validator = self.env["erpobe.weight.validation"]
        for rps in self:
            groups = validator.get_rps_summary(rps)
            issues = [group for group in groups if group["status"] != "complete"]
            rps.weight_issue_count = len(issues)
            rps.weight_status = "incomplete" if issues else "complete"

    bobot_cpmk_mk_ids = fields.One2many(
        "erpobe.bobot.cpmk.mk", "rps_id", string="Bobot CPMK -> MK"
    )
    bobot_komponen_cpmk_ids = fields.One2many(
        "erpobe.bobot.komponen.cpmk", "rps_id", string="Bobot Komponen -> CPMK"
    )

    # === 4. Detail Aktivitas ===
    kegiatan_perkuliahan_ids = fields.One2many(
        "erpobe.akademik.kegiatan.perkuliahan", "rps_id", string="Kegiatan Perkuliahan"
    )
    rubrik_penilaian_ids = fields.One2many(
        "erpobe.akademik.rubrik.penilaian", "rps_id", string="Rubrik Penilaian"
    )

    # === 5. Logic Sinkronisasi Aman ===
    def _sync_bobot_tables(self):
        """
        Sinkronisasi tabel bobot tanpa menghapus nilai yang sudah diinput user.
        Hanya menambah baris baru atau menghapus baris yang validitasnya hilang.
        """
        for rps in self:
            # Snapshot komponen for exact RPS lineage. Existing master selections remain for compatibility.
            catalog_ids = set(rps.komponen_ids.ids)
            existing_catalog_ids = {
                line.komponen_id.id
                for line in rps.rps_komponen_ids
                if line.komponen_id
            }
            snapshot_commands = []
            for component in rps.komponen_ids:
                if component.id not in existing_catalog_ids:
                    snapshot_commands.append(
                        Command.create(
                            {
                                "komponen_id": component.id,
                                "name": component.name,
                                "tipe": component.tipe,
                                "description": getattr(component, "description", False),
                                "source": "catalog",
                                "aktif": True,
                            }
                        )
                    )
            obsolete_snapshots = rps.rps_komponen_ids.filtered(
                lambda line: line.komponen_id
                and line.komponen_id.id not in catalog_ids
                and line.source == "catalog"
            )
            snapshot_commands.extend(
                Command.delete(line.id) for line in obsolete_snapshots
            )
            if snapshot_commands:
                rps.write({"rps_komponen_ids": snapshot_commands})

            # --- A. Sync Bobot CPMK -> MK ---
            existing_cpmk_mk = rps.bobot_cpmk_mk_ids.mapped("cpmk_id")
            new_cpmk = rps.cpmk_ids - existing_cpmk_mk
            obsolete_cpmk = existing_cpmk_mk - rps.cpmk_ids

            cmds_mk = []
            if new_cpmk:
                cmds_mk.extend(
                    [
                        Command.create({"cpmk_id": c.id, "bobot_cpmk_mk": 0.0})
                        for c in new_cpmk
                    ]
                )
            if obsolete_cpmk:
                to_remove = rps.bobot_cpmk_mk_ids.filtered(
                    lambda l: l.cpmk_id in obsolete_cpmk
                )
                cmds_mk.extend([Command.delete(l.id) for l in to_remove])
            if cmds_mk:
                rps.write({"bobot_cpmk_mk_ids": cmds_mk})

            # --- C. Reconcile component allocations and their RPS snapshots ---
            desired_snapshots = rps.rps_komponen_ids
            desired_pairs = {
                (snapshot.id, cpmk.id)
                for snapshot in desired_snapshots
                for cpmk in rps.cpmk_ids
            }
            allocations = rps.bobot_komponen_cpmk_ids
            allocation_by_snapshot_cpmk = {
                (line.rps_komponen_id.id, line.cpmk_id.id): line
                for line in allocations
                if line.rps_komponen_id
            }
            allocation_by_catalog_cpmk = {
                (line.komponen_penilaian.id, line.cpmk_id.id): line
                for line in allocations
                if line.komponen_penilaian
            }
            cmds_komp = []
            for snapshot in desired_snapshots:
                for cpmk in rps.cpmk_ids:
                    line = allocation_by_snapshot_cpmk.get(
                        (snapshot.id, cpmk.id)
                    )
                    if not line and snapshot.komponen_id:
                        line = allocation_by_catalog_cpmk.get(
                            (snapshot.komponen_id.id, cpmk.id)
                        )
                    if line:
                        if line.rps_komponen_id != snapshot:
                            line.write({"rps_komponen_id": snapshot.id})
                    else:
                        cmds_komp.append(
                            Command.create(
                                {
                                    "cpmk_id": cpmk.id,
                                    "komponen_penilaian": snapshot.komponen_id.id,
                                    "rps_komponen_id": snapshot.id,
                                    "bobot_komponen_cpmk": 0.0,
                                }
                            )
                        )

            obsolete = allocations.filtered(
                lambda line: (
                    line.rps_komponen_id
                    and (
                        line.rps_komponen_id not in desired_snapshots
                        or (line.rps_komponen_id.id, line.cpmk_id.id)
                        not in desired_pairs
                    )
                )
                or (
                    line.komponen_penilaian
                    and line.komponen_penilaian not in rps.komponen_ids
                )
            )
            cmds_komp.extend(Command.delete(line.id) for line in obsolete)
            if cmds_komp:
                rps.write({"bobot_komponen_cpmk_ids": cmds_komp})

    @api.model_create_multi
    def create(self, vals_list):
        if any(vals.get("status") == "final" for vals in vals_list):
            raise UserError("RPS baru harus ditinjau sebelum dapat difinalisasi.")
        records = super().create(vals_list)
        records._sync_bobot_tables()
        return records

    def write(self, vals):
        if any(record.status == "final" for record in self):
            raise UserError(
                "RPS berstatus Final bersifat read-only. Salin RPS untuk membuat versi baru."
            )
        if (
            any(record.status == "review" for record in self)
            and vals.get("status") not in ("review", "final")
            and not self.env.context.get("preserve_rps_review_status")
        ):
            vals = {**vals, "status": "draft"}
        if vals.get("status") == "final":
            for rps in self:
                if rps.status != "review":
                    raise UserError(
                        "Tandai RPS sebagai Perlu Ditinjau sebelum finalisasi."
                    )
                if not self.env["erpobe.weight.validation"].validate_rps(rps)[
                    "complete"
                ]:
                    raise UserError(
                        "RPS belum dapat difinalisasi karena bobot belum lengkap 100%."
                    )
        res = super().write(vals)
        # Trigger sync jika ada perubahan pada MK, CPMK, atau Komponen
        if any(f in vals for f in ["matakuliah_id", "cpmk_ids", "komponen_ids"]):
            self._sync_bobot_tables()
        if "status" in vals:
            rps_ids = self.ids
            grade_cpmk = self.env["erpobe.grade.cpmk"].sudo().search([
                ("rps_id", "in", rps_ids),
            ])
            grade_mk = self.env["erpobe.grade.mk"].sudo().search([
                ("rps_id", "in", rps_ids),
            ])
            grade_cpl = self.env["erpobe.grade.cpl"].sudo().search([
                ("mahasiswa_id", "in", grade_cpmk.mapped("mahasiswa_id").ids),
            ])
            if grade_cpmk:
                grade_cpmk._compute_nilai_cpmk()
            if grade_mk:
                grade_mk._compute_nilai_mk()
            if grade_cpl:
                grade_cpl._compute_nilai_cpl()
                grade_cpl._compute_status_capaian()
            if grade_cpmk or grade_mk or grade_cpl:
                mhs_ids = (grade_cpmk.mapped("mahasiswa_id") | grade_mk.mapped("mahasiswa_id") | grade_cpl.mapped("mahasiswa_id")).ids
                if "erpobe.report.khs" in self.env:
                    self.env["erpobe.report.khs"].sudo().action_generate_khs(mhs_ids)
        return res

    def copy(self, default=None):
        self.ensure_one()
        values = dict(default or {})
        values.setdefault("source_rps_id", self.id)
        values.setdefault("version", self.version + 1)
        values.setdefault("status", "review")
        return super(
            ErpObeAkademikRps,
            self.with_context(preserve_rps_review_status=True),
        ).copy(values)

    def unlink(self):
        if any(record.status == "final" for record in self):
            raise UserError("RPS berstatus Final tidak dapat dihapus.")
        return super().unlink()

    def action_finalize(self):
        for rps in self:
            if rps.status != "review":
                raise UserError(
                    "Tandai RPS sebagai Perlu Ditinjau sebelum finalisasi."
                )
            validation = self.env["erpobe.weight.validation"].validate_rps(rps)
            if not validation["complete"]:
                messages = [
                    f"{item['relation']} / {item['item_name']}: {item['total']:.2f}% "
                    f"({'kurang' if item['difference'] > 0 else 'lebih'} "
                    f"{abs(item['difference']):.2f}%)"
                    for item in validation["problems"][:10]
                ]
                raise UserError(
                    "RPS belum dapat difinalisasi karena bobot belum 100%:\n"
                    + "\n".join(messages)
                )
            rps.write({"status": "final"})

    def _link_finalized_to_offer(self, penawaran_line):
        self.ensure_one()
        if self.status != "final":
            raise UserError("RPS harus difinalisasi sebelum dihubungkan ke penawaran.")
        if penawaran_line.matakuliah_id != self.matakuliah_id:
            raise ValidationError(
                "Mata kuliah pada penawaran harus sama dengan mata kuliah RPS."
            )
        if self.penawaran_line_id:
            if self.penawaran_line_id != penawaran_line:
                raise ValidationError(
                    "RPS final sudah terhubung ke penawaran mata kuliah lain."
                )
            return
        super(ErpObeAkademikRps, self).write(
            {"penawaran_line_id": penawaran_line.id}
        )

    def action_mark_for_review(self):
        for rps in self:
            if rps.status == "final":
                raise UserError("RPS Final tidak dapat ditinjau ulang; salin versinya.")
            rps.write({"status": "review"})

    def action_revise(self):
        for rps in self:
            if rps.status != "final":
                raise UserError("Hanya RPS Final yang dapat dibuat revisinya.")
            revised = rps.copy()
            return {
                "type": "ir.actions.act_window",
                "res_model": "erpobe.akademik.rps",
                "res_id": revised.id,
                "view_mode": "form",
                "target": "current",
            }


class ErpObeAkademikKegiatanPerkuliahan(models.Model):
    _name = "erpobe.akademik.kegiatan.perkuliahan"
    _inherit = ["erpobe.rps.lock.mixin"]
    _description = "Kegiatan Perkuliahan"
    _order = "minggu asc"

    rps_id = fields.Many2one("erpobe.akademik.rps", required=True, ondelete="cascade")
    minggu = fields.Integer(string="Minggu Ke", required=True)

    cpmk_id = fields.Many2one(
        "erpobe.akademik.cpmk",
        string="CPMK",
        required=True,
        domain="[('mk_id', '=', parent.matakuliah_id)]",
    )
    bahan_kajian = fields.Text(required=True)
    metode_pembelajaran_id = fields.Many2one(
        "erpobe.akademik.metode.pembelajaran", required=True
    )

    pengalaman_belajar = fields.Text()
    indikator_penilaian = fields.Text()
    estimasi_waktu = fields.Integer(string="Waktu (Menit)", default=170)

    # FIX: Definisikan 'relation' secara manual agar nama tabel pendek
    referensi_ids = fields.Many2many(
        comodel_name="erpobe.akademik.referensi",
        relation="erpobe_kegiatan_ref_rel",
        column1="kegiatan_id",
        column2="referensi_id",
        string="Referensi",
    )
    teknik_penilaian = fields.Char(
        string="teknik penilaian"
    )

    prodi_id = fields.Many2one(
        related="rps_id.prodi_id", store=True, readonly=True, index=True
    )

    fakultas_id = fields.Many2one(
        related="prodi_id.fakultas_id", store=True, readonly=True, index=True
    )

    @api.constrains("rps_id", "cpmk_id")
    def _check_activity_faculty(self):
        for record in self:
            if record.cpmk_id.mk_id != record.rps_id.matakuliah_id:
                raise ValidationError(
                    "CPMK kegiatan harus berasal dari mata kuliah pada RPS."
                )



class ErpObeAkademikMetodePembelajaran(models.Model):
    _name = "erpobe.akademik.metode.pembelajaran"
    _description = "Master Metode Pembelajaran"
    name = fields.Char(string="Nama Metode", required=True)
    kode = fields.Char(string="Kode", size=5)
    active = fields.Boolean(default=True)
    prodi_id = fields.Many2one(
        "erpobe.master.prodi", string="Program Studi", index=True
    )
    fakultas_id = fields.Many2one(
        related="prodi_id.fakultas_id", store=True, readonly=True, index=True
    )

    _uniq_name_constraint = models.Constraint('unique(name)', 'Nama metode sudah ada')


class ErpObeAkademikReferensi(models.Model):
    _name = "erpobe.akademik.referensi"  # Fix Typo
    _description = "Master Referensi / Pustaka"
    _rec_name = "judul"

    kode = fields.Char(
        string="Kode Pustaka"
    )  # Integer tidak fleksibel untuk ISBN/Kode Unik
    judul = fields.Char(required=True)
    penulis = fields.Char()
    tahun = fields.Char(size=4)
    link = fields.Char(string="URL")
    jenis = fields.Selection(
        [("utama", "Utama"), ("pendukung", "Pendukung")], default="pendukung"
    )
    prodi_id = fields.Many2one(
        "erpobe.master.prodi", string="Program Studi", index=True
    )
    fakultas_id = fields.Many2one(
        related="prodi_id.fakultas_id", store=True, readonly=True, index=True
    )


class ErpObeAkademikRubrikPenilaian(models.Model):
    _name = "erpobe.akademik.rubrik.penilaian"
    _inherit = ["erpobe.rps.lock.mixin"]
    _description = "Item Rubrik (Baris)"
    _order = "sequence, id"

    rps_id = fields.Many2one("erpobe.akademik.rps", required=True, ondelete="cascade")
    sequence = fields.Integer(default=10)

    materi_soal = fields.Text(required=True)
    komponen_id = fields.Many2one("erpobe.akademik.komponen", required=True)
    cpmk_id = fields.Many2one("erpobe.akademik.cpmk", required=True)
    bobot = fields.Float(string="Bobot (%)", required=True)

    # === FIXED RELATION ===
    kriteria_ids = fields.One2many(
        "erpobe.akademik.kriteria", "rubrik_id", string="Detail Kriteria"
    )

    prodi_id = fields.Many2one(
        related="rps_id.prodi_id", store=True, readonly=True, index=True
    )

    fakultas_id = fields.Many2one(
        related="prodi_id.fakultas_id", store=True, readonly=True, index=True
    )

    @api.constrains("rps_id", "cpmk_id")
    def _check_rubric_faculty(self):
        for record in self:
            if record.cpmk_id.mk_id != record.rps_id.matakuliah_id:
                raise ValidationError(
                    "CPMK rubrik harus berasal dari mata kuliah pada RPS."
                )

    def action_open_kriteria(self):
        """ Membuka form view rubrik untuk mengedit kriteria secara detail """
        self.ensure_one()
        return {
            'name': 'Detail Kriteria Penilaian',
            'type': 'ir.actions.act_window',
            'res_model': 'erpobe.akademik.rubrik.penilaian',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }


class ErpObeAkademikKriteria(models.Model):
    _name = "erpobe.akademik.kriteria"
    _inherit = ["erpobe.rps.lock.mixin"]
    _rps_link_field = "rubrik_id.rps_id"
    _description = "Kriteria Penilaian RPS"

    # === FIXED RELATION ===
    rubrik_id = fields.Many2one(
        "erpobe.akademik.rubrik.penilaian", required=True, ondelete="cascade"
    )

    # Relasi ke Master Grade Global
    grade_id = fields.Many2one("erpobe.master.grade", string="Grade", required=True)

    # Data Readonly dari Global
    nilai_min = fields.Float(related="grade_id.nilai_min", readonly=True)
    nilai_max = fields.Float(related="grade_id.nilai_max", readonly=True)

    # Data Spesifik
    deskripsi = fields.Text(string="Deskripsi Spesifik", required=True)

    _uniq_grade_item_constraint = models.Constraint('unique(rubrik_id, grade_id)', 'Grade duplikat dalam satu item soal')

    prodi_id = fields.Many2one(
        related="rubrik_id.prodi_id", store=True, readonly=True, index=True
    )

    fakultas_id = fields.Many2one(
        related="prodi_id.fakultas_id", store=True, readonly=True, index=True
    )

    @api.onchange("grade_id")
    def _onchange_grade(self):
        if self.grade_id and not self.deskripsi:
            self.deskripsi = self.grade_id.keterangan_standar
