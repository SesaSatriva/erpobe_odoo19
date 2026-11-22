# Daftar Akun Pengguna dan Hak Akses ERP OBE — Teknik Sipil

**Identitas Dokumen**

| Item | Nilai |
|---|---|
| Nama Dokumen | Daftar Akun Pengguna dan Hak Akses ERP OBE — Teknik Sipil |
| Versi | 1.3 |
| Tanggal Penyusunan | 2026-11-22 |
| Program Studi | Teknik Sipil |
| Kode Program Studi | SI |
| Fakultas | Fakultas Teknik |
| Status | Audit source code — tanpa akses database produksi |

## Riwayat Perubahan

| Versi | Tanggal | Keterangan |
|---|---|---|
| 1.0 | 2026-11-22 | Penyusunan awal dokumen gabungan berdasarkan audit source code. |
| 1.3 | 2026-11-22 | Pemisahan dokumen per program studi dan pemfilteran akun sesuai cakupan prodi. |

## Batas Dokumen

Dokumen ini khusus mencakup Program Studi **Teknik Sipil** pada Fakultas Teknik. Daftar akun berasal dari fixture akademik pada source code dan bukan bukti bahwa akun tersebut aktif pada database deployment. Audit tidak mengakses database produksi.

Cakupan autentikasi dan role:

- `erpobe.group_admin`: Administrator dengan cakupan prodi.
- `erpobe.group_dosen`: Dosen pada prodi yang diampu.
- `erpobe.group_mahasiswa`: Mahasiswa pada prodi terkait.
- `erpobe.group_superadmin` dan `base.group_system`: akun administratif teknis/internal, bukan akun dosen atau mahasiswa akademik.

## Akun Administrator Prodi

Seeder fixture akademik tidak otomatis membuat akun Admin Prodi untuk empat prodi fixture pada daftar ini. Akun Admin Prodi fixture dinamis hanya dibuat untuk prodi lain yang tidak memiliki kurikulum fixture.

| Role | Program Studi | Login | Password | Status pada Fixture Akademik |
|---|---|---|---|---|
| Admin Prodi fixture dinamis | Teknik Sipil | `admin.si` (dapat berakhiran `.p<ID>` jika login bentrok) | `Demo123!` | Tidak otomatis dibuat untuk prodi ini |

## Akun Dosen

Login dan password awal dosen sama dengan NIP pada fixture. Dosen lintas-prodi disertakan pada prodi yang tercantum dalam cakupan fixture-nya.

| No. | Program Studi | Login (NIP)            | Password               |
|-----|---------------|------------------------|------------------------|
| 41  | Teknik Sipil  | SIM-DOSEN-SIPIL_SIM_01 | SIM-DOSEN-SIPIL_SIM_01 |
| 42  | Teknik Sipil  | SIM-DOSEN-SIPIL_SIM_02 | SIM-DOSEN-SIPIL_SIM_02 |
| 43  | Teknik Sipil  | SIM-DOSEN-SIPIL_SIM_03 | SIM-DOSEN-SIPIL_SIM_03 |
| 44  | Teknik Sipil  | SIM-DOSEN-SIPIL_SIM_04 | SIM-DOSEN-SIPIL_SIM_04 |
| 45  | Teknik Sipil  | SIM-DOSEN-SIPIL_SIM_05 | SIM-DOSEN-SIPIL_SIM_05 |
| 46  | Teknik Sipil  | SIM-DOSEN-SIPIL_SIM_06 | SIM-DOSEN-SIPIL_SIM_06 |

**Jumlah akun dosen pada dokumen ini:** 6.

## Akun Mahasiswa

Login dan password awal mahasiswa sama dengan NIM pada fixture.

| No. | Program Studi | Login (NIM) | Password   |
|-----|---------------|-------------|------------|
| 76  | Teknik Sipil  | SIMSI22001  | SIMSI22001 |
| 77  | Teknik Sipil  | SIMSI22002  | SIMSI22002 |
| 78  | Teknik Sipil  | SIMSI22003  | SIMSI22003 |
| 79  | Teknik Sipil  | SIMSI22004  | SIMSI22004 |
| 80  | Teknik Sipil  | SIMSI22005  | SIMSI22005 |
| 81  | Teknik Sipil  | SIMSI22006  | SIMSI22006 |
| 82  | Teknik Sipil  | SIMSI22007  | SIMSI22007 |
| 83  | Teknik Sipil  | SIMSI22008  | SIMSI22008 |
| 84  | Teknik Sipil  | SIMSI22009  | SIMSI22009 |
| 85  | Teknik Sipil  | SIMSI22010  | SIMSI22010 |
| 86  | Teknik Sipil  | SIMSI22011  | SIMSI22011 |
| 87  | Teknik Sipil  | SIMSI22012  | SIMSI22012 |
| 88  | Teknik Sipil  | SIMSI22013  | SIMSI22013 |
| 89  | Teknik Sipil  | SIMSI22014  | SIMSI22014 |
| 90  | Teknik Sipil  | SIMSI22015  | SIMSI22015 |
| 91  | Teknik Sipil  | SIMSI22016  | SIMSI22016 |
| 92  | Teknik Sipil  | SIMSI22017  | SIMSI22017 |
| 93  | Teknik Sipil  | SIMSI22018  | SIMSI22018 |
| 94  | Teknik Sipil  | SIMSI22019  | SIMSI22019 |
| 95  | Teknik Sipil  | SIMSI22020  | SIMSI22020 |
| 96  | Teknik Sipil  | SIMSI22021  | SIMSI22021 |
| 97  | Teknik Sipil  | SIMSI22022  | SIMSI22022 |
| 98  | Teknik Sipil  | SIMSI22023  | SIMSI22023 |
| 99  | Teknik Sipil  | SIMSI22024  | SIMSI22024 |
| 100 | Teknik Sipil  | SIMSI22025  | SIMSI22025 |

**Jumlah akun mahasiswa pada dokumen ini:** 25.

## Matriks Hak Akses untuk Teknik Sipil

| Modul/Fitur | Administrator | Dosen | Mahasiswa |
|---|---|---|---|
| Dashboard | Tidak ada menu dashboard backend khusus. | Portal kelas/RPS/analisis/perwalian pada cakupan Teknik Sipil. | Portal ringkasan tugas dan aktivitas pada cakupan Teknik Sipil. |
| Manajemen Pengguna | R/W profil dosen/mahasiswa dalam cakupan prodi. | R profil dosen sendiri. | R profil sendiri. |
| Fakultas dan Program Studi | CRUD pada fakultas/prodi yang diizinkan; cakupan prodi wajib. | Read pada cakupan Teknik Sipil. | Read pada cakupan Teknik Sipil. |
| Data Dosen | CRUD pada cakupan yang diizinkan. | Read/Update profil dosen pada cakupan prodi. | Read terbatas. |
| Data Mahasiswa | CRUD pada cakupan yang diizinkan. | Read mahasiswa pada cakupan Teknik Sipil. | Read/Update profil sendiri. |
| Kurikulum dan Mata Kuliah | CRUD pada Teknik Sipil. | Read pada cakupan Teknik Sipil. | Read pada cakupan Teknik Sipil. |
| CPL dan CPMK | CRUD. | Read/Update sesuai ACL. | Read sesuai ACL. |
| RPS | CRUD dan finalisasi pada Teknik Sipil. | Create/Read/Update/Salin/Finalisasi mata kuliah yang diampu. | Read RPS final yang relevan. |
| Penilaian | CRUD dan kalkulasi pada Teknik Sipil. | Input nilai pada kelas yang diampu. | Read nilai dan KHS. |
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
