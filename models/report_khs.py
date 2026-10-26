from odoo import models, fields, api, Command, _
import logging

_logger = logging.getLogger(__name__)


class ErpObeReportKhs(models.Model):
    _name = "erpobe.report.khs"
    _description = "Rekap Hasil Studi (Transkrip)"
    _inherit = ["mail.thread", "mail.activity.mixin"]
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

    @api.model_create_multi
    def create(self, vals_list):
        """Override create untuk otomatis fetch nilai saat record dibuat."""
        records = super().create(vals_list)
        for rec in records:
            rec._sync_from_grades()
        return records

    @api.model
    def action_generate_khs(self, mahasiswa_ids):
        """
        Public Method: Dipanggil dari erpobe.input.nilai atau erpobe.grade.mk.
        Mencakup logika: Jika belum ada -> Create, Jika sudah ada -> Sync.
        """
        if not mahasiswa_ids:
            return

        # 1. Pisahkan Existing vs New
        existing_reports = self.search([("mahasiswa_id", "in", mahasiswa_ids)])
        existing_mhs_ids = existing_reports.mapped("mahasiswa_id.id")

        all_mhs_set = set(mahasiswa_ids)
        existing_mhs_set = set(existing_mhs_ids)
        new_mhs_ids = list(all_mhs_set - existing_mhs_set)

        # 2. CREATE (Otomatis trigger _sync_from_grades via override create)
        if new_mhs_ids:
            _logger.info(f"[KHS] Creating reports for {len(new_mhs_ids)} students.")
            self.create([{"mahasiswa_id": mid} for mid in new_mhs_ids])

        # 3. UPDATE (Force sync manual untuk data lama)
        if existing_reports:
            _logger.info(
                f"[KHS] Updating reports for {len(existing_reports)} students."
            )
            for report in existing_reports:
                report._sync_from_grades()

        return True

    def action_fetch_nilai(self):
        """Action Button untuk manual refresh."""
        self._sync_from_grades()

    def _sync_from_grades(self):
        """
        Engine utama sinkronisasi.
        Mengambil data dari model erpobe.grade.* dan mengisi line report.
        """
        self.ensure_one()
        mhs_id = self.mahasiswa_id.id

        # A. Fetch Grade MK (Urut Semester & Kode)
        GradeMk = self.env["erpobe.grade.mk"].sudo()
        source_mk = GradeMk.search(
            [("mahasiswa_id", "=", mhs_id)], order="semester asc, kode_mk asc"
        )

        # Gunakan Command.clear() untuk menghapus data lama dan insert baru (Snapshot)
        mk_cmds = [Command.clear()] + [
            Command.create({"mk_id": g.mk_id.id, "grade_id": g.id}) for g in source_mk
        ]

        # Simpan ID MK yang diambil untuk filter CPMK
        mk_ids_taken = source_mk.mapped("mk_id.id")

        # B. Fetch Grade CPMK (Hanya untuk MK yang diambil)
        GradeCpmk = self.env["erpobe.grade.cpmk"].sudo()
        source_cpmk = GradeCpmk.search(
            [("mahasiswa_id", "=", mhs_id), ("mk_id", "in", mk_ids_taken)]
        )
        cpmk_cmds = [Command.clear()] + [
            Command.create({"cpmk_id": g.cpmk_id.id, "grade_id": g.id})
            for g in source_cpmk
        ]

        # C. Fetch Grade CPL
        GradeCpl = self.env["erpobe.grade.cpl"].sudo()
        source_cpl = GradeCpl.search([("mahasiswa_id", "=", mhs_id)])
        cpl_cmds = [Command.clear()] + [
            Command.create({"cpl_id": g.cpl_id.id, "grade_id": g.id})
            for g in source_cpl
        ]

        # D. Execute Write
        self.write(
            {
                "mk_line_ids": mk_cmds,
                "cpmk_line_ids": cpmk_cmds,
                "cpl_line_ids": cpl_cmds,
                "tanggal_cetak": fields.Date.context_today(self),
            }
        )

    @api.depends("mk_line_ids.bobot", "mk_line_ids.sks", "mk_line_ids.kode_mk")
    def _compute_statistik(self):
        """
        Menghitung IPK dengan Logic 'Best Grade' (Nilai Terbaik).
        Jika ada MK mengulang, ambil bobot tertinggi saja agar SKS pembagi tidak dobel.
        """
        for rec in self:
            # 1. Dictionary untuk menyimpan Nilai Terbaik per Kode MK
            # Format: {'KODE_MK': record_line_terbaik}
            best_grades = {}

            # Filter hanya yang SKS > 0 (MK Valid)
            valid_lines = rec.mk_line_ids.filtered(lambda l: l.sks > 0)

            for line in valid_lines:
                kode = line.kode_mk
                if not kode: 
                    continue # Skip jika master data kotor (tidak ada kode)

                # Logic: Jika belum ada atau bobot nilai ini lebih tinggi dari yang tersimpan
                if kode not in best_grades:
                    best_grades[kode] = line
                else:
                    # Cek mana yang lebih bagus? Yang lama atau yang baru?
                    if line.bobot > best_grades[kode].bobot:
                        best_grades[kode] = line
            
            # 2. Hitung Total dari Dictionary 'best_grades'
            # Sekarang setiap Kode MK hanya muncul 1 kali (yang terbaik)
            final_lines = best_grades.values()
            
            total_sks_ambil = sum(l.sks for l in final_lines)
            total_mutu = sum(l.sks * l.bobot for l in final_lines)

            # 3. Hitung Total SKS Lulus (Total SKS MK unik yang bobotnya > 0)
            # Biasanya MK dengan nilai E (bobot 0) tidak dihitung dalam 'Total SKS Lulus' di transkrip
            sks_lulus_lines = [l for l in final_lines if l.bobot > 0]
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
    nilai_angka = fields.Float(related="grade_id.nilai_mk", store=True)
    semester_mk = fields.Integer(related="mk_id.semester", store=True)
    kode_mk = fields.Char(related="mk_id.kode_mk", store=True)
    sks = fields.Integer(related="mk_id.sks", store=True)

    # Data Computed (Konversi Angka ke Huruf)
    nilai_huruf = fields.Char(compute="_compute_grade", store=True)
    bobot = fields.Float(compute="_compute_grade", store=True, digits=(3, 2))

    @api.depends("nilai_angka")
    def _compute_grade(self):
        # Optimasi: Fetch Master Grade hanya sekali di luar loop record
        grades = (
            self.env["erpobe.master.grade"].sudo().search([], order="nilai_min desc")
        )

        for rec in self:
            rec.nilai_huruf = "E"
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


class ErpObeReportKhsCpl(models.Model):
    _name = "erpobe.report.khs.cpl"
    _description = "Line KHS CPL"

    khs_id = fields.Many2one("erpobe.report.khs", ondelete="cascade")
    grade_id = fields.Many2one("erpobe.grade.cpl", required=True)

    cpl_id = fields.Many2one(related="grade_id.cpl_id", store=True)
    nilai_angka = fields.Float(related="grade_id.nilai_cpl", store=True)