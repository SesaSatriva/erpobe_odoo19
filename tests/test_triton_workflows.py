import re
import uuid
from unittest.mock import patch

from lxml import html
from odoo import Command
from odoo.exceptions import ValidationError
from odoo.tests import HttpCase, TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestTritonKrsWorkflows(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.suffix = uuid.uuid4().hex[:6].upper()
        cls.Faculty = cls.env["erpobe.master.fakultas"]
        cls.Prodi = cls.env["erpobe.master.prodi"]
        cls.Rombel = cls.env["erpobe.master.rombel"]
        cls.Course = cls.env["erpobe.master.matakuliah"]
        cls.Year = cls.env["erpobe.akademik.tahunajaran"]
        cls.Offer = cls.env["erpobe.akademik.penawaran"]
        cls.OfferLine = cls.env["erpobe.akademik.penawaran.line"]
        cls.Krs = cls.env["erpobe.akademik.krs"]
        cls.KrsLine = cls.env["erpobe.akademik.krs.line"]
        cls.GradeMk = cls.env["erpobe.grade.mk"]

        cls.faculty = cls.Faculty.create(
            {"name": f"Fakultas Triton KRS {cls.suffix}", "kode": f"TK{cls.suffix}"}
        )
        cls.prodi = cls.Prodi.create(
            {
                "name": f"Prodi Triton KRS {cls.suffix}",
                "kode": f"TP{cls.suffix}",
                "fakultas_id": cls.faculty.id,
            }
        )
        cls.rombel = cls.Rombel.create(
            {"name": "A", "angkatan": 2025, "prodi_id": cls.prodi.id}
        )
        cls.year = cls.Year.create(
            {
                "tahun_ajaran": f"2099/{cls.suffix}",
                "semester": "ganjil",
                "aktif": True,
            }
        )
        cls.offer = cls.Offer.create(
            {
                "tahun_ajaran": cls.year.id,
                "prodi_id": cls.prodi.id,
                "rombel_ids": [Command.link(cls.rombel.id)],
            }
        )
        cls.student = cls._create_student(
            "Mahasiswa KRS", f"NM{cls.suffix}", cls.rombel
        )
        cls.teacher = cls._create_teacher(
            "Dosen KRS", f"NP{cls.suffix}", cls.prodi
        )
        cls.student.write({"dosen_wali_id": cls.teacher.id})
        cls.course = cls._create_course(
            "Mata Kuliah KRS", f"MK{cls.suffix}", 3
        )
        cls.offer_line = cls._create_offer_line(
            cls.course, "senin", 8.0, 10.0
        )

    @classmethod
    def _create_student(cls, name, nim, rombel):
        partner = cls.env["res.partner"].create(
            {"name": name, "email": f"{nim.lower()}@example.test"}
        )
        return cls.env["erpobe.master.mahasiswa"].create(
            {"partner_id": partner.id, "nim": nim, "rombel_id": rombel.id}
        )

    @classmethod
    def _create_teacher(cls, name, nip, prodi):
        partner = cls.env["res.partner"].create(
            {"name": name, "email": f"{nip.lower()}@example.test"}
        )
        return cls.env["erpobe.master.dosen"].create(
            {
                "partner_id": partner.id,
                "nip": nip,
                "prodi_ids": [Command.link(prodi.id)],
            }
        )

    @classmethod
    def _create_course(cls, name, code, credits, prerequisites=None):
        return cls.Course.create(
            {
                "name": name,
                "kode_mk": code,
                "sks": credits,
                "semester": 1,
                "prodi_id": cls.prodi.id,
                "mk_prasyarat_ids": [Command.set((prerequisites or cls.Course).ids)],
            }
        )

    @classmethod
    def _create_offer_line(cls, course, day=None, start=0.0, end=0.0):
        return cls.OfferLine.create(
            {
                "penawaran_id": cls.offer.id,
                "matakuliah_id": course.id,
                "rombel_ids": [Command.link(cls.rombel.id)],
                "jadwal_hari": day,
                "jam_mulai": start,
                "jam_selesai": end,
            }
        )

    def _new_krs(self, student=None):
        return self.Krs.create(
            {
                "mahasiswa_id": (student or self.student).id,
                "penawaran_id": self.offer.id,
            }
        )

    def test_sks_limit_is_enforced(self):
        course = self._create_course("Mata Kuliah SKS", f"MS{self.suffix}", 25)
        offer_line = self._create_offer_line(course)
        krs = self._new_krs()
        with self.assertRaises(ValidationError):
            self.KrsLine.create(
                {"krs_id": krs.id, "penawaran_line_id": offer_line.id}
            )

    def test_bulk_krs_line_create_links_each_student_to_offer_line(self):
        second_student = self._create_student(
            "Mahasiswa Batch", f"NB{self.suffix}", self.rombel
        )
        first_krs = self._new_krs()
        second_krs = self._new_krs(second_student)

        report_model_class = type(self.env["erpobe.report.khs"])
        original_sync = report_model_class._sync_from_grades
        sync_batches = []

        def count_sync(reports):
            sync_batches.append(tuple(reports.mapped("mahasiswa_id").ids))
            return original_sync(reports)

        with patch.object(report_model_class, "_sync_from_grades", count_sync):
            self.KrsLine.create(
                [
                    {
                        "krs_id": first_krs.id,
                        "penawaran_line_id": self.offer_line.id,
                    },
                    {
                        "krs_id": second_krs.id,
                        "penawaran_line_id": self.offer_line.id,
                    },
                ]
            )

        self.assertEqual(len(sync_batches), 1)
        self.assertEqual(set(sync_batches[0]), {self.student.id, second_student.id})
        self.assertEqual(
            self.offer_line.mahasiswa_ids,
            self.student | second_student,
        )

    def test_bulk_krs_line_change_moves_students_between_offer_lines(self):
        second_student = self._create_student(
            "Mahasiswa Pindah Batch", f"NC{self.suffix}", self.rombel
        )
        first_krs = self._new_krs()
        second_krs = self._new_krs(second_student)
        lines = self.KrsLine.create(
            [
                {
                    "krs_id": first_krs.id,
                    "penawaran_line_id": self.offer_line.id,
                },
                {
                    "krs_id": second_krs.id,
                    "penawaran_line_id": self.offer_line.id,
                },
            ]
        )
        second_course = self._create_course(
            "Mata Kuliah Pindahan", f"MPD{self.suffix}", 3
        )
        second_offer_line = self._create_offer_line(second_course)

        report_model_class = type(self.env["erpobe.report.khs"])
        original_sync = report_model_class._sync_from_grades
        sync_batches = []

        def count_sync(reports):
            sync_batches.append(tuple(reports.mapped("mahasiswa_id").ids))
            return original_sync(reports)

        with patch.object(report_model_class, "_sync_from_grades", count_sync):
            lines.write({"penawaran_line_id": second_offer_line.id})

        self.assertEqual(len(sync_batches), 1)
        self.assertEqual(set(sync_batches[0]), {self.student.id, second_student.id})
        self.assertFalse(
            self.offer_line.mahasiswa_ids & (self.student | second_student)
        )
        self.assertEqual(
            second_offer_line.mahasiswa_ids,
            self.student | second_student,
        )

    def test_krs_line_reassignment_refreshes_previous_and_current_students(self):
        second_student = self._create_student(
            "Mahasiswa KRS Baru", f"NK{self.suffix}", self.rombel
        )
        first_krs = self._new_krs()
        second_krs = self._new_krs(second_student)
        line = self.KrsLine.create(
            {"krs_id": first_krs.id, "penawaran_line_id": self.offer_line.id}
        )

        report_model_class = type(self.env["erpobe.report.khs"])
        original_sync = report_model_class._sync_from_grades
        sync_batches = []

        def count_sync(reports):
            sync_batches.append(tuple(reports.mapped("mahasiswa_id").ids))
            return original_sync(reports)

        with patch.object(report_model_class, "_sync_from_grades", count_sync):
            line.write({"krs_id": second_krs.id})

        self.assertEqual(len(sync_batches), 1)
        self.assertEqual(set(sync_batches[0]), {self.student.id, second_student.id})
        self.assertEqual(line.mahasiswa_id, second_student)
        self.assertNotIn(self.student, self.offer_line.mahasiswa_ids)
        self.assertIn(second_student, self.offer_line.mahasiswa_ids)

    def test_krs_student_reassignment_refreshes_previous_and_current_students(self):
        second_student = self._create_student(
            "Mahasiswa Pemilik Baru", f"NO{self.suffix}", self.rombel
        )
        krs = self._new_krs()

        report_model_class = type(self.env["erpobe.report.khs"])
        original_sync = report_model_class._sync_from_grades
        sync_batches = []

        def count_sync(reports):
            sync_batches.append(tuple(reports.mapped("mahasiswa_id").ids))
            return original_sync(reports)

        with patch.object(report_model_class, "_sync_from_grades", count_sync):
            krs.write({"mahasiswa_id": second_student.id})

        self.assertEqual(len(sync_batches), 1)
        self.assertEqual(set(sync_batches[0]), {self.student.id, second_student.id})

    def test_schedule_conflict_is_rejected(self):
        other_course = self._create_course(
            "Mata Kuliah Bentrok", f"MB{self.suffix}", 2
        )
        other_line = self._create_offer_line(other_course, "senin", 9.0, 11.0)
        krs = self._new_krs()
        self.KrsLine.create(
            {"krs_id": krs.id, "penawaran_line_id": self.offer_line.id}
        )
        with self.assertRaises(ValidationError):
            self.KrsLine.create(
                {"krs_id": krs.id, "penawaran_line_id": other_line.id}
            )

    def test_unsatisfied_prerequisite_is_rejected(self):
        prerequisite = self._create_course("Prasyarat", f"MP{self.suffix}", 2)
        course = self._create_course(
            "Mata Kuliah Lanjutan",
            f"ML{self.suffix}",
            3,
            prerequisites=prerequisite,
        )
        offer_line = self._create_offer_line(course)
        krs = self._new_krs()
        with self.assertRaises(ValidationError):
            self.KrsLine.create(
                {"krs_id": krs.id, "penawaran_line_id": offer_line.id}
            )

    def test_advisor_approval_and_rejection_require_submission(self):
        krs = self._new_krs()
        self.KrsLine.create(
            {"krs_id": krs.id, "penawaran_line_id": self.offer_line.id}
        )
        krs.with_user(self.student.user_id).action_submit()
        self.assertEqual(krs.state, "submitted")
        krs.with_user(self.teacher.user_id).action_approve()
        self.assertEqual(krs.state, "approved")

        second_student = self._create_student(
            "Mahasiswa Kedua",             f"N2{self.suffix}", self.rombel
        )
        second_student.write({"dosen_wali_id": self.teacher.id})
        second_krs = self._new_krs(second_student)
        second_line = self._create_offer_line(
            self._create_course("MK Penolakan", f"MR{self.suffix}", 2)
        )
        self.KrsLine.create(
            {"krs_id": second_krs.id, "penawaran_line_id": second_line.id}
        )
        second_krs.with_user(second_student.user_id).action_submit()
        with self.assertRaises(ValidationError):
            second_krs.with_user(self.teacher.user_id).action_reject("")
        second_krs.with_user(self.teacher.user_id).action_reject("Jadwal perlu diperbaiki.")
        self.assertEqual(second_krs.state, "rejected")

    def test_students_cannot_read_other_students_krs(self):
        first_krs = self._new_krs()
        second_student = self._create_student(
            "Mahasiswa Ketiga",             f"N3{self.suffix}", self.rombel
        )
        second_krs = self._new_krs(second_student)
        first_krs_line = self.KrsLine.create(
            {"krs_id": first_krs.id, "penawaran_line_id": self.offer_line.id}
        )
        second_krs_line = self.KrsLine.create(
            {"krs_id": second_krs.id, "penawaran_line_id": self.offer_line.id}
        )
        component = self.env["erpobe.akademik.komponen"].create(
            {"name": f"Tugas privasi {self.suffix}", "tipe": "assignment"}
        )
        grade_component_model = self.env["erpobe.grade.komponen"]
        first_grade = grade_component_model.create(
            {"krs_line_id": first_krs_line.id, "komponen_id": component.id, "nilai": 81}
        )
        second_grade = grade_component_model.create(
            {"krs_line_id": second_krs_line.id, "komponen_id": component.id, "nilai": 73}
        )
        self.assertNotEqual(self.student.user_id, second_student.user_id)
        visible_ids = self.Krs.with_user(self.student.user_id).search(
            [("id", "in", [first_krs.id, second_krs.id])]
        ).ids
        self.assertIn(first_krs.id, visible_ids)
        self.assertNotIn(second_krs.id, visible_ids)

        report_model = self.env["erpobe.report.khs"]
        first_report = report_model.search(
            [("mahasiswa_id", "=", self.student.id)], limit=1
        ) or report_model.create({"mahasiswa_id": self.student.id})
        second_report = report_model.search(
            [("mahasiswa_id", "=", second_student.id)], limit=1
        ) or report_model.create({"mahasiswa_id": second_student.id})
        component_line_model = self.env["erpobe.report.khs.komponen"]
        component_line_model.create(
            [
                {"khs_id": first_report.id, "grade_id": first_grade.id},
                {"khs_id": second_report.id, "grade_id": second_grade.id},
            ]
        )
        visible_report_ids = report_model.with_user(self.student.user_id).search(
            [("id", "in", [first_report.id, second_report.id])]
        ).ids
        self.assertIn(first_report.id, visible_report_ids)
        self.assertNotIn(second_report.id, visible_report_ids)
        first_component_line = first_report.komponen_line_ids.filtered(
            lambda line: line.grade_id == first_grade
        )
        second_component_line = second_report.komponen_line_ids.filtered(
            lambda line: line.grade_id == second_grade
        )
        visible_component_line_ids = component_line_model.with_user(
            self.student.user_id
        ).search(
            [
                (
                    "id",
                    "in",
                    [first_component_line.id, second_component_line.id],
                )
            ]
        ).ids
        self.assertIn(first_component_line.id, visible_component_line_ids)
        self.assertNotIn(second_component_line.id, visible_component_line_ids)

    def test_prerequisite_passes_with_passing_grade(self):
        prerequisite = self._create_course(
            "Prasyarat Lulus", f"MP{self.suffix}L", 2
        )
        course = self._create_course(
            "Mata Kuliah Setelah Prasyarat",
            f"MA{self.suffix}",
            3,
            prerequisites=prerequisite,
        )
        offer_line = self._create_offer_line(course)
        self.GradeMk.create(
            {"mahasiswa_id": self.student.id, "mk_id": prerequisite.id}
        )
        self.env["ir.config_parameter"].sudo().set_param(
            "erpobe.krs.minimum_passing_score", "0"
        )
        krs = self._new_krs()
        line = self.KrsLine.create(
            {"krs_id": krs.id, "penawaran_line_id": offer_line.id}
        )
        self.assertTrue(line)

    def test_unavailable_grade_is_excluded_from_ipk_and_sks(self):
        report = self.env["erpobe.report.khs"].search(
            [("mahasiswa_id", "=", self.student.id)], limit=1
        ) or self.env["erpobe.report.khs"].create(
            {"mahasiswa_id": self.student.id}
        )
        unavailable_grade = self.GradeMk.create(
            {
                "mahasiswa_id": self.student.id,
                "mk_id": self.course.id,
            }
        )
        unavailable_grade.invalidate_recordset(["nilai_mk", "is_available"])
        unavailable_grade._compute_nilai_mk()
        report._sync_from_grades()

        line = report.mk_line_ids.filtered(
            lambda record: record.mk_id == self.course
        )
        self.assertEqual(len(line), 1)
        self.assertFalse(line.data_available)
        self.assertEqual(line.nilai_tampil, "Belum tersedia")
        self.assertEqual(report.ipk, 0.0)
        self.assertEqual(report.total_sks_lulus, 0)

    def test_khs_generation_batches_students_in_one_sync(self):
        second_student = self._create_student(
            "Mahasiswa Batch", f"NB{self.suffix}", self.rombel
        )
        report_model = self.env["erpobe.report.khs"]
        report_model_class = type(report_model)
        original_sync = report_model_class._sync_from_grades
        sync_batches = []

        def count_sync(reports):
            sync_batches.append(tuple(reports.mapped("mahasiswa_id").ids))
            return original_sync(reports)

        with patch.object(report_model_class, "_sync_from_grades", count_sync):
            report_model.action_generate_khs(
                [self.student.id, second_student.id, self.student.id]
            )

        self.assertEqual(len(sync_batches), 1)
        self.assertEqual(set(sync_batches[0]), {self.student.id, second_student.id})

    def test_cpl_and_ipk_are_calculated_from_weighted_grade_data(self):
        cpl = self.env["erpobe.akademik.cpl"].create(
            {
                "name": "Capaian pembelajaran KRS",
                "kode_cpl": f"CPL{self.suffix}",
                "jenis_cpl": "pengetahuan",
                "prodi_id": self.prodi.id,
            }
        )
        cpmk = self.env["erpobe.akademik.cpmk"].create(
            {
                "mk_id": self.course.id,
                "kode_cpmk": f"CP{self.suffix}",
                "name": "CPMK KRS",
            }
        )
        self.env["erpobe.akademik.cpl.mk.cpmk"].create(
            {"cpl_id": cpl.id, "cpmk_id": cpmk.id}
        )
        self.assertEqual(cpmk.display_name, f"{cpmk.kode_cpmk}: {cpmk.name}")
        self.assertEqual(cpl.display_name, f"{cpl.kode_cpl}: {cpl.name}")
        self.env["erpobe.akademik.mk.cpl"].create(
            {"mk_id": self.course.id, "cpl_id": cpl.id}
        )
        component = self.env["erpobe.akademik.komponen"].create(
            {"name": f"Komponen {self.suffix}", "tipe": "assignment"}
        )
        rps = self.env["erpobe.akademik.rps"].create(
            {
                "matakuliah_id": self.course.id,
                "penawaran_line_id": self.offer_line.id,
                "komponen_ids": [Command.link(component.id)],
            }
        )
        rps.rps_komponen_ids.write({"bobot": 100.0})
        rps.bobot_cpmk_mk_ids.write({"bobot_cpmk_mk": 100.0})
        rps.bobot_komponen_cpmk_ids.write({"bobot_komponen_cpmk": 100.0})
        rps.action_mark_for_review()
        rps.action_finalize()

        krs = self._new_krs()
        krs_line = self.KrsLine.create(
            {"krs_id": krs.id, "penawaran_line_id": self.offer_line.id}
        )
        krs.write({"state": "approved"})
        grade_component = self.env["erpobe.grade.komponen"].create(
            {
                "krs_line_id": krs_line.id,
                "komponen_id": component.id,
                "rps_id": rps.id,
                "rps_komponen_id": rps.rps_komponen_ids[:1].id,
                "nilai": 80.0,
                "audit_reason": "Initial assessment",
            }
        )
        audit_model = self.env["erpobe.grade.komponen.audit"].sudo()
        self.assertEqual(
            audit_model.search([("grade_id", "=", grade_component.id)], limit=1).reason,
            "Initial assessment",
        )
        grade_cpmk = self.env["erpobe.grade.cpmk"].create(
            {
                "mahasiswa_id": self.student.id,
                "cpmk_id": cpmk.id,
                "krs_line_id": krs_line.id,
                "rps_id": rps.id,
            }
        )
        grade_cpl = self.env["erpobe.grade.cpl"].create(
            {"mahasiswa_id": self.student.id, "cpl_id": cpl.id}
        )
        grade_mk = self.GradeMk.create(
            {
                "mahasiswa_id": self.student.id,
                "mk_id": self.course.id,
                "krs_line_id": krs_line.id,
                "rps_id": rps.id,
            }
        )
        ungraded_component = self.env["erpobe.akademik.komponen"].create(
            {"name": f"Kuis belum dinilai {self.suffix}", "tipe": "quiz"}
        )
        self.env["erpobe.grade.komponen"].create(
            {
                "krs_line_id": krs_line.id,
                "komponen_id": ungraded_component.id,
                "is_graded": False,
            }
        )
        self.assertEqual(grade_cpmk.nilai_cpmk, 80.0)
        self.assertEqual(grade_cpl.nilai_cpl, 80.0)
        self.assertEqual(grade_mk.nilai_mk, 80.0)
        report_before_change = self.env["erpobe.report.khs"].search(
            [("mahasiswa_id", "=", self.student.id)], limit=1
        )
        self.assertTrue(report_before_change)
        initial_line_ids = {
            "mk": set(report_before_change.mk_line_ids.ids),
            "cpmk": set(report_before_change.cpmk_line_ids.ids),
            "cpl": set(report_before_change.cpl_line_ids.ids),
            "komponen": set(report_before_change.komponen_line_ids.ids),
        }
        report_model_class = type(self.env["erpobe.report.khs"])
        original_sync = report_model_class._sync_from_grades
        sync_batches = []

        def count_sync(reports):
            sync_batches.append(tuple(reports.mapped("mahasiswa_id").ids))
            return original_sync(reports)

        with patch.object(report_model_class, "_sync_from_grades", count_sync):
            grade_component.write(
                {"nilai": 75.0, "audit_reason": "Verified correction"}
            )
        self.assertEqual(len(sync_batches), 1)
        self.assertEqual(grade_cpmk.nilai_cpmk, 75.0)
        self.assertEqual(grade_cpl.nilai_cpl, 75.0)
        self.assertEqual(grade_mk.nilai_mk, 75.0)
        report_before_change.invalidate_recordset()
        self.assertEqual(set(report_before_change.mk_line_ids.ids), initial_line_ids["mk"])
        self.assertEqual(
            set(report_before_change.cpmk_line_ids.ids), initial_line_ids["cpmk"]
        )
        self.assertEqual(
            set(report_before_change.cpl_line_ids.ids), initial_line_ids["cpl"]
        )
        self.assertEqual(
            set(report_before_change.komponen_line_ids.ids),
            initial_line_ids["komponen"],
        )
        correction = audit_model.search(
            [("grade_id", "=", grade_component.id)],
            order="create_date desc, id desc",
            limit=1,
        )
        self.assertEqual(correction.old_value, 80.0)
        self.assertEqual(correction.new_value, 75.0)
        self.assertEqual(correction.reason, "Verified correction")

        report = self.env["erpobe.report.khs"].search(
            [("mahasiswa_id", "=", self.student.id)], limit=1
        ) or self.env["erpobe.report.khs"].create(
            {"mahasiswa_id": self.student.id}
        )
        report_line = report.mk_line_ids.filtered(
            lambda record: record.mk_id == self.course
        )
        self.assertEqual(len(report_line), 1)
        self.assertEqual(report.total_sks_lulus, self.course.sks)
        self.assertEqual(report.ipk, report_line.bobot)
        component_line = report.komponen_line_ids.filtered(
            lambda record: record.grade_id == grade_component
        )
        self.assertEqual(len(component_line), 1)
        self.assertEqual(component_line.mk_id, self.course)
        self.assertEqual(component_line.komponen_id, component)
        self.assertEqual(component_line.tipe, "assignment")
        self.assertEqual(component_line.nilai_angka, 75.0)
        self.assertEqual(len(report.komponen_line_ids), 1)

        line_ids = {
            "mk": set(report.mk_line_ids.ids),
            "cpmk": set(report.cpmk_line_ids.ids),
            "cpl": set(report.cpl_line_ids.ids),
            "komponen": set(report.komponen_line_ids.ids),
        }
        report._sync_from_grades()
        report._sync_from_grades()
        self.assertEqual(set(report.mk_line_ids.ids), line_ids["mk"])
        self.assertEqual(set(report.cpmk_line_ids.ids), line_ids["cpmk"])
        self.assertEqual(set(report.cpl_line_ids.ids), line_ids["cpl"])
        self.assertEqual(set(report.komponen_line_ids.ids), line_ids["komponen"])
        self.assertEqual(component_line.exists().nilai_angka, 75.0)


@tagged("post_install", "-at_install")
class TestTritonPublicRoutes(HttpCase):
    def test_student_cpl_detail_renders_notebook_and_enforces_ownership(self):
        suffix = uuid.uuid4().hex[:8].upper()
        faculty = self.env["erpobe.master.fakultas"].sudo().create(
            {"name": f"CPL Portal Faculty {suffix}", "kode": f"CPF{suffix}"}
        )
        prodi = self.env["erpobe.master.prodi"].sudo().create(
            {
                "name": f"CPL Portal Program {suffix}",
                "kode": f"CPP{suffix}",
                "fakultas_id": faculty.id,
            }
        )
        rombel = self.env["erpobe.master.rombel"].sudo().create(
            {"name": f"Portal {suffix}", "angkatan": 2025, "prodi_id": prodi.id}
        )
        nim = f"CPL{suffix}"
        partner = self.env["res.partner"].sudo().create(
            {
                "name": f"Mahasiswa CPL {suffix}",
                "email": f"{nim.lower()}@example.test",
            }
        )
        student = self.env["erpobe.master.mahasiswa"].sudo().create(
            {
                "partner_id": partner.id,
                "nim": nim,
                "rombel_id": rombel.id,
            }
        )
        course = self.env["erpobe.master.matakuliah"].sudo().create(
            {
                "name": f"Mata Kuliah CPL {suffix}",
                "kode_mk": f"MKCPL{suffix}",
                "sks": 3,
                "semester": 1,
                "prodi_id": prodi.id,
            }
        )
        cpl = self.env["erpobe.akademik.cpl"].sudo().create(
            {
                "name": f"Capaian uji portal {suffix}",
                "kode_cpl": f"TEST-CPL-{suffix}",
                "prodi_id": prodi.id,
            }
        )
        cpmks = self.env["erpobe.akademik.cpmk"].sudo().create(
            [
                {
                    "mk_id": course.id,
                    "kode_cpmk": f"CPL{suffix}-01",
                    "name": f"CPMK pertama {suffix}",
                },
                {
                    "mk_id": course.id,
                    "kode_cpmk": f"CPL{suffix}-02",
                    "name": f"CPMK kedua {suffix}",
                },
            ]
        )
        self.env["erpobe.akademik.cpl.mk.cpmk"].sudo().create(
            [
                {"cpl_id": cpl.id, "cpmk_id": cpmk.id}
                for cpmk in cpmks
            ]
        )
        self.env["erpobe.akademik.mk.cpl"].sudo().create(
            {"mk_id": course.id, "cpl_id": cpl.id}
        )
        self.env["erpobe.grade.cpl"].sudo().create(
            {"mahasiswa_id": student.id, "cpl_id": cpl.id}
        )

        self.authenticate(student.user_id.login, student.nim)
        list_response = self.url_open("/my/capaian-cpl")
        self.assertEqual(list_response.status_code, 200)
        self.assertIn(cpl.kode_cpl, list_response.text)
        self.assertNotIn("CPMK Kontributor", list_response.text)
        filtered_response = self.url_open(
            "/my/capaian-cpl?jenis=lainnya&status=belum_tersedia"
        )
        self.assertEqual(filtered_response.status_code, 200)
        self.assertIn(cpl.kode_cpl, filtered_response.text)
        filtered_html = html.fromstring(filtered_response.text)
        for filter_name in ("jenis", "status"):
            self.assertEqual(
                len(
                    filtered_html.xpath(
                        f"//form[contains(@class, 'o_triton_list-toolbar')]"
                        f"//select[@name='{filter_name}']"
                    )
                ),
                1,
            )
            self.assertFalse(
                filtered_html.xpath(
                    f"//form[contains(@class, 'o_triton_list-toolbar')]"
                    f"//input[@type='hidden' and @name='{filter_name}']"
                )
            )
        excluded_response = self.url_open("/my/capaian-cpl?jenis=sikap")
        self.assertEqual(excluded_response.status_code, 200)
        self.assertNotIn(cpl.kode_cpl, excluded_response.text)

        detail_response = self.url_open(f"/my/capaian-cpl/{cpl.id}")
        self.assertEqual(detail_response.status_code, 200)
        for label in (
            "Ringkasan",
            "CPMK Kontributor",
            "Mata Kuliah Kontributor",
            "Detail Perhitungan",
        ):
            self.assertIn(label, detail_response.text)
        detail_html = html.fromstring(detail_response.text)
        self.assertEqual(
            len(detail_html.xpath("//section[@id='cpl-cpmk']//tbody/tr")),
            2,
        )
        self.assertEqual(
            len(detail_html.xpath("//section[@id='cpl-courses']//tbody/tr")),
            1,
        )

        unowned_cpl = self.env["erpobe.akademik.cpl"].sudo().create(
            {
                "name": f"Capaian privat uji {suffix}",
                "kode_cpl": f"PRIVATE-CPL-{suffix}",
                "prodi_id": student.prodi_id.id,
            }
        )
        unowned_response = self.url_open(
            f"/my/capaian-cpl/{unowned_cpl.id}",
            allow_redirects=False,
        )
        self.assertEqual(unowned_response.status_code, 403)

    def test_program_detail_data_tabs_render_with_website_layout(self):
        prodi = self.env["erpobe.master.prodi"].search(
            [("active", "=", True)],
            order="id",
            limit=1,
        )
        self.assertTrue(prodi, "The academic fixture should provide a public program")

        for tab in ("cpl", "mata-kuliah"):
            with self.subTest(tab=tab):
                response = self.url_open(
                    f"/prodi/{prodi.id}?tab={tab}"
                )
                self.assertEqual(response.status_code, 200, tab)

        sorted_courses = self.url_open(
            f"/prodi/{prodi.id}?tab=mata-kuliah&sort=course"
        )
        self.assertEqual(sorted_courses.status_code, 200)
        searched_courses = self.url_open(
            f"/prodi/{prodi.id}?tab=mata-kuliah&q=Pendidikan"
        )
        self.assertEqual(searched_courses.status_code, 200)

    def test_teacher_listing_sorts_and_grade_detail_render(self):
        teacher = self.env["erpobe.master.dosen"].search(
            [("user_id", "!=", False)],
            order="id",
            limit=1,
        )
        self.assertTrue(teacher, "The academic fixture should provide a teacher")
        line_domain = [
            "|",
            ("matakuliah_id.koordinator_id", "=", teacher.id),
            ("matakuliah_id.tim_pengampu_ids", "in", teacher.id),
        ]
        lines = self.env["erpobe.akademik.penawaran.line"].sudo().search(
            line_domain,
            order="id",
        )
        graded_line = lines.filtered(
            lambda line: line.latest_rps_id
            and line.latest_rps_id.status == "final"
            and line.latest_rps_id.weight_status == "complete"
        )[:1]
        self.assertTrue(
            graded_line,
            "The academic fixture should provide an assessable teacher class",
        )

        self.authenticate(teacher.user_id.login, teacher.nip)
        routes = (
            "/my/rps?sort=course",
            "/my/rps?sort=term",
            "/my/rps?sort=status",
            "/my/kelas?sort=course",
            "/my/kelas?sort=term",
            "/my/riwayat-nilai?sort=student",
            "/my/perwalian?sort=student",
            "/my/analisis?sort=course",
            f"/my/kelas/{graded_line.id}/nilai?sort=student",
            f"/my/kelas/{graded_line.id}/nilai?sort=nim",
        )
        for route in routes:
            with self.subTest(route=route):
                response = self.url_open(route)
                self.assertEqual(response.status_code, 200, route)

        report_response = self.url_open(
            f"/report/html/erpobe.action_report_rps/"
            f"{graded_line.latest_rps_id.id}"
        )
        self.assertEqual(report_response.status_code, 200)

    def test_student_khs_report_template_renders(self):
        khs = self.env["erpobe.report.khs"].search(
            [("mahasiswa_id.user_id", "!=", False)],
            order="id",
            limit=1,
        )
        self.assertTrue(khs, "The academic fixture should provide a student KHS")
        student = khs.mahasiswa_id
        self.authenticate(student.user_id.login, student.nim)

        response = self.url_open(
            f"/report/html/erpobe.action_report_khs/{khs.id}"
        )
        self.assertEqual(response.status_code, 200)

    def test_public_routes_and_frontend_asset_respond(self):
        home_response = self.url_open("/")
        self.assertEqual(home_response.status_code, 200, "/")
        routes = (
            "/cari?q=obe",
            "/fakultas",
            "/perbandingan-cpl",
            "/triton/api/perbandingan-cpl",
            "/triton/api/perbandingan-cpl/detail?jenis_cpl=sikap",
            "/perbandingan-cpl.csv",
            "/tracking",
            "/tentang",
            "/panduan",
            "/faq",
            "/kontak",
            "/privasi",
            "/kebijakan-privasi",
            "/metodologi",
        )
        for route in routes:
            response = self.url_open(route)
            self.assertEqual(response.status_code, 200, route)
        frontend_assets = re.findall(
            r'(?:src|href)="([^"]*web/assets/[^"]*web\.assets_frontend[^"]*)"',
            home_response.text,
        )
        self.assertTrue(frontend_assets, "Frontend assets are not linked by the home page")
        for asset_url in frontend_assets:
            asset_response = self.url_open(asset_url)
            self.assertEqual(asset_response.status_code, 200, asset_url)

    def test_comparison_filters_are_validated_and_limited(self):
        response = self.url_open(
            "/triton/api/perbandingan-cpl?jenis_cpl=sikap&semester=invalid"
            "&prodi_id=1&prodi_id=2&prodi_id=3&prodi_id=4&prodi_id=5"
            "&prodi_id=6&prodi_id=7"
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual([item["key"] for item in payload["categories"]], ["sikap"])
        self.assertLessEqual(len(payload["prodi_ids"]), 6)
        self.assertEqual(payload["semester"], "")

        invalid = self.url_open(
            "/triton/api/perbandingan-cpl?jenis_cpl=invalid"
        ).json()
        self.assertEqual(len(invalid["categories"]), 5)
        detail = self.url_open(
            "/triton/api/perbandingan-cpl/detail?jenis_cpl=sikap"
        ).json()
        self.assertEqual(detail["category"]["key"], "sikap")
        self.assertIn("rows", detail["category"])

    def test_portal_routes_require_authentication(self):
        for route in (
            "/my",
            "/my/home",
            "/my/triton",
            "/my/krs",
            "/my/khs",
            "/my/mata-kuliah",
            "/my/capaian-cpl",
            "/my/rps",
            "/my/kelas",
            "/my/perwalian",
            "/my/analisis",
            "/my/profil",
        ):
            response = self.url_open(route, allow_redirects=False)
            self.assertIn(response.status_code, (302, 303), route)

    def test_teacher_analysis_shows_cpmk_cpl_and_cohort_filters(self):
        suffix = uuid.uuid4().hex[:8].upper()
        faculty = self.env["erpobe.master.fakultas"].create(
            {"name": f"Faculty Analysis {suffix}", "kode": f"FA{suffix}"}
        )
        prodi = self.env["erpobe.master.prodi"].create(
            {
                "name": f"Program Analysis {suffix}",
                "kode": f"PA{suffix}",
                "fakultas_id": faculty.id,
            }
        )
        rombel = self.env["erpobe.master.rombel"].create(
            {
                "name": f"Rombel Analysis {suffix}",
                "angkatan": 2025,
                "prodi_id": prodi.id,
            }
        )
        nip = f"NA{suffix}"
        teacher_partner = self.env["res.partner"].create(
            {
                "name": f"Teacher Analysis {suffix}",
                "email": f"teacher-analysis-{suffix.lower()}@example.test",
            }
        )
        teacher = (
            self.env["erpobe.master.dosen"]
            .sudo()
            .with_context(install_mode=True)
            .create(
                {
                    "partner_id": teacher_partner.id,
                    "nip": nip,
                    "prodi_ids": [Command.link(prodi.id)],
                }
            )
        )
        year = self.env["erpobe.akademik.tahunajaran"].create(
            {
                "tahun_ajaran": f"2099/{suffix}",
                "semester": "ganjil",
                "aktif": True,
            }
        )
        offer = self.env["erpobe.akademik.penawaran"].create(
            {
                "tahun_ajaran": year.id,
                "prodi_id": prodi.id,
                "rombel_ids": [Command.link(rombel.id)],
            }
        )
        course = self.env["erpobe.master.matakuliah"].create(
            {
                "name": f"Course Analysis {suffix}",
                "kode_mk": f"CA{suffix}",
                "sks": 3,
                "semester": 1,
                "prodi_id": prodi.id,
                "koordinator_id": teacher.id,
            }
        )
        offer_line = self.env["erpobe.akademik.penawaran.line"].create(
            {
                "penawaran_id": offer.id,
                "matakuliah_id": course.id,
                "rombel_ids": [Command.link(rombel.id)],
            }
        )
        student_partner = self.env["res.partner"].create(
            {
                "name": f"Student Analysis {suffix}",
                "email": f"student-analysis-{suffix.lower()}@example.test",
            }
        )
        student = self.env["erpobe.master.mahasiswa"].create(
            {
                "partner_id": student_partner.id,
                "nim": f"SA{suffix}",
                "rombel_id": rombel.id,
            }
        )
        krs = self.env["erpobe.akademik.krs"].create(
            {"mahasiswa_id": student.id, "penawaran_id": offer.id}
        )
        krs_line = self.env["erpobe.akademik.krs.line"].create(
            {"krs_id": krs.id, "penawaran_line_id": offer_line.id}
        )
        cpl = self.env["erpobe.akademik.cpl"].create(
            {
                "name": f"Bertakwa Analysis {suffix}",
                "kode_cpl": f"CPL-A{suffix}",
                "prodi_id": prodi.id,
            }
        )
        cpmk = self.env["erpobe.akademik.cpmk"].create(
            {
                "mk_id": course.id,
                "kode_cpmk": f"CPMK-A{suffix}",
                "name": f"CPMK Analysis {suffix}",
            }
        )
        self.env["erpobe.akademik.cpl.mk.cpmk"].create(
            {"cpl_id": cpl.id, "cpmk_id": cpmk.id}
        )
        component = self.env["erpobe.akademik.komponen"].create(
            {"name": f"Assignment Analysis {suffix}", "tipe": "assignment"}
        )
        rps = self.env["erpobe.akademik.rps"].create(
            {
                "matakuliah_id": course.id,
                "penawaran_line_id": offer_line.id,
                "komponen_ids": [Command.link(component.id)],
            }
        )
        snapshot = rps.rps_komponen_ids.filtered(
            lambda record: record.komponen_id == component
        )
        snapshot.write({"bobot": 100.0})
        rps.bobot_cpmk_mk_ids.write({"bobot_cpmk_mk": 100.0})
        rps.bobot_komponen_cpmk_ids.write({"bobot_komponen_cpmk": 100.0})
        self.env["erpobe.grade.komponen"].create(
            {
                "krs_line_id": krs_line.id,
                "komponen_id": component.id,
                "rps_id": rps.id,
                "rps_komponen_id": snapshot.id,
                "nilai": 86.0,
                "origin": "actual",
                "is_graded": True,
            }
        )
        self.env["erpobe.grade.cpmk"].create(
            {
                "mahasiswa_id": student.id,
                "cpmk_id": cpmk.id,
                "krs_line_id": krs_line.id,
                "rps_id": rps.id,
            }
        )
        self.env["erpobe.grade.cpl"].create(
            {"mahasiswa_id": student.id, "cpl_id": cpl.id}
        )

        self.authenticate(teacher.user_id.login, nip)
        response = self.url_open(
            f"/my/analisis?angkatan=2025&rombel_id={rombel.id}"
        )
        self.assertEqual(response.status_code, 200)
        self.assertRegex(
            response.text,
            rf"{re.escape(f'CPL-A{suffix}')}</strong>\s*:\s*"
            rf"{re.escape(f'Bertakwa Analysis {suffix}')}",
        )
        self.assertRegex(
            response.text,
            rf"{re.escape(f'CPMK-A{suffix}')}</strong>\s*:\s*"
            rf"{re.escape(f'CPMK Analysis {suffix}')}",
        )
        self.assertIn('name="angkatan"', response.text)
        self.assertIn('name="rombel_id"', response.text)

    def test_student_courses_route_renders_without_approved_krs(self):
        suffix = uuid.uuid4().hex[:8].upper()
        faculty = self.env["erpobe.master.fakultas"].create(
            {"name": f"Faculty Courses {suffix}", "kode": f"FC{suffix}"}
        )
        prodi = self.env["erpobe.master.prodi"].create(
            {
                "name": f"Program Courses {suffix}",
                "kode": f"PC{suffix}",
                "fakultas_id": faculty.id,
            }
        )
        rombel = self.env["erpobe.master.rombel"].create(
            {"name": f"Rombel {suffix}", "angkatan": 2025, "prodi_id": prodi.id}
        )
        email = f"student-courses-{suffix.lower()}@example.test"
        student = self.env["erpobe.master.mahasiswa"].create(
            {
                "partner_id": self.env["res.partner"].create(
                    {"name": f"Student Courses {suffix}", "email": email}
                ).id,
                "nim": f"SC{suffix}",
                "rombel_id": rombel.id,
            }
        )
        self.authenticate(email, student.nim)

        portal_home = self.url_open("/my")
        self.assertEqual(portal_home.status_code, 200)
        self.assertIn("Selamat datang", portal_home.text)

        response = self.url_open("/my/mata-kuliah")

        self.assertEqual(response.status_code, 200)
        self.assertIn("Belum ada mata kuliah", response.text)
