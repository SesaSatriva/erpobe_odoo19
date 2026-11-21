from types import SimpleNamespace

from odoo import Command
from odoo.exceptions import AccessError
from odoo.tests import TransactionCase, tagged

from ..controllers.academic_assistant_service import AcademicAssistantService
from ..controllers.assistant_intents import (
    detect_intent,
    extract_entities,
    normalize_keyword,
)


@tagged("post_install", "-at_install")
class TestAcademicAssistantIntent(TransactionCase):
    def test_conversation_context_rejects_untrusted_entity_codes(self):
        context = AcademicAssistantService._sanitize_conversation_context({
            "intent_id": "cpmk_achievement",
            "entity_kind": "cpmk",
            "entity_code": "CPMK-%",
        })
        self.assertEqual(context, {"intent_id": "cpmk_achievement"})

        valid = AcademicAssistantService._sanitize_conversation_context({
            "intent_id": "cpmk_achievement",
            "entity_kind": "cpmk",
            "entity_code": "CPMK-B",
        })
        self.assertEqual(valid["entity_code"], "CPMK-B")

    def test_keyword_normalization_handles_indonesian_text(self):
        self.assertEqual(normalize_keyword("Capaian Pembelajaran"), "capaian pembelajaran")
        self.assertEqual(normalize_keyword("Nilai: Mahasiswa!"), "nilai mahasiswa")
        self.assertEqual(normalize_keyword("Rata-rata nilai"), "rata rata nilai")

    def test_aliases_and_outcome_codes_are_detected(self):
        self.assertEqual(detect_intent("mhs aktif")["intent_id"], "student_active")
        self.assertEqual(detect_intent("pengajar aktif")["intent_id"], "lecturer_active")

        cpl = detect_intent("Jelaskan kompetensi lulusan CPL-A")
        self.assertEqual(cpl["intent"], "cpl")
        self.assertEqual(cpl["entity_code"], "CPL-A")

        cpmk = detect_intent("Apa capaian mata kuliah CPMK-B?")
        self.assertEqual(cpmk["intent"], "cpmk")
        self.assertEqual(cpmk["entity_code"], "CPMK-B")

        related_cpl = detect_intent("CPL terkait CPMK-B")
        self.assertEqual(related_cpl["intent_id"], "cpl_details")
        self.assertEqual(related_cpl["entity_kind"], "cpmk")

        related_cpmk = detect_intent("CPMK yang terkait CPL-A")
        self.assertEqual(related_cpmk["intent_id"], "cpmk_details")
        self.assertEqual(related_cpmk["entity_kind"], "cpl")

        self.assertEqual(detect_intent("CPLV")["entity_code"], "CPLV")

    def test_student_entities_are_extracted_and_validated_as_values(self):
        entities = extract_entities(
            "Mahasiswa angkatan 2022 dari Teknik Informatika dengan IPK di bawah 3,00"
        )
        self.assertEqual(entities["cohort"], 2022)
        self.assertEqual(entities["program"], "teknik informatika")
        self.assertEqual(entities["gpa_operator"], "<")
        self.assertEqual(entities["gpa_value"], 3.0)

    def test_lecturer_name_is_extracted_for_search(self):
        result = detect_intent("Cari dosen Budi Santoso")
        self.assertEqual(result["intent_id"], "lecturer_search")
        self.assertEqual(result["search_name"], "budi santoso")

    def test_course_code_and_academic_period_are_extracted(self):
        course = detect_intent("Berapa SKS IF-202?")
        self.assertEqual(course["intent"], "course")
        self.assertEqual(course["entity_code"], "IF-202")

        rps = detect_intent(
            "Tampilkan RPS semester ganjil 2026 yang belum divalidasi"
        )
        self.assertEqual(rps["intent_id"], "rps_unvalidated")
        self.assertEqual(rps["semester"], "ganjil")
        self.assertEqual(rps["cohort"], 2026)

    def test_ambiguous_relationship_is_not_guessed(self):
        result = detect_intent(
            "Berapa mahasiswa yang mengambil mata kuliah dosen X?"
        )
        self.assertEqual(result["intent_id"], "clarify")

    def test_context_and_unknown_questions(self):
        contextual = detect_intent(
            "Bagaimana performanya?",
            page_context={"model": "erpobe.master.mahasiswa", "res_id": 3},
        )
        self.assertEqual(contextual["intent_id"], "student_academic_performance")

        follow_up = detect_intent(
            "Bagaimana targetnya?",
            {
                "intent": "cpmk",
                "entity_kind": "cpmk",
                "entity_code": "CPMK-B",
            },
        )
        self.assertEqual(follow_up["intent_id"], "cpmk_achievement")
        self.assertEqual(follow_up["entity_code"], "CPMK-B")

        unknown = detect_intent("Apa ini?", {"intent": [], "entity_kind": {}})
        self.assertEqual(unknown["intent_id"], "help")
        self.assertEqual(unknown["entity_code"], "")


@tagged("post_install", "-at_install")
class TestAcademicAssistantService(TransactionCase):
    def test_lecturer_grade_aggregates_are_program_scoped(self):
        user = SimpleNamespace(
            has_group=lambda group: group == "erpobe.group_dosen",
            erpobe_prodi_ids=SimpleNamespace(ids=[3, 7]),
        )
        service = AcademicAssistantService(SimpleNamespace(user=user))
        domain = service._assistant_grade_domain([("is_available", "=", True)])
        self.assertEqual(
            domain,
            [
                ("is_available", "=", True),
                ("prodi_id", "in", [3, 7]),
            ],
        )

    def test_student_count_uses_the_active_orm_environment(self):
        expected = self.env["erpobe.master.mahasiswa"].search_count([])
        response = AcademicAssistantService(self.env).answer(
            "Berapa jumlah mahasiswa?"
        )
        self.assertEqual(response["type"], "statistic")
        self.assertEqual(response["data"]["total"], expected)

    def test_query_respects_model_access(self):
        user = self.env["res.users"].create({
            "name": "Assistant Restricted Test",
            "login": f"academic-assistant-{id(self)}",
            "groups_id": [Command.set([self.env.ref("base.group_user").id])],
        })
        service = AcademicAssistantService(self.env(user=user))
        with self.assertRaises(AccessError):
            service.answer("Berapa jumlah mahasiswa?")

    def test_page_context_is_whitelisted_and_record_access_is_checked(self):
        safe = AcademicAssistantService._sanitize_page_context({
            "model": "res.users",
            "res_id": 1,
        })
        self.assertEqual(safe, {})

        service = AcademicAssistantService(self.env)
        with self.assertRaises(AccessError):
            service.answer(
                "Bagaimana performanya?",
                page_context={
                    "model": "erpobe.master.mahasiswa",
                    "res_id": 2147483647,
                },
            )
