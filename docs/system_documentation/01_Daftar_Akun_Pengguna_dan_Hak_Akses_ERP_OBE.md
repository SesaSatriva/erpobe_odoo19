# Daftar Akun Pengguna dan Hak Akses ERP OBE

**Identitas Dokumen**

| Item | Nilai |
|---|---|
| Nama Dokumen | Daftar Akun Pengguna dan Hak Akses ERP OBE |
| Versi | 1.2 |
| Tanggal Penyusunan | 2026-11-22 |
| Status | Audit source code — tanpa akses database produksi |

## Riwayat Perubahan

| Versi | Tanggal | Keterangan |
|---|---|---|
| 1.0 | 2026-11-22 | Penyusunan awal berdasarkan audit source code ERP OBE. |
| 1.1 | 2026-11-22 | Menambahkan daftar login akun fixture untuk pengujian. |
| 1.2 | 2026-11-22 | Menyajikan login dan password per akun dalam baris terpisah. |

## Daftar Isi

[Daftar isi diperbarui otomatis pada dokumen Word.]

# Pendahuluan dan Batas Audit

Dokumen ini menyusun daftar akun dan matriks hak akses ERP OBE berdasarkan implementasi source code Odoo 19. Audit tidak mengakses database `obe`, database produksi, atau database pengguna lain. Karena itu, jumlah dan identitas akun aktual hanya dapat dinyatakan apabila tersedia dalam source data fixture; akun lain yang mungkin ada di database tidak dapat dihitung atau didaftar tanpa data database yang diizinkan.

Akses autentikasi direpresentasikan oleh tiga grup utama: `erpobe.group_admin`, `erpobe.group_dosen`, dan `erpobe.group_mahasiswa`. Kelompok `erpobe.group_superadmin` dan `base.group_system` digunakan sebagai grup administratif teknis/internal, bukan role pengguna akademik tambahan; dalam dokumentasi operasional keduanya dipetakan ke Administrator.

# Audit Sumber Akun

Sumber akun yang diperiksa meliputi `_create_or_update_profile_user()` pada `models/master_user.py`, seeder fixture pada `models/fixture_seeder.py`, profil dosen/mahasiswa pada `models/master_user.py`, data XML fakultas/prodi, test akun demo, ACL, dan record rules.

Akun baru dibuat ketika profil dosen atau mahasiswa dibuat atau melalui seeder fixture. Relasi akun dilakukan melalui `res.partner` → profil dosen/mahasiswa → `res.users.partner_id`. Dosen memakai `nip` dan mahasiswa memakai `nim`; mahasiswa dan dosen juga mendapat cakupan program studi pada `res.users.erpobe_prodi_ids`.

# Daftar Akun Administrator

Seeder fixture dinamis membuat akun Admin Prodi hanya untuk prodi tanpa kurikulum fixture. Akun ini tidak otomatis dibuat untuk empat prodi fixture akademik pada daftar berikut.

| Role | Program Studi | Login | Password |
|---|---|---|---|
| Admin Prodi fixture dinamis | Sesuai prodi yang diseed | `admin.<kode-prodi>` (dapat berakhiran `.p<ID>` jika login bentrok) | `Demo123!` |

Password Admin Prodi memang tidak sama dengan login pada source fixture. Akun superadmin/administrator teknis tidak disediakan sebagai akun demo. Jangan gunakan akun fixture di produksi.

# Daftar Akun Dosen Fixture Akademik

Login dapat memakai NIP; pada fixture ini NIP juga menjadi password awal. Jadi kolom Login dan Password berisi nilai yang sama. Semua akun di bawah adalah akun fixture pengujian.

| No. | Program Studi | Login (NIP) | Password |
|---:|---|---|---|
| 1 | Teknik Industri | `SIM-DOSEN-MOHAMMAD_ADAM_JERUSALEM` | `SIM-DOSEN-MOHAMMAD_ADAM_JERUSALEM` |
| 2 | Teknik Industri | `SIM-DOSEN-NOVA_SUPARMANTO` | `SIM-DOSEN-NOVA_SUPARMANTO` |
| 3 | Teknik Industri | `SIM-DOSEN-HERI_NURDIYANTO` | `SIM-DOSEN-HERI_NURDIYANTO` |
| 4 | Teknik Industri | `SIM-DOSEN-ADHE_RIZKY_ANUGERAH` | `SIM-DOSEN-ADHE_RIZKY_ANUGERAH` |
| 5 | Teknik Industri | `SIM-DOSEN-GRAHITA_PRISCA_BRILIANTI` | `SIM-DOSEN-GRAHITA_PRISCA_BRILIANTI` |
| 6 | Teknik Industri | `SIM-DOSEN-UMMI_FAKHRIYAH_JAYATRI` | `SIM-DOSEN-UMMI_FAKHRIYAH_JAYATRI` |
| 7 | Teknik Industri | `SIM-DOSEN-DYANTIKA_PUTRY_MAHMUD` | `SIM-DOSEN-DYANTIKA_PUTRY_MAHMUD` |
| 8 | Teknik Industri | `SIM-DOSEN-ANISA_KHARISMAWATI` | `SIM-DOSEN-ANISA_KHARISMAWATI` |
| 9 | Teknik Industri | `SIM-DOSEN-PERDANA_SUTEJA_PUTRA` | `SIM-DOSEN-PERDANA_SUTEJA_PUTRA` |
| 10 | Teknik Industri | `SIM-DOSEN-BROTO_WIDYA_HARTANTO` | `SIM-DOSEN-BROTO_WIDYA_HARTANTO` |
| 11 | Teknik Industri | `SIM-DOSEN-KETUT_IMA_ISMARA` | `SIM-DOSEN-KETUT_IMA_ISMARA` |
| 12 | Teknik Industri / Teknik Elektro | `SIM-DOSEN-MUHAMAD_ALI` | `SIM-DOSEN-MUHAMAD_ALI` |
| 13 | Teknik Industri | `SIM-DOSEN-DIAN_EKSANA_WIBOWO` | `SIM-DOSEN-DIAN_EKSANA_WIBOWO` |
| 14 | Teknik Elektro | `SIM-DOSEN-MOH_KHAIRUDIN` | `SIM-DOSEN-MOH_KHAIRUDIN` |
| 15 | Teknik Elektro | `SIM-DOSEN-RUSTAM_ASNAWI` | `SIM-DOSEN-RUSTAM_ASNAWI` |
| 16 | Teknik Elektro | `SIM-DOSEN-SIGIT_YATMONO` | `SIM-DOSEN-SIGIT_YATMONO` |
| 17 | Teknik Elektro | `SIM-DOSEN-ARIADIE_CHANDRA_NUGRAHA` | `SIM-DOSEN-ARIADIE_CHANDRA_NUGRAHA` |
| 18 | Teknik Elektro | `SIM-DOSEN-DENY_BUDI_HERTANTO` | `SIM-DOSEN-DENY_BUDI_HERTANTO` |
| 19 | Teknik Elektro | `SIM-DOSEN-AJI_ERY_BURHANDENNY` | `SIM-DOSEN-AJI_ERY_BURHANDENNY` |
| 20 | Teknik Elektro | `SIM-DOSEN-SARWO_PRANOTO` | `SIM-DOSEN-SARWO_PRANOTO` |
| 21 | Teknik Elektro | `SIM-DOSEN-NURMAN_SETIAWAN` | `SIM-DOSEN-NURMAN_SETIAWAN` |
| 22 | Teknik Elektro | `SIM-DOSEN-YUDI_UTOMO_PUTRA` | `SIM-DOSEN-YUDI_UTOMO_PUTRA` |
| 23 | Teknik Elektro | `SIM-DOSEN-VANDO_GUSTI_AL_HAKIM` | `SIM-DOSEN-VANDO_GUSTI_AL_HAKIM` |
| 24 | Teknik Elektro | `SIM-DOSEN-RIZAL_PRIYAMBUDI` | `SIM-DOSEN-RIZAL_PRIYAMBUDI` |
| 25 | Teknik Elektro | `SIM-DOSEN-ARIF_NUGROHO` | `SIM-DOSEN-ARIF_NUGROHO` |
| 26 | Teknik Elektro | `SIM-DOSEN-FATCHUL_ARIFIN` | `SIM-DOSEN-FATCHUL_ARIFIN` |
| 27 | Teknik Manufaktur | `SIM-DOSEN-DIDIK_NURHADIYANTO` | `SIM-DOSEN-DIDIK_NURHADIYANTO` |
| 28 | Teknik Manufaktur | `SIM-DOSEN-TIWAN` | `SIM-DOSEN-TIWAN` |
| 29 | Teknik Manufaktur | `SIM-DOSEN-MUJIYONO` | `SIM-DOSEN-MUJIYONO` |
| 30 | Teknik Manufaktur | `SIM-DOSEN-HERI_WIBOWO` | `SIM-DOSEN-HERI_WIBOWO` |
| 31 | Teknik Manufaktur | `SIM-DOSEN-ARIANTO_LEMAN` | `SIM-DOSEN-ARIANTO_LEMAN` |
| 32 | Teknik Manufaktur | `SIM-DOSEN-FREDY_SURAHMANTO` | `SIM-DOSEN-FREDY_SURAHMANTO` |
| 33 | Teknik Manufaktur | `SIM-DOSEN-APRI_NURYANTO` | `SIM-DOSEN-APRI_NURYANTO` |
| 34 | Teknik Manufaktur | `SIM-DOSEN-HENNY_PRATIWI` | `SIM-DOSEN-HENNY_PRATIWI` |
| 35 | Teknik Manufaktur | `SIM-DOSEN-MARTINUS_HERU_PALMIYANTO` | `SIM-DOSEN-MARTINUS_HERU_PALMIYANTO` |
| 36 | Teknik Manufaktur | `SIM-DOSEN-FEBRIANTO_AMRI_RISTADI` | `SIM-DOSEN-FEBRIANTO_AMRI_RISTADI` |
| 37 | Teknik Manufaktur | `SIM-DOSEN-BENI_TRI_SASONGKO` | `SIM-DOSEN-BENI_TRI_SASONGKO` |
| 38 | Teknik Manufaktur | `SIM-DOSEN-VIRDA_HERSY_LUTVIANA_SAPUTRI` | `SIM-DOSEN-VIRDA_HERSY_LUTVIANA_SAPUTRI` |
| 39 | Teknik Manufaktur | `SIM-DOSEN-ANDHITA_MUSTIKANINGTYAS` | `SIM-DOSEN-ANDHITA_MUSTIKANINGTYAS` |
| 40 | Teknik Manufaktur | `SIM-DOSEN-AULIA_MAJID` | `SIM-DOSEN-AULIA_MAJID` |
| 41 | Teknik Sipil | `SIM-DOSEN-SIPIL_SIM_01` | `SIM-DOSEN-SIPIL_SIM_01` |
| 42 | Teknik Sipil | `SIM-DOSEN-SIPIL_SIM_02` | `SIM-DOSEN-SIPIL_SIM_02` |
| 43 | Teknik Sipil | `SIM-DOSEN-SIPIL_SIM_03` | `SIM-DOSEN-SIPIL_SIM_03` |
| 44 | Teknik Sipil | `SIM-DOSEN-SIPIL_SIM_04` | `SIM-DOSEN-SIPIL_SIM_04` |
| 45 | Teknik Sipil | `SIM-DOSEN-SIPIL_SIM_05` | `SIM-DOSEN-SIPIL_SIM_05` |
| 46 | Teknik Sipil | `SIM-DOSEN-SIPIL_SIM_06` | `SIM-DOSEN-SIPIL_SIM_06` |

# Daftar Akun Mahasiswa Fixture Akademik

Login mahasiswa dapat memakai NIM, dan pada fixture ini NIM juga menjadi password awal. Jadi kolom Login dan Password berisi nilai yang sama.

| No. | Program Studi | Login (NIM) | Password |
|---:|---|---|---|
| 1 | Teknik Industri | `SIMIN22001` | `SIMIN22001` |
| 2 | Teknik Industri | `SIMIN22002` | `SIMIN22002` |
| 3 | Teknik Industri | `SIMIN22003` | `SIMIN22003` |
| 4 | Teknik Industri | `SIMIN22004` | `SIMIN22004` |
| 5 | Teknik Industri | `SIMIN22005` | `SIMIN22005` |
| 6 | Teknik Industri | `SIMIN22006` | `SIMIN22006` |
| 7 | Teknik Industri | `SIMIN22007` | `SIMIN22007` |
| 8 | Teknik Industri | `SIMIN22008` | `SIMIN22008` |
| 9 | Teknik Industri | `SIMIN22009` | `SIMIN22009` |
| 10 | Teknik Industri | `SIMIN22010` | `SIMIN22010` |
| 11 | Teknik Industri | `SIMIN22011` | `SIMIN22011` |
| 12 | Teknik Industri | `SIMIN22012` | `SIMIN22012` |
| 13 | Teknik Industri | `SIMIN22013` | `SIMIN22013` |
| 14 | Teknik Industri | `SIMIN22014` | `SIMIN22014` |
| 15 | Teknik Industri | `SIMIN22015` | `SIMIN22015` |
| 16 | Teknik Industri | `SIMIN22016` | `SIMIN22016` |
| 17 | Teknik Industri | `SIMIN22017` | `SIMIN22017` |
| 18 | Teknik Industri | `SIMIN22018` | `SIMIN22018` |
| 19 | Teknik Industri | `SIMIN22019` | `SIMIN22019` |
| 20 | Teknik Industri | `SIMIN22020` | `SIMIN22020` |
| 21 | Teknik Industri | `SIMIN22021` | `SIMIN22021` |
| 22 | Teknik Industri | `SIMIN22022` | `SIMIN22022` |
| 23 | Teknik Industri | `SIMIN22023` | `SIMIN22023` |
| 24 | Teknik Industri | `SIMIN22024` | `SIMIN22024` |
| 25 | Teknik Industri | `SIMIN22025` | `SIMIN22025` |
| 26 | Teknik Elektro | `SIMEL22001` | `SIMEL22001` |
| 27 | Teknik Elektro | `SIMEL22002` | `SIMEL22002` |
| 28 | Teknik Elektro | `SIMEL22003` | `SIMEL22003` |
| 29 | Teknik Elektro | `SIMEL22004` | `SIMEL22004` |
| 30 | Teknik Elektro | `SIMEL22005` | `SIMEL22005` |
| 31 | Teknik Elektro | `SIMEL22006` | `SIMEL22006` |
| 32 | Teknik Elektro | `SIMEL22007` | `SIMEL22007` |
| 33 | Teknik Elektro | `SIMEL22008` | `SIMEL22008` |
| 34 | Teknik Elektro | `SIMEL22009` | `SIMEL22009` |
| 35 | Teknik Elektro | `SIMEL22010` | `SIMEL22010` |
| 36 | Teknik Elektro | `SIMEL22011` | `SIMEL22011` |
| 37 | Teknik Elektro | `SIMEL22012` | `SIMEL22012` |
| 38 | Teknik Elektro | `SIMEL22013` | `SIMEL22013` |
| 39 | Teknik Elektro | `SIMEL22014` | `SIMEL22014` |
| 40 | Teknik Elektro | `SIMEL22015` | `SIMEL22015` |
| 41 | Teknik Elektro | `SIMEL22016` | `SIMEL22016` |
| 42 | Teknik Elektro | `SIMEL22017` | `SIMEL22017` |
| 43 | Teknik Elektro | `SIMEL22018` | `SIMEL22018` |
| 44 | Teknik Elektro | `SIMEL22019` | `SIMEL22019` |
| 45 | Teknik Elektro | `SIMEL22020` | `SIMEL22020` |
| 46 | Teknik Elektro | `SIMEL22021` | `SIMEL22021` |
| 47 | Teknik Elektro | `SIMEL22022` | `SIMEL22022` |
| 48 | Teknik Elektro | `SIMEL22023` | `SIMEL22023` |
| 49 | Teknik Elektro | `SIMEL22024` | `SIMEL22024` |
| 50 | Teknik Elektro | `SIMEL22025` | `SIMEL22025` |
| 51 | Teknik Manufaktur | `SIMMF22001` | `SIMMF22001` |
| 52 | Teknik Manufaktur | `SIMMF22002` | `SIMMF22002` |
| 53 | Teknik Manufaktur | `SIMMF22003` | `SIMMF22003` |
| 54 | Teknik Manufaktur | `SIMMF22004` | `SIMMF22004` |
| 55 | Teknik Manufaktur | `SIMMF22005` | `SIMMF22005` |
| 56 | Teknik Manufaktur | `SIMMF22006` | `SIMMF22006` |
| 57 | Teknik Manufaktur | `SIMMF22007` | `SIMMF22007` |
| 58 | Teknik Manufaktur | `SIMMF22008` | `SIMMF22008` |
| 59 | Teknik Manufaktur | `SIMMF22009` | `SIMMF22009` |
| 60 | Teknik Manufaktur | `SIMMF22010` | `SIMMF22010` |
| 61 | Teknik Manufaktur | `SIMMF22011` | `SIMMF22011` |
| 62 | Teknik Manufaktur | `SIMMF22012` | `SIMMF22012` |
| 63 | Teknik Manufaktur | `SIMMF22013` | `SIMMF22013` |
| 64 | Teknik Manufaktur | `SIMMF22014` | `SIMMF22014` |
| 65 | Teknik Manufaktur | `SIMMF22015` | `SIMMF22015` |
| 66 | Teknik Manufaktur | `SIMMF22016` | `SIMMF22016` |
| 67 | Teknik Manufaktur | `SIMMF22017` | `SIMMF22017` |
| 68 | Teknik Manufaktur | `SIMMF22018` | `SIMMF22018` |
| 69 | Teknik Manufaktur | `SIMMF22019` | `SIMMF22019` |
| 70 | Teknik Manufaktur | `SIMMF22020` | `SIMMF22020` |
| 71 | Teknik Manufaktur | `SIMMF22021` | `SIMMF22021` |
| 72 | Teknik Manufaktur | `SIMMF22022` | `SIMMF22022` |
| 73 | Teknik Manufaktur | `SIMMF22023` | `SIMMF22023` |
| 74 | Teknik Manufaktur | `SIMMF22024` | `SIMMF22024` |
| 75 | Teknik Manufaktur | `SIMMF22025` | `SIMMF22025` |
| 76 | Teknik Sipil | `SIMSI22001` | `SIMSI22001` |
| 77 | Teknik Sipil | `SIMSI22002` | `SIMSI22002` |
| 78 | Teknik Sipil | `SIMSI22003` | `SIMSI22003` |
| 79 | Teknik Sipil | `SIMSI22004` | `SIMSI22004` |
| 80 | Teknik Sipil | `SIMSI22005` | `SIMSI22005` |
| 81 | Teknik Sipil | `SIMSI22006` | `SIMSI22006` |
| 82 | Teknik Sipil | `SIMSI22007` | `SIMSI22007` |
| 83 | Teknik Sipil | `SIMSI22008` | `SIMSI22008` |
| 84 | Teknik Sipil | `SIMSI22009` | `SIMSI22009` |
| 85 | Teknik Sipil | `SIMSI22010` | `SIMSI22010` |
| 86 | Teknik Sipil | `SIMSI22011` | `SIMSI22011` |
| 87 | Teknik Sipil | `SIMSI22012` | `SIMSI22012` |
| 88 | Teknik Sipil | `SIMSI22013` | `SIMSI22013` |
| 89 | Teknik Sipil | `SIMSI22014` | `SIMSI22014` |
| 90 | Teknik Sipil | `SIMSI22015` | `SIMSI22015` |
| 91 | Teknik Sipil | `SIMSI22016` | `SIMSI22016` |
| 92 | Teknik Sipil | `SIMSI22017` | `SIMSI22017` |
| 93 | Teknik Sipil | `SIMSI22018` | `SIMSI22018` |
| 94 | Teknik Sipil | `SIMSI22019` | `SIMSI22019` |
| 95 | Teknik Sipil | `SIMSI22020` | `SIMSI22020` |
| 96 | Teknik Sipil | `SIMSI22021` | `SIMSI22021` |
| 97 | Teknik Sipil | `SIMSI22022` | `SIMSI22022` |
| 98 | Teknik Sipil | `SIMSI22023` | `SIMSI22023` |
| 99 | Teknik Sipil | `SIMSI22024` | `SIMSI22024` |
| 100 | Teknik Sipil | `SIMSI22025` | `SIMSI22025` |

Jika fixture belum dijalankan, akun di atas belum tentu ada pada database. Jika login atau password pernah diubah, gunakan nilai yang tersimpan di database pengujian. Jangan gunakan akun/password fixture pada produksi.

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
| Akun dosen fixture akademik | 46 | Source seeder; bukan jumlah akun produksi |
| Akun mahasiswa fixture akademik | 100 | Source seeder; bukan jumlah akun produksi |
| Fakultas terverifikasi | 1 | Fixture XML |
| Program Studi terverifikasi | 4 | Fixture XML |
| Akun aktif/nonaktif aktual | Tidak dapat dihitung | Memerlukan data database |

Jumlah akun fixture berasal dari mekanisme seeder dan bukan bukti jumlah akun pada database deployment.

# Akun, Login, dan Keamanan

1. Untuk dosen dan mahasiswa fixture, gunakan NIP/NIM pada kolom Login; nilai yang sama dipakai sebagai password awal. Odoo juga menerima NIP/NIM melalui `res.users._get_login_domain()`.
2. Pada proses normal, login dapat berupa email. Untuk Admin Prodi fixture dinamis, gunakan login `admin.<kode-prodi>` dan password `Demo123!`.
3. Pembuatan profil normal memakai password identitas sebagai password awal (`nip` untuk dosen dan `nim` untuk mahasiswa), sedangkan admin fixture memakai `Demo123!`.
4. Hash password tidak dibongkar dan tidak dikarang.
5. Setelah login pertama, password identitas agar segera diganti dengan password kuat unik.
6. Reset password untuk akun produksi dilakukan melalui mekanisme administrasi akun Odoo, bukan dengan mengubah database atau source code.
7. Akun demo wajib dibedakan dari akun produksi dan tidak boleh digunakan sebagai kredensial operasional.

# Catatan Kelengkapan

Belum dapat diverifikasi: daftar seluruh akun aktual di database deployment, status aktif/nonaktif aktual, password yang mungkin telah diubah, akun Administrator aktual, dan identitas superadmin aktual. Daftar di atas hanya akun fixture pengujian yang ditentukan source code dan tidak membuktikan bahwa akun tersebut ada atau aktif pada database tertentu.
