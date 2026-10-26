from odoo import models, fields, api, tools


class ErpObeGradeMk(models.Model):
    _name = "erpobe.grade.mk"
    _description = "Nilai Akhir Mata Kuliah"

    mahasiswa_id = fields.Many2one("erpobe.master.mahasiswa", required=True, index=True)
    mk_id = fields.Many2one("erpobe.master.matakuliah", required=True, index=True)
    semester = fields.Integer(related="mk_id.semester", store=True, string="Semester")
    kode_mk = fields.Char(related="mk_id.kode_mk", store=True, string="Kode MK")
    nilai_mk = fields.Float(compute="_compute_nilai_mk", store=True, digits=(16, 2))

    _uniq_mhs_mk_constraint = models.Constraint('unique(mahasiswa_id, mk_id)', 'Nilai MK exist.')

    # === UPDATE TRIGGER (PENTING: Agar Transkrip Realtime) ===
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
    @api.depends("mahasiswa_id.grade_cpmk_ids.nilai_cpmk")
    def _compute_nilai_mk(self):
        Rps = self.env["erpobe.akademik.rps"]
        BobotCpmkMk = self.env["erpobe.bobot.cpmk.mk"]
        GradeCpmk = self.env["erpobe.grade.cpmk"]

        # 1. Prepare Data
        mk_ids = self.mapped("mk_id")

        # Ambil RPS Terbaru (id desc) untuk MK terkait
        rps_records = Rps.search([("matakuliah_id", "in", mk_ids.ids)], order="id desc")

        # Map Bobot: {mk_id: {cpmk_id: bobot}}
        weight_map = {}
        # Filter bobot hanya dari RPS yang relevan (agar tidak duplikat jika ada banyak RPS)
        # Sederhananya, kita ambil semua, tapi jika duplikat, yang terakhir (terbaru) menang
        bobot_lines = BobotCpmkMk.search([("rps_id", "in", rps_records.ids)])

        for b in bobot_lines:
            mk = b.rps_id.matakuliah_id.id
            if mk not in weight_map:
                weight_map[mk] = {}
            weight_map[mk][b.cpmk_id.id] = b.bobot_cpmk_mk

        # 2. Get Nilai CPMK Mahasiswa
        mhs_ids = self.mapped("mahasiswa_id")
        cpmk_grades = GradeCpmk.search(
            [
                ("mahasiswa_id", "in", mhs_ids.ids),
                ("mk_id", "in", mk_ids.ids),
            ]
        )

        # Map: {mahasiswa_id: {cpmk_id: nilai}}
        grade_map = {}
        for g in cpmk_grades:
            if g.mahasiswa_id.id not in grade_map:
                grade_map[g.mahasiswa_id.id] = {}
            grade_map[g.mahasiswa_id.id][g.cpmk_id.id] = g.nilai_cpmk

        # 3. Calculate
        for rec in self:
            rec.nilai_mk = 0.0

            weights = weight_map.get(rec.mk_id.id, {})
            student_scores = grade_map.get(rec.mahasiswa_id.id, {})

            final_score = 0.0
            for cpmk_id, bobot in weights.items():
                s_cpmk = student_scores.get(cpmk_id, 0.0)
                final_score += s_cpmk * (bobot / 100.0)

            rec.nilai_mk = final_score


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
        "erpobe.master.fakultas", readonly=True, index=True
    )

    nilai_rata_mk = fields.Float(
        string="Rata-rata Nilai MK",
        readonly=True,
    )

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
                    AVG(gm.nilai_mk) AS nilai_rata_mk
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

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(f"""
            CREATE VIEW {self._table} AS (
                SELECT
                    MIN(gm.id) AS id,
                    r.angkatan AS angkatan,
                    gm.mk_id AS mk_id,
                    AVG(gm.nilai_mk) AS nilai_rata_mk
                FROM erpobe_grade_mk gm
                JOIN erpobe_master_mahasiswa m
                    ON m.id = gm.mahasiswa_id
                JOIN erpobe_master_rombel r
                    ON r.id = m.rombel_id
                GROUP BY r.angkatan, gm.mk_id
            )
        """)
