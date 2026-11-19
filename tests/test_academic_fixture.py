from odoo.tests import TransactionCase, tagged


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
            self.skipTest("Academic demo fixture is not installed")
        return students

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
        visible_results = self.env["erpobe.grade.subcpmk"].with_user(
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
            self.assertEqual(len(activities.mapped("subcpmk_id")), 16)
            self.assertTrue(
                all(
                    group["status"] == "complete"
                    for group in validator.get_rps_summary(rps)
                )
            )

    def test_cpl_ignores_unassessed_cpmks(self):
        students = self._require_fixture()
        cpl_grades = self.env["erpobe.grade.cpl"].sudo().search(
            [("mahasiswa_id", "in", students.ids)]
        )
        mappings = self.env["erpobe.bobot.cpmk.cpl"].sudo().search(
            [("cpl_id", "in", cpl_grades.mapped("cpl_id").ids)]
        )
        mappings_by_cpl = {}
        for mapping in mappings:
            mappings_by_cpl.setdefault(mapping.cpl_id.id, []).append(mapping)

        grade_model = self.env["erpobe.grade.cpmk"].sudo()
        for student in students:
            student_cpl_grades = cpl_grades.filtered(
                lambda grade: grade.mahasiswa_id == student
            )
            for cpl_grade in student_cpl_grades:
                cpl_mappings = mappings_by_cpl.get(cpl_grade.cpl_id.id, [])
                cpmk_ids = {mapping.cpmk_id.id for mapping in cpl_mappings}
                student_grades = grade_model.search(
                    [
                        ("mahasiswa_id", "=", student.id),
                        ("cpmk_id", "in", list(cpmk_ids)),
                    ]
                )
                scores = {
                    grade.cpmk_id.id: grade.nilai_cpmk for grade in student_grades
                }
                assessed = [
                    mapping
                    for mapping in cpl_mappings
                    if mapping.cpmk_id.id in scores
                ]
                if not assessed or len(scores) == len(cpmk_ids):
                    continue

                total_weight = sum(
                    mapping.bobot_cpmk_cpl for mapping in assessed
                )
                expected = sum(
                    mapping.bobot_cpmk_cpl * scores[mapping.cpmk_id.id]
                    for mapping in assessed
                ) / total_weight
                self.assertAlmostEqual(cpl_grade.nilai_cpl, expected, places=2)
                return

        self.fail("Fixture has no CPL with both assessed and unassessed CPMKs")
