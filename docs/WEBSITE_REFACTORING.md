# Refactoring XML Website ERP OBE

Tanggal: 2026-11-18

## Ruang lingkup

Refactoring memisahkan template Website berdasarkan halaman dan menyamakan
prefix nama file. Root modul, model, route, autentikasi, security, dan business
logic dipertahankan. Satu order key controller diperbaiki agar halaman mata
kuliah tidak gagal pada query Odoo 19. XML backend serta report PDF tetap berada
di `views/` non-Website.

## Struktur awal sebelum page split

Sebelum pemecahan halaman, semua file berada langsung di `views/`. Template
Website digabung dalam:

- `triton_public_templates.xml`: menu publik, navigasi, footer, dan 14 halaman
  publik.
- `triton_portal_templates.xml`: navigasi portal dan 12 halaman portal.
- `triton_reports.xml`: dua template QWeb PDF, bukan halaman Website.
- `triton_settings_views.xml`: inherited form backend `res.config.settings`.
- `weight_monitor_views.xml`: form monitoring bobot dan dua wizard backend.

File XML backend lain yang tetap berada di root `views/`:

```text
akademik_cpl_views.xml
akademik_cpmk_views.xml
akademik_fakultas_views.xml
akademik_komponen_views.xml
akademik_krs_views.xml
akademik_penawaran_views.xml
akademik_rps_views.xml
akademik_tahunajaran_views.xml
grade_cpl_views.xml
grade_cpmk_views.xml
grade_mk_views.xml
grade_views.xml
import_export_views.xml
master_akademik_views.xml
master_angkatan_view_views.xml
master_grade_views.xml
master_prodi_views.xml
master_user_views.xml
menus.xml
report_khs_views.xml
report_summary_views.xml
```

## Struktur sesudah

```text
views/
├── website/
│   ├── components/
│   │   ├── website_navigation.xml
│   │   └── portal_navigation.xml
│   ├── public/
│   │   ├── website_about.xml
│   │   ├── website_comparison.xml
│   │   ├── website_contact.xml
│   │   ├── website_faculty_detail.xml
│   │   ├── website_faculty_list.xml
│   │   ├── website_faq.xml
│   │   ├── website_guide.xml
│   │   ├── website_home.xml
│   │   ├── website_methodology.xml
│   │   ├── website_person_profile.xml
│   │   ├── website_privacy.xml
│   │   ├── website_program_detail.xml
│   │   ├── website_search.xml
│   │   └── website_tracking.xml
│   └── portal/
│       ├── portal_dashboard.xml
│       ├── portal_profile.xml
│       ├── student/
│       │   ├── portal_courses.xml
│       │   ├── portal_cpl.xml
│       │   ├── portal_khs.xml
│       │   └── portal_krs.xml
│       └── teacher/
│           ├── portal_advising.xml
│           ├── portal_analysis.xml
│           ├── portal_classes.xml
│           ├── portal_grades.xml
│           ├── portal_rps.xml
│           └── portal_rps_edit.xml
├── akademik_cpl_views.xml
├── akademik_cpmk_views.xml
├── akademik_fakultas_views.xml
├── akademik_komponen_views.xml
├── akademik_krs_views.xml
├── akademik_penawaran_views.xml
├── akademik_rps_views.xml
├── akademik_tahunajaran_views.xml
├── grade_cpl_views.xml
├── grade_cpmk_views.xml
├── grade_mk_views.xml
├── grade_views.xml
├── import_export_views.xml
├── master_akademik_views.xml
├── master_angkatan_view_views.xml
├── master_grade_views.xml
├── master_prodi_views.xml
├── master_user_views.xml
├── menus.xml
├── report_khs_views.xml
├── report_summary_views.xml
├── triton_reports.xml
├── triton_settings_views.xml
└── weight_monitor_views.xml
```

## Rename untuk konsistensi prefix

Sebelum rename ini, berkas website berada di direktori yang sama dengan
struktur sesudah page split, tetapi nama filenya belum memakai prefix. XML ID
dan isi template tidak berubah.

| Sebelum | Sesudah |
|---|---|
| `website/components/navigation.xml` | `website/components/website_navigation.xml` |
| `website/public/about.xml` | `website/public/website_about.xml` |
| `website/public/comparison.xml` | `website/public/website_comparison.xml` |
| `website/public/contact.xml` | `website/public/website_contact.xml` |
| `website/public/faculty_detail.xml` | `website/public/website_faculty_detail.xml` |
| `website/public/faculty_list.xml` | `website/public/website_faculty_list.xml` |
| `website/public/faq.xml` | `website/public/website_faq.xml` |
| `website/public/guide.xml` | `website/public/website_guide.xml` |
| `website/public/home.xml` | `website/public/website_home.xml` |
| `website/public/methodology.xml` | `website/public/website_methodology.xml` |
| `website/public/person_profile.xml` | `website/public/website_person_profile.xml` |
| `website/public/privacy.xml` | `website/public/website_privacy.xml` |
| `website/public/program_detail.xml` | `website/public/website_program_detail.xml` |
| `website/public/search.xml` | `website/public/website_search.xml` |
| `website/public/tracking.xml` | `website/public/website_tracking.xml` |
| `website/portal/dashboard.xml` | `website/portal/portal_dashboard.xml` |
| `website/portal/profile.xml` | `website/portal/portal_profile.xml` |
| `website/portal/student/courses.xml` | `website/portal/student/portal_courses.xml` |
| `website/portal/student/cpl.xml` | `website/portal/student/portal_cpl.xml` |
| `website/portal/student/khs.xml` | `website/portal/student/portal_khs.xml` |
| `website/portal/student/krs.xml` | `website/portal/student/portal_krs.xml` |
| `website/portal/teacher/advising.xml` | `website/portal/teacher/portal_advising.xml` |
| `website/portal/teacher/analysis.xml` | `website/portal/teacher/portal_analysis.xml` |
| `website/portal/teacher/classes.xml` | `website/portal/teacher/portal_classes.xml` |
| `website/portal/teacher/grades.xml` | `website/portal/teacher/portal_grades.xml` |
| `website/portal/teacher/rps.xml` | `website/portal/teacher/portal_rps.xml` |
| `website/portal/teacher/rps_edit.xml` | `website/portal/teacher/portal_rps_edit.xml` |

`website/components/portal_navigation.xml` sudah sesuai prefix dan tidak
di-rename. File lama `triton_public_templates.xml` dan
`triton_portal_templates.xml` tidak terdaftar lagi dan sudah dihapus setelah
kontennya dipindahkan.

## Komponen dan halaman yang ditemukan

Komponen bersama:

- Navigasi publik: dipakai oleh halaman publik.
- Footer: dipakai oleh halaman publik dan portal.
- Navigasi portal: dipakai oleh halaman portal.
- Menu website `menu_triton_public`: tetap dimuat bersama komponen navigasi.

Halaman publik: beranda, pencarian, daftar fakultas, detail fakultas, detail
program studi, profil individu, perbandingan CPL, tracking, tentang, panduan,
FAQ, kontak, privasi, dan metodologi.

Halaman portal: dashboard, profil, KRS, KHS, mata kuliah, capaian CPL, daftar
RPS dosen, editor RPS, kelas dosen, input nilai, perwalian, dan analisis kelas.

## Mapping file lama dan XML ID

| Sumber lama | XML ID | File baru |
|---|---|---|
| `triton_public_templates.xml` | `menu_triton_public`, `triton_main_nav`, `triton_footer` | `website/components/website_navigation.xml` |
| `triton_public_templates.xml` | `triton_home_page` | `website/public/website_home.xml` |
| `triton_public_templates.xml` | `triton_search_page` | `website/public/website_search.xml` |
| `triton_public_templates.xml` | `triton_faculty_list_page` | `website/public/website_faculty_list.xml` |
| `triton_public_templates.xml` | `triton_faculty_detail_page` | `website/public/website_faculty_detail.xml` |
| `triton_public_templates.xml` | `triton_prodi_detail_page` | `website/public/website_program_detail.xml` |
| `triton_public_templates.xml` | `triton_person_profile_page` | `website/public/website_person_profile.xml` |
| `triton_public_templates.xml` | `triton_comparison_page` | `website/public/website_comparison.xml` |
| `triton_public_templates.xml` | `triton_tracking_page` | `website/public/website_tracking.xml` |
| `triton_public_templates.xml` | `triton_about_page` | `website/public/website_about.xml` |
| `triton_public_templates.xml` | `triton_guide_page` | `website/public/website_guide.xml` |
| `triton_public_templates.xml` | `triton_faq_page` | `website/public/website_faq.xml` |
| `triton_public_templates.xml` | `triton_contact_page` | `website/public/website_contact.xml` |
| `triton_public_templates.xml` | `triton_privacy_page` | `website/public/website_privacy.xml` |
| `triton_public_templates.xml` | `triton_methodology_page` | `website/public/website_methodology.xml` |
| `triton_portal_templates.xml` | `triton_portal_nav` | `website/components/portal_navigation.xml` |
| `triton_portal_templates.xml` | `triton_portal_home_page` | `website/portal/portal_dashboard.xml` |
| `triton_portal_templates.xml` | `triton_student_profile_page` | `website/portal/portal_profile.xml` |
| `triton_portal_templates.xml` | `triton_krs_page` | `website/portal/student/portal_krs.xml` |
| `triton_portal_templates.xml` | `triton_khs_page` | `website/portal/student/portal_khs.xml` |
| `triton_portal_templates.xml` | `triton_student_courses_page` | `website/portal/student/portal_courses.xml` |
| `triton_portal_templates.xml` | `triton_student_cpl_page` | `website/portal/student/portal_cpl.xml` |
| `triton_portal_templates.xml` | `triton_teacher_rps_page` | `website/portal/teacher/portal_rps.xml` |
| `triton_portal_templates.xml` | `triton_rps_edit_page` | `website/portal/teacher/portal_rps_edit.xml` |
| `triton_portal_templates.xml` | `triton_teacher_classes_page` | `website/portal/teacher/portal_classes.xml` |
| `triton_portal_templates.xml` | `triton_teacher_grades_page` | `website/portal/teacher/portal_grades.xml` |
| `triton_portal_templates.xml` | `triton_advising_page` | `website/portal/teacher/portal_advising.xml` |
| `triton_portal_templates.xml` | `triton_teacher_analysis_page` | `website/portal/teacher/portal_analysis.xml` |

Seluruh blok XML dipertahankan persis, termasuk isi, atribut, struktur QWeb, dan
XML ID. Tidak ada template Website yang di-inherit atau dipecah menjadi
komponen satu halaman; relasi `t-call` tetap menunjuk ke layout dan komponen
bersama yang sama.

## Mapping route dan controller

Semua route tetap memakai decorator dan controller yang sama. Route halaman
publik tetap `auth='public'`; halaman portal tetap `auth='user'`.

| Halaman / XML ID | Route | Controller |
|---|---|---|
| `triton_home_page` | `/`, `/triton` | `controllers/main.py` |
| `triton_search_page` | `/cari`, `/triton/cari` | `controllers/main.py` |
| `triton_about_page` | `/tentang`, `/triton/tentang` | `controllers/main.py` |
| `triton_guide_page` | `/panduan`, `/triton/panduan` | `controllers/main.py` |
| `triton_faq_page` | `/faq`, `/triton/faq` | `controllers/main.py` |
| `triton_contact_page` | `/kontak`, `/triton/kontak` | `controllers/main.py` |
| `triton_privacy_page` | `/privasi`, `/kebijakan-privasi`, `/triton/kebijakan-privasi` | `controllers/main.py` |
| `triton_methodology_page` | `/metodologi`, `/triton/metodologi` | `controllers/main.py` |
| `triton_faculty_list_page` | `/fakultas`, `/triton/fakultas` | `controllers/fakultas.py` |
| `triton_faculty_detail_page` | `/fakultas/<int:faculty_id>`, `/triton/fakultas/<int:faculty_id>` | `controllers/fakultas.py` |
| `triton_prodi_detail_page` | `/prodi/<int:prodi_id>`, `/triton/prodi/<int:prodi_id>` | `controllers/fakultas.py` |
| `triton_person_profile_page` | `/dosen/<int:dosen_id>`, `/triton/dosen/<int:dosen_id>`, `/mahasiswa/<int:mahasiswa_id>`, `/triton/mahasiswa/<int:mahasiswa_id>` | `controllers/profil.py` |
| `triton_comparison_page` | `/perbandingan-cpl`, `/triton/perbandingan` | `controllers/perbandingan.py` |
| `triton_tracking_page` | `/tracking`, `/triton/tracking` | `controllers/tracking.py` |
| `triton_portal_home_page` | `/my/triton` | `controllers/portal.py` |
| `triton_krs_page` | `/my/krs`, `/my/krs/<int:krs_id>` | `controllers/portal_mahasiswa.py` |
| `triton_khs_page` | `/my/khs` | `controllers/portal_mahasiswa.py` |
| `triton_student_courses_page` | `/my/mata-kuliah` | `controllers/portal_mahasiswa.py` |
| `triton_student_cpl_page` | `/my/capaian-cpl` | `controllers/portal_mahasiswa.py` |
| `triton_student_profile_page` | `/my/profil` | `controllers/portal_mahasiswa.py` |
| `triton_teacher_rps_page` | `/my/rps` | `controllers/portal_dosen.py` |
| `triton_rps_edit_page` | `/my/rps/<int:line_id>/edit` | `controllers/portal_dosen.py` |
| `triton_teacher_classes_page` | `/my/kelas` | `controllers/portal_dosen.py` |
| `triton_teacher_grades_page` | `/my/kelas/<int:line_id>/nilai` | `controllers/portal_dosen.py` |
| `triton_advising_page` | `/my/perwalian` | `controllers/portal_dosen.py` |
| `triton_teacher_analysis_page` | `/my/analisis` | `controllers/portal_dosen.py` |

Route API/unduhan tetap berada pada implementasi existing:
`/triton/api/perbandingan-cpl`, `/perbandingan-cpl.csv`,
`/my/krs/<int:krs_id>/submit`, aksi RPS (`create`, `finalize`, `copy`), dan
`/my/perwalian/<int:krs_id>/putusan`. Parameter, metode HTTP, CSRF,
autentikasi/otorisasi, `request.render`, domain ORM, dan data template tetap.
Seluruh 34 deklarasi route controller dipertahankan. Perubahan controller
terbatas pada kunci pengurutan query `/my/mata-kuliah`.

## Perubahan manifest

Pada `__manifest__.py`, dua referensi lama ke
`views/triton_public_templates.xml` dan `views/triton_portal_templates.xml`
diganti dengan 28 file baru. Komponen dimuat sebelum halaman yang memanggilnya.
Semua entry security, view backend, report, demo, dan asset lainnya
dipertahankan. Tidak ada path data duplikat dan seluruh path terdaftar tersedia.
Setelah perubahan daftar file data, proses Odoo yang sudah berjalan perlu
direstart sebelum upgrade agar memuat manifest yang baru, bukan cache daftar
file lama.

## Hasil validasi

- Seluruh 65 file XML dapat diparse; 1.553 XML ID unik.
- Seluruh 55 manifest data entry dan 11 asset path tersedia; tidak ada
  duplikasi `data` entry.
- Seluruh 26 target `request.render()` terdaftar; 28 file XML Website terdaftar
  melalui manifest. Controller dan test Python berhasil diparse.
- Install `erpobe` berhasil pada database terisolasi
  `erpobe_test_consistency_20261118_1139`.
- Upgrade `-u erpobe` berhasil pada database yang sama. Log upgrade tidak
  memuat `External ID not found`, `QWebException`, `ParseError`, atau traceback.
- Test terfokus `TestTritonPublicRoutes`: 4 test lulus, 0 gagal/error.
  Halaman publik, API/unduhan, dan asset yang diuji merespons HTTP 200; halaman
  portal tanpa autentikasi mengarahkan ke login; `/my/mata-kuliah` terautentikasi
  merespons HTTP 200.
- Suite lengkap: 51 test berjalan, 50 lulus dan 1 gagal. Kegagalan adalah
  `TestErpObeUiViews.test_faculty_form_only_contains_program_studies`, yang
  mengharapkan menu Program Studi berada di bawah Fakultas, sedangkan menu
  aktual berada di bawah root. Ini tidak terkait pemuatan Website XML; tidak
  ada error atau traceback pada suite.

### Perbaikan konsistensi terkait

Query `/my/mata-kuliah` kini mengurutkan berdasarkan `krs_id asc,
matakuliah_id asc`. Ini menghindari dotted order path yang sebelumnya
menyebabkan HTTP 500; urutan KRS terkait tetap mengikuti `_order` model.
Regression test HTTP menegaskan bahwa mahasiswa tanpa KRS disetujui mendapat
halaman kosong yang valid, bukan exception.

Duplikasi deklarasi backend `menu_erpobe_master_prodi` di
`views/menus.xml` telah dibersihkan dengan mempertahankan deklarasi root menu
yang berlaku. Perubahan ini diperlukan agar XML ID menu tidak dideklarasikan
dua kali.

## Hasil akhir

Struktur root modul tidak berubah. File Website memakai prefix `website_` atau
`portal_`, sementara XML ID dan route tetap dipertahankan. Install, upgrade,
dan test HTTP terfokus telah selesai pada database `erpobe_test` khusus. Satu
kegagalan suite lengkap yang menyangkut ekspektasi parent menu backend dicatat
di atas dan tidak disamarkan sebagai suite yang sepenuhnya lulus.
