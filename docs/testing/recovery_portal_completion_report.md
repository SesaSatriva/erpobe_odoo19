# Recovery and Portal Completion Report

## Recovery scope

The existing module was audited from the actual working tree. The recovered changes
preserved:

- `_assessment_summary` in `controllers/portal_base.py`;
- the lecturer dashboard/detail assessment consistency;
- the separation of `origin = actual` and `origin = simulated`;
- KHS and RPS XLSX exports;
- existing Odoo PDF KHS and RPS reports;
- the existing 42,875 component grade records.

No Odoo core source file was changed.

## Verified data

The development database still contains:

- 42,875 total component grade records;
- 42,805 simulated records;
- 70 actual records;
- 42,875 records marked `is_graded`;
- no deletion or grade-value rewrite.

## Recovered and completed changes

### Lecturer portal

- RPS list with search, sort, pagination, and academic filters;
- authorized RPS create/edit/detail/copy/finalize workflow;
- RPS final lock protection;
- class list with complete, incomplete, and not-started assessment counts;
- assessment detail status filters using `_assessment_summary`.

### Student course and CPMK monitoring

- course table with RPS and component/CPMK summary;
- owned course detail route;
- CPMK detail route;
- component-to-CPMK traceability;
- existing computed CPMK value and target display;
- actual/simulated/legacy component labels;
- read-only final RPS detail template.

### Student CPL monitoring

- CPL table with actual category labels;
- owned CPL detail route;
- mapped course and CPMK traceability;
- valid and incomplete CPMK counts;
- CPMK value, target, and course weight display;
- existing CPL aggregate formula disclosed without frontend recalculation.

### Public homepage

- corrected institutional CPL average;
- valid CPL count;
- CPL count meeting target;
- CPL count below target;
- unavailable state when no valid aggregate is present;
- public aggregate scope remains free of individual identities.

## Validation

Passed:

- Python compilation;
- all website XML parsing;
- 4 focused UI template tests;
- 5 existing route/report regression tests;
- isolated database smoke test in `erpobe_test_portal_20261126`;
- browser render of public homepage, course detail, CPMK detail, CPL detail,
  and read-only RPS detail;
- cross-student RPS access returned HTTP 403.

## Limitations

Aggregate KHS and RPS import remains intentionally unimplemented. The existing
XLSX/PDF exports remain in place. The public homepage currently uses available
valid aggregate data from the existing comparison scope and does not expose
individual student values.
