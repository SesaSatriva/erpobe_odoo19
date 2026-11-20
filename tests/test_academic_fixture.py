from unittest.mock import patch

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

    def test_completed_fixture_seed_skips_rebuild(self):
        params = self.env["ir.config_parameter"].sudo()
        params.set_param(FIXTURE_SEED_VERSION_PARAM, FIXTURE_SEED_VERSION)
        seeder = self.env["erpobe.fixture.seeder"]

        with patch.object(
            type(seeder), "_read_program_document", side_effect=AssertionError
        ):
            self.assertTrue(seeder.load_2022_cohort())

    def test_program_cohort_counts_and_student_isolation(self):
        students = self._require_fixture()
        self.assertEqual(len(students), 100)

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
            self.assertEqual(len(cohort), 25)
            self.assertTrue(all(student.user_id for student in cohort))
            self.assertEqual(len(cpls), cpl_count)
            self.assertTrue(all(cpl.prodi_id == prodi for cpl in cpls))
            self.assertEqual(len(program_teachers), teacher_count)
            self.assertEqual(len(krs_records), 200)

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

    def test_fixture_calculation_uses_unweighted_cpl_mapping(self):
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
        mapped_cpmks = cpl.cpmk_mapping_ids.mapped("cpmk_id")
        contributing_cpmks = self.env["erpobe.grade.cpmk"].sudo().search(
            [
                ("mahasiswa_id", "=", component_grade.mahasiswa_id.id),
                ("cpmk_id", "in", mapped_cpmks.ids),
                ("is_available", "=", True),
            ]
        )
        matrix = cpl.mk_mapping_ids
        mapped_course_ids = set(matrix.mapped("mk_id").ids)
        if mapped_course_ids:
            contributing_cpmks = contributing_cpmks.filtered(
                lambda result: result.cpmk_id.mk_id.id in mapped_course_ids
            )
        expected_cpl = sum(
            result.nilai_cpmk for result in contributing_cpmks
        ) / len(contributing_cpmks)
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
        self._require_fixture()
        rps_records = self._fixture_records("erpobe.akademik.rps", "fixture_rps_")
        krs_lines = self._fixture_records(
            "erpobe.akademik.krs.line", "fixture_krsline_"
        )
        component_grades = self.env["erpobe.grade.komponen"].sudo().search(
            [("krs_line_id", "in", krs_lines.ids)]
        )
        before = {
            "rps": len(rps_records),
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
