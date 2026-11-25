# Laporan Pengujian Unit Modul ERPOBE

## A. Informasi Pengujian

| Informasi | Nilai |
|---|---|
| Nama modul | `erpobe` |
| Versi modul terpasang | `19.0.2.8.0` |
| Versi Odoo | `19.0` |
| Versi Python | `3.12.3` |
| Virtual environment | `/home/sesa/odoo-dev/custom-odoo19/.venv` |
| Executable Odoo | `/home/sesa/odoo-dev/odoo19/odoo-bin` |
| Database pengujian | `erpobe_unittest` |
| Database dilindungi | `erpobe_final` (tidak dijalankan pengujian dan tidak diubah) |
| Metode pengujian | Unit test Odoo per berkas menggunakan `--test-file` |
| Pendekatan database | Pendekatan A — database kosong baru |
| Port pengujian | `8071` |
| Waktu mulai pengujian per berkas | `2026-11-26 01:10:08 +0700` |
| Waktu selesai pengujian per berkas | `2026-11-26 01:12:12 +0700` |
| Total durasi pengujian | `2 menit 4 detik` |
| Lokasi log | `custom_module/erpobe/docs/testing/unit_test_results/` |

Pengujian dilakukan pada database terpisah `erpobe_unittest`. Pendekatan A berhasil setelah instalasi modul pada database kosong baru. Konfigurasi Odoo yang tersedia digunakan pada
`/home/sesa/odoo-dev/odoo19/debian/odoo.conf`; koneksi pengujian lokal menggunakan identitas PostgreSQL lokal `sesa` yang telah terverifikasi memiliki hak pembuatan database. Tidak ada password atau kredensial lain ditulis ke laporan atau log.

## B. Hasil Pengujian Per Berkas

| No. | Nama Berkas | Jumlah Uji | Lulus | Gagal | Galat | Status |
|---:|---|---:|---:|---:|---:|---|
| 1 | `test_audit_log.py` | 10 | 10 | 0 | 0 | SELESAI |
| 2 | `test_faculty_scope.py` | 19 | 18 | 1 | 0 | SELESAI |
| 3 | `test_rps_versioning.py` | 5 | 4 | 0 | 1 | SELESAI |
| 4 | `test_weight_validation.py` | 10 | 9 | 1 | 0 | SELESAI |
| 5 | `test_academic_fixture.py` | 10 | 10 | 0 | 0 | SELESAI |
| 6 | `test_triton_workflows.py` | 18 | 14 | 4 | 0 | SELESAI |
| 7 | `test_import_export.py` | 11 | 11 | 0 | 0 | SELESAI |
| 8 | `test_ui_views.py` | 10 | 10 | 0 | 0 | SELESAI |
| 9 | `test_academic_assistant.py` | 13 | 11 | 0 | 2 | SELESAI |
| 10 | `test_demo_users.py` | 3 | 3 | 0 | 0 | SELESAI |

Tidak ada berkas yang mengalami `TIMEOUT` atau `TIDAK_ADA_RINGKASAN`.

## C. Rekapitulasi Kelompok Pengujian Tabel 22

| No. | Kelompok Pengujian | Jumlah Uji | Lulus | Gagal | Galat |
|---:|---|---:|---:|---:|---:|
| 1 | Audit — `test_audit_log` | 10 | 10 | 0 | 0 |
| 2 | Hak akses dan cakupan fakultas — `test_faculty_scope` | 19 | 18 | 1 | 0 |
| 3 | Versi RPS dan bobot — `test_rps_versioning` + `test_weight_validation` | 15 | 13 | 1 | 1 |
| 4 | Fixture dan perhitungan — `test_academic_fixture` + `test_triton_workflows` | 28 | 24 | 4 | 0 |
| 5 | Impor dan ekspor — `test_import_export` | 11 | 11 | 0 | 0 |
| 6 | Antarmuka — `test_ui_views` | 10 | 10 | 0 | 0 |
| 7 | Asisten akademik — `test_academic_assistant` | 13 | 11 | 0 | 2 |

Jumlah pengujian utama adalah 106 uji, dengan 97 lulus, 6 gagal, dan 3 galat.

## D. Pengujian Tambahan: `test_demo_users`

`test_demo_users.py` menguji pembuatan profil pengguna fixture, cakupan akun berdasarkan prodi dan fakultas, autentikasi akun dosen dan mahasiswa, administrasi prodi, serta sifat idempotent dan pemeliharaan akun yang telah dimodifikasi secara manual. Satu pengujian juga memverifikasi bahwa pengguna dinamis dibagi secara unik dan tidak mengizinkan mahasiswa atau dosen melihat cakupan yang bukan miliknya.

| Jumlah Uji | Lulus | Gagal | Galat | Status |
|---:|---:|---:|---:|---|
| 3 | 3 | 0 | 0 | SELESAI |

Angka pengujian ini tidak dimasukkan ke rekapitulasi kelompok utama Tabel 22. Berdasarkan isi pengujiannya, `test_demo_users` paling sesuai direkomendasikan sebagai pengujian tambahan atau bukti pendukung kelompok **Hak akses dan cakupan fakultas**, tetapi dipisahkan karena instruksi tugas secara khusus memerlukannya dilaporkan dalam subbagian tersendiri.

## E. Daftar Test FAIL dan ERROR

| No. | Berkas | Kelas.Metode | Kategori | Pesan Utama |
|---:|---|---|---|---|
| 1 | `test_faculty_scope.py` | `TestErpObeFacultyScope.test_models_are_consolidated_and_faculty_relations_are_consistent` | FAIL | Field `fakultas_id` tidak ditemukan pada model `erpobe.akademik.mk.cpl` |
| 2 | `test_weight_validation.py` | `TestErpObeWeightValidation.test_draft_groups_allow_incomplete_weights_and_report_totals` | FAIL | Status `complete` tidak terdapat pada hasil yang diperoleh untuk grup bobot draft |
| 3 | `test_rps_versioning.py` | `TestErpObeRpsVersioning.test_rps_can_finalize_before_offer_link` | ERROR | Finalisasi RPS ditolak karena bobot CPMK ke mata kuliah bernilai 0% |
| 4 | `test_triton_workflows.py` | `TestTritonKrsWorkflows.test_students_cannot_read_other_students_krs` | FAIL | KRS/baris komponen milik mahasiswa lain tidak tersedia pada cakupan mahasiswa yang diuji |
| 5 | `test_triton_workflows.py` | `TestTritonPublicRoutes.test_student_khs_report_template_renders` | FAIL | Tidak terdapat record `erpobe.report.khs` untuk siswa pada fixture akademik |
| 6 | `test_triton_workflows.py` | `TestTritonPublicRoutes.test_teacher_analysis_shows_cpmk_cpl_and_cohort_filters` | FAIL | Pola tampilan CPMK/CPL yang diharapkan tidak ditemukan pada respons portal analisis dosen |
| 7 | `test_triton_workflows.py` | `TestTritonPublicRoutes.test_teacher_listing_sorts_and_grade_detail_render` | FAIL | Data dosen fixture tidak tersedia pada skenario listing dan detail nilai |
| 8 | `test_academic_assistant.py` | `TestAcademicAssistantIntent.test_context_and_unknown_questions` | ERROR | `TypeError: unhashable type: 'list'` pada pemrosesan konteks intent |
| 9 | `test_academic_assistant.py` | `TestAcademicAssistantService.test_query_respects_model_access` | ERROR | Field `groups_id` tidak valid pada pembuatan `res.users` |

## F. Analisis Hasil

Kelompok **Audit**, **Impor dan ekspor**, **Antarmuka**, serta **Fixture dan perhitungan** memiliki hasil yang dapat dinilai. Kelompok audit, impor/ekspor, dan antarmuka lulus seluruhnya; kelompok fixture memiliki 10 uji fixture akademik yang lulus, sedangkan berkas alur TRITON memiliki 4 kegagalan dari 18 uji.

Kelompok **Hak akses dan cakupan fakultas** memiliki satu kegagalan pada konsistensi relasi fakultas. Kelompok **Versi RPS dan bobot** memiliki satu kegagalan pada pelaporan grup bobot draft dan satu galat pada skenario finalisasi RPS. Kelompok **Asisten akademik** memiliki dua galat dan tidak memiliki kegagalan.

Tidak ada pengujian yang berstatus `TIMEOUT` atau `TIDAK_ADA_RINGKASAN`. Hasil ini membuktikan bahwa seluruh berkas memberikan ringkasan hasil aktual pada proses yang selesai, tetapi tidak dapat digunakan untuk menyimpulkan bahwa aplikasi bebas bug.

## G. Detail Eksekusi

### G.1 Pemeriksaan Lingkungan dan Database

Perintah pembuktian lingkungan yang relevan:

```text
pwd
test -x /home/sesa/odoo-dev/odoo19/odoo-bin
test -x /home/sesa/odoo-dev/custom-odoo19/.venv/bin/python
test -d custom_module/erpobe/tests
test -d custom_module/erpobe/docs/skripsi
/home/sesa/odoo-dev/custom-odoo19/.venv/bin/python --version
/home/sesa/odoo-dev/odoo19/odoo-bin --version
psql -d postgres -Atc "SELECT datname FROM pg_database WHERE datname IN ('erpobe_final','erpobe_unittest','erpobe_unittest_copy') ORDER BY datname;"
psql -d postgres -Atc "SELECT count(*) FROM pg_stat_activity WHERE datname='erpobe_final';"
```

Sebelum pemeriksaan database, port `8069` dan `8071` tidak digunakan. `erpobe_final` ditemukan dan memiliki nol koneksi aktif. `erpobe_unittest` dan `erpobe_unittest_copy` tidak ditemukan.

### G.2 Persiapan dan Instalasi Database

Pendekatan yang digunakan adalah Pendekatan A. Instalasi dilakukan pada database baru `erpobe_unittest` dengan waktu mulai `2026-11-25 18:08:57` dan selesai `2026-11-25 18:09:43` berdasarkan log proses. Pemeriksaan pada akhir instalasi menemukan modul terpasang pada versi `19.0.2.8.0`.

Perintah aktual:

```text
timeout 1200s /home/sesa/odoo-dev/custom-odoo19/.venv/bin/python /home/sesa/odoo-dev/odoo19/odoo-bin -c /home/sesa/odoo-dev/odoo19/debian/odoo.conf --db_user=sesa -d erpobe_unittest -i erpobe --stop-after-init --without-demo=all --http-port=8071 --addons-path=/home/sesa/odoo-dev/odoo19/odoo/addons,/home/sesa/odoo-dev/odoo19/addons,/home/sesa/odoo-dev/custom-odoo19/custom_module
```

Proses instalasi dinyatakan berhasil dengan exit code `0`, hasil registri dimuat, dan modul `erpobe` terpasang pada database pengujian.

Sebelum instalasi, virtual environment juga dipulihkan menggunakan manifest dependensi Odoo:

```text
/home/sesa/odoo-dev/custom-odoo19/.venv/bin/python -m pip install -r /home/sesa/odoo-dev/odoo19/requirements.txt
/home/sesa/odoo-dev/custom-odoo19/.venv/bin/python -m pip check
```

### G.3 Perintah Pengujian Sepuluh Berkas

Semua proses menggunakan `--test-enable`, `--stop-after-init`, `--http-port=8071`, `--log-level=test`, `-u erpobe`, dan batas waktu `timeout 1200s`. Semua nilai database dan kredensial rahasia disensor.

```text
/home/sesa/odoo-dev/custom-odoo19/.venv/bin/python /home/sesa/odoo-dev/odoo19/odoo-bin -c /home/sesa/odoo-dev/odoo19/debian/odoo.conf --db_user=sesa -d erpobe_unittest -u erpobe --test-enable --test-file=/home/sesa/odoo-dev/custom-odoo19/custom_module/erpobe/tests/test_audit_log.py --stop-after-init --http-port=8071 --log-level=test --addons-path=/home/sesa/odoo-dev/odoo19/odoo/addons,/home/sesa/odoo-dev/odoo19/addons,/home/sesa/odoo-dev/custom-odoo19/custom_module
```

```text
/home/sesa/odoo-dev/custom-odoo19/.venv/bin/python /home/sesa/odoo-dev/odoo19/odoo-bin -c /home/sesa/odoo-dev/odoo19/debian/odoo.conf --db_user=sesa -d erpobe_unittest -u erpobe --test-enable --test-file=/home/sesa/odoo-dev/custom-odoo19/custom_module/erpobe/tests/test_faculty_scope.py --stop-after-init --http-port=8071 --log-level=test --addons-path=/home/sesa/odoo-dev/odoo19/odoo/addons,/home/sesa/odoo-dev/odoo19/addons,/home/sesa/odoo-dev/custom-odoo19/custom_module
```

```text
/home/sesa/odoo-dev/custom-odoo19/.venv/bin/python /home/sesa/odoo-dev/odoo19/odoo-bin -c /home/sesa/odoo-dev/odoo19/debian/odoo.conf --db_user=sesa -d erpobe_unittest -u erpobe --test-enable --test-file=/home/sesa/odoo-dev/custom-odoo19/custom_module/erpobe/tests/test_rps_versioning.py --stop-after-init --http-port=8071 --log-level=test --addons-path=/home/sesa/odoo-dev/odoo19/odoo/addons,/home/sesa/odoo-dev/odoo19/addons,/home/sesa/odoo-dev/custom-odoo19/custom_module
```

```text
/home/sesa/odoo-dev/custom-odoo19/.venv/bin/python /home/sesa/odoo-dev/odoo19/odoo-bin -c /home/sesa/odoo-dev/odoo19/debian/odoo.conf --db_user=sesa -d erpobe_unittest -u erpobe --test-enable --test-file=/home/sesa/odoo-dev/custom-odoo19/custom_module/erpobe/tests/test_weight_validation.py --stop-after-init --http-port=8071 --log-level=test --addons-path=/home/sesa/odoo-dev/odoo19/odoo/addons,/home/sesa/odoo-dev/odoo19/addons,/home/sesa/odoo-dev/custom-odoo19/custom_module
```

```text
/home/sesa/odoo-dev/custom-odoo19/.venv/bin/python /home/sesa/odoo-dev/odoo19/odoo-bin -c /home/sesa/odoo-dev/odoo19/debian/odoo.conf --db_user=sesa -d erpobe_unittest -u erpobe --test-enable --test-file=/home/sesa/odoo-dev/custom-odoo19/custom_module/erpobe/tests/test_academic_fixture.py --stop-after-init --http-port=8071 --log-level=test --addons-path=/home/sesa/odoo-dev/odoo19/odoo/addons,/home/sesa/odoo-dev/odoo19/addons,/home/sesa/odoo-dev/custom-odoo19/custom_module
```

```text
/home/sesa/odoo-dev/custom-odoo19/.venv/bin/python /home/sesa/odoo-dev/odoo19/odoo-bin -c /home/sesa/odoo-dev/odoo19/debian/odoo.conf --db_user=sesa -d erpobe_unittest -u erpobe --test-enable --test-file=/home/sesa/odoo-dev/custom-odoo19/custom_module/erpobe/tests/test_triton_workflows.py --stop-after-init --http-port=8071 --log-level=test --addons-path=/home/sesa/odoo-dev/odoo19/odoo/addons,/home/sesa/odoo-dev/odoo19/addons,/home/sesa/odoo-dev/custom-odoo19/custom_module
```

```text
/home/sesa/odoo-dev/custom-odoo19/.venv/bin/python /home/sesa/odoo-dev/odoo19/odoo-bin -c /home/sesa/odoo-dev/odoo19/debian/odoo.conf --db_user=sesa -d erpobe_unittest -u erpobe --test-enable --test-file=/home/sesa/odoo-dev/custom-odoo19/custom_module/erpobe/tests/test_import_export.py --stop-after-init --http-port=8071 --log-level=test --addons-path=/home/sesa/odoo-dev/odoo19/odoo/addons,/home/sesa/odoo-dev/odoo19/addons,/home/sesa/odoo-dev/custom-odoo19/custom_module
```

```text
/home/sesa/odoo-dev/custom-odoo19/.venv/bin/python /home/sesa/odoo-dev/odoo19/odoo-bin -c /home/sesa/odoo-dev/odoo19/debian/odoo.conf --db_user=sesa -d erpobe_unittest -u erpobe --test-enable --test-file=/home/sesa/odoo-dev/custom-odoo19/custom_module/erpobe/tests/test_ui_views.py --stop-after-init --http-port=8071 --log-level=test --addons-path=/home/sesa/odoo-dev/odoo19/odoo/addons,/home/sesa/odoo-dev/odoo19/addons,/home/sesa/odoo-dev/custom-odoo19/custom_module
```

```text
/home/sesa/odoo-dev/custom-odoo19/.venv/bin/python /home/sesa/odoo-dev/odoo19/odoo-bin -c /home/sesa/odoo-dev/odoo19/debian/odoo.conf --db_user=sesa -d erpobe_unittest -u erpobe --test-enable --test-file=/home/sesa/odoo-dev/custom-odoo19/custom_module/erpobe/tests/test_academic_assistant.py --stop-after-init --http-port=8071 --log-level=test --addons-path=/home/sesa/odoo-dev/odoo19/odoo/addons,/home/sesa/odoo-dev/odoo19/addons,/home/sesa/odoo-dev/custom-odoo19/custom_module
```

```text
/home/sesa/odoo-dev/custom-odoo19/.venv/bin/python /home/sesa/odoo-dev/odoo19/odoo-bin -c /home/sesa/odoo-dev/odoo19/debian/odoo.conf --db_user=sesa -d erpobe_unittest -u erpobe --test-enable --test-file=/home/sesa/odoo-dev/custom-odoo19/custom_module/erpobe/tests/test_demo_users.py --stop-after-init --http-port=8071 --log-level=test --addons-path=/home/sesa/odoo-dev/odoo19/odoo/addons,/home/sesa/odoo-dev/odoo19/addons,/home/sesa/odoo-dev/custom-odoo19/custom_module
```

Tidak ada perintah penghentian manual karena tidak ada proses yang mencapai batas waktu. Exit code aktual tiap berkas tercatat pada bagian awal atau akhir masing-masing log.
