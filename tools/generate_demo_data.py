#!/usr/bin/env python3
"""Generate ERP OBE demo data XML files for the supported programs."""

import os
import random
import textwrap

# ---------------------------------------------------------------
# Reference data
# ---------------------------------------------------------------

FAKULTAS = [
    {"id": "fakultas_teknik", "name": "Fakultas Teknik", "kode": "FT"},
]

PROGRAMS = [
    {"id": "prodi_ti", "name": "Teknik Industri", "kode": "IN"},
    {"id": "prodi_si", "name": "Teknik Sipil", "kode": "SI"},
    {"id": "prodi_mf", "name": "Teknik Manufaktur", "kode": "MF"},
    {"id": "prodi_el", "name": "Teknik Elektro", "kode": "EL"},
]

YEARS = [
    ("2022/2023", "ganjil", False),
    ("2022/2023", "genap", False),
    ("2023/2024", "ganjil", False),
    ("2023/2024", "genap", False),
    ("2024/2025", "ganjil", False),
    ("2024/2025", "genap", False),
    ("2025/2026", "ganjil", False),
    ("2025/2026", "genap", False),
    ("2026/2027", "ganjil", True),
    ("2026/2027", "genap", False),
]

ROMBEL_NAMES = ["A", "B", "C", "D"]

RANDOM = random.Random(42)

FIRST_NAMES = [
    "Ahmad", "Budi", "Citra", "Dedi", "Eka", "Fajar", "Galih", "Hesti",
    "Indra", "Joko", "Krisna", "Lestari", "Mahendra", "Nia", "Omar", "Putri",
    "Rizki", "Sari", "Taufik", "Winda", "Yoga", "Zahra", "Bagus", "Dewi",
]
LAST_NAMES = [
    "Wijaya", "Santoso", "Kurnia", "Prasetyo", "Wibowo", "Fauzi", "Ramadhan",
    "Wijaya", "Utomo", "Santoso", "Kusuma", "Pramesih", "Hartono", "Nugroho",
    "Firmansyah", "Widya",
]


def student_nim(prodi_code, angkatan, i):
    angkatan_int = int(angkatan)
    return f"{angkatan_int}{prodi_code.upper()}{str(i + 1).zfill(3)}"


def student_email(prodi_code, angkatan, i):
    return f"mhs.{prodi_code.lower()}.{angkatan}.{i + 1}@example.com"


def student_name(i, suffix=""):
    first = FIRST_NAMES[i % len(FIRST_NAMES)]
    last = LAST_NAMES[(i // len(FIRST_NAMES)) % len(LAST_NAMES)]
    return f"{first} {last} {suffix}".strip()


def generate_students(prodi_code, prodi_id, angkatan, count=24):
    students = []
    per_rombel = count // 2
    for i in range(count):
        rombel_letter = "a" if i < per_rombel else "b"
        students.append({
            "id": f"mhs_{prodi_code.lower()}_{angkatan}_{i + 1:03d}",
            "name": student_name(i, f"{angkatan}"),
            "nim": student_nim(prodi_code, angkatan, i),
            "email": student_email(prodi_code, angkatan, i),
            "prodi_id": prodi_id,
            "rombel_id": f"rombel_{prodi_code.lower()}_{angkatan}_{rombel_letter}",
        })
    return students


# ---------------------------------------------------------------
# XML generation helpers
# ---------------------------------------------------------------

def xstr(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def xml_record(record_id, model, fields):
    lines = [f'    <record id="{record_id}" model="{model}">']
    for key, val in fields.items():
        if val is None:
            continue
        if isinstance(val, bool):
            val_str = "True" if val else "False"
        elif isinstance(val, (int, float)):
            val_str = str(val)
        elif isinstance(val, str):
            val_str = f'"{xstr(val)}"'
        else:
            val_str = f'"{xstr(str(val))}"'
        lines.append(f'        <field name="{key}" eval="{val_str}" />')
    lines.append("    </record>")
    return "\n".join(lines)


def q(x):
    return f'"{xstr(x)}"' if x is not None else ""


# ---------------------------------------------------------------
# Generate demo_01_fakultas_prodi.xml
# ---------------------------------------------------------------

def gen_demo_01():
    lines = [
        "<?xml version='1.0' encoding='utf-8'?>",
        '<odoo noupdate="1">',
        "    <record id=\"fakultas_teknik\" model=\"erpobe.master.fakultas\">",
        "        <field name=\"name\">Fakultas Teknik</field>",
        "        <field name=\"kode\">FT</field>",
        "    </record>",
    ]
    for prog in PROGRAMS:
        lines.append(f'    <record id="{prog["id"]}" model="erpobe.master.prodi">')
        lines.append(f'        <field name="name">{prog["name"]}</field>')
        lines.append(f'        <field name="kode">{prog["kode"]}</field>')
        lines.append('        <field name="fakultas_id" ref="erpobe.fakultas_teknik" />')
        lines.append("    </record>")
    lines.append("</odoo>")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------
# Generate demo_02_tahun_ajaran_rombels.xml
# ---------------------------------------------------------------

def gen_demo_02():
    lines = [
        "<?xml version='1.0' encoding='utf-8'?>",
        '<odoo noupdate="1">',
    ]
    for tahun, semester, aktif in YEARS:
        rid = f'ta_{tahun.replace("/", "_")}_{semester}'
        lines.append(f'    <record id="{rid}" model="erpobe.akademik.tahunajaran">')
        lines.append(f'        <field name="tahun_ajaran">{tahun}</field>')
        lines.append(f'        <field name="semester">{semester}</field>')
        lines.append(f'        <field name="aktif" eval="{aktif}" />')
        lines.append("    </record>")
    for prog in PROGRAMS:
        code = prog["kode"].lower()
        for rombel in ROMBEL_NAMES:
            rid = f"rombel_{code}_2026_{rombel.lower()}"
            lines.append(f'    <record id="{rid}" model="erpobe.master.rombel">')
            lines.append(f'        <field name="name">{rombel}</field>')
            lines.append('        <field name="angkatan">2026</field>')
            lines.append(f'        <field name="prodi_id" ref="erpobe.{prog["id"]}" />')
            lines.append("    </record>")
            lines.append(f'    <record id="rombel_{code}_2022_{rombel.lower()}" model="erpobe.master.rombel">')
            lines.append(f'        <field name="name">{rombel}</field>')
            lines.append('        <field name="angkatan">2022</field>')
            lines.append(f'        <field name="prodi_id" ref="erpobe.{prog["id"]}" />')
            lines.append("    </record>")
    lines.append("</odoo>")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------
# Generate demo_03_cpl_matakuliah_cpmk.xml
# ---------------------------------------------------------------

def gen_demo_03():
    lines = [
        "<?xml version='1.0' encoding='utf-8'?>",
        '<odoo noupdate="1">',
    ]
    for prog in PROGRAMS:
        code = prog["kode"].lower()
        prodi_ref = f"erpobe.{prog['id']}"
        cpl_id = f"cpl_{code}"
        lines.append(f'    <record id="{cpl_id}" model="erpobe.akademik.cpl">')
        lines.append(f'        <field name="prodi_id" ref="{prodi_ref}" />')
        lines.append(f'        <field name="kode_cpl">CPL-{code.upper()}</field>')
        lines.append(f'        <field name="name">Capaian Pembelajaran Lulusan {prog["name"]}.</field>')
        lines.append("    </record>")
    for prog in PROGRAMS:
        code = prog["kode"].lower()
        prodi_ref = f"erpobe.{prog['id']}"
        lines.append(f'    <record id="mk_{code}" model="erpobe.master.matakuliah">')
        lines.append(f'        <field name="prodi_id" ref="{prodi_ref}" />')
        lines.append(f'        <field name="kode_mk">MK-{code.upper()}</field>')
        lines.append(f'        <field name="name">Mata Kuliah Umum {prog["name"]}</field>')
        lines.append('        <field name="sks">3</field>')
        lines.append('        <field name="semester">1</field>')
        lines.append("    </record>")
    for prog in PROGRAMS:
        code = prog["kode"].lower()
        lines.append(f'    <record id="cpmk_{code}" model="erpobe.akademik.cpmk">')
        lines.append(f'        <field name="mk_id" ref="erpobe.mk_{code}" />')
        lines.append(f'        <field name="kode_cpmk">CPMK-{code.upper()}</field>')
        lines.append(f'        <field name="name">Capaian Pembelajaran Mata Kuliah {prog["name"]}</field>')
        lines.append("    </record>")
    lines.append("</odoo>")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------
# Generate demo_04_dosen_mahasiswa.xml
# ---------------------------------------------------------------

def gen_demo_04():
    lines = [
        "<?xml version='1.0' encoding='utf-8'?>",
        '<odoo noupdate="1">',
    ]
    for program_number, prog in enumerate(PROGRAMS, start=1):
        code = prog["kode"].lower()
        # Dosen
        for i in range(5):
            did = f"dosen_{code}_{i + 1}"
            lines.append(f'    <record id="{did}" model="erpobe.master.dosen">')
            lines.append(f'        <field name="prodi_ids" eval="[(6, 0, [ref(\'erpobe.{prog["id"]}\')])]"/>')
            lines.append(f'        <field name="name">Dr. Dosen {code.upper()} {i + 1}</field>')
            lines.append(f'        <field name="email">dosen.{code}.{i + 1}@example.com</field>')
            lines.append(f'        <field name="nip">198{4000 + i}{program_number:02d}01</field>')
            lines.append("    </record>")
    for prog in PROGRAMS:
        code = prog["kode"].lower()
        students = generate_students(code, prog["id"], "2022", count=24)
        for student in students:
            sid = student["id"]
            lines.append(f'    <record id="{sid}" model="erpobe.master.mahasiswa">')
            lines.append(f'        <field name="name">{student["name"]}</field>')
            lines.append(f'        <field name="nim">{student["nim"]}</field>')
            lines.append(f'        <field name="email">{student["email"]}</field>')
            lines.append(f'        <field name="rombel_id" ref="erpobe.{student["rombel_id"]}" />')
            lines.append(f'        <field name="dosen_wali_id" ref="erpobe.dosen_{code}_1" />')
            lines.append("    </record>")
    lines.append("</odoo>")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------
# Generate demo_05_komponen_bobot.xml
# ---------------------------------------------------------------

def gen_demo_05():
    lines = [
        "<?xml version='1.0' encoding='utf-8'?>",
        '<odoo noupdate="1">',
        '    <record id="komponen_kognitif" model="erpobe.akademik.komponen">',
        '        <field name="name">Penilaian Kognitif</field>',
        '        <field name="tipe">kognitif</field>',
        '    </record>',
        '    <record id="komponen_partisipatif" model="erpobe.akademik.komponen">',
        '        <field name="name">Penilaian Partisipatif</field>',
        '        <field name="tipe">partisipatif</field>',
        '    </record>',
    ]
    lines.append("</odoo>")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------
# Generate demo_06_akun_akses.xml
# ---------------------------------------------------------------

def gen_demo_06():
    lines = [
        "<?xml version='1.0' encoding='utf-8'?>",
        '<odoo noupdate="1">',
    ]
    lines.append("</odoo>")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------
# Generate demo_07_penawaran.xml
# ---------------------------------------------------------------

def gen_demo_07():
    lines = [
        "<?xml version='1.0' encoding='utf-8'?>",
        '<odoo noupdate="1">',
        "    <record id=\"penawaran_ind_2026_2027_ganjil\" model=\"erpobe.akademik.penawaran\">",
        "        <field name=\"prodi_id\" ref=\"erpobe.prodi_ti\" />",
        "        <field name=\"tahun_ajaran\" ref=\"erpobe.ta_2026_2027_ganjil\" />",
        "        <field name=\"rombel_ids\" eval=\"[(6, 0, [ref('erpobe.rombel_in_2022_a'), ref('erpobe.rombel_in_2022_b')])]\" />",
        "    </record>",
    ]
    lines.append("</odoo>")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------
# Generate demo_08_rps.xml
# ---------------------------------------------------------------

def gen_demo_08():
    lines = [
        "<?xml version='1.0' encoding='utf-8'?>",
        '<odoo noupdate="1">',
    ]
    for prog in PROGRAMS:
        code = prog["kode"].lower()
        lines.append(f'    <record id="rps_{code}" model="erpobe.akademik.rps">')
        lines.append(f'        <field name="matakuliah_id" ref="erpobe.mk_{code}" />')
        lines.append('        <field name="status">draft</field>')
        lines.append("    </record>")
    lines.append("</odoo>")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------
# Generate demo_09_krs.xml
# ---------------------------------------------------------------

def gen_demo_09():
    lines = [
        "<?xml version='1.0' encoding='utf-8'?>",
        '<odoo noupdate="1">',
        "    <record id=\"krs_ind_1\" model=\"erpobe.akademik.krs\">",
        "        <field name=\"mahasiswa_id\" ref=\"erpobe.mhs_in_2022_001\" />",
        "        <field name=\"penawaran_id\" ref=\"erpobe.penawaran_ind_2026_2027_ganjil\" />",
        "        <field name=\"state\">draft</field>",
        "    </record>",
    ]
    lines.append("</odoo>")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------
# Generate demo_10_nilai.xml
# ---------------------------------------------------------------

def gen_demo_10():
    lines = [
        "<?xml version='1.0' encoding='utf-8'?>",
        '<odoo noupdate="1">',
    ]
    lines.append("</odoo>")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------
# Generate demo_11_capaian.xml
# ---------------------------------------------------------------

def gen_demo_11():
    lines = [
        "<?xml version='1.0' encoding='utf-8'?>",
        '<odoo noupdate="1">',
    ]
    lines.append("</odoo>")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------
# Main
# ---------------------------------------------------------------

def main():
    out_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "custom_module",
        "erpobe",
        "data",
    )
    out_dir = os.path.abspath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "erpobe", "data")
    )
    os.makedirs(out_dir, exist_ok=True)

    generators = [
        ("demo_01_fakultas_prodi.xml", gen_demo_01),
        ("demo_02_tahun_ajaran_rombels.xml", gen_demo_02),
        ("demo_03_cpl_matakuliah_cpmk.xml", gen_demo_03),
        ("demo_04_dosen_mahasiswa.xml", gen_demo_04),
        ("demo_05_komponen_bobot.xml", gen_demo_05),
        ("demo_06_akun_akses.xml", gen_demo_06),
        ("demo_07_penawaran.xml", gen_demo_07),
        ("demo_08_rps.xml", gen_demo_08),
        ("demo_09_krs.xml", gen_demo_09),
        ("demo_10_nilai.xml", gen_demo_10),
        ("demo_11_capaian.xml", gen_demo_11),
    ]
    for fname, gen in generators:
        content = gen()
        with open(os.path.join(out_dir, fname), "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Generated {fname}")


if __name__ == "__main__":
    main()
