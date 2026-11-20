from odoo import models, fields, api, tools
from odoo.exceptions import ValidationError


class ErpObeGradeCpmk(models.Model):
    _name = "erpobe.grade.cpmk"
    _description = "Nilai CPMK Mahasiswa"

    mahasiswa_id = fields.Many2one("erpobe.master.mahasiswa", required=True, index=True)
    cpmk_id = fields.Many2one("erpobe.akademik.cpmk", required=True, index=True)
    krs_line_id = fields.Many2one(
        "erpobe.akademik.krs.line", string="Attempt KRS", ondelete="restrict", index=True
    )
    rps_id = fields.Many2one(
        "erpobe.akademik.rps", string="RPS Digunakan", ondelete="restrict", index=True
    )
    mk_id = fields.Many2one(related="cpmk_id.mk_id", store=True, string="Mata Kuliah")

    nilai_cpmk = fields.Float(
        compute="_compute_nilai_cpmk",
        store=True,
        digits=(16, 2),
        help="Dihitung dari rata-rata tertimbang Komponen terhadap CPMK berdasarkan RPS.",
    )
    is_available = fields.Boolean(
        string="Data Tersedia",
        compute="_compute_nilai_cpmk",
        store=True,
    )
    target_nilai = fields.Float(
        related="cpmk_id.target_nilai", store=True, readonly=True
    )
    status_capaian = fields.Selection(
        [
            ("belum_tersedia", "Belum Tersedia"),
            ("tercapai", "Tercapai"),
            ("belum", "Belum Tercapai"),
        ],
        compute="_compute_status_capaian",
        store=True,
        string="Status Capaian",
    )

    _uniq_mhs_cpmk_constraint = models.Constraint('unique(mahasiswa_id, cpmk_id)', 'Grade CPMK exist.')

    prodi_id = fields.Many2one(
        related="mahasiswa_id.prodi_id", store=True, readonly=True, index=True
    )

    fakultas_id = fields.Many2one(
        related="prodi_id.fakultas_id", store=True, readonly=True, index=True
    )

    @api.depends("nilai_cpmk", "target_nilai", "is_available")
    def _compute_status_capaian(self):
        for record in self:
            if not record.is_available:
                record.status_capaian = "belum_tersedia"
            elif record.nilai_cpmk >= record.target_nilai:
                record.status_capaian = "tercapai"
            else:
                record.status_capaian = "belum"

    @api.depends(
        "mahasiswa_id.grade_komponen_ids.nilai",
        "mahasiswa_id.grade_komponen_ids.krs_line_id",
        "mahasiswa_id.grade_komponen_ids.rps_komponen_id",
        "mahasiswa_id.grade_komponen_ids.is_graded",
        "mahasiswa_id.grade_komponen_ids.origin",
        "rps_id.rps_komponen_ids.bobot",
        "rps_id.bobot_komponen_cpmk_ids.bobot_komponen_cpmk",
    )
    def _compute_nilai_cpmk(self):
        Rps = self.env["erpobe.akademik.rps"]
        BobotKomp = self.env["erpobe.bobot.komponen.cpmk"]
        GradeKomp = self.env["erpobe.grade.komponen"]

        exact_records = self.filtered(
            lambda grade: grade.rps_id and grade.krs_line_id
        )
        allocations = BobotKomp.search([
            ("rps_id", "in", exact_records.mapped("rps_id").ids),
            ("cpmk_id", "in", exact_records.mapped("cpmk_id").ids),
            ("rps_komponen_id", "!=", False),
        ])
        allocation_map = {}
        for allocation in allocations:
            allocation_map.setdefault(
                (allocation.rps_id.id, allocation.cpmk_id.id), []
            ).append(allocation)

        grades = GradeKomp.search([
            ("krs_line_id", "in", exact_records.mapped("krs_line_id").ids),
            ("rps_id", "in", exact_records.mapped("rps_id").ids),
            ("rps_komponen_id", "in", allocations.mapped("rps_komponen_id").ids),
            ("is_graded", "=", True),
        ])
        grade_map = {
            (grade.krs_line_id.id, grade.rps_id.id, grade.rps_komponen_id.id): grade
            for grade in grades
        }

        for rec in exact_records:
            weighted_total = 0.0
            denominator = 0.0
            for allocation in allocation_map.get(
                (rec.rps_id.id, rec.cpmk_id.id), []
            ):
                snapshot = allocation.rps_komponen_id
                if not snapshot.aktif:
                    continue
                grade = grade_map.get(
                    (rec.krs_line_id.id, rec.rps_id.id, snapshot.id)
                )
                if not grade:
                    continue
                attribution = snapshot.bobot * allocation.bobot_komponen_cpmk / 100.0
                weighted_total += grade.nilai * attribution
                denominator += attribution
            rec.is_available = bool(denominator)
            rec.nilai_cpmk = weighted_total / denominator if denominator else 0.0

        # Compatibility path for historical records that have no exact RPS/kRS lineage.
        legacy_records = self.filtered(lambda grade: not grade.rps_id or not grade.krs_line_id)
        if not legacy_records:
            return

        mk_ids = legacy_records.mapped("cpmk_id.mk_id")

        # Ambil RPS Terbaru
        rps_records = Rps.search([("matakuliah_id", "in", mk_ids.ids)], order="id desc")

        weight_map = {}
        target_cpmk_ids = legacy_records.mapped("cpmk_id").ids

        bobot_lines = BobotKomp.search(
            [("rps_id", "in", rps_records.ids), ("cpmk_id", "in", target_cpmk_ids)]
        )

        for b in bobot_lines:
            if b.cpmk_id.id not in weight_map:
                weight_map[b.cpmk_id.id] = {}
            weight_map[b.cpmk_id.id][b.komponen_penilaian.id] = b.bobot_komponen_cpmk

        mhs_ids = legacy_records.mapped("mahasiswa_id")
        student_grades = GradeKomp.search(
            [
                ("mahasiswa_id", "in", mhs_ids.ids),
                ("krs_line_id.matakuliah_id", "in", mk_ids.ids),
                ("is_graded", "=", True),
            ]
        )

        grade_map = {}
        for g in student_grades:
            m_id = g.mahasiswa_id.id
            k_mk_id = g.krs_line_id.matakuliah_id.id
            grade_map.setdefault((m_id, k_mk_id, g.komponen_id.id), g)

        for rec in legacy_records:
            rec.nilai_cpmk = 0.0
            rec.is_available = False

            cpmk_weights = weight_map.get(rec.cpmk_id.id, {})
            if not cpmk_weights:
                continue

            weighted_total = 0.0
            denominator = 0.0
            for komp_id, bobot in cpmk_weights.items():
                grade_record = grade_map.get(
                    (rec.mahasiswa_id.id, rec.mk_id.id, komp_id)
                )
                if not grade_record:
                    continue
                weighted_total += grade_record.nilai * (bobot / 100.0)
                denominator += bobot / 100.0
            rec.is_available = bool(denominator)
            rec.nilai_cpmk = (
                weighted_total / denominator if denominator else 0.0
            )

    @api.constrains("mahasiswa_id", "cpmk_id")
    def _check_grade_faculty(self):
        for record in self:
            if (
                record.mahasiswa_id
                and record.cpmk_id
                and record.mahasiswa_id.prodi_id != record.cpmk_id.prodi_id
            ):
                raise ValidationError(
                    "Nilai CPMK dan mahasiswa harus berada di fakultas yang sama."
                )



class ErpObeCpmkRombel(models.Model):
    _name = "erpobe.cpmk.rombel"
    _description = "Agregasi Nilai CPMK per Rombel"
    _auto = False

    rombel_id = fields.Many2one("erpobe.master.rombel", string="Rombel", readonly=True)
    prodi_id = fields.Many2one("erpobe.master.prodi", readonly=True, index=True)
    fakultas_id = fields.Many2one(
        related="prodi_id.fakultas_id", readonly=True, index=True
    )
    cpmk_id = fields.Many2one("erpobe.akademik.cpmk", string="CPMK", readonly=True)
    nilai_rata_cpmk = fields.Float(
        string="Rata-rata CPMK", readonly=True, digits=(16, 2)
    )

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(f"""
            CREATE OR REPLACE VIEW {self._table} AS (
                SELECT
                    ROW_NUMBER() OVER() AS id,
                    m.rombel_id         AS rombel_id,
                    m.prodi_id          AS prodi_id,
                    r.fakultas_id       AS fakultas_id,
                    gc.cpmk_id          AS cpmk_id,
                    AVG(gc.nilai_cpmk)  AS nilai_rata_cpmk
                FROM erpobe_grade_cpmk gc
                JOIN erpobe_master_mahasiswa m ON m.id = gc.mahasiswa_id
                JOIN erpobe_master_rombel r ON r.id = m.rombel_id
                WHERE m.rombel_id IS NOT NULL AND gc.is_available IS TRUE
                GROUP BY m.rombel_id, m.prodi_id, r.fakultas_id, gc.cpmk_id
            )
        """)


class ErpObeCpmkAngkatan(models.Model):
    _name = "erpobe.cpmk.angkatan"
    _description = "Agregasi Nilai CPMK per Angkatan"
    _auto = False

    angkatan = fields.Integer(string="Angkatan", readonly=True)
    cpmk_id = fields.Many2one("erpobe.akademik.cpmk", string="CPMK", readonly=True)
    nilai_rata_cpmk = fields.Float(
        string="Rata-rata CPMK Angkatan", readonly=True, digits=(16, 2)
    )

    prodi_id = fields.Many2one(
        related="cpmk_id.prodi_id", readonly=True, index=True
    )

    fakultas_id = fields.Many2one(
        related="prodi_id.fakultas_id", readonly=True, index=True
    )

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(f"""
            CREATE OR REPLACE VIEW {self._table} AS (
                SELECT
                    ROW_NUMBER() OVER() AS id,
                    r.angkatan          AS angkatan,
                    gc.cpmk_id          AS cpmk_id,
                    AVG(gc.nilai_cpmk)  AS nilai_rata_cpmk
                FROM erpobe_grade_cpmk gc
                JOIN erpobe_master_mahasiswa m ON m.id = gc.mahasiswa_id
                JOIN erpobe_master_rombel r ON r.id = m.rombel_id
                WHERE r.angkatan IS NOT NULL AND gc.is_available IS TRUE
                GROUP BY r.angkatan, gc.cpmk_id
            )
        """)
