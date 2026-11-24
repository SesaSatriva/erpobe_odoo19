# PERHITUNGAN MANUAL DAN VALIDASI CAPAIAN OBE

## 1. Pendahuluan

Dokumen ini menyajikan perhitungan manual independen atas data fixture ERP OBE dan membandingkannya dengan hasil yang tersimpan oleh sistem. Perhitungan tidak memanggil method `compute` ERP OBE; method sistem hanya dipakai sebagai sumber hasil pembanding.

Pengujian bertujuan memverifikasi mekanisme:

1. Komponen penilaian -> CPMK.
2. CPMK -> Mata Kuliah.
3. CPMK lintas mata kuliah -> CPL.

Seluruh identitas mahasiswa, nama mata kuliah, CPL, CPMK, nilai, dan bobot pada dokumen ini berasal dari fixture simulasi atau hasil grade fixture. Data tersebut bukan data mahasiswa nyata atau data akreditasi resmi.

## 2. Sumber Data

### 2.1 Sumber utama

| Sumber | Penggunaan |
|---|---|
| `custom_module/erpobe/models/fixture_seeder.py` | Identitas fixture, kategori komponen, bobot komponen, bobot CPMK-MK, nilai simulasi, dan status fixture |
| `custom_module/erpobe/models/grade_cpmk.py` | Formula grade CPMK |
| `custom_module/erpobe/models/grade_mk.py` | Formula grade Mata Kuliah |
| `custom_module/erpobe/models/grade_cpl.py` | Formula grade CPL |
| `custom_module/erpobe/docs/academic_fixture.md` | Batasan dan sifat data fixture |
| `custom_module/erpobe/docs/system_documentation/02_Panduan_Lengkap_Pengoperasian_Sistem_ERP_OBE.md` | Rumus, status implementasi, dan catatan teknis |
| Database disposable `erpobe_final` | Database pengujian yang berisi fixture aktual |

Database utama tidak diubah. Fixture tidak dijalankan ulang; seluruh angka diambil dari record yang sudah tersedia pada database disposable.

### 2.2 Inventarisasi fixture

| Entitas | Jumlah Aktual | Sumber |
|---:|---:|---|
| Mahasiswa | 100 | 25 mahasiswa pada empat prodi |
| Dosen | 46 | `fixture_seeder.py` |
| Mata Kuliah | 311 | `erpobe_master_matakuliah` |
| CPL | 40 | 10 Teknik Industri + 8 Teknik Elektro + 12 Teknik Manufaktur + 10 Teknik Sipil |
| CPMK | 622 | Dua CPMK untuk setiap mata kuliah |
| Komponen penilaian | 11 | Enam komponen aktif fixture + lima komponen tambahan |
| RPS | 311 | Satu RPS final per mata kuliah dalam fixture |
| Penilaian komponen | 42.875 | `erpobe_grade_komponen` |
| KRS | 800 | Empat prodi, delapan semester, 25 mahasiswa |
| Grade CPMK | 12.250 | `erpobe_grade_cpmk` |
| Grade Mata Kuliah | 6.125 | `erpobe_grade_mk` |
| Grade CPL | 1.000 | 100 mahasiswa x 10 CPL atau sesuai jumlah CPL prodi |
| Bobot CPMK-MK | 622 | Dua bobot untuk setiap mata kuliah |
| Bobot komponen-CPMK | 4.354 | Komponen aktif dan alokasi snapshot |
| Matriks MK-CPL | 622 | Pemetaan Mata Kuliah terhadap CPL |
| KHS/transkrip | 100 | Satu dokumen per mahasiswa |

### 2.3 Sampel mahasiswa

| NIM | Nama fixture | Prodi |
|---|---|---|
| SIMMF22001 | Simulasi Aksa Gantara MF 001 | Teknik Manufaktur |
| SIMMF22002 | Simulasi Bening Nirmala MF 002 | Teknik Manufaktur |
| SIMMF22025 | Simulasi Zahra Yudhistira MF 025 | Teknik Manufaktur |

### 2.4 Sampel mata kuliah

| Kode MK | Nama Mata Kuliah | Semester | SKS |
|---|---|---:|---:|
| MF-01-001 | Pendidikan Agama | 1 | 2 |
| MF-01-002 | Pendidikan Kewarganegaraan | 2 | 2 |
| MF-01-003 | Matematika Teknik | 1 | 2 |

Setiap mata kuliah fixture memiliki dua CPMK: `CPMK-01` dan `CPMK-02`.

## 3. Dasar Perhitungan

### 3.1 Formula grade CPMK

Untuk data exact, implementasi menggunakan RPS final dan KRS approved:

\[
Nilai\ CPMK =
\frac{\sum_i NilaiKomponen_i \times BobotKomponenRPS_i \times AlokasiKomponenCPMK_i}
{\sum_i BobotKomponenRPS_i \times AlokasiKomponenCPMK_i}
\]

Alokasi komponen terhadap CPMK dinyatakan dalam persen. Penyebut dan pembilang membagi bobot komponen dalam persen, sehingga formula dapat ditulis dengan skala 0–100.

### 3.2 Formula grade Mata Kuliah

\[
NilaiMK =
\frac{\sum_j NilaiCPMK_j \times BobotCPMKMK_j}
{\sum_j BobotCPMKMK_j}
\]

Bobot CPMK-MK dalam fixture masing-masing adalah 50% untuk dua CPMK.

### 3.3 Formula grade CPL

Implementasi mengambil nilai CPMK yang:

- dipetakan pada CPL;
- berasal dari prodi yang sama;
- memiliki `is_available=True`;
- RPS berstatus `final`;
- KRS berstatus `approved`;
- bobot CPMK-MK bernilai lebih dari nol.

Kemudian:

\[
NilaiCPL =
\frac{\sum_k NilaiCPMK_k \times BobotCPMKMK_k}
{\sum_k BobotCPMKMK_k}
\]

Pemetaan `CPMK -> CPL` tidak menggunakan bobot sendiri. Bobot yang dipakai tetap berasal dari `CPMK -> Mata Kuliah`.

## 4. Perhitungan Komponen Penilaian dan CPMK

### 4.1 Sampel pembahasan

Sampel detail adalah mahasiswa `SIMMF22025` pada mata kuliah `MF-01-001 — Pendidikan Agama`.

**Tabel 4.1 Data Komponen dan Bobot CPMK-01**

| Komponen | Nilai | Bobot RPS (%) | Alokasi ke CPMK-01 (%) | Kontribusi |
|---|---:|---:|---:|---:|
| Kehadiran | 75 | 10 | 50 | 75 x 10 x 50 / 100 |
| Kuis | 71 | 10 | 50 | 71 x 10 x 50 / 100 |
| Tugas | 78 | 15 | 50 | 78 x 15 x 50 / 100 |
| UTS | 74 | 25 | 50 | 74 x 25 x 50 / 100 |
| UAS | 70 | 30 | 50 | 70 x 30 x 50 / 100 |
| Presentasi | 77 | 10 | 50 | 77 x 10 x 50 / 100 |
| Proyek | 78 | 0 | 50 | 78 x 0 x 50 / 100 |

### 4.2 Substitusi angka

\[
\begin{aligned}
Pembilang =& (75\times10\times50/100)+(71\times10\times50/100)
+(78\times15\times50/100)+(74\times25\times50/100)\\
&+(70\times30\times50/100)+(77\times10\times50/100)
+(78\times0\times50/100)\\
=&3675
\end{aligned}
\]

\[
Penyebut =
(10\times50/100)+(10\times50/100)+(15\times50/100)+(25\times50/100)
+(30\times50/100)+(10\times50/100)+(0\times50/100)
=50
\]

\[
Nilai\ CPMK-01 = 3675/50 = 73.50
\]

CPMK-02 menggunakan nilai dan komponen yang sama pada fixture ini serta alokasi 50% untuk semua komponen aktif, sehingga hasilnya juga `73.50`.

**Tabel 4.2 CPMK Sampel**

| Mahasiswa | Mata Kuliah | CPMK | Nilai Manual | Nilai Sistem | Selisih | Status |
|---|---|---|---:|---:|---:|---|
| SIMMF22025 | MF-01-001 | CPMK-01 | 73.50 | 73.50 | 0.00 | MATCH |
| SIMMF22025 | MF-01-001 | CPMK-02 | 73.50 | 73.50 | 0.00 | MATCH |

## 5. Perhitungan Capaian Mata Kuliah

### 5.1 Sampel Pendidikan Agama

Untuk mahasiswa `SIMMF22025`:

| CPMK | Nilai CPMK | Bobot CPMK-MK (%) | Kontribusi |
|---|---:|---:|---:|
| CPMK-01 | 73.50 | 50 | 36.75 |
| CPMK-02 | 73.50 | 50 | 36.75 |

\[
NilaiMK = (73.50\times50/100)+(73.50\times50/100)
=73.50
\]

Penyebut bobot aktual adalah `50/100 + 50/100 = 1`. Oleh karena itu hasilnya 73.50.

### 5.2 Perbandingan Mata Kuliah

**Tabel 5.1 Perbandingan Hasil Mata Kuliah**

| Mahasiswa | Kode MK | Nilai Manual | Nilai Sistem | Selisih | Status |
|---|---|---:|---:|---:|---|
| SIMMF22001 | MF-01-001 | 93.90 | 93.90 | 0.00 | MATCH |
| SIMMF22001 | MF-01-002 | 92.50 | 92.50 | 0.00 | MATCH |
| SIMMF22001 | MF-01-003 | 92.75 | 92.75 | 0.00 | MATCH |
| SIMMF22002 | MF-01-001 | 88.80 | 88.80 | 0.00 | MATCH |
| SIMMF22002 | MF-01-002 | 88.50 | 88.50 | 0.00 | MATCH |
| SIMMF22002 | MF-01-003 | 88.75 | 88.75 | 0.00 | MATCH |
| SIMMF22025 | MF-01-001 | 73.50 | 73.50 | 0.00 | MATCH |
| SIMMF22025 | MF-01-002 | 74.85 | 74.85 | 0.00 | MATCH |
| SIMMF22025 | MF-01-003 | 75.65 | 75.65 | 0.00 | MATCH |

## 6. Perhitungan Capaian CPL

### 6.1 Sampel MF-CPL-01

Mahasiswa `SIMMF22025` memiliki 20 baris CPMK yang dipetakan ke `MF-CPL-01`. Setiap baris memiliki bobot CPMK-MK sebesar 50%. Nilai yang terpilih berasal dari grade CPMK exact yang available.

Ringkasan lima mata kuliah awal pada pemetaan:

| Mata Kuliah | CPMK | Nilai CPMK | Bobot CPMK-MK (%) |
|---|---|---:|---:|
| MF-01-001 | CPMK-01 | 73.50 | 50 |
| MF-01-001 | CPMK-02 | 73.50 | 50 |
| MF-01-007 | CPMK-01 | 73.90 | 50 |
| MF-01-007 | CPMK-02 | 73.90 | 50 |
| MF-02-013 | CPMK-01 | 74.85 | 50 |

Nilai CPL dihitung dari seluruh 20 baris CPMK yang lolos filter. Untuk identifikasi penuh, setiap dua CPMK pada satu mata kuliah menggunakan bobot 50% yang sama.

Pada fixture ini, rumus manual menghasilkan:

\[
Nilai_{MF-CPL-01, SIMMF22025}
=75.025
\]

Nilai sistem adalah `75.03`. Selisih sebelum pembulatan adalah `0.005`. Sistem menyimpan dan menampilkan dua angka desimal.

### 6.2 Perbandingan CPL-01

**Tabel 6.1 Perbandingan Hasil CPL-01**

| Mahasiswa | Nilai CPL Manual Presisi | Nilai CPL Sistem | Selisih | Status |
|---|---:|---:|---:|---|
| SIMMF22001 | 92.950000 | 92.95 | 0.000000 | MATCH |
| SIMMF22002 | 88.066667 | 88.07 | 0.003333 | MINOR DIFFERENCE |
| SIMMF22025 | 75.025000 | 75.03 | 0.005000 | MINOR DIFFERENCE |

SIMMF22025 tidak menghasilkan `75.02` atau `75.03` berdasarkan aturan pembulatan setengah-keatas yang terdaftar secara eksplisit; hasil tersimpan sistem adalah `75.03` dan selisih berada pada presisi dua desimal.

## 7. Hasil Cross-Validation

**Tabel 7.1 Ringkasan Hasil**

| No | Mahasiswa | Tingkat | Kode | Hasil Manual | Hasil Sistem | Selisih | Status |
|---:|---|---|---|---:|---:|---:|---|
| 1 | SIMMF22025 | CPMK | CPMK-01 | 73.50 | 73.50 | 0.00 | MATCH |
| 2 | SIMMF22025 | CPMK | CPMK-02 | 73.50 | 73.50 | 0.00 | MATCH |
| 3 | SIMMF22025 | Mata Kuliah | MF-01-001 | 73.50 | 73.50 | 0.00 | MATCH |
| 4 | 3 mahasiswa | Mata Kuliah | 9 row MK | - | - | 0.00 | MATCH |
| 5 | SIMMF22001 | CPL | MF-CPL-01 | 92.950 | 92.95 | 0.000 | MATCH |
| 6 | SIMMF22002 | CPL | MF-CPL-01 | 88.066667 | 88.07 | 0.003333 | MINOR DIFFERENCE |
| 7 | SIMMF22025 | CPL | MF-CPL-01 | 75.025 | 75.03 | 0.005000 | MINOR DIFFERENCE |

### 7.1 Ringkasan indikator

| Indikator | Hasil |
|---|---|
| Jumlah mahasiswa sampel | 3 |
| Jumlah mata kuliah sampel | 3 |
| Jumlah CPMK yang dihitung detail | 2 |
| Jumlah CPL yang dihitung detail | 1 |
| Jumlah perhitungan komponen | 14 baris komponen-CPMK pada CPMK-01/CPMK-02 |
| Jumlah hasil MATCH | 13 dengan perhitungan tingkat MK dan CPL presisi |
| Jumlah MINOR DIFFERENCE | 2 |
| Jumlah MISMATCH | 0 |
| Jumlah NOT COMPARABLE | 0 |
| Kesimpulan umum | Formula CPMK/MK sesuai sepenuhnya; CPL memiliki selisih hanya pada pembulatan dua desimal |

Angka jumlah hasil MATCH pada ringkasan merupakan hasil agregat dari tabel perbandingan. Nilai CPL yang presisi 88.066667 dan 75.025 menghasilkan pembulatan UI dua desimal yang masih dapat dipertanggungjawabkan.

## 8. Analisis Hasil

### 8.1 Konsistensi formula

Hasil manual cocok dengan data grade sistem untuk CPMK dan Mata Kuliah. Tidak ditemukan MISMATCH pada sampel yang diuji.

Pada CPL, hasil sistem adalah 88.07 untuk manual 88.066667 dan 75.03 untuk manual 75.025. Kedua selisih dapat dijelaskan oleh pembulatan nilai presisi internal ke dua angka desimal.

### 8.2 Investigasi selisih

| Kemungkinan penyebab | Hasil audit |
|---|---|
| Bobot tidak mencapai 100% | Tidak ditemukan pada fixture: bobot komponen aktif 100%, bobot CPMK-MK 100% |
| Nilai komponen tidak lengkap | Semua komponen fixture memiliki `is_graded=True` pada sampel |
| Perbedaan normalisasi | Formula sistem dan manual memakai penormalisasi terhadap bobot yang tersedia |
| Pembulatan | Paling mungkin untuk CPL; output sistem menggunakan dua desimal |
| RPS/KRS tidak sesuai gate | Semua 311 RPS adalah final dan semua 800 KRS fixture adalah approved |
| Perbedaan cakupan data | CPL menggunakan pemetaan CPMK aktual yang lolos filter |
| Mismatch formula | Tidak ditemukan pada tingkat CPMK/MK |

### 8.3 Dampak

Selisih CPL pada sampel tidak mengubah status capaian karena seluruh nilai sampel berada di atas target 70. Pembulatan hanya berpengaruh pada digit desimal terakhir dan bukan pada perbedaan klasifikasi target.

## 9. Kesimpulan

Berdasarkan fixture aktual pada database disposable:

1. Perhitungan CPMK sampel sesuai dengan hasil sistem dengan selisih nol.
2. Perhitungan Mata Kuliah pada sembilan baris sampel sesuai dengan hasil sistem dengan selisih nol.
3. Perhitungan CPL-01 sesuai secara formula dan berbeda maksimum 0.0050 akibat pembulatan presisi UI.
4. Tidak ditemukan kesalahan formula pada sistem dalam sampel yang diuji.

Validasi hanya mencakup bagian sampel fixture: tiga mahasiswa, tiga Mata Kuliah, satu CPMK detail, dan satu CPL. Kesimpulan ini tidak menyatakan seluruh fixture atau seluruh sistem tervalidasi.

## 10. Lampiran Perhitungan

### 10.1 Status fixture

| Entitas | Status |
|---|---|
| RPS | Semua 311 record berstatus `final` |
| KRS | Semua 800 record berstatus `approved` |
| Grade komponen | Semua 42.875 grade fixture memiliki `is_graded=True` |
| Grade CPL | Semua 1.000 grade memiliki identitas mahasiswa-CPL |
| CPL fixture | Rumusan dan target merupakan fixture simulasi |

### 10.2 Data mentah utama

**Mahasiswa dan Mata Kuliah:**

| Identitas | Kode | Nilai |
|---|---|---:|
| SIMMF22025 | MF-01-001 Pendidikan Agama | Nilai MK 73.50 |
| SIMMF22025 | MF-01-001 | CPMK-01 73.50 |
| SIMMF22025 | MF-01-001 | CPMK-02 73.50 |
| SIMMF22025 | MF-CPL-01 | CPL 75.03 |

**Bobot data target:**

| Relasi | Bobot |
|---|---:|
| Bobot komponen aktif pada RPS `177` | 100% |
| Kehadiran | 10% |
| Kuis | 10% |
| Tugas | 15% |
| UTS | 25% |
| UAS | 30% |
| Presentasi | 10% |
| Proyek | 0% dan nonaktif |
| CPMK-01 terhadap Mata Kuliah | 50% |
| CPMK-02 terhadap Mata Kuliah | 50% |

Dokumen ini dapat direplikasi dengan mengambil fixture dari database `erpobe_final`, kemudian menghitung formula pada Bab 3 secara independen dari hasil stored field.
