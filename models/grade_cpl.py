from odoo import models, fields, api, tools
from odoo.exceptions import ValidationError


class ErpObeGradeCpl(models.Model):
    _name = "erpobe.grade.cpl"
    _description = "Nilai CPL Mahasiswa"

    mahasiswa_id = fields.Many2one("erpobe.master.mahasiswa", required=True, index=True)
    cpl_id = fields.Many2one("erpobe.akademik.cpl", required=True, index=True)
    cpl_name = fields.Text(related="cpl_id.name", store=True, index=True)
    cpl_kode = fields.Char(related="cpl_id.kode_cpl", store=True, index=True)
    krs_line_id = fields.Many2one(
        "erpobe.akademik.krs.line",
        string="Attempt KRS",
        ondelete="restrict",
        index=True,
        help="Dibiarkan kosong karena grade CPL merupakan agregat lintas mata kuliah.",
    )
    rps_id = fields.Many2one(
        "erpobe.akademik.rps",
        string="RPS Digunakan",
        ondelete="restrict",
        index=True,
        help="Tidak digunakan sebagai identitas tunggal untuk nilai CPL agregat lintas mata kuliah.",
    )

    nilai_cpl = fields.Float(compute="_compute_nilai_cpl", store=True, digits=(16, 2))
    is_available = fields.Boolean(
        string="Data Tersedia", compute="_compute_nilai_cpl", store=True
    )
    target_nilai = fields.Float(
        related="cpl_id.target_nilai", store=True, readonly=True
    )
    status_capaian = fields.Selection(
        [
            ("belum_tersedia", "Belum Tersedia"),
            ("dalam_proses", "Dalam Proses"),
            ("tercapai", "Tercapai"),
            ("belum", "Belum Tercapai"),
        ],
        compute="_compute_status_capaian",
        store=True,
        string="Status Capaian",
    )

    _uniq_mhs_cpl_constraint = models.Constraint('unique(mahasiswa_id, cpl_id)', 'Nilai CPL exist.')

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

    @api.depends(
        "nilai_cpl",
        "target_nilai",
        "is_available",
        "cpl_id.cpmk_mapping_ids.cpmk_id",
        "mahasiswa_id",
        "mahasiswa_id.rombel_id",
        "krs_line_id.krs_id.state",
        "krs_line_id.matakuliah_id",
    )
    def _compute_status_capaian(self):
        unavailable = self.filtered(lambda record: not record.is_available)
        student_ids = unavailable.mapped("mahasiswa_id").ids
        cpls = unavailable.mapped("cpl_id")
        mappings = self.env["erpobe.akademik.cpl.mk.cpmk"].search([
            ("cpl_id", "in", cpls.ids),
        ])
        mapping_map = {}
        for mapping in mappings:
            mapping_map.setdefault(mapping.cpl_id.id, set()).add(
                mapping.cpmk_id.mk_id.id
            )

        all_course_ids = set().union(*mapping_map.values()) if mapping_map else set()
        enrolled = self.env["erpobe.akademik.krs.line"].search([
            ("mahasiswa_id", "in", student_ids),
            ("matakuliah_id", "in", list(all_course_ids)),
            ("krs_id.state", "=", "approved"),
        ])
        enrolled_pairs = {
            (line.mahasiswa_id.id, line.matakuliah_id.id) for line in enrolled
        }

        for record in self:
            if not record.is_available:
                contributing_course_ids = mapping_map.get(record.cpl_id.id, set())
                record.status_capaian = (
                    "dalam_proses"
                    if any(
                        (record.mahasiswa_id.id, course_id)
                        in enrolled_pairs
                        for course_id in contributing_course_ids
                    )
                    else "belum_tersedia"
                )
            elif record.nilai_cpl >= record.target_nilai:
                record.status_capaian = "tercapai"
            else:
                record.status_capaian = "belum"

    @api.depends(
        "mahasiswa_id.grade_cpmk_ids.cpmk_id",
        "mahasiswa_id.grade_cpmk_ids.nilai_cpmk",
        "mahasiswa_id.grade_cpmk_ids.is_available",
        "mahasiswa_id.grade_cpmk_ids.rps_id.status",
        "mahasiswa_id.grade_cpmk_ids.krs_line_id.krs_id.state",
        "mahasiswa_id.grade_cpmk_ids.rps_id.bobot_cpmk_mk_ids.cpmk_id",
        "mahasiswa_id.grade_cpmk_ids.rps_id.bobot_cpmk_mk_ids.bobot_cpmk_mk",
        "cpl_id.cpmk_mapping_ids.cpmk_id",
        "cpl_id.mk_mapping_ids.mk_id",
        "cpl_id.cpmk_mapping_ids",
        "cpl_id.mk_mapping_ids",
        "mahasiswa_id",
        "cpl_id",
    )
    def _compute_nilai_cpl(self):
        GradeCpmk = self.env["erpobe.grade.cpmk"]
        course_mappings = self.env["erpobe.akademik.mk.cpl"].search([
            ("cpl_id", "in", self.mapped("cpl_id").ids),
        ])
        mapped_courses_by_cpl = {}
        for mapping in course_mappings:
            mapped_courses_by_cpl.setdefault(mapping.cpl_id.id, set()).add(
                mapping.mk_id.id
            )

        cpmk_mappings = self.env["erpobe.akademik.cpl.mk.cpmk"].search([
            ("cpl_id", "in", self.mapped("cpl_id").ids),
        ])
        cpmk_ids = cpmk_mappings.mapped("cpmk_id").ids
        grade_cpmks = GradeCpmk.search([
            ("mahasiswa_id", "in", self.mapped("mahasiswa_id").ids),
            ("cpmk_id", "in", cpmk_ids),
            ("is_available", "=", True),
            ("rps_id.status", "=", "final"),
            ("krs_line_id.krs_id.state", "=", "approved"),
        ])
        grade_map = {}
        for grade in grade_cpmks:
            key = (grade.mahasiswa_id.id, grade.cpmk_id.id)
            current = grade_map.get(key)
            if (
                not current
                or grade.nilai_cpmk > current.nilai_cpmk
                or (
                    grade.nilai_cpmk == current.nilai_cpmk
                    and (
                        (grade.rps_id.id or 0, grade.krs_line_id.id or 0, grade.id)
                        > (current.rps_id.id or 0, current.krs_line_id.id or 0, current.id)
                    )
                )
            ):
                grade_map[key] = grade
        mappings_by_cpl = {}
        for mapping in cpmk_mappings:
            mappings_by_cpl.setdefault(mapping.cpl_id.id, []).append(mapping)

        for rec in self:
            weighted_total = 0.0
            denominator = 0.0
            mapped_course_ids = mapped_courses_by_cpl.get(rec.cpl_id.id, set())
            for mapping in mappings_by_cpl.get(rec.cpl_id.id, []):
                cpmk = mapping.cpmk_id
                if cpmk.prodi_id != rec.cpl_id.prodi_id:
                    continue
                if mapped_course_ids and cpmk.mk_id.id not in mapped_course_ids:
                    continue
                grade = grade_map.get((rec.mahasiswa_id.id, cpmk.id))
                if not grade:
                    continue
                weight = 0.0
                for weight_line in grade.rps_id.bobot_cpmk_mk_ids:
                    if weight_line.cpmk_id == cpmk:
                        weight = weight_line.bobot_cpmk_mk
                        break
                if weight <= 0:
                    continue
                weighted_total += grade.nilai_cpmk * weight
                denominator += weight
            rec.is_available = bool(denominator)
            rec.nilai_cpl = (
                max(0.0, min(100.0, weighted_total / denominator))
                if denominator else 0.0
            )

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
    jumlah_mahasiswa = fields.Integer(string="Jumlah Mahasiswa (N)", readonly=True)
    jumlah_nilai_tersedia = fields.Integer(string="Nilai Tersedia", readonly=True)
    jumlah_nilai_belum_tersedia = fields.Integer(string="Belum Memiliki Nilai", readonly=True)

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
                    AVG(gc.nilai_cpl) FILTER (WHERE gc.is_available IS TRUE) AS nilai_rata_cpl,
                    COUNT(DISTINCT gc.mahasiswa_id) AS jumlah_mahasiswa,
                    COUNT(DISTINCT gc.mahasiswa_id) FILTER (WHERE gc.is_available IS TRUE) AS jumlah_nilai_tersedia,
                    COUNT(DISTINCT gc.mahasiswa_id) FILTER (WHERE gc.is_available IS NOT TRUE) AS jumlah_nilai_belum_tersedia
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
    jumlah_mahasiswa = fields.Integer(string="Jumlah Mahasiswa (N)", readonly=True)
    jumlah_nilai_tersedia = fields.Integer(string="Nilai Tersedia", readonly=True)
    jumlah_nilai_belum_tersedia = fields.Integer(string="Belum Memiliki Nilai", readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        # Fix: Nama tabel diganti menjadi erpobe_grade_cpl
        self.env.cr.execute(f"""
            CREATE VIEW {self._table} AS (
                SELECT
                    MIN(gc.id) AS id,
                    r.angkatan,
                    m.prodi_id,
                    gc.cpl_id,
                    AVG(gc.nilai_cpl) FILTER (WHERE gc.is_available IS TRUE) AS nilai_rata_cpl,
                    COUNT(DISTINCT gc.mahasiswa_id) AS jumlah_mahasiswa,
                    COUNT(DISTINCT gc.mahasiswa_id) FILTER (WHERE gc.is_available IS TRUE) AS jumlah_nilai_tersedia,
                    COUNT(DISTINCT gc.mahasiswa_id) FILTER (WHERE gc.is_available IS NOT TRUE) AS jumlah_nilai_belum_tersedia
                FROM erpobe_grade_cpl gc
                JOIN erpobe_master_mahasiswa m ON m.id = gc.mahasiswa_id
                JOIN erpobe_master_rombel r ON r.id = m.rombel_id
                WHERE r.angkatan IS NOT NULL
                GROUP BY r.angkatan, m.prodi_id, gc.cpl_id
            )
        """)
