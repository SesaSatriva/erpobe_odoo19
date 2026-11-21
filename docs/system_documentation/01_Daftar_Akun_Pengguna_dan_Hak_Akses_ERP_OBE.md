# Daftar Akun Pengguna dan Hak Akses ERP OBE

**Identitas Dokumen**

| Item | Nilai |
|---|---|
| Nama Dokumen | Daftar Akun Pengguna dan Hak Akses ERP OBE |
| Versi | 1.0 |
| Tanggal Penyusunan | 2026-11-22 |
| Status | Audit source code — tanpa akses database produksi |

## Riwayat Perubahan

| Versi | Tanggal | Keterangan |
|---|---|---|
| 1.0 | 2026-11-22 | Penyusunan awal berdasarkan audit source code ERP OBE. |

## Daftar Isi

[Daftar isi diperbarui otomatis pada dokumen Word.]

# Pendahuluan dan Batas Audit

Dokumen ini menyusun daftar akun dan matriks hak akses ERP OBE berdasarkan implementasi source code Odoo 19. Audit tidak mengakses database `obe`, database produksi, atau database pengguna lain. Karena itu, jumlah dan identitas akun aktual hanya dapat dinyatakan apabila tersedia dalam source data fixture; akun lain yang mungkin ada di database tidak dapat dihitung atau didaftar tanpa data database yang diizinkan.

Akses autentikasi direpresentasikan oleh tiga grup utama: `erpobe.group_admin`, `erpobe.group_dosen`, dan `erpobe.group_mahasiswa`. Kelompok `erpobe.group_superadmin` dan `base.group_system` digunakan sebagai grup administratif teknis/internal, bukan role pengguna akademik tambahan; dalam dokumentasi operasional keduanya dipetakan ke Administrator.

# Audit Sumber Akun

Sumber akun yang diperiksa meliputi `_create_or_update_profile_user()` pada `models/master_user.py`, seeder fixture pada `models/fixture_seeder.py`, profil dosen/mahasiswa pada `models/master_user.py`, data XML fakultas/prodi, test akun demo, ACL, dan record rules.

Akun baru dibuat ketika profil dosen atau mahasiswa dibuat atau melalui seeder fixture. Relasi akun dilakukan melalui `res.partner` → profil dosen/mahasiswa → `res.users.partner_id`. Dosen memakai `nip` dan mahasiswa memakai `nim`; mahasiswa dan dosen juga mendapat cakupan program studi pada `res.users.erpobe_prodi_ids`.

# Akuntansi Administrator

| No | Nama | Username/Login | Email | Role | Status | Keterangan |
|---|---|---|---|---|---|---|
| — | Akun Admin Prodi fixture | Berpola `admin.<kode-prodi>`, misalnya `admin.du.p` pada pengujian | Berpasangan `login@example.test` | Administrator | Aktif pada fixture yang dijalankan | Satu akun admin per prodi fixture; password awal fixture `Demo123!`; data aktual belum dapat diverifikasi tanpa database |
| — | Akun superadmin/administrator teknis | Tidak diambil dari database | Tidak ditampilkan | Administrator | Belum dapat diverifikasi | Bukan role tambahan dalam dokumen; grup teknis `base.group_system`/`group_superadmin` dipetakan ke Administrator |

**Password awal:** password fixture Admin adalah `Demo123!` dan benar-benar tersedia pada kode source seeder. Password tersebut harus dianggap password demo bersama dan diganti sebelum digunakan di lingkungan produksi. Bukan produksi.

# Akuntansi Dosen

Tidak dapat menyusun tabel nama dosen aktual tanpa data database atau fixture individu yang lengkap. Mekanisme fixture target membuat tiga dosen aktif per prodi, dengan login `dosen.<kode-prodi>.<nomor>` dan password awal sama dengan nilai `nip` dosen. Contoh format login berasal dari pengujian; nama, NIP/NIDN, fakultas, dan prodi aktual database tidak boleh dikarang.

# Akuntansi Mahasiswa

Tidak dapat menyusun tabel nama mahasiswa aktual tanpa data database atau fixture individu yang lengkap. Mekanisme fixture target membuat dua puluh mahasiswa aktif per prodi, dengan login `mahasiswa.<kode-prodi>.<nomor>`, password awal sama dengan `nim`, dan email `login@example.test`. Kelas/rombel dan angkatan berasal dari data profil/rombel; nilai aktual tidak tersedia dari audit source.

# Data Fakuitas dan Program Studi yang Terverifikasi

| Fakultas | Kode | Program Studi | Kode |
|---|---|---|---|
| Fakultas Teknik | FT | Teknik Industri | IN |
| Fakultas Teknik | FT | Teknik Sipil | SI |
| Fakultas Teknik | FT | Teknik Manufaktur | MF |
| Fakultas Teknik | FT | Teknik Elektro | EL |

Angka prodi di atas berasal dari `data/fixture_01_fakultas_prodi.xml`. Mahasiswa/dosen aktual tidak dihitung karena database tidak diakses.

# Matriks Hak Akses

| Modul/Fitur | Administrator | Dosen | Mahasiswa |
|---|---|---|---|
| Dashboard | Tidak ada menu dashboard backend khusus pada menus.xml. | Portal RPS/kelas/analisis/perwalian. | Portal ringkasan tugas dan aktivitas. |
| Manajemen Pengguna | R/W: profil dosen/mahasiswa melalui aplikasi; Superadmin administratif | R: profil dosen sendiri | R: profil sendiri |
| Fakultas dan Program Studi | Create/Read/Update/Delete sesuai ACL; cakupan prodi untuk Admin | Read pada cakupan prodi | Read pada cakupan prodi |
| Data Dosen | CRUD | Read/Update pada profil dosen dan cakupan prodi | Read terbatas |
| Data Mahasiswa | CRUD | Read pada cakupan prodi; Mahasiswa di menu backend tidak dapat dipilih secara umum | Read/Update terbatas pada profil sendiri |
| Kurikulum | CRUD | Read pada cakupan prodi | Read pada cakupan prodi |
| Mata Kuliah | CRUD | Read pada cakupan prodi | Read pada cakupan prodi |
| CPL | CRUD | Read/Update sesuai ACL | Read sesuai ACL |
| CPMK | CRUD | Read/Update sesuai ACL | Read sesuai ACL |
| RPS | CRUD/Finalisasi | Create/Read/Update/Salin/Finalisasi hanya mata kuliah yang diampu | Read RPS final yang relevan |
| Penilaian | CRUD dan kalkulasi | Input nilai aktual pada kelas yang diampu | Read nilai/KHS |
| Analisis Capaian | Read/kelola analisis | Read portal analisis sesuai cakupan | Read CPL sendiri |
| Laporan | Read laporan backend/KHS | Read laporan/analisis portal | Read KHS dan CPL portal |
| Portal Akademik | Dapat masuk sebagai pengguna internal bila grup berlaku | Kelas, RPS, nilai, perwalian, analisis | KRS, mata kuliah, RPS, KHS, CPL, profil |

# Ringkasan Statistik

| Indikator | Nilai | Status |
|---|---|---|
| Administrator aktual | Tidak dapat dihitung | Memerlukan data database |
| Dosen aktual | Tidak dapat dihitung | Memerlukan data database |
| Mahasiswa aktual | Tidak dapat dihitung | Memerlukan data database |
| Fakultas terverifikasi | 1 | Fixture XML |
| Program Studi terverifikasi | 4 | Fixture XML |
| Target dosen fixture per prodi | 3 | Seeding source/test |
| Target mahasiswa fixture per prodi | 20 | Seeding source/test |
| Akun aktif/nonaktif aktual | Tidak dapat dihitung | Memerlukan data database |

Jumlah target seeder bersifat mekanisme pengujian dan bukan bukti jumlah akun pada database deployment.

# Akun, Login, dan Keamanan

1. Login dosen dapat berupa email pada proses normal, atau email lokal saat fixture. Login dapat juga berupa NIP melalui `res.users._get_login_domain()`.
2. Login mahasiswa dapat berupa email atau NIM.
3. Pembuatan profil normal memakai password identitas sebagai password awal (`nip` untuk dosen dan `nim` untuk mahasiswa), sedangkan admin fixture memakai `Demo123!`.
4. Hash password tidak dibongkar dan tidak dikarang.
5. Setelah login pertama, password identitas agar segera diganti dengan password kuat unik.
6. Reset password untuk akun produksi dilakukan melalui mekanisme administrasi akun Odoo, bukan dengan mengubah database atau source code.
7. Akun demo wajib dibedakan dari akun produksi dan tidak boleh digunakan sebagai kredensial operasional.

# Catatan Kelengkapan

Belum dapat diverifikasi: daftar seluruh akun aktual, status aktif/nonaktif aktual, nama dosen/mahasiswa aktual, email aktual, password produksi, grafik distribusi pengguna, dan identitas superadmin aktual. Catatan ini harus diganti setelah pemeriksaan database pengujian yang memiliki izin.
