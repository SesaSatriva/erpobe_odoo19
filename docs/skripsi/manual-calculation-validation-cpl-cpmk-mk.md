# Validasi Perhitungan Manual CPL, CPMK, dan Mata Kuliah pada Empat Program Studi ERP OBE

## 1. Pendahuluan

Dokumen ini menyajikan pemeriksaan independen terhadap hasil capaian OBE yang tersimpan pada database ERP OBE. Seluruh identitas mahasiswa, nama mata kuliah, kode CPL/CPMK, nilai, dan bobot berasal dari fixture akademik simulasi dan database aktual. Data ini bukan data mahasiswa nyata atau data akreditasi resmi.

Pengujian membandingkan perhitungan manual dengan nilai stored field:

1. Komponen penilaian menuju CPMK.
2. CPMK menuju mata kuliah.
3. CPMK lintas mata kuliah menuju CPL.

Method `compute` Odoo tidak dipanggil untuk menghasilkan pembanding manual. Perhitungan independen dibangun dari record PostgreSQL; method sistem hanya digunakan sebagai sumber nilai yang tersimpan untuk dibandingkan.

## 2. Tujuan Pengujian

Tujuan pengujian adalah memastikan formula, status kelayakan, hubungan prodi, RPS final, KRS approved, bobot komponen, bobot CPMK-MK, dan pemetaan CPMK-CPL menghasilkan nilai yang konsisten dengan database untuk Teknik Industri, Teknik Elektro, Teknik Manufaktur, dan Teknik Sipil.

## 3. Sumber Data dan Lingkungan Pengujian

| Sumber | Penggunaan |
|---|---|
| `custom_module/erpobe/models/fixture_seeder.py` | Fixture identitas, relasi, status, dan nilai simulasi |
| `custom_module/erpobe/models/grade_cpmk.py` | Implementasi formula CPMK |
| `custom_module/erpobe/models/grade_mk.py` | Implementasi formula mata kuliah |
| `custom_module/erpobe/models/grade_cpl.py` | Implementasi formula CPL dan gate kelayakan |
| `custom_module/erpobe/docs/academic_fixture.md` | Batasan dan sifat fixture |
| `custom_module/erpobe/docs/system_documentation/02_Panduan_Lengkap_Pengoperasian_Sistem_ERP_OBE.md` | Rumus dan ketentuan operasional |
| Database PostgreSQL `erpobe_final` | Sumber record aktual yang divalidasi |

Database alternatif diperiksa. `erpobe_final` teridentifikasi sebagai database fixture paling lengkap. Database tidak diubah dan fixture tidak dijalankan ulang.

Toleransi klasifikasi adalah 0,01 dari nilai internal. Status:

- `MATCH`: selisih mutlak <= 0,01.
- `MINOR DIFFERENCE`: 0,01 < selisih <= 0,02 atau dapat dijelaskan pembulatan/presisi.
- `MISMATCH`: selisih > 0,02.
- `NOT COMPARABLE`: prasyarat data tidak memenuhi syarat.
- `MISSING`: record yang seharusnya tersedia tidak ditemukan.

## 4. Inventarisasi Data Empat Program Studi

| Entitas | Teknik Industri | Teknik Elektro | Teknik Manufaktur | Teknik Sipil |
|---|---:|---:|---:|---:|
| Mahasiswa | 25 | 25 | 25 | 25 |
| Mata kuliah | 76 | 100 | 71 | 64 |
| CPL | 10 | 8 | 12 | 10 |
| CPMK | 152 | 200 | 142 | 128 |
| RPS final | 76 | 100 | 71 | 64 |
| KRS approved | 200 baris/25 mahasiswa | 200/25 mahasiswa | 200/25 mahasiswa | 200/25 mahasiswa |
| Grade komponen | 10.375 | 13.000 | 10.700 | 8.800 |
| Grade CPMK | 3.150 | 2.850 | 3.050 | 3.200 |
| Grade mata kuliah | 1.575 | 1.425 | 1.525 | 1.600 |
| Grade CPL | 250 | 200 | 300 | 250 |

Inventarisasi total: 100 mahasiswa, 311 mata kuliah, 40 CPL, 622 CPMK, 311 RPS final, 800 KRS approved, 42.875 grade komponen, 12.250 grade CPMK, 6.125 grade mata kuliah, dan 1.000 grade CPL.

## 5. Metodologi dan Formula Perhitungan

### 5.1 Komponen penilaian menuju CPMK

\[
NilaiCPMK=
\frac{\sum_i NilaiKomponen_i \times BobotKomponenRPS_i \times Alokasi_i}
{\sum_i BobotKomponenRPS_i \times Alokasi_i}
\]

Alokasi dinyatakan dalam persen. Hanya snapshot komponen aktif yang memiliki grade `is_graded=True`, RPS final, dan KRS approved yang dihitung.

### 5.2 CPMK menuju mata kuliah

\[
NilaiMK=
\frac{\sum_j NilaiCPMK_j \times BobotCPMKMK_j}
{\sum_j BobotCPMKMK_j}
\]

### 5.3 CPMK lintas mata kuliah menuju CPL

\[
NilaiCPL=
\frac{\sum_k NilaiCPMK_k \times BobotCPMKMK_k}
{\sum_k BobotCPMKMK_k}
\]

Pemetaan CPMK-CPL tidak menambahkan bobot CPMK-CPL. Bobot yang digunakan tetap berasal dari relasi CPMK-MK. Implementasi juga membatasi CPMK pada prodi yang sama dan mata kuliah yang dipetakan ke CPL.

## 6. Validasi CPMK

| Prodi | Mahasiswa diperiksa | CPMK diperiksa | MATCH | MINOR | MISMATCH | NOT COMPARABLE | MISSING |
|---|---:|---:|---:|---:|---:|---:|---:|
| Teknik Industri | 25 | 3.150 | 3.150 | 0 | 0 | 0 | 0 |
| Teknik Elektro | 25 | 2.850 | 2.850 | 0 | 0 | 0 | 0 |
| Teknik Manufaktur | 25 | 3.050 | 3.050 | 0 | 0 | 0 | 0 |
| Teknik Sipil | 25 | 3.200 | 3.200 | 0 | 0 | 0 | 0 |
| **Total** | **100** | **12.250** | **12.250** | **0** | **0** | **0** | **0** |

### 6.1 Contoh hasil per program studi

| Prodi | NIM | Kode MK | CPMK | Nilai manual | Nilai sistem | Selisih | Status |
|---|---|---|---|---:|---:|---:|---|
| Teknik Industri | SIMIN22007 | IN-02-012 | CPMK-01 | 67,75 | 67,75 | 0,00 | MATCH |
| Teknik Industri | SIMIN22022 | IN-06-047 | CPMK-02 | 87,85 | 87,85 | 0,00 | MATCH |
| Teknik Elektro | SIMEL22001 | EL-01-001 | CPMK-01 | 93,90 | 93,90 | 0,00 | MATCH |
| Teknik Elektro | SIMEL22022 | EL-03-029 | CPMK-02 | 88,50 | 88,50 | 0,00 | MATCH |
| Teknik Manufaktur | SIMMF22001 | MF-01-001 | CPMK-01 | 93,90 | 93,90 | 0,00 | MATCH |
| Teknik Manufaktur | SIMMF22022 | MF-04-031 | CPMK-02 | 86,50 | 86,50 | 0,00 | MATCH |
| Teknik Sipil | SIMSI22001 | SI-01-001 | CPMK-01 | 93,90 | 93,90 | 0,00 | MATCH |
| Teknik Sipil | SIMSI22002 | SI-05-049 | CPMK-01 | 86,50 | 86,50 | 0,00 | MATCH |

## 7. Validasi Mata Kuliah

| Prodi | Mata kuliah diperiksa | MATCH | MINOR | MISMATCH | NOT COMPARABLE | MISSING |
|---|---:|---:|---:|---:|---:|---:|
| Teknik Industri | 1.575 | 1.575 | 0 | 0 | 0 | 0 |
| Teknik Elektro | 1.425 | 1.425 | 0 | 0 | 0 | 0 |
| Teknik Manufaktur | 1.525 | 1.525 | 0 | 0 | 0 | 0 |
| Teknik Sipil | 1.600 | 1.600 | 0 | 0 | 0 | 0 |
| **Total** | **6.125** | **6.125** | **0** | **0** | **0** | **0** |

### 7.1 Contoh hasil per program studi

| Prodi | NIM | Kode MK | Nama MK | Nilai manual | Nilai sistem | Selisih | Status |
|---|---|---|---|---:|---:|---:|---|
| Teknik Industri | SIMIN22002 | IN-02-012 | Bahasa Indonesia | 88,80 | 88,80 | 0,00 | MATCH |
| Teknik Industri | SIMIN22001 | IN-04-033 | Ekonomika dan Ekonomi Teknik | 93,65 | 93,65 | 0,00 | MATCH |
| Teknik Elektro | SIMEL22001 | EL-01-001 | Pendidikan Agama | 93,90 | 93,90 | 0,00 | MATCH |
| Teknik Elektro | SIMEL22022 | EL-04-029 | Internet of Things | 87,75 | 87,75 | 0,00 | MATCH |
| Teknik Manufaktur | SIMMF22001 | MF-01-001 | Pendidikan Agama | 93,90 | 93,90 | 0,00 | MATCH |
| Teknik Manufaktur | SIMMF22016 | MF-04-031 | Teknologi Pengangkat dan Pengangkut | 70,75 | 70,75 | 0,00 | MATCH |
| Teknik Sipil | SIMSI22001 | SI-01-001 | Pendidikan Agama Islam | 93,90 | 93,90 | 0,00 | MATCH |
| Teknik Sipil | SIMSI22007 | SI-04-033 | Kreativitas, Inovasi, dan Kewirausahaan | 67,50 | 67,50 | 0,00 | MATCH |

## 8. Validasi CPL

| Prodi | CPL diperiksa | MATCH | MINOR | MISMATCH | NOT COMPARABLE | MISSING |
|---|---:|---:|---:|---:|---:|---:|
| Teknik Industri | 250 | 250 | 0 | 0 | 0 | 0 |
| Teknik Elektro | 200 | 200 | 0 | 0 | 0 | 0 |
| Teknik Manufaktur | 300 | 300 | 0 | 0 | 0 | 0 |
| Teknik Sipil | 250 | 250 | 0 | 0 | 0 | 0 |
| **Total** | **1.000** | **1.000** | **0** | **0** | **0** | **0** |

### 8.1 Contoh hasil per program studi

| Prodi | NIM | Kode CPL | Jumlah CPMK | Nilai manual | Nilai sistem | Selisih | Status |
|---|---|---|---:|---:|---:|---:|---|
| Teknik Industri | SIMIN22010 | IN-CPL-06 | 24 | 54,041667 | 54,04 | 0,001667 | MATCH |
| Teknik Industri | SIMIN22016 | IN-CPL-06 | 26 | 70,953846 | 70,95 | 0,003846 | MATCH |
| Teknik Elektro | SIMEL22007 | EL-CPL-01 | 32 | 67,987500 | 67,99 | 0,002500 | MATCH |
| Teknik Elektro | SIMEL22019 | EL-CPL-05 | 28 | 58,796429 | 58,80 | 0,003571 | MATCH |
| Teknik Manufaktur | SIMMF22001 | MF-CPL-01 | 20 | 92,950000 | 92,95 | 0,000000 | MATCH |
| Teknik Manufaktur | SIMMF22017 | MF-CPL-01 | 20 | 68,110000 | 68,11 | 0,000000 | MATCH |
| Teknik Sipil | SIMSI22001 | SI-CPL-01 | 26 | 93,107692 | 93,11 | 0,002308 | MATCH |
| Teknik Sipil | SIMSI22015 | SI-CPL-06 | 26 | 74,800000 | 74,80 | 0,000000 | MATCH |

## 9. Contoh Perhitungan Manual Teknik Industri

**CPMK:** Mahasiswa `SIMIN22007`, mata kuliah `IN-02-012 — Bahasa Indonesia`, CPMK-01.

| Komponen | Nilai | Bobot RPS | Alokasi CPMK | Kontribusi |
|---|---:|---:|---:|---:|
| Kehadiran | 72 | 10% | 50% | 72×10×50/100 = 360 |
| Kuis | 68 | 10% | 50% | 68×10×50/100 = 340 |
| Tugas | 64 | 15% | 50% | 64×15×50/100 = 480 |
| UTS | 71 | 25% | 50% | 71×25×50/100 = 887,5 |
| UAS | 67 | 30% | 50% | 67×30×50/100 = 1005 |
| Presentasi | 63 | 10% | 50% | 63×10×50/100 = 315 |
| Proyek | 64 | 0% | 50% | tidak berkontribusi |

\[
NilaiCPMK=\frac{360+340+480+887,5+1005+315}{5+5+7,5+12,5+15+5}
=\frac{3387,5}{50}=67,75
\]

Nilai sistem: 67,75; selisih: 0,00; status: `MATCH`.

**Mata kuliah:** `SIMIN22002`, `IN-02-012 — Bahasa Indonesia`.

\[
NilaiMK=\frac{88,80\times50+88,80\times50}{50+50}=88,80
\]

Nilai sistem: 88,80; selisih: 0,00; status: `MATCH`.

**CPL:** `SIMIN22010`, `IN-CPL-06`, 24 CPMK terhitung, bobot CPMK-MK 50% untuk relasi yang terpetakan.

\[
NilaiCPL=\frac{\sum_{k=1}^{24} NilaiCPMK_k\times50}
{24\times50}
=54,041667\approx54,04
\]

Nilai sistem: 54,04; selisih presisi: 0,001667; status: `MATCH`.

## 10. Contoh Perhitungan Manual Teknik Elektro

Dua CPMK: `SIMEL22001/EL-01-001/CPMK-01 = 93,90` dan `SIMEL22022/EL-04-029/CPMK-02 = 88,50`; kedua hasil sama dengan nilai sistem.

Untuk mata kuliah, dengan dua bobot masing-masing 50%:

\[
NilaiMK_{SIMEL22001}=\frac{93,90\times50+93,90\times50}{50+50}=93,90
\]

\[
NilaiMK_{SIMEL22022}=\frac{87,75\times50+87,75\times50}{50+50}=87,75
\]

Contoh CPL:

\[
NilaiCPL_{SIMEL22007,EL-CPL-01}
=\frac{\sum_{k=1}^{32} NilaiCPMK_k\times50}{32\times50}
=67,987500\approx67,99
\]

Nilai sistem: 67,99; selisih: 0,002500; `MATCH`.

## 11. Contoh Perhitungan Manual Teknik Manufaktur

**CPMK:** `SIMMF22001`, `MF-01-001 — Pendidikan Agama`, CPMK-01.

Nilai komponen aktual adalah Kehadiran 91, Kuis 98, Tugas 94, UTS 90, UAS 97, Presentasi 93, dan Proyek 94 dengan bobot aktif 10/10/15/25/30/10 persen. Alokasi CPMK-01 adalah 50% untuk seluruh komponen aktif. Komponen proyek bobot 0 dan tidak aktif.

\[
NilaiCPMK=
\frac{91(10)(50)+98(10)(50)+94(15)(50)+90(25)(50)+97(30)(50)+93(10)(50)}
{10(50)+10(50)+15(50)+25(50)+30(50)+10(50)}
\times\frac1{100}
=93,90
\]

Nilai sistem: 93,90; selisih: 0,00; `MATCH`.

Untuk dua mahasiswa mata kuliah:

\[
NilaiMK_{SIMMF22001,MF-01-001}
=\frac{93,90(50)+93,90(50)}{50+50}=93,90
\]

\[
NilaiMK_{SIMMF22016,MF-04-031}
=\frac{70,75(50)+70,75(50)}{50+50}=70,75
\]

Contoh CPL `SIMMF22001/MF-CPL-01` menggunakan 20 CPMK terpetakan:

\[
NilaiCPL=\frac{\sum_{k=1}^{20} NilaiCPMK_k\times50}{20\times50}=92,95
\]

Nilai sistem: 92,95; selisih: 0,00; `MATCH`.

## 12. Contoh Perhitungan Manual Teknik Sipil

Dua CPMK: `SIMSI22001/SI-01-001/CPMK-01 = 93,90` dan `SIMSI22002/SI-05-049/CPMK-01 = 86,50`; nilai sistem masing-masing identik.

Dua mata kuliah:

\[
NilaiMK_{SIMSI22001,SI-01-001}
=\frac{93,90(50)+93,90(50)}{50+50}=93,90
\]

\[
NilaiMK_{SIMSI22007,SI-04-033}
=\frac{67,50(50)+67,50(50)}{50+50}=67,50
\]

Contoh CPL:

\[
NilaiCPL_{SIMSI22001,SI-CPL-01}
=\frac{\sum_{k=1}^{26} NilaiCPMK_k\times50}{26\times50}
=93,107692\approx93,11
\]

Nilai sistem: 93,11; selisih presisi: 0,002308; `MATCH`.

## 13. Rekapitulasi Cross-Validation

| Tingkat | Jumlah perhitungan | MATCH | MINOR DIFFERENCE | MISMATCH | NOT COMPARABLE | MISSING |
|---|---:|---:|---:|---:|---:|---:|
| CPMK | 12.250 | 12.250 | 0 | 0 | 0 | 0 |
| Mata kuliah | 6.125 | 6.125 | 0 | 0 | 0 | 0 |
| CPL | 1.000 | 1.000 | 0 | 0 | 0 | 0 |
| **Gabungan** | **19.375** | **19.375** | **0** | **0** | **0** | **0** |

Persentase kesesuaian = 19.375 / 19.375 × 100% = 100,00%. Tidak ada MINOR DIFFERENCE maupun MISMATCH pada pembandingan record penuh.

Rekap per prodi:

| Indikator | Teknik Industri | Teknik Elektro | Teknik Manufaktur | Teknik Sipil |
|---|---:|---:|---:|---:|
| Mahasiswa diperiksa | 25 | 25 | 25 | 25 |
| Mahasiswa valid | 25 | 25 | 25 | 25 |
| CPMK diperiksa | 3.150 | 2.850 | 3.050 | 3.200 |
| MK diperiksa | 1.575 | 1.425 | 1.525 | 1.600 |
| CPL diperiksa | 250 | 200 | 300 | 250 |
| MATCH | 4.975 | 4.475 | 4.875 | 5.050 |
| MINOR DIFFERENCE | 0 | 0 | 0 | 0 |
| MISMATCH | 0 | 0 | 0 | 0 |
| NOT COMPARABLE | 0 | 0 | 0 | 0 |
| MISSING | 0 | 0 | 0 | 0 |
| Persentase kesesuaian | 100% | 100% | 100% | 100% |

## 14. Analisis Selisih dan Anomali

Tidak ditemukan MINOR DIFFERENCE, MISMATCH, maupun NOT COMPARABLE pada 19.375 perbandingan record.

Temuan konsistensi:

| Pemeriksaan | Hasil |
|---|---|
| Nilai CPMK, MK, atau CPL di luar 0–100 | Tidak ditemukan |
| CPL tanpa CPMK terpetakan | Tidak ditemukan |
| CPMK tanpa mata kuliah | Tidak ditemukan |
| Mata kuliah tanpa RPS final | Tidak ditemukan |
| KRS approved | 800/800 |
| Bobot komponen aktif per RPS | Semua total 100% |
| Bobot CPMK-MK per RPS | Semua total 100% |
| Alokasi komponen-CPMK aktif | Tidak ditemukan pelanggaran pada relasi yang digunakan |
| Grade komponen duplikat pada attempt | Tidak ditemukan |
| Grade CPMK duplikat pasangan mahasiswa-CPMK | Tidak ditemukan |
| Grade MK duplikat pasangan mahasiswa-MK | Tidak ditemukan |
| Grade CPL duplikat pasangan mahasiswa-CPL | Tidak ditemukan |
| Nilai CPMK/MK/CPL tersedia | Seluruh record grade yang ada bernilai available |

Anomali terbatas:

1. Enam CPMK Teknik Elektro tidak memiliki grade CPMK: EL-07-092 CPMK-01/02, EL-07-095 CPMK-01/02, dan EL-07-098 CPMK-01/02. Ketiganya merupakan mata kuliah pilihan simulasi. Tidak terdapat grade mahasiswanya.
2. Enam CPMK tersebut tidak termasuk dalam 12.250 record yang dapat dibandingkan, dan status kelengkapannya perlu dicatat sebagai `MISSING` pada tingkat inventarisasi CPMK, bukan MISMATCH perhitungan.
3. Tidak ditemukan grade CPL unavailable. Semua 1.000 record CPL tersedia.

## 15. Evaluasi Konsistensi Antarprogram Studi

Relasi dan formula konsisten pada keempat prodi. Seluruh bobot aktif RPS mencapai 100%, CPMK-MK mencapai 100%, RPS berstatus final, dan KRS fixture berstatus approved. Nilai dihitung tetap terpisah berdasarkan `prodi_id` mahasiswa dan entitas akademik. Tidak ditemukan pencampuran mahasiswa atau CPMK lintas prodi.

Terdapat perbedaan jumlah mata kuliah dan CPL antarprodi sebagaimana konfigurasi fixture, tetapi tidak ada perbedaan struktur formula yang teramati.

## 16. Kesimpulan

Berdasarkan database `erpobe_final`, keempat program studi telah diperiksa secara aktual. Seluruh 12.250 grade CPMK, 6.125 grade mata kuliah, dan 1.000 grade CPL cocok dengan perhitungan manual menurut tolok ukur 0,01. Dengan demikian, persentase kesesuaian pembanding yang tersedia adalah 100%.

Tidak ada MISMATCH formula pada fixture yang diperiksa. Enam CPMK pilihan Teknik Elektro dicatat sebagai coverage MISSING karena tidak memiliki record grade, bukan sebagai kesalahan nilai.

## 17. Lampiran Data dan Perhitungan

### 17.1 Status database

| Item | Hasil |
|---|---|
| Database pengujian | `erpobe_final` |
| Akses PostgreSQL | Berhasil |
| Database produksi diubah | Tidak |
| Fixture dijalankan ulang | Tidak |
| Mahasiswa fixture diperiksa | 100/100 |
| Mahasiswa valid | 100/100 |

### 17.2 Keamanan klaim akademik

Dokumen ini memvalidasi data fixture ERP OBE dan implementasi rumus pada database pengujian. Dokumen tidak menyatakan bahwa nilai fixture merupakan capaian resmi mahasiswa maupun bukti akreditasi.

### 17.3 Jejak data

- Nilai komponen: `erpobe_grade_komponen`
- Bobot komponen-CPMK: `erpobe_bobot_komponen_cpmk`
- Bobot CPMK-MK: `erpobe_bobot_cpmk_mk`
- Pemetaan CPL-CPMK: `erpobe_akademik_cpl_mk_cpmk`
- Pemetaan MK-CPL: `erpobe_akademik_mk_cpl`
- RPS: `erpobe_akademik_rps`
- Snapshot komponen RPS: `erpobe_akademik_rps_komponen`
- KRS: `erpobe_akademik_krs` dan `erpobe_akademik_krs_line`
- Pembanding CPMK: `erpobe_grade_cpmk`
- Pembanding MK: `erpobe_grade_mk`
- Pembanding CPL: `erpobe_grade_cpl`
