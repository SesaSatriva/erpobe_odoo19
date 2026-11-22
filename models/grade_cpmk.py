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

    _uniq_mhs_cpmk_attempt_constraint = models.Constraint(
        "unique(mahasiswa_id, cpmk_id, krs_line_id)",
        "Nilai CPMK untuk attempt KRS yang sama sudah ada.",
    )

    prodi_id = fields.Many2one(
        related="mahasiswa_id.prodi_id", store=True, readonly=True, index=True
    )

    fakultas_id = fields.Many2one(
        related="prodi_id.fakultas_id", store=True, readonly=True, index=True
    )

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._trigger_report_sync()
        return records

    def write(self, vals):
        result = super().write(vals)
        self._trigger_report_sync()
        return result

    def _trigger_report_sync(self):
        mhs_ids = self.mapped("mahasiswa_id.id")
        if mhs_ids and "erpobe.report.khs" in self.env:
            self.env["erpobe.report.khs"].sudo().action_generate_khs(mhs_ids)

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
        "rps_id.status",
        "krs_line_id.krs_id.state",
        "mahasiswa_id.grade_komponen_ids.nilai",
        "mahasiswa_id.grade_komponen_ids.krs_line_id",
        "mahasiswa_id.grade_komponen_ids.rps_komponen_id",
        "mahasiswa_id.grade_komponen_ids.is_graded",
        "mahasiswa_id.grade_komponen_ids.origin",
        "rps_id.rps_komponen_ids.bobot",
        "rps_id.bobot_komponen_cpmk_ids.bobot_komponen_cpmk",
        "rps_id.status",
        "krs_line_id.krs_id.state",
    )
    def _compute_nilai_cpmk(self):
        Rps = self.env["erpobe.akademik.rps"]
        BobotKomp = self.env["erpobe.bobot.komponen.cpmk"]
        GradeKomp = self.env["erpobe.grade.komponen"]

        for rec in self:
            rec.nilai_cpmk = 0.0
            rec.is_available = False

        exact_records = self.filtered(
            lambda grade:
                grade.rps_id
                and grade.rps_id.status == "final"
                and grade.krs_line_id
                and grade.krs_line_id.krs_id.state == "approved"
        )
        allocations = BobotKomp.search([
            ("rps_id", "in", exact_records.mapped("rps_id").ids),
            ("cpmk_id", "in", exact_records.mapped("cpmk_id").ids),
        ])
        allocation_map = {}
        for allocation in allocations:
            allocation_map.setdefault(
                (allocation.rps_id.id, allocation.cpmk_id.id), []
            ).append(allocation)

        resolved_snapshot_ids = set()
        for allocation in allocations:
            snapshot = allocation.rps_komponen_id
            if not snapshot and allocation.komponen_penilaian:
                snapshot = allocation.rps_id.rps_komponen_ids.filtered(
                    lambda line:
                        line.komponen_id == allocation.komponen_penilaian
                        and line.aktif
                )[:1]
            if snapshot:
                resolved_snapshot_ids.add(snapshot.id)

        grades = GradeKomp.search([
            ("krs_line_id", "in", exact_records.mapped("krs_line_id").ids),
            ("rps_id", "in", exact_records.mapped("rps_id").ids),
            ("rps_komponen_id", "in", list(resolved_snapshot_ids)),
            ("is_graded", "=", True),
        ])
        grade_map = {
            (grade.krs_line_id.id, grade.rps_id.id, grade.rps_komponen_id.id): grade
            for grade in grades
        }

        for rec in exact_records:
            if (
                rec.rps_id.status != "final"
                or rec.krs_line_id.krs_id.state != "approved"
            ):
                rec.is_available = False
                rec.nilai_cpmk = 0.0
                continue
            weighted_total = 0.0
            denominator = 0.0
            for allocation in allocation_map.get(
                (rec.rps_id.id, rec.cpmk_id.id), []
            ):
                snapshot = allocation.rps_komponen_id
                if not snapshot and allocation.komponen_penilaian:
                    snapshot = rec.rps_id.rps_komponen_ids.filtered(
                        lambda line:
                            line.komponen_id == allocation.komponen_penilaian
                            and line.aktif
                    )[:1]
                if not snapshot:
                    continue
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
        for rec in legacy_records:
            rec.nilai_cpmk = 0.0
            rec.is_available = False

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
    jumlah_mahasiswa = fields.Integer(string="Jumlah Mahasiswa (N)", readonly=True)
    jumlah_nilai_tersedia = fields.Integer(string="Nilai Tersedia", readonly=True)
    jumlah_nilai_belum_tersedia = fields.Integer(string="Belum Memiliki Nilai", readonly=True)

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
                    AVG(gc.nilai_cpmk) FILTER (WHERE gc.is_available IS TRUE) AS nilai_rata_cpmk,
                    COUNT(DISTINCT gc.mahasiswa_id) AS jumlah_mahasiswa,
                    COUNT(DISTINCT gc.mahasiswa_id) FILTER (WHERE gc.is_available IS TRUE) AS jumlah_nilai_tersedia,
                    COUNT(DISTINCT gc.mahasiswa_id) FILTER (WHERE gc.is_available IS NOT TRUE) AS jumlah_nilai_belum_tersedia
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
    jumlah_mahasiswa = fields.Integer(string="Jumlah Mahasiswa (N)", readonly=True)
    jumlah_nilai_tersedia = fields.Integer(string="Nilai Tersedia", readonly=True)
    jumlah_nilai_belum_tersedia = fields.Integer(string="Belum Memiliki Nilai", readonly=True)
    prodi_id = fields.Many2one("erpobe.master.prodi", readonly=True, index=True)

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
                    m.prodi_id          AS prodi_id,
                    gc.cpmk_id          AS cpmk_id,
                    AVG(gc.nilai_cpmk) FILTER (WHERE gc.is_available IS TRUE) AS nilai_rata_cpmk,
                    COUNT(DISTINCT gc.mahasiswa_id) AS jumlah_mahasiswa,
                    COUNT(DISTINCT gc.mahasiswa_id) FILTER (WHERE gc.is_available IS TRUE) AS jumlah_nilai_tersedia,
                    COUNT(DISTINCT gc.mahasiswa_id) FILTER (WHERE gc.is_available IS NOT TRUE) AS jumlah_nilai_belum_tersedia
                FROM erpobe_grade_cpmk gc
                JOIN erpobe_master_mahasiswa m ON m.id = gc.mahasiswa_id
                JOIN erpobe_master_rombel r ON r.id = m.rombel_id
                WHERE r.angkatan IS NOT NULL
                GROUP BY r.angkatan, m.prodi_id, gc.cpmk_id
            )
        """)
