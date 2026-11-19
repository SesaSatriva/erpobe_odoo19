import re
from datetime import date

from odoo import Command, api, fields, models
from odoo.exceptions import AccessError, ValidationError
from odoo.fields import Domain

from .faculty_access import _check_prodi_write_access


class ErpObeResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    triton_public_people_enabled = fields.Boolean(
        string="Tampilkan daftar dosen dan mahasiswa di situs publik",
        config_parameter="erpobe.triton.public_people_enabled",
        default=False,
        help=(
            "Jika dinonaktifkan, halaman publik tetap menampilkan statistik "
            "agregat, tetapi tidak menampilkan daftar atau profil individu."
        ),
    )


FIXTURE_USER_PASSWORD = "Demo123!"


def _create_or_update_profile_user(profile, identifier, role_xmlid, identifier_field):
    partner = profile.partner_id
    if not partner.email:
        raise ValidationError(
            "Email wajib diisi pada kontak dosen/mahasiswa untuk membuat login."
        )

    users = profile.env["res.users"].sudo().with_context(active_test=False)
    user = users.search([("partner_id", "=", partner.id)], limit=2)
    if len(user) > 1:
        raise ValidationError(
            f"Kontak {partner.display_name} terhubung ke lebih dari satu akun."
        )

    is_fixture_load = profile.env.context.get("install_mode")
    is_new_user = not bool(user)
    if user:
        linked_dosen = profile.env["erpobe.master.dosen"].sudo().search(
            [("user_id", "=", user.id)], limit=1
        )
        linked_mahasiswa = profile.env["erpobe.master.mahasiswa"].sudo().search(
            [("user_id", "=", user.id)], limit=1
        )
        profile_prodis = (
            profile.prodi_ids
            if profile._name == "erpobe.master.dosen"
            else profile.prodi_id
        )
        if (
            linked_dosen
            or linked_mahasiswa
            or not user.active
            or not user.has_group(role_xmlid)
            or user.has_group("erpobe.group_admin")
            or user.has_group("erpobe.group_superadmin")
            or user.has_group("base.group_system")
            or set(user.erpobe_prodi_ids.ids) != set(profile_prodis.ids)
        ):
            raise ValidationError(
                f"Akun yang sudah ada untuk {profile.name} tidak sesuai "
                "dengan role/cakupan profil; akun tidak diubah."
            )
    else:
        login = (
            partner.email.partition("@")[0]
            if is_fixture_load
            else partner.email
        )
        if users.search([("login", "=ilike", login)], limit=1):
            raise ValidationError(f"Login {login} sudah digunakan.")
        if users.search([("email", "=ilike", partner.email)], limit=1):
            raise ValidationError(f"Email {partner.email} sudah digunakan.")
        user = users.with_context(
            skip_sync_user_type=True,
            no_reset_password=True,
        ).create(
            {
                "name": profile.name,
                "login": login,
                "password": identifier,
                identifier_field: identifier,
                "partner_id": partner.id,
                "active": True,
                "group_ids": [
                    Command.link(profile.env.ref("base.group_portal").id),
                    Command.link(profile.env.ref(role_xmlid).id),
                ],
            }
        )

    profile.user_id = user.id
    if is_new_user:
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

    @api.model
    def load_erpobe_fixture_users(self):
        users = self.sudo().with_context(active_test=False)
        prodis = (
            self.env["erpobe.master.prodi"]
            .sudo()
            .with_context(active_test=False)
            .browse(
                self.env["ir.model.data"]
                .sudo()
                .search(
                    [
                        ("module", "=", "erpobe"),
                        ("model", "=", "erpobe.master.prodi"),
                    ],
                    order="name",
                )
                .mapped("res_id")
            )
            .exists()
        )
        if not prodis:
            return True

        fixture_curricula = (
            self.env["ir.model.data"]
            .sudo()
            .search(
                [
                    ("module", "=", "erpobe"),
                    ("model", "=", "erpobe.akademik.kurikulum"),
                    ("name", "=like", "fixture_curriculum_%"),
                ]
            )
        )
        fixture_prodi_ids = set(
            self.env["erpobe.akademik.kurikulum"]
            .sudo()
            .browse(fixture_curricula.mapped("res_id"))
            .exists()
            .mapped("prodi_id")
            .ids
        )

        dosen_model = (
            self.env["erpobe.master.dosen"]
            .sudo()
            .with_context(active_test=False)
        )
        mahasiswa_model = (
            self.env["erpobe.master.mahasiswa"]
            .sudo()
            .with_context(active_test=False)
        )
        rombel_model = (
            self.env["erpobe.master.rombel"]
            .sudo()
            .with_context(active_test=False)
        )
        group_admin = self.env.ref("erpobe.group_admin")
        slug_by_prodi = {}
        slug_counts = {}
        for prodi in prodis:
            slug = re.sub(r"[^a-z0-9]+", ".", (prodi.kode or "").lower()).strip(".")
            slug = slug or "prodi"
            slug_by_prodi[prodi.id] = slug
            slug_counts[slug] = slug_counts.get(slug, 0) + 1

        plans = []
        fixture_only_prodis = []
        account_ids = set()
        profile_by_user = {}
        for prodi in prodis:
            if prodi.id in fixture_prodi_ids:
                slug = slug_by_prodi[prodi.id]
                if slug_counts[slug] > 1:
                    slug = f"{slug}.p{prodi.id}"
                fixture_only_prodis.append((prodi, slug))
                continue

            slug = slug_by_prodi[prodi.id]
            if slug_counts[slug] > 1:
                slug = f"{slug}.p{prodi.id}"

            dosens = dosen_model.search(
                [
                    ("prodi_ids", "in", prodi.id),
                    ("active", "=", True),
                ],
                order="id",
            )
            mahasiswa = mahasiswa_model.search(
                [
                    ("prodi_id", "=", prodi.id),
                    ("active", "=", True),
                ],
                order="id",
            )
            if len(dosens) > 3 or len(mahasiswa) > 20:
                raise ValidationError(
                    f"Prodi {prodi.display_name} sudah memiliki {len(dosens)} "
                    f"dosen dan {len(mahasiswa)} mahasiswa. Seeder fixture tidak "
                    "akan menghapus atau mengubah profil yang sudah ada."
                )

            scoped_users = users.search(
                [("erpobe_prodi_ids", "in", prodi.id)]
            )
            admins = scoped_users.filtered(
                lambda user: user.has_group("erpobe.group_admin")
                and not user.has_group("erpobe.group_superadmin")
                and not user.has_group("base.group_system")
                and set(user.erpobe_prodi_ids.ids) == {prodi.id}
                and not user.has_group("erpobe.group_dosen")
                and not user.has_group("erpobe.group_mahasiswa")
            )
            if len(admins) > 1:
                raise ValidationError(
                    f"Prodi {prodi.display_name} sudah memiliki lebih dari "
                    "satu Admin Prodi; seeder fixture tidak mengubah akun lama."
                )
            if admins:
                admin = admins[0]
                if not admin.active:
                    raise ValidationError(
                        f"Akun Admin Prodi {admin.display_name} tidak aktif dan "
                        "tidak akan diubah."
                    )
                account_ids.add(admin.id)

            for profiles, role_xmlid, other_role_xmlid, role_name in (
                (
                    dosens,
                    "erpobe.group_dosen",
                    "erpobe.group_mahasiswa",
                    "dosen",
                ),
                (
                    mahasiswa,
                    "erpobe.group_mahasiswa",
                    "erpobe.group_dosen",
                    "mahasiswa",
                ),
            ):
                for profile in profiles:
                    user = profile.user_id
                    if not user:
                        profile._create_or_update_user()
                        user = profile.user_id
                    if not profile.active or not user.active:
                        raise ValidationError(
                            f"Profil {role_name} {profile.display_name} atau "
                            "akunnya tidak aktif dan tidak akan diubah."
                        )
                    expected_prodis = (
                        profile.prodi_ids
                        if role_name == "dosen"
                        else profile.prodi_id
                    )
                    if (
                        not user.has_group(role_xmlid)
                        or user.has_group(other_role_xmlid)
                        or user.has_group("erpobe.group_admin")
                        or user.has_group("erpobe.group_superadmin")
                        or user.has_group("base.group_system")
                        or set(user.erpobe_prodi_ids.ids)
                        != set(expected_prodis.ids)
                    ):
                        raise ValidationError(
                            f"Akun {user.display_name} tidak sesuai dengan role "
                            f"atau cakupan prodi profil {role_name}-nya."
                        )
                    profile_key = (profile._name, profile.id)
                    if (
                        user.id in profile_by_user
                        and profile_by_user[user.id] != profile_key
                    ):
                        raise ValidationError(
                            f"Akun {user.display_name} digunakan oleh lebih dari "
                            "satu profil."
                        )
                    profile_by_user[user.id] = profile_key
                    account_ids.add(user.id)

            plans.append((prodi, slug, dosens, mahasiswa, admins))

        accounts = users.browse(sorted(account_ids))
        logins = [user.login.casefold() for user in accounts if user.login]
        emails = [user.email.casefold() for user in accounts if user.email]
        if len(logins) != len(accounts) or len(set(logins)) != len(accounts):
            raise ValidationError(
                "Akun fixture yang sudah ada memiliki login kosong atau duplikat."
            )
        if len(emails) != len(accounts) or len(set(emails)) != len(accounts):
            raise ValidationError(
                "Akun fixture yang sudah ada memiliki email kosong atau duplikat."
            )

        reserved_logins = {
            login.casefold()
            for login in users.search([]).mapped("login")
            if login
        }
        reserved_emails = {
            email.casefold()
            for email in users.search([]).mapped("email")
            if email
        }
        used_nips = set(dosen_model.search([]).mapped("nip"))
        used_nims = set(mahasiswa_model.search([]).mapped("nim"))

        def reserve_identity(base, prodi):
            for login in (base, f"{base}.p{prodi.id}"):
                email = f"{login}@example.test"
                normalized_login = login.casefold()
                normalized_email = email.casefold()
                if (
                    normalized_login not in reserved_logins
                    and normalized_email not in reserved_emails
                    and normalized_email not in reserved_logins
                ):
                    reserved_logins.add(normalized_login)
                    reserved_emails.add(normalized_email)
                    return login, email
            raise ValidationError(
                f"Login fixture untuk {base} berbenturan dengan akun yang sudah ada."
            )

        def reserve_identifier(base, used_identifiers):
            identifier = base
            suffix = 1
            while identifier in used_identifiers:
                identifier = f"{base}-{suffix}"
                suffix += 1
            used_identifiers.add(identifier)
            return identifier

        for prodi, slug in fixture_only_prodis:
            scoped_users = users.search(
                [("erpobe_prodi_ids", "in", prodi.id)]
            )
            admins = scoped_users.filtered(
                lambda user: user.has_group("erpobe.group_admin")
                and not user.has_group("erpobe.group_superadmin")
                and not user.has_group("base.group_system")
                and set(user.erpobe_prodi_ids.ids) == {prodi.id}
                and not user.has_group("erpobe.group_dosen")
                and not user.has_group("erpobe.group_mahasiswa")
            )
            if len(admins) > 1:
                raise ValidationError(
                    f"Prodi {prodi.display_name} sudah memiliki lebih dari "
                    "satu Admin Prodi; seeder fixture tidak mengubah akun lama."
                )
            if admins and not admins.active:
                raise ValidationError(
                    f"Akun Admin Prodi {admins.display_name} tidak aktif dan "
                    "tidak akan diganti."
                )
            if not admins:
                login, email = reserve_identity(f"admin.{slug}", prodi)
                users.with_context(no_reset_password=True).create(
                    {
                        "name": f"Admin Prodi {prodi.name}",
                        "login": login,
                        "email": email,
                        "password": FIXTURE_USER_PASSWORD,
                        "group_ids": [Command.set([group_admin.id])],
                        "erpobe_prodi_ids": [Command.link(prodi.id)],
                        "active": True,
                    }
                )

        for prodi, slug, dosens, mahasiswa, admins in plans:
            if not admins:
                login, email = reserve_identity(f"admin.{slug}", prodi)
                users.with_context(no_reset_password=True).create(
                    {
                        "name": f"Admin Prodi {prodi.name}",
                        "login": login,
                        "email": email,
                        "password": FIXTURE_USER_PASSWORD,
                        "group_ids": [Command.set([group_admin.id])],
                        "erpobe_prodi_ids": [Command.link(prodi.id)],
                        "active": True,
                    }
                )

            for index in range(len(dosens) + 1, 4):
                login, email = reserve_identity(
                    f"dosen.{slug}.{index:02d}", prodi
                )
                partner = self.env["res.partner"].sudo().create(
                    {
                        "name": f"Demo Dosen {prodi.kode} {index:02d}",
                        "email": email,
                    }
                )
                dosen = dosen_model.create(
                    {
                        "partner_id": partner.id,
                        "name": partner.name,
                        "nip": reserve_identifier(
                            f"DEMO-DOSEN-{prodi.id:06d}-{index:02d}",
                            used_nips,
                        ),
                        "prodi_ids": [Command.link(prodi.id)],
                    }
                )
                dosen.user_id.with_context(skip_sync_user_type=True).write(
                    {"login": login, "password": dosen.nip}
                )

            dosens = dosen_model.search(
                [("prodi_ids", "in", prodi.id)], order="id"
            )
            rombel = rombel_model.search(
                [("prodi_id", "=", prodi.id)], order="angkatan desc, id", limit=1
            )
            if not mahasiswa and not rombel:
                rombel = rombel_model.create(
                    {
                        "name": f"Demo {slug}",
                        "angkatan": date.today().year,
                        "prodi_id": prodi.id,
                    }
                )
            elif not rombel:
                raise ValidationError(
                    f"Prodi {prodi.display_name} memiliki mahasiswa tetapi tidak "
                    "memiliki rombel."
                )

            wali_id = dosens[:1].id
            for index in range(len(mahasiswa) + 1, 21):
                login, email = reserve_identity(
                    f"mahasiswa.{slug}.{index:03d}", prodi
                )
                partner = self.env["res.partner"].sudo().create(
                    {
                        "name": f"Demo Mahasiswa {prodi.kode} {index:03d}",
                        "email": email,
                    }
                )
                student = mahasiswa_model.create(
                    {
                        "partner_id": partner.id,
                        "name": partner.name,
                        "nim": reserve_identifier(
                            f"DEMO-MHS-{prodi.id:06d}-{index:03d}",
                            used_nims,
                        ),
                        "rombel_id": rombel.id,
                        "dosen_wali_id": wali_id,
                    }
                )
                student.user_id.with_context(skip_sync_user_type=True).write(
                    {"login": login, "password": student.nim}
                )

        final_account_ids = set()
        for prodi, _, _, _, _ in plans:
            dosens = dosen_model.search(
                [
                    ("prodi_ids", "in", prodi.id),
                    ("active", "=", True),
                ],
                order="id",
            )
            mahasiswa = mahasiswa_model.search(
                [
                    ("prodi_id", "=", prodi.id),
                    ("active", "=", True),
                ],
                order="id",
            )
            admins = users.search(
                [
                    ("erpobe_prodi_ids", "in", prodi.id),
                    ("active", "=", True),
                ]
            ).filtered(
                lambda user: user.has_group("erpobe.group_admin")
                and not user.has_group("erpobe.group_superadmin")
                and not user.has_group("base.group_system")
                and set(user.erpobe_prodi_ids.ids) == {prodi.id}
                and not user.has_group("erpobe.group_dosen")
                and not user.has_group("erpobe.group_mahasiswa")
            )
            if len(dosens) != 3 or len(mahasiswa) != 20 or len(admins) != 1:
                raise ValidationError(
                    f"Jumlah akun fixture untuk {prodi.display_name} tidak sesuai "
                    "target 1 Admin Prodi, 3 dosen, dan 20 mahasiswa."
                )
            role_account_ids = (
                admins.ids
                + dosens.mapped("user_id").ids
                + mahasiswa.mapped("user_id").ids
            )
            if len(set(role_account_ids)) != 24:
                raise ValidationError(
                    f"Akun fixture pada {prodi.display_name} tidak terhubung ke "
                    "24 pengguna yang berbeda."
                )
            final_account_ids.update(role_account_ids)

        final_accounts = users.browse(sorted(final_account_ids))
        if len(final_accounts) != 24 * len(plans):
            raise ValidationError(
                "Jumlah pengguna unik tidak sesuai dengan 24 akun per prodi fixture."
            )
        final_logins = [user.login.casefold() for user in final_accounts if user.login]
        final_emails = [user.email.casefold() for user in final_accounts if user.email]
        if (
            len(final_logins) != len(final_accounts)
            or len(set(final_logins)) != len(final_accounts)
        ):
            raise ValidationError("Login akun fixture kosong atau tidak unik.")
        if (
            len(final_emails) != len(final_accounts)
            or len(set(final_emails)) != len(final_accounts)
        ):
            raise ValidationError("Email akun fixture kosong atau tidak unik.")

        return True

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
    jabatan_fungsional = fields.Char(string="Jabatan Fungsional")
    bidang_keahlian = fields.Char(string="Bidang Keahlian")
    is_public_visible = fields.Boolean(
        string="Tampil di halaman publik",
        default=True,
        help="Mengaktifkan atau menonaktifkan profil publik di halaman TRITON.",
    )
    public_opt_out = fields.Boolean(
        string="Opt-out publik",
        default=False,
        help="Jika aktif, nama tidak ditampilkan di daftar publik meski profil masih aktif.",
    )

    _nip_unique = models.Constraint("UNIQUE (nip)", "NIP tidak boleh duplikat.")

    prodi_ids = fields.Many2many(
        "erpobe.master.prodi",
        "erpobe_prodi_dosen_rel",
        "dosen_id",
        "prodi_id",
        string="Program Studi",
    )

    @api.constrains("prodi_ids")
    def _check_prodi_required(self):
        for record in self:
            if not record.prodi_ids:
                raise ValidationError("Dosen harus terdaftar pada minimal satu prodi.")
            faculties = record.prodi_ids.mapped("fakultas_id")
            courses = self.env["erpobe.master.matakuliah"].sudo().search(
                [
                    "|",
                    ("koordinator_id", "=", record.id),
                    ("tim_pengampu_ids", "in", record.id),
                ]
            )
            if any(course.prodi_id not in record.prodi_ids for course in courses):
                raise ValidationError(
                    "Dosen tidak dapat dilepas dari prodi mata kuliah yang diampu."
                )

    def write(self, vals):

        # Validasi cakupan ekstensi berjalan sebelum logika utama.
        _check_prodi_write_access(self, vals)

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

        # Validasi cakupan ekstensi berjalan setelah logika utama.
        _check_prodi_write_access(
            records,
            {"prodi_ids": [(6, 0, records.mapped("prodi_ids").ids)]},
        )

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
    status_akademik = fields.Selection(
        [
            ("aktif", "Aktif"),
            ("lulus", "Lulus"),
            ("cuti", "Cuti"),
        ],
        string="Status Akademik",
        default="aktif",
        required=True,
    )
    dosen_wali_id = fields.Many2one(
        "erpobe.master.dosen",
        string="Dosen Wali",
        ondelete="set null",
        domain="[('prodi_ids', 'in', prodi_id)]",
    )
    is_public_visible = fields.Boolean(
        string="Tampil di halaman publik",
        default=True,
        help="Mengaktifkan atau menonaktifkan profil publik di halaman TRITON.",
    )
    public_opt_out = fields.Boolean(
        string="Opt-out publik",
        default=False,
        help="Jika aktif, nama tidak ditampilkan di daftar publik meski profil masih aktif.",
    )

    rombel_id = fields.Many2one("erpobe.master.rombel", required=True)
    angkatan = fields.Integer(related="rombel_id.angkatan", store=True, readonly=True)
    kurikulum_id = fields.Many2one(
        "erpobe.akademik.kurikulum",
        string="Kurikulum",
        ondelete="restrict",
        index=True,
    )
    semester_saat_ini = fields.Integer(
        string="Semester Akademik Saat Ini",
        default=1,
        help="Semester berjalan berdasarkan riwayat KRS mahasiswa.",
    )

    grade_komponen_ids = fields.One2many("erpobe.grade.komponen", "mahasiswa_id")
    grade_cpmk_ids = fields.One2many("erpobe.grade.cpmk", "mahasiswa_id")

    _nim_unique = models.Constraint("UNIQUE (nim)", "NIM tidak boleh duplikat.")

    prodi_id = fields.Many2one(
        related="rombel_id.prodi_id", store=True, readonly=True, index=True
    )
    fakultas_id = fields.Many2one(
        related="prodi_id.fakultas_id", store=True, readonly=True, index=True
    )

    @api.constrains("kurikulum_id", "prodi_id", "semester_saat_ini")
    def _check_academic_program(self):
        for record in self:
            if record.kurikulum_id and record.kurikulum_id.prodi_id != record.prodi_id:
                raise ValidationError(
                    "Kurikulum mahasiswa harus berasal dari program studinya."
                )
            if record.semester_saat_ini < 1 or record.semester_saat_ini > 14:
                raise ValidationError("Semester akademik harus berada pada rentang 1–14.")

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
