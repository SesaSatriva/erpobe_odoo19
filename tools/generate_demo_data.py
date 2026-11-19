#!/usr/bin/env python3
"""Generate the small demo bootstrap XML; academic records are seeded by Odoo."""

from pathlib import Path
from xml.etree import ElementTree


MODULE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = MODULE_DIR / "data"

PROGRAMS = (
    ("prodi_ti", "Teknik Industri", "IN"),
    ("prodi_si", "Teknik Sipil", "SI"),
    ("prodi_mf", "Teknik Manufaktur", "MF"),
    ("prodi_el", "Teknik Elektro", "EL"),
)

YEARS = tuple(
    (f"{start}/{start + 1}", term, start == 2026 and term == "ganjil")
    for start in range(2022, 2027)
    for term in ("ganjil", "genap")
)


def _xml_text(element):
    return ElementTree.tostring(
        element,
        encoding="utf-8",
        xml_declaration=True,
    ).decode("utf-8")


def _record(root, record_id, model, fields):
    record = ElementTree.SubElement(
        root, "record", {"id": record_id, "model": model}
    )
    for name, value in fields:
        field = ElementTree.SubElement(record, "field", {"name": name})
        if isinstance(value, tuple) and value[0] == "ref":
            field.set("ref", value[1])
        elif isinstance(value, bool):
            field.set("eval", "True" if value else "False")
        else:
            field.text = str(value)
    return record


def generate_programs():
    root = ElementTree.Element("odoo", {"noupdate": "1"})
    _record(
        root,
        "fakultas_teknik",
        "erpobe.master.fakultas",
        (("name", "Fakultas Teknik"), ("kode", "FT")),
    )
    for xmlid, name, code in PROGRAMS:
        _record(
            root,
            xmlid,
            "erpobe.master.prodi",
            (
                ("name", name),
                ("kode", code),
                ("fakultas_id", ("ref", "erpobe.fakultas_teknik")),
            ),
        )
    return _xml_text(root)


def generate_years_and_classes():
    root = ElementTree.Element("odoo", {"noupdate": "1"})
    for year, term, active in YEARS:
        xmlid = f"ta_{year.replace('/', '_')}_{term}"
        _record(
            root,
            xmlid,
            "erpobe.akademik.tahunajaran",
            (("tahun_ajaran", year), ("semester", term), ("aktif", active)),
        )

    for xmlid, _name, code in PROGRAMS:
        prefix = code.lower()
        for cohort in (2022, 2026):
            for letter in ("a", "b", "c", "d"):
                _record(
                    root,
                    f"rombel_{prefix}_{cohort}_{letter}",
                    "erpobe.master.rombel",
                    (
                        ("name", letter.upper()),
                        ("angkatan", cohort),
                        ("prodi_id", ("ref", f"erpobe.{xmlid}")),
                    ),
                )
    return _xml_text(root)


def generate_assessment_components():
    root = ElementTree.Element("odoo", {"noupdate": "1"})
    components = (
        ("komponen_kognitif", "Penilaian Kognitif", "kognitif"),
        ("komponen_partisipatif", "Penilaian Partisipatif", "partisipatif"),
        ("fixture_component_project", "Penilaian Proyek", "partisipatif"),
        ("fixture_component_exam", "Ujian Akhir", "kognitif"),
    )
    for xmlid, name, kind in components:
        _record(
            root,
            xmlid,
            "erpobe.akademik.komponen",
            (("name", name), ("tipe", kind)),
        )
    return _xml_text(root)


def generate_fixture_loader():
    root = ElementTree.Element("odoo")
    ElementTree.SubElement(
        root,
        "function",
        {"model": "erpobe.fixture.seeder", "name": "load_2022_cohort"},
    )
    return _xml_text(root)


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    files = {
        "demo_01_fakultas_prodi.xml": generate_programs(),
        "demo_02_tahun_ajaran_rombels.xml": generate_years_and_classes(),
        "demo_05_komponen_bobot.xml": generate_assessment_components(),
        "demo_12_academic_fixture.xml": generate_fixture_loader(),
    }
    for filename, content in files.items():
        (DATA_DIR / filename).write_text(content + "\n", encoding="utf-8")
        print(f"Generated {DATA_DIR / filename}")


if __name__ == "__main__":
    main()
