# Audit UX dan CRUD Global ERP OBE

## Cakupan dan batas audit

Audit statis ini mencakup addon `erpobe`: controller portal/publik, menu, action,
view backend, model, ACL, dan record rule. Inventaris 100 view backend dirinci
di [ERP_OBE_BACKEND_UI_AUDIT.md](./ERP_OBE_BACKEND_UI_AUDIT.md). Addon ini
merupakan satu aplikasi ERP dalam workspace, bukan kumpulan beberapa addon
terpisah. Status di bawah membedakan implementasi yang terlihat pada source dari
pengujian runtime.

CLI Odoo 19 tersedia, tetapi addon belum di-upgrade pada database dalam pekerjaan
ini. Browser hanya mencapai database selector; tidak ada autentikasi pengujian
atau upgrade modul yang dijalankan. Karena itu semua hasil perilaku setelah
perubahan berstatus **NOT TESTED**. Status `PARTIAL` bukan klaim bahwa seluruh
standar global sudah terpenuhi.

## Perubahan fondasional pada daftar

- Shared helper portal memakai query ORM dengan `search_count`, `limit`, `offset`,
  allowlist sort, pencarian terbatas pada field yang ditentukan route, dan
  parameter filter/search/sort/page-size yang dibawa dalam URL.
- Ukuran halaman portal dan pencarian publik: default 10, pilihan 10/25/50/100.
- Daftar yang memakai helper: penilaian kelas, riwayat nilai, kelas dosen, RPS
  dosen, perwalian, analisis kelas, KHS, mata kuliah mahasiswa, CPL pribadi,
  fakultas publik, dan tab dosen/mahasiswa/CPL/mata kuliah pada detail prodi.
- Pencarian publik lintas kategori kini menghitung total seluruh kategori
  sebelum membatasi hasil halaman dan mendukung pencarian kode/NIM/NIP yang
  relevan.
- KRS mahasiswa tidak dipaginasi pada form pemilihan mata kuliah. Form saat ini
  mengganti seluruh pilihan dari payload, sehingga memaginasi checkbox tanpa
  mekanisme penyimpanan pilihan lintas halaman berisiko menghapus pilihan yang
  tidak sedang terlihat.
- Backend memakai pager server-side Odoo. Patch khusus model `erpobe.*`
  menetapkan default 10 dan menambahkan pilihan 10/25/50/100; persistensi pilihan
  ukuran melalui URL backend belum diverifikasi/diimplementasikan.

## Matriks audit modul

| Modul/entitas | Halaman list | Pagination | Search/filter/sort | Detail | Create/edit | Delete/archive | Export/print | Hak akses (statis) | Status implementasi | Hasil pengujian |
|---|---|---|---|---|---|---|---|---|---|---|
| Fakultas | Backend `Fakultas`; publik `/fakultas` | Publik 10/25/50/100 server-side; backend belum diverifikasi | Publik search nama/kode dan sort; backend search view belum runtime-tested | Backend form; publik `/fakultas/<id>` | Backend form | Ada status aktif; relasi/guard hapus belum diaudit lengkap | Tidak ditemukan pada halaman daftar | Menu backend admin/superadmin; publik hanya data aktif | PARTIAL | NOT TESTED |
| Program studi | Backend `Program Studi`; tab prodi publik | Tab publik 10/25/50/100; backend belum diverifikasi | Tab publik search, filter mahasiswa, sort; backend belum diverifikasi | `/prodi/<id>` bertab | Backend form | Ada status aktif; dampak relasi perlu audit runtime | Tidak ditemukan | Backend admin/superadmin; publik filter data orang memakai opt-in | PARTIAL | NOT TESTED |
| Mahasiswa | Backend `Mahasiswa`; hasil pencarian/tab publik | Pagination publik hanya pada daftar publik; backend belum diverifikasi | Publik dibatasi status/visibilitas dan pencarian; backend belum diverifikasi | Backend form, profil portal `/my/profil`, profil publik opt-in | Backend dan profil portal terbatas | Field aktif tersedia; kebijakan arsip/hapus belum dipastikan | Tidak ada export pada profil | Portal controller mengikat profil ke user; ACL/rules ada tetapi uji silang belum dilakukan | PARTIAL | NOT TESTED |
| Dosen | Backend `Dosen`; hasil pencarian/tab publik | Pagination publik hanya pada daftar publik; backend belum diverifikasi | Publik dibatasi visibilitas, search, dan sort; backend belum diverifikasi | Backend form, profil publik opt-in | Backend; profil portal hanya data profil | Field aktif tersedia; kebijakan arsip/hapus belum dipastikan | Tidak ditemukan | Portal dosen dibatasi assignment pada route kelas/RPS; perlu uji lintas dosen | PARTIAL | NOT TESTED |
| Mata kuliah | Backend `Mata Kuliah`; pencarian publik | Backend belum diverifikasi; pencarian publik masuk pagination lintas kategori | Search publik nama/kode; filter/sort backend belum diverifikasi | Backend form; info course juga tampil di portal mahasiswa | Backend form | Relasi kurikulum/penawaran menuntut validasi; aturan delete belum diaudit | RPS dapat dicetak dari portal dosen | Menu master admin/superadmin; relasi prodi tersedia | PARTIAL | NOT TESTED |
| CPL | Backend `CPL`; tab prodi publik; CPL pribadi mahasiswa | Tab prodi dan CPL pribadi memakai 10/25/50/100; backend belum diverifikasi | Search/sort pada daftar custom; backend belum diverifikasi | Backend form; agregat/portal mahasiswa | Backend form | Riwayat hasil terkait; kebijakan arsip belum diverifikasi | Ekspor perbandingan CPL CSV (agregat) | Data portal mahasiswa difilter ke pemilik akun; akses backend perlu uji | PARTIAL | NOT TESTED |
| CPMK | Backend `CPMK`; hasil OBE | Backend menggunakan agregat komponen; daftar hasil portal mahasiswa perlu verifikasi | Search/filter native backend perlu runtime-test | Backend form; CPMK tampil pada RPS/nilai | Backend form | Terikat pada RPS dan grade; aturan hapus perlu validasi relasi | Laporan akademik terkait tersedia; detail export belum diaudit | Group/menu dan ACL tersedia; uji lintas prodi belum dilakukan | PARTIAL | NOT TESTED |
| Kurikulum dan RPS | Backend `Kurikulum`, `RPS`; portal `/my/rps` | Portal RPS memakai pagination; backend belum diverifikasi | Portal search/sort/status; backend search belum runtime-tested | Backend form; portal edit RPS dan laporan RPS | Admin backend; dosen hanya penawaran yang ditugaskan | Lock RPS final ada; arsip dan relasi hapus belum diuji | Cetak PDF RPS | Route portal memvalidasi kepemilikan penawaran; record rules perlu uji | PARTIAL | NOT TESTED |
| Komponen penilaian | Backend `Komponen Penilaian`; detail komponen pada input nilai | Backend belum diverifikasi | Search/filter backend belum runtime-tested | Backend form; relasi snapshot RPS tampil pada input nilai | Backend form; perubahan bobot melalui RPS | Snapshot RPS dan nilai akademik terkait; delete belum diaudit | Tidak ditemukan untuk daftar komponen | ACL per grup tercatat, belum diverifikasi end-to-end | PARTIAL | NOT TESTED |
| Penilaian/nilai | Backend `Input Nilai`, grade/analitik; portal `/my/kelas/<id>/nilai` dan `/my/riwayat-nilai` | Portal nilai/history server-side 10/25/50/100 | Penilaian search NIM/nama, sort, filter kelengkapan; history search/sort | Detail nilai menampilkan mahasiswa, kelas/periode, komponen/bobot, CPMK, status, hasil jika tersimpan | Portal dosen mengedit hanya kelas yang diampu; validasi 0–100 pada controller/model | Audit nilai immutable; penghapusan nilai/histori tidak ditawarkan di portal | Cetak/export nilai belum ditemukan | Assignment dosen dicek; filter historis berdasarkan assignment; perlu uji keamanan | PARTIAL | NOT TESTED |
| KRS | Backend `Kartu Rencana Studi`; portal `/my/krs[/<id>]`; daftar perwalian | Daftar perwalian memakai shared pagination; form pilihan mata kuliah belum dipaginasi (lihat batas di atas) | Backend search state/tahun/rombel; perwalian search/filter/sort; portal KRS validasi bisnis | Portal KRS dan detail ID, backend form/chatter | Mahasiswa membuat/mengubah draft; dosen wali menyetujui/mengembalikan | KRS submitted/approved dilindungi dari perubahan; hapus belum diaudit | Tidak ditemukan | Pemeriksaan user pemilik dan dosen wali tersedia di model/controller; belum diuji lintas akun | PARTIAL | NOT TESTED |
| KHS/transkrip | Backend `Hasil Studi Mahasiswa`; portal `/my/khs` | Baris mata kuliah KHS memakai shared pagination; backend belum diverifikasi | Portal search/sort pada mata kuliah; backend search belum runtime-tested | Portal ringkasan/transkrip dan PDF | Dibuat/diperbarui lewat kalkulasi nilai; bukan CRUD bebas mahasiswa | Histori akademik perlu dipertahankan; penghapusan tidak tersedia di portal | PDF tersedia | Portal membatasi pencarian ke mahasiswa login; akses laporan silang belum diuji | PARTIAL | NOT TESTED |
| Tahun ajaran/penawaran/kelas/rombel | Backend `Tahun Ajaran`, `Penawaran`, `Rombel`; kelas dosen | Kelas dosen memakai shared pagination; backend belum diverifikasi | Kelas dosen search/sort; filter periode di backend belum diuji | Kelas detail melalui input nilai; detail Rombel di backend form | Backend form; workflow penawaran | Relasi ke KRS/nilai harus dijaga; aturan archive/delete belum ditinjau penuh | Tidak ditemukan | Penawaran dosen dibatasi assignment; admin mengelola master | PARTIAL | NOT TESTED |
| Analitik dan monitoring | Backend analitik MK/CPMK/CPL/komponen, monitoring bobot; publik `/tracking`, `/perbandingan-cpl` | Portal analisis dosen memakai pagination; agregat publik saat ini bukan list CRUD | Filter perbandingan CPL; backend search/filters belum seluruhnya dipetakan | View analitik, bukan detail CRUD | Tidak relevan/tergantung sumber akademik | Tidak relevan | CSV perbandingan; PDF/print lain perlu audit | Publik hanya agregat; scope dosen perlu uji | PARTIAL | NOT TESTED |
| Konfigurasi, import/export, fixture | Backend settings, wizard import/export, data fixture | Belum diaudit | Belum diaudit | Form/wizard sesuai view yang terdaftar | Admin/superadmin melalui menu/wizard | Konfirmasi, validasi relasi, dan arsip belum diaudit | Import/export tersedia pada wizard; detail format belum diuji | Menu admin/superadmin; ACL wizard perlu pengujian | NOT AUDITED | NOT TESTED |

## Detail prioritas penilaian yang terverifikasi dari source

- Nilai dibatasi 0–100 pada route portal dan constraint model.
- Route nilai memeriksa dosen terhadap kelas yang ditugaskan dan memerlukan RPS
  final dengan bobot lengkap.
- Pembaruan nilai memanggil kalkulasi CPMK/Mata Kuliah/CPL dan pembaruan KHS
  untuk semua KRS kelas, walaupun dosen hanya mengirim nilai pada halaman aktif.
- Perubahan nilai menyimpan pengguna, waktu, nilai lama/baru, dan alasan opsional;
  audit tidak dapat diubah atau dihapus lewat model.
- Halaman input menampilkan status kelengkapan per mahasiswa, bobot komponen,
  pemetaan CPMK, dan hasil grade/CPMK jika record kalkulasi tersedia.
- Filter kelengkapan memerlukan identifikasi semua grade aktual kelas dan belum
  diuji performanya pada kelas besar.
- Fitur export/cetak daftar penilaian, perubahan lintas halaman dalam satu submit,
  serta UX konfirmasi sebelum menyimpan belum tersedia/dijalankan.

## Pengujian

| Pemeriksaan | Status | Catatan |
|---|---|---|
| Inventory source dan route | PASS | Addon, manifest, menu, controller, view, model, ACL/rule ditinjau secara statis |
| Python syntax check | PASS | Pemeriksaan statis berhasil |
| XML well-formedness dan manifest | PASS | Pemeriksaan statis berhasil; template pager perlu upgrade untuk validasi Odoo |
| Odoo test suite/module upgrade | NOT TESTED | CLI Odoo 19 tersedia; belum menjalankan upgrade karena perlu database uji dan backup yang terkonfirmasi |
| Browser login/portal setelah perubahan | NOT TESTED | Browser saat ini hanya pada database selector; tidak menggunakan akun pengguna |
| Role isolation dan lintas-record | NOT TESTED | Harus dijalankan dengan akun uji mahasiswa/dosen/admin |
| Responsive viewport/console/server log | NOT TESTED | Belum membuka halaman hasil build atau mengumpulkan log |

## Pekerjaan lanjutan untuk menutup audit

1. Terapkan dan uji pemilih ukuran pagination pada backend list secara konsisten,
   setelah memverifikasi extension point frontend Odoo 19.
2. Audit semua form/action, ACL, record rule, konfirmasi unlink, dan strategi
   archive untuk seluruh model yang memiliki relasi histori.
3. Tambahkan halaman detail bertab untuk entitas yang saat ini hanya memiliki
   backend form/list atau ringkasan portal.
4. Lengkapi fitur status/filter, export/print, serta UX input bulk nilai lintas
   halaman tanpa kehilangan perubahan yang belum disimpan.
5. Jalankan upgrade addon dengan backup development database, test module, dan
   QA browser multi-role/responsif sebelum mengubah status implementasi matriks.
