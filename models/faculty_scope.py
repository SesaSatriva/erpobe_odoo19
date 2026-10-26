from odoo import api, fields, models
from odoo.exceptions import AccessError, ValidationError


def _check_prodi_write_access(recordset, values):
    if not ({"prodi_id", "prodi_ids"} & values.keys()) or recordset.env.su:
        return
    user = recordset.env.user
    if user.has_group("erpobe.group_superadmin") or user.has_group(
        "base.group_system"
    ):
        return
    allowed_ids = set(user.erpobe_prodi_ids.ids)
    if "prodi_id" in values and values["prodi_id"] not in allowed_ids:
        raise AccessError("Anda tidak dapat memindahkan data ke prodi lain.")
    if "prodi_ids" in values:
        prodi_ids = set(recordset.mapped("prodi_ids").ids)
        for command in values["prodi_ids"]:
            operation = command[0]
            if operation == 6:
                prodi_ids = set(command[2])
            elif operation == 4:
                prodi_ids.add(command[1])
            elif operation == 3:
                prodi_ids.discard(command[1])
            elif operation == 5:
                prodi_ids.clear()
        if not prodi_ids <= allowed_ids:
            raise AccessError("Anda tidak dapat menetapkan dosen ke prodi lain.")


class ErpObeMasterDosenFaculty(models.Model):
    _inherit = "erpobe.master.dosen"

    prodi_ids = fields.Many2many(
        "erpobe.master.prodi",
        "erpobe_prodi_dosen_rel",
        "dosen_id",
        "prodi_id",
        string="Program Studi",
    )
    @api.constrains("prodi_ids")
    def _check_prodi_required(self):
        for record in self:
            if not record.prodi_ids:
                raise ValidationError("Dosen harus terdaftar pada minimal satu prodi.")
            faculties = record.prodi_ids.mapped("fakultas_id")
            dean_faculties = self.env["erpobe.master.fakultas"].sudo().search(
                [("dekan_id", "=", record.id)]
            )
            if any(faculty not in faculties for faculty in dean_faculties):
                raise ValidationError(
                    "Prodi dosen dekan harus berada di fakultas yang dipimpin."
                )
            courses = self.env["erpobe.master.matakuliah"].sudo().search(
                [
                    "|",
                    ("koordinator_id", "=", record.id),
                    ("tim_pengampu_ids", "in", record.id),
                ]
            )
            if any(course.prodi_id not in record.prodi_ids for course in courses):
                raise ValidationError(
                    "Dosen tidak dapat dilepas dari prodi mata kuliah yang diampu."
                )

    def write(self, vals):
        _check_prodi_write_access(self, vals)
        return super().write(vals)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        _check_prodi_write_access(
            records, {"prodi_ids": [(6, 0, records.mapped("prodi_ids").ids)]}
        )
        return records


class ErpObeMasterMahasiswaFaculty(models.Model):
    _inherit = "erpobe.master.mahasiswa"

    prodi_id = fields.Many2one(
        related="rombel_id.prodi_id", store=True, readonly=True, index=True
    )
    fakultas_id = fields.Many2one(
        related="prodi_id.fakultas_id", store=True, readonly=True, index=True
    )


class ErpObeMasterMatakuliahFaculty(models.Model):
    _inherit = "erpobe.master.matakuliah"

    prodi_id = fields.Many2one(
        "erpobe.master.prodi",
        required=True,
        ondelete="restrict",
        index=True,
    )
    fakultas_id = fields.Many2one(
        related="prodi_id.fakultas_id", store=True, readonly=True, index=True
    )

    def write(self, vals):
        _check_prodi_write_access(self, vals)
        return super().write(vals)


class ErpObeMasterRombelFaculty(models.Model):
    _inherit = "erpobe.master.rombel"

    prodi_id = fields.Many2one(
        "erpobe.master.prodi",
        required=True,
        ondelete="restrict",
        index=True,
    )
    fakultas_id = fields.Many2one(
        related="prodi_id.fakultas_id", store=True, readonly=True, index=True
    )

    def write(self, vals):
        _check_prodi_write_access(self, vals)
        return super().write(vals)


class ErpObeAkademikCpmkFaculty(models.Model):
    _inherit = "erpobe.akademik.cpmk"

    prodi_id = fields.Many2one(
        related="mk_id.prodi_id", store=True, readonly=True, index=True
    )
    fakultas_id = fields.Many2one(
        related="prodi_id.fakultas_id", store=True, readonly=True, index=True
    )


class ErpObeCplCpmkMappingFaculty(models.Model):
    _inherit = "erpobe.akademik.cpl.mk.cpmk"

    prodi_id = fields.Many2one(
        related="mk_id.prodi_id", store=True, readonly=True, index=True
    )
    fakultas_id = fields.Many2one(
        related="prodi_id.fakultas_id", store=True, readonly=True, index=True
    )

    @api.constrains("cpl_id", "cpmk_id")
    def _check_cpl_prodi(self):
        for record in self:
            if record.cpl_id.prodi_id != record.prodi_id:
                raise ValidationError("CPL dan CPMK harus berasal dari prodi yang sama.")


class ErpObeRpsFaculty(models.Model):
    _inherit = "erpobe.akademik.rps"

    prodi_id = fields.Many2one(
        related="matakuliah_id.prodi_id", store=True, readonly=True, index=True
    )
    fakultas_id = fields.Many2one(
        related="prodi_id.fakultas_id", store=True, readonly=True, index=True
    )


class ErpObeKrsFaculty(models.Model):
    _inherit = "erpobe.akademik.krs"

    prodi_id = fields.Many2one(
        related="mahasiswa_id.prodi_id", store=True, readonly=True, index=True
    )
    fakultas_id = fields.Many2one(
        related="prodi_id.fakultas_id", store=True, readonly=True, index=True
    )

    @api.constrains("mahasiswa_id", "penawaran_id")
    def _check_krs_faculty(self):
        for record in self:
            if not record.mahasiswa_id or not record.penawaran_id:
                continue
            rombels = record.penawaran_id.rombel_ids
            if (
                record.mahasiswa_id.rombel_id not in rombels
                or any(
                    rombel.prodi_id != record.prodi_id for rombel in rombels
                )
            ):
                raise ValidationError(
                    "Penawaran KRS harus mencakup rombel dan prodi mahasiswa."
                )


class ErpObeKrsLineFaculty(models.Model):
    _inherit = "erpobe.akademik.krs.line"

    prodi_id = fields.Many2one(
        related="mahasiswa_id.prodi_id", store=True, readonly=True, index=True
    )
    fakultas_id = fields.Many2one(
        related="prodi_id.fakultas_id", store=True, readonly=True, index=True
    )

    @api.constrains("krs_id", "penawaran_line_id")
    def _check_krs_line_faculty(self):
        for record in self:
            if (
                record.penawaran_line_id
                and record.penawaran_line_id.prodi_id != record.prodi_id
            ):
                raise ValidationError(
                    "Mata kuliah KRS dan mahasiswa harus berada di prodi yang sama."
                )


class ErpObePenawaranLineFaculty(models.Model):
    _inherit = "erpobe.akademik.penawaran.line"

    prodi_id = fields.Many2one(
        related="matakuliah_id.prodi_id", store=True, readonly=True, index=True
    )
    fakultas_id = fields.Many2one(
        related="prodi_id.fakultas_id", store=True, readonly=True, index=True
    )

    @api.constrains(
        "matakuliah_id", "rombel_ids", "dosen_id", "pengampu_ids", "mahasiswa_ids"
    )
    def _check_penawaran_faculty(self):
        for record in self:
            if any(
                rombel.prodi_id != record.prodi_id
                for rombel in record.rombel_ids
            ):
                raise ValidationError(
                    "Rombel penawaran harus berasal dari prodi mata kuliah."
                )
            dosen = record.pengampu_ids | record.dosen_id
            if any(
                record.prodi_id not in teacher.prodi_ids for teacher in dosen
            ):
                raise ValidationError(
                    "Dosen pengampu harus terdaftar pada prodi mata kuliah."
                )
            if any(
                student.prodi_id != record.prodi_id
                for student in record.mahasiswa_ids
            ):
                raise ValidationError(
                    "Mahasiswa penawaran harus berasal dari prodi mata kuliah."
                )


class ErpObeInputNilaiFaculty(models.Model):
    _inherit = "erpobe.input.nilai"

    prodi_id = fields.Many2one(
        related="penawaran_line_id.prodi_id", store=True, readonly=True, index=True
    )
    fakultas_id = fields.Many2one(
        related="prodi_id.fakultas_id", store=True, readonly=True, index=True
    )

    @api.constrains("penawaran_id", "penawaran_line_id")
    def _check_input_faculty(self):
        for record in self:
            if (
                record.penawaran_line_id
                and record.penawaran_line_id.penawaran_id != record.penawaran_id
            ):
                raise ValidationError(
                    "Baris nilai harus berasal dari penawaran yang dipilih."
                )


class ErpObeGradeKomponenFaculty(models.Model):
    _inherit = "erpobe.grade.komponen"

    prodi_id = fields.Many2one(
        related="mahasiswa_id.prodi_id", store=True, readonly=True, index=True
    )
    fakultas_id = fields.Many2one(
        related="prodi_id.fakultas_id", store=True, readonly=True, index=True
    )


class ErpObeGradeCpmkFaculty(models.Model):
    _inherit = "erpobe.grade.cpmk"

    prodi_id = fields.Many2one(
        related="mahasiswa_id.prodi_id", store=True, readonly=True, index=True
    )
    fakultas_id = fields.Many2one(
        related="prodi_id.fakultas_id", store=True, readonly=True, index=True
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


class ErpObeGradeCplFaculty(models.Model):
    _inherit = "erpobe.grade.cpl"

    prodi_id = fields.Many2one(
        related="mahasiswa_id.prodi_id", store=True, readonly=True, index=True
    )
    fakultas_id = fields.Many2one(
        related="prodi_id.fakultas_id", store=True, readonly=True, index=True
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


class ErpObeGradeMkFaculty(models.Model):
    _inherit = "erpobe.grade.mk"

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
                    "Nilai mata kuliah dan mahasiswa harus berada di fakultas yang sama."
                )


class ErpObeReportKhsFaculty(models.Model):
    _inherit = "erpobe.report.khs"

    prodi_id = fields.Many2one(
        related="mahasiswa_id.prodi_id", store=True, readonly=True, index=True
    )
    fakultas_id = fields.Many2one(
        related="prodi_id.fakultas_id", store=True, readonly=True, index=True
    )


class ErpObeReportKhsMkFaculty(models.Model):
    _inherit = "erpobe.report.khs.mk"

    prodi_id = fields.Many2one(
        related="khs_id.prodi_id", store=True, readonly=True, index=True
    )
    fakultas_id = fields.Many2one(
        related="prodi_id.fakultas_id", store=True, readonly=True, index=True
    )


class ErpObeReportKhsCpmkFaculty(models.Model):
    _inherit = "erpobe.report.khs.cpmk"

    prodi_id = fields.Many2one(
        related="khs_id.prodi_id", store=True, readonly=True, index=True
    )
    fakultas_id = fields.Many2one(
        related="prodi_id.fakultas_id", store=True, readonly=True, index=True
    )


class ErpObeReportKhsCplFaculty(models.Model):
    _inherit = "erpobe.report.khs.cpl"

    prodi_id = fields.Many2one(
        related="khs_id.prodi_id", store=True, readonly=True, index=True
    )
    fakultas_id = fields.Many2one(
        related="prodi_id.fakultas_id", store=True, readonly=True, index=True
    )


class ErpObeAkademikActivityFaculty(models.Model):
    _name = "erpobe.akademik.kegiatan.perkuliahan"
    _inherit = "erpobe.akademik.kegiatan.perkuliahan"

    prodi_id = fields.Many2one(
        related="rps_id.prodi_id", store=True, readonly=True, index=True
    )
    fakultas_id = fields.Many2one(
        related="prodi_id.fakultas_id", store=True, readonly=True, index=True
    )

    @api.constrains("rps_id", "cpmk_id")
    def _check_activity_faculty(self):
        for record in self:
            if record.cpmk_id.prodi_id != record.rps_id.prodi_id:
                raise ValidationError(
                    "CPMK kegiatan harus berasal dari prodi mata kuliah RPS."
                )


class ErpObeAkademikRubricFaculty(models.Model):
    _name = "erpobe.akademik.rubrik.penilaian"
    _inherit = "erpobe.akademik.rubrik.penilaian"

    prodi_id = fields.Many2one(
        related="rps_id.prodi_id", store=True, readonly=True, index=True
    )
    fakultas_id = fields.Many2one(
        related="prodi_id.fakultas_id", store=True, readonly=True, index=True
    )

    @api.constrains("rps_id", "cpmk_id")
    def _check_rubric_faculty(self):
        for record in self:
            if record.cpmk_id.prodi_id != record.rps_id.prodi_id:
                raise ValidationError(
                    "CPMK rubrik harus berasal dari prodi mata kuliah RPS."
                )


class ErpObeAkademikCriteriaFaculty(models.Model):
    _inherit = "erpobe.akademik.kriteria"

    prodi_id = fields.Many2one(
        related="rubrik_id.prodi_id", store=True, readonly=True, index=True
    )
    fakultas_id = fields.Many2one(
        related="prodi_id.fakultas_id", store=True, readonly=True, index=True
    )


class ErpObeBobotCpmkCplFaculty(models.Model):
    _name = "erpobe.bobot.cpmk.cpl"
    _inherit = "erpobe.bobot.cpmk.cpl"

    prodi_id = fields.Many2one(
        related="rps_id.prodi_id", store=True, readonly=True, index=True
    )
    fakultas_id = fields.Many2one(
        related="prodi_id.fakultas_id", store=True, readonly=True, index=True
    )

    @api.constrains("rps_id", "cpmk_id")
    def _check_cpmk_faculty(self):
        for record in self:
            if record.cpmk_id.prodi_id != record.rps_id.prodi_id:
                raise ValidationError(
                    "Bobot CPMK harus berada di prodi mata kuliah RPS."
                )


class ErpObeBobotCpmkMkFaculty(models.Model):
    _name = "erpobe.bobot.cpmk.mk"
    _inherit = "erpobe.bobot.cpmk.mk"

    prodi_id = fields.Many2one(
        related="rps_id.prodi_id", store=True, readonly=True, index=True
    )
    fakultas_id = fields.Many2one(
        related="prodi_id.fakultas_id", store=True, readonly=True, index=True
    )

    @api.constrains("rps_id", "cpmk_id")
    def _check_cpmk_faculty(self):
        for record in self:
            if record.cpmk_id.prodi_id != record.rps_id.prodi_id:
                raise ValidationError(
                    "Bobot CPMK harus berada di prodi mata kuliah RPS."
                )


class ErpObeBobotKomponenFaculty(models.Model):
    _name = "erpobe.bobot.komponen.cpmk"
    _inherit = "erpobe.bobot.komponen.cpmk"

    prodi_id = fields.Many2one(
        related="rps_id.prodi_id", store=True, readonly=True, index=True
    )
    fakultas_id = fields.Many2one(
        related="prodi_id.fakultas_id", store=True, readonly=True, index=True
    )

    @api.constrains("rps_id", "cpmk_id")
    def _check_cpmk_faculty(self):
        for record in self:
            if record.cpmk_id.prodi_id != record.rps_id.prodi_id:
                raise ValidationError(
                    "Bobot CPMK harus berada di prodi mata kuliah RPS."
                )


class ErpObeGradeCpmkAngkatanFaculty(models.Model):
    _inherit = "erpobe.cpmk.angkatan"

    prodi_id = fields.Many2one(
        related="cpmk_id.prodi_id", readonly=True, index=True
    )
    fakultas_id = fields.Many2one(
        related="prodi_id.fakultas_id", readonly=True, index=True
    )


class ErpObeGradeMkAngkatanFaculty(models.Model):
    _inherit = "erpobe.grade.mk.angkatan"

    prodi_id = fields.Many2one(
        related="mk_id.prodi_id", readonly=True, index=True
    )
    fakultas_id = fields.Many2one(
        related="prodi_id.fakultas_id", readonly=True, index=True
    )
