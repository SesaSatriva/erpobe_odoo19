import re
import hashlib
import random
from pathlib import Path

from odoo import Command, api, models
from odoo.exceptions import ValidationError


PROGRAM_FILES = {
    "si": ("prodi_si", "55201", "kurikulum-obe-teknik-sipil-lengkap-obe.md"),
    "ti": ("prodi_ti", "55202", "kurikulum-obe-teknik-industri-lengkap-obe.md"),
    "mf": ("prodi_mf", "55205", "kurikulum-obe-teknik-manufaktur-lengkap-obe.md"),
    "el": ("prodi_el", "55203", "kurikulum-obe-teknik-elektro-lengkap-obe.md"),
}


def clean_markdown(value):
    return re.sub(r"\*\*", "", (value or "").strip())


def section(text, heading):
    match = re.search(r"^##\s+" + re.escape(heading) + r".*$", text, re.MULTILINE)
    if not match:
        raise ValidationError("Bagian dokumen tidak ditemukan: %s" % heading)
    next_heading = re.search(r"^##\s+", text[match.end():], re.MULTILINE)
    end = len(text) if not next_heading else match.end() + next_heading.start()
    return text[match.start():end]


def table_rows(text):
    rows = []
    for line in text.splitlines():
        if not line.startswith("|"):
            continue
        stripped = line.strip().strip("|")
        cells = [clean_markdown(cell) for cell in stripped.split("|")]
        if not cells or re.match(r"^:?-+", cells[0]):
            continue
        if not cells[0] or cells[0].casefold().startswith("parameter"):
            continue
        if "kode" in cells[0].casefold() and len(cells) > 1:
            continue
        rows.append(cells)
    return rows


class ErpObeOfficialCurriculum(models.AbstractModel):
    _name = "erpobe.official.curriculum"
    _description = "Impor Kurikulum Resmi dari Markdown"

    def _curriculum_dir(self):
        return Path(__file__).resolve().parents[1] / "docs" / "kurikulum"

    def _read_document(self, slug):
        _xmlid, _code, filename = PROGRAM_FILES[slug]
        path = self._curriculum_dir() / filename
        if not path.is_file():
            raise ValidationError("Dokumen kurikulum tidak ditemukan: %s" % path)
        return path.read_text(encoding="utf-8")

    def parse_cpls(self, text):
        rows = table_rows(section(text, "2. Daftar CPL"))
        result = []
        for row in rows:
            if len(row) < 4:
                raise ValidationError("Baris CPL tidak lengkap: %s" % " | ".join(row))
            result.append({
                "code": clean_markdown(row[0]),
                "title": clean_markdown(row[1]),
                "category": clean_markdown(row[2]),
                "description": clean_markdown(row[3]),
            })
        if not result:
            raise ValidationError("Daftar CPL kosong.")
        return result

    def parse_courses(self, text):
        rows = table_rows(section(text, "3. Daftar Mata Kuliah"))
        result = []
        for row in rows:
            if len(row) < 7:
                raise ValidationError("Baris mata kuliah tidak lengkap: %s" % " | ".join(row))
            try:
                result.append({
                    "code": clean_markdown(row[0]),
                    "name": clean_markdown(row[1]),
                    "semester": int(clean_markdown(row[2])),
                    "theory": int(clean_markdown(row[3])),
                    "practice": int(clean_markdown(row[4])),
                    "sks": int(clean_markdown(row[5])),
                    "status": clean_markdown(row[6]),
                })
            except (TypeError, ValueError) as error:
                raise ValidationError("Format mata kuliah tidak valid: %s" % " | ".join(row)) from error
        if not result:
            raise ValidationError("Daftar mata kuliah kosong.")
        return result

    def parse_cpmks(self, text):
        rows = table_rows(section(text, "4. Daftar CPMK"))
        result = []
        for row in rows:
            if len(row) < 5:
                raise ValidationError("Baris CPMK tidak lengkap: %s" % " | ".join(row))
            result.append({
                "course_code": clean_markdown(row[0]),
                "course_name": clean_markdown(row[1]),
                "code": clean_markdown(row[2]),
                "title": clean_markdown(row[3]),
                "description": clean_markdown(row[4]),
            })
        return result

    def parse_cpl_cpmk_mapping(self, text):
        rows = table_rows(section(text, "5. Pemetaan CPL–CPMK"))
        return [
            (
                clean_markdown(row[0]),
                clean_markdown(row[1]),
                clean_markdown(row[2]),
                clean_markdown(row[3]),
            )
            for row in rows
            if len(row) >= 4
        ]

    def parse_cpl_cpmk_weights(self, text):
        rows = table_rows(section(text, "6. Bobot CPL–CPMK"))
        result = []
        for row in rows:
            if len(row) < 4:
                raise ValidationError("Baris bobot CPL–CPMK tidak lengkap: %s" % " | ".join(row))
            result.append({
                "cpl": clean_markdown(row[0]),
                "course": clean_markdown(row[1]),
                "cpmk": clean_markdown(row[2]),
                "weight": float(clean_markdown(row[3]).replace("%", "").replace(",", ".")),
            })
        return result

    def parse_cpmk_mk_weights(self, text):
        rows = table_rows(section(text, "7. Bobot CPMK–MK"))
        result = []
        for row in rows:
            if len(row) < 4:
                raise ValidationError("Baris bobot CPMK–MK tidak lengkap: %s" % " | ".join(row))
            result.append({
                "course": clean_markdown(row[0]),
                "course_name": clean_markdown(row[1]),
                "cpmk": clean_markdown(row[2]),
                "weight": float(clean_markdown(row[3]).replace("%", "").replace(",", ".")),
            })
        return result

    def parse_components(self, text):
        rows = table_rows(section(text, "8. Komponen Penilaian"))
        result = []
        for row in rows:
            if len(row) < 7:
                raise ValidationError("Baris komponen penilaian tidak lengkap: %s" % " | ".join(row))
            try:
                weight = float(clean_markdown(row[5]).replace("%", "").replace(",", "."))
                cpmk_weight = float(clean_markdown(row[6]).replace("%", "").replace(",", "."))
            except ValueError as error:
                raise ValidationError("Bobot komponen tidak valid: %s" % " | ".join(row)) from error
            result.append({
                "course": clean_markdown(row[0]),
                "course_name": clean_markdown(row[1]),
                "name": clean_markdown(row[2]),
                "cpmk": clean_markdown(row[3]),
                "method": clean_markdown(row[4]),
                "weight": weight,
                "cpmk_weight": cpmk_weight,
            })
        return result

    @api.model
    def load_all(self):
        affected_student_ids = set()
        importer = self.with_context(defer_khs_refresh=True)
        summary = importer._load_all(affected_student_ids)
        importer._sync_khs_batch(affected_student_ids)
        return summary

    @api.model
    def _load_all(self, affected_student_ids):
        summary = {}
        for slug, (xmlid, _code, _filename) in PROGRAM_FILES.items():
            text = self._read_document(slug)
            summary[slug] = self.import_one(slug, xmlid, text)
        self._activate_2025_genap()
        summary["operations"] = self._sync_semester6_operations(
            affected_student_ids
        )
        return summary

    def _sync_khs_batch(self, student_ids):
        self.env["erpobe.report.khs"].sudo().action_generate_khs(
            sorted(set(student_ids))
        )

    @api.model
    def _activate_2025_genap(self):
        Year = self.env["erpobe.akademik.tahunajaran"].sudo()
        Year.search([("aktif", "=", True)]).write({"aktif": False})
        period = Year.search([
            ("tahun_ajaran", "=", "2025/2026"),
            ("semester", "=", "genap"),
        ], limit=1)
        if not period:
            period = Year.create({
                "tahun_ajaran": "2025/2026",
                "semester": "genap",
                "aktif": True,
            })
        else:
            period.write({"aktif": True})
        return period

    def _component_type(self, name):
        name = (name or "").casefold()
        if "kuis" in name or "tugas" in name:
            return "quiz" if "kuis" in name else "assignment"
        if "ujian" in name:
            return "midterm" if "tengah" in name else "final_exam"
        if "prakt" in name or "unjuk kerja" in name:
            return "practicum"
        if "present" in name or "portofolio" in name:
            return "presentation"
        if "proyek" in name or "studi kasus" in name:
            return "project"
        return "other"

    @api.model
    def _register_source(self, record, source_type, note):
        Source = self.env["erpobe.akademik.fixture.source"].sudo()
        source = Source.search([
            ("record_model", "=", record._name),
            ("record_id", "=", record.id),
        ], limit=1)
        if source:
            if (
                source_type == "official"
                and source.source_type == "mixed"
                and record._name == "erpobe.master.matakuliah"
            ):
                return source
            if (
                source_type == "mixed"
                and source.source_type == "official"
                and record._name == "erpobe.master.matakuliah"
            ):
                note = "%s; teaching assignment is simulated." % source.source_note
            elif source.source_type != source_type:
                raise ValidationError(
                    "Konflik provenance untuk %s %s: %s vs %s."
                    % (record._name, record.id, source.source_type, source_type)
                )
        values = {
            "name": record.display_name,
            "fixture_key": "official_curriculum_%s_%s"
            % (record._name.replace(".", "_"), record.id),
            "record_model": record._name,
            "record_id": record.id,
            "source_type": source_type,
            "source_note": note,
            "source_url": False,
        }
        if source:
            source.write(values)
        else:
            Source.create(values)
        return source

    @api.model
    def _ensure_simulated_course_team(self, course, prodi):
        lecturers = (course.tim_pengampu_ids | course.koordinator_id).filtered(
            lambda lecturer: prodi in lecturer.prodi_ids
        )
        invalid_assignments = (
            course.tim_pengampu_ids | course.koordinator_id
        ) - lecturers
        if invalid_assignments:
            raise ValidationError(
                "Dosen di luar program studi terhubung ke mata kuliah %s."
                % course.display_name
            )
        if not lecturers:
            available = self.env["erpobe.master.dosen"].sudo().search([
                ("prodi_ids", "in", [prodi.id]),
            ], order="id")
            fixture_teacher_data = self.env["ir.model.data"].sudo().search([
                ("module", "=", "erpobe"),
                ("model", "=", "erpobe.master.dosen"),
                ("name", "=like", "fixture_teacher_%"),
                ("res_id", "in", available.ids),
            ])
            source_records = self.env[
                "erpobe.akademik.fixture.source"
            ].sudo().search([
                ("record_model", "=", "erpobe.master.dosen"),
                ("record_id", "in", fixture_teacher_data.mapped("res_id")),
                ("source_type", "in", ("dummy", "mixed")),
            ])
            lecturers = available.filtered(
                lambda lecturer: lecturer.id in source_records.mapped("record_id")
            )[:1]
            if not lecturers:
                raise ValidationError(
                    "Tidak ada dosen simulasi untuk %s; RPS tidak dapat diberi "
                    "tim pengampu tanpa mengubah identitas dosen."
                    % prodi.name
                )
        team = course.tim_pengampu_ids | lecturers
        values = {"tim_pengampu_ids": [Command.set(team.ids)]}
        if not course.koordinator_id:
            values["koordinator_id"] = lecturers[:1].id
        course.sudo().write(values)
        self._register_source(
            course,
            "mixed",
            "Mata kuliah berasal dari dokumen kurikulum resmi; tim pengampu "
            "ditambahkan sebagai simulasi.",
        )
        return course.tim_pengampu_ids

    @api.model
    def _ensure_simulated_rps_catalog(self, slug, prodi):
        seeder = self.env["erpobe.fixture.seeder"].sudo()
        methods = seeder._ensure_methods()
        for method in methods:
            seeder._mark_source(
                method, "dummy", "Metode pembelajaran untuk RPS simulasi."
            )

        reference_specs = (
            ("modul", "Modul pembelajaran %s (referensi simulasi)" % prodi.name),
            ("praktik", "Panduan praktik %s (referensi simulasi)" % prodi.name),
            ("kasus", "Kumpulan studi kasus %s (referensi simulasi)" % prodi.name),
            ("asesmen", "Panduan asesmen %s (referensi simulasi)" % prodi.name),
        )
        items = [
            (
                "fixture_reference_rps_%s_%s" % (slug, key),
                {
                    "judul": title,
                    "penulis": "Tim Akademik (simulasi)",
                    "tahun": "2025",
                    "jenis": "pendukung",
                    "prodi_id": prodi.id,
                },
            )
            for key, title in reference_specs
        ]
        seeder._preserve_existing_fixture_values(
            "erpobe.akademik.referensi", items
        )
        references = seeder._upsert_many("erpobe.akademik.referensi", items)
        for reference in references.values():
            seeder._mark_source(
                reference,
                "dummy",
                "Placeholder referensi simulasi; bukan sitasi akademik resmi.",
            )
        return methods, list(references.values())

    @api.model
    def _rps_content_is_complete(self, rps):
        return (
            len(rps.kegiatan_perkuliahan_ids) == 16
            and bool(rps.referensi_ids)
            and bool(rps.rubrik_penilaian_ids)
            and all(rubric.kriteria_ids for rubric in rps.rubrik_penilaian_ids)
            and bool(rps.tim_pengampu_ids)
            and bool(rps.koordinator_id)
        )

    @api.model
    def _populate_simulated_rps_content(
        self, rps, course, slug, methods, references, component_records
    ):
        seeder = self.env["erpobe.fixture.seeder"].sudo()
        cpmks = rps.cpmk_ids.sorted("kode_cpmk")
        if not cpmks:
            raise ValidationError(
                "RPS %s tidak memiliki CPMK untuk mengisi aktivitas."
                % course.display_name
            )
        if not methods or not references:
            raise ValidationError(
                "Katalog simulasi RPS belum lengkap untuk %s."
                % course.display_name
            )

        topics = (
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
            "praktik pemecahan masalah secara bertahap",
            "kerja kelompok dan tinjauan sejawat",
            "validasi solusi berdasarkan kriteria",
            "komunikasi hasil dan dokumentasi",
            "integrasi capaian pembelajaran",
            "refleksi dan evaluasi akhir",
        )
        activities_by_week = {}
        for activity in rps.kegiatan_perkuliahan_ids:
            if activity.minggu in activities_by_week:
                raise ValidationError(
                    "RPS %s memiliki aktivitas duplikat pada minggu %s."
                    % (course.display_name, activity.minggu)
                )
            activities_by_week[activity.minggu] = activity
        for week, topic in enumerate(topics, start=1):
            if week in activities_by_week:
                continue
            cpmk = cpmks[(week - 1) % len(cpmks)]
            activity = self.env[
                "erpobe.akademik.kegiatan.perkuliahan"
            ].sudo().create({
                "rps_id": rps.id,
                "minggu": week,
                "cpmk_id": cpmk.id,
                "bahan_kajian": "%s: %s" % (course.name, topic),
                "metode_pembelajaran_id": methods[(week - 1) % len(methods)].id,
                "pengalaman_belajar": (
                    "Mahasiswa mengerjakan latihan simulasi terkait %s dan "
                    "mendiskusikan hasilnya." % topic
                ),
                "indikator_penilaian": (
                    "Ketepatan analisis, penggunaan konsep, dan kejelasan "
                    "komunikasi (indikator simulasi)."
                ),
                "estimasi_waktu": 170,
                "referensi_ids": [Command.set([reference.id for reference in references])],
                "teknik_penilaian": "Latihan/studi kasus (simulasi)",
            })
            self._register_source(
                activity, "dummy", "Aktivitas mingguan RPS hasil simulasi."
            )

        grades = self.env["erpobe.master.grade"].sudo().search([
            ("name", "in", ("A", "B", "C", "D")),
        ])
        if set(grades.mapped("name")) != {"A", "B", "C", "D"}:
            raise ValidationError(
                "Master grade A-D harus tersedia untuk kriteria RPS simulasi."
            )
        descriptions = {
            "A": "Menguasai capaian dengan analisis tepat dan dokumentasi lengkap (simulasi).",
            "B": "Mencapai capaian dengan kekeliruan kecil yang tidak mendasar (simulasi).",
            "C": "Mencapai sebagian capaian dan memerlukan perbaikan pada analisis (simulasi).",
            "D": "Belum menunjukkan bukti capaian yang memadai (simulasi).",
        }
        for index, (component, spec) in enumerate(component_records):
            snapshot = rps.rps_komponen_ids.filtered(
                lambda item: item.komponen_id == component and item.aktif
            )[:1]
            if not snapshot:
                continue
            cpmk = cpmks.filtered(
                lambda item: item.kode_cpmk == spec.get("cpmk")
            )[:1] or cpmks[index % len(cpmks)]
            rubric = rps.rubrik_penilaian_ids.filtered(
                lambda item: item.komponen_id == component
            )[:1]
            if not rubric:
                rubric = self.env[
                    "erpobe.akademik.rubrik.penilaian"
                ].sudo().create({
                    "rps_id": rps.id,
                    "sequence": (index + 1) * 10,
                    "materi_soal": (
                        "%s: asesmen simulasi untuk %s."
                        % (component.name, course.name)
                    ),
                    "komponen_id": component.id,
                    "cpmk_id": cpmk.id,
                    "bobot": snapshot.bobot,
                })
                self._register_source(
                    rubric, "dummy", "Rubrik penilaian simulasi RPS."
                )

            existing_grade_ids = set(rubric.kriteria_ids.mapped("grade_id").ids)
            for grade in grades:
                if grade.id in existing_grade_ids:
                    continue
                criterion = self.env["erpobe.akademik.kriteria"].sudo().create({
                    "rubrik_id": rubric.id,
                    "grade_id": grade.id,
                    "deskripsi": descriptions[grade.name],
                })
                self._register_source(
                    criterion, "dummy", "Kriteria rubrik simulasi RPS."
                )

        values = {
            "referensi_ids": [
                Command.set((rps.referensi_ids | self.env[
                    "erpobe.akademik.referensi"
                ].browse([reference.id for reference in references])).ids)
            ],
        }
        if not rps.tujuan_pembelajaran:
            values["tujuan_pembelajaran"] = (
                "Menerapkan capaian pembelajaran mata kuliah %s melalui aktivitas "
                "dan asesmen simulasi." % course.name
            )
        if not rps.materi_pembelajaran:
            values["materi_pembelajaran"] = "\n".join(
                "%s. %s" % (index, topic)
                for index, topic in enumerate(topics, start=1)
            )
        if not rps.sumber_belajar:
            values["sumber_belajar"] = "\n".join(
                reference.judul for reference in references
            )
        if not rps.media_software:
            values["media_software"] = "Perangkat lunak sesuai topik (simulasi)."
        if not rps.media_hardware:
            values["media_hardware"] = "Perangkat pembelajaran kelas (simulasi)."
        rps.write(values)
        self._register_source(rps, "dummy", "RPS simulasi sinkron kurikulum OBE.")

    @api.model
    def sync_semester6_operations(self):
        affected_student_ids = set()
        importer = self.with_context(defer_khs_refresh=True)
        counts = importer._sync_semester6_operations(affected_student_ids)
        importer._sync_khs_batch(affected_student_ids)
        return counts

    @api.model
    def _sync_semester6_operations(self, affected_student_ids):
        period = self._activate_2025_genap()
        counts = {"rps": 0, "krs": 0, "krs_lines": 0, "component_grades": 0, "students": 0}
        for slug, (xmlid, _code, _filename) in PROGRAM_FILES.items():
            text = self._read_document(slug)
            prodi = self.env.ref("erpobe.%s" % xmlid)
            students = self.env["erpobe.master.mahasiswa"].sudo().search([
                ("angkatan", "=", 2022),
                ("prodi_id", "=", prodi.id),
            ])
            semester_courses = self.env["erpobe.master.matakuliah"].sudo().search([
                ("prodi_id", "=", prodi.id),
                ("semester", "=", 6),
                ("active", "=", True),
                ("identity_key", "!=", False),
            ])
            if not semester_courses:
                continue
            methods, references = self._ensure_simulated_rps_catalog(slug, prodi)

            mandatory_courses = semester_courses.filtered(
                lambda course: "Pilihan" not in (course.status_mk or "")
            )
            mandatory_sks = sum(mandatory_courses.mapped("sks"))
            if mandatory_sks > 24:
                details = ", ".join(
                    "%s %s (%s SKS)"
                    % (course.kode_mk, course.name, course.sks)
                    for course in mandatory_courses
                )
                raise ValidationError(
                    "Konflik kurikulum: mata kuliah wajib semester 6 %s berjumlah "
                    "%s SKS, melebihi batas KRS 24 SKS. Periksa kurikulum tanpa "
                    "menghapus mata kuliah wajib. Rincian: %s."
                    % (prodi.name, mandatory_sks, details)
                )
            krs_courses = list(mandatory_courses)
            remaining_sks = 24 - mandatory_sks
            elective_courses = semester_courses.filtered(
                lambda course: "Pilihan" in (course.status_mk or "")
            ).sorted(lambda course: (course.identity_key or "", course.id))
            for course in elective_courses:
                if course.sks <= remaining_sks:
                    krs_courses.append(course)
                    remaining_sks -= course.sks

            rombels = self.env["erpobe.master.rombel"].sudo().search([
                ("prodi_id", "=", prodi.id),
                ("angkatan", "=", 2022),
            ])
            offer = self.env["erpobe.akademik.penawaran"].sudo().search([
                ("tahun_ajaran", "=", period.id),
                ("prodi_id", "=", prodi.id),
            ], limit=1)
            if not offer:
                offer = self.env["erpobe.akademik.penawaran"].sudo().create({
                    "tahun_ajaran": period.id,
                    "prodi_id": prodi.id,
                    "rombel_ids": [Command.set(rombels.ids)],
                })
            else:
                offer.write({"rombel_ids": [Command.set(rombels.ids)]})

            lines_by_course = {}
            for course in semester_courses:
                self._ensure_simulated_course_team(course, prodi)
                line = offer.line_ids.filtered(
                    lambda item: item.matakuliah_id == course
                )[:1]
                if not line:
                    line = self.env["erpobe.akademik.penawaran.line"].sudo().create({
                        "penawaran_id": offer.id,
                        "matakuliah_id": course.id,
                        "rombel_ids": [Command.set(rombels.ids)],
                    })
                else:
                    line.write({"rombel_ids": [Command.set(rombels.ids)]})
                lines_by_course[course.id] = line

                rps = self.env["erpobe.akademik.rps"].sudo().search([
                    ("matakuliah_id", "=", course.id),
                    ("penawaran_line_id", "=", line.id),
                ], order="version desc, id desc", limit=1)
                if not rps:
                    rps = self.env["erpobe.akademik.rps"].sudo().create({
                        "matakuliah_id": course.id,
                        "penawaran_line_id": line.id,
                        "tujuan_pembelajaran": "Dummy RPS mengikuti CPL, CPMK, dan bobot kurikulum OBE 2025.",
                        "materi_pembelajaran": "Materi disusun berdasarkan karakter dan nama mata kuliah.",
                    })
                if rps.status == "final" and not self._rps_content_is_complete(rps):
                    rps = rps.copy()

                component_specs = [
                    item for item in self.parse_components(text)
                    if item["course"] == course.kode_mk
                    and item["course_name"] == course.name
                ]
                component_records = []
                seen_names = set()
                for spec in component_specs:
                    name = spec["name"]
                    key = (name, self._component_type(name))
                    if key in seen_names:
                        continue
                    seen_names.add(key)
                    component = self.env["erpobe.akademik.komponen"].sudo().search([
                        ("name", "=", name),
                        ("tipe", "=", key[1]),
                    ], limit=1)
                    if not component:
                        component = self.env["erpobe.akademik.komponen"].sudo().create({
                            "name": name,
                            "tipe": key[1],
                            "description": spec["method"],
                            "aktif": True,
                        })
                    component_records.append((component, spec))

                if not component_records:
                    component_records = self._default_semester6_components(course)

                if rps.status != "final":
                    rps.write({
                        "komponen_ids": [Command.set([item[0].id for item in component_records])],
                    })
                    rps._sync_bobot_tables()

                cpmk_weights = [
                    item for item in self.parse_cpmk_mk_weights(text)
                    if item["course"] == course.kode_mk
                    and item["course_name"] == course.name
                ]
                cpmk_weight_by_code = {
                    item["cpmk"]: item["weight"] for item in cpmk_weights
                }
                if rps.status != "final":
                    for weight_line in rps.bobot_cpmk_mk_ids:
                        weight = cpmk_weight_by_code.get(weight_line.cpmk_id.kode_cpmk)
                        if weight is None:
                            continue
                        weight_line.write({"bobot_cpmk_mk": weight})

                if rps.status != "final":
                    for snapshot in rps.rps_komponen_ids.filtered("aktif"):
                        spec = next(
                            (
                                spec for component, spec in component_records
                                if component == snapshot.komponen_id
                            ),
                            None,
                        )
                        if spec:
                            snapshot.write({"bobot": spec["weight"], "aktif": True})

                if rps.status != "final":
                    snapshot_total = sum(
                        snapshot.bobot for snapshot in rps.rps_komponen_ids.filtered("aktif")
                    )
                    if snapshot_total <= 0:
                        snapshots = rps.rps_komponen_ids.filtered("aktif")
                        weights = self._distribute_weights(100.0, len(snapshots))
                        for snapshot, weight in zip(snapshots, weights):
                            snapshot.write({"bobot": weight})

                if rps.status != "final":
                    for snapshot in rps.rps_komponen_ids.filtered("aktif"):
                        spec = next(
                            (
                                spec for component, spec in component_records
                                if component == snapshot.komponen_id
                            ),
                            None,
                        )
                        if not spec:
                            continue
                        cpmk = rps.cpmk_ids.filtered(
                            lambda item: item.kode_cpmk == spec["cpmk"]
                        )[:1]
                        if not cpmk:
                            continue
                        allocation = rps.bobot_komponen_cpmk_ids.filtered(
                            lambda item: item.rps_komponen_id == snapshot
                            and item.cpmk_id == cpmk
                        )[:1]
                        if allocation:
                            allocation.write({"bobot_komponen_cpmk": 100.0})

                if rps.status != "final":
                    grade_cpmk = self.env["erpobe.grade.cpmk"].sudo().search([
                        ("rps_id", "=", rps.id),
                    ])
                    grade_mk = self.env["erpobe.grade.mk"].sudo().search([
                        ("rps_id", "=", rps.id),
                    ])
                    affected_student_ids.update(
                        grade_cpmk.mapped("mahasiswa_id").ids
                    )
                    affected_student_ids.update(grade_mk.mapped("mahasiswa_id").ids)
                    self._populate_simulated_rps_content(
                        rps,
                        course,
                        slug,
                        methods,
                        references,
                        component_records,
                    )
                    if rps.status == "draft":
                        rps.action_mark_for_review()
                    validation = self.env["erpobe.weight.validation"].validate_rps(rps)
                    if not validation["complete"]:
                        details = "; ".join(
                            f"{item['item_name']} ({item['relation']}): {item['total']:.2f}%"
                            for item in validation["problems"]
                        )
                        raise ValidationError(
                            f"Bobot RPS {course.name} belum valid: {details}"
                        )
                    rps.action_finalize()
                self._register_source(
                    rps, "dummy", "RPS simulasi sinkron kurikulum OBE 2025."
                )
                rps._link_finalized_to_offer(line)
                counts["rps"] += 1

            counts["students"] += len(students)
            existing_krs = self.env["erpobe.akademik.krs"].sudo().search([
                ("mahasiswa_id", "in", students.ids),
                ("penawaran_id", "=", offer.id),
            ])
            affected_student_ids.update(
                self._remove_obsolete_fixture_krs_lines(existing_krs)
            )
            existing_krs_by_student = {
                krs.mahasiswa_id.id: krs for krs in existing_krs
            }

            for student in students:
                krs = existing_krs_by_student.get(student.id)
                existing_lines = krs.line_ids if krs else self.env[
                    "erpobe.akademik.krs.line"
                ]
                existing_course_ids = set(
                    existing_lines.mapped("matakuliah_id").ids
                )
                missing_courses = [
                    course for course in krs_courses
                    if course.id not in existing_course_ids
                ]
                projected_sks = sum(existing_lines.mapped("sks")) + sum(
                    course.sks for course in missing_courses
                )
                if projected_sks > 24:
                    details = ", ".join(
                        "%s %s (%s SKS)"
                        % (line.matakuliah_kode, line.matakuliah_name, line.sks)
                        for line in existing_lines
                    )
                    details += (", " if details else "") + ", ".join(
                        "%s %s (%s SKS)"
                        % (course.kode_mk, course.name, course.sks)
                        for course in missing_courses
                    )
                    raise ValidationError(
                        "KRS mahasiswa %s (%s, %s) akan berjumlah %s SKS, "
                        "melebihi batas 24 SKS. KRS lama dipertahankan; periksa "
                        "pilihan mata kuliah dan riwayat akademik. Rincian: %s."
                        % (
                            student.nim,
                            prodi.name,
                            student.rombel_id.name,
                            projected_sks,
                            details,
                        )
                    )

            for student in students:
                krs = self.env["erpobe.akademik.krs"].sudo().search([
                    ("mahasiswa_id", "=", student.id),
                    ("penawaran_id", "=", offer.id),
                ], limit=1)
                if not krs:
                    krs = self.env["erpobe.akademik.krs"].sudo().create({
                        "mahasiswa_id": student.id,
                        "penawaran_id": offer.id,
                        "state": "approved",
                        "max_sks_allowed": 24,
                        "advisor_note": "KRS dummy semester 6 mengikuti kurikulum OBE 2025.",
                    })
                    counts["krs"] += 1
                    affected_student_ids.add(student.id)

                for course in krs_courses:
                    line = krs.line_ids.filtered(
                        lambda item: item.matakuliah_id == course
                    )[:1]
                    if not line:
                        self.env["erpobe.akademik.krs.line"].sudo().create({
                            "krs_id": krs.id,
                            "penawaran_line_id": lines_by_course[course.id].id,
                            "status_pengambilan": "baru",
                        })
                        counts["krs_lines"] += 1
                        affected_student_ids.add(student.id)

        counts["component_grades"] = self._generate_dummy_grades(
            force=False,
            affected_student_ids=affected_student_ids,
        )
        return counts

    @api.model
    def _remove_obsolete_fixture_krs_lines(self, krs_records):
        lines = krs_records.mapped("line_ids")
        if not lines:
            return set()

        legacy_courses = lines.mapped("matakuliah_id").filtered(
            lambda course: not course.identity_key and course.semester == 6
        )
        if not legacy_courses:
            return set()
        fixture_sources = self.env["erpobe.akademik.fixture.source"].sudo().search([
            ("record_model", "=", "erpobe.master.matakuliah"),
            ("record_id", "in", legacy_courses.ids),
            ("source_type", "in", ("dummy", "mixed")),
        ])
        fixture_course_ids = set(fixture_sources.mapped("record_id"))
        obsolete_lines = lines.filtered(
            lambda line: line.matakuliah_id.id in fixture_course_ids
        )
        if not obsolete_lines:
            return set()

        affected_student_ids = set(obsolete_lines.mapped("mahasiswa_id").ids)
        line_ids = obsolete_lines.ids
        grades = self.env["erpobe.grade.komponen"].sudo().search([
            ("krs_line_id", "in", line_ids),
        ])
        non_simulated_grades = grades.filtered(
            lambda grade: grade.origin != "simulated"
        )
        if non_simulated_grades:
            affected = ", ".join(
                "%s / %s"
                % (grade.mahasiswa_nim, grade.krs_line_id.matakuliah_id.display_name)
                for grade in non_simulated_grades
            )
            raise ValidationError(
                "KRS fixture lama memiliki nilai non-simulasi; data dipertahankan "
                "dan perlu migrasi manual sebelum sinkronisasi kurikulum resmi: %s."
                % affected
            )

        linked_cpl_grades = self.env["erpobe.grade.cpl"].sudo().search([
            ("krs_line_id", "in", line_ids),
        ])
        if linked_cpl_grades:
            raise ValidationError(
                "KRS fixture lama memiliki nilai CPL yang terhubung langsung ke "
                "detail KRS; data dipertahankan dan perlu migrasi manual."
            )

        audits = self.env["erpobe.grade.komponen.audit"].sudo().search([
            ("grade_id", "in", grades.ids),
        ])
        invalid_audits = audits.filtered(
            lambda audit: (
                audit.reason != "Initial grade entry"
                or audit.old_value != 0
                or audit.new_value != audit.grade_id.nilai
            )
        )
        if invalid_audits:
            affected = ", ".join(
                "%s / %s"
                % (
                    audit.mahasiswa_nim,
                    audit.krs_line_id.matakuliah_id.display_name,
                )
                for audit in invalid_audits
            )
            raise ValidationError(
                "KRS fixture lama memiliki riwayat nilai di luar nilai simulasi "
                "awal; data dipertahankan dan perlu migrasi manual: %s."
                % affected
            )

        reports = self.env["erpobe.report.khs"].sudo().search([
            ("mahasiswa_id", "in", obsolete_lines.mapped("mahasiswa_id").ids),
        ])
        if reports:
            reports.write({
                "mk_line_ids": [Command.clear()],
                "cpmk_line_ids": [Command.clear()],
                "cpl_line_ids": [Command.clear()],
                "komponen_line_ids": [Command.clear()],
            })

        audits._unlink_fixture_generated_simulation()
        self.env["erpobe.grade.cpmk"].sudo().search([
            ("krs_line_id", "in", line_ids),
        ]).with_context(skip_khs_refresh=True).unlink()
        self.env["erpobe.grade.mk"].sudo().search([
            ("krs_line_id", "in", line_ids),
        ]).with_context(skip_khs_refresh=True).unlink()
        grades.with_context(skip_khs_refresh=True).unlink()
        obsolete_lines.with_context(skip_khs_refresh=True).unlink()
        return affected_student_ids

    def _distribute_weights(self, total, count):
        if count <= 0:
            return []
        base = total / count
        values = [round(base, 2) for _ in range(count)]
        values[-1] = round(total - sum(values[:-1]), 2)
        return values

    def _default_semester6_components(self, course):
        defaults = (
            ("Tugas", "assignment", 20.0, "CPMK-01", 100.0),
            ("Ujian/Analisis Individu", "midterm", 20.0, "CPMK-02", 100.0),
            ("Proyek/Studi Kasus Terapan", "project", 40.0, "CPMK-03", 66.67),
            ("Presentasi/Portofolio", "presentation", 20.0, "CPMK-03", 33.33),
        )
        result = []
        for name, kind, _weight, cpmk_code, cpmk_weight in defaults:
            component = self.env["erpobe.akademik.komponen"].sudo().search([
                ("name", "=", name),
                ("tipe", "=", kind),
            ], limit=1)
            if not component:
                component = self.env["erpobe.akademik.komponen"].sudo().create({
                    "name": name,
                    "tipe": kind,
                    "aktif": True,
                })
            result.append((component, {
                "course": course.kode_mk,
                "course_name": course.name,
                "name": name,
                "cpmk": cpmk_code,
                "method": "Dummy asesmen berdasarkan kurikulum.",
                "weight": _weight,
                "cpmk_weight": cpmk_weight,
            }))
        return result

    @api.model
    def generate_dummy_grades(self, force=False):
        affected_student_ids = set()
        importer = self.with_context(defer_khs_refresh=True)
        count = importer._generate_dummy_grades(
            force=force,
            affected_student_ids=affected_student_ids,
        )
        importer._sync_khs_batch(affected_student_ids)
        return count

    @api.model
    def _generate_dummy_grades(self, force, affected_student_ids):
        """Generate or regenerate only origin=simulated component grades."""
        count = 0
        Grade = self.env["erpobe.grade.komponen"].sudo().with_context(
            skip_khs_refresh=True,
            defer_academic_recompute=True,
        )
        GradeCpmk = self.env["erpobe.grade.cpmk"].sudo().with_context(
            skip_khs_refresh=True
        )
        GradeMk = self.env["erpobe.grade.mk"].sudo().with_context(
            skip_khs_refresh=True
        )
        GradeCpl = self.env["erpobe.grade.cpl"].sudo().with_context(
            skip_khs_refresh=True
        )
        students_to_refresh = set()
        for line in self.env["erpobe.akademik.krs.line"].sudo().search([
            ("krs_id.state", "=", "approved"),
        ]):
            rps = line.penawaran_line_id.latest_rps_id
            if not rps or rps.status != "final":
                continue
            input_record = self.env["erpobe.input.nilai"].sudo().search([
                ("penawaran_line_id", "=", line.penawaran_line_id.id),
            ], limit=1)
            if not input_record:
                input_record = self.env["erpobe.input.nilai"].sudo().create({
                    "penawaran_id": line.penawaran_line_id.penawaran_id.id,
                    "penawaran_line_id": line.penawaran_line_id.id,
                })
            for snapshot_index, snapshot in enumerate(
                rps.rps_komponen_ids.filtered("aktif").sorted("sequence")
            ):
                existing = Grade.search([
                    ("krs_line_id", "=", line.id),
                    ("komponen_id", "=", snapshot.komponen_id.id),
                ], limit=1)
                if existing and existing.origin == "actual":
                    continue
                if existing and existing.origin == "simulated" and not force:
                    continue
                seed_text = "%s|%s|%s|%s" % (
                    line.mahasiswa_id.nim,
                    line.matakuliah_id.kode_mk,
                    snapshot.komponen_id.tipe,
                    snapshot_index,
                )
                if force:
                    rng = random.SystemRandom()
                else:
                    seed = int(hashlib.sha256(seed_text.encode("utf-8")).hexdigest()[:16], 16)
                    rng = random.Random(seed)
                band = rng.choice((92, 82, 72, 61))
                score = max(55, min(98, band + rng.randint(-10, 10)))
                values = {
                    "input_nilai_id": input_record.id,
                    "krs_line_id": line.id,
                    "komponen_id": snapshot.komponen_id.id,
                    "rps_id": rps.id,
                    "rps_komponen_id": snapshot.id,
                    "origin": "simulated",
                    "is_graded": True,
                    "nilai": score,
                }
                if existing:
                    existing.write(values)
                else:
                    Grade.create(values)
                count += 1
                students_to_refresh.add(line.mahasiswa_id.id)

            recompute_students = line.mahasiswa_id
            cpmk_grades = GradeCpmk.search([
                ("mahasiswa_id", "=", line.mahasiswa_id.id),
                ("krs_line_id", "=", line.id),
            ])
            if not cpmk_grades:
                for cpmk in rps.cpmk_ids:
                    cpmk_grades |= GradeCpmk.create({
                        "mahasiswa_id": line.mahasiswa_id.id,
                        "cpmk_id": cpmk.id,
                        "krs_line_id": line.id,
                        "rps_id": rps.id,
                    })
                students_to_refresh.add(line.mahasiswa_id.id)
            cpmk_grades._compute_nilai_cpmk()

            mk_grade = GradeMk.search([
                ("mahasiswa_id", "=", line.mahasiswa_id.id),
                ("mk_id", "=", line.matakuliah_id.id),
                ("krs_line_id", "=", line.id),
            ], limit=1)
            if not mk_grade:
                mk_grade = GradeMk.create({
                    "mahasiswa_id": line.mahasiswa_id.id,
                    "mk_id": line.matakuliah_id.id,
                    "krs_line_id": line.id,
                    "rps_id": rps.id,
                })
                students_to_refresh.add(line.mahasiswa_id.id)
            mk_grade._compute_nilai_mk()

            for cpl in rps.cpl_ids:
                cpl_grade = GradeCpl.search([
                    ("mahasiswa_id", "=", recompute_students.id),
                    ("cpl_id", "=", cpl.id),
                ], limit=1)
                if not cpl_grade:
                    cpl_grade = GradeCpl.create({
                        "mahasiswa_id": recompute_students.id,
                        "cpl_id": cpl.id,
                    })
                    students_to_refresh.add(line.mahasiswa_id.id)
                cpl_grade._compute_nilai_cpl()

        affected_student_ids.update(students_to_refresh)
        return count

    @api.model
    def import_one(self, slug, xmlid, text):
        prodi = self.env.ref("erpobe.%s" % xmlid)
        document_name = PROGRAM_FILES[slug][2]
        source_note = "Data kurikulum resmi dari docs/kurikulum/%s." % document_name
        cpl_specs = self.parse_cpls(text)
        course_specs = self.parse_courses(text)
        cpmk_specs = self.parse_cpmks(text)
        mapping_specs = self.parse_cpl_cpmk_mapping(text)
        cpl_weight_specs = self.parse_cpl_cpmk_weights(text)
        cpmk_weight_specs = self.parse_cpmk_mk_weights(text)
        component_specs = self.parse_components(text)

        curriculum = self.env["erpobe.akademik.kurikulum"].sudo().search([
            ("prodi_id", "=", prodi.id),
            ("kode", "=", "KUR-2025"),
        ], limit=1)
        if not curriculum:
            curriculum = self.env["erpobe.akademik.kurikulum"].sudo().create({
                "name": "Kurikulum OBE 2025",
                "kode": "KUR-2025",
                "prodi_id": prodi.id,
                "angkatan_mulai": 2025,
                "source_type": "official",
                "source_note": "Diimpor dari dokumen kurikulum OBE resmi Tahun 2025.",
            })
        else:
            curriculum.write({
                "name": "Kurikulum OBE 2025",
                "angkatan_mulai": 2025,
                "source_type": "official",
                "source_note": "Diimpor dari dokumen kurikulum OBE resmi Tahun 2025.",
            })
        self._register_source(curriculum, "official", source_note)

        cpls = {}
        for spec in cpl_specs:
            record = self.env["erpobe.akademik.cpl"].sudo().search([
                ("prodi_id", "=", prodi.id),
                ("kode_cpl", "=", spec["code"]),
            ], limit=1)
            values = {
                "prodi_id": prodi.id,
                "kode_cpl": spec["code"],
                "nama_cpl": spec["title"],
                "name": spec["description"],
                "indikator_capaian": spec["category"],
            }
            if record:
                record.write(values)
            else:
                record = self.env["erpobe.akademik.cpl"].sudo().create(values)
            self._register_source(record, "official", source_note)
            cpls[spec["code"]] = record

        courses = {}
        for index, spec in enumerate(course_specs, start=1):
            identity = "%s|%s|%s" % (spec["code"], spec["semester"], spec["name"])
            record = self.env["erpobe.master.matakuliah"].sudo().search([
                ("prodi_id", "=", prodi.id),
                ("identity_key", "=", identity),
            ], limit=1)
            values = {
                "name": spec["name"],
                "kode_mk": spec["code"],
                "identity_key": identity,
                "sks": spec["sks"],
                "sks_teori": spec["theory"],
                "sks_praktik": spec["practice"],
                "status_mk": spec["status"],
                "semester": spec["semester"],
                "active": True,
                "prodi_id": prodi.id,
                "kurikulum_id": curriculum.id,
                "deskripsi_mk": "Mata kuliah dari Kurikulum OBE Tahun 2025.",
            }
            if record:
                record.write(values)
            else:
                record = self.env["erpobe.master.matakuliah"].sudo().create(values)
            self._register_source(record, "official", source_note)
            courses[(spec["code"], spec["name"])] = record
            courses.setdefault(spec["code"], record)

        cpmks = {}
        for spec in cpmk_specs:
            course = courses.get((spec["course_code"], spec["course_name"]))
            if not course:
                course = courses.get(spec["course_code"])
            if not course:
                raise ValidationError(
                    "CPMK merujuk mata kuliah tidak ditemukan: %s" % spec["course_code"]
                )
            record = self.env["erpobe.akademik.cpmk"].sudo().search([
                ("mk_id", "=", course.id),
                ("kode_cpmk", "=", spec["code"]),
            ], limit=1)
            values = {
                "mk_id": course.id,
                "kode_cpmk": spec["code"],
                "name": spec["description"],
                "indikator": spec["title"],
            }
            if record:
                record.write(values)
            else:
                record = self.env["erpobe.akademik.cpmk"].sudo().create(values)
            self._register_source(record, "official", source_note)
            cpmks[(spec["course_code"], spec["course_name"], spec["code"])] = record
            cpmks.setdefault((spec["course_code"], spec["code"]), record)

        for course_code, course_name, cpmk_code, cpl_code in mapping_specs:
            course = courses.get((course_code, course_name)) or courses.get(course_code)
            cpmk = cpmks.get((course_code, course_name, cpmk_code)) or cpmks.get((course_code, cpmk_code))
            cpl = cpls.get(cpl_code)
            if not course or not cpmk or not cpl:
                raise ValidationError(
                    "Pemetaan CPL–CPMK tidak valid: %s / %s / %s"
                    % (course_code, cpmk_code, cpl_code)
                )
            mapping = self.env["erpobe.akademik.cpl.mk.cpmk"].sudo().search([
                ("cpmk_id", "=", cpmk.id),
                ("cpl_id", "=", cpl.id),
            ], limit=1)
            weight = next(
                (
                    item["weight"]
                    for item in cpl_weight_specs
                    if item["course"] == course_code
                    and item["cpmk"] == cpmk_code
                    and item["cpl"] == cpl_code
                ),
                0.0,
            )
            if not mapping:
                mapping = self.env["erpobe.akademik.cpl.mk.cpmk"].sudo().create({
                    "cpmk_id": cpmk.id,
                    "cpl_id": cpl.id,
                    "bobot_cpl_cpmk": weight,
                })
            else:
                mapping.write({"bobot_cpl_cpmk": weight})
            self._register_source(mapping, "official", source_note)

            mk_cpl = self.env["erpobe.akademik.mk.cpl"].sudo().search([
                ("mk_id", "=", course.id),
                ("cpl_id", "=", cpl.id),
            ], limit=1)
            if not mk_cpl:
                mk_cpl = self.env["erpobe.akademik.mk.cpl"].sudo().create({
                    "mk_id": course.id,
                    "cpl_id": cpl.id,
                })
            self._register_source(mk_cpl, "official", source_note)

        for spec in cpmk_weight_specs:
            course = courses.get(spec["course"])
            if not course:
                raise ValidationError("Bobot merujuk mata kuliah tidak ditemukan: %s" % spec["course"])
            cpmks_for_course = course.cpmk_ids
            cpmk = cpmks_for_course.filtered(lambda item: item.kode_cpmk == spec["cpmk"])
            if not cpmk:
                raise ValidationError("CPMK untuk bobot tidak ditemukan: %s / %s" % (spec["course"], spec["cpmk"]))

        component_names = set()
        for spec in component_specs:
            if spec["course"] not in courses:
                raise ValidationError("Komponen merujuk mata kuliah tidak ditemukan: %s" % spec["course"])
            component_names.add((spec["name"], self._component_type(spec["name"])))
        for name, kind in sorted(component_names):
            component = self.env["erpobe.akademik.komponen"].sudo().search([
                ("name", "=", name),
                ("tipe", "=", kind),
            ], limit=1)
            if not component:
                component = self.env["erpobe.akademik.komponen"].sudo().create({
                    "name": name,
                    "tipe": kind,
                    "aktif": True,
                })

        for course_spec in course_specs:
            course = courses[course_spec["code"]]
            course_weights = [
                item for item in cpmk_weight_specs
                if item["course"] == course_spec["code"]
                and item["course_name"] == course_spec["name"]
            ]
            if course_weights and abs(sum(item["weight"] for item in course_weights) - 100.0) > 0.01:
                raise ValidationError(
                    "Total bobot CPMK–MK tidak 100%% untuk %s" % course_spec["code"]
                )
            course_components = [
                item for item in component_specs
                if item["course"] == course_spec["code"]
                and item.get("course_name", course_spec["name"]) == course_spec["name"]
            ]
            if course_components and abs(sum(item["weight"] for item in course_components) - 100.0) > 0.01:
                raise ValidationError(
                    "Total bobot komponen tidak 100%% untuk %s" % course_spec["code"]
                )

        return {
            "prodi": prodi.name,
            "courses": len(course_specs),
            "cpls": len(cpl_specs),
            "cpmks": len(cpmk_specs),
            "mappings": len(mapping_specs),
            "components": len(component_specs),
        }
