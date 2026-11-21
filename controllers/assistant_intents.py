import re
import unicodedata


INTENT_REGISTRY = {
    "student_count": ("jumlah mahasiswa", "berapa mahasiswa", "total mahasiswa"),
    "student_active": ("mahasiswa aktif", "berapa mahasiswa aktif"),
    "student_search": ("cari mahasiswa", "tampilkan mahasiswa", "daftar mahasiswa"),
    "student_by_cohort": ("mahasiswa angkatan", "angkatan mahasiswa"),
    "student_by_program": (
        "mahasiswa dari prodi",
        "mahasiswa program studi",
        "mahasiswa jurusan",
    ),
    "student_gpa_statistics": (
        "rata rata ipk",
        "rata ipk",
        "statistik ipk mahasiswa",
    ),
    "student_gpa_below": (
        "mahasiswa dengan ipk",
        "ipk di bawah",
        "ipk kurang dari",
        "ipk lebih dari",
        "ipk di atas",
    ),
    "student_academic_performance": (
        "performa akademik",
        "performa saya",
        "bagaimana performanya",
        "berapa nilai saya",
        "nilai saya",
    ),
    "lecturer_count": ("jumlah dosen", "berapa dosen", "total dosen"),
    "lecturer_active": ("dosen aktif", "berapa dosen aktif"),
    "lecturer_search": ("cari dosen", "tampilkan dosen", "daftar dosen"),
    "lecturer_by_program": ("dosen dari prodi", "dosen program studi"),
    "lecturer_workload": (
        "beban mengajar dosen",
        "beban mengajar tertinggi",
        "beban dosen",
    ),
    "program_count": (
        "jumlah program studi",
        "berapa program studi",
        "seluruh program studi",
    ),
    "program_statistics": ("statistik program studi", "ringkasan program studi"),
    "program_student_distribution": (
        "mahasiswa terbanyak",
        "distribusi mahasiswa",
        "mahasiswa per program studi",
    ),
    "faculty_statistics": ("statistik fakultas", "mahasiswa per fakultas"),
    "rps_count": ("jumlah rps", "berapa rps", "total rps"),
    "rps_unvalidated": (
        "rps belum divalidasi",
        "rps yang belum divalidasi",
        "rps belum tervalidasi",
        "rps belum final",
        "rps belum lengkap",
        "rps yang belum lengkap",
    ),
    "rps_search": ("cari rps", "tampilkan rps", "daftar rps"),
    "rps_by_course": ("rps mata kuliah", "rps matkul"),
    "rps_details": ("detail rps", "pemetaan rps", "pemetaan cpl cpmk"),
    "cpl_count": ("jumlah cpl", "berapa cpl", "total cpl"),
    "cpl_lowest_achievement": (
        "cpl paling rendah",
        "cpl mana yang paling rendah",
        "cpl yang paling rendah",
        "cpl terendah",
        "capaian cpl terendah",
    ),
    "cpl_achievement": ("capaian cpl", "ketercapaian cpl", "hasil cpl"),
    "cpl_statistics": ("statistik cpl", "rata rata cpl", "rata cpl"),
    "cpl_by_program": ("cpl program studi", "capaian cpl prodi"),
    "cpl_details": ("detail cpl", "jelaskan cpl", "cpl terkait"),
    "cpmk_count": ("jumlah cpmk", "berapa cpmk", "total cpmk"),
    "cpmk_lowest_achievement": (
        "cpmk paling rendah",
        "cpmk mana yang paling rendah",
        "cpmk yang paling rendah",
        "cpmk terendah",
        "capaian cpmk terendah",
    ),
    "cpmk_achievement": ("capaian cpmk", "ketercapaian cpmk", "hasil cpmk"),
    "cpmk_statistics": ("statistik cpmk", "rata rata cpmk", "rata cpmk"),
    "cpmk_by_course": ("cpmk mata kuliah", "cpmk matkul"),
    "cpmk_details": (
        "detail cpmk",
        "jelaskan cpmk",
        "cpmk yang terkait",
        "capaian mata kuliah",
    ),
    "course_count": (
        "jumlah mata kuliah",
        "berapa mata kuliah",
        "jumlah matkul",
    ),
    "course_search": (
        "cari mata kuliah",
        "tampilkan mata kuliah",
        "daftar mata kuliah",
        "mata kuliah semester",
    ),
    "course_performance": (
        "performa mata kuliah",
        "capaian terbaik",
        "mata kuliah terbaik",
    ),
    "assessment_statistics": (
        "statistik asesmen",
        "hasil asesmen",
        "statistik penilaian",
        "rata rata nilai kelas",
    ),
    "course_statistics": (
        "statistik mata kuliah",
        "rata rata nilai mata kuliah",
    ),
    "academic_summary": (
        "ringkasan akademik",
        "kondisi akademik",
        "ringkasan akademik saat ini",
    ),
    "dashboard_summary": ("ringkasan dashboard", "ringkasan data akademik"),
    "academic_comparison": (
        "bandingkan",
        "perbandingan semester",
        "semester sebelumnya",
        "antarprogram studi",
    ),
    "help": ("bantuan", "apa yang bisa", "bisa dibantu", "fitur assistant"),
}

_INTENT_DOMAIN = {
    name: (
        "student" if name.startswith("student_")
        else "lecturer" if name.startswith("lecturer_")
        else "program" if name.startswith(("program_", "faculty_"))
        else "rps" if name.startswith("rps_")
        else "cpl" if name.startswith("cpl_")
        else "cpmk" if name.startswith("cpmk_")
        else "course" if name.startswith("course_") or name == "assessment_statistics"
        else "analytics" if name in {
            "academic_summary", "dashboard_summary", "academic_comparison",
        }
        else "help"
    )
    for name in INTENT_REGISTRY
}

_ALIASES = {
    "mhs": "mahasiswa",
    "student": "mahasiswa",
    "peserta didik": "mahasiswa",
    "lecturer": "dosen",
    "pengajar": "dosen",
    "tenaga pengajar": "dosen",
    "jurusan": "program studi",
    "prodi": "program studi",
    "matkul": "mata kuliah",
    "course": "mata kuliah",
    "achievement": "capaian",
    "pencapaian": "capaian",
    "hasil": "capaian",
    "cohort": "angkatan",
    "tahun masuk": "angkatan",
}

_STOP_WORDS = {
    "apa", "apakah", "bagaimana", "berapa", "cari", "carikan", "jelaskan",
    "tolong", "tampilkan", "daftar", "tentang", "dari", "untuk", "dengan",
    "pada", "di", "dan", "atau", "saya", "aku", "milik", "punya", "statistik",
    "rata", "rerata", "jumlah", "analisis", "persentase", "ringkasan",
    "capaian", "kompetensi", "lulusan", "mata", "kuliah", "matakuliah",
    "matkul", "kode", "mk", "sks", "prasyarat", "rps", "kurikulum", "semester",
    "cpl", "cpmk", "terkait", "yang", "ada", "ini", "itu", "tersebut",
    "target", "targetnya", "tadi", "mahasiswa", "mhs", "dosen", "pengajar",
    "akademik", "program", "studi", "kelas", "angkatan", "ipk", "ips", "khs",
    "aktif", "belum", "validasi", "divalidasi", "nilai", "dengan", "kurang",
    "lebih", "bawah", "atas", "dari", "paling", "mana",
}


def normalize_keyword(value):
    normalized = unicodedata.normalize("NFKD", value or "")
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii").casefold()
    text = " ".join(re.findall(r"[a-z0-9.,<>]+", ascii_text))
    for alias, canonical in sorted(_ALIASES.items(), key=lambda item: -len(item[0])):
        text = re.sub(rf"\b{re.escape(alias)}\b", canonical, text)
    return " ".join(text.split())


def extract_entities(question):
    normalized = normalize_keyword(question)
    original = unicodedata.normalize("NFKD", question or "")
    original = original.encode("ascii", "ignore").decode("ascii").casefold()
    entities = {
        "entity_kind": "",
        "entity_code": "",
        "entity_text": "",
        "cohort": None,
        "program": "",
        "course": "",
        "search_name": "",
        "gpa_operator": "",
        "gpa_value": None,
        "semester": "",
        "rps_weight_issue": False,
        "active_only": False,
        "count_requested": False,
    }

    outcome_patterns = (
        r"\b(cpl|cpmk)\s*[-:#]\s*([a-z0-9]+)\b",
        r"\b(cpl|cpmk)([a-z]\d*|\d+[a-z]?)\b",
        r"\b(cpl|cpmk)\s+(\d+[a-z]?)\b",
    )
    outcome_match = None
    for pattern in outcome_patterns:
        outcome_match = re.search(pattern, original)
        if outcome_match:
            break
    if outcome_match:
        entities["entity_kind"] = outcome_match.group(1)
        prefix = outcome_match.group(1).upper()
        suffix = outcome_match.group(2).upper()
        separator = "-" if re.search(r"[-:#\s]", outcome_match.group(0)) else ""
        entities["entity_code"] = f"{prefix}{separator}{suffix}"

    course_code = re.search(r"\b([a-z]{1,8}[-/]?\d{2,5}[a-z]?)\b", original)
    if course_code:
        entities["entity_kind"] = "course"
        entities["entity_code"] = course_code.group(1).upper()

    cohort = re.search(r"\b(19\d{2}|20\d{2})\b", normalized)
    if cohort:
        entities["cohort"] = int(cohort.group(1))

    gpa = re.search(
        r"\b(ipk|ips)\b.*?\b(di bawah|dibawah|kurang dari|<|di atas|diatas|"
        r"lebih dari|>)\s*(\d(?:[.,]\d{1,2})?)",
        normalized,
    )
    if gpa:
        entities["gpa_operator"] = "<" if gpa.group(2) in {
            "di bawah", "dibawah", "kurang dari", "<",
        } else ">"
        entities["gpa_value"] = float(gpa.group(3).replace(",", "."))

    semester = re.search(r"\bsemester\s+(ganjil|genap|[1-8])\b", normalized)
    if semester:
        entities["semester"] = semester.group(1)

    name = re.search(
        r"\b(?:cari|tampilkan|nama)\s+(?:mahasiswa|dosen)?\s*"
        r"(?:bernama)?\s+([a-z][a-z .'-]{1,60})",
        normalized,
    )
    if name:
        candidate = name.group(1).strip()
        candidate = re.split(
            r"\b(?:dari|angkatan|prodi|program studi|jurusan|semester)\b",
            candidate,
            maxsplit=1,
        )[0].strip()
        if candidate and candidate not in _STOP_WORDS:
            entities["search_name"] = candidate[:60]

    program = re.search(
        r"\b(?:program studi|prodi|jurusan)\s+(?:dari\s+)?"
        r"([a-z0-9][a-z0-9 .&/-]{1,60})",
        normalized,
    )
    if program:
        entities["program"] = re.split(
            r"\b(?:angkatan|semester|dengan|yang|dan|mata kuliah|dosen)\b",
            program.group(1),
            maxsplit=1,
        )[0].strip()[:60]
    else:
        program_from = re.search(
            r"\b(?:mahasiswa|dosen)\b.*?\bdari\s+"
            r"([a-z0-9][a-z0-9 .&/-]{1,60})",
            normalized,
        )
        if program_from:
            entities["program"] = re.split(
                r"\b(?:angkatan|semester|dengan|yang|dan|mata kuliah)\b",
                program_from.group(1),
                maxsplit=1,
            )[0].strip()[:60]

    course = re.search(
        r"\b(?:mata kuliah|matkul)\s+(?:bernama\s+)?"
        r"([a-z0-9][a-z0-9 .&/-]{1,60})",
        normalized,
    )
    if course:
        entities["course"] = re.split(
            r"\b(?:semester|angkatan|dari prodi|dari program studi|dengan)\b",
            course.group(1),
            maxsplit=1,
        )[0].strip()[:60]

    entities["rps_weight_issue"] = (
        " rps " in f" {normalized} "
        and " lengkap " in f" {normalized} "
        and " belum " in f" {normalized} "
    )
    entities["active_only"] = " aktif " in f" {normalized} "
    entities["count_requested"] = any(
        f" {term} " in f" {normalized} "
        for term in ("berapa", "jumlah", "total")
    )
    return entities


def detect_intent(question, context=None, page_context=None):
    original = (question or "").strip()[:500]
    normalized = normalize_keyword(original)
    padded = f" {normalized} "
    entities = extract_entities(original)
    candidates = []

    for intent, phrases in INTENT_REGISTRY.items():
        matches = [
            len(normalize_keyword(phrase).split())
            for phrase in phrases
            if f" {normalize_keyword(phrase)} " in padded
        ]
        if matches:
            candidates.append((max(matches), intent))

    if entities["gpa_operator"]:
        candidates.append((5, "student_gpa_below"))
    if entities["cohort"] and "mahasiswa" in padded:
        candidates.append((4, "student_by_cohort"))
    if entities["program"] and "mahasiswa" in padded:
        candidates.append((4, "student_by_program"))
    if entities["program"] and "dosen" in padded:
        candidates.append((4, "lecturer_by_program"))
    if "rps" in padded and "belum" in padded and (
        "validasi" in padded or "tervalidasi" in padded
    ):
        candidates.append((5, "rps_unvalidated"))
    if entities["rps_weight_issue"]:
        candidates.append((5, "rps_unvalidated"))
    if "cpl" in padded and any(term in padded for term in ("rendah", "terendah")):
        candidates.append((5, "cpl_lowest_achievement"))
    if "cpmk" in padded and any(term in padded for term in ("rendah", "terendah")):
        candidates.append((5, "cpmk_lowest_achievement"))

    if (
        "mahasiswa" in padded
        and "mata kuliah" in padded
        and ("mengambil" in padded or "dosen" in padded)
    ):
        return {
            **entities,
            "normalized_question": normalized,
            "intent_id": "clarify",
            "intent": "clarify",
            "confidence": 0.0,
        }

    page_context = page_context if isinstance(page_context, dict) else {}
    context_model = page_context.get("model")
    if any(term in padded for term in (
        " bandingkan ", " perbandingan ", " semester sebelumnya ",
    )):
        candidates = [(5, "academic_comparison")]
    if not candidates:
        if any(term in padded for term in (" performa ", " nilainya ", "hasilnya ")):
            candidates.append((3, "student_academic_performance"))
        elif any(term in padded for term in (" paling rendah ", " terendah ")):
            if context_model == "erpobe.akademik.cpl":
                candidates.append((3, "cpl_lowest_achievement"))
            elif context_model == "erpobe.akademik.cpmk":
                candidates.append((3, "cpmk_lowest_achievement"))
        elif context_model == "erpobe.akademik.rps" and "pemetaan" in normalized:
            candidates.append((3, "rps_details"))

    if not candidates and entities["entity_code"]:
        candidates.append((
            3,
            "cpl_details" if entities["entity_kind"] == "cpl"
            else "cpmk_details" if entities["entity_kind"] == "cpmk"
            else "course_search",
        ))

    if candidates:
        highest = max(score for score, _intent in candidates)
        best = {intent for score, intent in candidates if score == highest}
        domains = {_INTENT_DOMAIN[intent] for intent in best}
        if len(best) > 1 and len(domains) > 1:
            return {
                **entities,
                "normalized_question": normalized,
                "intent_id": "clarify",
                "intent": "clarify",
                "confidence": 0.0,
            }
        intent_id = sorted(best)[0]
        confidence = min(1.0, highest / 4)
    else:
        previous = context if isinstance(context, dict) else {}
        previous_intent = previous.get("intent_id")
        if not previous_intent:
            previous_intent = {
                "course": "course_search",
                "cpl": "cpl_achievement",
                "cpmk": "cpmk_achievement",
                "grade": "student_academic_performance",
                "statistics": "academic_summary",
            }.get(previous.get("intent"))
        compatible = {
            "course": "course_search",
            "cpl": "cpl_achievement",
            "cpmk": "cpmk_achievement",
            "rps": "rps_details",
            "student": "student_academic_performance",
            "course_search": "course_search",
            "cpl_achievement": "cpl_achievement",
            "cpmk_achievement": "cpmk_achievement",
            "academic_summary": "academic_summary",
            "cpl_details": "cpl_achievement",
            "cpmk_details": "cpmk_achievement",
        }
        intent_id = compatible.get(previous_intent, previous_intent if previous_intent in INTENT_REGISTRY else "")
        if not intent_id and context_model == "erpobe.master.mahasiswa":
            intent_id = "student_academic_performance"
        if not intent_id and context_model == "erpobe.akademik.rps":
            intent_id = "rps_details"
        if not intent_id and context_model == "erpobe.akademik.cpl":
            intent_id = "cpl_achievement"
        if not intent_id and context_model == "erpobe.akademik.cpmk":
            intent_id = "cpmk_achievement"
        if not intent_id:
            intent_id = "help"
        confidence = 0.75 if intent_id != "help" else 0.0
        if intent_id != "help":
            expected_kind = {
                "course_search": "course",
                "cpl_achievement": "cpl",
                "cpmk_achievement": "cpmk",
            }.get(intent_id, "")
            if previous.get("entity_kind") == expected_kind:
                previous_code = previous.get("entity_code")
                previous_text = previous.get("entity_text")
                if isinstance(previous_code, str):
                    entities["entity_code"] = previous_code[:40]
                    entities["entity_kind"] = expected_kind
                if isinstance(previous_text, str):
                    entities["entity_text"] = previous_text[:100]

    intent = _INTENT_DOMAIN.get(intent_id, "clarify")
    return {
        **entities,
        "normalized_question": normalized,
        "intent_id": intent_id,
        "intent": intent,
        "confidence": confidence,
    }
