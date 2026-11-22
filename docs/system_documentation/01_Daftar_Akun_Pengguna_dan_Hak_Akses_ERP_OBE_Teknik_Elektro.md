# Daftar Akun Pengguna dan Hak Akses ERP OBE — Teknik Elektro

**Identitas Dokumen**

| Item | Nilai |
|---|---|
| Nama Dokumen | Daftar Akun Pengguna dan Hak Akses ERP OBE — Teknik Elektro |
| Versi | 1.3 |
| Tanggal Penyusunan | 2026-11-22 |
| Program Studi | Teknik Elektro |
| Kode Program Studi | EL |
| Fakultas | Fakultas Teknik |
| Status | Audit source code — tanpa akses database produksi |

## Riwayat Perubahan

| Versi | Tanggal | Keterangan |
|---|---|---|
| 1.0 | 2026-11-22 | Penyusunan awal dokumen gabungan berdasarkan audit source code. |
| 1.3 | 2026-11-22 | Pemisahan dokumen per program studi dan pemfilteran akun sesuai cakupan prodi. |

## Batas Dokumen

Dokumen ini khusus mencakup Program Studi **Teknik Elektro** pada Fakultas Teknik. Daftar akun berasal dari fixture akademik pada source code dan bukan bukti bahwa akun tersebut aktif pada database deployment. Audit tidak mengakses database produksi.

Cakupan autentikasi dan role:

- `erpobe.group_admin`: Administrator dengan cakupan prodi.
- `erpobe.group_dosen`: Dosen pada prodi yang diampu.
- `erpobe.group_mahasiswa`: Mahasiswa pada prodi terkait.
- `erpobe.group_superadmin` dan `base.group_system`: akun administratif teknis/internal, bukan akun dosen atau mahasiswa akademik.

## Akun Administrator Prodi

Seeder fixture akademik tidak otomatis membuat akun Admin Prodi untuk empat prodi fixture pada daftar ini. Akun Admin Prodi fixture dinamis hanya dibuat untuk prodi lain yang tidak memiliki kurikulum fixture.

| Role | Program Studi | Login | Password | Status pada Fixture Akademik |
|---|---|---|---|---|
| Admin Prodi fixture dinamis | Teknik Elektro | `admin.el` (dapat berakhiran `.p<ID>` jika login bentrok) | `Demo123!` | Tidak otomatis dibuat untuk prodi ini |

## Akun Dosen

Login dan password awal dosen sama dengan NIP pada fixture. Dosen lintas-prodi disertakan pada prodi yang tercantum dalam cakupan fixture-nya.

| No. | Program Studi                    | Login (NIP)                       | Password                          |
|-----|----------------------------------|-----------------------------------|-----------------------------------|
| 12  | Teknik Industri / Teknik Elektro | SIM-DOSEN-MUHAMAD_ALI             | SIM-DOSEN-MUHAMAD_ALI             |
| 14  | Teknik Elektro                   | SIM-DOSEN-MOH_KHAIRUDIN           | SIM-DOSEN-MOH_KHAIRUDIN           |
| 15  | Teknik Elektro                   | SIM-DOSEN-RUSTAM_ASNAWI           | SIM-DOSEN-RUSTAM_ASNAWI           |
| 16  | Teknik Elektro                   | SIM-DOSEN-SIGIT_YATMONO           | SIM-DOSEN-SIGIT_YATMONO           |
| 17  | Teknik Elektro                   | SIM-DOSEN-ARIADIE_CHANDRA_NUGRAHA | SIM-DOSEN-ARIADIE_CHANDRA_NUGRAHA |
| 18  | Teknik Elektro                   | SIM-DOSEN-DENY_BUDI_HERTANTO      | SIM-DOSEN-DENY_BUDI_HERTANTO      |
| 19  | Teknik Elektro                   | SIM-DOSEN-AJI_ERY_BURHANDENNY     | SIM-DOSEN-AJI_ERY_BURHANDENNY     |
| 20  | Teknik Elektro                   | SIM-DOSEN-SARWO_PRANOTO           | SIM-DOSEN-SARWO_PRANOTO           |
| 21  | Teknik Elektro                   | SIM-DOSEN-NURMAN_SETIAWAN         | SIM-DOSEN-NURMAN_SETIAWAN         |
| 22  | Teknik Elektro                   | SIM-DOSEN-YUDI_UTOMO_PUTRA        | SIM-DOSEN-YUDI_UTOMO_PUTRA        |
| 23  | Teknik Elektro                   | SIM-DOSEN-VANDO_GUSTI_AL_HAKIM    | SIM-DOSEN-VANDO_GUSTI_AL_HAKIM    |
| 24  | Teknik Elektro                   | SIM-DOSEN-RIZAL_PRIYAMBUDI        | SIM-DOSEN-RIZAL_PRIYAMBUDI        |
| 25  | Teknik Elektro                   | SIM-DOSEN-ARIF_NUGROHO            | SIM-DOSEN-ARIF_NUGROHO            |
| 26  | Teknik Elektro                   | SIM-DOSEN-FATCHUL_ARIFIN          | SIM-DOSEN-FATCHUL_ARIFIN          |

**Jumlah akun dosen pada dokumen ini:** 14.

## Akun Mahasiswa

Login dan password awal mahasiswa sama dengan NIM pada fixture.

| No. | Program Studi  | Login (NIM) | Password   |
|-----|----------------|-------------|------------|
| 26  | Teknik Elektro | SIMEL22001  | SIMEL22001 |
| 27  | Teknik Elektro | SIMEL22002  | SIMEL22002 |
| 28  | Teknik Elektro | SIMEL22003  | SIMEL22003 |
| 29  | Teknik Elektro | SIMEL22004  | SIMEL22004 |
| 30  | Teknik Elektro | SIMEL22005  | SIMEL22005 |
| 31  | Teknik Elektro | SIMEL22006  | SIMEL22006 |
| 32  | Teknik Elektro | SIMEL22007  | SIMEL22007 |
| 33  | Teknik Elektro | SIMEL22008  | SIMEL22008 |
| 34  | Teknik Elektro | SIMEL22009  | SIMEL22009 |
| 35  | Teknik Elektro | SIMEL22010  | SIMEL22010 |
| 36  | Teknik Elektro | SIMEL22011  | SIMEL22011 |
| 37  | Teknik Elektro | SIMEL22012  | SIMEL22012 |
| 38  | Teknik Elektro | SIMEL22013  | SIMEL22013 |
| 39  | Teknik Elektro | SIMEL22014  | SIMEL22014 |
| 40  | Teknik Elektro | SIMEL22015  | SIMEL22015 |
| 41  | Teknik Elektro | SIMEL22016  | SIMEL22016 |
| 42  | Teknik Elektro | SIMEL22017  | SIMEL22017 |
| 43  | Teknik Elektro | SIMEL22018  | SIMEL22018 |
| 44  | Teknik Elektro | SIMEL22019  | SIMEL22019 |
| 45  | Teknik Elektro | SIMEL22020  | SIMEL22020 |
| 46  | Teknik Elektro | SIMEL22021  | SIMEL22021 |
| 47  | Teknik Elektro | SIMEL22022  | SIMEL22022 |
| 48  | Teknik Elektro | SIMEL22023  | SIMEL22023 |
| 49  | Teknik Elektro | SIMEL22024  | SIMEL22024 |
| 50  | Teknik Elektro | SIMEL22025  | SIMEL22025 |

**Jumlah akun mahasiswa pada dokumen ini:** 25.

## Matriks Hak Akses untuk Teknik Elektro

| Modul/Fitur | Administrator | Dosen | Mahasiswa |
|---|---|---|---|
| Dashboard | Tidak ada menu dashboard backend khusus. | Portal kelas/RPS/analisis/perwalian pada cakupan Teknik Elektro. | Portal ringkasan tugas dan aktivitas pada cakupan Teknik Elektro. |
| Manajemen Pengguna | R/W profil dosen/mahasiswa dalam cakupan prodi. | R profil dosen sendiri. | R profil sendiri. |
| Fakultas dan Program Studi | CRUD pada fakultas/prodi yang diizinkan; cakupan prodi wajib. | Read pada cakupan Teknik Elektro. | Read pada cakupan Teknik Elektro. |
| Data Dosen | CRUD pada cakupan yang diizinkan. | Read/Update profil dosen pada cakupan prodi. | Read terbatas. |
| Data Mahasiswa | CRUD pada cakupan yang diizinkan. | Read mahasiswa pada cakupan Teknik Elektro. | Read/Update profil sendiri. |
| Kurikulum dan Mata Kuliah | CRUD pada Teknik Elektro. | Read pada cakupan Teknik Elektro. | Read pada cakupan Teknik Elektro. |
| CPL dan CPMK | CRUD. | Read/Update sesuai ACL. | Read sesuai ACL. |
| RPS | CRUD dan finalisasi pada Teknik Elektro. | Create/Read/Update/Salin/Finalisasi mata kuliah yang diampu. | Read RPS final yang relevan. |
| Penilaian | CRUD dan kalkulasi pada Teknik Elektro. | Input nilai pada kelas yang diampu. | Read nilai dan KHS. |
| Analisis Capaian | Read/kelola analisis. | Read portal analisis pada cakupan. | Read CPL sendiri. |
| Laporan | Read laporan backend/KHS. | Read laporan/analisis portal. | Read KHS dan CPL portal. |
| Portal Akademik | Akses bila grup Administrator berlaku. | Kelas, RPS, nilai, perwalian, dan analisis. | KRS, mata kuliah, RPS, KHS, CPL, dan profil. |

## Keamanan dan Penggunaan Kredensial

1. Gunakan login dan password fixture hanya pada lingkungan pengujian.
2. Setelah login pertama, password identitas wajib diganti dengan password kuat dan unik.
3. Jangan menulis kredensial produksi di source code atau fixture.
4. Login dapat berupa email atau identitas akademik sesuai konfigurasi Odoo.
5. Reset password akun produksi dilakukan melalui mekanisme administrasi akun Odoo.
6. Jika fixture belum dijalankan atau login/password pernah diubah, gunakan nilai pada database pengujian yang sah.

## Catatan Kelengkapan

Belum dapat diverifikasi: akun aktual pada database deployment, status aktif/nonaktif, password yang telah diubah, akun Administrator aktual, dan identitas superadmin aktual. Daftar dosen dan mahasiswa pada dokumen ini berasal dari fixture source code dan tidak membuktikan bahwa akun tersebut ada pada database tertentu.
