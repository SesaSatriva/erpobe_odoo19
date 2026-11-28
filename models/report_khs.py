from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)


class ErpObeReportKhs(models.Model):
    _name = "erpobe.report.khs"
    _description = "Rekap Hasil Studi (Transkrip)"
    _inherit = ["mail.thread", "mail.activity.mixin", "erpobe.audit.mixin"]
    _rec_name = "mahasiswa_id"
    _order = "angkatan desc, mahasiswa_id asc"

    # === HEADER ===
    mahasiswa_id = fields.Many2one(
        "erpobe.master.mahasiswa",
        string="Mahasiswa",
        required=True,
        index=True,
        tracking=True,
    )
    tahun_ajaran_id = fields.Many2one('erpobe.akademik.tahunajaran', string='Tahun Ajaran')
    nim = fields.Char(related="mahasiswa_id.nim", store=True)
    rombel_id = fields.Many2one(related="mahasiswa_id.rombel_id", store=True)
    angkatan = fields.Integer(related="rombel_id.angkatan", store=True)

    # State & Info
    tanggal_cetak = fields.Date(
        string="Terakhir Update", default=fields.Date.context_today, readonly=True
    )

    # === LINES ===
    mk_line_ids = fields.One2many(
        "erpobe.report.khs.mk", "khs_id", string="Nilai Mata Kuliah", readonly=True
    )
    cpmk_line_ids = fields.One2many(
        "erpobe.report.khs.cpmk", "khs_id", string="Capaian CPMK", readonly=True
    )
    cpl_line_ids = fields.One2many(
        "erpobe.report.khs.cpl", "khs_id", string="Capaian CPL", readonly=True
    )
    komponen_line_ids = fields.One2many(
        "erpobe.report.khs.komponen",
        "khs_id",
        string="Nilai Komponen",
        readonly=True,
    )

    # === STATISTIK ===
    total_sks_lulus = fields.Integer(
        string="Total SKS Lulus",
        compute="_compute_statistik",
        store=True,
        tracking=True,
    )
    ipk = fields.Float(
        string="IPK",
        compute="_compute_statistik",
        store=True,
        digits=(4, 2),
        tracking=True,
    )

    _uniq_mahasiswa_khs_constraint = models.Constraint('unique(mahasiswa_id)', 'Mahasiswa ini sudah memiliki dokumen Transkrip.')

    # === CORE METHODS ===

    prodi_id = fields.Many2one(
        related="mahasiswa_id.prodi_id", store=True, readonly=True, index=True
    )

    fakultas_id = fields.Many2one(
        related="prodi_id.fakultas_id", store=True, readonly=True, index=True
    )

    @api.model_create_multi
    def create(self, vals_list):
        """Override create untuk otomatis fetch nilai saat record dibuat."""
        records = super().create(vals_list)
        if not self.env.context.get("defer_khs_sync"):
            records._sync_from_grades()
        return records

    @api.model
    def action_generate_khs(self, mahasiswa_ids):
        """
        Public Method: Dipanggil dari erpobe.input.nilai atau erpobe.grade.mk.
        Mencakup logika: Jika belum ada -> Create, Jika sudah ada -> Sync.
        """
        if not mahasiswa_ids:
            return

        mahasiswa_ids = list(dict.fromkeys(mahasiswa_ids))
        existing_reports = self.search([("mahasiswa_id", "in", mahasiswa_ids)])
        existing_mhs_ids = existing_reports.mapped("mahasiswa_id.id")
        existing_mhs_set = set(existing_mhs_ids)
        new_mhs_ids = [
            mahasiswa_id
            for mahasiswa_id in mahasiswa_ids
            if mahasiswa_id not in existing_mhs_set
        ]
        new_reports = self.browse()
        if new_mhs_ids:
            _logger.info(f"[KHS] Creating reports for {len(new_mhs_ids)} students.")
            new_reports = self.with_context(defer_khs_sync=True).create(
                [{"mahasiswa_id": mahasiswa_id} for mahasiswa_id in new_mhs_ids]
            )

        if existing_reports:
            _logger.info(
                f"[KHS] Updating reports for {len(existing_reports)} students."
            )
        (existing_reports | new_reports)._sync_from_grades()

        return True

    def action_fetch_nilai(self):
        """Action Button untuk manual refresh."""
        self._sync_from_grades()

    def _sync_from_grades(self):
        """
        Engine utama sinkronisasi.
        Mengambil data dari model erpobe.grade.* dan mengisi line report.
        """
        reports = self.exists()
        if not reports:
            return False
        reports_by_student = {
            report.mahasiswa_id.id: report
            for report in reports
        }
        student_ids = list(reports_by_student)

        GradeMk = self.env["erpobe.grade.mk"].sudo()
        source_mk = GradeMk.search(
            [("mahasiswa_id", "in", student_ids)],
            order="semester asc, kode_mk asc",
        )
        source_mk = source_mk.filtered(
            lambda grade: (
                not grade.krs_line_id
                or grade.krs_line_id.krs_id.state == "approved"
            )
        )
        best_mk = {}
        for grade in source_mk:
            key = (grade.mahasiswa_id.id, grade.mk_id.id)
            current = best_mk.get(key)
            if (
                not current
                or (grade.is_available and not current.is_available)
                or (
                    grade.is_available
                    and current.is_available
                    and grade.nilai_mk > current.nilai_mk
                )
            ):
                best_mk[key] = grade
        source_mk_by_student = {}
        mk_ids_by_student = {}
        for (student_id, _mk_id), grade in best_mk.items():
            source_mk_by_student.setdefault(student_id, []).append(grade)
            mk_ids_by_student.setdefault(student_id, set()).add(grade.mk_id.id)
        for student_id, grades in source_mk_by_student.items():
            source_mk_by_student[student_id] = sorted(
                grades,
                key=lambda grade: (grade.semester, grade.kode_mk or ""),
            )

        # Match the previous per-student course filter while searching in one batch.
        mk_ids_taken = set().union(*mk_ids_by_student.values()) if mk_ids_by_student else set()
        GradeCpmk = self.env["erpobe.grade.cpmk"].sudo()
        source_cpmk = GradeCpmk.search(
            [
                ("mahasiswa_id", "in", student_ids),
                ("mk_id", "in", list(mk_ids_taken)),
            ]
        )
        source_cpmk = source_cpmk.filtered(
            lambda grade: (
                not grade.krs_line_id
                or grade.krs_line_id.krs_id.state == "approved"
            )
        )
        best_cpmk = {}
        for grade in source_cpmk:
            student_id = grade.mahasiswa_id.id
            if grade.mk_id.id not in mk_ids_by_student.get(student_id, set()):
                continue
            key = (student_id, grade.cpmk_id.id)
            current = best_cpmk.get(key)
            if (
                not current
                or (grade.is_available and not current.is_available)
                or (
                    grade.is_available
                    and current.is_available
                    and grade.nilai_cpmk > current.nilai_cpmk
                )
            ):
                best_cpmk[key] = grade
        source_cpmk_by_student = {}
        for (student_id, _cpmk_id), grade in best_cpmk.items():
            source_cpmk_by_student.setdefault(student_id, []).append(grade)

        GradeCpl = self.env["erpobe.grade.cpl"].sudo()
        source_cpl = GradeCpl.search([("mahasiswa_id", "in", student_ids)])
        source_cpl_by_student = {}
        for grade in source_cpl:
            source_cpl_by_student.setdefault(grade.mahasiswa_id.id, []).append(grade)

        GradeKomponen = self.env["erpobe.grade.komponen"].sudo()
        source_komponen = GradeKomponen.search(
            [
                ("mahasiswa_id", "in", student_ids),
                ("is_graded", "=", True),
                ("krs_line_id.krs_id.state", "=", "approved"),
                ("rps_id.status", "=", "final"),
            ],
            order="id asc",
        )
        source_komponen_by_student = {}
        for grade in source_komponen:
            source_komponen_by_student.setdefault(
                grade.mahasiswa_id.id, []
            ).append(grade)

        self._sync_detail_lines(
            "erpobe.report.khs.mk", source_mk_by_student
        )
        self._sync_detail_lines(
            "erpobe.report.khs.cpmk", source_cpmk_by_student
        )
        self._sync_detail_lines(
            "erpobe.report.khs.cpl", source_cpl_by_student
        )
        self._sync_detail_lines(
            "erpobe.report.khs.komponen", source_komponen_by_student
        )

        today = fields.Date.context_today(self)
        reports_to_stamp = reports.filtered(
            lambda report: report.tanggal_cetak != today
        )
        if reports_to_stamp:
            reports_to_stamp.write({"tanggal_cetak": today})
        return True

    def _sync_detail_lines(self, line_model_name, source_by_student):
        line_model = self.env[line_model_name]
        report_by_student = {
            report.mahasiswa_id.id: report
            for report in self
        }
        desired_pairs = {
            (report_by_student[student_id].id, source.id)
            for student_id, sources in source_by_student.items()
            if student_id in report_by_student
            for source in sources
        }
        existing_lines = line_model.search([("khs_id", "in", self.ids)])
        existing_pairs = set()
        stale_ids = []
        for line in existing_lines:
            pair = (line.khs_id.id, line.grade_id.id)
            if pair not in desired_pairs or pair in existing_pairs:
                stale_ids.append(line.id)
            else:
                existing_pairs.add(pair)

        if stale_ids:
            line_model.browse(stale_ids).unlink()

        missing_pairs = desired_pairs - existing_pairs
        if missing_pairs:
            line_model.create([
                {"khs_id": khs_id, "grade_id": grade_id}
                for khs_id, grade_id in sorted(missing_pairs)
            ])

    @api.depends(
        "mk_line_ids.bobot",
        "mk_line_ids.sks",
        "mk_line_ids.kode_mk",
        "mk_line_ids.nilai_angka",
        "mk_line_ids.data_available",
    )
    def _compute_statistik(self):
        """
        Menghitung IPK dengan Logic 'Best Grade' (Nilai Terbaik).
        Jika ada MK mengulang, ambil bobot tertinggi saja agar SKS pembagi tidak dobel.
        """
        for rec in self:
            # 1. Dictionary untuk menyimpan Nilai Terbaik per Kode MK
            # Format: {'KODE_MK': record_line_terbaik}
            best_grades = {}

            # Ambil hanya attempt yang tersedia; nilai 0 aktual tetap bernilai aktual.
            valid_lines = rec.mk_line_ids.filtered(
                lambda l: l.sks > 0 and l.data_available
            )

            for line in valid_lines:
                kode = line.kode_mk
                if not kode: 
                    continue # Skip jika master data kotor (tidak ada kode)

                # Retake: gunakan nilai numerik terbaik agar konsisten dengan CPL.
                # Urutan baris tidak boleh menentukan hasil jika nilai numeriknya sama.
                if kode not in best_grades:
                    best_grades[kode] = line
                else:
                    current = best_grades[kode]
                    if (
                        line.nilai_angka > current.nilai_angka
                        or (
                            line.nilai_angka == current.nilai_angka
                            and line.bobot > current.bobot
                        )
                    ):
                        best_grades[kode] = line
            
            # 2. Hitung Total dari Dictionary 'best_grades'
            # Sekarang setiap Kode MK hanya muncul 1 kali (yang terbaik)
            final_lines = best_grades.values()
            
            total_sks_ambil = sum(l.sks for l in final_lines)
            total_mutu = sum(l.sks * l.bobot for l in final_lines)

            # 3. Hitung SKS lulus berdasarkan konfigurasi batas kelulusan.
            passing_score = float(
                rec.env["ir.config_parameter"].sudo().get_param(
                    "erpobe.krs.minimum_passing_score", "60"
                )
            )
            sks_lulus_lines = [
                l for l in final_lines
                if l.nilai_angka >= passing_score
            ]
            rec.total_sks_lulus = sum(l.sks for l in sks_lulus_lines)

            # 4. Hitung IPK
            if total_sks_ambil > 0:
                rec.ipk = total_mutu / total_sks_ambil
            else:
                rec.ipk = 0.0


# === LINE MODELS ===


class ErpObeReportKhsMk(models.Model):
    _name = "erpobe.report.khs.mk"
    _description = "Line KHS MK"
    _order = "semester_mk asc"

    khs_id = fields.Many2one("erpobe.report.khs", ondelete="cascade")
    grade_id = fields.Many2one("erpobe.grade.mk", required=True)

    # Data Related (Auto update jika Master Grade berubah)
    mk_id = fields.Many2one(related="grade_id.mk_id", store=True)
    mk_name = fields.Char(related="mk_id.name", store=True, index=True)
    nilai_angka = fields.Float(related="grade_id.nilai_mk", store=True)
    semester_mk = fields.Integer(related="mk_id.semester", store=True)
    kode_mk = fields.Char(related="mk_id.kode_mk", store=True)
    sks = fields.Integer(related="mk_id.sks", store=True)
    data_available = fields.Boolean(
        related="grade_id.is_available", store=True, readonly=True
    )
    nilai_tampil = fields.Char(compute="_compute_nilai_tampil", store=True)

    # Data Computed (Konversi Angka ke Huruf)
    nilai_huruf = fields.Char(compute="_compute_grade", store=True)
    bobot = fields.Float(compute="_compute_grade", store=True, digits=(3, 2))

    prodi_id = fields.Many2one(
        related="khs_id.prodi_id", store=True, readonly=True, index=True
    )

    fakultas_id = fields.Many2one(
        related="prodi_id.fakultas_id", store=True, readonly=True, index=True
    )

    @api.depends("nilai_angka", "data_available")
    def _compute_nilai_tampil(self):
        for rec in self:
            rec.nilai_tampil = (
                f"{rec.nilai_angka:.2f}" if rec.data_available else "Belum tersedia"
            )

    @api.depends("nilai_angka", "data_available")
    def _compute_grade(self):
        # Optimasi: Fetch Master Grade hanya sekali di luar loop record
        grades = (
            self.env["erpobe.master.grade"].sudo().search([], order="nilai_min desc")
        )

        for rec in self:
            if not rec.data_available:
                rec.nilai_huruf = False
                rec.bobot = 0.0
                continue
            rec.nilai_huruf = False
            rec.bobot = 0.0

            # Loop in-memory (Cepat)
            for g in grades:
                if rec.nilai_angka >= g.nilai_min:
                    rec.nilai_huruf = g.name
                    rec.bobot = g.bobot
                    break


class ErpObeReportKhsCpmk(models.Model):
    _name = "erpobe.report.khs.cpmk"
    _description = "Line KHS CPMK"

    khs_id = fields.Many2one("erpobe.report.khs", ondelete="cascade")
    grade_id = fields.Many2one("erpobe.grade.cpmk", required=True)

    cpmk_id = fields.Many2one(related="grade_id.cpmk_id", store=True)
    mk_id = fields.Many2one(related="grade_id.mk_id", store=True)
    nilai_angka = fields.Float(related="grade_id.nilai_cpmk", store=True)
    data_available = fields.Boolean(
        related="grade_id.is_available", store=True, readonly=True
    )
    nilai_tampil = fields.Char(compute="_compute_nilai_tampil", store=True)

    prodi_id = fields.Many2one(
        related="khs_id.prodi_id", store=True, readonly=True, index=True
    )

    fakultas_id = fields.Many2one(
        related="prodi_id.fakultas_id", store=True, readonly=True, index=True
    )

    @api.depends("nilai_angka", "data_available")
    def _compute_nilai_tampil(self):
        for rec in self:
            rec.nilai_tampil = (
                f"{rec.nilai_angka:.2f}" if rec.data_available else "Belum tersedia"
            )



class ErpObeReportKhsCpl(models.Model):
    _name = "erpobe.report.khs.cpl"
    _description = "Line KHS CPL"

    khs_id = fields.Many2one("erpobe.report.khs", ondelete="cascade")
    grade_id = fields.Many2one("erpobe.grade.cpl", required=True)

    cpl_id = fields.Many2one(related="grade_id.cpl_id", store=True)
    nilai_angka = fields.Float(related="grade_id.nilai_cpl", store=True)
    data_available = fields.Boolean(
        related="grade_id.is_available", store=True, readonly=True
    )
    nilai_tampil = fields.Char(compute="_compute_nilai_tampil", store=True)
    prodi_id = fields.Many2one(
        related="khs_id.prodi_id", store=True, readonly=True, index=True
    )

    fakultas_id = fields.Many2one(
        related="prodi_id.fakultas_id", store=True, readonly=True, index=True
    )

    @api.depends("nilai_angka", "data_available")
    def _compute_nilai_tampil(self):
        for rec in self:
            rec.nilai_tampil = (
                f"{rec.nilai_angka:.2f}" if rec.data_available else "Belum tersedia"
            )


class ErpObeReportKhsKomponen(models.Model):
    _name = "erpobe.report.khs.komponen"
    _description = "Line KHS Komponen Penilaian"
    _order = "mk_id, komponen_id"

    khs_id = fields.Many2one("erpobe.report.khs", ondelete="cascade")
    grade_id = fields.Many2one(
        "erpobe.grade.komponen", required=True, ondelete="cascade"
    )
    mk_id = fields.Many2one(
        related="grade_id.krs_line_id.matakuliah_id", store=True
    )
    komponen_id = fields.Many2one(
        related="grade_id.komponen_id", store=True
    )
    tipe = fields.Selection(
        related="komponen_id.tipe", string="Jenis Aktivitas", store=True
    )
    nilai_angka = fields.Float(related="grade_id.nilai", store=True)
    origin = fields.Selection(related="grade_id.origin", store=True)
    prodi_id = fields.Many2one(
        related="khs_id.prodi_id", store=True, readonly=True, index=True
    )
    fakultas_id = fields.Many2one(
        related="prodi_id.fakultas_id", store=True, readonly=True, index=True
    )

