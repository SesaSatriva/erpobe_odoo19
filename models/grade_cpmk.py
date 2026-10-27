from odoo import models, fields, api, tools
from odoo.exceptions import ValidationError


class ErpObeGradeCpmk(models.Model):
    _name = "erpobe.grade.cpmk"
    _description = "Nilai CPMK Mahasiswa"

    mahasiswa_id = fields.Many2one("erpobe.master.mahasiswa", required=True, index=True)
    cpmk_id = fields.Many2one("erpobe.akademik.cpmk", required=True, index=True)
    mk_id = fields.Many2one(related="cpmk_id.mk_id", store=True, string="Mata Kuliah")

    nilai_cpmk = fields.Float(
        compute="_compute_nilai_cpmk",
        store=True,
        digits=(16, 2),
        help="Dihitung dari rata-rata tertimbang Komponen terhadap CPMK berdasarkan RPS.",
    )

    _uniq_mhs_cpmk_constraint = models.Constraint('unique(mahasiswa_id, cpmk_id)', 'Grade CPMK exist.')

    prodi_id = fields.Many2one(
        related="mahasiswa_id.prodi_id", store=True, readonly=True, index=True
    )

    fakultas_id = fields.Many2one(
        related="prodi_id.fakultas_id", store=True, readonly=True, index=True
    )

    @api.depends(
        "mahasiswa_id.grade_komponen_ids.nilai",
        "mahasiswa_id.grade_komponen_ids.krs_line_id",
    )
    def _compute_nilai_cpmk(self):
        Rps = self.env["erpobe.akademik.rps"]
        BobotKomp = self.env["erpobe.bobot.komponen.cpmk"]
        GradeKomp = self.env["erpobe.grade.komponen"]

        mk_ids = self.mapped("cpmk_id.mk_id")

        # Ambil RPS Terbaru
        rps_records = Rps.search([("matakuliah_id", "in", mk_ids.ids)], order="id desc")

        weight_map = {}
        target_cpmk_ids = self.mapped("cpmk_id").ids

        bobot_lines = BobotKomp.search(
            [("rps_id", "in", rps_records.ids), ("cpmk_id", "in", target_cpmk_ids)]
        )

        for b in bobot_lines:
            if b.cpmk_id.id not in weight_map:
                weight_map[b.cpmk_id.id] = {}
            weight_map[b.cpmk_id.id][b.komponen_penilaian.id] = b.bobot_komponen_cpmk

        mhs_ids = self.mapped("mahasiswa_id")
        student_grades = GradeKomp.search(
            [
                ("mahasiswa_id", "in", mhs_ids.ids),
                ("krs_line_id.matakuliah_id", "in", mk_ids.ids),
            ]
        )

        grade_map = {}
        for g in student_grades:
            m_id = g.mahasiswa_id.id
            k_mk_id = g.krs_line_id.matakuliah_id.id
            if m_id not in grade_map:
                grade_map[m_id] = {}
            if k_mk_id not in grade_map[m_id]:
                grade_map[m_id][k_mk_id] = {}
            grade_map[m_id][k_mk_id][g.komponen_id.id] = g.nilai

        for rec in self:
            rec.nilai_cpmk = 0.0

            cpmk_weights = weight_map.get(rec.cpmk_id.id, {})
            if not cpmk_weights:
                continue

            student_mk_grades = grade_map.get(rec.mahasiswa_id.id, {}).get(
                rec.mk_id.id, {}
            )

            total_score = 0.0

            for komp_id, bobot in cpmk_weights.items():
                # Default nilai 0.0 jika mahasiswa belum dinilai komponen tersebut
                nilai_mhs = student_mk_grades.get(komp_id, 0.0)
                total_score += nilai_mhs * (bobot / 100.0)

            rec.nilai_cpmk = total_score

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
                WHERE m.rombel_id IS NOT NULL
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
                WHERE r.angkatan IS NOT NULL
                GROUP BY r.angkatan, gc.cpmk_id
            )
        """)
