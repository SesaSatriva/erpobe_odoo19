from odoo import models, fields, api, tools
from odoo.exceptions import ValidationError


class ErpObeGradeMk(models.Model):
    _name = "erpobe.grade.mk"
    _inherit = ["erpobe.audit.mixin"]
    _description = "Nilai Akhir Mata Kuliah"

    mahasiswa_id = fields.Many2one("erpobe.master.mahasiswa", required=True, index=True)
    mk_id = fields.Many2one("erpobe.master.matakuliah", required=True, index=True)
    krs_line_id = fields.Many2one(
        "erpobe.akademik.krs.line", string="Attempt KRS", ondelete="restrict", index=True
    )
    rps_id = fields.Many2one(
        "erpobe.akademik.rps", string="RPS Digunakan", ondelete="restrict", index=True
    )
    semester = fields.Integer(related="mk_id.semester", store=True, string="Semester")
    kode_mk = fields.Char(related="mk_id.kode_mk", store=True, string="Kode MK")
    nilai_mk = fields.Float(compute="_compute_nilai_mk", store=True, digits=(16, 2))
    is_available = fields.Boolean(
        string="Data Tersedia", compute="_compute_nilai_mk", store=True
    )

    _uniq_mhs_mk_attempt_constraint = models.Constraint(
        "unique(mahasiswa_id, mk_id, krs_line_id)",
        "Nilai MK untuk attempt KRS yang sama sudah ada.",
    )

    # === UPDATE TRIGGER (PENTING: Agar Transkrip Realtime) ===

    prodi_id = fields.Many2one(
        related="mahasiswa_id.prodi_id", store=True, readonly=True, index=True
    )

    fakultas_id = fields.Many2one(
        related="prodi_id.fakultas_id", store=True, readonly=True, index=True
    )

    @api.constrains("mahasiswa_id", "mk_id")
    def _check_grade_faculty(self):
        for record in self:
            if (
                record.mahasiswa_id
                and record.mk_id
                and record.mahasiswa_id.prodi_id != record.mk_id.prodi_id
            ):
                raise ValidationError(
                    "Nilai mata kuliah dan mahasiswa harus berada di fakultas "
                    "yang sama."
                )

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        self._trigger_report_sync(records)
        return records

    def write(self, vals):
        res = super().write(vals)
        self._trigger_report_sync(self)
        return res

    def _trigger_report_sync(self, records):
        """
        Memaksa Report KHS untuk refresh saat ada nilai MK baru/berubah.
        Ini memastikan mata kuliah baru langsung muncul di transkrip.
        """
        if self.env.context.get("skip_khs_refresh"):
            return

        # Cari Report KHS milik mahasiswa yang terdampak
        mhs_ids = records.mapped("mahasiswa_id.id")
        if not mhs_ids:
            return

        reports = (
            self.env["erpobe.report.khs"]
            .sudo()
            .search([("mahasiswa_id", "in", mhs_ids)])
        )

        for report in reports:
            # Panggil method sync yang sudah kita buat di erpobe.report.khs
            report._sync_from_grades()

    # === COMPUTE LOGIC ===
    @api.depends(
        "rps_id.status",
        "krs_line_id.krs_id.state",
        "mahasiswa_id.grade_cpmk_ids.nilai_cpmk",
        "mahasiswa_id.grade_cpmk_ids.is_available",
        "mahasiswa_id.grade_cpmk_ids.rps_id.status",
        "mahasiswa_id.grade_cpmk_ids.krs_line_id.krs_id.state",
        "rps_id.bobot_cpmk_mk_ids.bobot_cpmk_mk",
        "rps_id.status",
        "krs_line_id.krs_id.state",
    )
    def _compute_nilai_mk(self):
        Rps = self.env["erpobe.akademik.rps"]
        BobotCpmkMk = self.env["erpobe.bobot.cpmk.mk"]
        GradeCpmk = self.env["erpobe.grade.cpmk"]

        for rec in self:
            rec.nilai_mk = 0.0
            rec.is_available = False

        exact_records = self.filtered(
            lambda grade:
                grade.rps_id
                and grade.rps_id.status == "final"
                and grade.krs_line_id
                and grade.krs_line_id.krs_id.state == "approved"
        )
        weight_lines = BobotCpmkMk.search([
            ("rps_id", "in", exact_records.mapped("rps_id").ids),
        ])
        weights_by_rps = {}
        for weight_line in weight_lines:
            weights_by_rps.setdefault(weight_line.rps_id.id, []).append(weight_line)

        cpmk_grades = GradeCpmk.search([
            ("mahasiswa_id", "in", exact_records.mapped("mahasiswa_id").ids),
            ("krs_line_id", "in", exact_records.mapped("krs_line_id").ids),
            ("rps_id", "in", exact_records.mapped("rps_id").ids),
            ("is_available", "=", True),
            ("rps_id.status", "=", "final"),
            ("krs_line_id.krs_id.state", "=", "approved"),
        ])
        grade_map = {
            (
                grade.mahasiswa_id.id,
                grade.krs_line_id.id,
                grade.rps_id.id,
                grade.cpmk_id.id,
            ): grade
            for grade in cpmk_grades
        }
        for rec in exact_records:
            total_score = 0.0
            total_weight = 0.0
            for weight_line in weights_by_rps.get(rec.rps_id.id, []):
                grade = grade_map.get(
                    (
                        rec.mahasiswa_id.id,
                        rec.krs_line_id.id,
                        rec.rps_id.id,
                        weight_line.cpmk_id.id,
                    )
                )
                if not grade or weight_line.bobot_cpmk_mk <= 0:
                    continue
                total_score += grade.nilai_cpmk * weight_line.bobot_cpmk_mk / 100.0
                total_weight += weight_line.bobot_cpmk_mk / 100.0
            rec.is_available = bool(total_weight)
            rec.nilai_mk = (
                total_score / total_weight if total_weight else 0.0
            )

        legacy_records = self.filtered(lambda grade: not grade.rps_id or not grade.krs_line_id)
        for rec in legacy_records:
            rec.nilai_mk = 0.0
            rec.is_available = False


class ErpObeGradeMkRombel(models.Model):
    _name = "erpobe.grade.mk.rombel"
    _description = "Agregasi Nilai MK per Rombel"
    _auto = False

    rombel_id = fields.Many2one(
        "erpobe.master.rombel",
        string="Rombel",
        readonly=True,
    )

    mk_id = fields.Many2one(
        "erpobe.master.matakuliah",
        string="Mata Kuliah",
        readonly=True,
    )
    prodi_id = fields.Many2one("erpobe.master.prodi", readonly=True, index=True)
    fakultas_id = fields.Many2one(
        related="prodi_id.fakultas_id", readonly=True, index=True
    )

    nilai_rata_mk = fields.Float(
        string="Rata-rata Nilai MK",
        readonly=True,
    )
    jumlah_mahasiswa = fields.Integer(string="Jumlah Mahasiswa (N)", readonly=True)
    jumlah_nilai_tersedia = fields.Integer(string="Nilai Tersedia", readonly=True)
    jumlah_nilai_belum_tersedia = fields.Integer(string="Belum Memiliki Nilai", readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(f"""
            CREATE VIEW {self._table} AS (
                SELECT
                    MIN(gm.id) AS id,
                    m.rombel_id AS rombel_id,
                    m.prodi_id AS prodi_id,
                    r.fakultas_id AS fakultas_id,
                    gm.mk_id AS mk_id,
                    AVG(gm.nilai_mk) FILTER (WHERE gm.is_available IS TRUE) AS nilai_rata_mk,
                    COUNT(DISTINCT gm.mahasiswa_id) AS jumlah_mahasiswa,
                    COUNT(DISTINCT gm.mahasiswa_id) FILTER (WHERE gm.is_available IS TRUE) AS jumlah_nilai_tersedia,
                    COUNT(DISTINCT gm.mahasiswa_id) FILTER (WHERE gm.is_available IS NOT TRUE) AS jumlah_nilai_belum_tersedia
                FROM erpobe_grade_mk gm
                JOIN erpobe_master_mahasiswa m
                    ON m.id = gm.mahasiswa_id
                JOIN erpobe_master_rombel r
                    ON r.id = m.rombel_id
                WHERE m.rombel_id IS NOT NULL
                GROUP BY m.rombel_id, m.prodi_id, r.fakultas_id, gm.mk_id
            )
        """)


class ErpObeGradeMkAngkatan(models.Model):
    _name = "erpobe.grade.mk.angkatan"
    _description = "Agregasi Nilai MK per Angkatan"
    _auto = False

    angkatan = fields.Integer(
        string="Angkatan",
        readonly=True,
    )

    mk_id = fields.Many2one(
        "erpobe.master.matakuliah",
        string="Mata Kuliah",
        readonly=True,
    )

    nilai_rata_mk = fields.Float(
        string="Rata-rata Nilai MK Angkatan",
        readonly=True,
    )
    jumlah_mahasiswa = fields.Integer(string="Jumlah Mahasiswa (N)", readonly=True)
    jumlah_nilai_tersedia = fields.Integer(string="Nilai Tersedia", readonly=True)
    jumlah_nilai_belum_tersedia = fields.Integer(string="Belum Memiliki Nilai", readonly=True)

    prodi_id = fields.Many2one("erpobe.master.prodi", readonly=True, index=True)
    fakultas_id = fields.Many2one(
        "erpobe.master.fakultas", readonly=True, index=True
    )

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(f"""
            CREATE VIEW {self._table} AS (
                SELECT
                    MIN(gm.id) AS id,
                    r.angkatan AS angkatan,
                    gm.mk_id AS mk_id,
                    m.prodi_id AS prodi_id,
                    r.fakultas_id AS fakultas_id,
                    AVG(gm.nilai_mk) FILTER (WHERE gm.is_available IS TRUE) AS nilai_rata_mk,
                    COUNT(DISTINCT gm.mahasiswa_id) AS jumlah_mahasiswa,
                    COUNT(DISTINCT gm.mahasiswa_id) FILTER (WHERE gm.is_available IS TRUE) AS jumlah_nilai_tersedia,
                    COUNT(DISTINCT gm.mahasiswa_id) FILTER (WHERE gm.is_available IS NOT TRUE) AS jumlah_nilai_belum_tersedia
                FROM erpobe_grade_mk gm
                JOIN erpobe_master_mahasiswa m
                    ON m.id = gm.mahasiswa_id
                JOIN erpobe_master_rombel r
                    ON r.id = m.rombel_id
                GROUP BY r.angkatan, gm.mk_id, m.prodi_id, r.fakultas_id
            )
        """)
