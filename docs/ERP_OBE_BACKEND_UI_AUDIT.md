# Audit UI Backend ERP OBE

## Cakupan audit

Audit inventaris mencakup 25 berkas XML di `views/`, termasuk view backend,
view Website, report, dan menu. Sebanyak 23 berkas memuat `ir.ui.view`.
Inventaris backend mencatat 100 record view pada 48 model: 25 form, 33 list,
22 search, 4 pivot, 4 graph, dan 12 view extension berbasis XPath.
Addon juga berisi 30 template XML Website/portal di `views/website/`; template
tersebut tidak diubah karena berada di luar lingkup internal-user.

Berkas view yang diaudit:

- Master/data akademik: `academic_fixture_views.xml`,
  `akademik_fakultas_views.xml`, `master_akademik_views.xml`,
  `master_angkatan_view_views.xml`, `master_grade_views.xml`,
  `master_prodi_views.xml`, `master_user_views.xml`.
- Kurikulum/pembelajaran: `akademik_cpl_views.xml`,
  `akademik_cpmk_views.xml`, `akademik_komponen_views.xml`,
  `akademik_penawaran_views.xml`, `akademik_rps_views.xml`,
  `akademik_tahunajaran_views.xml`.
- Perkuliahan/nilai: `akademik_krs_views.xml`, `grade_views.xml`.
- Hasil/analitik: `grade_cpl_views.xml`, `grade_cpmk_views.xml`,
  `grade_mk_views.xml`, `report_khs_views.xml`, `report_summary_views.xml`.
- Wizard/konfigurasi: `import_export_views.xml`,
  `triton_settings_views.xml`, `weight_monitor_views.xml`.

Modul tidak mendefinisikan view kanban, calendar, activity, atau dashboard
khusus. View analitik yang tersedia memakai graph dan pivot native Odoo.
Menu, action, dan urutan navigasi ditinjau sebagai batasan dan tidak diubah.

## Implementasi native Odoo

Seluruh asset override khusus backend dihapus agar warna, typography, control
panel, list, form, pagination, badge, dialog, dan komponen lain kembali memakai
implementasi native Odoo 19. Pagination kustom dan pengubahan default page size
dihapus; pager dan page size kembali mengikuti perilaku Odoo.

Tidak ada CSS/SCSS atau JavaScript backend kustom yang tersisa. Asset Website
yang terdaftar pada `web.assets_frontend`, termasuk variabel Sass yang
mempertahankan branding Website, portal, controller, dan template portal tidak
diubah. Variabel Sass tersebut dikecualikan dari bundle backend utama dan lazy.

Beberapa form dengan informasi berdekatan dirapikan memakai struktur native:

- List KRS, RPS, dan Mata Kuliah memakai lebar kolom native Odoo 19 yang
  proporsional untuk kode, nama, relasi, angka, dan badge. Tidak ada kolom yang
  disembunyikan atau dihapus.
- KRS memisahkan informasi akademik, batas studi, dan daftar mata kuliah.
- Input nilai memisahkan informasi penawaran, mata kuliah, dan nilai mahasiswa.
- Pemantauan bobot memisahkan kriteria, ringkasan, dan rincian; tombol tindakan
  memakai header form native.
- Wizard salin RPS memisahkan data tujuan, sumber, pratinjau, dan konfirmasi.
- Skala nilai memisahkan rentang/konversi dari keterangan standar.

Perubahan hanya pada penyajian arsitektur XML. Field, modifier, domain, action,
filter, tombol, hak akses, model, dan data tidak dihapus atau diganti.

## Audit template OWL

Loop `props.pageSizes` yang sebelumnya memicu OWL error berada pada ekstensi
pager backend kustom. Ekstensi tersebut dihapus agar pagination kembali native.
Test addon kini memeriksa seluruh XML di `static/src/` dan gagal jika menemukan
`t-foreach` tanpa `t-key`. Template server-side QWeb di `views/` tidak termasuk
template OWL.

## Berkas yang diubah

- `__manifest__.py`: menghapus registrasi asset backend kustom dan mengecualikan
  branding Sass Website dari bundle backend.
- `views/akademik_krs_views.xml`: mengelompokkan informasi form KRS.
- `views/akademik_rps_views.xml`: menetapkan lebar native untuk list RPS.
- `views/master_akademik_views.xml`: menetapkan lebar native list Mata Kuliah.
- `views/grade_views.xml`: mengelompokkan informasi input nilai.
- `views/weight_monitor_views.xml`: menata filter, ringkasan, rincian, dan
  wizard salin RPS.
- `views/master_grade_views.xml`: mengelompokkan rentang nilai dan keterangan.
- `tests/test_ui_views.py`: memeriksa keyed loop pada seluruh template OWL addon.
- `static/src/scss/backend/_backend.scss`,
  `static/src/xml/backend_ui.xml`,
  `static/src/xml/backend_pagination.xml`, dan
  `static/src/js/backend_list_pager.js`: asset custom backend dihapus.

## Validasi

- **PASS** — Odoo 19 upgrade `erpobe` pada database uji
  `erpobe_test_rps_link_20261120`; 43 modul dimuat.
- **PASS** — `TestErpObeUiViews`: 3 test lulus, 0 gagal/error. Seluruh action
  internal berhasil memuat jenis view yang dikonfigurasi.
- **PASS** — 61 XML addon berhasil diparse; tidak ditemukan loop OWL tanpa
  `t-key` dalam `static/src/`.
- **PASS** — Odoo membuat asset JS/CSS backend tanpa error. Backend CSS hasil
  kompilasi tidak memuat warna atau selector theme/pager ERP OBE yang dihapus.
- **PASS** — Browser: list KRS, form KRS, dan input nilai berhasil dirender.
  Pager native bergerak dari 1-80/800 ke 81-160/800; pencarian KRS menghasilkan
  32 record. Statusbar, inline list, nested pager, dan chatter tampil. Form
  skala nilai juga menampilkan grup rentang dan keterangan standar.
- **PASS** — Browser: view pivot dan graph Analisis Mata Kuliah dirender, graph
  canvas tersedia, dan tidak ada console/page error pada alur tersebut.
- **PASS** — Responsive check list KRS pada 1440x900, 1366x768, 768x1024,
  390x844, dan 360x800 tidak menunjukkan horizontal overflow pada dokumen.
  Pada viewport sempit, tabel memakai scroll container native Odoo.
- **BLOCKED** — Tombol Kelengkapan Bobot di browser menolak user uji saat ini
  karena ACL model `erpobe.weight.monitor` membatasi create ke grup Admin dan
  Superadmin. ACL sengaja tidak diubah. XML view tetap dimuat saat upgrade.
- **PARTIAL** — CRUD lengkap, semua wizard, dan seluruh 88 arsitektur view belum
  dijalankan satu per satu melalui browser; test otomatis memuat view dari
  seluruh action yang terdaftar.

## Batasan audit

Tidak ada view khusus kanban, calendar, activity, atau dashboard di addon ini;
jenis tersebut tetap menggunakan komponen native Odoo bila disediakan melalui
modul lain.
