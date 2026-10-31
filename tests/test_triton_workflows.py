import re
import uuid

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
        self.assertNotEqual(self.student.user_id, second_student.user_id)
        visible_ids = self.Krs.with_user(self.student.user_id).search(
            [("id", "in", [first_krs.id, second_krs.id])]
        ).ids
        self.assertIn(first_krs.id, visible_ids)
        self.assertNotIn(second_krs.id, visible_ids)

        report_model = self.env["erpobe.report.khs"]
        first_report = report_model.create({"mahasiswa_id": self.student.id})
        second_report = report_model.create({"mahasiswa_id": second_student.id})
        visible_report_ids = report_model.with_user(self.student.user_id).search(
            [("id", "in", [first_report.id, second_report.id])]
        ).ids
        self.assertIn(first_report.id, visible_report_ids)
        self.assertNotIn(second_report.id, visible_report_ids)

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
        component = self.env["erpobe.akademik.komponen"].create(
            {"name": f"Komponen {self.suffix}", "tipe": "kognitif"}
        )
        rps = self.env["erpobe.akademik.rps"].create(
            {
                "matakuliah_id": self.course.id,
                "penawaran_line_id": self.offer_line.id,
                "komponen_ids": [Command.link(component.id)],
            }
        )
        rps.bobot_cpmk_cpl_ids.write({"bobot_cpmk_cpl": 100.0})
        rps.bobot_cpmk_mk_ids.write({"bobot_cpmk_mk": 100.0})
        rps.bobot_komponen_cpmk_ids.write({"bobot_komponen_cpmk": 100.0})

        krs = self._new_krs()
        krs_line = self.KrsLine.create(
            {"krs_id": krs.id, "penawaran_line_id": self.offer_line.id}
        )
        self.env["erpobe.grade.komponen"].create(
            {
                "krs_line_id": krs_line.id,
                "komponen_id": component.id,
                "nilai": 80.0,
            }
        )
        grade_cpmk = self.env["erpobe.grade.cpmk"].create(
            {"mahasiswa_id": self.student.id, "cpmk_id": cpmk.id}
        )
        grade_cpl = self.env["erpobe.grade.cpl"].create(
            {"mahasiswa_id": self.student.id, "cpl_id": cpl.id}
        )
        grade_mk = self.GradeMk.create(
            {"mahasiswa_id": self.student.id, "mk_id": self.course.id}
        )
        self.env["erpobe.master.grade"].create(
            {
                "name": f"Grade KRS {self.suffix}",
                "nilai_min": 0.0,
                "nilai_max": 79.99,
                "bobot": 1.0,
            }
        )
        self.assertEqual(grade_cpmk.nilai_cpmk, 80.0)
        self.assertEqual(grade_cpl.nilai_cpl, 80.0)
        self.assertEqual(grade_mk.nilai_mk, 80.0)

        report = self.env["erpobe.report.khs"].create(
            {"mahasiswa_id": self.student.id}
        )
        report_line = report.mk_line_ids.filtered(
            lambda record: record.mk_id == self.course
        )
        self.assertEqual(len(report_line), 1)
        self.assertEqual(report.total_sks_lulus, self.course.sks)
        self.assertEqual(report.ipk, report_line.bobot)


@tagged("post_install", "-at_install")
class TestTritonPublicRoutes(HttpCase):
    def test_public_routes_and_frontend_asset_respond(self):
        home_response = self.url_open("/")
        self.assertEqual(home_response.status_code, 200, "/")
        routes = (
            "/cari?q=obe",
            "/fakultas",
            "/perbandingan-cpl",
            "/triton/api/perbandingan-cpl",
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

    def test_portal_routes_require_authentication(self):
        for route in (
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
