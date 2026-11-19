# TRITON RPS & Assessment Engine — Phase 1 Audit and Proposed Architecture

**Status:** Phase 1 (audit and design only)  
**Project:** `erpobe`, Odoo 19  
**Audit date:** 2026-11-20  
**Scope:** Existing model, calculation, access, controller, view, fixture and test paths. No production code or database changes were made.

## 1. Executive summary

TRITON already has the core entities for RPS, CPMK/CPL, component scores, computed CPMK/MK/CPL results, KRS and KHS. The rebuild should extend and reconnect these entities rather than introduce parallel grade or RPS systems.

The current implementation does not yet satisfy the requested academic semantics:

1. `erpobe.akademik.komponen` is a global, effectively read-only catalog whose required `tipe` is hard-coded to **Kognitif** or **Partisipatif**. An RPS selects catalog records through a Many2many, but does not own editable name/description/weight snapshots.
2. `erpobe.bobot.komponen.cpmk` stores allocation per CPMK, validated as 100% **per CPMK**. It does not configure each assessment component's overall contribution to the course, nor allocate one component's contribution across its measured CPMKs.
3. CPMK results select RPS weights by newest RPS for a course, while scores are gathered across the student's course attempts. Result records do not identify the RPS version or term used.
4. CPMK→CPL is currently calculated using `bobot_cpmk_cpl`; this is a weighted relationship, not a mapping-only relationship.
5. The fixture seeder's score function is deterministic and bounded but uses ten repeating student bands and a small periodic offset. It has no random-seed argument, and generated component-score records are not individually marked as simulated.
6. Final RPS records and their child configuration rows are protected against edits. However, the score-to-RPS-version link needed to make that protection meaningful for historical calculations is absent.

**Recommendation:** retain existing grade/KHS/KRS models and keep the global component model as the catalog; add a per-RPS component snapshot and connect grades to that snapshot. Preserve the existing weighted formula as an explicit legacy path for old records. Do not silently convert old configurations or rewrite old grades.

## 2. Existing models and responsibilities

| Model | Responsibility and relevant fields | Current relationships / observations |
|---|---|---|
| `erpobe.master.matakuliah` | Course identity, code, SKS, curriculum semester, program, coordinator/teaching team, prerequisites. | Owns CPMK and RPS records. `rps_ids` can span offers/academic years. |
| `erpobe.akademik.tahunajaran` | Academic year, term (`ganjil`, `genap`, `pendek`) and single-active-year flag. | `penawaran` and RPS obtain their year through their offer line. |
| `erpobe.akademik.penawaran` / `.line` | Semester offering and course section; class/rombel, teachers, schedule, students and per-line RPS versions. | `.line.latest_rps_id` sorts by `(version, id)` and can therefore point at a newer draft/review version instead of a previous final one. |
| `erpobe.akademik.rps` | Course/offer reference, version, source version, status (`draft`, `review`, `final`), component and CPMK/CPL selections, learning activities and rubrics. | `cpmk_ids` is computed from all CPMKs of the course; `cpl_ids` is derived from CPMK mappings. Owns the three existing weight tables. |
| `erpobe.akademik.cpmk` | Course learning outcome, description, indicator and target. | Belongs to a course; maps to CPL through `erpobe.akademik.cpl.mk.cpmk`. |
| `erpobe.akademik.cpl` / `.cpl.mk.cpmk` | Program learning outcome and direct CPL↔CPMK mapping. | The bridge is unique per `(cpl_id, cpmk_id)` and checks program consistency. This is the appropriate mapping relation to retain. |
| `erpobe.akademik.komponen` | Global assessment component catalog: `name`, required `tipe`, `aktif`, `color`. | `name`, `tipe`, `aktif` are declared read-only in Python; `tipe` is fixed to Kognitif/Partisipatif. An RPS links to the master, not to a frozen per-RPS copy. |
| `erpobe.bobot.komponen.cpmk` | RPS-specific component↔CPMK rows and `bobot_komponen_cpmk`. | Has unique `(rps_id, komponen_penilaian, cpmk_id)` and 0–100 per-row SQL checks. Current group total is 100% per CPMK. |
| `erpobe.bobot.cpmk.mk` | RPS-specific CPMK contribution to the course. | Current course total is validated as 100%; used by the MK calculation. |
| `erpobe.bobot.cpmk.cpl` | RPS-specific CPMK↔CPL row with `bobot_cpmk_cpl`. | Current implementation adds weights to the direct mapping and uses them in CPL scores. |
| `erpobe.akademik.krs` / `.line` | Student semester registration and course enrollment. | A line points to an offered course and student; its offer line determines class and academic period. |
| `erpobe.input.nilai` / `erpobe.grade.komponen` | Class grade input and individual component score. | `grade.komponen` points to KRS line and global component; unique per `(krs_line_id, komponen_id)`. It currently has no FK to an RPS or RPS version and no backend 0–100 constraint. |
| `erpobe.grade.komponen.audit` | Immutable history of component score changes. | Captures writes and nonzero initial values; preserves old/new values, actor and reason. |
| `erpobe.grade.cpmk` | Stored computed student CPMK score and target status. | Unique per `(mahasiswa_id, cpmk_id)`; stores no term or RPS version. |
| `erpobe.grade.mk` | Stored computed course score. | Unique per `(mahasiswa_id, mk_id)`; stores no semester attempt or RPS version. |
| `erpobe.grade.cpl` | Stored computed student CPL score and target status. | Unique per `(mahasiswa_id, cpl_id)`; aggregates across mapped CPMK grade records. |
| `erpobe.master.grade` | Grade-letter/grade-point thresholds used to convert numeric MK values for KHS. | KHS line computation depends on these ranges; preserve existing grade bands during calculation changes. |
| `erpobe.report.khs` and line models | Student transcript snapshot of MK/CPMK/CPL grades, GPA and passed credits. | One report per student. Sync copies all existing grade records; `tahun_ajaran_id` is not used to scope its grade fetch. GPA logic takes the best grade for a repeated course code, although the current unique student+course grade constraint limits representing repeated attempts. |
| `erpobe.akademik.kurikulum`, `erpobe.master.rombel` | Curriculum and student cohort/class group. | Curriculum links courses/students; rombel links students, offers and program. |
| `erpobe.akademik.subcpmk` / `erpobe.grade.subcpmk` | Per-RPS sub-outcomes and results. | Actively used by RPS activities, seeder and tests. This is legacy data to handle carefully if the new workflow removes Sub-CPMK use. |
| `erpobe.akademik.fixture.source` | General provenance record (`official`, `mixed`, `dummy`, `derived`) for fixture-created records. | Can help preserve provenance, but component-grade records created by the seeder are not individually marked in its score-upsert path. |

Primary source files: [model imports](../models/__init__.py), [RPS and activity/rubric models](../models/akademik_rps.py), [component catalog](../models/akademik_komponen.py), [weight tables](../models/bobot_komponen_cpmk.py), [CPL mapping](../models/akademik_cpl_mk_cpmk.py), [grade input and audit](../models/grade.py), [CPMK scores](../models/grade_cpmk.py), [MK scores](../models/grade_mk.py), [CPL scores](../models/grade_cpl.py), [KHS](../models/report_khs.py), [KRS](../models/akademik_krs.py), [offer and class](../models/akademik_penawaran.py), [academic year](../models/akademik_tahunajaran.py), and [fixture/provenance models](../models/academic_fixture.py).

## 3. Current data flow and formulas

```text
Course → CPMKs → direct CPL↔CPMK mapping
Offer line → RPS version → selected global components + three RPS weight tables
Approved KRS line → actual component grade → computed CPMK → computed MK / computed CPL
Computed MK, CPMK, CPL → KHS snapshot
```

### Current implementation

- **Assessment component→CPMK:** for a CPMK, the implementation adds each selected component score multiplied by `bobot_komponen_cpmk / 100`. The configured weights sum to 100 per CPMK. Missing component scores are treated as `0`.
- **CPMK→MK:** adds CPMK score multiplied by `bobot_cpmk_mk / 100`, with current CPMK→MK weights expected to total 100.
- **CPMK→CPL:** for mapped CPMKs with a student grade, computes `Σ(CPMK score × bobot_cpmk_cpl) / Σ(bobot_cpmk_cpl)`. Unassessed CPMKs are omitted and the denominator is renormalized.
- **KHS GPA:** uses each course code's highest grade point; GPA is `Σ(SKS × grade point) / Σ(SKS)` over the selected best-grade lines. Passed credits are counted only where grade point is greater than zero.
- **RPS finalization:** `erpobe.weight.validation` checks group totals against 100% with 0.01 tolerance. Drafts can retain incomplete weights; finalization is the backend gate. The relevant tables have per-row range checks, but aggregate totals are not database constraints.

### Calculation and traceability risks

1. `grade.cpmk` selects RPS records by course and sorts by descending ID; its weight map is not scoped to the student's KRS line, offer line, academic year or exact RPS. Component grades are also gathered across course attempts and keyed only by student/course/component.
2. `grade.mk` similarly builds weights from RPS records across the course and student CPMK grades, not a specific enrollment/version.
3. `grade.cpl` searches `bobot.cpmk.cpl` by CPL across RPS records, not by an academic period or RPS version. Duplicate CPMK/CPL pairs from different RPS records can overwrite the same in-memory map entry.
4. Compute dependencies primarily watch score fields. RPS weight edits are not explicit dependencies of the stored student grade fields, so a change may not recompute all affected results unless the orchestrator explicitly forces recomputation.
5. The manual score controller checks 0–100, but the grade model itself has no equivalent range constraint; ORM imports or other server-side callers can bypass that controller validation.
6. `input.nilai`'s onchange builds rows from all globally active components, not the RPS configuration. The newer portal grade route does use the selected RPS components; the two input paths can therefore disagree.
7. Component grades are unique by `(krs_line_id, komponen_id)`. A per-RPS component snapshot may require a new uniqueness key; preserve the existing one for legacy records while introducing the new key.
8. CPL evaluation currently has an explicit weighted formula that conflicts with the requested mapping-only CPMK→CPL semantics. The public methodology text also describes the weighted formula and must be kept in sync when a later implementation is approved.
9. Final RPS configuration is protected by `erpobe.rps.lock.mixin`; `copy()` creates a separate review version. The protection does not freeze the grade formula inputs historically because score records are not linked to the exact RPS version.

## 4. Controllers, access, views and tests audited

- **Portal RPS / grades:** `controllers/portal_dosen.py` exposes list/create/edit/copy/finalize and class grade-input routes. It checks teacher-to-course assignment through `portal_base.py`, then uses `sudo()` for reads/writes. Score POST validates 0–100 and invokes the calculation/KHS orchestrator. RPS POST writes description, media, selected master components and weight rows; it does not create custom component master records.
- **Backend access:** `ir.model.access.csv` grants lecturers RPS create/write but not unlink; students can read RPS. Teacher access to grade component records is program-scoped. Grade CPMK/MK/CPL access differs by role and uses student-owned rules. Portal routes rely on explicit teacher ownership checks because they use elevated access.
- **RPS views/PDF:** backend RPS form has tabs for learning outcomes, selected components, activities, rubrics and weight tables. It exposes Sub-CPMK. The portal RPS editor lists master components and separate weight tables; it has no per-RPS snapshot/custom component, component-total summary, allocation matrix or completion progress. QWeb PDF actions exist for RPS and KHS; the RPS PDF currently lists selected component names but not component weights or allocation.
- **Seed/simulation:** `fixture_seeder.py` uses fixed student bands `(93, 88, 83, 79, 75, 71, 68, 64, 59, 54)` by student index, then a periodic offset from student/course/component indices, clamped to 40–99. It is reproducible because it is deterministic, but does not accept a random seed and creates strongly patterned scores. The general fixture-source model exists; generated `grade.komponen` records are not marked in the component-grade creation loop.
- **Current relevant tests:** `test_weight_validation.py`, `test_rps_versioning.py`, `test_triton_workflows.py` and `test_academic_fixture.py` cover portions of weight checks, final-RPS copy protection, grade formulas, KHS IPK and fixture generation. Existing tests encode weighted CPMK→CPL and Sub-CPMK usage. They do not establish the requested new component snapshots, version-pinned grade lineage, actual-vs-dummy isolation or a seeded statistical distribution.

Relevant files: [portal grade/RPS controller](../controllers/portal_dosen.py), [portal authorization helper](../controllers/portal_base.py), [ACL](../security/ir.model.access.csv), [record rules](../security/rules.xml), [backend RPS form](../views/akademik_rps_views.xml), [portal RPS editor](../views/website/portal/teacher/portal_rps_edit.xml), [RPS/KHS PDF](../views/triton_reports.xml), and [existing academic tests](../tests/).

## 5. Proposed model design (not implemented)

### Reuse existing models

- Keep `erpobe.akademik.rps`, CPMK/CPL, KRS, grade, KHS, offer and year/class models.
- Keep `erpobe.akademik.komponen` as the reusable catalog; remove the fixed cognitive/participative classification from the primary workflow. Catalog changes must not mutate already-used RPS records.
- Keep `erpobe.bobot.komponen.cpmk` as the component-to-CPMK allocation table where practical, extending it to reference the per-RPS component snapshot instead of only the global master. Retain the old reference/data path for legacy RPS until migration is verified.
- Keep `grade.komponen.audit` as the score-change ledger. Extend provenance for actual versus simulated grades rather than making a parallel scoring model.

### Add per-RPS configuration and lineage

Add a child configuration record (proposed model name: `erpobe.akademik.rps.komponen`) with:

- required RPS reference;
- optional catalog/master reference (empty for a lecturer-created component);
- copied name and description, so edits to a master never alter a finalized RPS;
- component weight in the final course grade;
- active/inactive state before finalization;
- explicit source/provenance and ordering fields as needed.

Each component-to-CPMK allocation references this RPS component record and an allocation percentage. Add an exact RPS version reference to the stored component grade (and, where needed, the derived result lineage). Introduce a version-aware uniqueness key for new grade records while preserving the old uniqueness rule for legacy rows. Resolve the RPS from the KRS/offer line for new score entry; never choose the "latest RPS for course" during a historical recompute.

### Backend validation rules

1. Score values are constrained to 0–100 at the model/service boundary, regardless of controller or import path.
2. Active component weights on one RPS total 100% (0.01 tolerance, consistent with current helper).
3. Each active component allocated to CPMKs has allocation totals of 100%; all CPMKs belong to the same course as the RPS.
4. Validate aggregate totals at RPS review/finalization and through server-side operations. Drafts may be incomplete. SQL checks remain appropriate for per-row ranges/uniqueness; aggregate totals require ORM/service validation.
5. Disable/add/remove components and edit allocations while draft/review only. Once scores exist for the RPS version, reject in-place configuration changes; create a new RPS version and leave prior grades/configuration intact.
6. A missing component score must not silently become zero. The design should distinguish missing/ungraded from an actual zero and expose provisional/incomplete status. A finalized academic grade should only be published under an explicitly agreed completeness rule.

### Proposed formulas and double-count prevention

Let `w_i` be component `i`'s percentage of the course grade, `a_ij` the percentage of component `i` allocated to CPMK `j`, and `s_i` the student's component score (0–100). The component weights total 100%; allocations for each component total 100%.

- **Course final score:** `Σ(s_i × w_i / 100)` over required, graded, active components. This is the only route from component weights to final MK score; do not sum CPMK attributions again into the same final MK score.
- **CPMK achievement:** `Σ(s_i × w_i × a_ij) / Σ(w_i × a_ij)` over graded components that measure CPMK `j`. This normalizes a CPMK's attribution against the component/course weight assigned to it and keeps its score on a 0–100 scale. Preserve component-grade IDs and allocation rows as provenance for every result.
- **CPL evaluation (proposal):** use the CPL↔CPMK mapping only to select distinct, assessed CPMKs; calculate an unweighted mean of those CPMK achievements for the chosen student/period/cohort. Do not persist or apply CPMK→CPL weights. Confirm the aggregation population/period and missing-CPMK policy before implementation.

The CPMK score is an attribution/result, not an additional component in the final course score. This avoids counting the same component score once through the component total and again through CPMK totals.

### Academic versus dummy data

Separate the deterministic academic calculation service from a test/simulation generator. The generator should accept a seed and produce reproducible but diverse student profiles (e.g. strength/weakness dimensions plus component-specific deviations), clamp all scores to the valid range, and mark every generated score explicitly as simulated. Reports, KHS, CPL evaluation and dashboards must default to actual records or clearly separate/filter simulation records. Simulation must never overwrite actual grades.

## 6. Compatibility and data migration strategy

1. **Add first:** deploy new per-RPS component snapshots, lineage and origin fields additively. Do not rename/drop current fields or constraints in the first schema migration.
2. **Preserve legacy semantics:** identify existing RPS versions and grades as legacy calculation schema. Preserve their current allocations, computed results and audit rows. Do not infer missing overall component weights or silently translate CPMK→CPL weights.
3. **New-version transition:** new RPS versions use the new component-weight and component→CPMK-allocation rules. Copy from an old RPS as a draft/review snapshot with an explicit conversion/confirmation step; no automatic finalization.
4. **Backfill cautiously:** create per-RPS component snapshots for old RPS records by copying selected master names/descriptions and preserving old master IDs. Link old allocation/score records only where identity and academic period can be established unambiguously; report unresolved/ambiguous records for review.
5. **Compatibility window:** keep legacy columns and read paths until reconciliation proves parity for a sampled set of historical grade, KHS and CPL results. Only then consider a later migration to remove obsolete fields/tables.
6. **Sub-CPMK:** stop creating/editing it in the new RPS workflow. Keep existing Sub-CPMK records and their score relations readable/exportable as legacy history until references and reports are safely migrated; do not cascade-delete them as part of this phase.
7. **Reconcile:** compare pre/post values for component grades, CPMK, MK, CPL and KHS before making the new calculation path the default. Keep a rollback/backup and run module upgrade/tests on a non-production copy first.

## 7. Impact and risks for later phases

| Area | Expected impact | Main risk / control |
|---|---|---|
| RPS and component catalog | New per-RPS rows, editable custom labels/descriptions and active flags. | Master edits must not change snapshots; preserve old many-to-many references for legacy. |
| Component allocation and grade models | Point allocations and new scores to the exact RPS component/version. | Existing score uniqueness is component-master-based and has no term dimension; deduplicate/backfill carefully. |
| CPMK/MK/CPL calculations | Replace cross-RPS "latest" lookup with exact enrollment/version; direct component total for MK; mapping-only CPL aggregation. | Stored computes and callers/forced recomputes must all use the same service and provenance. |
| KHS and repeated enrollments | Need a defined per-term attempt/source relationship before KHS snapshotting. | Current one-grade-per-student+course key cannot represent repeated attempts; GPA best-grade behavior and KHS period label need a policy. |
| KRS, offer line, year and rombel | Provide the academic-period context for the RPS selected for each enrollment. | Historical KRS lines must not begin using a newer RPS version after an upgrade. |
| Controllers, backend/portal views, PDF | Add custom component editing, allocation matrix, progress/summary and printable weight/mapping details. | Portal routes use `sudo`; retain strict teacher-to-offer authorization and test cross-program access. |
| CPL dashboard/public methodology | Update aggregation and descriptions after mapping-only formula is approved. | Existing explanatory public pages currently promise a weighted CPL formula. |
| Security/access | Add ACL and program-scoped rules for new snapshot/allocation fields/models. | Student read scope and teacher write scope must remain least-privilege, including elevated portal operations. |
| Fixture/seeder/tests | Replace repetitive score logic and mark each generated score; update tests that currently assert weighted CPL/Sub-CPMK. | Fixture seed is versioned and may skip rebuilding; migration/test data must not rewrite actual records. |

## 8. Phase 1 completion record

- **Files created:** `docs/TRITON_RPS_MODEL_ARCHITECTURE.md` (this audit/design report).
- **Production files changed:** none.
- **Models/relations affected by future phases:** RPS, component master, proposed RPS component snapshot, component↔CPMK allocation, component grades/audit, computed CPMK/MK/CPL grades, KHS, KRS/offer/year/class, fixture provenance and Sub-CPMK legacy models.
- **Testing/upgrade:** no Odoo tests or module upgrade run. Phase 1 made no implementation changes; upgrading database `erpobe` before design approval would be an out-of-phase schema/data change. No live database result is claimed.
- **Screenshot:** none; no UI was changed or tested.
- **Working-tree coordination:** the module repository was on `main` with pre-existing edits in portal navigation and SCSS (`views/website/components/*navigation.xml`, `static/src/scss/_tokens.scss`, `static/src/scss/components/*`, `static/src/scss/pages/_professional.scss`). These were not edited. Portal RPS/controller/view files are likely future overlap points and should be rechecked immediately before any later edit.
- **Not completed:** implementation, database migration, statistical simulation tests, live role/access tests, module upgrade, and UI/PDF validation are all deferred to later phases.

## 9. References

- [RPS models and lifecycle](../models/akademik_rps.py)
- [Assessment component master](../models/akademik_komponen.py)
- [Component-to-CPMK allocation](../models/bobot_komponen_cpmk.py)
- [Weight validation](../models/weight_validation.py)
- [CPMK-to-CPL mapping](../models/akademik_cpl_mk_cpmk.py)
- [Component scores and audit](../models/grade.py)
- [CPMK/MK/CPL calculation models](../models/grade_cpmk.py), [grade_mk.py](../models/grade_mk.py), [grade_cpl.py](../models/grade_cpl.py)
- [KHS snapshots and GPA](../models/report_khs.py)
- [Fixture seeder and score function](../models/fixture_seeder.py)
- [Existing weight/version/workflow tests](../tests/test_weight_validation.py), [test_rps_versioning.py](../tests/test_rps_versioning.py), [test_triton_workflows.py](../tests/test_triton_workflows.py), [test_academic_fixture.py](../tests/test_academic_fixture.py)
