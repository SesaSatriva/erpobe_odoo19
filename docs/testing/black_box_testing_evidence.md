# Bukti Pelaksanaan Pengujian Black-Box

## Lingkungan Pengujian

- Sistem operasi: Linux
- Aplikasi: Odoo 19
- Modul: ERP OBE TRITON versi 19.0.2.8.0
- Database pengembangan: `erpobe`
- Port HTTP: `8069`
- Akun mahasiswa: `mhs.ti.2022.001`
- Akun dosen: `dosen.mohammad_adam_jerusalem`
- Metode: browser Playwright terhubung ke Odoo dan rangkaian test Odoo module suite

## Bukti Login Mahasiswa

Langkah:

1. Membuka `/web/login`.
2. Memasukkan login `mhs.ti.2022.001`.
3. Memasukkan password fixture `SIMIN22001`.
4. Menekan tombol Log in.

Respons aktual:

- Sistem berhasil membuka `/my/triton`.
- Judul halaman: `Beranda Portal`.
- Nama pengguna ditampilkan sebagai `Simulasi Aksa Gantara IN 001`.
- Dashboard menampilkan IPK `0.00`, SKS lulus `0`, status belum ada mata kuliah periode aktif, serta tautan akademik.

## Bukti Login Dosen

Langkah:

1. Membuka `/web/login` pada browser terpisah.
2. Memasukkan login `dosen.mohammad_adam_jerusalem`.
3. Memasukkan password fixture `SIM-DOSEN-MOHAMMAD_ADAM_JERUSALEM`.
4. Menekan tombol Log in.

Respons aktual:

- Sistem berhasil membuka `/my/triton`.
- Judul dashboard: `Beranda Portal`.
- Dosen ditampilkan sebagai `Mohammad Adam Jerusalem, S.T., S.H., M.T., Ph.D.`
- Dashboard menampilkan 16 mata kuliah diampu, 16 kelas/penawaran, 25 mahasiswa, 344 penilaian selesai, dan 0 penilaian belum lengkap.

## Bukti Portal Mahasiswa

### KRS

URL: `/my/krs`

Respons aktual:

- Judul: `Kartu Rencana Studi`.
- Status: `Disetujui`.
- Total: `19 / 24 SKS`.
- Catatan dosen wali menampilkan teks KRS simulasi dengan persetujuan otomatis untuk data uji.
- Sistem menampilkan bahwa tidak ada penawaran aktif untuk rombel.

### KHS

URL: `/my/khs`

Respons aktual:

- Judul: `Kartu Hasil Studi dan Transkrip`.
- IPK: `0.0`.
- SKS lulus: `0`.
- Ada 63 record, dengan paginasi 10 record per halaman.
- Tautan Cetak PDF tersedia pada `/report/pdf/erpobe.action_report_khs/1`.

### Mata Kuliah

URL: `/my/mata-kuliah`

Respons aktual:

- Judul: `Mata kuliah saya`.
- Sistem menampilkan 63 record.
- Contoh record menampilkan nama mata kuliah, tahun ajaran, kode mata kuliah, SKS, semester, nilai komponen, dan status `RPS Final belum tersedia`.

### Capaian CPL

URL: `/my/capaian-cpl`

Respons aktual:

- Sistem menampilkan IN-CPL-01 sampai IN-CPL-10.
- Semua CPL sampel menampilkan `0.0%`.
- Target ditampilkan `70.0%`.
- Terdapat pernyataan bahwa capaian individu merupakan data privat.

## Bukti Portal Dosen

### Dashboard

URL: `/my/triton`

Respons aktual:

- Ringkasan menampilkan 16 mata kuliah diampu.
- Ringkasan menampilkan 16 kelas/penawaran.
- Ringkasan menampilkan 25 mahasiswa terdaftar.
- Tabel daftar kelas menampilkan periode, jumlah mahasiswa, nilai lengkap, dan rata-rata.

### RPS

URL: `/my/rps`

Respons aktual:

- Sistem menampilkan 16 RPS milik penawaran dosen.
- Sampel menunjukkan status RPS `review`.
- Status bobot ditampilkan `complete`.
- Terdapat aksi `Edit RPS`, `Finalisasi`, dan `Lihat Detail`.

### Input Nilai

URL: `/my/kelas/1/nilai`

Respons aktual:

- Respons HTTP: `422 UNPROCESSABLE ENTITY`.
- Pesan: `Input nilai memerlukan RPS final dengan bobot lengkap.`
- Bukti ini mengonfirmasi bahwa backend mencegah input nilai sebelum RPS final.

## Bukti Pembatasan Lintas Role

Langkah:

1. Tetap menggunakan sesi mahasiswa `mhs.ti.2022.001`.
2. Membuka `/my/kelas`.

Respons aktual:

- Respons HTTP: `403 FORBIDDEN`.
- Pesan: `Akun ini tidak terhubung ke profil dosen.`
- Halaman mahasiswa tidak dapat mengakses fungsi dosen.

## Bukti Analitik Publik

URL: `/perbandingan-cpl`

Respons aktual:

- Halaman dapat dibuka tanpa membocorkan data mahasiswa.
- Sistem menampilkan empat prodi: Teknik Elektro, Teknik Industri, Teknik Manufaktur, dan Teknik Sipil.
- Sistem menampilkan lima kelompok CPL.
- Untuk semua prodi, data agregat dinyatakan belum tersedia.
- Nilai rata-rata capaian dan tren tidak tersedia pada periode yang dipilih.
- Metodologi menyebut bahwa CPMK dihitung dari komponen dinilai dan alokasi RPS final, sedangkan CPL memakai pemetaan CPMK–CPL serta bobot CPMK–mata kuliah pada RPS yang sama.

## Bukti Rangkaian Test Odoo

Perintah yang dijalankan:

```text
odoo-bin -d erpobe -u erpobe --test-enable --test-tags /erpobe --stop-after-init --http-port=8071 --log-level=test
```

Temuan awal:

- `TestAcademicAssistantIntent.test_context_and_unknown_questions`: ERROR.
- `TestAcademicAssistantService.test_query_respects_model_access`: ERROR.
- Tidak ada ringkasan akhir suite karena proses dihentikan setelah sekitar 33 menit karena beban regenerasi ratusan ribu record laporan pada database pengembangan.
- Karena suite dihentikan, skenario bobot, KRS, RPS, dan scope belum diberikan status PASS berdasarkan pernyataan source code saja.

## Referensi Source Code dan Data Pengujian

- Model dan view RPS: `models/akademik_rps.py`, `views/akademik_rps_views.xml`.
- Model dan view KRS: `models/akademik_krs.py`, `views/akademik_krs_views.xml`.
- Perhitungan nilai: `models/grade.py`, `models/grade_cpmk.py`, `models/grade_mk.py`, `models/grade_cpl.py`.
- RPS dan bobot: `models/weight_validation.py`, `models/weight_monitor.py`.
- Hak akses: `security/groups.xml`, `security/ir.model.access.csv`, `security/rules.xml`.
- Route mahasiswa/dosen/publik: `controllers/portal_mahasiswa.py`, `controllers/portal_dosen.py`, `controllers/perbandingan.py`, `controllers/main.py`.
- Test Odoo: `tests/test_triton_workflows.py`, `tests/test_weight_validation.py`, `tests/test_faculty_scope.py`, `tests/test_rps_versioning.py`, `tests/test_academic_assistant.py`, `tests/test_audit_log.py`.
