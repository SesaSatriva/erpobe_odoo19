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
        "erpobe.akademik.krs.line", string="Attempt KRS", ondelete="restrict", index=True
    )
    rps_id = fields.Many2one(
        "erpobe.akademik.rps", string="RPS Digunakan", ondelete="restrict", index=True
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

    @api.depends(
        "nilai_cpl",
        "target_nilai",
        "is_available",
        "cpl_id.cpmk_mapping_ids.cpmk_id",
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
        "cpl_id.cpmk_mapping_ids.cpmk_id",
        "cpl_id.mk_mapping_ids.mk_id",
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
        ])
        grade_map = {
            (grade.mahasiswa_id.id, grade.cpmk_id.id): grade
            for grade in grade_cpmks
        }
        mappings_by_cpl = {}
        for mapping in cpmk_mappings:
            mappings_by_cpl.setdefault(mapping.cpl_id.id, []).append(mapping)

        for rec in self:
            total = 0.0
            count = 0
            mapped_course_ids = mapped_courses_by_cpl.get(rec.cpl_id.id)
            for mapping in mappings_by_cpl.get(rec.cpl_id.id, []):
                cpmk = mapping.cpmk_id
                if mapped_course_ids and cpmk.mk_id.id not in mapped_course_ids:
                    continue
                grade = grade_map.get((rec.mahasiswa_id.id, cpmk.id))
                if not grade:
                    continue
                total += grade.nilai_cpmk
                count += 1

            rec.is_available = bool(count)
            rec.nilai_cpl = total / count if count else 0.0

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
                WHERE gc.is_available IS TRUE
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
                WHERE gc.is_available IS TRUE
                GROUP BY r.angkatan, cpl.prodi_id, gc.cpl_id
            )
        """)
