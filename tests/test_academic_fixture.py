from types import SimpleNamespace
from unittest.mock import patch

from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged

from ..models.fixture_seeder import FIXTURE_SEED_VERSION, FIXTURE_SEED_VERSION_PARAM


@tagged("post_install", "-at_install")
class TestErpObeAcademicFixture(TransactionCase):
    PROGRAMS = {
        "ti": ("prodi_ti", 10, 13),
        "el": ("prodi_el", 8, 14),
        "mf": ("prodi_mf", 12, 14),
        "si": ("prodi_si", 10, 6),
    }

    def _fixture_records(self, model, prefix):
        data = self.env["ir.model.data"].sudo().search(
            [
                ("module", "=", "erpobe"),
                ("model", "=", model),
                ("name", "=like", f"{prefix}%"),
            ],
            order="name",
        )
        return self.env[model].sudo().browse(data.mapped("res_id")).exists()

    def _require_fixture(self):
        students = self._fixture_records(
            "erpobe.master.mahasiswa", "fixture_student_"
        )
        if not students:
            self.skipTest("Academic fixture data is not installed")
        return students

    def test_krs_selection_prioritizes_required_courses_and_caps_electives(self):
        seeder = self.env["erpobe.fixture.seeder"]

        def course(code, sks, group=None, choice_count=1):
            return {
                "spec": {"group": group, "choice_count": choice_count},
                "course": SimpleNamespace(kode_mk=code, name=code, sks=sks),
            }

        required = [course("WAJIB-01", 21)]
        electives = [
            course("PILIHAN-01", 4, "choice", 2),
            course("PILIHAN-02", 3, "choice", 2),
        ]
        selected = seeder._select_courses(required + electives, 0)

        self.assertEqual(
            [item["course"].kode_mk for item in selected],
            ["WAJIB-01", "PILIHAN-02"],
        )
        self.assertEqual(sum(item["course"].sks for item in selected), 24)

    def test_krs_selection_reports_mandatory_curriculum_over_limit(self):
        seeder = self.env["erpobe.fixture.seeder"]
        required = [
            {
                "spec": {"group": None},
                "course": SimpleNamespace(
                    kode_mk=f"WAJIB-{sks}",
                    name=f"Mata Kuliah {sks}",
                    sks=sks,
                ),
            }
            for sks in (13, 12)
        ]

        with self.assertRaisesRegex(
            ValidationError, "Konflik kurikulum.*25 SKS.*batas 24 SKS"
        ):
            seeder._select_courses(
                required,
                0,
                student=SimpleNamespace(nim="20220001"),
                program_name="Teknik Uji",
            )

    def test_completed_fixture_seed_skips_rebuild(self):
        seeder = self.env["erpobe.fixture.seeder"]
        self.assertTrue(seeder.load_2022_cohort())

    def test_program_cohort_counts_and_student_isolation(self):
        students = self._require_fixture()
        self.assertEqual(len(students), 240)

        teachers = self._fixture_records("erpobe.master.dosen", "fixture_teacher_")
        self.assertEqual(len(teachers), 46)

        for slug, (prodi_xmlid, cpl_count, teacher_count) in self.PROGRAMS.items():
            prodi = self.env.ref(f"erpobe.{prodi_xmlid}")
            cohort = students.filtered(lambda student: student.prodi_id == prodi)
            cpls = self._fixture_records(
                "erpobe.akademik.cpl", f"fixture_cpl_{slug}_"
            )
            program_teachers = teachers.filtered(
                lambda teacher: prodi in teacher.prodi_ids
            )
            krs_records = self.env["erpobe.akademik.krs"].sudo().search(
                [("mahasiswa_id", "in", cohort.ids)]
            )
            self.assertEqual(len(cohort), 60)
            self.assertTrue(all(student.user_id for student in cohort))
            self.assertEqual(len(cpls), cpl_count)
            self.assertTrue(all(cpl.prodi_id == prodi for cpl in cpls))
            self.assertEqual(len(program_teachers), teacher_count)
            self.assertEqual(len(krs_records), 60)

        ti_students = students.filtered(
            lambda student: student.prodi_id == self.env.ref("erpobe.prodi_ti")
        ).sorted("nim")
        own_student, other_student = ti_students[:2]
        visible_results = self.env["erpobe.grade.cpmk"].with_user(
            own_student.user_id
        ).search(
            [
                ("mahasiswa_id", "in", [own_student.id, other_student.id]),
            ]
        )
        self.assertTrue(visible_results)
        self.assertEqual(set(visible_results.mapped("mahasiswa_id").ids), {own_student.id})

    def test_academic_fixture_seeding_creates_scoped_admins_for_all_programs(self):
        self._require_fixture()
        self.env["erpobe.fixture.seeder"].load_2022_cohort()

        for slug, (prodi_xmlid, _, _) in self.PROGRAMS.items():
            prodi = self.env.ref(f"erpobe.{prodi_xmlid}")
            admins = prodi.user_ids.filtered(
                lambda user: user.has_group("erpobe.group_admin")
                and not user.has_group("erpobe.group_superadmin")
                and not user.has_group("base.group_system")
            )
            self.assertEqual(len(admins), 1)
            self.assertEqual(admins.erpobe_prodi_ids, prodi)
            self.assertTrue(
                admins.login
                in (
                    f"admin.{prodi.kode.lower()}",
                    f"admin.{prodi.kode.lower()}.p{prodi.id}",
                )
            )

    def test_reseeding_preserves_existing_student_and_lecturer_identities(self):
        students = self._require_fixture()
        student = students[0]
        student_values = {
            "name": "Nama Mahasiswa Manual",
            "nim": "MANUAL-IDENTITY-001",
            "email": "manual.student@example.test",
        }
        student.write(student_values)

        teacher = self._fixture_records(
            "erpobe.master.dosen", "fixture_teacher_"
        )[:1]
        teacher_values = {
            "name": "Nama Dosen Manual",
            "nip": "MANUAL-DOSEN-001",
            "email": "manual.lecturer@example.test",
        }
        teacher.write(teacher_values)

        self.env["erpobe.fixture.seeder"].with_context(
            force_fixture_seed=True
        ).load_2022_cohort()

        self.assertEqual(
            {field: student[field] for field in student_values},
            student_values,
        )
        self.assertEqual(
            {field: teacher[field] for field in teacher_values},
            teacher_values,
        )

    def test_fixture_rps_has_sixteen_weeks_and_complete_weights(self):
        self._require_fixture()
        validator = self.env["erpobe.weight.validation"]
        for slug in self.PROGRAMS:
            rps_records = self._fixture_records(
                "erpobe.akademik.rps", f"fixture_rps_{slug}_"
            )
            self.assertTrue(rps_records)
            rps = rps_records[0]
            self.assertEqual(rps.status, "final")
            activities = rps.kegiatan_perkuliahan_ids
            self.assertEqual(len(activities), 16)
            self.assertTrue(all(activities.mapped("cpmk_id")))
            if rps.rps_komponen_ids:
                self.assertTrue(
                    all(
                        group["status"] == "complete"
                        for group in validator.get_rps_summary(rps)
                    )
                )

    def test_seeded_rps_uses_component_to_cpmk_allocations(self):
        self._require_fixture()
        rps = self._fixture_records("erpobe.akademik.rps", "fixture_rps_ti_")[0]
        self.assertTrue(rps.rps_komponen_ids)
        self.assertTrue(
            rps.bobot_komponen_cpmk_ids.filtered("rps_komponen_id")
        )
        self.assertEqual(rps.status, "final")
        self.assertEqual(
            sum(rps.rps_komponen_ids.filtered("aktif").mapped("bobot")),
            100.0,
        )
        self.assertEqual(
            sum(rps.bobot_cpmk_mk_ids.mapped("bobot_cpmk_mk")),
            100.0,
        )
        self.assertEqual(
            {line.tipe for line in rps.rps_komponen_ids.filtered("aktif")},
            {"attendance", "quiz", "assignment", "midterm", "final_exam", "presentation"},
        )

    def test_fixture_grades_are_component_level_and_computed_results_are_available(self):
        students = self._require_fixture()
        grades = self.env["erpobe.grade.komponen"].sudo().search([
            ("mahasiswa_id", "in", students.ids),
            ("origin", "=", "simulated"),
            ("is_graded", "=", True),
        ])
        self.assertTrue(grades)
        self.assertTrue(all(0 <= score <= 100 for score in grades.mapped("nilai")))
        self.assertGreater(len(set(grades.mapped("nilai"))), 1)
        self.assertTrue(all(
            grade.krs_line_id
            and grade.krs_line_id.mahasiswa_id == grade.mahasiswa_id
            and grade.krs_line_id.matakuliah_id == grade.rps_id.matakuliah_id
            and grade.rps_komponen_id.rps_id == grade.rps_id
            and grade.rps_komponen_id.komponen_id == grade.komponen_id
            and grade.rps_komponen_id.tipe
            for grade in grades
        ))

        cpmk_results = self.env["erpobe.grade.cpmk"].sudo().search([
            ("mahasiswa_id", "in", students.ids),
            ("is_available", "=", True),
        ])
        course_results = self.env["erpobe.grade.mk"].sudo().search([
            ("mahasiswa_id", "in", students.ids),
            ("is_available", "=", True),
        ])
        cpl_results = self.env["erpobe.grade.cpl"].sudo().search([
            ("mahasiswa_id", "in", students.ids),
            ("is_available", "=", True),
        ])
        self.assertTrue(cpmk_results)
        self.assertTrue(course_results)
        self.assertTrue(cpl_results)
        self.assertTrue(all(0 <= score <= 100 for score in cpmk_results.mapped("nilai_cpmk")))
        self.assertTrue(all(0 <= score <= 100 for score in course_results.mapped("nilai_mk")))
        self.assertTrue(all(0 <= score <= 100 for score in cpl_results.mapped("nilai_cpl")))

        components = self._fixture_records(
            "erpobe.akademik.komponen", "fixture_component_"
        ) | self.env.ref("erpobe.komponen_kognitif") | self.env.ref(
            "erpobe.komponen_partisipatif"
        )
        self.assertTrue(all(component.tipe not in ("kognitif", "partisipatif") for component in components))

        for cpl in self._fixture_records("erpobe.akademik.cpl", "fixture_cpl_"):
            mappings = cpl.mk_mapping_ids
            self.assertTrue(mappings)
            mapped_course_ids = set(mappings.mapped("mk_id").ids)
            cpmk_course_ids = set(cpl.cpmk_mapping_ids.mapped("cpmk_id.mk_id").ids)
            self.assertTrue(mapped_course_ids <= cpmk_course_ids)
        self.assertNotIn(
            "bobot_mk_cpl",
            self.env["erpobe.akademik.mk.cpl"]._fields,
        )

    def test_fixture_calculation_uses_official_cpl_mapping_weights(self):
        students = self._require_fixture()
        component_grade = self.env["erpobe.grade.komponen"].sudo().search(
            [
                ("mahasiswa_id", "in", students.ids),
                ("origin", "=", "simulated"),
                ("is_graded", "=", True),
            ],
            limit=1,
        )
        rps = component_grade.rps_id
        cpmk = rps.cpmk_ids[0]
        allocations = rps.bobot_komponen_cpmk_ids.filtered(
            lambda line: line.cpmk_id == cpmk
            and line.rps_komponen_id.aktif
        )
        cpmk_result = self.env["erpobe.grade.cpmk"].sudo().search(
            [
                ("mahasiswa_id", "=", component_grade.mahasiswa_id.id),
                ("cpmk_id", "=", cpmk.id),
                ("krs_line_id", "=", component_grade.krs_line_id.id),
                ("rps_id", "=", rps.id),
            ],
            limit=1,
        )
        cpmk_scores = self.env["erpobe.grade.komponen"].sudo().search(
            [
                ("krs_line_id", "=", component_grade.krs_line_id.id),
                ("rps_id", "=", rps.id),
                ("rps_komponen_id", "in", allocations.mapped("rps_komponen_id").ids),
                ("is_graded", "=", True),
            ]
        )
        component_total = sum(
            score.nilai
            * score.rps_komponen_id.bobot
            * score.rps_komponen_id.allocation_ids.filtered(
                lambda line: line.cpmk_id == cpmk
            ).bobot_komponen_cpmk
            / 100
            for score in cpmk_scores
        )
        component_weight = sum(
            score.rps_komponen_id.bobot
            * score.rps_komponen_id.allocation_ids.filtered(
                lambda line: line.cpmk_id == cpmk
            ).bobot_komponen_cpmk
            / 100
            for score in cpmk_scores
        )
        self.assertEqual(
            cpmk_result.nilai_cpmk,
            round(component_total / component_weight, 2),
        )

        course_result = self.env["erpobe.grade.mk"].sudo().search(
            [
                ("mahasiswa_id", "=", component_grade.mahasiswa_id.id),
                ("mk_id", "=", rps.matakuliah_id.id),
                ("krs_line_id", "=", component_grade.krs_line_id.id),
                ("rps_id", "=", rps.id),
            ],
            limit=1,
        )
        course_scores = cpmk_result.search(
            [
                ("mahasiswa_id", "=", component_grade.mahasiswa_id.id),
                ("mk_id", "=", rps.matakuliah_id.id),
                ("krs_line_id", "=", component_grade.krs_line_id.id),
                ("rps_id", "=", rps.id),
                ("is_available", "=", True),
            ]
        )
        course_weights = {
            line.cpmk_id.id: line.bobot_cpmk_mk
            for line in rps.bobot_cpmk_mk_ids
        }
        expected_course = sum(
            result.nilai_cpmk * course_weights[result.cpmk_id.id]
            for result in course_scores
        ) / sum(course_weights[result.cpmk_id.id] for result in course_scores)
        self.assertEqual(course_result.nilai_mk, round(expected_course, 2))

        cpl = cpmk.cpl_mapping_ids[:1].cpl_id
        cpl_result = self.env["erpobe.grade.cpl"].sudo().search(
            [
                ("mahasiswa_id", "=", component_grade.mahasiswa_id.id),
                ("cpl_id", "=", cpl.id),
            ],
            limit=1,
        )
        cpl_mappings = cpl.cpmk_mapping_ids.filtered(
            lambda mapping: mapping.cpmk_id.prodi_id == cpl.prodi_id
            and (
                not cpl.mk_mapping_ids
                or mapping.cpmk_id.mk_id in cpl.mk_mapping_ids.mapped("mk_id")
            )
        )
        contributing_cpmks = self.env["erpobe.grade.cpmk"].sudo().search(
            [
                ("mahasiswa_id", "=", component_grade.mahasiswa_id.id),
                ("cpmk_id", "in", cpl_mappings.mapped("cpmk_id").ids),
                ("is_available", "=", True),
                ("rps_id.status", "=", "final"),
                ("krs_line_id.krs_id.state", "=", "approved"),
            ]
        )
        weighted_total = 0.0
        weight_total = 0.0
        for mapping in cpl_mappings:
            candidates = contributing_cpmks.filtered(
                lambda result: result.cpmk_id == mapping.cpmk_id
            )
            if not candidates:
                continue
            result = max(
                candidates,
                key=lambda grade: (
                    grade.nilai_cpmk,
                    grade.rps_id.id or 0,
                    grade.krs_line_id.id or 0,
                    grade.id,
                ),
            )
            weight = mapping.bobot_cpl_cpmk
            if weight <= 0:
                weight = next(
                    (
                        line.bobot_cpmk_mk
                        for line in result.rps_id.bobot_cpmk_mk_ids
                        if line.cpmk_id == mapping.cpmk_id
                    ),
                    0.0,
                )
            if weight > 0:
                weighted_total += result.nilai_cpmk * weight
                weight_total += weight
        expected_cpl = weighted_total / weight_total
        self.assertEqual(cpl_result.nilai_cpl, round(expected_cpl, 2))

    def test_fixture_regeneration_preserves_manually_entered_component_grades(self):
        self._require_fixture()
        grade = self.env["erpobe.grade.komponen"].sudo().search(
            [("origin", "=", "simulated"), ("is_graded", "=", True)],
            limit=1,
        )
        grade.write({"nilai": 91.0, "origin": "actual"})
        self.env["erpobe.fixture.seeder"].with_context(
            force_fixture_seed=True
        ).load_2022_cohort()
        self.assertEqual(grade.nilai, 91.0)
        self.assertEqual(grade.origin, "actual")

    def test_repeated_seed_does_not_duplicate_or_delete_history(self):
        students = self._require_fixture()
        rps_records = self._fixture_records("erpobe.akademik.rps", "fixture_rps_")
        krs_records = self.env["erpobe.akademik.krs"].sudo().search(
            [("mahasiswa_id", "in", students.ids)]
        )
        krs_lines = krs_records.mapped("line_ids")
        component_grades = self.env["erpobe.grade.komponen"].sudo().search(
            [("krs_line_id", "in", krs_lines.ids)]
        )
        before = {
            "rps": len(rps_records),
            "krs": len(krs_records),
            "krs_lines": len(krs_lines),
            "snapshots": sum(len(rps.rps_komponen_ids) for rps in rps_records),
            "allocations": sum(
                len(rps.bobot_komponen_cpmk_ids) for rps in rps_records
            ),
            "grades": len(component_grades),
            "audits": self.env["erpobe.grade.komponen.audit"].sudo().search_count(
                [("grade_id", "in", component_grades.ids)]
            ),
        }
        seeder = self.env["erpobe.fixture.seeder"]
        force_seeder = seeder.with_context(force_fixture_seed=True)
        self.assertTrue(force_seeder.load_2022_cohort())
        self.assertTrue(force_seeder.load_2022_cohort())
        after = {
            "rps": len(self._fixture_records("erpobe.akademik.rps", "fixture_rps_")),
            "krs": self.env["erpobe.akademik.krs"].sudo().search_count(
                [("mahasiswa_id", "in", students.ids)]
            ),
            "krs_lines": self.env["erpobe.akademik.krs.line"].sudo().search_count(
                [("krs_id.mahasiswa_id", "in", students.ids)]
            ),
            "snapshots": sum(
                len(rps.rps_komponen_ids)
                for rps in self._fixture_records("erpobe.akademik.rps", "fixture_rps_")
            ),
            "allocations": sum(
                len(rps.bobot_komponen_cpmk_ids)
                for rps in self._fixture_records("erpobe.akademik.rps", "fixture_rps_")
            ),
            "grades": self.env["erpobe.grade.komponen"].sudo().search_count(
                [("krs_line_id", "in", krs_lines.ids)]
            ),
            "audits": self.env["erpobe.grade.komponen.audit"].sudo().search_count(
                [("grade_id", "in", component_grades.ids)]
            ),
        }
        self.assertEqual(after, before)

    def test_cpl_uses_direct_cpmk_mapping_not_weight_rows(self):
        students = self._require_fixture()
        cpl_grades = self.env["erpobe.grade.cpl"].sudo().search(
            [("mahasiswa_id", "in", students.ids)]
        )
        mappings = self.env["erpobe.akademik.cpl.mk.cpmk"].sudo().search(
            [("cpl_id", "in", cpl_grades.mapped("cpl_id").ids)]
        )
        self.assertTrue(mappings)
        self.assertTrue(all(mappings.mapped("cpmk_id")))

        rps_records = self._fixture_records("erpobe.akademik.rps", "fixture_rps_")
        self.assertTrue(rps_records)
