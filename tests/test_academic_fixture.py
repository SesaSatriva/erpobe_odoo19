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

    def test_seeded_rps_uses_component_to_cpmk_allocations_without_subcpmk(self):
        self._require_fixture()
        rps = self._fixture_records("erpobe.akademik.rps", "fixture_rps_ti_")[0]
        self.assertTrue(rps.rps_komponen_ids)
        self.assertTrue(
            rps.bobot_komponen_cpmk_ids.filtered("rps_komponen_id")
        )
        self.assertEqual(rps.status, "final")

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
            "subcpmks": len(
                self._fixture_records("erpobe.akademik.subcpmk", "fixture_subcpmk_")
            ),
            "subcpmk_results": len(
                self._fixture_records("erpobe.grade.subcpmk", "fixture_subresult_")
            ),
        }
        seeder = self.env["erpobe.fixture.seeder"]
        self.assertTrue(seeder.load_2022_cohort())
        self.assertTrue(seeder.load_2022_cohort())
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
            "subcpmks": len(
                self._fixture_records("erpobe.akademik.subcpmk", "fixture_subcpmk_")
            ),
            "subcpmk_results": len(
                self._fixture_records("erpobe.grade.subcpmk", "fixture_subresult_")
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
        self.assertTrue(
            all(
                not line.bobot_cpmk_cpl
                for rps in rps_records
                for line in rps.bobot_cpmk_cpl_ids
            )
        )
