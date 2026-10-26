from odoo import models, fields, tools


class ErpObeSummaryAnalytics(models.AbstractModel):
    """
    Abstract Model untuk field standar agar tidak duplikasi kode.
    """

    _name = "erpobe.summary.analytics.mixin"
    _description = "Mixin Analisis OBE"
    _auto = False

    # Dimensions
    mahasiswa_id = fields.Many2one(
        "erpobe.master.mahasiswa", string="Mahasiswa", readonly=True
    )
    rombel_id = fields.Many2one("erpobe.master.rombel", string="Rombel", readonly=True)
    prodi_id = fields.Many2one(
        "erpobe.master.prodi", string="Program Studi", readonly=True, index=True
    )
    fakultas_id = fields.Many2one(
        "erpobe.master.fakultas", string="Fakultas", readonly=True, index=True
    )

    # PERBAIKAN: Tambahkan aggregator="max" agar tidak dijumlahkan (2023+2023)
    angkatan = fields.Integer(string="Angkatan", readonly=True, aggregator="max")


# -------------------------------------------------------------------------
# 1. ANALISIS MATA KULIAH (MK)
# -------------------------------------------------------------------------
class ErpObeSummaryMk(models.Model):
    _name = "erpobe.summary.mk"
    _description = "Analisis Performa Mata Kuliah"
    _inherit = "erpobe.summary.analytics.mixin"
    _auto = False
    _rec_name = "mk_id"

    mk_id = fields.Many2one(
        "erpobe.master.matakuliah", string="Mata Kuliah", readonly=True
    )
    semester_mk = fields.Integer(
        string="Semester MK", readonly=True, aggregator="max"
    )
    nilai_angka = fields.Float(
        string="Nilai Akhir", aggregator="avg", readonly=True
    )

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(
            """
            CREATE OR REPLACE VIEW %s AS (
                SELECT
                    g.id,
                    g.mahasiswa_id,
                    m.rombel_id,
                    m.prodi_id,
                    r.fakultas_id,
                    r.angkatan,
                    g.mk_id,
                    mk.semester AS semester_mk,
                    g.nilai_mk AS nilai_angka
                FROM erpobe_grade_mk g
                JOIN erpobe_master_mahasiswa m ON g.mahasiswa_id = m.id
                JOIN erpobe_master_rombel r ON m.rombel_id = r.id
                JOIN erpobe_master_matakuliah mk ON g.mk_id = mk.id
            )
        """
            % self._table
        )


class ErpObeSummaryCpmk(models.Model):
    _name = "erpobe.summary.cpmk"
    _description = "Analisis Ketercapaian CPMK"
    _inherit = "erpobe.summary.analytics.mixin"
    _auto = False
    _rec_name = "cpmk_id"

    mk_id = fields.Many2one(
        "erpobe.master.matakuliah", string="Mata Kuliah", readonly=True
    )
    cpmk_id = fields.Many2one("erpobe.akademik.cpmk", string="CPMK", readonly=True)
    nilai_cpmk = fields.Float(string="Skor CPMK", aggregator="avg", readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(
            """
            CREATE OR REPLACE VIEW %s AS (
                SELECT
                    g.id,
                    g.mahasiswa_id,
                    m.rombel_id,
                    m.prodi_id,
                    r.fakultas_id,
                    r.angkatan,
                    c.mk_id,
                    g.cpmk_id,
                    g.nilai_cpmk
                FROM erpobe_grade_cpmk g
                JOIN erpobe_master_mahasiswa m ON g.mahasiswa_id = m.id
                JOIN erpobe_master_rombel r ON m.rombel_id = r.id
                JOIN erpobe_akademik_cpmk c ON g.cpmk_id = c.id
            )
        """
            % self._table
        )


class ErpObeSummaryCpl(models.Model):
    _name = "erpobe.summary.cpl"
    _description = "Analisis Ketercapaian CPL"
    _inherit = "erpobe.summary.analytics.mixin"
    _auto = False
    _rec_name = "cpl_id"

    cpl_id = fields.Many2one("erpobe.akademik.cpl", string="CPL", readonly=True)
    nilai_cpl = fields.Float(string="Skor CPL", aggregator="avg", readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(
            """
            CREATE OR REPLACE VIEW %s AS (
                SELECT
                    g.id,
                    g.mahasiswa_id,
                    m.rombel_id,
                    m.prodi_id,
                    r.fakultas_id,
                    r.angkatan,
                    g.cpl_id,
                    g.nilai_cpl
                FROM erpobe_grade_cpl g
                JOIN erpobe_master_mahasiswa m ON g.mahasiswa_id = m.id
                JOIN erpobe_master_rombel r ON m.rombel_id = r.id
            )
        """
            % self._table
        )


# -------------------------------------------------------------------------
# 4. ANALISIS KOMPONEN
# -------------------------------------------------------------------------
class ErpObeSummaryKomponen(models.Model):
    _name = "erpobe.summary.komponen"
    _description = "Analisis Komponen Penilaian"
    _inherit = "erpobe.summary.analytics.mixin"
    _auto = False
    _rec_name = "komponen_id"

    mk_id = fields.Many2one(
        "erpobe.master.matakuliah", string="Mata Kuliah", readonly=True
    )
    komponen_id = fields.Many2one(
        "erpobe.akademik.komponen", string="Komponen", readonly=True
    )
    nilai_komponen = fields.Float(string="Nilai", aggregator="avg", readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(
            """
            CREATE OR REPLACE VIEW %s AS (
                SELECT
                    g.id,
                    m.id AS mahasiswa_id,
                    r.id AS rombel_id,
                    m.prodi_id,
                    r.fakultas_id,
                    r.angkatan,
                    krs.matakuliah_id AS mk_id,
                    g.komponen_id,
                    g.nilai AS nilai_komponen
                FROM erpobe_grade_komponen g
                JOIN erpobe_akademik_krs_line krs ON g.krs_line_id = krs.id
                JOIN erpobe_master_mahasiswa m ON krs.mahasiswa_id = m.id
                JOIN erpobe_master_rombel r ON m.rombel_id = r.id
            )
        """
            % self._table
        )
