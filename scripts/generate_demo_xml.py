from __future__ import annotations

from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / 'data'
DATA_DIR.mkdir(exist_ok=True)

PRODIS = {
    'ti': {
        'name': 'Teknik Informatika',
        'code': 'IF',
        'cpls': [
            ('CPL-01', 'Menunjukkan sikap religius, etis, dan bertanggung jawab dalam tugas akademik.', 'sikap'),
            ('CPL-02', 'Menguasai konsep algoritma, struktur data, dan analisis sistem informasi.', 'pengetahuan'),
            ('CPL-03', 'Merancang solusi perangkat lunak yang aman, terukur, dan ramah pengguna.', 'keterampilan_khusus'),
            ('CPL-04', 'Menganalisis kebutuhan sistem lalu merumuskan spesifikasi fungsional.', 'keterampilan_umum'),
            ('CPL-05', 'Mendesain dan menguji antarmuka serta fitur perangkat lunak.', 'keterampilan_khusus'),
            ('CPL-06', 'Mengoperasikan basis data dan query SQL untuk kebutuhan bisnis.', 'pengetahuan'),
            ('CPL-07', 'Memecahkan persoalan teknologi informasi dengan pendekatan ilmiah.', 'keterampilan_umum'),
            ('CPL-08', 'Bekerja dalam tim dan menyampaikan hasil secara efektif.', 'sikap'),
        ],
        'courses': [
            ('IF101', 'Algoritma dan Struktur Data', 3, 1, 'T'),
            ('IF102', 'Basis Data', 3, 2, 'T'),
            ('IF203', 'Rekayasa Perangkat Lunak', 4, 3, 'T'),
            ('IF204', 'Jaringan Komputer', 3, 4, 'T'),
            ('IF205', 'Kecerdasan Buatan', 3, 5, 'T'),
        ],
    },
    'si': {
        'name': 'Teknik Sipil',
        'code': 'SI',
        'cpls': [
            ('CPL-01', 'Menggunakan prinsip keselamatan, etika, dan tanggung jawab dalam rancang bangun sipil.', 'sikap'),
            ('CPL-02', 'Menganalisis mekanika tanah dan beban struktur secara tepat.', 'pengetahuan'),
            ('CPL-03', 'Merancang komponen struktur dan pondasi sesuai standar teknis.', 'keterampilan_khusus'),
            ('CPL-04', 'Mengevaluasi material konstruksi serta eksposur lingkungan.', 'pengetahuan'),
            ('CPL-05', 'Mengelola proyek konstruksi secara operasional dan aman.', 'keterampilan_umum'),
            ('CPL-06', 'Membaca dan menafsirkan data survei dan pemetaan lahan.', 'pengetahuan'),
            ('CPL-07', 'Mengembangkan solusi rekayasa infrastruktur berkelanjutan.', 'keterampilan_khusus'),
            ('CPL-08', 'Menyusun laporan teknis dan presentasi hasil kajian.', 'sikap'),
        ],
        'courses': [
            ('SI101', 'Mekanika Tanah', 3, 2, 'T'),
            ('SI102', 'Struktur Beton', 4, 3, 'T'),
            ('SI103', 'Hidrologi', 3, 2, 'T'),
            ('SI204', 'Surveying dan Pemetaan', 3, 4, 'T'),
            ('SI205', 'Transportasi dan Perkerasan', 3, 5, 'T'),
        ],
    },
    'me': {
        'name': 'Teknik Mesin',
        'code': 'ME',
        'cpls': [
            ('CPL-01', 'Menunjukkan sikap profesional dan bertanggung jawab dalam praktik mekanik.', 'sikap'),
            ('CPL-02', 'Menguasai prinsip termodinamika dan mekanika fluida.', 'pengetahuan'),
            ('CPL-03', 'Merancang komponen mesin sesuai kebutuhan performa dan keamanan.', 'keterampilan_khusus'),
            ('CPL-04', 'Menganalisis proses manufaktur dan sistem energi.', 'pengetahuan'),
            ('CPL-05', 'Menyusun simulasi dan eksperimen mesin secara valid.', 'keterampilan_umum'),
            ('CPL-06', 'Memilih material dan proses manufaktur yang efisien.', 'pengetahuan'),
            ('CPL-07', 'Mengembangkan inovasi mesin dan otomasi.', 'keterampilan_khusus'),
            ('CPL-08', 'Mengkomunikasikan hasil desain teknis secara efektif.', 'sikap'),
        ],
        'courses': [
            ('ME101', 'Termodinamika', 3, 2, 'T'),
            ('ME102', 'Mekanika Fluida', 3, 2, 'T'),
            ('ME203', 'Desain Mesin', 4, 3, 'T'),
            ('ME204', 'Proses Manufaktur', 3, 4, 'T'),
            ('ME205', 'CAD/CAM', 3, 5, 'T'),
        ],
    },
    'el': {
        'name': 'Teknik Elektro',
        'code': 'EL',
        'cpls': [
            ('CPL-01', 'Menjaga etika kerja dan keselamatan dalam praktik kelistrikan.', 'sikap'),
            ('CPL-02', 'Menguasai prinsip rangkaian, sinyal, dan sistem tenaga listrik.', 'pengetahuan'),
            ('CPL-03', 'Merancang sistem kontrol dan elektronik kendali.', 'keterampilan_khusus'),
            ('CPL-04', 'Menganalisis perilaku sistem tenaga dan instalasi listrik.', 'pengetahuan'),
            ('CPL-05', 'Menggunakan alat ukur dan pemodelan sistem listrik.', 'keterampilan_umum'),
            ('CPL-06', 'Menerapkan teknik komunikasi dan elektronika digital.', 'pengetahuan'),
            ('CPL-07', 'Merancang solusi energi terbarukan dan penggunaan listrik efektif.', 'keterampilan_khusus'),
            ('CPL-08', 'Menyampaikan hasil analisis dan desain teknis dengan jelas.', 'sikap'),
        ],
        'courses': [
            ('EL101', 'Rangkaian Listrik', 3, 2, 'T'),
            ('EL102', 'Elektronika Dasar', 3, 2, 'T'),
            ('EL203', 'Sistem Kontrol', 4, 3, 'T'),
            ('EL204', 'Sistem Tenaga', 3, 4, 'T'),
            ('EL205', 'Teknik Digital', 3, 5, 'T'),
        ],
    },
    'ind': {
        'name': 'Teknik Industri',
        'code': 'IN',
        'cpls': [
            ('CPL-01', 'Menunjukkan sikap profesional dan integritas dalam penyelesaian masalah industri.', 'sikap'),
            ('CPL-02', 'Menguasai prinsip optimasi, tata letak, dan manajemen operasi.', 'pengetahuan'),
            ('CPL-03', 'Merancang sistem produksi yang efisien dan berkelanjutan.', 'keterampilan_khusus'),
            ('CPL-04', 'Menganalisis kebutuhan pelanggan dan performa proses industri.', 'pengetahuan'),
            ('CPL-05', 'Menggunakan alat keputusan dan simulasi dalam pengambilan keputusan.', 'keterampilan_umum'),
            ('CPL-06', 'Menilai kualitas, keselamatan, dan ergonomi kerja.', 'pengetahuan'),
            ('CPL-07', 'Mengembangkan inovasi rantai pasok dan manufaktur digital.', 'keterampilan_khusus'),
            ('CPL-08', 'Menyampaikan rekomendasi operasional secara efektif.', 'sikap'),
        ],
        'courses': [
            ('IN101', 'Analisis Operasi', 3, 2, 'T'),
            ('IN102', 'Perencanaan Produksi', 3, 2, 'T'),
            ('IN203', 'Sistem Manufaktur', 4, 3, 'T'),
            ('IN204', 'Ergonomi Industri', 3, 4, 'T'),
            ('IN205', 'Logistik dan Supply Chain', 3, 5, 'T'),
        ],
    },
}

COMPONENTS = [
    ('komp_tugas', 'Tugas', 'kognitif'),
    ('komp_kuis', 'Kuis', 'partisipatif'),
    ('komp_uts', 'UTS', 'kognitif'),
    ('komp_uas', 'UAS', 'kognitif'),
    ('komp_proyek', 'Proyek', 'partisipatif'),
    ('komp_praktikum', 'Praktikum', 'partisipatif'),
]

MASTER_GRADES = [
    ('grade_a', 'A', 85.0, 100.0, 4.0, 'Sangat Baik'),
    ('grade_ab', 'A-', 80.0, 84.99, 3.7, 'Baik Sekali'),
    ('grade_b', 'B', 70.0, 79.99, 3.0, 'Baik'),
    ('grade_bc', 'B-', 65.0, 69.99, 2.7, 'Cukup Baik'),
    ('grade_c', 'C', 55.0, 64.99, 2.0, 'Cukup'),
    ('grade_d', 'D', 40.0, 54.99, 1.0, 'Kurang'),
    ('grade_e', 'E', 0.0, 39.99, 0.0, 'Gagal'),
]

STUDENT_NAMES = {
    'ti': ['Anisa Putri', 'Raka Pradana', 'Lukman Hidayat', 'Nadia Aulia', 'Farhan Wijaya', 'Salsa Putri'],
    'si': ['Gilang Permana', 'Maya Sari', 'Rafi Kusuma', 'Della Putri', 'Hafiz Rahman', 'Wulan Safitri'],
    'me': ['Dewi Lestari', 'Adit Pratama', 'Santi Wulandari', 'Bram Setiawan', 'Nabil Ahmad', 'Yuliana Sari'],
    'el': ['Irfan Maulana', 'Citra Lestari', 'Aditya Firmansyah', 'Rizky Hidayat', 'Sabrina Noor', 'Vega Pratama'],
    'ind': ['Maya Sari', 'Farel Nanda', 'Hana Rahma', 'Dimas Akbar', 'Aisyah Putri', 'Yusuf Hadi'],
}


def xml_field(name, value=None, ref=None, eval_value=None):
    attrs = {'name': name}
    if ref is not None:
        attrs['ref'] = ref
    if eval_value is not None:
        attrs['eval'] = eval_value
    field = ET.Element('field', attrs)
    if value is not None and ref is None and eval_value is None:
        field.text = str(value)
    return field


def build_records(list_of_entries):
    root = ET.Element('odoo', {'noupdate': '1'})
    for model, xml_id, fields in list_of_entries:
        rec = ET.SubElement(root, 'record', {'id': xml_id, 'model': model})
        for field_name, value in fields.items():
            if value is None:
                continue
            if isinstance(value, dict) and 'ref' in value:
                rec.append(xml_field(field_name, ref=value['ref']))
            elif isinstance(value, dict) and 'eval' in value:
                rec.append(xml_field(field_name, eval_value=value['eval']))
            elif isinstance(value, str) and field_name in {'name', 'kode', 'kode_mk', 'kode_cpl', 'kode_cpmk', 'tahun_ajaran', 'semester', 'login', 'email', 'password', 'jabatan_fungsional', 'status_akademik', 'keterangan_standar'}:
                rec.append(xml_field(field_name, value))
            elif isinstance(value, bool):
                rec.append(xml_field(field_name, str(value).capitalize(), eval_value=f"{value}"))
            elif isinstance(value, (int, float)):
                rec.append(xml_field(field_name, str(value)))
            else:
                rec.append(xml_field(field_name, str(value)))
    return root


def write_file(filename, root):
    path = DATA_DIR / filename
    tree = ET.ElementTree(root)
    ET.indent(tree, space='    ')
    tree.write(path, encoding='utf-8', xml_declaration=True)


def generate_demo_files():
    # 01: faculty + prodi
    faculty_records = []
    faculty_records.append(('erpobe.master.fakultas', 'fakultas_teknik', {'name': 'Fakultas Teknik', 'kode': 'FT'}))
    for key, cfg in PRODIS.items():
        faculty_records.append((
            'erpobe.master.prodi',
            f'prodi_{key}',
            {'name': cfg['name'], 'kode': cfg['code'], 'fakultas_id': {'ref': 'erpobe.fakultas_teknik'}}
        ))
    write_file('demo_01_fakultas_prodi.xml', build_records(faculty_records))

    # 02: years + rombels
    year_records = []
    years = [
        ('ta_2022_2023_ganjil', '2022/2023', 'ganjil', False),
        ('ta_2022_2023_genap', '2022/2023', 'genap', False),
        ('ta_2023_2024_ganjil', '2023/2024', 'ganjil', False),
        ('ta_2023_2024_genap', '2023/2024', 'genap', False),
        ('ta_2024_2025_ganjil', '2024/2025', 'ganjil', False),
        ('ta_2024_2025_genap', '2024/2025', 'genap', False),
        ('ta_2025_2026_ganjil', '2025/2026', 'ganjil', False),
        ('ta_2025_2026_genap', '2025/2026', 'genap', False),
        ('ta_2026_2027_ganjil', '2026/2027', 'ganjil', True),
        ('ta_2026_2027_genap', '2026/2027', 'genap', False),
    ]
    for xml_id, tahun, semester, aktif in years:
        year_records.append(('erpobe.akademik.tahunajaran', xml_id, {'tahun_ajaran': tahun, 'semester': semester, 'aktif': aktif}))
    for key in PRODIS:
        year_records.append(('erpobe.master.rombel', f'rombel_{key}_2026_a', {'name': 'A', 'angkatan': 2026, 'prodi_id': {'ref': f'erpobe.prodi_{key}'}}))
        year_records.append(('erpobe.master.rombel', f'rombel_{key}_2025_a', {'name': 'A', 'angkatan': 2025, 'prodi_id': {'ref': f'erpobe.prodi_{key}'}}))
    write_file('demo_02_tahun_ajaran_rombels.xml', build_records(year_records))

    # 03: cpls, courses, cpmks, mappings
    core_records = []
    for key, cfg in PRODIS.items():
        for idx, (kode_cpl, desc, jenis) in enumerate(cfg['cpls'], 1):
            core_records.append((
                'erpobe.akademik.cpl',
                f'cpl_{key}_{idx:02d}',
                {'kode_cpl': kode_cpl, 'name': desc, 'jenis_cpl': jenis, 'prodi_id': {'ref': f'erpobe.prodi_{key}'}}
            ))
        for idx, (kode_mk, name_mk, sks, semester, tipe) in enumerate(cfg['courses'], 1):
            mk_id = f'mk_{key}_{idx:02d}'
            core_records.append((
                'erpobe.master.matakuliah',
                mk_id,
                {
                    'name': name_mk,
                    'kode_mk': kode_mk,
                    'sks': sks,
                    'semester': semester,
                    'tipe_mk': tipe,
                    'jenis_mk': 'I',
                    'bahasa': 'I',
                    'deskripsi_mk': f'{name_mk} adalah mata kuliah inti dalam bidang {cfg["name"]}.',
                    'prodi_id': {'ref': f'erpobe.prodi_{key}'}
                }
            ))
            for sub_idx in range(1, 4):
                cpmk_id = f'cpmk_{key}_{kode_mk.lower()}_{sub_idx}'
                desc = f'Mahasiswa mampu menghitung, menganalisis, dan menyampaikan solusi relevan untuk {name_mk.lower()} secara terukur.'
                core_records.append((
                    'erpobe.akademik.cpmk',
                    cpmk_id,
                    {'mk_id': {'ref': f'erpobe.{mk_id}'}, 'kode_cpmk': f'CPMK-{kode_mk}-{sub_idx}', 'name': desc}
                ))
                cpl_targets = [f'erpobe.cpl_{key}_{(sub_idx * 2 + idx) % len(cfg["cpls"]) + 1:02d}' if False else '']
                # map each CPMK to two CPLs with a stable offset
                mapped = [
                    f'cpl_{key}_{((idx + sub_idx - 1) % len(cfg["cpls"])) + 1:02d}',
                    f'cpl_{key}_{((idx + sub_idx + 1) % len(cfg["cpls"])) + 1:02d}',
                ]
                for cpl in mapped:
                    core_records.append((
                        'erpobe.akademik.cpl.mk.cpmk',
                        f'map_{cpmk_id}_{cpl}',
                        {'cpl_id': {'ref': f'erpobe.{cpl}'}, 'cpmk_id': {'ref': f'erpobe.{cpmk_id}'}}
                    ))
    write_file('demo_03_cpl_matakuliah_cpmk.xml', build_records(core_records))

    # 04: dosen + mahasiswa (diverse, enough to support KRS and portal)
    user_records = []
    nip_counter = 1987001001
    for key, cfg in PRODIS.items():
        dosen_names = [
            ('Dr. Rina Kumalasari', None, 'Lektor Kepala'),
            ('Budi Santoso, S.T.', None, 'Asisten Ahli'),
            ('Ir. Damar Priyanto', None, 'Guru Besar'),
        ]
        if key == 'el':
            dosen_names = [('Nadya Rahmawati, M.Eng.', None, 'Lektor'), ('Rahmat Setiawan, S.T.', None, 'Asisten Ahli')]
        elif key == 'ind':
            dosen_names = [('Fadli Nugraha, S.T.', None, 'Asisten Ahli'), ('Mira Lestari, M.T.', None, 'Lektor')]
        elif key == 'me':
            dosen_names = [('Ari Setiawan, M.T.', None, 'Lektor'), ('Lina Mardiana, S.T.', None, 'Asisten Ahli')]
        for idx, (name, _, jabatan) in enumerate(dosen_names, 1):
            nip = str(nip_counter)
            nip_counter += 1
            pid = f'partner_{key}_dosen_{idx}'
            user_records.append(('res.partner', pid, {'name': name, 'email': f'{key}.dosen{idx}@example.test'}))
            user_records.append((
                'erpobe.master.dosen',
                f'dosen_{key}_{idx}',
                {
                    'partner_id': {'ref': f'erpobe.{pid}'},
                    'name': name,
                    'nip': nip,
                    'jabatan_fungsional': jabatan,
                    'prodi_ids': {'eval': f"[(6, 0, [ref('erpobe.prodi_{key}')])]"},
                    'is_public_visible': True,
                    'public_opt_out': False,
                }
            ))

        for idx, student_name in enumerate(STUDENT_NAMES[key], 1):
            pid = f'partner_{key}_mhs_{idx}'
            user_records.append(('res.partner', pid, {'name': student_name, 'email': f'{key}.mhs.{idx}@example.test'}))
            status = 'aktif' if idx % 3 else 'cuti'
            if idx == 1 and key in {'ti', 'si'}:
                status = 'lulus'
            user_records.append((
                'erpobe.master.mahasiswa',
                f'mhs_{key}_{idx}',
                {
                    'partner_id': {'ref': f'erpobe.{pid}'},
                    'name': student_name,
                    'nim': f'2026{PRODIS[key]["code"]}{idx:03d}',
                    'status_akademik': status,
                    'rombel_id': {'ref': f'erpobe.rombel_{key}_2026_a'},
                    'dosen_wali_id': {'ref': f'erpobe.dosen_{key}_1'},
                    'is_public_visible': idx % 2 == 0,
                    'public_opt_out': idx % 5 == 0,
                }
            ))
    write_file('demo_04_dosen_mahasiswa.xml', build_records(user_records))

    # 05: global components + bobot completeness for active RPS
    comp_records = []
    for xml_id, name, tipe in COMPONENTS:
        comp_records.append(('erpobe.akademik.komponen', xml_id, {'name': name, 'tipe': tipe, 'aktif': True, 'color': 0}))
    write_file('demo_05_komponen_bobot.xml', build_records(comp_records))

    # 06: admin account and access
    access_records = [
        ('res.users', 'demo_admin_erpobe', {
            'name': 'Admin Akademik Demo',
            'login': 'admin.akademik@example.test',
            'email': 'admin.akademik@example.test',
            'password': 'admin123',
            'group_ids': {'eval': "[(6, 0, [ref('base.group_user'), ref('erpobe.group_admin')])]"},
        })
    ]
    write_file('demo_06_akun_akses.xml', build_records(access_records))

    # 07: offerings for active year and some previous years
    offer_records = []
    active_year = 'ta_2026_2027_ganjil'
    active_year_ref = f'erpobe.{active_year}'
    for key, cfg in PRODIS.items():
        offer_id = f'penawaran_{key}_{active_year}'
        offer_records.append((
            'erpobe.akademik.penawaran',
            offer_id,
            {
                'tahun_ajaran': {'ref': active_year_ref},
                'prodi_id': {'ref': f'erpobe.prodi_{key}'},
                'rombel_ids': {'eval': f"[(6, 0, [ref('erpobe.rombel_{key}_2026_a')])]"},
            }
        ))
        for idx, (kode_mk, name_mk, sks, semester, tipe) in enumerate(cfg['courses'], 1):
            line_id = f'penawaran_line_{key}_{idx}'
            offer_records.append((
                'erpobe.akademik.penawaran.line',
                line_id,
                {
                    'penawaran_id': {'ref': f'erpobe.{offer_id}'},
                    'matakuliah_id': {'ref': f'erpobe.mk_{key}_{idx:02d}'},
                    'rombel_ids': {'eval': f"[(6, 0, [ref('erpobe.rombel_{key}_2026_a')])]"},
                    'jadwal_hari': ['senin', 'selasa', 'rabu', 'kamis', 'jumat'][idx % 5],
                    'jam_mulai': float(8 + idx * 0.5),
                    'jam_selesai': float(9.5 + idx * 0.5),
                }
            ))
    write_file('demo_07_penawaran.xml', build_records(offer_records))

    # 08: RPS and weights for all offered lines; keep weights complete for demo stability
    rps_records = []
    for key, cfg in PRODIS.items():
        offer_id = f'penawaran_{key}_{active_year}'
        for idx, (kode_mk, name_mk, sks, semester, tipe) in enumerate(cfg['courses'], 1):
            line_id = f'penawaran_line_{key}_{idx}'
            rps_id = f'rps_{key}_{idx}'
            rps_records.append((
                'erpobe.akademik.rps',
                rps_id,
                {
                    'matakuliah_id': {'ref': f'erpobe.mk_{key}_{idx:02d}'},
                    'penawaran_line_id': {'ref': f'erpobe.{line_id}'},
                    'version': 1,
                    'status': 'final',
                }
            ))
            # cpmk-mk distribution exact 100% per course
            cpmk_ids = [
                f'cpmk_{key}_{kode_mk.lower()}_{sub_idx}' for sub_idx in range(1, 4)
            ]
            weights_mk = [35, 35, 30]
            for cpmk_id, pct in zip(cpmk_ids, weights_mk):
                rps_records.append((
                    'erpobe.bobot.cpmk.mk',
                    f'bobot_mk_{rps_id}_{cpmk_id}',
                    {
                        'rps_id': {'ref': f'erpobe.{rps_id}'},
                        'cpmk_id': {'ref': f'erpobe.{cpmk_id}'},
                        'bobot_cpmk_mk': pct,
                    }
                ))
            # cpmk-cpl distribution exact 100% per cpmk
            cpl_dist = [
                f'cpl_{key}_{((idx + 1) % len(cfg["cpls"])) + 1:02d}',
                f'cpl_{key}_{((idx + 2) % len(cfg["cpls"])) + 1:02d}',
            ]
            for sub_idx, cpmk_id in enumerate(cpmk_ids, 1):
                for cpl_id, pct in zip(cpl_dist, [60, 40]):
                    rps_records.append((
                        'erpobe.bobot.cpmk.cpl',
                        f'bobot_cpl_{rps_id}_{cpmk_id}_{cpl_id}',
                        {
                            'rps_id': {'ref': f'erpobe.{rps_id}'},
                            'cpmk_id': {'ref': f'erpobe.{cpmk_id}'},
                            'cpl_id': {'ref': f'erpobe.{cpl_id}'},
                            'bobot_cpmk_cpl': pct,
                        }
                    ))
            # komponen weights exact 100% per cpmk
            for sub_idx, cpmk_id in enumerate(cpmk_ids, 1):
                comp_values = [25, 15, 20, 25, 10, 5]
                for comp_index, comp_id in enumerate([cid for cid, *_ in COMPONENTS], start=0):
                    if comp_index >= len(comp_values):
                        continue
                    rps_records.append((
                        'erpobe.bobot.komponen.cpmk',
                        f'bobot_comp_{rps_id}_{cpmk_id}_{comp_id}',
                        {
                            'rps_id': {'ref': f'erpobe.{rps_id}'},
                            'cpmk_id': {'ref': f'erpobe.{cpmk_id}'},
                            'komponen_penilaian': {'ref': f'erpobe.{comp_id}'},
                            'bobot_komponen_cpmk': comp_values[comp_index],
                        }
                    ))
    write_file('demo_08_rps.xml', build_records(rps_records))

    # 09: KRS for current students across active offering
    krs_records = []
    for key, cfg in PRODIS.items():
        offer_id = f'penawaran_{key}_{active_year}'
        for idx, student_id in enumerate([f'mhs_{key}_{i}' for i in range(1, 4)], start=1):
            krs_id = f'krs_{key}_{idx}'
            krs_records.append((
                'erpobe.akademik.krs',
                krs_id,
                {
                    'mahasiswa_id': {'ref': f'erpobe.{student_id}'},
                    'penawaran_id': {'ref': f'erpobe.{offer_id}'},
                    'state': 'approved' if idx % 2 else 'submitted',
                }
            ))
            for line_no in range(1, 3):
                line_id = f'krs_line_{krs_id}_{line_no}'
                matakuliah_id = f'mk_{key}_{line_no:02d}'
                krs_records.append((
                    'erpobe.akademik.krs.line',
                    line_id,
                    {
                        'krs_id': {'ref': f'erpobe.{krs_id}'},
                        'penawaran_line_id': {'ref': f'erpobe.penawaran_line_{key}_{line_no}'},
                        'status_pengambilan': 'baru',
                    }
                ))
    write_file('demo_09_krs.xml', build_records(krs_records))

    # 10: master grade + sample input and component grades
    grade_records = []
    for xml_id, grade, minv, maxv, bobot, desc in MASTER_GRADES:
        grade_records.append((
            'erpobe.master.grade',
            xml_id,
            {'name': grade, 'nilai_min': minv, 'nilai_max': maxv, 'bobot': bobot, 'keterangan_standar': desc}
        ))
    write_file('demo_10_nilai.xml', build_records(grade_records))

    # 11: a few report/capaian records, which are generated from the KRS values and not required as source data
    cap_records = []
    cap_records.append((
        'erpobe.summary.analytics.mixin',
        'demo_summary_analytics',
        {'name': 'Data demo analytics', 'active': True}
    ))
    write_file('demo_11_capaian.xml', build_records(cap_records))


def main():
    generate_demo_files()
    print(f'Generated demo files under {DATA_DIR}')


if __name__ == '__main__':
    main()
