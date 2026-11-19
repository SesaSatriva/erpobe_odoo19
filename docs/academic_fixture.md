# Academic test fixture

The academic cohort is demo data, not official university data. It is loaded
only when Odoo loads the module's `demo` section. Keep demo loading disabled for
production databases.

## What is generated

`tools/generate_demo_data.py` writes the small bootstrap XML files. During demo
loading, `erpobe.fixture.seeder.load_2022_cohort` creates an idempotent fixture
for Teknik Industri, Teknik Elektro, Teknik Sipil, and Teknik Manufaktur:

- 25 explicitly simulated students per program, assigned to the 2022 A/B
  rombels, with generated NIMs, email addresses, and portal accounts.
- Teacher profiles based on the public-name summaries in
  `docs/data_prodi.md`: 13 for Industri, 14 for Elektro, 14 for Manufaktur,
  and 6 simulated profiles for Sipil. Muhamad Ali is one shared profile for
  Industri and Elektro. NIP and email values are simulated.
- Curriculum, course offerings, student KRS records, four assessment
  components, numeric component scores, computed CPMK/MK/CPL results, and
  KHS reports.
- Two simulated CPMKs per course and 16 weekly Sub-CPMK/activity records per
  RPS. RPS weights and rubrics are complete for testing and marked final, but
  this does not mean they were reviewed or approved by a program.

## Source and simulation boundaries

`docs/data_prodi.md` contains paraphrases and records limitations in the
public sources. CPL text is not copied as authoritative wording. The fixture
marks generated curriculum details, codes, all per-course SKS values, indicators,
rubrics, all student identities and scores, and incomplete semester/elective
information as simulated. Civil semesters 6–8 and the unavailable Civil CPLs
are entirely simulated. Confirm curriculum applicability and source documents
with each program before using any information for academic decisions,
accreditation, or official reporting.

The admin-only **Sumber Data Fixture** menu exposes source type, note, and
reference URL for the fixture's source records. Grade values are generated
test measurements; they are not student records or official assessment data.

## Safety and repeatability

Generated records use `fixture_*` external IDs and are updated in place when
the demo seeder runs again. The seeder does not delete records or clean up
unmarked data. Install and update this fixture only in a disposable database
whose name starts with `erpobe_test`; do not load module demo data into a
production database. Reconcile or remove obsolete fixture records only through
a reviewed migration, never by deleting unrelated records.
