# Academic fixture data

The academic fixture is loaded as required module data during installation and
module upgrade, even when Odoo demo loading is disabled. It includes simulated
academic records and is not official university data.

## What is generated

`tools/generate_demo_data.py` writes the bootstrap XML files. The module data
loader calls `erpobe.fixture.seeder.load_2022_cohort`, which creates an
idempotent fixture for Teknik Industri, Teknik Elektro, Teknik Sipil, and
Teknik Manufaktur:

- 25 explicitly simulated students per program, assigned to the 2022 A/B
  rombels, with generated NIMs, email addresses, and portal accounts.
- Teacher profiles based on the public-name summaries in
  `docs/data_prodi.md`: 13 for Industri, 14 for Elektro, 14 for Manufaktur,
  and 6 simulated profiles for Sipil. Muhamad Ali is one shared profile for
  Industri and Elektro. NIP and email values are simulated.
- Curriculum, course offerings, student KRS records, four assessment
  components, numeric component scores, computed CPMK/MK/CPL results, and
  KHS reports.
- Two simulated CPMKs per course, linked directly to CPLs, and 16 weekly
  course-activity records mapped directly to CPMKs. Each RPS has component
  weights totaling 100% and component-to-CPMK allocations totaling 100%.
  Legacy sub-outcome records are not created or used by the current seeder. RPS weights and rubrics are
  marked final for testing, but this does not mean they were reviewed or
  approved by a program.

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
the seeder runs again. The seeder does not delete records or clean up unmarked
data. Because this fixture is required module data, every database that installs
or upgrades `erpobe` receives the simulated cohort, test accounts, KRS, grades,
and reports. Do not install or upgrade this module in a production database
until the fixture is replaced with approved official data or separated from
required module data. Validate changes in a disposable database whose name
starts with `erpobe_test`. Reconcile or remove obsolete fixture records only
through a reviewed migration, never by deleting unrelated records.

The initial fixture load creates tens of thousands of assessment records and can
take several minutes. Upgrade an existing database from the Odoo CLI with
`--stop-after-init` rather than through the UI request, which may exceed the
HTTP worker time limit.
