# Assessment Consistency Audit

## Scope

This audit compares the lecturer dashboard and the lecturer assessment detail page
without changing or regenerating existing grade records.

## Source of truth

The assessment detail page uses one approved KRS attempt per student and the exact
latest final RPS for the offered class. A student is complete only when every RPS
component has a grade record that is:

- linked to the exact RPS;
- marked `is_graded = True`;
- marked `origin = actual`.

The following states are kept separate:

- **Not started**: no component grade record exists for the exact RPS/class attempt.
- **Not graded**: a grade record exists, but `is_graded = False`.
- **Incomplete**: at least one required RPS component is missing or not graded.
- **Complete**: all required RPS components are graded actual values.
- **Unlinked**: a grade record is not linked to an RPS.
- **Simulated**: an `is_graded = True` generated fixture record with `origin = simulated`;
  it is not counted as an actual lecturer assessment.

A value of `0` is valid and is counted as graded because completion is based on
`is_graded`, `origin`, RPS linkage, and component linkage, not on a truthy value.

## Data audit result

The development database audit found:

- 42,875 total component grade records;
- 42,875 records marked `is_graded`;
- 42,805 simulated records;
- 70 actual records;
- no records marked ungraded.

The generated fixture records are real grade records but use `origin = simulated`.
They are therefore excluded from the dashboard's and detail page's "actual assessment
complete" definition, just as they were previously excluded by the detail page.

No generated data was deleted or changed during this audit.

## Root cause

The lecturer dashboard previously collected every component ID found on any grade
record for any KRS attempt and did not filter by:

- exact RPS;
- `is_graded`;
- `origin = actual`;
- required RPS component membership.

This differed from the assessment detail page, which checks the exact RPS and
requires `is_graded = True` and `origin = actual`. The same data could therefore
appear complete on the dashboard while being incomplete on the detail page.

## Implemented correction

The dashboard and assessment detail page now use a shared `_assessment_summary`
calculation. It returns the exact approved-student set and exact RPS component set
for a class. The dashboard and detail filter classes and students with the same
granularity:

- complete;
- incomplete;
- not started;
- not graded.

Dashboard class rows expose counts for required components, complete students,
incomplete students, and not-started students. Each count links to the corresponding
assessment detail status filter.

## KHS and RPS document actions

KHS and RPS XLSX exports are available through owner/role-scoped portal routes.
Existing PDF reports remain the formal print mechanism. The implementation does not
replace IPS/IPK or OBE computations.

KHS and RPS aggregate imports are intentionally not enabled in this change. KHS is
computed from approved KRS and grade models, while RPS is a multi-relational,
versioned, lockable document. Importing aggregate Excel values would risk overwriting
computed or finalized academic data. A safe implementation requires a dedicated
validated preview/transaction wizard for source grade records or RPS relation sheets,
plus explicit confirmation for draft updates and revision creation.

## Public CPL average and student monitoring follow-up

The public institutional CPL average now uses the raw, deduplicated available CPL
grade values from the same eligible RPS/KRS scope used by the public comparison.
It no longer averages flattened category/program aggregates a second time.

Student course monitoring distinguishes actual component grades from simulated
fixture grades and shows component allocations to CPMK. CPL monitoring includes
CPMK-to-course and CPMK-to-course weight traceability. Student RPS detail uses a
separate read-only template rather than the lecturer management template.
