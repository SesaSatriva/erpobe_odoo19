import uuid
from unittest.mock import patch

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestErpObeOfficialCurriculum(TransactionCase):
    def _create_importer_student(self, prodi_xmlid):
        prodi = self.env.ref("erpobe.%s" % prodi_xmlid)
        rombel = self.env["erpobe.master.rombel"].sudo().search([
            ("prodi_id", "=", prodi.id),
            ("angkatan", "=", 2022),
            ("name", "=", "A"),
        ], limit=1)
        self.assertTrue(rombel)
        suffix = uuid.uuid4().hex[:10]
        partner = self.env["res.partner"].sudo().create({
            "name": "KHS Import Test %s" % suffix,
            "email": "khs-import-%s@example.test" % suffix,
        })
        return self.env["erpobe.master.mahasiswa"].sudo().create({
            "partner_id": partner.id,
            "nim": "KHS-IMPORT-%s" % suffix.upper(),
            "rombel_id": rombel.id,
        })

    def test_demo_students_are_2022_two_classes_minimum_30(self):
        programs = {
            "Teknik Sipil": self.env.ref("erpobe.prodi_si"),
            "Teknik Industri": self.env.ref("erpobe.prodi_ti"),
            "Teknik Manufaktur": self.env.ref("erpobe.prodi_mf"),
            "Teknik Elektro": self.env.ref("erpobe.prodi_el"),
        }
        for name, prodi in programs.items():
            rombels = self.env["erpobe.master.rombel"].sudo().search([
                ("prodi_id", "=", prodi.id),
                ("angkatan", "=", 2022),
            ])
            for rombel in rombels.filtered(lambda r: r.name in ("A", "B")):
                count = self.env["erpobe.master.mahasiswa"].sudo().search_count([
                    ("rombel_id", "=", rombel.id),
                ])
                self.assertGreaterEqual(count, 30, "%s kelas %s" % (name, rombel.name))

    def test_official_master_counts_match_documents(self):
        expected = {"si": (56, 9, 168), "ti": (64, 11, 192),
                    "mf": (55, 8, 165), "el": (62, 8, 186)}
        program_files = {
            "si": "prodi_si", "ti": "prodi_ti",
            "mf": "prodi_mf", "el": "prodi_el",
        }
        source_model = self.env["erpobe.akademik.fixture.source"].sudo()

        def officially_sourced_count(model_name, prodi):
            sources = source_model.search([
                ("record_model", "=", model_name),
                ("source_type", "=", "official"),
            ])
            records = self.env[model_name].sudo().browse(
                sources.mapped("record_id")
            ).exists()
            return len(records.filtered(lambda record: record.prodi_id == prodi))

        for slug, xmlid in program_files.items():
            prodi = self.env.ref("erpobe.%s" % xmlid)
            course_count = self.env[
                "erpobe.master.matakuliah"
            ].sudo().search_count([
                ("prodi_id", "=", prodi.id),
                ("identity_key", "!=", False),
            ])
            cpl_count = officially_sourced_count(
                "erpobe.akademik.cpl", prodi
            )
            cpmk_count = officially_sourced_count(
                "erpobe.akademik.cpmk", prodi
            )
            self.assertEqual(course_count, expected[slug][0])
            self.assertEqual(cpl_count, expected[slug][1])
            self.assertEqual(cpmk_count, expected[slug][2])

    def test_semester6_recovery_has_rps_and_weights(self):
        Rps = self.env["erpobe.akademik.rps"].sudo()
        period = self.env["erpobe.akademik.tahunajaran"].sudo().search([
            ("tahun_ajaran", "=", "2025/2026"),
            ("semester", "=", "genap"),
        ], limit=1)
        offers = self.env["erpobe.akademik.penawaran"].sudo().search([
            ("tahun_ajaran", "=", period.id),
        ])
        active_offer_ids = [
            offer.id
            for offer in offers
            if self.env["erpobe.akademik.krs"].sudo().search_count([
                ("penawaran_id", "=", offer.id),
            ])
        ]
        rps_records = Rps.search([
            ("semester", "=", 6),
            ("matakuliah_id.identity_key", "!=", False),
            ("penawaran_line_id.penawaran_id", "in", active_offer_ids),
        ], order="penawaran_line_id, version desc, id desc")
        latest_by_offer = {}
        for rps in rps_records:
            latest_by_offer.setdefault(rps.penawaran_line_id.id, rps)
        rps_records = Rps.browse(
            [rps.id for rps in latest_by_offer.values()]
        )
        self.assertTrue(rps_records)
        self.assertEqual(
            len(rps_records),
            len(set(rps_records.mapped("penawaran_line_id").ids)),
        )
        self.assertTrue(all(rps.status == "final" for rps in rps_records))
        validator = self.env["erpobe.weight.validation"]
        for rps in rps_records:
            self.assertTrue(validator.validate_rps(rps)["complete"])
            self.assertEqual(len(rps.kegiatan_perkuliahan_ids), 16)
            self.assertTrue(rps.referensi_ids)
            self.assertTrue(rps.rubrik_penilaian_ids)
            self.assertTrue(
                all(rubric.kriteria_ids for rubric in rps.rubrik_penilaian_ids)
            )
            self.assertTrue(rps.tim_pengampu_ids)
            self.assertIn(rps.koordinator_id, rps.tim_pengampu_ids)
            self.assertTrue(
                all(
                    rps.prodi_id in lecturer.prodi_ids
                    for lecturer in rps.tim_pengampu_ids
                )
            )
            self.assertEqual(
                round(sum(rps.bobot_cpmk_mk_ids.mapped("bobot_cpmk_mk")), 2),
                100.0,
            )

        krs_records = self.env["erpobe.akademik.krs"].sudo().search([
            ("mahasiswa_id.angkatan", "=", 2022),
            ("penawaran_id", "in", active_offer_ids),
        ])
        krs_records = krs_records.filtered(
            lambda krs: any(krs.line_ids.mapped("matakuliah_id.identity_key"))
        )
        self.assertTrue(krs_records)
        for krs in krs_records:
            courses = self.env["erpobe.master.matakuliah"].sudo().search([
                ("prodi_id", "=", krs.prodi_id.id),
                ("semester", "=", 6),
                ("identity_key", "!=", False),
            ])
            mandatory = courses.filtered(
                lambda course: "Pilihan" not in (course.status_mk or "")
            )
            electives = courses.filtered(
                lambda course: "Pilihan" in (course.status_mk or "")
            )
            selected_ids = set(krs.line_ids.mapped("matakuliah_id").ids)
            self.assertLessEqual(krs.total_sks, 24)
            self.assertTrue(set(mandatory.ids) <= selected_ids)
            self.assertTrue(selected_ids <= set(courses.ids))
            if sum(courses.mapped("sks")) <= 24:
                self.assertTrue(set(electives.ids) <= selected_ids)

    def test_fixture_loader_creates_2022_cohort(self):
        seeder = self.env["erpobe.fixture.seeder"].sudo()
        self.assertTrue(seeder.load_2022_cohort())
        fixture_students = self.env["erpobe.master.mahasiswa"].sudo().search_count([
            ("nim", "=like", "SIM%"),
        ])
        self.assertGreaterEqual(fixture_students, 240)

    def test_official_curriculum_documents_import_idempotently(self):
        loader = self.env["erpobe.official.curriculum"].sudo()
        first = loader.load_all()
        rps_count = self.env["erpobe.akademik.rps"].sudo().search_count([
            ("semester", "=", 6),
            ("matakuliah_id.identity_key", "!=", False),
        ])
        second = loader.load_all()
        self.assertEqual(
            self.env["erpobe.akademik.rps"].sudo().search_count([
                ("semester", "=", 6),
                ("matakuliah_id.identity_key", "!=", False),
            ]),
            rps_count,
        )

        expected = {
            "si": (56, 9),
            "ti": (64, 11),
            "mf": (55, 8),
            "el": (62, 8),
        }
        for slug, (course_count, cpl_count) in expected.items():
            self.assertEqual(first[slug]["courses"], course_count)
            self.assertEqual(first[slug]["cpls"], cpl_count)
            self.assertEqual(second[slug]["courses"], course_count)
            self.assertEqual(second[slug]["cpls"], cpl_count)

        period = self.env["erpobe.akademik.tahunajaran"].sudo().search(
            [("aktif", "=", True)]
        )
        self.assertEqual(len(period), 1)
        self.assertEqual(period.tahun_ajaran, "2025/2026")
        self.assertEqual(period.semester, "genap")

    def test_load_all_batches_krs_only_changes_for_unique_students(self):
        self.env["erpobe.fixture.seeder"].sudo().load_2022_cohort()
        students = (
            self._create_importer_student("prodi_ti")
            | self._create_importer_student("prodi_ti")
        )
        Grade = self.env["erpobe.grade.komponen"].sudo()
        grade_counts_before = {
            student.id: Grade.search_count([
                ("mahasiswa_id", "=", student.id),
            ])
            for student in students
        }
        loader = self.env["erpobe.official.curriculum"].sudo()
        report_model_class = type(self.env["erpobe.report.khs"])
        original_generate = report_model_class.action_generate_khs
        batches = []

        def capture_batch(report_model, student_ids):
            batches.append(tuple(student_ids))
            return original_generate(report_model, student_ids)

        def skip_grade_changes(importer, force=False, affected_student_ids=None):
            return 0

        with (
            patch.object(report_model_class, "action_generate_khs", capture_batch),
            patch.object(
                type(loader), "_generate_dummy_grades", skip_grade_changes
            ),
        ):
            summary = loader.load_all()

        self.assertEqual(len(batches), 1)
        self.assertEqual(len(batches[0]), len(set(batches[0])))
        self.assertTrue(set(students.ids) <= set(batches[0]))
        self.assertGreaterEqual(summary["operations"]["krs_lines"], 2)
        for student in students:
            krs = self.env["erpobe.akademik.krs"].sudo().search([
                ("mahasiswa_id", "=", student.id),
                ("tahun_ajaran.tahun_ajaran", "=", "2025/2026"),
                ("tahun_ajaran.semester", "=", "genap"),
            ], limit=1)
            self.assertTrue(krs)
            self.assertGreater(len(krs.line_ids), 1)
            self.assertEqual(
                Grade.search_count([("mahasiswa_id", "=", student.id)]),
                grade_counts_before[student.id],
            )
            self.assertEqual(
                self.env["erpobe.report.khs"].sudo().search_count([
                    ("mahasiswa_id", "=", student.id),
                ]),
                1,
            )

    def test_fixture_and_importer_use_one_final_khs_batch(self):
        report_model_class = type(self.env["erpobe.report.khs"])
        original_generate = report_model_class.action_generate_khs
        batches = []

        def capture_batch(report_model, student_ids):
            batches.append(tuple(student_ids))
            return original_generate(report_model, student_ids)

        with patch.object(report_model_class, "action_generate_khs", capture_batch):
            self.env["erpobe.fixture.seeder"].sudo().load_2022_cohort_if_enabled()

        self.assertEqual(len(batches), 1)
        self.assertEqual(len(batches[0]), len(set(batches[0])))

    def test_load_all_exception_does_not_leak_defer_context(self):
        loader = self.env["erpobe.official.curriculum"].sudo()
        original_context = dict(loader.env.context)
        with (
            patch.object(
                type(loader), "_read_document", side_effect=RuntimeError("test failure")
            ),
            self.assertRaisesRegex(RuntimeError, "test failure"),
        ):
            loader.load_all()

        self.assertEqual(loader.env.context, original_context)
        self.assertNotIn("defer_khs_refresh", loader.env.context)

    def test_deferred_rps_status_change_does_not_generate_khs_individually(self):
        Rps = self.env["erpobe.akademik.rps"].sudo()
        rps = Rps.search([
            ("status", "=", "final"),
            ("semester", "=", 6),
            ("penawaran_line_id", "!=", False),
        ], limit=1)
        self.assertTrue(rps)
        rombel = rps.penawaran_line_id.penawaran_id.rombel_ids.filtered(
            lambda record: record.prodi_id == rps.matakuliah_id.prodi_id
        )[:1]
        self.assertTrue(rombel)
        suffix = uuid.uuid4().hex[:10]
        student = self.env["erpobe.master.mahasiswa"].sudo().create({
            "partner_id": self.env["res.partner"].sudo().create({
                "name": "KHS RPS Test %s" % suffix,
                "email": "khs-rps-%s@example.test" % suffix,
            }).id,
            "nim": "KHS-RPS-%s" % suffix.upper(),
            "rombel_id": rombel.id,
        })
        krs = self.env["erpobe.akademik.krs"].sudo().with_context(
            defer_khs_refresh=True
        ).create({
            "mahasiswa_id": student.id,
            "penawaran_id": rps.penawaran_line_id.penawaran_id.id,
        })
        krs_line = self.env["erpobe.akademik.krs.line"].sudo().with_context(
            defer_khs_refresh=True
        ).create({
            "krs_id": krs.id,
            "penawaran_line_id": rps.penawaran_line_id.id,
        })
        krs.with_context(
            allow_krs_state_change=True,
            defer_khs_refresh=True,
        ).write({"state": "approved"})
        revision = rps.copy()
        self.assertEqual(revision.status, "review")

        GradeMk = self.env["erpobe.grade.mk"].sudo().with_context(
            defer_khs_refresh=True
        )
        grade = GradeMk.search([
            ("krs_line_id", "=", krs_line.id),
        ], limit=1)
        if grade:
            grade.write({"rps_id": revision.id})
        else:
            GradeMk.create({
                "mahasiswa_id": student.id,
                "mk_id": krs_line.matakuliah_id.id,
                "krs_line_id": krs_line.id,
                "rps_id": revision.id,
            })

        report_model_class = type(self.env["erpobe.report.khs"])
        generated_batches = []

        def capture_batch(report_model, student_ids):
            generated_batches.append(tuple(student_ids))

        with patch.object(
            report_model_class, "action_generate_khs", capture_batch
        ):
            revision.with_context(defer_khs_refresh=True).write(
                {"status": "draft"}
            )

        self.assertEqual(revision.status, "draft")
        self.assertEqual(generated_batches, [])

    def test_repeated_khs_generation_preserves_detail_ids_and_report_count(self):
        report_model = self.env["erpobe.report.khs"].sudo()
        report = report_model.search([("mk_line_ids", "!=", False)], limit=1)
        self.assertTrue(report)

        detail_fields = (
            "mk_line_ids",
            "cpmk_line_ids",
            "cpl_line_ids",
            "komponen_line_ids",
        )
        report_model.action_generate_khs([report.mahasiswa_id.id])
        first_ids = {
            field_name: set(report[field_name].ids) for field_name in detail_fields
        }
        report_model.action_generate_khs([report.mahasiswa_id.id])
        report.invalidate_recordset(detail_fields)

        self.assertEqual(
            {
                field_name: set(report[field_name].ids)
                for field_name in detail_fields
            },
            first_ids,
        )
        self.assertEqual(
            report_model.search_count([
                ("mahasiswa_id", "=", report.mahasiswa_id.id),
            ]),
            1,
        )

    def test_official_curriculum_records_have_provenance(self):
        Source = self.env["erpobe.akademik.fixture.source"].sudo()
        for model_name in (
            "erpobe.akademik.kurikulum",
            "erpobe.akademik.cpl",
            "erpobe.akademik.cpmk",
            "erpobe.akademik.cpl.mk.cpmk",
            "erpobe.akademik.mk.cpl",
        ):
            sources = Source.search([
                ("record_model", "=", model_name),
                ("source_type", "=", "official"),
            ])
            self.assertTrue(sources, model_name)

        course_sources = Source.search([
            ("record_model", "=", "erpobe.master.matakuliah"),
            ("fixture_key", "=like", "official_curriculum_erpobe_master_matakuliah_%"),
        ])
        self.assertTrue(course_sources)
        self.assertTrue(
            all(source.source_type in ("official", "mixed") for source in course_sources)
        )
        self.assertTrue(
            any(source.source_type == "mixed" for source in course_sources)
        )

    def test_placeholder_course_codes_remain_distinct(self):
        loader = self.env["erpobe.official.curriculum"].sudo()
        text = loader._read_document("ti")
        courses = loader.parse_courses(text)
        placeholders = [
            course for course in courses
            if course["code"].endswith("602XX")
        ]
        names = {course["name"] for course in placeholders}
        self.assertGreaterEqual(len(placeholders), 4)
        self.assertEqual(len(names), len(placeholders))
