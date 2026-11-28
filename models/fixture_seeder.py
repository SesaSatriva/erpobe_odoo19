import re
import unicodedata
from pathlib import Path

from odoo import Command, api, models
from odoo.exceptions import UserError, ValidationError

from .weight_validation import _distribute_percent


PROGRAMS = (
    {
        "slug": "ti",
        "xmlid": "prodi_ti",
        "code": "IN",
        "name": "Teknik Industri",
        "source_url": "https://teknikindustri.ft.uny.ac.id/id/daftar-mata-kuliah-1",
        "teacher_url": "https://teknikindustri.ft.uny.ac.id/id/staff-pengajar",
        "cpl_count": 10,
        "teachers": (
            ("mohammad_adam_jerusalem", "Mohammad Adam Jerusalem, S.T., S.H., M.T., Ph.D.", "Analisis Keputusan"),
            ("nova_suparmanto", "Dr. Nova Suparmanto, M.Sc.", "Sistem Informasi dan ERP; Proses Manufaktur"),
            ("heri_nurdiyanto", "Dr. Ir. Heri Nurdiyanto, S.Kom., M.T.I., M.M.T.", "Sistem Informasi Industri"),
            ("adhe_rizky_anugerah", "Adhe Rizky Anugerah, S.T., M.Eng.", "Manajemen Industri"),
            ("grahita_prisca_brilianti", "Grahita Prisca Brilianti, S.T., M.Sc.", "Human Factor dan Desain Sistem Kerja"),
            ("ummi_fakhriyah_jayatri", "Ummi Fakhriyah Jayatri, S.T., MBA., M.Sc.", "Supply Chain Management"),
            ("dyantika_putry_mahmud", "Dyantika Putry Mahmud, S.Si., MBA.", "Data Analitik"),
            ("anisa_kharismawati", "Anisa Kharismawati, S.T., M.Sc.", "Lean Manufacturing"),
            ("perdana_suteja_putra", "Perdana Suteja Putra, S.T., M.T.", "Desain dan Pengembangan Produk"),
            ("broto_widya_hartanto", "Dr. Broto Widya Hartanto, S.T., M.M., M.Sc.", "Pengembangan Produk Baru; Concurrent Engineering; AI; Sistem Industri Terintegrasi"),
            ("ketut_ima_ismara", "Prof. Dr. Ir. Ketut Ima Ismara, M.Pd., M.Kes.", "K3; Ergonomics"),
            ("muhamad_ali", "Dr. phil. Ir. Muhamad Ali, M.T.", "Fisika; Tenaga Listrik"),
            ("dian_eksana_wibowo", "Ir. Dian Eksana Wibowo, S.T., M.Eng.", "Mekanika dan Material Teknik"),
        ),
    },
    {
        "slug": "el",
        "xmlid": "prodi_el",
        "code": "EL",
        "name": "Teknik Elektro",
        "source_url": "https://teknik-elektro-s1.ft.uny.ac.id/id/daftar-mata-kuliah",
        "teacher_url": "https://teknik-elektro-s1.ft.uny.ac.id/id/capaian-pembelajaran-lulusan",
        "cpl_count": 8,
        "teachers": (
            ("moh_khairudin", "Prof. Ir. Moh. Khairudin, S.Pd., S.T., M.T., Ph.D.", "Otomasi Elektro"),
            ("rustam_asnawi", "Ir. Rustam Asnawi, S.T., M.T., Ph.D.", "Internet of Things"),
            ("sigit_yatmono", "Sigit Yatmono, S.T., M.T.", "Robotika"),
            ("ariadie_chandra_nugraha", "Ariadie Chandra Nugraha, S.T., M.T.", "Kontrol"),
            ("deny_budi_hertanto", "Deny Budi Hertanto, S.Si., M.Kom.", "Software Engineering"),
            ("muhamad_ali", "Dr. Phil. Ir. Muhamad Ali, S.T., M.T.", "Manajemen Industri"),
            ("aji_ery_burhandenny", "Dr. Eng. Aji Ery Burhandenny, S.T., M.AIT.", "Bidang keahlian simulasi belum tercantum pada sumber yang dibaca"),
            ("sarwo_pranoto", "Dr. Eng. Sarwo Pranoto, S.T., M.Eng.", "Bidang keahlian simulasi belum tercantum pada sumber yang dibaca"),
            ("nurman_setiawan", "Nurman Setiawan, S.T., M.Eng.", "Bidang keahlian simulasi belum tercantum pada sumber yang dibaca"),
            ("yudi_utomo_putra", "Yudi Utomo Putra, M.T.", "Bidang keahlian simulasi belum tercantum pada sumber yang dibaca"),
            ("vando_gusti_al_hakim", "Vando Gusti Al Hakim, M.Sc., Ph.D.", "Bidang keahlian simulasi belum tercantum pada sumber yang dibaca"),
            ("rizal_priyambudi", "Rizal Priyambudi, S.Tr.T., M.T.", "Bidang keahlian simulasi belum tercantum pada sumber yang dibaca"),
            ("arif_nugroho", "Dr. Arif Nugroho", "Bidang keahlian simulasi belum tercantum pada sumber yang dibaca"),
            ("fatchul_arifin", "Dr. Ir. Fatchul Arifin, M.T.", "Bidang keahlian simulasi belum tercantum pada sumber yang dibaca"),
        ),
    },
    {
        "slug": "mf",
        "xmlid": "prodi_mf",
        "code": "MF",
        "name": "Teknik Manufaktur",
        "source_url": "http://tman.ft.uny.ac.id/id/rencana-pembelajaran-semester",
        "teacher_url": "https://tman.ft.uny.ac.id/id/dosen-pengajar-program-studi",
        "cpl_count": 12,
        "teachers": (
            ("didik_nurhadiyanto", "Prof. Dr. Eng. Ir. Didik Nurhadiyanto, S.T., M.T.", "Rekayasa Material"),
            ("tiwan", "Prof. Dr. Tiwan, S.T., M.T.", "Teknologi Bahan"),
            ("mujiyono", "Prof. Dr. Ir. Mujiyono, S.T., M.T.", "Rekayasa Material"),
            ("heri_wibowo", "Prof. Dr. Ir. Heri Wibowo, S.T., M.T.", "Metalurgi Las"),
            ("arianto_leman", "Arianto Leman Soemowidagdo, M.T.", "Pengecoran"),
            ("fredy_surahmanto", "Dr. Fredy Surahmanto, S.T., M.Eng.", "Konversi Energi"),
            ("apri_nuryanto", "Ir. Apri Nuryanto, S.T., M.T.", "Desain Produk Manufaktur"),
            ("henny_pratiwi", "Dr. Henny Pratiwi, S.T., M.Eng.", "Material Komposit"),
            ("martinus_heru_palmiyanto", "Dr. Ir. Martinus Heru Palmiyanto, S.T., M.T.", "Karakterisasi Material"),
            ("febrianto_amri_ristadi", "Febrianto Amri Ristadi, S.T., M.Eng.Sc.", "Desain Produk Manufaktur"),
            ("beni_tri_sasongko", "Beni Tri Sasongko, S.T., M.Eng.", "Proses Manufaktur"),
            ("virda_hersy_lutviana_saputri", "Virda Hersy Lutviana Saputri, S.T., M.T.", "Sustainable Manufacturing"),
            ("andhita_mustikaningtyas", "Andhita Mustikaningtyas, S.T., M.T.", "Konversi Energi"),
            ("aulia_majid", "Aulia Majid, S.T., M.Eng.", "Additive Manufacturing"),
        ),
    },
    {
        "slug": "si",
        "xmlid": "prodi_si",
        "code": "SI",
        "name": "Teknik Sipil",
        "source_url": "http://tsipil.ft.uny.ac.id/id/rps-mata-kuliah",
        "teacher_url": "",
        "cpl_count": 10,
        "teachers": tuple(
            (
                f"sipil_sim_{index:02d}",
                f"Dosen Simulasi Sipil {index:02d}",
                "Bidang keahlian simulasi Teknik Sipil",
            )
            for index in range(1, 7)
        ),
    },
)

CIVIL_CPLS = (
    "Menerapkan matematika, sains, dan prinsip rekayasa sipil pada masalah teknik.",
    "Menganalisis data dan hasil eksperimen untuk mendukung solusi rekayasa.",
    "Merancang infrastruktur dengan mempertimbangkan standar dan batasan realistis.",
    "Memilih metode konstruksi yang memperhatikan keselamatan dan lingkungan.",
    "Menggunakan perangkat komputasi dan teknologi informasi untuk analisis teknik.",
    "Mengomunikasikan gagasan dan hasil kerja secara efektif.",
    "Berkolaborasi dan bertanggung jawab dalam tim multidisiplin.",
    "Menjalankan etika profesi serta tanggung jawab sosial.",
    "Mengelola proyek teknik sipil secara terencana dan akuntabel.",
    "Mengembangkan kompetensi profesional melalui pembelajaran sepanjang hayat.",
)

MANUFACTURING_ELECTIVES = (
    "Perancangan dan Produksi Bahan Komposit",
    "Plastic Moulding",
    "High Speed and Precision Machining",
    "Pengelasan Logam Khusus",
    "Teknologi Pengecoran Lanjut",
    "Tribology",
    "Pengukuran Teknik",
    "Product Life Cycle Management",
    "Toleransi Geometri",
    "Total Quality Management",
    "Robotika Industri",
    "Standarisasi dan Sistem Manajemen Mutu",
)

FIRST_NAMES = (
    "Aksa", "Bening", "Cakra", "Dara", "Elang", "Farah", "Gilang", "Hana",
    "Intan", "Jati", "Kirana", "Laras", "Miko", "Nadia", "Oka", "Pertiwi",
    "Qori", "Raka", "Sinta", "Tegar", "Uli", "Vira", "Wahyu", "Yuda", "Zahra",
)
LAST_NAMES = (
    "Arunika", "Baskara", "Cendana", "Dewangga", "Ekaputra", "Fajri", "Gantara",
    "Hapsari", "Iswara", "Jatmiko", "Kusuma", "Laksana", "Mahardika", "Nirmala",
    "Pradana", "Prameswari", "Raharja", "Sasmita", "Utami", "Wicaksana",
    "Yudhistira", "Zahira",
)

WEEK_TOPICS = (
    "orientasi, tujuan, dan ruang lingkup mata kuliah",
    "konsep dasar dan istilah utama",
    "prinsip, model, dan landasan teori",
    "analisis kasus dan identifikasi masalah",
    "metode perancangan dan pemilihan alternatif",
    "penggunaan alat, data, dan perangkat pendukung",
    "integrasi konsep melalui latihan terstruktur",
    "evaluasi tengah semester",
    "penerapan konsep pada studi kasus",
    "analisis hasil dan pertimbangan batasan",
    "kerja kolaboratif dan komunikasi teknis",
    "perancangan solusi dan dokumentasi",
    "pengujian, verifikasi, dan perbaikan",
    "presentasi hasil dan umpan balik",
    "integrasi capaian pembelajaran",
    "evaluasi akhir semester",
)

SOURCE_KIND = {
    "official": "official",
    "mixed": "mixed",
    "dummy": "dummy",
    "derived": "derived",
}
FIXTURE_SEED_VERSION = "5"
FIXTURE_SEED_VERSION_PARAM = "erpobe.fixture.2022_cohort_seed_version"
FIXTURE_COMPONENTS = (
    ("komponen_partisipatif", "Kehadiran", "attendance", 10.0),
    ("fixture_component_quiz", "Kuis", "quiz", 10.0),
    ("komponen_kognitif", "Tugas", "assignment", 15.0),
    ("fixture_component_midterm", "UTS", "midterm", 25.0),
    ("fixture_component_exam", "UAS", "final_exam", 30.0),
    ("fixture_component_presentation", "Presentasi", "presentation", 10.0),
)
ADDITIONAL_COMPONENTS = (
    ("fixture_component_project", "Proyek", "project"),
    ("fixture_component_practicum", "Praktikum", "practicum"),
    ("fixture_component_case_study", "Studi Kasus", "case_study"),
    ("fixture_component_tbp", "TBP", "tbp"),
    ("fixture_component_other", "Aktivitas Penilaian Khusus", "other"),
)


class ErpObeFixtureSeeder(models.AbstractModel):
    _name = "erpobe.fixture.seeder"
    _description = "Pemuat Fixture Akademik OBE"

    @api.model
    def _ensure_fixture_admin_accounts(self):
        return self.env["res.users"].with_context(
            fixture_admins_only=True
        ).load_erpobe_fixture_users()

    @api.model
    def load_2022_cohort_if_enabled(self):
        """Muatan utama fixture akademik angkatan 2022."""
        affected_student_ids = set()
        deferred_seeder = self.with_context(defer_khs_refresh=True)
        deferred_seeder._load_2022_cohort(affected_student_ids)
        importer = self.env["erpobe.official.curriculum"].sudo().with_context(
            defer_khs_refresh=True
        )
        importer._load_all(affected_student_ids)
        importer._sync_khs_batch(affected_student_ids)
        return True

    @api.model
    def _fixture_cohort_is_complete(self):
        imd_model = self.env["ir.model.data"].sudo()
        for config in PROGRAMS:
            prodi = self.env.ref("erpobe.%s" % config["xmlid"])
            data = imd_model.search([
                ("module", "=", "erpobe"),
                ("model", "=", "erpobe.master.mahasiswa"),
                ("name", "=like", "fixture_student_%s_2022_%%" % config["slug"]),
            ])
            students = self.env["erpobe.master.mahasiswa"].sudo().browse(
                data.mapped("res_id")
            ).exists()
            for letter in ("a", "b"):
                rombel = self.env.ref(
                    "erpobe.rombel_%s_2022_%s"
                    % (config["code"].lower(), letter)
                )
                count = len(students.filtered(
                    lambda student: (
                        student.prodi_id == prodi
                        and student.rombel_id == rombel
                    )
                ))
                if count < 30:
                    return False
        return True

    @api.model
    def load_2022_cohort(self):
        """Defer hook-level KHS refreshes until the final student batch."""
        affected_student_ids = set()
        result = self.with_context(defer_khs_refresh=True)._load_2022_cohort(
            affected_student_ids
        )
        if affected_student_ids:
            self.env["erpobe.report.khs"].sudo().action_generate_khs(
                sorted(affected_student_ids)
            )
        return result

    @api.model
    def _load_2022_cohort(self, affected_student_ids):
        params = self.env["ir.config_parameter"].sudo()
        force_seed = self.env.context.get("force_fixture_seed")
        if not force_seed:
            if params.get_param(FIXTURE_SEED_VERSION_PARAM) == FIXTURE_SEED_VERSION:
                if self._fixture_cohort_is_complete():
                    self._ensure_fixture_admin_accounts()
                    return True

            imd_model = self.env["ir.model.data"].sudo()
            final_grade = imd_model.search(
                [
                    ("module", "=", "erpobe"),
                    ("model", "=", "erpobe.grade.cpl"),
                    ("name", "=", "fixture_grade_cpl_mf_2022_025_12"),
                ],
                limit=1,
            )
            final_student = imd_model.search(
                [
                    ("module", "=", "erpobe"),
                    ("model", "=", "erpobe.master.mahasiswa"),
                    ("name", "=", "fixture_student_mf_2022_025"),
                ],
                limit=1,
            )
            current_components = self.env.ref(
                "erpobe.fixture_component_midterm", raise_if_not_found=False
            )
            if (
                not params.get_param(FIXTURE_SEED_VERSION_PARAM)
                and final_grade
                and final_student
                and current_components
                and current_components.tipe == "midterm"
            ):
                report_exists = self.env["erpobe.report.khs"].sudo().search_count(
                    [("mahasiswa_id", "=", final_student.res_id)]
                )
                if report_exists:
                    params.set_param(
                        FIXTURE_SEED_VERSION_PARAM, FIXTURE_SEED_VERSION
                    )
                    self._ensure_fixture_admin_accounts()
                    return True

        source_text = self._read_program_document()
        program_data = self._prepare_program_data(source_text)
        component_ids = self._ensure_components()
        methods = self._ensure_methods()
        grades = self._ensure_grades()
        teacher_map = self._ensure_teachers()

        programs = {}
        all_students = []
        for config in PROGRAMS:
            program = self._ensure_program(
                config,
                program_data[config["slug"]],
                teacher_map,
                component_ids,
                methods,
                grades,
            )
            programs[config["slug"]] = program
            all_students.extend(program["students"])

        self._ensure_fixture_admin_accounts()
        self._create_cpl_results(programs)
        affected_student_ids.update(student.id for student in all_students)
        params.set_param(FIXTURE_SEED_VERSION_PARAM, FIXTURE_SEED_VERSION)
        return True

    def _read_program_document(self):
        path = Path(__file__).resolve().parents[1] / "docs" / "data_prodi.md"
        if not path.is_file():
            raise UserError(f"Dokumen sumber fixture tidak ditemukan: {path}")
        return path.read_text(encoding="utf-8")

    @api.model
    def _prepare_program_data(self, source_text):
        ti_section = self._section(
            source_text, "## 1. Teknik Industri", "## 2. Teknik Elektro"
        )
        el_section = self._section(
            source_text, "## 2. Teknik Elektro", "## 3. Teknik Sipil"
        )
        mf_section = self._section(
            source_text, "## 4. Teknik Manufaktur", "## 5. Daftar mata kuliah"
        )
        civil_section = self._section(
            source_text, "## 3. Teknik Sipil", "## 4. Teknik Manufaktur"
        )
        course_section = self._section(
            source_text, "## 5. Daftar mata kuliah", "## 6. Dosen per prodi"
        )

        ti_cpl = self._numbered_items(
            self._section(
                ti_section, "### Capaian Pembelajaran Lulusan (CPL)", "### Profil lulusan"
            )
        )
        el_cpl = []
        for line in el_section.splitlines():
            if not line.startswith("| CPL-"):
                continue
            cells = [cell.strip() for cell in line.strip("|").split("|")]
            if len(cells) >= 3:
                el_cpl.append((cells[2], cells[1]))
        mf_cpl = self._numbered_items(mf_section)
        if len(ti_cpl) != 10 or len(el_cpl) != 8 or len(mf_cpl) != 12:
            raise ValidationError(
                "Jumlah CPL pada docs/data_prodi.md tidak sesuai dengan sumber yang diharapkan."
            )

        ti_courses = self._parse_semester_courses(
            self._section(
                course_section,
                "### Teknik Industri (152 SKS)",
                "### Teknik Elektro",
            )
        )
        el_courses = self._parse_semester_courses(
            self._section(course_section, "### Teknik Elektro", "### Teknik Sipil")
        )
        mf_courses = self._parse_semester_courses(
            self._section(course_section, "### Teknik Manufaktur")
        )
        civil_courses = self._parse_semester_courses(
            self._section(
                civil_section,
                "### RPS per mata kuliah",
                "Sumber:",
            )
        )
        for semester in range(6, 9):
            for index, name in enumerate(
                (
                    "Pemodelan dan Analisis Infrastruktur",
                    "Perancangan Infrastruktur Lanjut",
                    "Manajemen Proyek Konstruksi",
                    "Proyek Terpadu Teknik Sipil",
                ),
                start=1,
            ):
                civil_courses.append(
                    {
                        "semester": semester,
                        "name": f"{name} {index:02d}",
                        "group": None,
                        "source_type": "dummy",
                    }
                )

        self._add_industrial_electives(ti_courses)
        self._add_electrical_electives(el_courses)
        self._add_manufacturing_electives(mf_courses)

        if not all((ti_courses, el_courses, mf_courses, civil_courses)):
            raise ValidationError(
                "Daftar mata kuliah fixture tidak dapat dibaca lengkap dari docs/data_prodi.md."
            )
        for program_name, courses in (
            ("Teknik Industri", ti_courses),
            ("Teknik Elektro", el_courses),
            ("Teknik Manufaktur", mf_courses),
            ("Teknik Sipil", civil_courses),
        ):
            semesters = {course["semester"] for course in courses}
            if not set(range(1, 9)).issubset(semesters):
                raise ValidationError(
                    f"Daftar mata kuliah {program_name} tidak mencakup semester 1–8."
                )
        return {
            "ti": {"cpls": [(item, None) for item in ti_cpl], "courses": ti_courses},
            "el": {"cpls": el_cpl, "courses": el_courses},
            "mf": {
                "cpls": [(item, None) for item in mf_cpl],
                "courses": mf_courses,
            },
            "si": {
                "cpls": [(item, None) for item in CIVIL_CPLS],
                "courses": civil_courses,
            },
        }

    @api.model
    def _section(self, text, start_marker, end_marker=None):
        start = text.find(start_marker)
        if start < 0:
            raise ValidationError(
                f"Penanda bagian dokumen tidak ditemukan: {start_marker}"
            )
        start += len(start_marker)
        end = text.find(end_marker, start) if end_marker else -1
        if end_marker and end < 0:
            raise ValidationError(
                f"Penanda akhir bagian dokumen tidak ditemukan: {end_marker}"
            )
        return text[start:end] if end >= 0 else text[start:]

    @api.model
    def _numbered_items(self, text):
        return [
            match.group(1).strip()
            for match in re.finditer(r"(?m)^\s*\d+\.\s+(.+)$", text)
        ]

    @api.model
    def _split_course_names(self, value):
        protected = (
            "Kreativitas, Inovasi, dan Kewirausahaan",
            "Kreativitas, Inovasi dan Kewirausahaan",
            "Metodologi Penelitian, Teknik Penulisan dan Presentasi",
        )
        for index, phrase in enumerate(protected):
            value = value.replace(phrase, phrase.replace(",", f"@@{index}@@"))
        value = re.sub(
            r",?\s*(?:dua|lima|tiga)\s+mata kuliah pilihan\.?$",
            "",
            value,
            flags=re.IGNORECASE,
        )
        parts = []
        for item in value.split(","):
            for index, phrase in enumerate(protected):
                item = item.replace(f"@@{index}@@", ",")
            item = item.strip().rstrip(".")
            if item and "mata kuliah pilihan" not in item.lower():
                parts.append(item)
        return parts

    @api.model
    def _parse_semester_courses(self, text):
        courses = []
        for match in re.finditer(
            r"(?m)^\s*-\s*Semester\s+(\d+):\s*(.*?)\s*$", text
        ):
            semester = int(match.group(1))
            names = re.sub(r"\s*\(\d+\s*SKS\)\.?$", "", match.group(2)).strip()
            for name in self._split_course_names(names):
                courses.append(
                    {
                        "semester": semester,
                        "name": name,
                        "group": None,
                        "source_type": "mixed",
                    }
                )
        return courses

    @api.model
    def _add_industrial_electives(self, courses):
        groups = (
            ("Sistem dan Rekayasa Produksi", 4, 6),
            ("Penelitian Operasional", 4, 6),
            ("Ergonomi dan Rekayasa Faktor Manusia", 4, 7),
            ("Manajemen Informasi dan Teknologi Industri 4.0", 5, 7),
        )
        for group_index, (group_name, count, semester) in enumerate(groups, start=1):
            for index in range(1, count + 1):
                courses.append(
                    {
                        "semester": semester,
                        "name": f"{group_name} - Pilihan Simulasi {index:02d}",
                        "group": f"ti_choice_{group_index}",
                        "source_type": "dummy",
                        "choice_count": 1,
                    }
                )

    @api.model
    def _add_electrical_electives(self, courses):
        depth_examples = (
            "Elektronika Daya",
            "Robotika",
            "Digital Signal Processing",
            "Computer Vision",
        )
        for index in range(1, 21):
            name = (
                depth_examples[index - 1]
                if index <= len(depth_examples)
                else f"Pendalaman Materi Teknik Elektro - Simulasi {index:02d}"
            )
            courses.append(
                {
                    "semester": 6,
                    "name": name,
                    "group": "el_depth",
                    "source_type": "mixed" if index <= 4 else "dummy",
                    "choice_count": 5,
                }
            )
        for track, count in (
            ("Sistem Ketenagaan", 11),
            ("Sistem Kendali", 10),
            ("Sistem Komputer", 9),
        ):
            for index in range(1, count + 1):
                courses.append(
                    {
                        "semester": 7,
                        "name": f"{track} - Pilihan Simulasi {index:02d}",
                        "group": f"el_{track.lower().replace(' ', '_')}",
                        "source_type": "dummy",
                        "choice_count": 2,
                    }
                )

    @api.model
    def _add_manufacturing_electives(self, courses):
        for index, name in enumerate(MANUFACTURING_ELECTIVES):
            semester = 6 if index < 6 else 7
            courses.append(
                {
                    "semester": semester,
                    "name": name,
                    "group": f"mf_choice_{semester}",
                    "source_type": "mixed",
                    "choice_count": 1,
                }
            )

    @api.model
    def _upsert_many(self, model_name, items):
        items = list(items)
        if not items:
            return {}
        keys = [item[0] for item in items]
        if len(keys) != len(set(keys)):
            raise ValidationError(f"ID fixture duplikat untuk model {model_name}.")

        imd_model = self.env["ir.model.data"].sudo()
        existing_data = imd_model.search(
            [("module", "=", "erpobe"), ("name", "in", keys)]
        )
        data_by_key = {record.name: record for record in existing_data}
        model_context = {"install_mode": True}
        if model_name == "erpobe.akademik.krs.line":
            model_context["defer_offer_student_sync"] = True
        model = self.env[model_name].sudo().with_context(**model_context)
        records = {}
        new_items = []

        for key, values in items:
            data = data_by_key.get(key)
            if not data:
                new_items.append((key, values))
                continue
            if data.model != model_name:
                raise ValidationError(
                    f"XML ID erpobe.{key} menunjuk ke {data.model}, bukan {model_name}."
                )
            record = model.browse(data.res_id).exists()
            if not record:
                raise ValidationError(
                    f"XML ID erpobe.{key} menunjuk ke record yang sudah tidak ada."
                )
            if model_name == "erpobe.akademik.rps" and record.status == "final":
                records[key] = record
                continue
            if not self._record_matches_values(record, values):
                record.write(values)
            records[key] = record

        if new_items:
            created = model.create([item[1] for item in new_items])
            records.update(dict(zip((item[0] for item in new_items), created)))
            imd_model.create(
                [
                    {
                        "module": "erpobe",
                        "name": key,
                        "model": model_name,
                        "res_id": record.id,
                        "noupdate": True,
                    }
                    for key, record in zip(
                        (item[0] for item in new_items), created
                    )
                ]
            )
        return records

    @api.model
    def _record_matches_values(self, record, values):
        for field_name, expected in values.items():
            field = record._fields[field_name]
            current = record[field_name]
            if field.type == "many2one":
                expected_id = expected.id if hasattr(expected, "id") else expected
                if current.id != (expected_id or False):
                    return False
            elif field.type in ("many2many", "one2many"):
                if not expected:
                    if current:
                        return False
                    continue
                if (
                    len(expected) != 1
                    or expected[0][0] != Command.SET
                    or set(current.ids) != set(expected[0][2])
                ):
                    return False
            elif current != expected:
                return False
        return True

    @api.model
    def _upsert(self, model_name, key, values):
        return self._upsert_many(model_name, [(key, values)])[key]

    @api.model
    def _preserve_existing_fixture_values(self, model_name, items):
        keys = [key for key, _values in items]
        data = self.env["ir.model.data"].sudo().search([
            ("module", "=", "erpobe"),
            ("name", "in", keys),
        ])
        data_by_key = {record.name: record for record in data}
        model = self.env[model_name].sudo()
        for key, values in items:
            external_id = data_by_key.get(key)
            if not external_id or external_id.model != model_name:
                continue
            record = model.browse(external_id.res_id).exists()
            if not record:
                continue
            for field_name in values:
                field = record._fields[field_name]
                current = record[field_name]
                if field.type == "many2one":
                    values[field_name] = current.id or False
                elif field.type in ("many2many", "one2many"):
                    values[field_name] = [Command.set(current.ids)]
                else:
                    values[field_name] = current

    @api.model
    def _mark_source(self, record, source_type, note, source_url=None):
        self._mark_sources([(record, source_type, note, source_url)])

    @api.model
    def _mark_sources(self, items):
        items = list(items)
        if not items:
            return

        source_items = []
        for record, source_type, note, source_url in items:
            source_items.append(
                (
                    f"{record._name}:{record.id}",
                    {
                        "name": record.display_name,
                        "record_model": record._name,
                        "record_id": record.id,
                        "source_type": SOURCE_KIND[source_type],
                        "source_note": note,
                        "source_url": source_url or False,
                    },
                )
            )

        model = self.env["erpobe.akademik.fixture.source"].sudo()
        keys = [key for key, _values in source_items]
        existing_sources = model.search([("fixture_key", "in", keys)])
        source_by_key = {source.fixture_key: source for source in existing_sources}
        new_values = []
        for key, values in source_items:
            values["fixture_key"] = key
            source = source_by_key.get(key)
            if not source:
                new_values.append(values)
                continue
            if any(source[field] != value for field, value in values.items()):
                source.write(values)
        if new_values:
            model.create(new_values)

    @api.model
    def _ensure_components(self):
        entries = [
            (key, name, kind)
            for key, name, kind, _weight in FIXTURE_COMPONENTS
        ] + list(ADDITIONAL_COMPONENTS)
        records = self._upsert_many(
            "erpobe.akademik.komponen",
            [
                (key, {"name": name, "tipe": kind, "aktif": True})
                for key, name, kind in entries
            ],
        )
        return [
            records[key]
            for key, _name, _kind, _weight in FIXTURE_COMPONENTS
        ]

    @api.model
    def _ensure_methods(self):
        items = []
        for index, name in enumerate(
            (
                "Case Method",
                "Project Based Learning",
                "Kuliah Interaktif",
                "Praktik dan Laboratorium",
            ),
            start=1,
        ):
            items.append(
                (
                    f"fixture_method_{index:02d}",
                    {"name": name, "kode": f"F{index:02d}", "active": True},
                )
            )
        self._preserve_existing_fixture_values(
            "erpobe.akademik.metode.pembelajaran", items
        )
        records = self._upsert_many(
            "erpobe.akademik.metode.pembelajaran", items
        )
        return [records[key] for key, _values in items]

    @api.model
    def _ensure_grades(self):
        grade_values = (
            ("A", 85.0, 100.0, 4.0, "Capaian sangat baik."),
            ("B", 75.0, 84.99, 3.0, "Capaian baik."),
            ("C", 60.0, 74.99, 2.0, "Capaian cukup."),
            ("D", 0.0, 59.99, 1.0, "Capaian perlu ditingkatkan."),
        )
        result = []
        for name, minimum, maximum, weight, description in grade_values:
            existing = self.env["erpobe.master.grade"].sudo().search(
                [("name", "=", name)], limit=1
            )
            if existing:
                result.append(existing)
                continue
            result.append(
                self._upsert(
                    "erpobe.master.grade",
                    f"fixture_grade_{name.lower()}",
                    {
                        "name": name,
                        "nilai_min": minimum,
                        "nilai_max": maximum,
                        "bobot": weight,
                        "keterangan_standar": description,
                    },
                )
            )
        return result

    @api.model
    def _ensure_teachers(self):
        by_key = {}
        for program in PROGRAMS:
            for key, name, expertise in program["teachers"]:
                row = by_key.setdefault(
                    key,
                    {
                        "name": name,
                        "expertise": expertise,
                        "programs": set(),
                        "urls": set(),
                        "dummy": program["slug"] == "si",
                    },
                )
                row["programs"].add(program["xmlid"])
                if program["teacher_url"]:
                    row["urls"].add(program["teacher_url"])

        prodis = {
            config["xmlid"]: self.env.ref(f"erpobe.{config['xmlid']}")
            for config in PROGRAMS
        }
        items = []
        for key, row in by_key.items():
            slug = self._slug(key)
            items.append(
                (
                    f"fixture_teacher_{slug}",
                    {
                        "name": row["name"],
                        "email": f"dosen.{slug}@example.test",
                        "nip": f"SIM-DOSEN-{slug.upper()}",
                        "bidang_keahlian": row["expertise"],
                        "prodi_ids": [
                            Command.set(
                                [prodis[xmlid].id for xmlid in sorted(row["programs"])]
                            )
                        ],
                    },
                )
            )
        self._preserve_existing_fixture_values(
            "erpobe.master.dosen", items
        )
        teachers = self._upsert_many("erpobe.master.dosen", items)
        result = {}
        source_items = []
        for key, row in by_key.items():
            teacher = teachers[f"fixture_teacher_{self._slug(key)}"]
            dummy = row["dummy"]
            source_items.append(
                (
                    teacher,
                    "dummy" if dummy else "mixed",
                    (
                        "Profil dosen simulasi; nama dan bidang belum diverifikasi pada sumber prodi."
                        if dummy
                        else "Nama/bidang diringkas dari docs/data_prodi.md; NIP dan email adalah simulasi. "
                        "Muhamad Ali dideduplikasi lintas Teknik Industri dan Teknik Elektro."
                    ),
                    next(iter(sorted(row["urls"])), None),
                ),
            )
            result[key] = teacher
        self._mark_sources(source_items)
        return result

    @api.model
    def _ensure_program(
        self, config, data, teacher_map, component_ids, methods, grades
    ):
        prodi = self.env.ref(f"erpobe.{config['xmlid']}")
        self._mark_source(
            prodi,
            "official",
            "Nama program studi dan kode merujuk ke bootstrap demo; verifikasi perubahan resmi pada situs fakultas.",
            config["source_url"],
        )
        rombels = [
            self.env.ref(
                f"erpobe.rombel_{config['code'].lower()}_2022_{letter}"
            )
            for letter in ("a", "b")
        ]
        curriculum_key = f"fixture_curriculum_{config['slug']}_2022"
        curriculum = self._upsert(
            "erpobe.akademik.kurikulum",
            curriculum_key,
            {
                "name": f"Kurikulum Fixture {config['name']} Angkatan 2022",
                "kode": f"SIM-{config['code']}-2022",
                "prodi_id": prodi.id,
                "angkatan_mulai": 2022,
                "source_type": "dummy" if config["slug"] == "si" else "mixed",
                "source_note": (
                    "Kurikulum simulasi. Daftar semester 6–8 dan kode/SKS tidak tersedia "
                    "pada sumber yang dibaca."
                    if config["slug"] == "si"
                    else "Nama mata kuliah dirujuk dari docs/data_prodi.md; penetapan "
                    "kurikulum untuk angkatan 2022, kode, dan seluruh nilai SKS per mata kuliah merupakan simulasi."
                ),
                "source_url": config["source_url"],
            },
        )
        self._mark_source(
            curriculum,
            "dummy" if config["slug"] == "si" else "mixed",
            curriculum.source_note,
            config["source_url"],
        )

        cpls = self._ensure_cpls(config, data["cpls"], prodi)
        students = self._ensure_students(config, curriculum, rombels, teacher_map)
        reference = self._upsert(
            "erpobe.akademik.referensi",
            f"fixture_reference_{config['slug']}_program",
            {
                "kode": f"REF-{config['code']}-SIM",
                "judul": f"Sumber Program Studi {config['name']} (rujukan fixture)",
                "penulis": "Program Studi terkait; dirangkum dalam docs/data_prodi.md",
                "tahun": "2026",
                "link": config["source_url"],
                "jenis": "utama",
                "prodi_id": prodi.id,
            },
        )
        self._mark_source(
            reference,
            "dummy" if config["slug"] == "si" else "mixed",
            "Referensi ini menunjuk ke halaman sumber yang tercatat dalam docs/data_prodi.md; bukan pustaka mata kuliah yang tervalidasi.",
            config["source_url"],
        )
        courses = self._ensure_courses(
            config, data["courses"], prodi, curriculum, cpls, teacher_map
        )
        for course in courses:
            course["reference"] = reference
        offers = self._ensure_offers(config, prodi, rombels, courses)
        for course in courses:
            course["offer_line"] = offers[course["code"]]["line"]
            course["input_nilai"] = offers[course["code"]]["input"]
            if course["spec"]["semester"] == 6:
                course["rps"] = self._ensure_rps(
                    config,
                    course,
                    component_ids,
                    methods,
                    grades,
                )
            else:
                course["rps"] = False
        return {
            "config": config,
            "prodi": prodi,
            "curriculum": curriculum,
            "cpls": cpls,
            "students": students,
            "courses": courses,
            "rombels": rombels,
        }

    @api.model
    def _ensure_cpls(self, config, cpl_specs, prodi):
        items = []
        for index, (description, category) in enumerate(cpl_specs, start=1):
            items.append(
                (
                    "fixture_cpl_%s_%02d" % (config["slug"], index),
                    {
                        "prodi_id": prodi.id,
                        "kode_cpl": "%s-CPL-%02d" % (config["code"], index),
                        "nama_cpl": "Capaian Pembelajaran %02d" % index,
                        "name": description,
                        "indikator_capaian": category
                        or "Indikator simulasi untuk CPL-%02d." % index,
                    },
                )
            )
        self._preserve_existing_fixture_values(
            "erpobe.akademik.cpl", items
        )
        records = self._upsert_many("erpobe.akademik.cpl", items)
        if not records:
            raise ValidationError(
                "Data CPL simulasi kosong untuk prodi %s." % prodi.display_name
            )
        result = list(records.values())
        self._mark_sources([
            (
                cpl,
                "dummy",
                "CPL dibuat untuk data simulasi; bukan rumusan resmi prodi.",
                None,
            )
            for cpl in result
        ])
        return result

    @api.model
    def _ensure_students(self, config, curriculum, rombels, teacher_map):
        program_teacher_keys = [row[0] for row in config["teachers"]]
        advisors = [teacher_map[key] for key in program_teacher_keys]
        items = []
        for index in range(1, 61):
            student_code = f"{config['code']}22{index:03d}"
            first = FIRST_NAMES[(index - 1) % len(FIRST_NAMES)]
            last = LAST_NAMES[(index * 7 - 1) % len(LAST_NAMES)]
            rombel = (
                rombels[0]
                if index <= 15 or 31 <= index <= 45
                else rombels[1]
            )
            items.append(
                (
                    f"fixture_student_{config['slug']}_2022_{index:03d}",
                    {
                        "name": f"Simulasi {first} {last} {config['code']} {index:03d}",
                        "nim": f"SIM{student_code}",
                        "email": f"mhs.{config['slug']}.2022.{index:03d}@example.test",
                        "rombel_id": rombel.id,
                        "dosen_wali_id": advisors[(index - 1) % len(advisors)].id,
                        "kurikulum_id": curriculum.id,
                        "semester_saat_ini": 6,
                        "status_akademik": "aktif",
                    },
                )
            )
        self._preserve_existing_fixture_values(
            "erpobe.master.mahasiswa", items
        )
        records = self._upsert_many("erpobe.master.mahasiswa", items)
        students = []
        source_items = []
        for index in range(1, 61):
            student = records[
                f"fixture_student_{config['slug']}_2022_{index:03d}"
            ]
            source_items.append(
                (
                    student,
                    "dummy",
                    "Identitas, NIM, email, angkatan, dan status akademik dibuat untuk pengujian; bukan data mahasiswa nyata.",
                    None,
                )
            )
            students.append(student)
        self._mark_sources(source_items)
        return students

    @api.model
    def _ensure_courses(self, config, specs, prodi, curriculum, cpls, teacher_map):
        teachers = [teacher_map[row[0]] for row in config["teachers"]]
        items = []
        for sequence, spec in enumerate(specs, start=1):
            code = f"{config['code']}-{spec['semester']:02d}-{sequence:03d}"
            slug_code = code.lower().replace("-", "_")
            spec["code"] = code
            spec["key"] = slug_code
            spec["sequence"] = sequence
            spec["sks"] = self._estimated_sks(spec["name"])
            spec["jenis_mk"] = (
                "P" if spec.get("group") else self._course_kind(spec["name"])
            )
            spec["tipe_mk"] = self._course_type(spec["name"])
            cpl_start = ((sequence - 1) * 2) % len(cpls)
            selected_cpls = [cpls[cpl_start], cpls[(cpl_start + 1) % len(cpls)]]
            spec["cpls"] = selected_cpls
            items.append(
                (
                    f"fixture_course_{config['slug']}_{slug_code}",
                    {
                        "name": spec["name"],
                        "kode_mk": code,
                        "prodi_id": prodi.id,
                        "kurikulum_id": curriculum.id,
                        "sks": spec["sks"],
                        "semester": spec["semester"],
                        "active": True,
                        "jenis_mk": spec["jenis_mk"],
                        "tipe_mk": spec["tipe_mk"],
                        "deskripsi_mk": (
                            f"Mata kuliah fixture untuk {config['name']}. "
                            "Deskripsi pembelajaran ini dibuat untuk simulasi dan "
                            "bukan RPS resmi."
                        ),
                        "koordinator_id": teachers[(sequence - 1) % len(teachers)].id,
                        "tim_pengampu_ids": [
                            Command.set(
                                [
                                    teachers[(sequence - 1 + offset) % len(teachers)].id
                                    for offset in range(min(3, len(teachers)))
                                ]
                            )
                        ],
                    },
                )
            )

        course_records = self._upsert_many("erpobe.master.matakuliah", items)
        cpmk_items = []
        for spec in specs:
            course_key = f"fixture_course_{config['slug']}_{spec['key']}"
            course = course_records[course_key]
            for number in (1, 2):
                cpmk_key = f"fixture_cpmk_{spec['key']}_{number:02d}"
                cpmk_items.append(
                    (
                        cpmk_key,
                        {
                            "mk_id": course.id,
                            "kode_cpmk": f"CPMK-{number:02d}",
                            "name": (
                                f"Mahasiswa mampu menerapkan dan mengevaluasi "
                                f"{spec['name'].lower()} pada konteks rekayasa."
                            ),
                            "indikator": (
                                f"Bukti kinerja simulasi untuk {spec['name']} "
                                f"(CPMK {number})."
                            ),
                            "target_nilai": 70.0,
                        },
                    )
                )
        cpmk_records = self._upsert_many("erpobe.akademik.cpmk", cpmk_items)

        mapping_items = []
        source_items = []
        result = []
        for spec in specs:
            course_key = f"fixture_course_{config['slug']}_{spec['key']}"
            course = course_records[course_key]
            for number in (1, 2):
                cpmk = cpmk_records[f"fixture_cpmk_{spec['key']}_{number:02d}"]
                source_items.append(
                    (
                        cpmk,
                        "dummy",
                        "Rumusan, kode, indikator, dan target CPMK dibuat untuk simulasi.",
                        None,
                    )
                )
                for cpl_index, cpl in enumerate(spec["cpls"], start=1):
                    mapping_key = (
                        f"fixture_mapping_{spec['key']}_{number:02d}_{cpl_index:02d}"
                    )
                    mapping_items.append(
                        (
                            mapping_key,
                            {"cpl_id": cpl.id, "cpmk_id": cpmk.id},
                        )
                    )
            source_items.append(
                (
                    course,
                    spec["source_type"],
                    (
                        "Nama mata kuliah dirujuk dari docs/data_prodi.md; kode, seluruh nilai SKS, "
                        "penempatan semester pilihan, dan deskripsi merupakan simulasi."
                        if spec["source_type"] == "mixed"
                        else "Mata kuliah dan penempatannya dibuat untuk melengkapi fixture; bukan daftar resmi."
                    ),
                    config["source_url"],
                ),
            )
        self._upsert_many("erpobe.akademik.cpl.mk.cpmk", mapping_items)
        mk_cpl_items = []
        for spec in specs:
            course = course_records[
                f"fixture_course_{config['slug']}_{spec['key']}"
            ]
            for cpl in spec["cpls"]:
                mk_cpl_items.append(
                    (
                        f"fixture_mk_cpl_{config['slug']}_{spec['key']}_{cpl.id}",
                        {
                            "mk_id": course.id,
                            "cpl_id": cpl.id,
                        },
                    )
                )
        mk_cpl_records = self._upsert_many(
            "erpobe.akademik.mk.cpl", mk_cpl_items
        )
        for spec in specs:
            course = course_records[
                f"fixture_course_{config['slug']}_{spec['key']}"
            ]
            cpmks = [
                cpmk_records[f"fixture_cpmk_{spec['key']}_{number:02d}"]
                for number in (1, 2)
            ]
            result.append(
                {
                    "spec": spec,
                    "course": course,
                    "code": spec["code"],
                    "cpmks": cpmks,
                    "cpls": spec["cpls"],
                    "mk_cpl_mappings": [
                        mk_cpl_records[
                            f"fixture_mk_cpl_{config['slug']}_{spec['key']}_{cpl.id}"
                        ]
                        for cpl in spec["cpls"]
                    ],
                }
            )
        self._mark_sources(source_items)
        return result

    @api.model
    def _ensure_offers(self, config, prodi, rombels, courses):
        term_groups = {}
        for course in courses:
            year_id = self._year_for_semester(course["spec"]["semester"])
            term_groups.setdefault(year_id.id, {"year": year_id, "courses": []})
            term_groups[year_id.id]["courses"].append(course)

        offers = {}
        input_items = []
        for group in term_groups.values():
            year = group["year"]
            year_slug = year.tahun_ajaran.replace("/", "_") + f"_{year.semester}"
            offer_key = f"fixture_offer_{config['slug']}_{year_slug}"
            offer = self._upsert(
                "erpobe.akademik.penawaran",
                offer_key,
                {
                    "tahun_ajaran": year.id,
                    "prodi_id": prodi.id,
                    "rombel_ids": [Command.set([rombel.id for rombel in rombels])],
                },
            )
            line_items = []
            for course in group["courses"]:
                line_key = (
                    f"fixture_offerline_{config['slug']}_{course['spec']['key']}"
                )
                line_items.append(
                    (
                        line_key,
                        {
                            "penawaran_id": offer.id,
                            "matakuliah_id": course["course"].id,
                            "rombel_ids": [
                                Command.set([rombel.id for rombel in rombels])
                            ],
                        },
                    )
                )
            lines = self._upsert_many(
                "erpobe.akademik.penawaran.line", line_items
            )
            offer._sync_master_data()
            for course in group["courses"]:
                line = lines[
                    f"fixture_offerline_{config['slug']}_{course['spec']['key']}"
                ]
                input_key = (
                    f"fixture_input_{config['slug']}_{course['spec']['key']}"
                )
                input_items.append(
                    (
                        input_key,
                        {
                            "penawaran_id": offer.id,
                            "penawaran_line_id": line.id,
                        },
                    )
                )
                offers[course["code"]] = {
                    "offer": offer,
                    "line": line,
                    "input_key": input_key,
                }
        inputs = self._upsert_many("erpobe.input.nilai", input_items)
        for course in offers.values():
            course["input"] = inputs.pop(course.pop("input_key"))
        return offers

    @api.model
    def _ensure_rps(self, config, course, component_ids, methods, grades):
        spec = course["spec"]
        rps_key = f"fixture_rps_{config['slug']}_{spec['key']}"
        rps_model = self.env["erpobe.akademik.rps"].sudo()
        data = self.env["ir.model.data"].sudo().search(
            [("module", "=", "erpobe"), ("name", "=", rps_key)], limit=1
        )
        if data and data.model == "erpobe.akademik.rps":
            rps = rps_model.browse(data.res_id).exists()
            if not rps:
                raise ValidationError(f"XML ID erpobe.{rps_key} tidak memiliki RPS.")
            if rps.status == "final":
                rps._link_finalized_to_offer(course["offer_line"])
                return rps
        else:
            rps = self._upsert(
                "erpobe.akademik.rps",
                rps_key,
                {
                    "matakuliah_id": course["course"].id,
                    "version": max(
                        course["offer_line"].rps_ids.mapped("version"),
                        default=0,
                    ) + 1,
                    "komponen_ids": [Command.set([item.id for item in component_ids])],
                    "media_software": "Perangkat lunak sesuai topik (simulasi)",
                    "media_hardware": "Laboratorium/perangkat praktik (simulasi)",
                },
            )

        legacy_project = self.env.ref("erpobe.fixture_component_project")
        rps.write({
            "komponen_ids": [
                Command.set([component.id for component in component_ids] + [legacy_project.id])
            ],
            "referensi_ids": [Command.set([course["reference"].id])],
            "tujuan_pembelajaran": (
                f"Mahasiswa mampu mencapai CPMK pada {spec['name']} (simulasi)."
            ),
            "materi_pembelajaran": (
                f"Materi pembelajaran disusun mengikuti topik mingguan {spec['name']}."
            ),
            "sumber_belajar": course["reference"].judul,
        })
        rps._sync_bobot_tables()
        if not course["cpmks"]:
            raise ValidationError(
                f"RPS fixture {spec['name']} tidak memiliki CPMK untuk dialokasikan."
            )
        snapshots = rps.rps_komponen_ids.filtered("aktif").sorted(
            key=lambda component: (component.sequence, component.id)
        )
        if not snapshots:
            raise ValidationError(
                f"RPS fixture {spec['name']} tidak memiliki komponen penilaian aktif."
            )
        fixture_weights = {
            kind: weight for _key, _name, kind, weight in FIXTURE_COMPONENTS
        }
        for snapshot in rps.rps_komponen_ids:
            component_type = (
                snapshot.komponen_id.tipe if snapshot.komponen_id else snapshot.tipe
            )
            if component_type == "project":
                snapshot.write({
                    "tipe": component_type,
                    "name": snapshot.komponen_id.name,
                    "bobot": 0.0,
                    "aktif": False,
                })
                continue
            weight = fixture_weights.get(component_type)
            if weight is None:
                snapshot.write({
                    "tipe": component_type,
                    "name": snapshot.komponen_id.name if snapshot.komponen_id else snapshot.name,
                    "bobot": 0.0,
                    "aktif": False,
                })
                continue
            snapshot.write({
                "tipe": component_type,
                "name": snapshot.komponen_id.name,
                "description": snapshot.komponen_id.description,
                "bobot": weight,
                "aktif": True,
            })

        cpmk_weights = _distribute_percent(100, len(course["cpmks"]))
        for line, weight in zip(
            rps.bobot_cpmk_mk_ids.sorted("cpmk_id"),
            cpmk_weights,
        ):
            line.write({"bobot_cpmk_mk": weight})

        for snapshot in snapshots:
            allocations = snapshot.allocation_ids.filtered(
                lambda line: line.rps_id == rps
                and line.cpmk_id in course["cpmks"]
            ).sorted(key=lambda line: (line.cpmk_id.id, line.id))
            if {line.cpmk_id.id for line in allocations} != {
                cpmk.id for cpmk in course["cpmks"]
            }:
                raise ValidationError(
                    f"Alokasi komponen {snapshot.name} pada RPS {spec['name']} "
                    "belum mencakup semua CPMK yang dikonfigurasi."
                )
            allocation_weights = _distribute_percent(100, len(allocations))
            for allocation, weight in zip(allocations, allocation_weights):
                allocation.write({"bobot_komponen_cpmk": weight})

        activity_items = []
        for week in range(1, 17):
            cpmk = course["cpmks"][(week - 1) % len(course["cpmks"])]
            activity_key = f"fixture_activity_{spec['key']}_{week:02d}"
            activity_items.append(
                (
                    activity_key,
                    {
                        "rps_id": rps.id,
                        "minggu": week,
                        "cpmk_id": cpmk.id,
                        "bahan_kajian": f"Minggu {week}: {spec['name']} - {WEEK_TOPICS[week - 1]}.",
                        "metode_pembelajaran_id": methods[(week - 1) % len(methods)].id,
                        "pengalaman_belajar": (
                            "Mahasiswa mengerjakan latihan/studi kasus, mendiskusikan "
                            "hasil, dan menyusun bukti belajar (simulasi)."
                        ),
                        "indikator_penilaian": cpmk.indikator,
                        "estimasi_waktu": 170,
                        "referensi_ids": [
                            Command.set([course["reference"].id])
                        ],
                        "teknik_penilaian": (
                            "Ujian Tengah Semester" if week == 8 else
                            "Ujian Akhir Semester" if week == 16 else
                            "Tugas/observasi/rubrik"
                        ),
                    },
                )
            )
        self._upsert_many("erpobe.akademik.kegiatan.perkuliahan", activity_items)

        rubric_sequence = 0
        rubric_items = []
        for component in component_ids:
            for cpmk in course["cpmks"]:
                rubric_sequence += 1
                rubric_key = (
                    f"fixture_rubric_{spec['key']}_{component.id}_{cpmk.id}"
                )
                rubric_items.append(
                    (
                        rubric_key,
                        {
                            "rps_id": rps.id,
                            "sequence": rubric_sequence * 10,
                            "materi_soal": (
                                f"Penilaian {component.name} untuk {spec['name']} "
                                f"(CPMK {cpmk.kode_cpmk}, simulasi)."
                            ),
                            "komponen_id": component.id,
                            "cpmk_id": cpmk.id,
                            "bobot": 12.5,
                        },
                    )
                )
        rubrics = self._upsert_many(
            "erpobe.akademik.rubrik.penilaian", rubric_items
        )

        criterion_items = []
        for component in component_ids:
            for cpmk in course["cpmks"]:
                rubric_key = (
                    f"fixture_rubric_{spec['key']}_{component.id}_{cpmk.id}"
                )
                rubric = rubrics[rubric_key]
                for grade in grades:
                    criterion_key = (
                        f"fixture_criterion_{spec['key']}_{component.id}_{cpmk.id}_{grade.id}"
                    )
                    criterion_items.append(
                        (
                            criterion_key,
                            {
                                "rubrik_id": rubric.id,
                                "grade_id": grade.id,
                                "deskripsi": (
                                    f"{grade.name}: {grade.keterangan_standar} "
                                    "Deskripsi kriteria ini adalah simulasi."
                                ),
                            },
                        )
                    )
        self._upsert_many("erpobe.akademik.kriteria", criterion_items)

        if rps.status != "final":
            validation = self.env["erpobe.weight.validation"].validate_rps(rps)
            if not validation["complete"]:
                details = "; ".join(
                    f"{item['item_name']} ({item['relation']}): {item['total']:.2f}%"
                    for item in validation["problems"]
                )
                raise ValidationError(
                    f"Konfigurasi bobot RPS {spec['name']} belum valid: {details}"
                )
            rps.action_mark_for_review()
            rps.action_finalize()
        rps._link_finalized_to_offer(course["offer_line"])
        self._mark_source(
            rps,
            "dummy",
            "Seluruh isi RPS, bobot, rubrik, dan kegiatan dibuat untuk simulasi; "
            "RPS final ini bukan RPS resmi atau pengesahan program studi.",
            config["source_url"],
        )
        return rps

    @api.model
    def _create_cpl_results(self, programs):
        items = []
        for program in programs.values():
            config = program["config"]
            for student_index, student in enumerate(program["students"], start=1):
                for cpl_index, cpl in enumerate(program["cpls"], start=1):
                    items.append(
                        (
                            f"fixture_grade_cpl_{config['slug']}_2022_{student_index:03d}_{cpl_index:02d}",
                            {"mahasiswa_id": student.id, "cpl_id": cpl.id},
                        )
                    )
        self._upsert_many("erpobe.grade.cpl", items)

    @api.model
    def _select_courses(
        self, offered, student_index, student=None, program_name=None
    ):
        core = [course for course in offered if not course["spec"].get("group")]
        groups = {}
        for course in offered:
            group = course["spec"].get("group")
            if group:
                groups.setdefault(group, []).append(course)

        selected = list(core)
        total_sks = sum(course["course"].sks for course in core)
        if total_sks > 24:
            student_label = f" untuk mahasiswa {student.nim}" if student else ""
            program_label = f" ({program_name})" if program_name else ""
            courses = ", ".join(
                f"{course['course'].kode_mk} {course['course'].name} "
                f"({course['course'].sks} SKS)"
                for course in core
            )
            raise ValidationError(
                f"Konflik kurikulum: mata kuliah wajib semester 6{program_label}"
                f"{student_label} berjumlah {total_sks} SKS, melebihi batas 24 SKS. "
                f"Periksa kurikulum sebelum membuat KRS. Rincian: {courses}."
            )

        for group, choices in groups.items():
            count = choices[0]["spec"].get("choice_count", 1)
            if group.startswith("el_sistem_"):
                track = ("el_sistem_ketenagaan", "el_sistem_kendali", "el_sistem_komputer")[
                    student_index % 3
                ]
                if group != track:
                    continue
            count = min(count, len(choices))
            if count <= 0:
                continue
            offset = (student_index * count) % len(choices)
            selected_count = 0
            for index in range(len(choices)):
                choice = choices[(offset + index) % len(choices)]
                choice_sks = choice["course"].sks
                if total_sks + choice_sks > 24:
                    continue
                selected.append(choice)
                total_sks += choice_sks
                selected_count += 1
                if selected_count == count:
                    break
        return selected

    @api.model
    def _offer_for_course(self, course, year):
        if course["offer_line"].tahun_ajaran_id != year:
            raise ValidationError("KRS fixture merujuk ke tahun ajaran yang tidak sesuai.")
        return course["offer_line"].penawaran_id

    @api.model
    def _year_for_semester(self, semester):
        if semester == 6:
            period = self.env["erpobe.akademik.tahunajaran"].sudo().search([
                ("tahun_ajaran", "=", "2025/2026"),
                ("semester", "=", "genap"),
            ], limit=1)
            if period:
                return period
        year_start = 2022 + (semester - 1) // 2
        term = "ganjil" if semester % 2 else "genap"
        xmlid = f"ta_{year_start}_{year_start + 1}_{term}"
        return self.env.ref(f"erpobe.{xmlid}")

    @api.model
    def _estimated_sks(self, name):
        normalized = name.casefold()
        if any(token in normalized for token in ("skripsi", "tugas akhir")):
            return 8
        if "kuliah kerja nyata" in normalized:
            return 4
        if "praktik industri" in normalized or "praktek industri" in normalized:
            return 6
        if "capstone" in normalized or "proyek terpadu" in normalized:
            return 3
        if "praktikum" in normalized or normalized.startswith("praktik "):
            return 1
        return 2

    @api.model
    def _course_kind(self, name):
        normalized = name.casefold()
        if any(
            token in normalized
            for token in (
                "pendidikan",
                "pancasila",
                "bahasa",
                "kewarganegaraan",
                "transformasi digital",
                "literasi sosial",
            )
        ):
            return "U"
        if any(token in normalized for token in ("fisika", "matematika", "kimia", "statistika")):
            return "B"
        return "I"

    @api.model
    def _course_type(self, name):
        normalized = name.casefold()
        if any(token in normalized for token in ("praktik industri", "praktek industri", "kuliah kerja nyata")):
            return "L"
        if "praktik" in normalized or "praktikum" in normalized:
            return "P"
        return "T"

    @api.model
    def _slug(self, value):
        normalized = unicodedata.normalize("NFKD", value)
        ascii_value = normalized.encode("ascii", "ignore").decode("ascii").lower()
        return re.sub(r"[^a-z0-9]+", "_", ascii_value).strip("_")
