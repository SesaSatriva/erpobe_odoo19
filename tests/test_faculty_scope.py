from odoo import Command
from odoo.exceptions import AccessDenied, AccessError, UserError, ValidationError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestErpObeFacultyScope(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Faculty = cls.env["erpobe.master.fakultas"]
        cls.Prodi = cls.env["erpobe.master.prodi"]
        cls.Partner = cls.env["res.partner"]
        cls.Users = cls.env["res.users"]
        cls.Dosen = cls.env["erpobe.master.dosen"]
        cls.Mahasiswa = cls.env["erpobe.master.mahasiswa"]
        cls.Rombel = cls.env["erpobe.master.rombel"]
        cls.Matakuliah = cls.env["erpobe.master.matakuliah"]

        cls.faculty_a = cls.Faculty.create({"name": "Fakultas A", "kode": "FA"})
        cls.faculty_b = cls.Faculty.create({"name": "Fakultas B", "kode": "FB"})
        cls.prodi_a = cls.Prodi.create(
            {"name": "Prodi A", "kode": "PA", "fakultas_id": cls.faculty_a.id}
        )
        cls.prodi_b = cls.Prodi.create(
            {"name": "Prodi B", "kode": "PB", "fakultas_id": cls.faculty_b.id}
        )
        cls.rombel_a = cls.Rombel.create(
            {"name": "Kelas A", "angkatan": 2024, "prodi_id": cls.prodi_a.id}
        )
        cls.rombel_b = cls.Rombel.create(
            {"name": "Kelas B", "angkatan": 2024, "prodi_id": cls.prodi_b.id}
        )
        cls.mk_a = cls.Matakuliah.create(
            {
                "name": "Mata Kuliah A",
                "kode_mk": "MKA",
                "sks": 3,
                "semester": 1,
                "prodi_id": cls.prodi_a.id,
            }
        )
        cls.mk_b = cls.Matakuliah.create(
            {
                "name": "Mata Kuliah B",
                "kode_mk": "MKB",
                "sks": 3,
                "semester": 1,
                "prodi_id": cls.prodi_b.id,
            }
        )

        cls.dosen_a = cls._create_dosen(
            "Dosen A", "dosen.a@example.test", "NIP-A", cls.prodi_a
        )
        cls.dosen_b = cls._create_dosen(
            "Dosen B", "dosen.b@example.test", "NIP-B", cls.prodi_b
        )
        cls.mahasiswa_a = cls._create_mahasiswa(
            "Mahasiswa A", "mahasiswa.a@example.test", "NIM-A", cls.rombel_a
        )
        cls.mahasiswa_b = cls._create_mahasiswa(
            "Mahasiswa B", "mahasiswa.b@example.test", "NIM-B", cls.rombel_b
        )

        cls.admin = cls._create_user(
            "Admin A",
            "admin.a@example.test",
            "admin-password",
            "erpobe.group_admin",
        )
        cls.admin.write(
            {"erpobe_prodi_ids": [Command.link(cls.prodi_a.id)]}
        )
        cls.admin_without_faculty = cls._create_user(
            "Admin Kosong",
            "admin.empty@example.test",
            "admin-password",
            "erpobe.group_admin",
        )
        cls.superadmin = cls._create_user(
            "Superadmin",
            "superadmin@example.test",
            "superadmin-password",
            "erpobe.group_superadmin",
        )
        cls.system_user = cls.env.ref("base.user_admin")

    @classmethod
    def _create_user(cls, name, login, password, group_xmlid):
        return cls.Users.with_context(no_reset_password=True).create(
            {
                "name": name,
                "login": login,
                "password": password,
                "group_ids": [Command.set([cls.env.ref(group_xmlid).id])],
            }
        )

    @classmethod
    def _create_dosen(cls, name, email, nip, prodi):
        partner = cls.Partner.create({"name": name, "email": email})
        return cls.Dosen.create(
            {
                "partner_id": partner.id,
                "nip": nip,
                "prodi_ids": [Command.link(prodi.id)],
            }
        )

    @classmethod
    def _create_mahasiswa(cls, name, email, nim, rombel):
        partner = cls.Partner.create({"name": name, "email": email})
        return cls.Mahasiswa.create(
            {
                "partner_id": partner.id,
                "nim": nim,
                "rombel_id": rombel.id,
            }
        )

    def test_profile_user_creation_login_and_scope(self):
        for profile, role_group, identifier_field, identifier in (
            (self.dosen_a, "erpobe.group_dosen", "nip", "NIP-A"),
            (self.mahasiswa_a, "erpobe.group_mahasiswa", "nim", "NIM-A"),
        ):
            user = profile.user_id
            self.assertEqual(user.login, profile.email)
            self.assertEqual(getattr(user, identifier_field), identifier)
            self.assertTrue(user.has_group("base.group_portal"))
            self.assertTrue(user.has_group(role_group))
            self.assertFalse(user.has_group("base.group_user"))
            profile_prodis = (
                profile.prodi_ids
                if profile._name == "erpobe.master.dosen"
                else profile.prodi_id
            )
            self.assertEqual(user.erpobe_prodi_ids, profile_prodis)
        self.assertEqual(self.mahasiswa_a.angkatan, self.rombel_a.angkatan)
        self.assertEqual(self.mahasiswa_a.prodi_id, self.prodi_a)
        self.assertEqual(self.prodi_a.fakultas_id, self.faculty_a)

        for login, password, expected_user in (
            ("NIP-A", "NIP-A", self.dosen_a.user_id),
            ("dosen.a@example.test", "NIP-A", self.dosen_a.user_id),
            ("NIM-A", "NIM-A", self.mahasiswa_a.user_id),
            ("mahasiswa.a@example.test", "NIM-A", self.mahasiswa_a.user_id),
        ):
            result = self.Users.authenticate(
                {"type": "password", "login": login, "password": password},
                {"interactive": True},
            )
            self.assertEqual(result["uid"], expected_user.id)
        with self.assertRaises(AccessDenied):
            self.Users.authenticate(
                {"type": "password", "login": "NIM-A", "password": "salah"},
                {"interactive": True},
            )

    def test_duplicate_identifiers_and_angkatan_validation(self):
        with self.assertRaises(ValidationError):
            self._create_dosen(
                "Dosen Duplikat", "dosen.duplicate@example.test", "NIP-A", self.prodi_a
            )
        with self.assertRaises(ValidationError):
            self._create_mahasiswa(
                "Mahasiswa Duplikat",
                "mahasiswa.duplicate@example.test",
                "NIM-A",
                self.rombel_a,
            )
        with self.assertRaises(ValidationError):
            self.Matakuliah.create(
                {
                    "name": "Duplikat",
                    "kode_mk": "MKA",
                    "sks": 3,
                    "semester": 1,
                    "prodi_id": self.prodi_a.id,
                }
            )
        with self.assertRaises(ValidationError):
            self.Rombel.create(
                {
                    "name": "Kelas A",
                    "angkatan": 2024,
                    "prodi_id": self.prodi_a.id,
                }
            )
        with self.assertRaises(ValidationError):
            self.Rombel.create(
                {
                    "name": "Tahun invalid",
                    "angkatan": 1999,
                    "prodi_id": self.prodi_a.id,
                }
            )

    def test_admin_superadmin_group_regression(self):
        for group in ("erpobe.group_admin", "erpobe.group_superadmin"):
            user = self._create_user(
                f"User {group}",
                f"{group.rsplit('.', 1)[-1]}@example.test",
                "password",
                group,
            )
            self.assertTrue(user.has_group(group))
            self.assertTrue(user.has_group("base.group_user"))
        self.assertFalse(self.superadmin.has_group("base.group_system"))

    def test_prodi_uniqueness_is_scoped_to_faculty(self):
        duplicate = self.Prodi.create(
            {
                "name": "Prodi A",
                "kode": "PA",
                "fakultas_id": self.faculty_b.id,
            }
        )
        self.assertTrue(duplicate)
        with self.assertRaises(ValidationError):
            self.Prodi.create(
                {
                    "name": "Prodi A",
                    "kode": "PA",
                    "fakultas_id": self.faculty_a.id,
                }
            )

    def test_fakultas_access_rights_and_delete_restrict(self):
        faculty = self.Faculty.with_user(self.superadmin).create(
            {"name": "Fakultas sementara", "kode": "FT"}
        )
        faculty.with_user(self.superadmin).write({"name": "Fakultas uji"})
        faculty.with_user(self.superadmin).unlink()

        for user in (self.admin, self.dosen_a.user_id, self.mahasiswa_a.user_id):
            self.assertTrue(
                self.Faculty.with_user(user).search(
                    [("id", "=", self.faculty_a.id)]
                )
            )
            with self.assertRaises(AccessError):
                self.Faculty.with_user(user).create(
                    {"name": "Tidak boleh", "kode": f"NO{user.id}"}
                )

        with self.assertRaises(UserError):
            self.faculty_a.with_user(self.superadmin).unlink()

    def test_prodi_relations_and_delete_restrict(self):
        self.assertEqual(self.faculty_a.prodi_ids, self.prodi_a)
        self.assertEqual(self.prodi_a.dosen_ids, self.dosen_a)
        self.assertEqual(self.prodi_a.mahasiswa_ids, self.mahasiswa_a)
        self.assertEqual(self.prodi_a.matakuliah_ids, self.mk_a)
        self.assertEqual(self.prodi_a.rombel_ids, self.rombel_a)
        self.assertIn(self.admin, self.prodi_a.user_ids)

        cpl = self.env["erpobe.akademik.cpl"].create(
            {
                "name": "CPL Prodi A",
                "kode_cpl": "CPL-A",
                "prodi_id": self.prodi_a.id,
            }
        )
        self.assertEqual(self.prodi_a.cpl_ids, cpl)
        cpl_b = self.env["erpobe.akademik.cpl"].create(
            {
                "name": "CPL Prodi B",
                "kode_cpl": "CPL-B",
                "prodi_id": self.prodi_b.id,
            }
        )
        visible_cpls = self.env["erpobe.akademik.cpl"].with_user(self.admin).search([])
        self.assertEqual(visible_cpls, cpl)
        with self.assertRaises(AccessError):
            cpl_b.with_user(self.admin).read(["name"])

        self.dosen_a.write({"prodi_ids": [Command.link(self.prodi_b.id)]})
        self.assertIn(self.dosen_a, self.prodi_b.dosen_ids)
        with self.assertRaises(UserError):
            self.prodi_a.with_user(self.superadmin).unlink()

    def test_all_prodi_scope_rules_resolve(self):
        rules = self.env["ir.rule"].search([("name", "ilike", "cakupan prodi")])
        self.assertGreaterEqual(len(rules), 35)
        for rule in rules:
            self.env[rule.model_id.model].with_user(self.admin).search([], limit=1)

    def test_prodi_scope_and_superadmin_global_access(self):
        self.assertEqual(
            self.Dosen.with_user(self.admin).search([]).ids, [self.dosen_a.id]
        )
        self.assertEqual(
            self.Mahasiswa.with_user(self.admin).search([]).ids, [self.mahasiswa_a.id]
        )
        self.assertEqual(self.Rombel.with_user(self.admin).search([]).ids, [self.rombel_a.id])
        self.assertEqual(self.Matakuliah.with_user(self.admin).search([]).ids, [self.mk_a.id])
        self.assertEqual(
            self.Prodi.with_user(self.admin).search([]).ids, [self.prodi_a.id]
        )
        with self.assertRaises(AccessError):
            self.Dosen.with_user(self.admin).browse(self.dosen_b.id).read(["name"])

        self.assertFalse(self.Dosen.with_user(self.admin_without_faculty).search([]))
        for model in (self.Mahasiswa, self.Rombel, self.Matakuliah):
            self.assertFalse(model.with_user(self.admin_without_faculty).search([]))
        self.assertFalse(self.Prodi.with_user(self.admin_without_faculty).search([]))
        for model in (
            self.Dosen,
            self.Mahasiswa,
            self.Rombel,
            self.Matakuliah,
            self.Prodi,
        ):
            self.assertEqual(len(model.with_user(self.superadmin).search([])), 2)
        self.mk_b.with_user(self.superadmin).write({"name": "MK B diubah"})
        self.assertEqual(
            self.Dosen.with_user(self.dosen_a.user_id).search([]).ids, [self.dosen_a.id]
        )
        self.assertEqual(
            self.Mahasiswa.with_user(self.mahasiswa_a.user_id).search([]).ids,
            [self.mahasiswa_a.id],
        )

    def test_admin_cannot_create_or_move_out_of_scope(self):
        with self.assertRaises(AccessError):
            self.Matakuliah.with_user(self.admin).create(
                {
                    "name": "MK di luar scope",
                    "kode_mk": "OUT",
                    "sks": 3,
                    "semester": 1,
                    "prodi_id": self.prodi_b.id,
                }
            )
        with self.assertRaises(AccessError):
            self.mk_a.with_user(self.admin).write(
                {"prodi_id": self.prodi_b.id}
            )

    def test_faculty_relationship_validation_and_recompute(self):
        with self.assertRaises(ValidationError):
            self.mk_a.write({"rombel_ids": [Command.link(self.rombel_b.id)]})
        self.faculty_a.write({"dekan_id": self.dosen_a.id})
        with self.assertRaises(ValidationError):
            self.faculty_a.write({"dekan_id": self.dosen_b.id})

        self.rombel_a.write({"prodi_id": self.prodi_b.id})
        self.assertEqual(self.mahasiswa_a.fakultas_id, self.faculty_b)
        self.assertEqual(self.mahasiswa_a.prodi_id, self.prodi_b)
        self.assertEqual(
            self.mahasiswa_a.user_id.erpobe_prodi_ids, self.prodi_b
        )

    def test_user_prodi_scope_field_is_protected(self):
        for user, target in (
            (self.admin, self.admin),
            (self.admin, self.dosen_a.user_id),
            (self.dosen_a.user_id, self.dosen_a.user_id),
        ):
            with self.assertRaises(AccessError):
                target.with_user(user).write(
                    {"erpobe_prodi_ids": [Command.link(self.prodi_b.id)]}
                )
        with self.assertRaises(AccessError):
            self.Users.with_user(self.admin).create(
                {
                    "name": "Akses ditolak",
                    "login": "scope.denied@example.test",
                    "erpobe_prodi_ids": [Command.link(self.prodi_b.id)],
                }
            )
        with self.assertRaises(AccessError):
            self.dosen_a.with_user(self.admin).write(
                {"prodi_ids": [Command.link(self.prodi_b.id)]}
            )
        self.admin.with_user(self.superadmin).write(
            {"erpobe_prodi_ids": [Command.link(self.prodi_b.id)]}
        )

    def test_system_user_is_not_restricted(self):
        self.assertTrue(self.system_user.has_group("base.group_system"))
        self.assertEqual(
            len(self.Faculty.with_user(self.system_user).search([])), 2
        )
        self.assertEqual(
            len(self.Dosen.with_user(self.system_user).search([])), 2
        )

    def test_user_rule_and_profile_creation_remain_usable(self):
        visible_users = self.Users.with_user(self.admin).search([])
        self.assertIn(self.admin, visible_users)
        self.assertIn(self.dosen_a.user_id, visible_users)
        self.assertNotIn(self.dosen_b.user_id, visible_users)
        created = self._create_mahasiswa(
            "Mahasiswa Baru", "new.student@example.test", "NIM-NEW", self.rombel_a
        )
        self.assertEqual(created.user_id.login, "new.student@example.test")

    def test_email_is_required_for_profile_login(self):
        partner = self.Partner.create({"name": "Tanpa Email"})
        with self.assertRaisesRegex(ValidationError, "Email wajib diisi"):
            self.Dosen.create(
                {
                    "partner_id": partner.id,
                    "nip": "NIP-NO-EMAIL",
                    "prodi_ids": [Command.link(self.prodi_a.id)],
                }
            )

    def test_rombel_action_creates_missing_profile_user(self):
        mahasiswa = self._create_mahasiswa(
            "Mahasiswa Tanpa User", "no.user@example.test", "NIM-NO-USER", self.rombel_a
        )
        user = mahasiswa.user_id
        mahasiswa.user_id = False
        self.rombel_a.action_generate_mahasiswa_user()
        self.assertEqual(mahasiswa.user_id, user)

    def test_profile_deletion_removes_user_and_partner(self):
        dosen = self._create_dosen(
            "Dosen Hapus", "delete.teacher@example.test", "NIP-DELETE", self.prodi_a
        )
        user = dosen.user_id
        partner = dosen.partner_id
        dosen.unlink()
        self.assertFalse(self.Users.sudo().browse(user.id).exists())
        self.assertFalse(self.Partner.sudo().browse(partner.id).exists())

        mahasiswa = self._create_mahasiswa(
            "Mahasiswa Hapus",
            "delete.student@example.test",
            "NIM-DELETE",
            self.rombel_a,
        )
        user = mahasiswa.user_id
        partner = mahasiswa.partner_id
        mahasiswa.unlink()
        self.assertFalse(self.Users.sudo().browse(user.id).exists())
        self.assertFalse(self.Partner.sudo().browse(partner.id).exists())

    def test_dosen_prodi_change_synchronizes_user_scope(self):
        dosen = self._create_dosen(
            "Dosen Pindah", "move.teacher@example.test", "NIP-MOVE", self.prodi_a
        )
        dosen.write({"prodi_ids": [Command.set([self.prodi_b.id])]})
        self.assertEqual(dosen.user_id.erpobe_prodi_ids, self.prodi_b)
