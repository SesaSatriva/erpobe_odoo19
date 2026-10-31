# Upgrade notes: 19.0.2.1.0

The pre-migration step snapshots non-empty faculty dean assignments in
`erpobe_master_fakultas_dekan_archive`. The ORM then removes `dekan_id`; the
snapshot is retained so an administrator can restore the old release without
losing assignments.

The post-migration step drops the obsolete faculty column and links an old RPS
only when its course has exactly one offering line and exactly one legacy RPS.
Backfilled RPS records are marked `Perlu Ditinjau`, never `Final`. Courses with
multiple offers or multiple legacy RPS records remain unlinked for manual
assignment; ambiguous links are not guessed.

Offers are assigned a program only when all their existing lines belong to the
same program. Multi-program or empty offers remain without a program and must be
reviewed before they become visible to program-scoped users.

For a manual downgrade, first downgrade the module code/schema so
`erpobe_master_fakultas.dekan_id` exists again, then run `rollback.rollback(cr)`
inside an Odoo database migration transaction. Assignments whose former lecturer
record no longer exists are intentionally not restored.

RPS records created before this release have no academic-year or offering
identity. They cannot be backfilled unambiguously when a course has more than one
historical offering; those records must be reviewed manually before assigning
them to a specific offering.
