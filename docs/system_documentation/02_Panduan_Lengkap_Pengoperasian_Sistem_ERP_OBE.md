# Panduan Lengkap Pengoperasian Sistem ERP OBE

**Identitas Dokumen**

| Item | Nilai |
|---|---|
| Nama Dokumen | Panduan Lengkap Pengoperasian Sistem ERP OBE |
| Versi | 1.0 |
| Tanggal Penyusunan | 2026-11-22 |
| Status | Audit source code — tanpa akses database produksi |

## Riwayat Perubahan

| Versi | Tanggal | Keterangan |
|---|---|---|
| 1.0 | 2026-11-22 | Penyusunan awal berdasarkan audit source code ERP OBE. |

## Daftar Isi

[Daftar isi diperbarui otomatis pada dokumen Word.]

# BAB I — Pendahuluan

ERP OBE adalah aplikasi Odoo custom untuk mengelola struktur akademik, kurikulum, CPL, CPMK, RPS, penilaian komponen, dan analisis capaian. Sistem mengatasi kebutuhan penyimpanan relasi akademik sekaligus pengolahan nilai dari komponen penilaian menjadi nilai CPMK, nilai mata kuliah, dan nilai CPL.

Outcome-Based Education (OBE) diterapkan melalui rantai kurikulum: mata kuliah ↔ CPMK ↔ CPL, dengan bobot pada CPMK terhadap mata kuliah serta alokasi komponen penilaian terhadap CPMK. Ruang lingkup mencakup backend untuk administrator/dosen dan portal untuk dosen/mahasiswa. Sistem tidak mengklaim fitur administrasi, approval, atau integrasi yang tidak ditemukan pada source.

# BAB II — Arsitektur Sistem

Platform utama adalah Odoo 19. Logika ditulis dalam Python dan ORM, penyimpanan menggunakan PostgreSQL, antarmuka menggunakan XML/QWeb, dan modul website menyediakan portal. Modul standar Odoo yang dinyatakan dalam manifest adalah `base`, `web`, `website`, `portal`, `contacts`, dan `mail`. Modul custom utama adalah `erpobe`.

# BAB III — Struktur Modul dan Fitur

| Fitur | Status aktual | Pengguna | Lokasi |
|---|---|---|---|
| Fakultas/Prodi | Diimplementasikan | Administrator; read dosen/mahasiswa | models/akademik_fakultas.py, master_prodi.py |
| Dosen/Mahasiswa/Rombel | Diimplementasikan | Administrator; dosen/mahasiswa terbatas | models/master_user.py |
| Kurikulum | Diimplementasikan | Administrator backend | models/akademik_...; views/menus.xml |
| Mata Kuliah | Diimplementasikan | Administrator backend | models/master_akademik.py |
| CPL/CPMK | Diimplementasikan | Administrator CRUD; dosen read/write sesuai ACL | models/akademik_cpl.py, akademik_cpmk.py |
| RPS dan locking final | Diimplementasikan | Administrator; dosen yang berwenang pada mata kuliah | models/akademik_rps.py, rps_lock.py |
| Komponen penilaian | Diimplementasikan | Administrator; dosen pada RPS | rps_komponen.py, akademik_komponen.py |
| KRS | Diimplementasikan | Mahasiswa mengajukan; dosen wali memutuskan | models/akademik_krs.py; portal_mahasiswa.py |
| Input nilai | Diimplementasikan | Administrator/Dosen | models/grade.py; portal_dosen.py |
| KHS | Diimplementasikan | Administrator/Mahasiswa | models/report_khs.py |
| Analisis CPL/CPMK/MK | Diimplementasikan sebagai SQL/pivot views dan portal | Administrator/Dosen | models/report_summary.py; grade_*.py |

# BAB IV — Alur Data dan Proses Bisnis

Alur akademik aktual: Fakultas → Program Studi → Rombel/Angkatan → Kurikulum/Mata Kuliah → CPL/CPMK → RPS → Penawaran kelas → KRS → nilai komponen → CPMK → mata kuliah → CPL → KHS/analisis.

Persiapan dimulai dengan pengisian master akademik. RPS dibuat dari penawaran mata kuliah dan dapat berada dalam status draft, review, atau final. RPS final bersifat read-only dan hanya dapat dibuat versi baru melalui mekanisme salin. Mahasiswa mengajukan KRS pada penawaran aktif; dosen wali menyetujui atau mengembalikan. Dosen yang merupakan koordinator atau tim pengampu dapat mengelola RPS dan input nilai setelah RPS final dengan bobot lengkap.

# BAB V — Formula dan Mekanisme Perhitungan

Bagian ini memuat formula yang benar-benar ditelusuri dari source code.

## 5.1 Validasi dan Bobot Komponen

**Tujuan:** memastikan bobot dapat difinalisasi.

Sistem menghitung total bobot komponen aktif RPS. Nilai dianggap lengkap jika total berada dalam toleransi 0,01 dari 100:

`complete = |total - 100| ≤ 0.01`
`under = total < 100 - 0.01`
`over = total > 100 + 0.01`

Setiap komponen dibatasi 0–100%. Komponen aktif memiliki bobot mata kuliah. Alokasi komponen terhadap setiap CPMK dibatasi 0–100%. Untuk snapshot komponen aktif, nilai CPMK dihitung hanya terhadap komponen aktif yang tersedia dan `is_graded=True`. Tidak ada normalisasi skala lain dalam code CPMK; nilai komponen diharuskan 0–100.

Lokasi: `models/weight_validation.py`, `models/rps_komponen.py`, `models/bobot_komponen_cpmk.py`, `models/bobot_cpmk_mk.py`.

## 5.2 Nilai CPMK Mahasiswa

**Formula jalur exact RPS/KRS:**

`Aᵢ = bobot komponen i pada RPS × alokasi komponen i terhadap CPMK / 100`
`Nilai CPMK = Σ(nilai komponen i × Aᵢ) / Σ(Aᵢ)`

Komponen hanya dihitung jika snapshot aktif, nilai komponen `is_graded=True`, dan record mempunyai relasi RPS serta KRS exact. Jika penyebut 0, `is_available=False` dan nilai CPMK 0.0. Jalur kompatibilitas legacy memakai bobot komponen terhadap CPMK, dan mencocokkan nilai berdasarkan mahasiswa/mata kuliah/komponen.

Lokasi: `models/grade_cpmk.py::_compute_nilai_cpmk()`.

## 5.3 Ketercapaian CPMK

CPMK mempunyai `target_nilai`, default 70. Status:

`belum_tersedia` jika `is_available=False`; `tercapai` jika nilai CPMK ≥ target; `belum` jika nilai tersedia tetapi di bawah target.

Ini membedakan nilai CPMK aktual dari status target. Persentase jumlah mahasiswa yang mencapai target belum menjadi field CPMK; agregasi SQL dilihat sebagai tabel rata-rata saat tersedia.

## 5.4 Nilai Mata Kuliah

**Formula exact:**

`Nilai MK = Σ(Nilai CPMK j × bobot CPMK j terhadap MK / 100) / Σ(bobot CPMK j terhadap MK / 100)`

Hanya bobot positif dan grade CPMK tersedia yang dihitung. Jika penyebut 0, MK `is_available=False`, nilai 0.0. Lokasi: `models/grade_mk.py::_compute_nilai_mk()`.

## 5.5 Nilai CPL Mahasiswa

**Formula:**

`Nilai CPL = Σ(Nilai CPMK j × bobot CPMK j terhadap MK) / Σ(bobot CPMK j terhadap MK)`

Bobot berasal dari tabel `erpobe.bobot.cpmk.mk` pada RPS grade CPMK. CPL hanya mengambil CPMK yang dipetakan dan mata kuliahnya juga dipetakan ke CPL. Grade CPMK harus tersedia; RPS berstatus final; KRS berstatus approved; dan penawaran baris juga memiliki RPS final. Bobot tidak positif diabaikan. Hasil dibatasi 0–100. Status CPL dapat `belum_tersedia`, `dalam_proses`, `tercapai`, atau `belum`. Lokasi: `models/grade_cpl.py::_compute_nilai_cpl()` dan `_compute_status_capaian()`.

## 5.6 KHS dan IPK

Laporan KHS menghambil bobot nilai huruf dari master grade. Untuk mata kuliah unik, jika ada nilai ulang MK yang sama, hanya bobot tertinggi yang dipakai. `IPK = Σ(SKS mata kuliah unik × bobot nilai tertinggi) / Σ(SKS mata kuliah unik dengan bobot nilai > 0)` pada implementasi statistik yang terverifikasi. Nama dan detail implementasi dapat dilihat pada `models/report_khs.py`.

Hasil ini adalah indikator akademik umum, bukan rumus OBE.

**Catatan formula belum ditemukan:** tidak ditemukan rumus persentase mahasiswa yang mencapai CPMK sebagai field tersimpan; tidak ditemukan rumus capaian program studi agregat tertulis sebagai field selain SQL view aggregasi rata-rata.

## 5.7 Studi Kasus Simulasi

**Ilustrasi bukan data database:** Suatu MK mempunyai dua CPMK. Nilai komponen: tugas 80 untuk CPMK-01 dan UTS 75 untuk CPMK-01, dengan alokasi komponen pada RPS masing-masing 40%/60% bobot alokasi. Kontribusi efektif: CPMK-01 = (80×40% + 75×60%)=77.0. Jika CPMK-01 bobot MK 60% dan CPMK-02 bernilai 83 dengan bobot MK 40%, nilai MK = 77×0.60 + 83×0.40 = 79.4. Jika kedua CPMK dipetakan ke CPL-01 masing-masing dengan bobot RPS 60%/40%, nilai CPL = 77×0.60 + 83×0.40 = 79.4. Dengan target CPMK 70 dan target CPL 70, seluruh indikator tercapai dalam simulasi ini.

# BAB VI — Panduan Pengguna

Panduan berikut dibatasi fitur yang ditemukan pada source.

## 6.1 Administrator

Login backend melalui akun dengan grup Admin atau Superadmin administratif. Kelola master Fakultas, Program Studi, Dosen, Mahasiswa, Rombel, Mata Kuliah, Kurikulum, CPL, CPMK, Komponen, RPS, Penawaran Mata Kuliah, Tahun Ajaran, input nilai, dan laporan. Pastikan relasi prodi/fakultas konsisten, karena banyak constraint record rules dan `constraints` membatasi cross-prodi.

RPS hanya boleh difinalisasi setelah seluruh bobot mencapai 100% sesuai toleransi. RPS final read-only; gunakan salin untuk versi baru.

## 6.2 Dosen

Masuk portal `/my/triton` atau `/my/rps`, `/my/kelas`, `/my/perwalian`, dan `/my/analisis`. RPS dapat dibuat/diubah/salin/difinalisasi hanya untuk mata kuliah yang menjadi koordinator atau tim pengampu dosen. Input nilai memerlukan RPS final dan bobot lengkap. Dosen wali dapat meninjau dan memutuskan KRS mahasiswa bimbingan.

## 6.3 Mahasiswa

Masuk portal `/my/krs`, `/my/khs`, `/my/mata-kuliah`, `/my/rps/<id>`, `/my/capaian-cpl`, dan `/my/profil`. Mahasiswa dapat mengisi/diajukan KRS untuk penawaran aktif pada rombel/prodinya; melihat mata kuliah, komponen nilai, RPS final yang relevan, KHS, dan CPL. Mahasiswa tidak mempunyai hak backend untuk mengubah master atau penilaian.

# BAB VII — Diagram Sistem

Sumber diagram tersedia pada folder `diagrams/` dan memakai Mermaid.

# BAB VIII — Troubleshooting

| Masalah | Pemeriksaan | Solusi | Penangan |
|---|---|---|---|
| Tidak dapat login | Login/email/NIM/NIP dan status akun aktif | Periksa relasi profil serta reset password melalui administrasi Odoo | Administrator |
| Tidak memiliki akses menu | Grup dan record rule cakupan prodi | Tambahkan/grup role yang tepat; pastikan `erpobe_prodi_ids` | Administrator |
| Fakultas/prodi tidak muncul | Relasi `fakultas_id`, `prodi_id`, `erpobe_prodi_ids` | Perbaiki master secara administratif, jangan lewat SQL | Administrator |
| RPS tidak dapat disimpan/difinalisasi | Bobot komponen, alokasi CPMK, status draft/review | Lengkapi bobot hingga 100 ±0,01% | Dosen/Administrator |
| Nilai tidak dapat dihitung | RPS final, bobot lengkap, KRS approved, nilai `is_graded=True` | Lengkapi prerequisite dan jalankan kalkulasi | Dosen/Administrator |
| Capaian CPL tidak muncul | CPL/CPMK/MK mapping; RPS final; KRS approved | Perbaiki pemetaan dan status yang diperlukan | Administrator |
| Data portal tidak muncul | Relasi user-profil dan scope rombel/prodi | Periksa `_require_student()`/`_require_teacher()` serta rule | Administrator |

# BAB IX — Glosarium dan Referensi

**OBE** Outcome-Based Education. **CPL** Capaian Pembelajaran Lulusan. **CPMK** Capaian Pembelajaran Mata Kuliah. **RPS** Rencana Pembelajaran Semester. **Weighted average** rata-rata berbobot dengan penyebut bobot yang dipakai. **ORM** Object-Relational Mapping Odoo. **ACL** hak CRUD `ir.model.access`. **Record rule** pembatasan record berdasarkan domain. **Portal** antarmuka website untuk pengguna login.

Referensi implementasi: source module `erpobe`, terutama manifest, security, models, controllers, views, tests, dan fixtures. Referensi platform: dokumentasi resmi Odoo 19 untuk ORM, ACL, record rules, portal, website, dan QWeb. Referensi teori OBE digunakan hanya sebagai penjelasan konseptual dan tidak menggantikan formula source.
