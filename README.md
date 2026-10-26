# ERP OBE Management

Modul **ERP OBE Management** menyediakan sarana pengelolaan data akademik dan
evaluasi capaian pembelajaran berbasis Outcome-Based Education (OBE) di Odoo.
Modul ini menghubungkan data fakultas dan program studi dengan kurikulum,
perkuliahan, penilaian, hasil studi, dan analitik akademik.

## Fitur

### Data akademik

- Pengelolaan fakultas dan program studi.
- Data dosen, mahasiswa, rombongan belajar (rombel), mata kuliah, dan angkatan.
- Relasi data akademik mengikuti program studi terkait.

### Kurikulum dan RPS

- Pengelolaan Capaian Pembelajaran Lulusan (CPL) dan Capaian Pembelajaran Mata
  Kuliah (CPMK), termasuk pemetaan CPL–CPMK.
- Penyusunan Rencana Pembelajaran Semester (RPS).
- Pengelolaan kegiatan pembelajaran mingguan, metode, dan referensi.
- Pengaturan komponen penilaian, rubrik, kriteria, serta bobot penilaian.

### Perkuliahan dan penilaian

- Pengelolaan tahun ajaran dan penawaran mata kuliah.
- Pengisian Kartu Rencana Studi (KRS) mahasiswa.
- Pencatatan nilai komponen dan perhitungan capaian pembelajaran.
- Penyajian Kartu Hasil Studi (KHS).

### Hasil dan analitik

- Rekap nilai mata kuliah, CPMK, dan CPL.
- Ringkasan nilai per rombel dan angkatan.
- Tampilan analisis dalam bentuk daftar, pivot, dan grafik.

## Struktur menu

Navigasi utama tersedia pada menu **ERP OBE**:

| Menu | Isi |
| --- | --- |
| Data Akademik | Fakultas, program studi, dosen, mahasiswa, rombel, mata kuliah, dan angkatan |
| Kurikulum dan RPS | CPL, CPMK, RPS, komponen penilaian, metode pembelajaran, referensi, dan skala nilai |
| Perkuliahan | Tahun ajaran, penawaran mata kuliah, KRS, dan input nilai |
| Hasil dan Analitik | KHS, analisis capaian, serta rekap per rombel dan angkatan |

Kegiatan mingguan, rubrik, kriteria, dan pengaturan bobot dikelola dari formulir
RPS. Baris penawaran, KRS, dan nilai dikelola dari formulir induknya.

## Akses dan keamanan

Menu ditampilkan sesuai grup pengguna. Hak akses model (ACL) dan aturan record
(record rules) tetap menjadi kontrol akses terhadap data; visibilitas menu tidak
menggantikan kontrol tersebut.

## Struktur berkas view

Berkas view menggunakan nama berkas model dengan akhiran `_views.xml`, agar
pasangan model dan antarmukanya mudah ditemukan. Contoh:

- `models/master_prodi.py` → `views/master_prodi_views.xml`
- `models/akademik_krs.py` → `views/akademik_krs_views.xml`
- `models/report_summary.py` → `views/report_summary_views.xml`

Jika satu berkas model mendefinisikan beberapa model yang saling terkait,
view-view terkait dikelompokkan dalam satu berkas yang sepadan.

## Identitas penyusun

**Sesa Nugroho Satriva**  
Program Studi Teknik Industri

Disusun sebagai bagian dari **Tugas Akhir Sarjana**.
