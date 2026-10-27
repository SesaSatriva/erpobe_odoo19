from odoo import models, fields, api, tools
from odoo.exceptions import ValidationError


class ErpObeGradeCpl(models.Model):
    _name = "erpobe.grade.cpl"
    _description = "Nilai CPL Mahasiswa"

    mahasiswa_id = fields.Many2one("erpobe.master.mahasiswa", required=True, index=True)
    cpl_id = fields.Many2one("erpobe.akademik.cpl", required=True, index=True)

    nilai_cpl = fields.Float(compute="_compute_nilai_cpl", store=True, digits=(16, 2))

    _uniq_mhs_cpl_constraint = models.Constraint('unique(mahasiswa_id, cpl_id)', 'Nilai CPL exist.')

    prodi_id = fields.Many2one(
        related="mahasiswa_id.prodi_id", store=True, readonly=True, index=True
    )

    fakultas_id = fields.Many2one(
        related="prodi_id.fakultas_id", store=True, readonly=True, index=True
    )

    @api.depends("mahasiswa_id.grade_cpmk_ids.nilai_cpmk")
    def _compute_nilai_cpl(self):
        BobotCpmkCpl = self.env["erpobe.bobot.cpmk.cpl"]
        GradeCpmk = self.env["erpobe.grade.cpmk"]

        cpl_ids = self.mapped("cpl_id")
        
        # 1. Ambil Peta Bobot (Mapping CPL -> CPMK & Bobotnya)
        bobot_lines = BobotCpmkCpl.search([("cpl_id", "in", cpl_ids.ids)])

        weight_map = {}
        total_weight_per_cpl = {} # Simpan total bobot penuh per CPL
        relevant_cpmk_ids = set()

        for b in bobot_lines:
            cpl_id = b.cpl_id.id
            cpmk_id = b.cpmk_id.id
            bobot = b.bobot_cpmk_cpl

            if cpl_id not in weight_map:
                weight_map[cpl_id] = {}
                total_weight_per_cpl[cpl_id] = 0.0 # Init total bobot
            
            weight_map[cpl_id][cpmk_id] = bobot
            
            # FIX: Akumulasi total bobot di sini (Full Denominator)
            total_weight_per_cpl[cpl_id] += bobot
            
            relevant_cpmk_ids.add(cpmk_id)

        # 2. Ambil Nilai Mahasiswa yang Relevan
        mhs_ids = self.mapped("mahasiswa_id")
        cpmk_grades = GradeCpmk.search([
            ("mahasiswa_id", "in", mhs_ids.ids),
            ("cpmk_id", "in", list(relevant_cpmk_ids)),
        ])

        student_map = {}
        for g in cpmk_grades:
            mhs_id = g.mahasiswa_id.id
            if mhs_id not in student_map:
                student_map[mhs_id] = {}
            # Catatan: Jika ada duplikat nilai CPMK (mengulang), pastikan logic ambil yg terbaru/tertinggi
            # Kode ini mengambil record terakhir yang ditemukan (default Odoo order)
            student_map[mhs_id][g.cpmk_id.id] = g.nilai_cpmk

        # 3. Hitung Nilai CPL Tertimbang
        for rec in self:
            rec.nilai_cpl = 0.0

            cpl_weights = weight_map.get(rec.cpl_id.id, {})
            student_scores = student_map.get(rec.mahasiswa_id.id, {})
            
            # FIX: Ambil total bobot penuh dari mapping, bukan yang taken saja
            total_bobot_pembagi = total_weight_per_cpl.get(rec.cpl_id.id, 0.0)

            if not cpl_weights or total_bobot_pembagi == 0:
                continue

            total_score_tertimbang = 0.0

            for cpmk_id, bobot in cpl_weights.items():
                # Jika mahasiswa punya nilai, hitung. Jika tidak, anggap 0 (karena belum ambil/kosong)
                nilai = student_scores.get(cpmk_id, 0.0)
                total_score_tertimbang += (nilai * bobot)

            # Rumus: (Total Score * Bobot) / (Total Seluruh Bobot yang Ada)
            rec.nilai_cpl = total_score_tertimbang / total_bobot_pembagi

    @api.constrains("mahasiswa_id", "cpl_id")
    def _check_grade_faculty(self):
        for record in self:
            if record.cpl_id and (
                record.cpl_id.prodi_id != record.prodi_id
                or any(
                    mapping.prodi_id != record.prodi_id
                    for mapping in record.cpl_id.cpmk_mapping_ids
                )
            ):
                raise ValidationError(
                    "Nilai CPL dan mahasiswa harus berasal dari prodi yang sama."
                )



class ErpObeGradeCplRombel(models.Model):
    _name = "erpobe.grade.cpl.rombel"
    _description = "Agregasi Nilai CPL per Rombel"
    _auto = False

    rombel_id = fields.Many2one("erpobe.master.rombel", string="Rombel", readonly=True)
    prodi_id = fields.Many2one("erpobe.master.prodi", readonly=True, index=True)
    fakultas_id = fields.Many2one(
        related="prodi_id.fakultas_id", readonly=True, index=True
    )
    cpl_id = fields.Many2one("erpobe.akademik.cpl", string="CPL", readonly=True)
    nilai_rata_cpl = fields.Float(string="Rata-rata Nilai CPL", readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        # Fix: Nama tabel diganti menjadi erpobe_grade_cpl
        self.env.cr.execute(f"""
            CREATE VIEW {self._table} AS (
                SELECT
                    MIN(gc.id) AS id,
                    m.rombel_id,
                    m.prodi_id,
                    r.fakultas_id,
                    gc.cpl_id,
                    AVG(gc.nilai_cpl) AS nilai_rata_cpl
                FROM erpobe_grade_cpl gc
                JOIN erpobe_master_mahasiswa m ON m.id = gc.mahasiswa_id
                JOIN erpobe_master_rombel r ON r.id = m.rombel_id
                GROUP BY m.rombel_id, m.prodi_id, r.fakultas_id, gc.cpl_id
            )
        """)


class ErpObeGradeCplAngkatan(models.Model):
    _name = "erpobe.grade.cpl.angkatan"
    _description = "Agregasi Nilai CPL per Angkatan"
    _auto = False

    angkatan = fields.Integer(string="Angkatan", readonly=True)
    prodi_id = fields.Many2one("erpobe.master.prodi", readonly=True, index=True)
    fakultas_id = fields.Many2one(
        related="prodi_id.fakultas_id", readonly=True, index=True
    )
    cpl_id = fields.Many2one("erpobe.akademik.cpl", string="CPL", readonly=True)
    nilai_rata_cpl = fields.Float(string="Rata-rata Nilai CPL Angkatan", readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        # Fix: Nama tabel diganti menjadi erpobe_grade_cpl
        self.env.cr.execute(f"""
            CREATE VIEW {self._table} AS (
                SELECT
                    MIN(gc.id) AS id,
                    r.angkatan,
                    cpl.prodi_id,
                    gc.cpl_id,
                    AVG(gc.nilai_cpl) AS nilai_rata_cpl
                FROM erpobe_grade_cpl gc
                JOIN erpobe_master_mahasiswa m ON m.id = gc.mahasiswa_id
                JOIN erpobe_master_rombel r ON r.id = m.rombel_id
                JOIN erpobe_akademik_cpl cpl ON cpl.id = gc.cpl_id
                GROUP BY r.angkatan, cpl.prodi_id, gc.cpl_id
            )
        """)
