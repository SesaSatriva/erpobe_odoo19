# Website and Portal Reconstruction Report

## Scope and counts

Validation used only the isolated database `erpobe_test_rps_fix`. The existing
`obe` database was not accessed or changed.

- **27 custom page templates:** 14 public and 13 authenticated portal templates.
- **4 shared QWeb component templates:** public navigation/footer, portal
  navigation, list controls, and login branding.
- **36 public browser URL variants checked**, plus the CSV export over HTTP.
- The public person-profile template serves both lecturer and student routes.
  Their public routes correctly return 404 while public people visibility is
  disabled.
- Odoo-native `/my/security`, `/my` redirect, and `/web/login` are outside the
  custom page-template count.

All custom pages use `website.layout`. Public pages add the public navigation
and footer; portal pages add role-aware portal navigation and the TRITON footer.
Native security and login pages use Odoo's layouts with the module's login
branding inheritance.

## Public page inventory

| Page | URL | Controller / QWeb template | Role and purpose | Flow and QA finding |
|---|---|---|---|---|
| Homepage | `/`, `/triton` | `main.py` / `triton_home_page` | Public landing, academic summary, entry points | Start → search, faculty, comparison, tracking, information pages. CTA contrast and duplicate metrics were corrected. |
| Search | `/cari`, `/triton/cari` | `main.py` / `triton_search_page` | Public search for academic information | From public navigation/home → result links. HTTP 200 checked. |
| Faculty listing | `/fakultas`, `/triton/fakultas` | `fakultas.py` / `triton_faculty_list_page` | Public faculty discovery | Home → faculty detail. HTTP 200 checked. |
| Faculty detail | `/fakultas/<id>`, `/triton/fakultas/<id>` | `fakultas.py` / `triton_faculty_detail_page` | Faculty overview and study-program links | Faculty listing → program detail. HTTP 200 checked. |
| Program detail and tabs | `/prodi/<id>`, `/triton/prodi/<id>` | `fakultas.py` / `triton_prodi_detail_page` | Public profile, lecturer/student listings, CPL, courses | Faculty detail → tabs; profile tabs link to related public records. Removed the custom `pager` collision that caused 500s; course search/sort now uses stored related fields. |
| Public person profile | `/dosen/<id>`, `/triton/dosen/<id>`, `/mahasiswa/<id>`, `/triton/mahasiswa/<id>` | `profil.py` / `triton_person_profile_page` | Public profile, subject to visibility/privacy settings | Program detail → profile → program. 404 is expected while public people visibility is disabled; private data is not exposed. |
| CPL comparison | `/perbandingan-cpl`, `/triton/perbandingan` | `perbandingan.py` / `triton_comparison_page` | Public aggregated outcome comparison | Public navigation ↔ tracking/academic information. HTTP 200 checked. |
| Aggregate tracking | `/tracking`, `/triton/tracking` | `tracking.py` / `triton_tracking_page` | Public aggregate tracking | Public navigation ↔ comparison. HTTP 200 checked. |
| About | `/tentang`, `/triton/tentang` | `main.py` / `triton_about_page` | Public TRITON overview | Public navigation/footer → information pages. HTTP 200 checked. |
| Guide | `/panduan`, `/triton/panduan` | `main.py` / `triton_guide_page` | Public usage guidance | Public footer → FAQ/contact. HTTP 200 checked. |
| FAQ | `/faq`, `/triton/faq` | `main.py` / `triton_faq_page` | Public help | Guide/contact cross-links. HTTP 200 checked. |
| Contact | `/kontak`, `/triton/kontak` | `main.py` / `triton_contact_page` | Public contact information | Footer/help links. HTTP 200 checked. |
| Privacy policy | `/privasi`, `/kebijakan-privasi`, `/triton/kebijakan-privasi` | `main.py` / `triton_privacy_page` | Public privacy statement | Footer → methodology/about. HTTP 200 checked. |
| Methodology | `/metodologi`, `/triton/metodologi` | `main.py` / `triton_methodology_page` | Public explanation of CPL methodology | Footer → privacy/about. HTTP 200 checked. |

`/triton/api/perbandingan-cpl` and `/perbandingan-cpl.csv` are API/export
endpoints, not page templates. The API returned HTTP 200; CSV returned HTTP 200
with `text/csv`.

## Portal page inventory

| Page | URL | Controller / QWeb template | Role and purpose | Flow and QA finding |
|---|---|---|---|---|
| Portal dashboard | `/my`, `/my/triton` | `portal.py` / `triton_portal_home_page` | Student/lecturer role-specific workspace | Start → role navigation and priority actions. Student and lecturer dashboards rendered at all five viewport targets. |
| Student KRS | `/my/krs`, `/my/krs/<id>` | `portal_mahasiswa.py` / `triton_krs_page` | View/edit course plan and status | Dashboard → KRS → submit/return. Own KRS returned 200; another student's KRS returned 403. No active offers were available in the tested fixture, so the KRS selection POST was not exercised. |
| Student KHS | `/my/khs` | `portal_mahasiswa.py` / `triton_khs_page` | Transcript and semester results | Dashboard → KHS. Search and both sort options returned 200. |
| Student courses | `/my/mata-kuliah` | `portal_mahasiswa.py` / `triton_student_courses_page` | Approved course list and learning details | Dashboard/KRS → courses. Search/sort returned 200. |
| Student CPL | `/my/capaian-cpl` | `portal_mahasiswa.py` / `triton_student_cpl_page` | Personal outcome attainment | Dashboard → CPL. Search/sort returned 200; private data is not public. |
| User profile | `/my/profil` | `portal_mahasiswa.py` / `triton_student_profile_page` | Shared student/lecturer contact and privacy settings | Portal account menu → profile → native security. Academic identity, status, credits, and grades are not editable in the template. |
| Lecturer RPS listing | `/my/rps` | `portal_dosen.py` / `triton_teacher_rps_page` | Assigned RPS, status, search, filters, and actions | Dashboard → RPS → editor/review/finalization or report, depending on state. Search, filters, and all sort options returned 200. |
| Lecturer RPS editor | `/my/rps/<line_id>/edit` | `portal_dosen.py` / `triton_rps_edit_page` | RPS descriptions, components, and weight entry | RPS listing → editor → draft/review. Route and form rendered at all five viewport targets; write/finalization was not submitted. |
| Lecturer class listing | `/my/kelas` | `portal_dosen.py` / `triton_teacher_classes_page` | Assigned classes and assessment entry points | Dashboard → classes → grade entry. Search/sort returned 200. |
| Lecturer grade entry | `/my/kelas/<line_id>/nilai` | `portal_dosen.py` / `triton_teacher_grades_page` | Class-scoped student assessment | Class listing → grade entry → history/analysis. Search and sort returned 200; another teacher's class returned 403. Grade POST was not submitted. |
| Grade history | `/my/riwayat-nilai` | `portal_dosen.py` / `triton_grade_history_page` | Immutable history of grade changes for assigned classes | Dashboard/grade entry → history. Search/sort returned 200. |
| Advising | `/my/perwalian` | `portal_dosen.py` / `triton_advising_page` | Review advisee KRS and decisions | Dashboard → advising → approve/reject. List and sort returned 200; decision POST was not submitted. |
| Lecturer analysis | `/my/analisis` | `portal_dosen.py` / `triton_teacher_analysis_page` | Filtered CPMK/CPL/cohort analysis | Dashboard → analysis. Route and cohort filters returned 200. |

All portal pages require an authenticated user and controller-side role/ownership
checks. Student-to-lecturer routes returned 403; lecturer-to-student routes
returned 403. `/my/security` is the native Odoo account-security page, not a
custom TRITON template.

## Findings and implementation

Three application defects were found and corrected:

1. The program-detail controller populated Odoo's reserved `pager` context with a
   custom pagination object. Odoo 19's website layout then failed on the CPL and
   course tabs. The custom value is now passed only as `pagination`.
2. Several list sort expressions traversed many-to-one fields (for example
   `mahasiswa_id.name`), which Odoo 19 rejects for ordering. Stored related
   name/code fields now provide working sorting and search across public courses,
   student lists, RPS, KHS, CPL, advising, and grade lists.
3. KHS and RPS report templates applied QWeb field widgets directly to `<td>`.
   The widgets are now wrapped in inline `<span>` elements. Both authenticated
   HTML report routes now return HTTP 200.

Other related UI updates retained from the previous implementation include the
public/login navigation, profile security link, responsive portal styles,
homepage CTA contrast, removal of duplicate homepage metrics, and reuse of the
same comparison result for homepage statistics.

## Validation results

- Module upgrade on `erpobe_test_rps_fix`: **PASS**.
- Focused UI/public/portal/report tests: **14 passed, 0 failed, 0 errors**.
- Python compile check: **PASS**.
- Browser public URL checks: **36 URL variants**; 34 returned HTTP 200 and the
  two hidden person-profile routes returned the expected HTTP 404. The CSV
  endpoint was checked separately and returned HTTP 200.
- Student portal: 8 routes/states × 5 viewports = **40 checks**, all HTTP 200 and
  no document horizontal overflow.
- Lecturer portal: 9 routes/states × 5 viewports = **45 checks**, all HTTP 200
  and no document horizontal overflow. The RPS editor added 5 more checks.
- Repaired public CPL/course tabs: **10 route/viewport checks**, all HTTP 200
  with expected content and no horizontal overflow.
- Viewports: 1440×900, 1366×768, 768×1024, 390×844, and 360×800. The remote
  browser measured 1367×767 and 767×1024 for two targets, within one CSS pixel.
- Search/sort/pagination were exercised in the browser on the public course
  listing; student and lecturer list searches/sorts returned HTTP 200.
- Mobile portal menu opened and exposed role navigation, profile, public-site,
  and logout links. Student logout/login and lecturer login were exercised.
- Browser screenshots were captured and visually inspected for the public
  program page, lecturer dashboard (desktop/mobile), and lecturer grade-entry
  page. They were not saved as files in the module.
- Cross-role/ownership checks: expected HTTP 403 for lecturer-only routes from a
  student, a different student's KRS, and a class outside the lecturer's scope.

The complete module suite completed 80 post-install tests but is not clean:
**2 failures and 1 error** remain in `test_faculty_scope`,
`test_rps_versioning`, and `test_weight_validation`. These test paths were not
changed here; no clean baseline run was available to classify them as
pre-existing.

## Unresolved / not tested

- PDF report rendering returns HTTP 422 because this environment has no
  `wkhtmltopdf` executable. The PDF report action was exercised; the HTML report
  templates passed. No system package was installed.
- Data-mutating browser flows (KRS submit, profile save, grade save, RPS save,
  advising decision, password change, passkey, and account deletion) were not
  submitted, to avoid altering the existing test fixture. Their forms/routes
  were inspected where available.
- The public lecturer/student profile routes are intentionally not visible under
  the current privacy setting; enabling those routes requires an explicit
  configuration change and was not done.
- Full-suite failures listed above remain unresolved. The focused changed-route
  tests pass, but the project is not reported as fully green.

## Files changed in this continuation

- Controllers: `controllers/fakultas.py`, `controllers/portal_dosen.py`,
  `controllers/portal_mahasiswa.py`.
- Models: `models/akademik_krs.py`, `models/akademik_penawaran.py`,
  `models/akademik_rps.py`, `models/grade.py`, `models/grade_cpl.py`,
  `models/report_khs.py`.
- Views/tests: `views/triton_reports.xml`,
  `tests/test_triton_workflows.py`.

## Files retained from the previous implementation

- `views/menus.xml`, `views/website/components/website_navigation.xml`,
  `views/website/portal/portal_profile.xml`,
  `views/website/public/website_home.xml`.
- `static/src/scss/components/_portal.scss`,
  `static/src/scss/pages/_professional.scss`,
  `tests/test_ui_views.py`, `controllers/main.py`, and
  `controllers/helpers.py`.
