from odoo import Command, api, fields, models
from odoo.exceptions import AccessError, ValidationError
from odoo.fields import Domain


def _create_or_update_profile_user(profile, identifier, role_xmlid, identifier_field):
    partner = profile.partner_id
    if not partner.email:
        raise ValidationError(
            "Email wajib diisi pada kontak dosen/mahasiswa untuk membuat login."
        )

    users = profile.env["res.users"].sudo().with_context(active_test=False)
    user = users.search([("partner_id", "=", partner.id)], limit=1)
    values = {
        "name": profile.name,
        "login": partner.email,
        "password": identifier,
        identifier_field: identifier,
        "partner_id": partner.id,
        "active": True,
    }
    if user:
        user.write(values)
    else:
        user = users.with_context(skip_sync_user_type=True).create(
            {
                **values,
                "group_ids": [
                    Command.link(profile.env.ref("base.group_portal").id),
                    Command.link(profile.env.ref(role_xmlid).id),
                ],
            }
        )

    profile.user_id = user.id
    profile.env["res.users"].browse(user.id)._sync_user_type()

# RES USERS
class ResUsers(models.Model):
    _inherit = "res.users"

    nim = fields.Char(index=True)
    nip = fields.Char(index=True)
    erpobe_prodi_ids = fields.Many2many(
        "erpobe.master.prodi",
        "res_users_erpobe_prodi_rel",
        "user_id",
        "prodi_id",
        string="Program Studi",
    )

    _nim_unique = models.Constraint("UNIQUE (nim)", "NIM sudah digunakan.")
    _nip_unique = models.Constraint("UNIQUE (nip)", "NIP sudah digunakan.")

    @api.model
    def _get_login_domain(self, login):
        return (
            super()._get_login_domain(login)
            | Domain("nim", "=", login)
            | Domain("nip", "=", login)
        )

    # ===== GROUP LOGIC =====
    def _sync_user_type(self):
        if self.env.context.get("skip_sync_user_type"):
            return

        group_portal = self.env.ref("base.group_portal")
        group_internal = self.env.ref("base.group_user")
        group_dosen = self.env.ref("erpobe.group_dosen")
        group_mahasiswa = self.env.ref("erpobe.group_mahasiswa")
        group_admin = self.env.ref("erpobe.group_admin")
        group_superadmin = self.env.ref("erpobe.group_superadmin")
        group_system = self.env.ref("base.group_system")

        for user in self:
            user = user.sudo()
            current_groups = user.all_group_ids
            if current_groups & (group_admin | group_superadmin | group_system):
                continue

            dosen = self.env["erpobe.master.dosen"].sudo().search(
                [("user_id", "=", user.id)], limit=1
            )
            mahasiswa = self.env["erpobe.master.mahasiswa"].sudo().search(
                [("user_id", "=", user.id)], limit=1
            )
            if dosen:
                role_group = group_dosen
                profile_prodis = dosen.mapped("prodi_ids")
            elif mahasiswa:
                role_group = group_mahasiswa
                profile_prodis = mahasiswa.mapped("prodi_id")
            else:
                continue

            role_to_remove = group_mahasiswa if dosen else group_dosen
            group_commands = [
                Command.unlink(group.id)
                for group in (group_internal, role_to_remove)
                if group.id in user.group_ids.ids
            ]
            group_commands.extend(
                Command.link(group.id)
                for group in (group_portal, role_group)
                if group.id not in user.group_ids.ids
            )
            if group_commands:
                user.with_context(skip_sync_user_type=True).write(
                    {"group_ids": group_commands}
                )

            current_prodi_ids = set(user.erpobe_prodi_ids.ids)
            desired_prodi_ids = set(profile_prodis.ids)
            prodi_commands = [
                Command.unlink(faculty_id)
                for faculty_id in current_prodi_ids - desired_prodi_ids
            ]
            prodi_commands.extend(
                Command.link(faculty_id)
                for faculty_id in desired_prodi_ids - current_prodi_ids
            )
            if prodi_commands:
                user.with_context(skip_sync_user_type=True).write(
                    {"erpobe_prodi_ids": prodi_commands}
                )

    @api.model_create_multi
    def create(self, vals_list):
        if (
            any("erpobe_prodi_ids" in vals for vals in vals_list)
            and not self.env.su
            and not (
                self.env.user.has_group("erpobe.group_superadmin")
                or self.env.user.has_group("base.group_system")
            )
        ):
            raise AccessError(
                "Hanya Superadmin atau Administrator Settings yang dapat mengubah "
                "cakupan prodi."
            )
        users = super().create(vals_list)
        users._sync_user_type()
        return users

    def write(self, vals):
        if (
            "erpobe_prodi_ids" in vals
            and not self.env.su
            and not (
                self.env.user.has_group("erpobe.group_superadmin")
                or self.env.user.has_group("base.group_system")
            )
        ):
            raise AccessError(
                "Hanya Superadmin atau Administrator Settings yang dapat mengubah "
                "cakupan prodi."
            )
        res = super().write(vals)
        if "partner_id" in vals:
            self._sync_user_type()
        return res

# DOSEN
class ErpobeDosen(models.Model):
    _name = "erpobe.master.dosen"
    _description = "Dosen"
    _inherits = {"res.partner": "partner_id"}
    _rec_name = "name"

    user_id = fields.Many2one("res.users", readonly=True)
    partner_id = fields.Many2one("res.partner", required=True, ondelete="cascade")
    nip = fields.Char(required=True)

    _nip_unique = models.Constraint("UNIQUE (nip)", "NIP tidak boleh duplikat.")

    def write(self, vals):
        res = super().write(vals)
        for dosen in self:
            if not dosen.user_id:
                continue

            if "nip" in vals:
                dosen.partner_id.write({"ref": dosen.nip})
                dosen.user_id.sudo().with_context(skip_sync_user_type=True).write(
                    {"nip": dosen.nip}
                )

            if "name" in vals:
                dosen.user_id.sudo().with_context(skip_sync_user_type=True).write(
                    {"name": dosen.name}
                )
            if "prodi_ids" in vals:
                dosen.user_id._sync_user_type()
        return res

    def unlink(self):
        users = self.mapped("user_id")
        partners = users.mapped("partner_id")

        res = super().unlink()

        if users:
            users.sudo().unlink()

        for partner in partners:
            if not partner.sudo().user_ids:
                partner.sudo().unlink()

        return res

    @api.model_create_multi
    def create(self, vals_list):
        seen_nips = set()
        for vals in vals_list:
            nip = vals.get("nip")
            if nip and (
                nip in seen_nips
                or self.search_count([("nip", "=", nip)])
            ):
                raise ValidationError("NIP tidak boleh duplikat.")
            seen_nips.add(nip)
        records = super().create(vals_list)
        for dosen in records:
            if not dosen.email:
                raise ValidationError(
                    "Email wajib diisi pada kontak dosen untuk membuat login."
                )
            dosen.partner_id.write({"ref": dosen.nip})
            dosen._create_or_update_user()

        return records

    def _create_or_update_user(self):
        for dosen in self:
            _create_or_update_profile_user(
                dosen, dosen.nip, "erpobe.group_dosen", "nip"
            )

# MAHASISWA
class ErpobeMahasiswa(models.Model):
    _name = "erpobe.master.mahasiswa"
    _description = "Mahasiswa"
    _inherits = {"res.partner": "partner_id"}
    _rec_name = "name"

    user_id = fields.Many2one("res.users", readonly=True)
    partner_id = fields.Many2one("res.partner", required=True, ondelete="cascade")
    nim = fields.Char(required=True)

    rombel_id = fields.Many2one("erpobe.master.rombel", required=True)
    angkatan = fields.Integer(related="rombel_id.angkatan", store=True, readonly=True)

    grade_komponen_ids = fields.One2many("erpobe.grade.komponen", "mahasiswa_id")
    grade_cpmk_ids = fields.One2many("erpobe.grade.cpmk", "mahasiswa_id")

    _nim_unique = models.Constraint("UNIQUE (nim)", "NIM tidak boleh duplikat.")

    def write(self, vals):
        res = super().write(vals)
        for mhs in self:
            if not mhs.user_id:
                continue

            if "nim" in vals:
                mhs.partner_id.write({"ref": mhs.nim})
                mhs.user_id.sudo().with_context(skip_sync_user_type=True).write(
                    {"nim": mhs.nim}
                )

            if "name" in vals:
                mhs.user_id.sudo().with_context(skip_sync_user_type=True).write(
                    {"name": mhs.name}
                )
            if "rombel_id" in vals:
                mhs.user_id._sync_user_type()
        return res

    def unlink(self):
        users = self.mapped("user_id")
        partners = users.mapped("partner_id")

        res = super().unlink()

        if users:
            users.sudo().unlink()

        for partner in partners:
            if not partner.sudo().user_ids:
                partner.sudo().unlink()

        return res

    @api.model_create_multi
    def create(self, vals_list):
        seen_nims = set()
        for vals in vals_list:
            nim = vals.get("nim")
            if nim and (
                nim in seen_nims
                or self.search_count([("nim", "=", nim)])
            ):
                raise ValidationError("NIM tidak boleh duplikat.")
            seen_nims.add(nim)
        records = super().create(vals_list)
        for mhs in records:
            if not mhs.email:
                raise ValidationError(
                    "Email wajib diisi pada kontak mahasiswa untuk membuat login."
                )
            mhs.partner_id.write({"ref": mhs.nim})
            mhs._create_or_update_user()

        return records

    def _create_or_update_user(self):
        for mahasiswa in self:
            _create_or_update_profile_user(
                mahasiswa, mahasiswa.nim, "erpobe.group_mahasiswa", "nim"
            )
