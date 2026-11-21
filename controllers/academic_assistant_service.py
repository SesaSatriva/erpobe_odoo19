import re

from odoo.exceptions import AccessError

from .assistant_intents import detect_intent, normalize_keyword


_CONTEXT_MODELS = {
    "erpobe.master.mahasiswa": ("name", "prodi_id", "angkatan", "status_akademik"),
    "erpobe.master.dosen": ("name", "prodi_ids", "active"),
    "erpobe.master.prodi": ("name", "kode", "fakultas_id"),
    "erpobe.master.matakuliah": ("name", "kode_mk", "prodi_id", "semester"),
    "erpobe.akademik.rps": (
        "matakuliah_id", "status", "weight_status", "cpmk_ids",
        "mk_cpl_mapping_ids",
    ),
    "erpobe.akademik.cpl": ("name", "kode_cpl", "prodi_id"),
    "erpobe.akademik.cpmk": ("name", "kode_cpmk", "mk_id"),
}

_SUGGESTIONS = {
    "general": [
        "Berapa jumlah mahasiswa aktif?",
        "Bagaimana capaian CPL?",
        "Tampilkan RPS yang belum divalidasi.",
        "Mata kuliah mana dengan capaian CPMK terendah?",
    ],
    "student": [
        "Berapa jumlah mahasiswa aktif?",
        "Tampilkan mahasiswa angkatan 2022.",
        "Berapa rata-rata IPK mahasiswa?",
    ],
    "lecturer": [
        "Berapa jumlah dosen?",
        "Tampilkan dosen aktif.",
        "Siapa dosen dengan beban mengajar tertinggi?",
    ],
    "rps": [
        "Berapa jumlah RPS?",
        "Tampilkan RPS yang belum divalidasi.",
        "RPS mana yang bobotnya belum lengkap?",
    ],
    "cpl": [
        "Berapa jumlah CPL?",
        "Bagaimana capaian CPL?",
        "CPL mana yang paling rendah?",
    ],
    "cpmk": [
        "Berapa jumlah CPMK?",
        "Bagaimana capaian CPMK?",
        "CPMK mana yang paling rendah?",
    ],
    "course": [
        "Berapa jumlah mata kuliah?",
        "Tampilkan mata kuliah semester 3.",
        "Bagaimana statistik nilai mata kuliah?",
    ],
}


class AcademicAssistantService:
    def __init__(self, env):
        self.env = env

    def answer(self, question, conversation_context=None, page_context=None):
        context = self._sanitize_conversation_context(conversation_context)
        page = self._sanitize_page_context(page_context)
        detected = detect_intent(question, context, page)
        detected["filters"] = {
            key: detected[key]
            for key in (
                "cohort", "program", "course", "search_name",
                "gpa_operator", "gpa_value", "semester", "rps_weight_issue",
                "active_only", "count_requested",
            )
        }

        if detected["intent_id"] == "clarify":
            return self._response(
                "clarification",
                "Perlu diperjelas",
                "Pertanyaan memuat beberapa kemungkinan. Sebutkan domainnya "
                "(mahasiswa, dosen, RPS, CPL, CPMK, atau mata kuliah) dan "
                "informasi yang ingin dicari.",
                context=detected,
            )
        if detected["intent_id"] == "help":
            return self._help_response()
        if detected["intent_id"] == "academic_comparison":
            return self._response(
                "warning",
                "Perbandingan belum didukung",
                "Data model yang tersedia belum menyediakan dasar periode "
                "perbandingan yang konsisten. Saya tidak akan menyimpulkan "
                "perbandingan tanpa data tersebut.",
                context=detected,
            )

        context_record = self._context_record(page)
        handlers = {
            "student_count": self._student_query,
            "student_active": self._student_query,
            "student_search": self._student_query,
            "student_by_cohort": self._student_query,
            "student_by_program": self._student_query,
            "student_gpa_statistics": self._student_gpa,
            "student_gpa_below": self._student_gpa,
            "student_academic_performance": self._student_performance,
            "lecturer_count": self._lecturer_query,
            "lecturer_active": self._lecturer_query,
            "lecturer_search": self._lecturer_query,
            "lecturer_by_program": self._lecturer_query,
            "lecturer_workload": self._lecturer_workload,
            "program_count": self._program_query,
            "program_statistics": self._program_query,
            "program_student_distribution": self._program_query,
            "faculty_statistics": self._program_query,
            "rps_count": self._rps_query,
            "rps_search": self._rps_query,
            "rps_unvalidated": self._rps_query,
            "rps_by_course": self._rps_query,
            "rps_details": self._rps_details,
            "cpl_count": self._outcome_query,
            "cpl_statistics": self._outcome_query,
            "cpl_achievement": self._outcome_query,
            "cpl_lowest_achievement": self._outcome_query,
            "cpl_by_program": self._outcome_query,
            "cpl_details": self._outcome_query,
            "cpmk_count": self._outcome_query,
            "cpmk_statistics": self._outcome_query,
            "cpmk_achievement": self._outcome_query,
            "cpmk_lowest_achievement": self._outcome_query,
            "cpmk_by_course": self._outcome_query,
            "cpmk_details": self._outcome_query,
            "course_count": self._course_query,
            "course_search": self._course_query,
            "course_statistics": self._course_query,
            "course_performance": self._course_query,
            "assessment_statistics": self._assessment_statistics,
            "academic_summary": self._academic_summary,
            "dashboard_summary": self._academic_summary,
        }
        handler = handlers.get(detected["intent_id"])
        if not handler:
            return self._response(
                "warning",
                "Intent belum didukung",
                "Saya belum memiliki fungsi terverifikasi untuk pertanyaan itu.",
                context=detected,
            )
        return handler(detected, page, context_record)

    @staticmethod
    def _sanitize_conversation_context(context):
        if not isinstance(context, dict):
            return {}
        allowed = {"intent_id", "entity_kind", "entity_code", "entity_text"}
        safe = {
            key: value[:100] if isinstance(value, str) else value
            for key, value in context.items()
            if key in allowed and isinstance(value, (str, int, float, bool))
        }
        if safe.get("intent_id") not in {
            "course_search", "cpl_achievement", "cpmk_achievement",
            "cpl_details", "cpmk_details", "rps_details",
            "student_academic_performance",
        }:
            return {}
        entity_kind = safe.get("entity_kind")
        code = safe.get("entity_code")
        if code:
            patterns = {
                "course": r"[A-Z]{1,8}[-/]?\d{2,5}[A-Z]?",
                "cpl": r"CPL-?[A-Z0-9]{1,20}",
                "cpmk": r"CPMK-?[A-Z0-9]{1,20}",
            }
            if (
                entity_kind not in patterns
                or not isinstance(code, str)
                or not re.fullmatch(patterns[entity_kind], code.upper())
            ):
                safe.pop("entity_code", None)
                safe.pop("entity_kind", None)
        if isinstance(safe.get("entity_text"), str):
            safe["entity_text"] = normalize_keyword(safe["entity_text"])[:100]
        return safe

    @staticmethod
    def _sanitize_page_context(page_context):
        if not isinstance(page_context, dict):
            return {}
        model = page_context.get("model")
        if model not in _CONTEXT_MODELS:
            return {}
        record_id = page_context.get("res_id")
        if isinstance(record_id, bool) or not isinstance(record_id, int) or record_id <= 0:
            record_id = False
        return {
            "model": model,
            "res_id": record_id,
            "view_type": (
                page_context.get("view_type", "")[:20]
                if isinstance(page_context.get("view_type"), str)
                else ""
            ),
        }

    def _context_record(self, page):
        if not page.get("res_id"):
            return self.env[page["model"]].browse() if page.get("model") else False
        model = self.env[page["model"]]
        record = model.search([("id", "=", page["res_id"])], limit=1)
        if not record:
            raise AccessError("Record context tidak dapat diakses.")
        return record

    def _response(
        self, response_type, title, message, data=None, source="", context=None,
        suggestions=None,
    ):
        intent_id = (context or {}).get("intent_id", "")
        domain = intent_id.split("_", 1)[0]
        return {
            "type": response_type,
            "title": title,
            "message": message,
            "data": data or {},
            "source": source,
            "context": {
                key: value
                for key, value in (context or {}).items()
                if key in {"intent_id", "entity_kind", "entity_code", "entity_text"}
            },
            "suggested_questions": suggestions or _SUGGESTIONS.get(
                domain, _SUGGESTIONS["general"]
            ),
        }

    def _assistant_grade_domain(self, domain):
        user = self.env.user
        if (
            user.has_group("erpobe.group_dosen")
            and not user.has_group("erpobe.group_admin")
            and not user.has_group("erpobe.group_superadmin")
            and not user.has_group("base.group_system")
        ):
            domain.append(("prodi_id", "in", user.erpobe_prodi_ids.ids))
        return domain

    def _help_response(self):
        return self._response(
            "suggestion",
            "Academic Assistant",
            "Saya menggunakan pencocokan aturan dan data ORM yang dapat Anda "
            "akses. Saya dapat mencari mahasiswa, dosen, program studi, mata "
            "kuliah, RPS, serta ringkasan CPL/CPMK. Perbandingan antarperiode "
            "belum didukung.",
            suggestions=_SUGGESTIONS["general"],
        )

    def _resolve_program(self, text):
        Program = self.env["erpobe.master.prodi"]
        if not Program.has_access("read"):
            raise AccessError("Akun tidak dapat membaca program studi.")
        programs = Program.search([("active", "=", True)], order="name")
        if text:
            query = normalize_keyword(text)
            if not query:
                return Program.browse()
            matches = programs.filtered(
                lambda program: query in normalize_keyword(program.name)
                or query in normalize_keyword(program.kode)
            )
        else:
            matches = programs.browse()
        if len(matches) > 1:
            return None
        return matches

    def _program_filter(self, detected, page, context_record):
        text = detected["filters"]["program"]
        if not text and page.get("model") == "erpobe.master.prodi":
            return context_record
        if not text:
            if detected["intent_id"] not in {
                "student_by_program", "lecturer_by_program", "cpl_by_program",
            }:
                return self.env["erpobe.master.prodi"].browse()
            text = self._matching_program_name(detected)
            if text is None:
                return None
        return self._resolve_program(text)

    def _matching_program_name(self, detected):
        Program = self.env["erpobe.master.prodi"]
        if not Program.has_access("read"):
            raise AccessError("Akun tidak dapat membaca program studi.")
        question = detected.get("normalized_question", "")
        programs = self.env["erpobe.master.prodi"].search(
            [("active", "=", True)], order="name"
        )
        matches = programs.filtered(
            lambda program: (
                normalize_keyword(program.name) in question
                or normalize_keyword(program.kode) in question
            )
        )
        if len(matches) > 1:
            return None
        return matches.name if matches else ""

    def _student_query(self, detected, page, context_record):
        Student = self.env["erpobe.master.mahasiswa"]
        filters = detected["filters"]
        domain = []
        if filters["active_only"]:
            domain.append(("status_akademik", "=", "aktif"))
        if filters["cohort"] is not None:
            domain.append(("angkatan", "=", filters["cohort"]))
        program = self._program_filter(detected, page, context_record)
        if program is None:
            return self._clarify("Nama program studi cocok dengan lebih dari satu data.")
        if filters["program"] and not program:
            return self._clarify(
                "Program studi yang disebut tidak ditemukan dalam cakupan Anda."
            )
        if program:
            domain.append(("prodi_id", "=", program.id))
        elif detected["intent_id"] in {"student_by_program"}:
            return self._clarify("Sebutkan nama program studi yang ingin dicari.")
        if filters["search_name"]:
            domain.append(("name", "ilike", filters["search_name"]))

        total = Student.search_count(domain)
        records = Student.search(domain, order="name, id", limit=10)
        rows = [
            [
                record.name,
                str(record.angkatan or "-"),
                dict(record._fields["status_akademik"].selection).get(
                    record.status_akademik, "-"
                ),
            ]
            for record in records
        ]
        is_count = (
            detected["intent_id"] == "student_count"
            or filters["count_requested"]
        )
        title = "Statistik mahasiswa" if is_count else "Daftar mahasiswa"
        if is_count:
            return self._response(
                "statistic",
                title,
                "Jumlah mahasiswa yang dapat diakses sesuai filter.",
                {"total": total},
                "erpobe.master.mahasiswa",
                detected,
            )
        return self._response(
            "table",
            title,
            f"Menampilkan {len(rows)} dari {total} mahasiswa yang dapat diakses.",
            {
                "columns": ["Nama", "Angkatan", "Status akademik"],
                "rows": rows,
                "total": total,
            },
            "erpobe.master.mahasiswa",
            detected,
        )

    def _student_gpa(self, detected, _page, _context_record):
        filters = detected["filters"]
        threshold = filters["gpa_value"]
        domain = []
        if filters["cohort"] is not None:
            domain.append(("angkatan", "=", filters["cohort"]))
        if filters["active_only"]:
            domain.append(("mahasiswa_id.status_akademik", "=", "aktif"))
        if filters["search_name"]:
            domain.append(("mahasiswa_id.name", "ilike", filters["search_name"]))
        program = self._program_filter(detected, _page, _context_record)
        if program is None:
            return self._clarify(
                "Nama program studi cocok dengan lebih dari satu data."
            )
        if filters["program"] and not program:
            return self._clarify(
                "Program studi yang disebut tidak ditemukan dalam cakupan Anda."
            )
        if program:
            domain.append(("prodi_id", "=", program.id))
        if detected["intent_id"] == "student_gpa_below":
            if filters["gpa_operator"] not in {"<", ">"}:
                return self._clarify(
                    "Sebutkan apakah batas IPK yang dimaksud di bawah atau di atas."
                )
            if threshold is None or not 0 <= threshold <= 4:
                return self._clarify("Masukkan batas IPK yang valid, antara 0 dan 4.")
            operator = "<" if filters["gpa_operator"] == "<" else ">"
            domain.append(("ipk", operator, threshold))
            reports = self.env["erpobe.report.khs"].search(
                domain, order="ipk asc, mahasiswa_id", limit=10
            )
            total = self.env["erpobe.report.khs"].search_count(domain)
            rows = [
                [
                    report.mahasiswa_id.name,
                    f"{report.ipk:.2f}",
                ]
                for report in reports
            ]
            return self._response(
                "table",
                "Mahasiswa berdasarkan IPK",
                f"Menampilkan {len(rows)} dari {total} data yang dapat diakses.",
                {"columns": ["Nama", "IPK"], "rows": rows, "total": total},
                "erpobe.report.khs.ipk",
                detected,
            )
        result = self.env["erpobe.report.khs"]._read_group(
            domain, aggregates=["ipk:avg", "__count"]
        )
        average, total = result[0] if result else (0.0, 0)
        return self._response(
            "statistic",
            "Statistik IPK",
            "Rata-rata menggunakan field IPK yang dihitung oleh transkrip.",
            {"average_ipk": round(average or 0.0, 2), "total": total},
            "erpobe.report.khs.ipk",
            detected,
        )

    def _student_performance(self, detected, page, context_record):
        if page.get("model") != "erpobe.master.mahasiswa" or not context_record:
            return self._clarify(
                "Buka record mahasiswa yang dapat Anda akses, atau tanyakan "
                "statistik IPK secara umum."
            )
        report = self.env["erpobe.report.khs"].search(
            [("mahasiswa_id", "=", context_record.id)], limit=1
        )
        facts = {
            "mahasiswa": context_record.name,
            "angkatan": context_record.angkatan,
            "status_akademik": dict(
                context_record._fields["status_akademik"].selection
            ).get(context_record.status_akademik, "-"),
        }
        if report:
            facts.update({
                "ipk": round(report.ipk, 2),
                "sks_lulus": report.total_sks_lulus,
            })
        return self._response(
            "statistic",
            "Performa akademik",
            "Ringkasan ini memakai nilai IPK dan SKS lulus dari transkrip yang "
            "tersedia; assistant tidak menghitung ulang rumus akademik.",
            facts,
            "erpobe.report.khs",
            detected,
        )

    def _lecturer_query(self, detected, page, context_record):
        Lecturer = self.env["erpobe.master.dosen"]
        domain = []
        if detected["filters"]["active_only"]:
            domain.append(("active", "=", True))
        program = self._program_filter(detected, page, context_record)
        if program is None:
            return self._clarify("Nama program studi cocok dengan lebih dari satu data.")
        if detected["filters"]["program"] and not program:
            return self._clarify(
                "Program studi yang disebut tidak ditemukan dalam cakupan Anda."
            )
        if program:
            domain.append(("prodi_ids", "in", program.ids))
        elif detected["intent_id"] == "lecturer_by_program":
            return self._clarify("Sebutkan nama program studi yang ingin dicari.")
        if detected["filters"]["search_name"]:
            domain.append(("name", "ilike", detected["filters"]["search_name"]))
        total = Lecturer.search_count(domain)
        records = Lecturer.search(domain, order="name, id", limit=10)
        rows = [[record.name] for record in records]
        if (
            detected["intent_id"] == "lecturer_count"
            or detected["filters"]["count_requested"]
        ):
            return self._response(
                "statistic",
                "Statistik dosen",
                "Jumlah dosen pada cakupan data yang dapat Anda akses.",
                {"total": total},
                "erpobe.master.dosen",
                detected,
            )
        return self._response(
            "table",
            "Daftar dosen",
            f"Menampilkan {len(rows)} dari {total} dosen yang dapat diakses.",
            {"columns": ["Nama"], "rows": rows, "total": total},
            "erpobe.master.dosen",
            detected,
        )

    def _lecturer_workload(self, detected, _page, _context_record):
        lecturer_domain = []
        program = self._program_filter(detected, _page, _context_record)
        if program is None:
            return self._clarify("Nama program studi cocok dengan lebih dari satu data.")
        if detected["filters"]["program"] and not program:
            return self._clarify(
                "Program studi yang disebut tidak ditemukan dalam cakupan Anda."
            )
        if program:
            lecturer_domain.append(("prodi_ids", "in", program.ids))
        if detected["filters"]["search_name"]:
            lecturer_domain.append((
                "name", "ilike", detected["filters"]["search_name"],
            ))
        if detected["filters"]["active_only"]:
            lecturer_domain.append(("active", "=", True))
        lecturers = self.env["erpobe.master.dosen"].search(
            lecturer_domain, order="name, id"
        )
        Course = self.env["erpobe.master.matakuliah"]
        course_domain = [("prodi_id", "=", program.id)] if program else []
        counts_by_lecturer = {}
        offset = 0
        while True:
            courses = Course.search(
                course_domain, order="id", offset=offset, limit=500
            )
            if not courses:
                break
            for course in courses:
                assigned_ids = set(course.tim_pengampu_ids.ids)
                if course.koordinator_id:
                    assigned_ids.add(course.koordinator_id.id)
                for lecturer_id in assigned_ids:
                    counts_by_lecturer[lecturer_id] = (
                        counts_by_lecturer.get(lecturer_id, 0) + 1
                    )
            offset += len(courses)
        counts = [
            (counts_by_lecturer.get(lecturer.id, 0), lecturer.name)
            for lecturer in lecturers
        ]
        counts.sort(key=lambda item: (-item[0], item[1]))
        rows = [[name, str(total)] for total, name in counts[:10]]
        return self._response(
            "table",
            "Beban mata kuliah dosen",
            "Beban dihitung sebagai jumlah mata kuliah yang memiliki dosen "
            "sebagai koordinator atau anggota tim pengampu.",
            {"columns": ["Dosen", "Mata kuliah"], "rows": rows, "total": len(lecturers)},
            "erpobe.master.matakuliah.koordinator_id/tim_pengampu_ids",
            detected,
        )

    def _program_query(self, detected, page, _context_record):
        Prodi = self.env["erpobe.master.prodi"]
        if detected["intent_id"] == "program_count":
            return self._response(
                "statistic",
                "Jumlah program studi",
                "Jumlah program studi aktif yang dapat Anda akses.",
                {"total": Prodi.search_count([("active", "=", True)])},
                "erpobe.master.prodi",
                detected,
            )
        if detected["intent_id"] in {
            "program_student_distribution", "faculty_statistics",
        }:
            if detected["intent_id"] == "program_student_distribution":
                programs = Prodi.search([("active", "=", True)], order="name", limit=100)
                total_groups = Prodi.search_count([("active", "=", True)])
                rows = [
                    [
                        program.kode,
                        program.name,
                        str(self.env["erpobe.master.mahasiswa"].search_count([
                            ("prodi_id", "=", program.id),
                        ])),
                    ]
                    for program in programs
                ]
                rows.sort(key=lambda row: (-int(row[2]), row[1]))
                title = "Distribusi mahasiswa per program studi"
                source = "erpobe.master.mahasiswa.prodi_id"
            else:
                faculties = self.env["erpobe.master.fakultas"].search(
                    [], order="name", limit=50
                )
                total_groups = self.env["erpobe.master.fakultas"].search_count([])
                rows = []
                for faculty in faculties:
                    programs = Prodi.search([("fakultas_id", "=", faculty.id)])
                    count = self.env["erpobe.master.mahasiswa"].search_count([
                        ("prodi_id", "in", programs.ids),
                    ])
                    rows.append([faculty.kode, faculty.name, str(count)])
                title = "Distribusi mahasiswa per fakultas"
                source = "erpobe.master.fakultas / erpobe.master.mahasiswa"
            return self._response(
                "table",
                title,
                f"Menampilkan {len(rows)} dari {total_groups} kelompok yang "
                "dapat Anda akses.",
                {
                    "columns": ["Kode", "Nama", "Mahasiswa"],
                    "rows": rows,
                    "total": total_groups,
                },
                source,
                detected,
            )
        if detected["intent_id"] == "program_statistics":
            records = Prodi.search([("active", "=", True)], order="name", limit=100)
            total = Prodi.search_count([("active", "=", True)])
            rows = [[record.kode, record.name] for record in records]
            return self._response(
                "table",
                "Program studi",
                f"Menampilkan {len(rows)} dari {total} program studi aktif "
                "pada cakupan Anda.",
                {"columns": ["Kode", "Nama"], "rows": rows, "total": total},
                "erpobe.master.prodi",
                detected,
            )
        return self._academic_summary(detected, page, False)

    def _rps_query(self, detected, page, _context_record):
        Rps = self.env["erpobe.akademik.rps"]
        filters = detected["filters"]
        domain = []
        if detected["intent_id"] == "rps_unvalidated":
            if filters["rps_weight_issue"]:
                domain.append(("weight_status", "in", ["missing", "incomplete"]))
            else:
                domain.append(("status", "in", ["draft", "review"]))
        if filters["cohort"] is not None:
            domain.append((
                "tahun_ajaran_id.tahun_ajaran",
                "ilike",
                str(filters["cohort"]),
            ))
        if filters["semester"]:
            if filters["semester"] in {"ganjil", "genap"}:
                domain.append(("semester_akademik", "=", filters["semester"]))
            else:
                domain.append(("semester", "=", int(filters["semester"])))
        course_text = filters["course"]
        if detected["entity_kind"] == "course":
            course_text = detected["entity_code"]
        course_context = (
            detected if course_text or detected["intent_id"] == "rps_by_course"
            else None
        )
        course = self._resolve_course(course_text, course_context)
        if course is None:
            return self._clarify("Nama mata kuliah cocok dengan lebih dari satu data.")
        if course_text and not course:
            return self._clarify(
                "Mata kuliah yang disebut tidak ditemukan dalam cakupan Anda."
            )
        if course:
            domain.append(("matakuliah_id", "=", course.id))
        elif detected["intent_id"] == "rps_by_course":
            return self._clarify("Sebutkan nama atau kode mata kuliah.")

        total = Rps.search_count(domain)
        records = Rps.search(domain, order="matakuliah_name, version desc", limit=10)
        if detected["intent_id"] == "rps_count":
            return self._response(
                "statistic",
                "Jumlah RPS",
                "Jumlah RPS pada cakupan data yang dapat Anda akses.",
                {"total": total},
                "erpobe.akademik.rps",
                detected,
            )
        rows = [
            [
                record.kode_mk or "",
                record.matakuliah_name or "",
                record.version,
                dict(record._fields["status"].selection).get(record.status, ""),
                dict(record._fields["weight_status"].selection).get(
                    record.weight_status, "",
                ),
            ]
            for record in records
        ]
        return self._response(
            "table",
            "Daftar RPS",
            f"Menampilkan {len(rows)} dari {total} RPS yang sesuai.",
            {
                "columns": ["Kode MK", "Mata kuliah", "Versi", "Status", "Bobot"],
                "rows": rows,
                "total": total,
            },
            "erpobe.akademik.rps",
            detected,
        )

    def _resolve_course(self, text, detected=None):
        Course = self.env["erpobe.master.matakuliah"]
        if not text and not detected:
            return Course.browse()
        code = (
            detected.get("entity_code")
            if detected and detected.get("entity_kind") == "course"
            else ""
        )
        if text:
            query = normalize_keyword(text)
            if not query:
                return Course.browse()
            if code:
                matches = Course.search(
                    [
                        ("active", "=", True),
                        ("kode_mk", "ilike", code),
                    ],
                    order="name",
                    limit=2,
                )
                if matches:
                    return None if len(matches) > 1 else matches
            matches = Course.search(
                [
                    ("active", "=", True),
                    ("name", "ilike", query),
                ],
                order="name",
                limit=2,
            )
        elif detected:
            question = detected.get("normalized_question", "")
            courses = Course.search(
                [("active", "=", True)], order="name", limit=1000
            )
            matches = courses.filtered(
                lambda course: (
                    normalize_keyword(course.name) in question
                    or normalize_keyword(course.kode_mk) in question
                )
            )
        else:
            matches = courses.browse()
        if len(matches) > 1:
            return None
        return matches

    def _rps_details(self, detected, page, context_record):
        if page.get("model") != "erpobe.akademik.rps" or not context_record:
            return self._clarify("Buka record RPS yang dapat Anda akses terlebih dahulu.")
        course = context_record.matakuliah_id
        cpmks = context_record.cpmk_ids
        cpls = context_record.mk_cpl_mapping_ids.mapped("cpl_id")
        return self._response(
            "statistic",
            "Pemetaan pada RPS",
            "Ringkasan ini hanya memeriksa relasi yang tersimpan pada record RPS; "
            "assistant tidak menyimpulkan validitas pemetaan akademik.",
            {
                "mata_kuliah": course.display_name,
                "status_rps": dict(context_record._fields["status"].selection).get(
                    context_record.status, "",
                ),
                "cpmk_terkait": len(cpmks),
                "cpl_terkait": len(cpls),
                "cpmk": [f"{item.kode_cpmk}: {item.name}" for item in cpmks[:10]],
                "cpl": [f"{item.kode_cpl}: {item.name}" for item in cpls[:10]],
            },
            "erpobe.akademik.rps.cpmk_ids/mk_cpl_mapping_ids",
            detected,
        )

    def _outcome_query(self, detected, page, context_record):
        is_cpl = detected["intent_id"].startswith("cpl_")
        model_name = "erpobe.akademik.cpl" if is_cpl else "erpobe.akademik.cpmk"
        code_field = "kode_cpl" if is_cpl else "kode_cpmk"
        name_field = "name"
        score_field = "nilai_cpl" if is_cpl else "nilai_cpmk"
        grade_model_name = "erpobe.grade.cpl" if is_cpl else "erpobe.grade.cpmk"
        relation_field = "cpl_id" if is_cpl else "cpmk_id"
        Model = self.env[model_name]
        Grade = self.env[grade_model_name]
        domain = []

        if page.get("model") == model_name and context_record:
            domain.append(("id", "=", context_record.id))
        if page.get("model") == "erpobe.master.prodi" and context_record and is_cpl:
            domain.append(("prodi_id", "=", context_record.id))
        if page.get("model") == "erpobe.master.matakuliah" and context_record and not is_cpl:
            domain.append(("mk_id", "=", context_record.id))

        if detected["intent_id"] == "cpl_by_program" or detected["filters"]["program"]:
            program = self._program_filter(detected, page, context_record)
            if program is None:
                return self._clarify("Nama program studi cocok dengan lebih dari satu data.")
            if detected["filters"]["program"] and not program:
                return self._clarify(
                    "Program studi yang disebut tidak ditemukan dalam cakupan Anda."
                )
            if detected["intent_id"] == "cpl_by_program" and not program:
                return self._clarify("Sebutkan nama program studi yang ingin dianalisis.")
            if program:
                domain.append(("prodi_id", "=", program.id))
        if not is_cpl and detected["intent_id"] == "cpmk_by_course":
            course = self._resolve_course(
                detected["filters"]["course"],
                detected,
            )
            if course is None:
                return self._clarify("Nama mata kuliah cocok dengan lebih dari satu data.")
            if not course:
                return self._clarify("Sebutkan nama atau kode mata kuliah.")
            domain.append(("mk_id", "=", course.id))

        if detected["entity_code"] and detected["entity_kind"] == ("cpl" if is_cpl else "cpmk"):
            domain.append((code_field, "ilike", detected["entity_code"]))
        elif detected["entity_text"] and detected["entity_kind"] == ("cpl" if is_cpl else "cpmk"):
            domain.extend([
                "|",
                (code_field, "ilike", detected["entity_text"]),
                (name_field, "ilike", detected["entity_text"]),
            ])
        elif detected["entity_code"] and detected["entity_kind"] in {"cpl", "cpmk"}:
            Mapping = self.env["erpobe.akademik.cpl.mk.cpmk"]
            mapping_code_field = (
                "cpmk_id.kode_cpmk" if is_cpl else "cpl_id.kode_cpl"
            )
            mappings = Mapping.search([
                (mapping_code_field, "ilike", detected["entity_code"]),
            ])
            domain.append((
                "id",
                "in",
                mappings.mapped("cpl_id" if is_cpl else "cpmk_id").ids,
            ))

        outcomes = Model.search(domain, order=f"{code_field}, id", limit=100)
        total_outcomes = Model.search_count(domain)
        if detected["intent_id"].endswith("_count"):
            return self._response(
                "statistic",
                f"Jumlah {'CPL' if is_cpl else 'CPMK'}",
                "Jumlah outcome pada cakupan data yang dapat Anda akses.",
                {"total": total_outcomes},
                model_name,
                detected,
            )
        if not outcomes:
            return self._response(
                "warning",
                f"{'CPL' if is_cpl else 'CPMK'} belum ditemukan",
                "Tidak ada data yang cocok pada cakupan yang dapat Anda akses.",
                source=model_name,
                context=detected,
            )
        if total_outcomes > len(outcomes):
            return self._response(
                "clarification",
                "Persempit cakupan analisis",
                f"Ada {total_outcomes} outcome yang cocok. Untuk menghindari "
                "statistik parsial, pilih program studi, mata kuliah, atau kode "
                "CPL/CPMK yang lebih spesifik.",
                source=model_name,
                context=detected,
            )

        grade_domain = self._assistant_grade_domain([
            ("is_available", "=", True),
            (relation_field, "in", outcomes.ids),
        ])
        if detected["intent_id"].endswith("_lowest_achievement"):
            grouped = Grade._read_group(
                grade_domain,
                groupby=[relation_field],
                aggregates=[f"{score_field}:avg", "__count"],
                limit=1000,
            )
            grouped.sort(key=lambda item: item[1] if item[1] is not None else float("inf"))
            lowest = grouped[:5]
            rows = [
                [
                    item[0][code_field],
                    item[0][name_field],
                    f"{item[1]:.2f}" if item[1] is not None else "-",
                    str(item[2]),
                ]
                for item in lowest
            ]
            return self._response(
                "table",
                f"Capaian {'CPL' if is_cpl else 'CPMK'} terendah",
                "Urutan menggunakan rata-rata field capaian tersimpan yang tersedia.",
                {
                    "columns": ["Kode", "Nama", "Rata-rata", "Data tersedia"],
                    "rows": rows,
                    "total": len(rows),
                },
                f"{grade_model_name}.{score_field}",
                detected,
            )

        aggregate = Grade._read_group(
            grade_domain, aggregates=[f"{score_field}:avg", "__count"]
        )
        average, count = aggregate[0] if aggregate else (0.0, 0)
        achieved = Grade.search_count(grade_domain + [("status_capaian", "=", "tercapai")])
        rows = [
            [
                getattr(outcome, code_field),
                getattr(outcome, name_field),
                f"{outcome.target_nilai:.2f}",
            ]
            for outcome in outcomes[:10]
        ]
        return self._response(
            "statistic",
            f"Statistik {'CPL' if is_cpl else 'CPMK'}",
            "Rata-rata menggunakan field capaian tersimpan; persentase tercapai "
            "menggunakan status_capaian yang dihitung oleh model.",
            {
                "total_outcome": Model.search_count(domain),
                "average_score": round(average or 0.0, 2),
                "records_available": count,
                "records_achieved": achieved,
                "outcomes": rows,
            },
            f"{grade_model_name}.{score_field}/status_capaian",
            detected,
        )

    def _course_query(self, detected, page, context_record):
        Course = self.env["erpobe.master.matakuliah"]
        domain = []
        if page.get("model") == "erpobe.master.prodi" and context_record:
            domain.append(("prodi_id", "=", context_record.id))
        if detected["filters"]["semester"]:
            if not detected["filters"]["semester"].isdigit():
                return self._clarify(
                    "Mata kuliah memakai semester kurikulum 1 sampai 8. "
                    "Sebutkan nomor semesternya."
                )
            domain.append((
                "semester", "=", int(detected["filters"]["semester"]),
            ))
        course_text = detected["filters"]["course"]
        if detected["entity_kind"] == "course":
            course_text = detected["entity_code"]
        course_context = (
            detected if course_text or detected["intent_id"] == "course_search"
            else None
        )
        course = self._resolve_course(course_text, course_context)
        if course is None:
            return self._clarify("Nama mata kuliah cocok dengan lebih dari satu data.")
        if course_text and not course:
            return self._clarify(
                "Mata kuliah yang disebut tidak ditemukan dalam cakupan Anda."
            )
        if course:
            domain.append(("id", "=", course.id))
        if detected["entity_code"]:
            domain.append(("kode_mk", "ilike", detected["entity_code"]))
        if detected["filters"]["search_name"] and not course:
            name = detected["filters"]["search_name"]
            domain.extend(["|", ("name", "ilike", name), ("kode_mk", "ilike", name)])

        if detected["intent_id"] in {
            "course_statistics", "course_performance",
        }:
            Grade = self.env["erpobe.grade.mk"]
            grade_domain = self._assistant_grade_domain([
                ("is_available", "=", True),
            ])
            if domain:
                grade_domain.append(("mk_id", "in", Course.search(domain).ids))
            if detected["intent_id"] == "course_performance":
                grouped = Grade._read_group(
                    grade_domain,
                    groupby=["mk_id"],
                    aggregates=["nilai_mk:avg", "__count"],
                )
                grouped.sort(
                    key=lambda item: item[1] if item[1] is not None else float("-inf"),
                    reverse=True,
                )
                rows = [
                    [
                        item[0].kode_mk,
                        item[0].name,
                        f"{item[1]:.2f}" if item[1] is not None else "-",
                        str(item[2]),
                    ]
                    for item in grouped[:10]
                ]
                title = "Mata kuliah dengan rata-rata nilai tertinggi"
            else:
                aggregate = Grade._read_group(
                    grade_domain, aggregates=["nilai_mk:avg", "__count"]
                )
                average, count = aggregate[0] if aggregate else (0.0, 0)
                return self._response(
                    "statistic",
                    "Statistik nilai mata kuliah",
                    "Rata-rata menggunakan field nilai_mk yang dihitung model.",
                    {"average_score": round(average or 0.0, 2), "records_available": count},
                    "erpobe.grade.mk.nilai_mk",
                    detected,
                )
            return self._response(
                "table",
                title,
                "Urutan menggunakan nilai_mk tersimpan dari data yang dapat Anda akses.",
                {
                    "columns": ["Kode", "Mata kuliah", "Rata-rata", "Data tersedia"],
                    "rows": rows,
                    "total": len(rows),
                },
                "erpobe.grade.mk.nilai_mk",
                detected,
            )

        total = Course.search_count(domain)
        records = Course.search(domain, order="semester, name, id", limit=10)
        rows = [
            [
                record.kode_mk,
                record.name,
                str(record.sks),
                str(record.semester),
            ]
            for record in records
        ]
        if detected["intent_id"] == "course_count":
            return self._response(
                "statistic",
                "Jumlah mata kuliah",
                "Jumlah mata kuliah pada cakupan data yang dapat Anda akses.",
                {"total": total},
                "erpobe.master.matakuliah",
                detected,
            )
        return self._response(
            "table",
            "Daftar mata kuliah",
            f"Menampilkan {len(rows)} dari {total} mata kuliah yang sesuai.",
            {
                "columns": ["Kode", "Nama", "SKS", "Semester kurikulum"],
                "rows": rows,
                "total": total,
            },
            "erpobe.master.matakuliah",
            detected,
        )

    def _assessment_statistics(self, detected, page, context_record):
        Grade = self.env["erpobe.grade.komponen"]
        domain = self._assistant_grade_domain([
            ("is_graded", "=", True),
            ("origin", "=", "actual"),
        ])
        course_text = detected["filters"]["course"]
        if detected["entity_kind"] == "course":
            course_text = detected["entity_code"]
        course_context = detected if course_text else None
        course = self._resolve_course(course_text, course_context)
        if course is None:
            return self._clarify("Nama mata kuliah cocok dengan lebih dari satu data.")
        if course_text and not course:
            return self._clarify(
                "Mata kuliah yang disebut tidak ditemukan dalam cakupan Anda."
            )
        if course:
            domain.append(("krs_line_id.matakuliah_id", "=", course.id))
        elif page.get("model") == "erpobe.master.matakuliah" and context_record:
            domain.append(("krs_line_id.matakuliah_id", "=", context_record.id))

        grouped = Grade._read_group(
            domain,
            groupby=["komponen_id"],
            aggregates=["nilai:avg", "__count"],
            limit=1000,
        )
        values = Grade._read_group(domain, aggregates=["nilai:avg", "__count"])
        average, total = values[0] if values else (0.0, 0)
        rows = [
            [
                item[0].display_name,
                f"{item[1]:.2f}" if item[1] is not None else "-",
                str(item[2]),
            ]
            for item in grouped
        ]
        return self._response(
            "statistic",
            "Statistik asesmen",
            "Rata-rata memakai nilai komponen yang sudah dinilai dengan sumber "
            "aktual; data simulasi tidak disertakan.",
            {
                "average_score": round(average or 0.0, 2),
                "records_available": total,
                "columns": ["Komponen", "Rata-rata nilai", "Data tersedia"],
                "rows": rows,
            },
            "erpobe.grade.komponen.nilai/is_graded/origin",
            detected,
        )

    def _academic_summary(self, detected, page, _context_record):
        cards = []
        for title, model_name, domain in (
            ("Mahasiswa", "erpobe.master.mahasiswa", []),
            ("Dosen", "erpobe.master.dosen", []),
            ("Program studi", "erpobe.master.prodi", [("active", "=", True)]),
            ("Mata kuliah", "erpobe.master.matakuliah", [("active", "=", True)]),
            ("RPS", "erpobe.akademik.rps", []),
        ):
            model = self.env[model_name]
            if not model.has_access("read"):
                continue
            cards.append([title, model.search_count(domain)])
        if not cards:
            return self._response(
                "warning",
                "Ringkasan tidak tersedia",
                "Akun Anda tidak memiliki akses baca ke model ringkasan akademik.",
                context=detected,
            )
        return self._response(
            "statistic",
            "Ringkasan akademik",
            "Ringkasan hanya mencakup model yang dapat dibaca oleh akun Anda.",
            {"counts": cards},
            "erpobe.master.mahasiswa/dosen/prodi/matakuliah/akademik.rps",
            detected,
        )

    def _clarify(self, message):
        return self._response(
            "clarification",
            "Perlu informasi tambahan",
            message,
        )
