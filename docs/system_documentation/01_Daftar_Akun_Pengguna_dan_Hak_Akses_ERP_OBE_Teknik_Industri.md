# Daftar Akun Pengguna dan Hak Akses ERP OBE — Teknik Industri

**Identitas Dokumen**

| Item | Nilai |
|---|---|
| Nama Dokumen | Daftar Akun Pengguna dan Hak Akses ERP OBE — Teknik Industri |
| Versi | 1.3 |
| Tanggal Penyusunan | 2026-11-22 |
| Program Studi | Teknik Industri |
| Kode Program Studi | IN |
| Fakultas | Fakultas Teknik |
| Status | Audit source code — tanpa akses database produksi |

## Riwayat Perubahan

| Versi | Tanggal | Keterangan |
|---|---|---|
| 1.0 | 2026-11-22 | Penyusunan awal dokumen gabungan berdasarkan audit source code. |
| 1.3 | 2026-11-22 | Pemisahan dokumen per program studi dan pemfilteran akun sesuai cakupan prodi. |

## Batas Dokumen

Dokumen ini khusus mencakup Program Studi **Teknik Industri** pada Fakultas Teknik. Daftar akun berasal dari fixture akademik pada source code dan bukan bukti bahwa akun tersebut aktif pada database deployment. Audit tidak mengakses database produksi.

Cakupan autentikasi dan role:

- `erpobe.group_admin`: Administrator dengan cakupan prodi.
- `erpobe.group_dosen`: Dosen pada prodi yang diampu.
- `erpobe.group_mahasiswa`: Mahasiswa pada prodi terkait.
- `erpobe.group_superadmin` dan `base.group_system`: akun administratif teknis/internal, bukan akun dosen atau mahasiswa akademik.

## Akun Administrator Prodi

Seeder fixture akademik tidak otomatis membuat akun Admin Prodi untuk empat prodi fixture pada daftar ini. Akun Admin Prodi fixture dinamis hanya dibuat untuk prodi lain yang tidak memiliki kurikulum fixture.

| Role | Program Studi | Login | Password | Status pada Fixture Akademik |
|---|---|---|---|---|
| Admin Prodi fixture dinamis | Teknik Industri | `admin.in` (dapat berakhiran `.p<ID>` jika login bentrok) | `Demo123!` | Tidak otomatis dibuat untuk prodi ini |

## Akun Dosen

Login dan password awal dosen sama dengan NIP pada fixture. Dosen lintas-prodi disertakan pada prodi yang tercantum dalam cakupan fixture-nya.

| No. | Program Studi                    | Login (NIP)                        | Password                           |
|-----|----------------------------------|------------------------------------|------------------------------------|
| 1   | Teknik Industri                  | SIM-DOSEN-MOHAMMAD_ADAM_JERUSALEM  | SIM-DOSEN-MOHAMMAD_ADAM_JERUSALEM  |
| 2   | Teknik Industri                  | SIM-DOSEN-NOVA_SUPARMANTO          | SIM-DOSEN-NOVA_SUPARMANTO          |
| 3   | Teknik Industri                  | SIM-DOSEN-HERI_NURDIYANTO          | SIM-DOSEN-HERI_NURDIYANTO          |
| 4   | Teknik Industri                  | SIM-DOSEN-ADHE_RIZKY_ANUGERAH      | SIM-DOSEN-ADHE_RIZKY_ANUGERAH      |
| 5   | Teknik Industri                  | SIM-DOSEN-GRAHITA_PRISCA_BRILIANTI | SIM-DOSEN-GRAHITA_PRISCA_BRILIANTI |
| 6   | Teknik Industri                  | SIM-DOSEN-UMMI_FAKHRIYAH_JAYATRI   | SIM-DOSEN-UMMI_FAKHRIYAH_JAYATRI   |
| 7   | Teknik Industri                  | SIM-DOSEN-DYANTIKA_PUTRY_MAHMUD    | SIM-DOSEN-DYANTIKA_PUTRY_MAHMUD    |
| 8   | Teknik Industri                  | SIM-DOSEN-ANISA_KHARISMAWATI       | SIM-DOSEN-ANISA_KHARISMAWATI       |
| 9   | Teknik Industri                  | SIM-DOSEN-PERDANA_SUTEJA_PUTRA     | SIM-DOSEN-PERDANA_SUTEJA_PUTRA     |
| 10  | Teknik Industri                  | SIM-DOSEN-BROTO_WIDYA_HARTANTO     | SIM-DOSEN-BROTO_WIDYA_HARTANTO     |
| 11  | Teknik Industri                  | SIM-DOSEN-KETUT_IMA_ISMARA         | SIM-DOSEN-KETUT_IMA_ISMARA         |
| 12  | Teknik Industri / Teknik Elektro | SIM-DOSEN-MUHAMAD_ALI              | SIM-DOSEN-MUHAMAD_ALI              |
| 13  | Teknik Industri                  | SIM-DOSEN-DIAN_EKSANA_WIBOWO       | SIM-DOSEN-DIAN_EKSANA_WIBOWO       |

**Jumlah akun dosen pada dokumen ini:** 13.

## Akun Mahasiswa

Login dan password awal mahasiswa sama dengan NIM pada fixture.

| No. | Program Studi   | Login (NIM) | Password   |
|-----|-----------------|-------------|------------|
| 1   | Teknik Industri | SIMIN22001  | SIMIN22001 |
| 2   | Teknik Industri | SIMIN22002  | SIMIN22002 |
| 3   | Teknik Industri | SIMIN22003  | SIMIN22003 |
| 4   | Teknik Industri | SIMIN22004  | SIMIN22004 |
| 5   | Teknik Industri | SIMIN22005  | SIMIN22005 |
| 6   | Teknik Industri | SIMIN22006  | SIMIN22006 |
| 7   | Teknik Industri | SIMIN22007  | SIMIN22007 |
| 8   | Teknik Industri | SIMIN22008  | SIMIN22008 |
| 9   | Teknik Industri | SIMIN22009  | SIMIN22009 |
| 10  | Teknik Industri | SIMIN22010  | SIMIN22010 |
| 11  | Teknik Industri | SIMIN22011  | SIMIN22011 |
| 12  | Teknik Industri | SIMIN22012  | SIMIN22012 |
| 13  | Teknik Industri | SIMIN22013  | SIMIN22013 |
| 14  | Teknik Industri | SIMIN22014  | SIMIN22014 |
| 15  | Teknik Industri | SIMIN22015  | SIMIN22015 |
| 16  | Teknik Industri | SIMIN22016  | SIMIN22016 |
| 17  | Teknik Industri | SIMIN22017  | SIMIN22017 |
| 18  | Teknik Industri | SIMIN22018  | SIMIN22018 |
| 19  | Teknik Industri | SIMIN22019  | SIMIN22019 |
| 20  | Teknik Industri | SIMIN22020  | SIMIN22020 |
| 21  | Teknik Industri | SIMIN22021  | SIMIN22021 |
| 22  | Teknik Industri | SIMIN22022  | SIMIN22022 |
| 23  | Teknik Industri | SIMIN22023  | SIMIN22023 |
| 24  | Teknik Industri | SIMIN22024  | SIMIN22024 |
| 25  | Teknik Industri | SIMIN22025  | SIMIN22025 |

**Jumlah akun mahasiswa pada dokumen ini:** 25.

## Matriks Hak Akses untuk Teknik Industri

| Modul/Fitur | Administrator | Dosen | Mahasiswa |
|---|---|---|---|
| Dashboard | Tidak ada menu dashboard backend khusus. | Portal kelas/RPS/analisis/perwalian pada cakupan Teknik Industri. | Portal ringkasan tugas dan aktivitas pada cakupan Teknik Industri. |
| Manajemen Pengguna | R/W profil dosen/mahasiswa dalam cakupan prodi. | R profil dosen sendiri. | R profil sendiri. |
| Fakultas dan Program Studi | CRUD pada fakultas/prodi yang diizinkan; cakupan prodi wajib. | Read pada cakupan Teknik Industri. | Read pada cakupan Teknik Industri. |
| Data Dosen | CRUD pada cakupan yang diizinkan. | Read/Update profil dosen pada cakupan prodi. | Read terbatas. |
| Data Mahasiswa | CRUD pada cakupan yang diizinkan. | Read mahasiswa pada cakupan Teknik Industri. | Read/Update profil sendiri. |
| Kurikulum dan Mata Kuliah | CRUD pada Teknik Industri. | Read pada cakupan Teknik Industri. | Read pada cakupan Teknik Industri. |
| CPL dan CPMK | CRUD. | Read/Update sesuai ACL. | Read sesuai ACL. |
| RPS | CRUD dan finalisasi pada Teknik Industri. | Create/Read/Update/Salin/Finalisasi mata kuliah yang diampu. | Read RPS final yang relevan. |
| Penilaian | CRUD dan kalkulasi pada Teknik Industri. | Input nilai pada kelas yang diampu. | Read nilai dan KHS. |
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
