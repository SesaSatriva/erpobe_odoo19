# Daftar Akun Pengguna dan Hak Akses ERP OBE — Teknik Manufaktur

**Identitas Dokumen**

| Item | Nilai |
|---|---|
| Nama Dokumen | Daftar Akun Pengguna dan Hak Akses ERP OBE — Teknik Manufaktur |
| Versi | 1.4 |
| Tanggal Penyusunan | 2026-11-23 |
| Program Studi | Teknik Manufaktur |
| Kode Program Studi | MF |
| Fakultas | Fakultas Teknik |
| Status | Audit source code — tanpa akses database produksi |

## Riwayat Perubahan

| Versi | Tanggal | Keterangan |
|---|---|---|
| 1.0 | 2026-11-22 | Penyusunan awal dokumen gabungan berdasarkan audit source code. |
| 1.3 | 2026-11-22 | Pemisahan dokumen per program studi dan pemfilteran akun sesuai cakupan prodi. |
| 1.4 | 2026-11-23 | Pembuatan akun Admin Prodi otomatis saat fixture akademik dimuat. |

## Batas Dokumen

Dokumen ini khusus mencakup Program Studi **Teknik Manufaktur** pada Fakultas Teknik. Daftar akun berasal dari fixture akademik pada source code dan bukan bukti bahwa akun tersebut aktif pada database deployment. Audit tidak mengakses database produksi.

Cakupan autentikasi dan role:

- `erpobe.group_admin`: Administrator dengan cakupan prodi.
- `erpobe.group_dosen`: Dosen pada prodi yang diampu.
- `erpobe.group_mahasiswa`: Mahasiswa pada prodi terkait.
- `erpobe.group_superadmin` dan `base.group_system`: akun administratif teknis/internal, bukan akun dosen atau mahasiswa akademik.

## Akun Administrator Prodi

Seeder fixture akademik tidak otomatis membuat akun Admin Prodi untuk empat prodi fixture pada daftar ini. Akun Admin Prodi fixture dinamis hanya dibuat untuk prodi lain yang tidak memiliki kurikulum fixture.

| Role | Program Studi | Login | Password | Status pada Fixture Akademik |
|---|---|---|---|---|
| Admin Prodi fixture | Teknik Manufaktur | `admin.mf` (dapat berakhiran `.p<ID>` jika login bentrok) | `Demo123!` | Dibuat saat fixture akademik dimuat |

## Akun Dosen

Login dan password awal dosen sama dengan NIP pada fixture. Dosen lintas-prodi disertakan pada prodi yang tercantum dalam cakupan fixture-nya.

| No. | Program Studi     | Login (NIP)                            | Password                               |
|-----|-------------------|----------------------------------------|----------------------------------------|
| 27  | Teknik Manufaktur | SIM-DOSEN-DIDIK_NURHADIYANTO           | SIM-DOSEN-DIDIK_NURHADIYANTO           |
| 28  | Teknik Manufaktur | SIM-DOSEN-TIWAN                        | SIM-DOSEN-TIWAN                        |
| 29  | Teknik Manufaktur | SIM-DOSEN-MUJIYONO                     | SIM-DOSEN-MUJIYONO                     |
| 30  | Teknik Manufaktur | SIM-DOSEN-HERI_WIBOWO                  | SIM-DOSEN-HERI_WIBOWO                  |
| 31  | Teknik Manufaktur | SIM-DOSEN-ARIANTO_LEMAN                | SIM-DOSEN-ARIANTO_LEMAN                |
| 32  | Teknik Manufaktur | SIM-DOSEN-FREDY_SURAHMANTO             | SIM-DOSEN-FREDY_SURAHMANTO             |
| 33  | Teknik Manufaktur | SIM-DOSEN-APRI_NURYANTO                | SIM-DOSEN-APRI_NURYANTO                |
| 34  | Teknik Manufaktur | SIM-DOSEN-HENNY_PRATIWI                | SIM-DOSEN-HENNY_PRATIWI                |
| 35  | Teknik Manufaktur | SIM-DOSEN-MARTINUS_HERU_PALMIYANTO     | SIM-DOSEN-MARTINUS_HERU_PALMIYANTO     |
| 36  | Teknik Manufaktur | SIM-DOSEN-FEBRIANTO_AMRI_RISTADI       | SIM-DOSEN-FEBRIANTO_AMRI_RISTADI       |
| 37  | Teknik Manufaktur | SIM-DOSEN-BENI_TRI_SASONGKO            | SIM-DOSEN-BENI_TRI_SASONGKO            |
| 38  | Teknik Manufaktur | SIM-DOSEN-VIRDA_HERSY_LUTVIANA_SAPUTRI | SIM-DOSEN-VIRDA_HERSY_LUTVIANA_SAPUTRI |
| 39  | Teknik Manufaktur | SIM-DOSEN-ANDHITA_MUSTIKANINGTYAS      | SIM-DOSEN-ANDHITA_MUSTIKANINGTYAS      |
| 40  | Teknik Manufaktur | SIM-DOSEN-AULIA_MAJID                  | SIM-DOSEN-AULIA_MAJID                  |

**Jumlah akun dosen pada dokumen ini:** 14.

## Akun Mahasiswa

Login dan password awal mahasiswa sama dengan NIM pada fixture.

| No. | Program Studi     | Login (NIM) | Password   |
|-----|-------------------|-------------|------------|
| 51  | Teknik Manufaktur | SIMMF22001  | SIMMF22001 |
| 52  | Teknik Manufaktur | SIMMF22002  | SIMMF22002 |
| 53  | Teknik Manufaktur | SIMMF22003  | SIMMF22003 |
| 54  | Teknik Manufaktur | SIMMF22004  | SIMMF22004 |
| 55  | Teknik Manufaktur | SIMMF22005  | SIMMF22005 |
| 56  | Teknik Manufaktur | SIMMF22006  | SIMMF22006 |
| 57  | Teknik Manufaktur | SIMMF22007  | SIMMF22007 |
| 58  | Teknik Manufaktur | SIMMF22008  | SIMMF22008 |
| 59  | Teknik Manufaktur | SIMMF22009  | SIMMF22009 |
| 60  | Teknik Manufaktur | SIMMF22010  | SIMMF22010 |
| 61  | Teknik Manufaktur | SIMMF22011  | SIMMF22011 |
| 62  | Teknik Manufaktur | SIMMF22012  | SIMMF22012 |
| 63  | Teknik Manufaktur | SIMMF22013  | SIMMF22013 |
| 64  | Teknik Manufaktur | SIMMF22014  | SIMMF22014 |
| 65  | Teknik Manufaktur | SIMMF22015  | SIMMF22015 |
| 66  | Teknik Manufaktur | SIMMF22016  | SIMMF22016 |
| 67  | Teknik Manufaktur | SIMMF22017  | SIMMF22017 |
| 68  | Teknik Manufaktur | SIMMF22018  | SIMMF22018 |
| 69  | Teknik Manufaktur | SIMMF22019  | SIMMF22019 |
| 70  | Teknik Manufaktur | SIMMF22020  | SIMMF22020 |
| 71  | Teknik Manufaktur | SIMMF22021  | SIMMF22021 |
| 72  | Teknik Manufaktur | SIMMF22022  | SIMMF22022 |
| 73  | Teknik Manufaktur | SIMMF22023  | SIMMF22023 |
| 74  | Teknik Manufaktur | SIMMF22024  | SIMMF22024 |
| 75  | Teknik Manufaktur | SIMMF22025  | SIMMF22025 |

**Jumlah akun mahasiswa pada dokumen ini:** 25.

## Matriks Hak Akses untuk Teknik Manufaktur

| Modul/Fitur | Administrator | Dosen | Mahasiswa |
|---|---|---|---|
| Dashboard | Tidak ada menu dashboard backend khusus. | Portal kelas/RPS/analisis/perwalian pada cakupan Teknik Manufaktur. | Portal ringkasan tugas dan aktivitas pada cakupan Teknik Manufaktur. |
| Manajemen Pengguna | R/W profil dosen/mahasiswa dalam cakupan prodi. | R profil dosen sendiri. | R profil sendiri. |
| Fakultas dan Program Studi | CRUD pada fakultas/prodi yang diizinkan; cakupan prodi wajib. | Read pada cakupan Teknik Manufaktur. | Read pada cakupan Teknik Manufaktur. |
| Data Dosen | CRUD pada cakupan yang diizinkan. | Read/Update profil dosen pada cakupan prodi. | Read terbatas. |
| Data Mahasiswa | CRUD pada cakupan yang diizinkan. | Read mahasiswa pada cakupan Teknik Manufaktur. | Read/Update profil sendiri. |
| Kurikulum dan Mata Kuliah | CRUD pada Teknik Manufaktur. | Read pada cakupan Teknik Manufaktur. | Read pada cakupan Teknik Manufaktur. |
| CPL dan CPMK | CRUD. | Read/Update sesuai ACL. | Read sesuai ACL. |
| RPS | CRUD dan finalisasi pada Teknik Manufaktur. | Create/Read/Update/Salin/Finalisasi mata kuliah yang diampu. | Read RPS final yang relevan. |
| Penilaian | CRUD dan kalkulasi pada Teknik Manufaktur. | Input nilai pada kelas yang diampu. | Read nilai dan KHS. |
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
