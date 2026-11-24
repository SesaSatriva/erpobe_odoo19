# TRITON Portal QA Checklist

Status: PASS, FAIL, BLOCKED, NOT TESTED.

## Public website

- [x] PASS — Homepage opens and renders TRITON identity.
- [x] PASS — TRITON asset returns HTTP 200 and JPEG MIME.
- [x] PASS — Navbar/footer logo use official asset.
- [x] PASS — Login displays only TRITON identity.
- [ ] NOT TESTED — `/fakultas` full interaction.
- [ ] NOT TESTED — `/tentang` full interaction.
- [ ] NOT TESTED — `/cari`, comparison, tracking, and contact workflows.

## Authentication

- [x] PASS — Student login.
- [x] PASS — Lecturer login.
- [x] PASS — Logout redirects to login.
- [ ] NOT TESTED — Password change.
- [ ] NOT TESTED — Passkey.
- [ ] NOT TESTED — Reset password.

## Student portal

- [x] PASS — Dashboard.
- [x] PASS — KRS page and empty active-offer state.
- [x] PASS — KHS/transcript.
- [ ] NOT TESTED — Course detail.
- [ ] NOT TESTED — CPL chart and detail.
- [x] PASS — Profile render.
- [x] PASS — Profile persistence.
- [ ] NOT TESTED — Profile photo upload.
- [ ] NOT TESTED — Cross-student direct endpoint access.

## Lecturer portal

- [x] PASS — Dashboard.
- [x] PASS — Kelas.
- [x] PASS — Input grade route.
- [x] PASS — Grade range form.
- [x] PASS — Grade persistence and recompute request.
- [x] PASS — Assessment history.
- [ ] NOT TESTED — Grade export.
- [ ] NOT TESTED — RPS edit/finalization/copy.
- [ ] NOT TESTED — Advising approval.
- [ ] NOT TESTED — Cross-teacher class direct endpoint.

## Security

- [x] PASS — Lecturer denied student KRS route.
- [x] PASS — Student route hides NIM/NIP/status/grades editing.
- [ ] NOT TESTED — Direct unauthorized line grade endpoint.
- [ ] NOT TESTED — Direct other student profile endpoint.
- [ ] NOT TESTED — Public route privacy audit.

## Responsive

- [x] PASS — 1440×900 homepage.
- [x] PASS — 1366×768 grade page.
- [x] PASS — 768×1024 homepage.
- [x] PASS — 390×844 no measured horizontal overflow after viewport stabilization.
- [ ] NOT TESTED — 360×800.
- [ ] NOT TESTED — Mobile grade-table usability.
- [ ] NOT TESTED — Mobile modal.

## Performance

- [ ] BLOCKED — Grade save measured around 6.5 seconds; optimize or document.
- [ ] NOT TESTED — N+1 queries in class/student and report rendering.
- [ ] NOT TESTED — Browser network failed-request audit.

## Automated testing

- [x] PASS — XML parsing.
- [x] PASS — `check_refs.py`.
- [ ] NOT TESTED — Full Odoo test suite.
- [ ] NOT TESTED — Permanent Playwright test suite.

## Rule-based academic assistant

- The OWL component is registered through `main_components` in
  `web.assets_backend` and calls the authenticated JSON-RPC endpoint
  `/web/erpobe/assistant/query`. The endpoint accepts internal users and
  `erpobe.group_admin` users; model ACLs and record rules still constrain data.
- The service uses the active user's ORM environment without `sudo()` or raw SQL.
  Page record context is accepted only for an allowlisted model and is resolved
  again through ORM search, so ACLs and record rules remain in effect.
- Assistant aggregates over `erpobe.grade.cpmk` and `erpobe.grade.mk` explicitly
  restrict lecturer-group users to `user.erpobe_prodi_ids`; existing record rules
  for those models do not provide lecturer-specific scope.
- [x] PASS — Assistant SCSS compiles with libsass, the compiler used by Odoo.
- Verified data sources are `erpobe.master.mahasiswa`, `erpobe.master.dosen`,
  `erpobe.master.prodi`, `erpobe.master.fakultas`,
  `erpobe.master.matakuliah`, `erpobe.akademik.rps`,
  `erpobe.akademik.cpl`, `erpobe.akademik.cpmk`, their existing grade models,
  and `erpobe.report.khs`.
- Implemented intent groups cover student counts/search/cohort/program and
  accessible GPA data; lecturer counts/search/program/workload; program and
  faculty counts/distribution; RPS search/status/weight completeness; CPL/CPMK
  counts and stored-score summaries; course counts/search and stored-grade
  summaries; and a scoped academic count summary. Unsupported comparisons are
  reported as unsupported rather than inferred.
- [ ] NOT TESTED — Odoo module upgrade and authenticated backend endpoint.
- [ ] NOT TESTED — Role, ACL, and record-rule workflows in an `erpobe_test*`
  database.
- [ ] NOT TESTED — Backend chat visual/responsive behavior and OWL asset loading.
- [ ] NOT TESTED — Odoo TransactionCase assistant service tests.

## Phase 2 dashboard slice

- [x] PASS — Student dashboard reads IPK/SKS from KHS and current course rows from
  active-year KRS; unavailable IPS is explicitly not computed.
- [x] PASS — Student grade-distribution chart renders from KHS values with Odoo
  Chart.js; no JS errors on dashboard load.
- [x] PASS — CPL dashboard only aggregates mapped CPMKs when every mapped CPMK and
  its assessment components have saved values; CPMK→CPL mapping is not weighted.
  The current student fixture shows the explicit empty state.
- [x] PASS — Lecturer dashboard uses assigned classes, approved KRS rows, grade
  component completeness, and stored course grades.
- [x] PASS — Lecturer dashboard displays 16 assigned courses/classes, 25 distinct
  students, 344 completed student-class assessments, zero incomplete assessments,
  and a rendered class-average chart for the development fixture.
- [x] PASS — Dashboard viewport overflow: student 1440×900, 1367×767, 767×1024,
  390×844, and 360×800; lecturer 1440×900 and 390×844.
- [x] PASS — Lecturer grade table stays inside its horizontal scroll container at
  mobile width; the document itself does not overflow. Portal navigation is
  horizontally scrollable on mobile without causing document overflow.
- [x] PASS — Odoo module upgrade and Chart.js/module HTTP asset checks.
- [x] PASS — Permanent student before/after, tablet, and mobile screenshots saved
  under `docs/screenshots/`; lecturer after/mobile screenshots saved.
- [ ] NOT TESTED — Lecturer before screenshot; no baseline capture was available.
- [ ] NOT TESTED — KHS detail, CPL detail/analytics, grade-input performance and
  audit-reason flows; covered by later Phase 2 slices, not this dashboard change.

## Phase 1 — shared navigation and responsive shell

- [x] PASS — Portal lecturer dashboard route returns HTTP 200; desktop navigation
  and breadcrumb render at the measured 1440×900 CSS viewport with no document
  horizontal overflow.
- [x] PASS — Grade-entry route returns HTTP 200, marks `Kelas` active, and shows
  the nested breadcrumb `Beranda / Pengajaran / Kelas / Input nilai`.
- [x] PASS — Lecturer mobile menu opens at 390×844 and exposes role navigation,
  profile/settings, public site, and logout links without document overflow.
- [x] PASS — Public mobile menu opens at 390×844 and 360×800; both measured
  viewports have no document horizontal overflow.
- [x] PASS — Lecturer account dropdown opens with profile/settings and logout.
- [x] PASS — Clicking logout returns to `/`; a later `/my/triton` request redirects
  to the login page.
- [x] PASS — Official logo static URL returns HTTP 200 `image/jpeg`; portal
  navbar/footer use the same static asset.
- [x] PASS — `erpobe` module upgrade completed after a readable database backup.
  The upgrade loaded the whole module, including pending RPS/grade model changes
  outside this phase; those source files were not edited in this follow-up.
- [ ] NOT TESTED — Student-role shell and navigation; the authenticated browser
  account used for this run was a lecturer.
- [ ] BLOCKED — Permanent Phase 1 before/after screenshots. Captures rendered
  only a narrow page slice despite the requested viewport; unreliable files
  were discarded.
- [ ] NOT TESTED — Desktop visual comparison and student-role shell screenshot.
