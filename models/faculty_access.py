from odoo.exceptions import AccessError


def _check_prodi_write_access(recordset, values):
    if not ({"prodi_id", "prodi_ids"} & values.keys()) or recordset.env.su:
        return
    user = recordset.env.user
    if user.has_group("erpobe.group_superadmin") or user.has_group(
        "base.group_system"
    ):
        return
    allowed_ids = set(user.erpobe_prodi_ids.ids)
    if "prodi_id" in values and values["prodi_id"] not in allowed_ids:
        raise AccessError("Anda tidak dapat memindahkan data ke prodi lain.")
    if "prodi_ids" in values:
        prodi_ids = set(recordset.mapped("prodi_ids").ids)
        for command in values["prodi_ids"]:
            operation = command[0]
            if operation == 6:
                prodi_ids = set(command[2])
            elif operation == 4:
                prodi_ids.add(command[1])
            elif operation == 3:
                prodi_ids.discard(command[1])
            elif operation == 5:
                prodi_ids.clear()
        if not prodi_ids <= allowed_ids:
            raise AccessError("Anda tidak dapat menetapkan dosen ke prodi lain.")
