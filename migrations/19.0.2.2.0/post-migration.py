from odoo import SUPERUSER_ID, api


MODULE = "erpobe"
PROGRAM_MODEL = "erpobe.master.prodi"
LEGACY_XMLID = "legacy_prodi_ti_19_0_2_2_0"


def _delete_program_records(env, program):
    candidates = set()
    for model_name, model in env.registry.models.items():
        if (
            not model_name.startswith("erpobe.")
            or model_name == PROGRAM_MODEL
            or not model._auto
            or model._transient
        ):
            continue
        field = model._fields.get("prodi_id")
        if field and field.type == "many2one" and field.comodel_name == PROGRAM_MODEL:
            if env[model_name].search([("prodi_id", "=", program.id)], limit=1):
                candidates.add(model_name)

    children = {name: set() for name in candidates}
    parents = {name: set() for name in candidates}
    for child_name in candidates:
        for field in env[child_name]._fields.values():
            parent_name = field.comodel_name
            if (
                field.type == "many2one"
                and field.ondelete != "set null"
                and parent_name in candidates
                and parent_name != child_name
            ):
                parents[child_name].add(parent_name)
                children[parent_name].add(child_name)

    ready = sorted(name for name, dependents in children.items() if not dependents)
    ordered = []
    while ready:
        child_name = ready.pop(0)
        ordered.append(child_name)
        for parent_name in sorted(parents[child_name]):
            children[parent_name].remove(child_name)
            if (
                not children[parent_name]
                and parent_name not in ordered
                and parent_name not in ready
            ):
                ready.append(parent_name)
                ready.sort()

    if len(ordered) != len(candidates):
        remaining = sorted(candidates - set(ordered))
        raise ValueError(
            "Cannot safely remove program records with cyclic relations: "
            + ", ".join(remaining)
        )

    for model_name in ordered:
        env[model_name].search([("prodi_id", "=", program.id)]).unlink()


def _remove_program_memberships(env, program):
    dosens = env["erpobe.master.dosen"].search(
        [("prodi_ids", "in", [program.id])]
    )
    exclusive_dosens = dosens.filtered(
        lambda record: set(record.prodi_ids.ids) == {program.id}
    )
    if exclusive_dosens:
        exclusive_dosens.unlink()
    remaining_dosens = dosens - exclusive_dosens
    if remaining_dosens:
        remaining_dosens.write({"prodi_ids": [(3, program.id)]})

    users = env["res.users"].search(
        [("erpobe_prodi_ids", "in", [program.id])]
    )
    protected_user_ids = {
        SUPERUSER_ID,
        env.ref("base.user_admin").id,
        env.ref("base.public_user").id,
    }
    exclusive_users = users.filtered(
        lambda user: (
            set(user.erpobe_prodi_ids.ids) == {program.id}
            and user.id not in protected_user_ids
        )
    )
    partners = exclusive_users.mapped("partner_id")
    if exclusive_users:
        exclusive_users.unlink()
    for partner in partners.exists():
        if not partner.user_ids:
            partner.unlink()

    remaining_users = users - exclusive_users
    if remaining_users:
        remaining_users.write({"erpobe_prodi_ids": [(3, program.id)]})


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    legacy_xmlid = env["ir.model.data"].search(
        [("module", "=", MODULE), ("name", "=", LEGACY_XMLID)], limit=1
    )
    if not legacy_xmlid or legacy_xmlid.model != PROGRAM_MODEL:
        return

    program = env[PROGRAM_MODEL].browse(legacy_xmlid.res_id).exists()
    if not program:
        legacy_xmlid.unlink()
        return

    _delete_program_records(env, program)
    _remove_program_memberships(env, program)
    program.unlink()
    legacy_xmlid.unlink()
