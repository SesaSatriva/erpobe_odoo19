from odoo import models, fields, api, Command, _
from odoo.fields import Domain
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class ErpObeInputNilai(models.Model):
    _name = "erpobe.input.nilai"
    _inherit = ["erpobe.audit.mixin"]
    _description = "Input Nilai Mata Kuliah"
    _rec_name = "penawaran_line_id"

    penawaran_id = fields.Many2one("erpobe.akademik.penawaran", required=True)
    penawaran_line_id = fields.Many2one(
        "erpobe.akademik.penawaran.line",
        required=True,
        domain="[('penawaran_id', '=', penawaran_id)]",
    )

    # Informasi UI
    tahun_ajaran = fields.Many2one(related="penawaran_id.tahun_ajaran", store=True)
    matakuliah_id = fields.Many2one(
        related="penawaran_line_id.matakuliah_id", store=True
    )

    grade_komponen_ids = fields.One2many(
        "erpobe.grade.komponen", "input_nilai_id", string="Daftar Nilai Mahasiswa"
    )

    _uniq_input_penawaran_constraint = models.Constraint('unique(penawaran_line_id)', 'Input nilai untuk kelas ini sudah ada.')

    prodi_id = fields.Many2one(
        related="penawaran_line_id.prodi_id", store=True, readonly=True, index=True
    )

    fakultas_id = fields.Many2one(
        related="prodi_id.fakultas_id", store=True, readonly=True, index=True
    )

    def action_generate_simulated_component_grades(self):
        defer_khs_refresh = self.env.context.get("defer_khs_refresh")
        GradeKomponen = self.env["erpobe.grade.komponen"].with_context(
            defer_academic_recompute=True,
            defer_khs_refresh=True,
        )
        students_to_refresh = set()
        for input_record in self:
            rps = input_record.penawaran_line_id.latest_rps_id
            if not rps:
                raise ValidationError(
                    _("RPS final untuk kelas ini belum tersedia.")
                )
            krs_lines = input_record.grade_komponen_ids.mapped("krs_line_id")
            if not krs_lines:
                krs_lines = self.env["erpobe.akademik.krs.line"].search([
                    ("penawaran_line_id", "=", input_record.penawaran_line_id.id)
                ])
            import random
            rng = random.SystemRandom()
            for student_index, krs in enumerate(krs_lines.sorted("id")):
                band = rng.choice((93, 82, 72, 61))
                for component_index, snapshot in enumerate(
                    rps.rps_komponen_ids.filtered("aktif").sorted("sequence")
                ):
                    if not snapshot.komponen_id:
                        continue
                    grade = self.env["erpobe.grade.komponen"].search([
                        ("krs_line_id", "=", krs.id),
                        ("rps_komponen_id", "=", snapshot.id),
                    ], limit=1)
                    if grade and grade.origin == "actual" and grade.is_graded:
                        continue
                    score = max(
                        0,
                        min(
                            100,
                            round(
                                band
                                + rng.randint(-12, 12)
                                + ((student_index + component_index) % 5),
                                2,
                            ),
                        ),
                    )
                    vals = {
                        "krs_line_id": krs.id,
                        "komponen_id": snapshot.komponen_id.id,
                        "rps_id": rps.id,
                        "rps_komponen_id": snapshot.id,
                        "nilai": score,
                        "origin": "simulated",
                        "is_graded": True,
                    }
                    if grade:
                        GradeKomponen.browse(grade.id).with_context(
                            skip_simulation_confirm=True
                        ).write(vals)
                    else:
                        vals["input_nilai_id"] = input_record.id
                        GradeKomponen.create(vals)
            students_to_refresh.update(krs_lines.mapped("mahasiswa_id").ids)
            input_record.with_context(defer_khs_refresh=True).action_calculate_grades_and_khs(
                krs_lines
            )
        if (
            students_to_refresh
            and not defer_khs_refresh
            and not self.env.context.get("skip_khs_refresh")
        ):
            self.env["erpobe.report.khs"].sudo().action_generate_khs(
                sorted(students_to_refresh)
            )
        return True

    def action_calculate_grades_and_khs(self, krs_lines=None):
        """
        Orchestrator: Memastikan record Grade tersedia & MEMAKSA hitung ulang (Recompute).
        """
        GradeCpmk = self.env["erpobe.grade.cpmk"].with_context(
            defer_khs_refresh=True
        )
        GradeMk = self.env["erpobe.grade.mk"].with_context(
            defer_khs_refresh=True
        )
        GradeCpl = self.env["erpobe.grade.cpl"]
        Rps = self.env["erpobe.akademik.rps"]

        # 1. Fallback Data KRS
        if not krs_lines:
            krs_lines = self.grade_komponen_ids.mapped("krs_line_id")

        if not krs_lines:
            raise ValidationError(
                _("Tidak ada data mahasiswa (KRS) di kelas ini untuk dihitung.")
            )

        # 2. Validasi RPS: gunakan RPS yang melekat pada kelas, bukan RPS terbaru lintas kelas.
        current_mk_id = self.penawaran_line_id.matakuliah_id.id
        rps = self.penawaran_line_id.latest_rps_id
        if rps and rps.status == "final":
            rps = rps
        else:
            rps = Rps.search(
                [
                    ("penawaran_line_id", "=", self.penawaran_line_id.id),
                    ("status", "=", "final"),
                ],
                order="version desc, id desc",
                limit=1,
            )

        if not rps:
            raise ValidationError(
                _(
                    "Gagal Menghitung Nilai: RPS (Rencana Pembelajaran Semester) untuk mata kuliah '%s' belum dibuat."
                )
                % self.penawaran_line_id.matakuliah_id.name
            )

        # 3. Preparasi Data
        mahasiswa_to_update = set()
        cpmk_list = rps.cpmk_ids
        relevant_cpls = cpmk_list.mapped("cpl_mapping_ids.cpl_id")

        # Container untuk record yang perlu di-recompute
        recompute_cpmk = self.env["erpobe.grade.cpmk"]
        recompute_mk = self.env["erpobe.grade.mk"]
        recompute_cpl = self.env["erpobe.grade.cpl"]

        # 4. Loop & Create/Collect Grade Records
        for krs in krs_lines:
            mahasiswa = krs.mahasiswa_id
            mahasiswa_to_update.add(mahasiswa.id)

            # a. Ensure Grade CPMK
            for cpmk in cpmk_list:
                g_cpmk = GradeCpmk.search(
                    [
                        ("mahasiswa_id", "=", mahasiswa.id),
                        ("cpmk_id", "=", cpmk.id),
                        ("krs_line_id", "=", krs.id),
                        ("rps_id", "=", rps.id),
                    ],
                    limit=1,
                )
                if not g_cpmk:
                    g_cpmk = GradeCpmk.create(
                        {
                            "mahasiswa_id": mahasiswa.id,
                            "cpmk_id": cpmk.id,
                            "krs_line_id": krs.id,
                            "rps_id": rps.id,
                        }
                    )
                elif (
                    g_cpmk.krs_line_id != krs
                    or g_cpmk.rps_id != rps
                ):
                    g_cpmk.write({"krs_line_id": krs.id, "rps_id": rps.id})
                recompute_cpmk += g_cpmk  # Kumpulkan record

            # b. Ensure Grade MK
            g_mk = GradeMk.search(
                [
                    ("mahasiswa_id", "=", mahasiswa.id),
                    ("mk_id", "=", current_mk_id),
                    ("krs_line_id", "=", krs.id),
                    ("rps_id", "=", rps.id),
                ],
                limit=1,
            )
            if not g_mk:
                g_mk = GradeMk.create(
                    {
                        "mahasiswa_id": mahasiswa.id,
                        "mk_id": current_mk_id,
                        "krs_line_id": krs.id,
                        "rps_id": rps.id,
                    }
                )
            elif g_mk.krs_line_id != krs or g_mk.rps_id != rps:
                g_mk.write({"krs_line_id": krs.id, "rps_id": rps.id})
            recompute_mk += g_mk  # Kumpulkan record

            # c. Ensure Grade CPL
            for cpl in relevant_cpls:
                g_cpl = GradeCpl.search([
                    ("mahasiswa_id", "=", mahasiswa.id),
                    ("cpl_id", "=", cpl.id),
                ], limit=1)
                if g_cpl:
                    recompute_cpl += g_cpl

        # === FORCE RECOMPUTE (SOLUSI UTAMA) ===
        # Memaksa Odoo menghitung ulang nilai berdasarkan input komponen terbaru
        _logger.info("Forcing recompute for Grades...")
        if recompute_cpmk:
            recompute_cpmk._compute_nilai_cpmk()
        if recompute_mk:
            recompute_mk._compute_nilai_mk()
        if recompute_cpl:
            recompute_cpl._compute_nilai_cpl()

        # 5. Trigger Update Report KHS
        if (
            mahasiswa_to_update
            and not self.env.context.get("skip_khs_refresh")
            and not self.env.context.get("defer_khs_refresh")
        ):
            mhs_ids_list = list(mahasiswa_to_update)
            if "erpobe.report.khs" in self.env:
                self.env["erpobe.report.khs"].sudo().action_generate_khs(mhs_ids_list)
            else:
                _logger.warning("Modul erpobe.report.khs belum terinstall.")

    def action_regenerate_dummy_grades(self):
        grades_to_recompute = self.env["erpobe.grade.komponen"]
        for input_record in self:
            rps = input_record.penawaran_line_id.latest_rps_id
            if not rps or rps.status != "final":
                raise ValidationError(
                    _("RPS final untuk kelas ini belum tersedia.")
                )
            grades = input_record.grade_komponen_ids.filtered(
                lambda grade: grade.origin == "simulated"
            )
            if not grades:
                return {
                    "type": "ir.actions.client",
                    "tag": "display_notification",
                    "params": {
                        "title": "Regenerasi Nilai Dummy",
                        "message": "Tidak ada nilai simulasi pada penawaran ini.",
                        "type": "warning",
                        "sticky": False,
                    },
                }
            import random
            rng = random.SystemRandom()
            for grade in grades.with_context(
                defer_academic_recompute=True,
                defer_khs_refresh=True,
            ):
                student_index = grade.mahasiswa_id.id
                course_index = grade.rps_id.matakuliah_id.id
                component_index = grade.komponen_id.id
                band = rng.choice((93, 82, 72, 61))
                score = max(
                    55,
                    min(
                        98,
                        round(
                            band
                            + rng.randint(-10, 10)
                            + ((student_index + course_index + component_index) % 5),
                            2,
                        ),
                    ),
                )
                grade.write({"nilai": score})
            grades_to_recompute |= self.env[
                "erpobe.grade.komponen"
            ].browse(grades.ids)
        if grades_to_recompute:
            grades_to_recompute._trigger_academic_recompute()
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Regenerasi Nilai Dummy",
                "message": "Nilai simulasi berhasil diacak ulang. Nilai aktual tetap aman.",
                "type": "success",
                "sticky": False,
            },
        }

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

    @api.onchange("penawaran_line_id")
    def _onchange_generate_students(self):
        """
        Smart Onchange:
        1. Ambil mahasiswa dari KRS.
        2. Cek apakah Nilai Komponen SUDAH ADA di database?
           - Jika YA: Tampilkan nilai lamanya (jangan di-nol-kan).
           - Jika TIDAK: Baru set 0.0.
        """
        if not self.penawaran_line_id:
            self.grade_komponen_ids = [Command.clear()]
            return

        rps = self.penawaran_line_id.latest_rps_id
        active_components = rps.rps_komponen_ids.filtered("aktif") if rps else self.env["erpobe.akademik.rps.komponen"]
        if not active_components:
            return

        KrsLine = self.env["erpobe.akademik.krs.line"]
        krs_lines = KrsLine.search(
            [("penawaran_line_id", "=", self.penawaran_line_id.id)]
        )

        # Load Model Grade Komponen untuk cek data lama
        GradeKomponen = self.env["erpobe.grade.komponen"]

        new_lines = [Command.clear()]
        for krs in krs_lines:
            for snapshot in active_components:
                comp = snapshot.komponen_id
                if not comp:
                    continue
                # Cek database: Apakah mahasiswa ini sudah punya nilai komponen ini?
                existing_grade = GradeKomponen.search(
                    [
                        ("krs_line_id", "=", krs.id),
                        ("komponen_id", "=", comp.id),
                        ("rps_id", "=", rps.id if rps else False),
                    ],
                    limit=1,
                )

                if existing_grade:
                    # KASUS 1: Data Lama Ada -> Load nilainya
                    # Kita tidak pakai Command.link() karena ini One2many dengan parent berbeda bisa tricky,
                    # tapi karena ini form input, kita tampilkan saja nilainya.
                    # Jika user save, dia akan update record tersebut atau membuat baru (tergantung constraint).
                    # Dengan struktur InputNilai yang 'unique per kelas', ini aman.
                    val_nilai = existing_grade.nilai
                    is_graded = existing_grade.is_graded
                else:
                    val_nilai = False
                    is_graded = False

                new_lines.append(
                    Command.create(
                        {
                            "krs_line_id": krs.id,
                            "komponen_id": comp.id,
                            "nilai": val_nilai,  # Gunakan nilai cerdas
                            "rps_id": rps.id if rps else False,
                            "rps_komponen_id": snapshot.id if snapshot else False,
                            "is_graded": is_graded,
                        }
                    )
                )

        self.grade_komponen_ids = new_lines

class ErpObeGradeKomponen(models.Model):
    _name = "erpobe.grade.komponen"
    _inherit = ["erpobe.audit.mixin"]
    _description = "Nilai Komponen Mahasiswa"

    # Header Info
    input_nilai_id = fields.Many2one("erpobe.input.nilai", ondelete="cascade")

    # Store True pada related fields penting untuk performa pencarian
    krs_line_id = fields.Many2one(
        "erpobe.akademik.krs.line", required=True, ondelete="restrict", index=True
    )
    mahasiswa_id = fields.Many2one(
        related="krs_line_id.mahasiswa_id", store=True, index=True
    )

    # Core Data
    komponen_id = fields.Many2one("erpobe.akademik.komponen", required=True, index=True)
    nilai = fields.Float(string="Nilai Angka", default=0.0, digits=(16, 2))
    rps_id = fields.Many2one(
        "erpobe.akademik.rps", string="RPS Penilaian", ondelete="restrict", index=True
    )
    rps_komponen_id = fields.Many2one(
        "erpobe.akademik.rps.komponen",
        string="Komponen RPS",
        ondelete="restrict",
        index=True,
    )
    origin = fields.Selection(
        [
            ("legacy", "Legacy"),
            ("actual", "Nilai Aktual"),
            ("simulated", "Nilai Simulasi"),
        ],
        default="actual",
        required=True,
        index=True,
    )
    is_graded = fields.Boolean(
        string="Sudah Dinilai", default=True, index=True
    )

    _uniq_nilai_komp_constraint = models.Constraint('unique(krs_line_id, komponen_id)', 'Nilai komponen duplikat untuk mahasiswa ini.')
    _nilai_range_constraint = models.Constraint(
        "CHECK(nilai >= 0 AND nilai <= 100)",
        "Nilai komponen harus berada pada rentang 0–100.",
    )

    prodi_id = fields.Many2one(
        related="mahasiswa_id.prodi_id", store=True, readonly=True, index=True
    )

    fakultas_id = fields.Many2one(
        related="prodi_id.fakultas_id", store=True, readonly=True, index=True
    )

    def _trigger_academic_recompute(self):
        cpmk_model = self.env["erpobe.grade.cpmk"].with_context(
            defer_khs_refresh=True
        )
        mk_model = self.env["erpobe.grade.mk"].with_context(
            defer_khs_refresh=True
        )
        cpl_model = self.env["erpobe.grade.cpl"].with_context(
            defer_khs_refresh=True
        )
        grade_keys = {
            (grade.mahasiswa_id.id, grade.krs_line_id.id, grade.rps_id.id)
            for grade in self
            if grade.krs_line_id and grade.rps_id
        }
        student_ids = {student_id for student_id, _krs_id, _rps_id in grade_keys}
        grade_domain = (
            Domain.OR([
                [
                    ("mahasiswa_id", "=", student_id),
                    ("krs_line_id", "=", krs_id),
                    ("rps_id", "=", rps_id),
                ]
                for student_id, krs_id, rps_id in sorted(grade_keys)
            ])
            if grade_keys
            else []
        )
        cpmk_records = (
            cpmk_model.search(grade_domain) if grade_keys else cpmk_model.browse()
        )
        mk_records = (
            mk_model.search(grade_domain) if grade_keys else mk_model.browse()
        )
        cpl_records = (
            cpl_model.search([("mahasiswa_id", "in", list(student_ids))])
            if student_ids
            else cpl_model.browse()
        )

        if cpmk_records:
            cpmk_records._compute_nilai_cpmk()
        if mk_records:
            mk_records._compute_nilai_mk()
        if cpl_records:
            cpl_records._compute_nilai_cpl()
        if (
            student_ids
            and not self.env.context.get("skip_khs_refresh")
            and not self.env.context.get("defer_khs_refresh")
        ):
            self.env["erpobe.report.khs"].sudo().action_generate_khs(
                list(student_ids)
            )

    def write(self, vals):
        if "nilai" in vals:
            Audit = self.env["erpobe.grade.komponen.audit"].sudo()
            for grade in self:
                old_value = grade.nilai
                new_value = float(vals["nilai"])
                if old_value != new_value:
                    Audit.create({
                        "grade_id": grade.id,
                        "krs_line_id": grade.krs_line_id.id,
                        "komponen_id": grade.komponen_id.id,
                        "mahasiswa_id": grade.mahasiswa_id.id,
                        "penawaran_line_id": grade.krs_line_id.penawaran_line_id.id,
                        "user_id": self.env.user.id,
                        "old_value": old_value,
                        "new_value": new_value,
                        "reason": vals.get("audit_reason", ""),
                    })
        vals.pop("audit_reason", None)
        result = super().write(vals)
        if (
            {"nilai", "is_graded", "rps_id", "rps_komponen_id", "krs_line_id"}
            & set(vals)
            and not self.env.context.get("defer_academic_recompute")
        ):
            self._trigger_academic_recompute()
        return result

    @api.model_create_multi
    def create(self, vals_list):
        vals_list = [dict(values) for values in vals_list]
        reasons = [values.pop("audit_reason", "") for values in vals_list]
        records = super().create(vals_list)
        Audit = self.env["erpobe.grade.komponen.audit"].sudo()
        for grade, reason in zip(records, reasons):
            if grade.nilai:
                Audit.create({
                    "grade_id": grade.id,
                    "krs_line_id": grade.krs_line_id.id,
                    "komponen_id": grade.komponen_id.id,
                    "mahasiswa_id": grade.mahasiswa_id.id,
                    "penawaran_line_id": grade.krs_line_id.penawaran_line_id.id,
                    "user_id": self.env.user.id,
                    "old_value": 0.0,
                    "new_value": grade.nilai,
                    "reason": reason or "Initial grade entry",
                })
        if not self.env.context.get("defer_academic_recompute"):
            records._trigger_academic_recompute()
        return records


class ErpObeGradeKomponenAudit(models.Model):
    _name = "erpobe.grade.komponen.audit"
    _description = "Riwayat Perubahan Nilai Komponen"
    _order = "create_date desc, id desc"

    grade_id = fields.Many2one(
        "erpobe.grade.komponen", required=True, ondelete="restrict", readonly=True
    )
    krs_line_id = fields.Many2one(
        "erpobe.akademik.krs.line", required=True, ondelete="restrict", readonly=True
    )
    penawaran_line_id = fields.Many2one(
        "erpobe.akademik.penawaran.line", required=True, ondelete="restrict", readonly=True
    )
    komponen_id = fields.Many2one(
        "erpobe.akademik.komponen", required=True, ondelete="restrict", readonly=True
    )
    mahasiswa_id = fields.Many2one(
        "erpobe.master.mahasiswa", required=True, ondelete="restrict", readonly=True
    )
    mahasiswa_name = fields.Char(related="mahasiswa_id.name", store=True, index=True)
    mahasiswa_nim = fields.Char(related="mahasiswa_id.nim", store=True, index=True)
    komponen_name = fields.Char(related="komponen_id.name", store=True, index=True)
    user_id = fields.Many2one("res.users", required=True, readonly=True)
    old_value = fields.Float(digits=(16, 2), readonly=True)
    new_value = fields.Float(digits=(16, 2), readonly=True)
    reason = fields.Char(readonly=True)

    def write(self, vals):
        raise ValidationError("Riwayat penilaian bersifat immutable.")

    def unlink(self):
        raise ValidationError("Riwayat penilaian tidak boleh dihapus.")

    def _unlink_fixture_generated_simulation(self):
        grades = self.mapped("grade_id")
        if any(
            grade.origin != "simulated"
            or grade.krs_line_id.matakuliah_id.identity_key
            or grade.krs_line_id.matakuliah_id.semester != 6
            for grade in grades
        ):
            raise ValidationError(
                "Hanya audit nilai simulasi awal untuk MK fixture semester 6 "
                "yang dapat dibersihkan."
            )

        course_ids = grades.mapped("krs_line_id.matakuliah_id").ids
        sources = self.env["erpobe.akademik.fixture.source"].sudo().search([
            ("record_model", "=", "erpobe.master.matakuliah"),
            ("record_id", "in", course_ids),
            ("source_type", "in", ("dummy", "mixed")),
        ])
        if set(sources.mapped("record_id")) != set(course_ids) or any(
            audit.reason != "Initial grade entry"
            or audit.old_value != 0
            or audit.new_value != audit.grade_id.nilai
            for audit in self
        ):
            raise ValidationError(
                "Riwayat nilai bukan nilai simulasi awal fixture; tidak dihapus."
            )
        return super().unlink()
