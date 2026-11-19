from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestErpObeFixtureUsers(TransactionCase):
    def test_fixture_profile_creates_standard_user(self):
        faculty = self.env["erpobe.master.fakultas"].sudo().create(
            {"name": "Fixture User Faculty", "kode": "FUF"}
        )
        prodi = self.env["erpobe.master.prodi"].sudo().create(
            {
                "name": "Fixture User Program",
                "kode": "FUP",
                "fakultas_id": faculty.id,
            }
        )
        partner = self.env["res.partner"].sudo().create(
            {
                "name": "Fixture User Teacher",
                "email": "dosen.fup.01@example.test",
            }
        )
        dosen = (
            self.env["erpobe.master.dosen"]
            .sudo()
            .with_context(install_mode=True)
            .create(
                {
                    "partner_id": partner.id,
                    "nip": "FIXTURE-USER-NIP",
                    "prodi_ids": [(4, prodi.id)],
                }
            )
        )

        self.assertEqual(dosen.user_id.login, "dosen.fup.01")
        self.assertEqual(dosen.user_id.email, "dosen.fup.01@example.test")
        self.assertTrue(dosen.user_id.has_group("erpobe.group_dosen"))
        self.assertEqual(dosen.user_id.erpobe_prodi_ids, prodi)
        result = self.env["res.users"].authenticate(
            {
                "type": "password",
                "login": "dosen.fup.01",
                "password": "Demo123!",
            },
            {"interactive": True},
        )
        self.assertEqual(result["uid"], dosen.user_id.id)

    def test_dynamic_fixture_users_are_scoped_and_idempotent(self):
        Faculty = self.env["erpobe.master.fakultas"].sudo()
        Prodi = self.env["erpobe.master.prodi"].sudo()
        Users = self.env["res.users"]
        Dosen = self.env["erpobe.master.dosen"].sudo().with_context(active_test=False)
        Mahasiswa = self.env["erpobe.master.mahasiswa"].sudo().with_context(
            active_test=False
        )

        faculty_a = Faculty.create({"name": "Demo User Faculty A", "kode": "DUA"})
        faculty_b = Faculty.create({"name": "Demo User Faculty B", "kode": "DUB"})
        prodi_a = Prodi.create(
            {"name": "Demo User Program A", "kode": "DU", "fakultas_id": faculty_a.id}
        )
        prodi_b = Prodi.create(
            {"name": "Demo User Program B", "kode": "DU", "fakultas_id": faculty_b.id}
        )
        self.env["ir.model.data"].sudo().create(
            [
                {
                    "module": "erpobe",
                    "name": "test_demo_user_program_a",
                    "model": prodi_a._name,
                    "res_id": prodi_a.id,
                    "noupdate": True,
                },
                {
                    "module": "erpobe",
                    "name": "test_demo_user_program_b",
                    "model": prodi_b._name,
                    "res_id": prodi_b.id,
                    "noupdate": True,
                },
            ]
        )

        Users.load_erpobe_fixture_users()

        accounts = []
        account_ids_before = set()
        for prodi in (prodi_a, prodi_b):
            dosens = Dosen.search([("prodi_ids", "in", prodi.id)])
            mahasiswa = Mahasiswa.search([("prodi_id", "=", prodi.id)])
            scoped_accounts = prodi.user_ids
            admins = scoped_accounts.filtered(
                lambda user: user.has_group("erpobe.group_admin")
            )

            self.assertEqual(len(dosens), 3)
            self.assertEqual(len(mahasiswa), 20)
            self.assertEqual(len(admins), 1)
            self.assertEqual(len(scoped_accounts), 24)

            admin = admins[0]
            self.assertFalse(admin.has_group("erpobe.group_superadmin"))
            self.assertFalse(admin.has_group("base.group_system"))
            self.assertEqual(admin.erpobe_prodi_ids, prodi)
            self.assertEqual(
                Prodi.with_user(admin).search(
                    [("id", "in", [prodi_a.id, prodi_b.id])]
                ),
                prodi,
            )
            self.assertTrue(
                all(
                    dosen.user_id.has_group("erpobe.group_dosen")
                    for dosen in dosens
                )
            )
            self.assertTrue(
                all(
                    student.user_id.has_group("erpobe.group_mahasiswa")
                    for student in mahasiswa
                )
            )
            self.assertTrue(
                all(
                    dosen.user_id.erpobe_prodi_ids == dosen.prodi_ids
                    for dosen in dosens
                )
            )
            self.assertTrue(
                all(
                    student.user_id.erpobe_prodi_ids == student.prodi_id
                    for student in mahasiswa
                )
            )

            role_accounts = (
                [admin]
                + list(dosens.mapped("user_id"))
                + list(mahasiswa.mapped("user_id"))
            )
            logins = [user.login.casefold() for user in role_accounts]
            emails = [user.email.casefold() for user in role_accounts]
            self.assertEqual(len(set(logins)), 24)
            self.assertEqual(len(set(emails)), 24)
            self.assertTrue(
                all(login and email for login, email in zip(logins, emails))
            )
            accounts.extend(role_accounts)
            account_ids_before.update(user.id for user in role_accounts)

        self.assertEqual(len({user.id for user in accounts}), 48)
        self.assertEqual(
            len({user.login.casefold() for user in accounts}),
            48,
        )
        self.assertEqual(
            len({user.email.casefold() for user in accounts}),
            48,
        )
        self.assertTrue(
            all(
                user.login.startswith(
                    ("admin.du.p", "dosen.du.p", "mahasiswa.du.p")
                )
                for user in accounts
            )
        )

        student_a = Mahasiswa.search(
            [("prodi_id", "=", prodi_a.id)], order="id", limit=1
        )
        student_b = Mahasiswa.search(
            [("prodi_id", "=", prodi_b.id)], order="id", limit=1
        )
        dosen_a = Dosen.search([("prodi_ids", "in", prodi_a.id)], order="id", limit=1)
        student_visible = Mahasiswa.with_user(student_a.user_id).search(
            [("id", "in", [student_a.id, student_b.id])]
        )
        dosen_visible = Mahasiswa.with_user(dosen_a.user_id).search(
            [("id", "in", [student_a.id, student_b.id])]
        )
        self.assertEqual(student_visible, student_a)
        self.assertEqual(dosen_visible, student_a)
        self.assertFalse(student_a.user_id.has_group("erpobe.group_admin"))
        self.assertFalse(dosen_a.user_id.has_group("erpobe.group_admin"))

        for user in (
            accounts[0],
            dosen_a.user_id,
            student_a.user_id,
        ):
            result = Users.authenticate(
                {
                    "type": "password",
                    "login": user.login,
                    "password": "Demo123!",
                },
                {"interactive": True},
            )
            self.assertEqual(result["uid"], user.id)

        preserved_user = student_a.user_id.sudo()
        previous_email = preserved_user.email
        preserved_user.write(
            {
                "login": "preserved.demo.student@example.test",
                "password": "Preserve-Strong-57",
            }
        )
        Users.load_erpobe_fixture_users()
        account_ids_after = set()
        for prodi in (prodi_a, prodi_b):
            account_ids_after.update(prodi.user_ids.ids)
        self.assertEqual(account_ids_after, account_ids_before)
        self.assertEqual(preserved_user.login, "preserved.demo.student@example.test")
        self.assertEqual(preserved_user.email, previous_email)
        result = Users.authenticate(
            {
                "type": "password",
                "login": "preserved.demo.student@example.test",
                "password": "Preserve-Strong-57",
            },
            {"interactive": True},
        )
        self.assertEqual(result["uid"], preserved_user.id)
