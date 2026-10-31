# ERP OBE Management

Modul **ERP OBE Management** menyediakan sarana pengelolaan data akademik dan
evaluasi capaian pembelajaran berbasis Outcome-Based Education (OBE) di Odoo.
Modul ini menghubungkan data fakultas dan program studi dengan kurikulum,
perkuliahan, penilaian, hasil studi, dan analitik akademik.

## Fitur

### Data akademik

- Pengelolaan fakultas dan program studi.
- Data dosen, mahasiswa, rombongan belajar (rombel), mata kuliah, dan angkatan.
- Fakultas menampilkan data fakultas dan daftar program studi saja.
- Data akademik ditelusuri melalui **Fakultas → Program Studi → Detail Prodi**.

### Kurikulum dan RPS

- Pengelolaan Capaian Pembelajaran Lulusan (CPL) dan Capaian Pembelajaran Mata
  Kuliah (CPMK), termasuk pemetaan CPL–CPMK.
- Penyusunan Rencana Pembelajaran Semester (RPS).
- Pengelolaan kegiatan pembelajaran mingguan, metode, dan referensi.
- Pengaturan komponen penilaian, rubrik, kriteria, serta bobot penilaian.
- RPS melekat pada penawaran mata kuliah; salinan menjadi versi baru berstatus
  **Perlu Ditinjau** dan RPS **Final** bersifat read-only.
- Finalisasi RPS memerlukan seluruh kelompok bobot terkait tepat 100% dengan
  toleransi 0,01 poin persentase.
- Panel **Kelengkapan Bobot** pada detail prodi menampilkan kelompok bermasalah,
  selisih, filter, tautan perbaikan, dan daftar yang dapat diekspor.

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
| Fakultas | Data fakultas dan daftar program studi |
| Program Studi | Master akademik prodi, CPL/CPMK, mata kuliah, dosen, rombel, penawaran, RPS, dan monitoring bobot |
| Perkuliahan | KRS dan input nilai |
| Hasil dan Analitik | KHS, analisis capaian, serta rekap per rombel dan angkatan |

Tahun ajaran dan penawaran dibuka dari detail program studi. Kegiatan mingguan,
rubrik, kriteria, dan pengaturan bobot dikelola dari formulir RPS. Baris KRS dan
nilai dikelola dari formulir induknya.

Bobot dapat disimpan sebagai draft meskipun belum lengkap. Statusnya tetap
ditandai belum lengkap dan endpoint model `erpobe.weight.validation.get_problem_items`
menyediakan daftar isu untuk UI atau ekspor. Hanya RPS berstatus **Perlu
Ditinjau** dengan seluruh kelompok bobot lengkap yang dapat difinalisasi.

Saat upgrade, RPS lama hanya ditautkan otomatis jika mata kuliahnya cocok dengan
tepat satu penawaran. RPS dengan beberapa kemungkinan penawaran dan penawaran
lintas prodi tetap perlu diperiksa manual; lihat catatan di
`migrations/19.0.2.1.0/README.md`.

Asumsi: bobot CPMK–CPL disimpan pada record RPS, sehingga validasi dua arah
CPMK→CPL dan CPL←CPMK dihitung dalam satu versi RPS/penawaran, bukan
digabungkan lintas tahun ajaran. Tahun ajaran tetap menjadi master global yang
dipakai bersama oleh program studi.

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
