from odoo import Command, fields
from odoo.modules.registry import Registry
from odoo.exceptions import AccessDenied, AccessError
from odoo.tests import TransactionCase, tagged
from datetime import timedelta


@tagged("audit", "at_install")
class TestErpObeAuditLog(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.admin = cls.env["res.users"].with_context(no_reset_password=True).create({
            "name": "Audit Admin",
            "login": "audit.admin@example.test",
            "group_ids": [
                Command.set([
                    cls.env.ref("erpobe.group_admin").id,
                    cls.env.ref("erpobe.group_audit_manager").id,
                ])
            ],
        })

    def test_create_update_delete_and_sudo_actor(self):
        faculty = self.env["erpobe.master.fakultas"].sudo().with_context(
            audit_actor_id=self.admin.id,
            audit_source="backend",
        ).create({
            "name": "Fakultas Audit",
            "kode": "FAU",
        })
        logs = self.env["erpobe.audit.log"].sudo().search([
            ("model_name", "=", "erpobe.master.fakultas"),
            ("record_id", "=", faculty.id),
        ])
        self.assertTrue(logs.filtered(lambda log: log.action_type == "CREATE"))

        faculty.sudo().with_context(
            audit_actor_id=self.admin.id,
            audit_source="backend",
        ).write({"name": "Fakultas Audit Baru"})
        update = self.env["erpobe.audit.log"].sudo().search([
            ("model_name", "=", "erpobe.master.fakultas"),
            ("record_id", "=", faculty.id),
            ("action_type", "=", "UPDATE"),
        ], order="id desc", limit=1)
        self.assertTrue(update)
        self.assertIn("name", update.changed_fields)
        self.assertEqual(update.new_values.get("name"), "Fakultas Audit Baru")
        self.assertEqual(update.user_id, self.admin)

        record_id = faculty.id
        record_name = faculty.display_name
        faculty.sudo().with_context(
            audit_actor_id=self.admin.id,
            audit_source="backend",
        ).unlink()
        delete = self.env["erpobe.audit.log"].sudo().search([
            ("model_name", "=", "erpobe.master.fakultas"),
            ("record_id", "=", record_id),
            ("action_type", "=", "DELETE"),
        ], order="id desc", limit=1)
        self.assertTrue(delete)
        self.assertEqual(delete.record_name_snapshot, record_name)

    def test_sudo_preserves_actor_context(self):
        faculty = self.env["erpobe.master.fakultas"].sudo().create({
            "name": "Fakultas Portal",
            "kode": "FPO",
        })
        faculty.with_context(
            audit_actor_id=self.admin.id,
            audit_source="portal",
        ).sudo().write({"name": "Fakultas Portal Baru"})
        update = self.env["erpobe.audit.log"].sudo().search([
            ("model_name", "=", "erpobe.master.fakultas"),
            ("record_id", "=", faculty.id),
            ("action_type", "=", "UPDATE"),
        ], order="id desc", limit=1)
        self.assertEqual(update.user_id, self.admin)
        self.assertEqual(update.source, "portal")

    def test_masking_and_immutability(self):
        log = self.env["erpobe.audit.log"].sudo().log_event(
            "UPDATE",
            model_name="res.users",
            description="Masked test",
            old_values={"password": "old-secret", "token": "old-token", "name": "Old"},
            new_values={"password": "new-secret", "token": "new-token", "name": "New"},
            changed_fields=["password", "token", "name"],
        )
        self.assertEqual(log.old_values["password"], "[MASKED]")
        self.assertEqual(log.new_values["token"], "[MASKED]")
        with self.assertRaises(AccessError):
            log.with_user(self.admin).write({"description": "changed"})
        with self.assertRaises(AccessError):
            log.with_user(self.admin).unlink()

    def test_unchanged_update_not_logged(self):
        faculty = self.env["erpobe.master.fakultas"].sudo().with_context(
            audit_actor_id=self.admin.id,
            audit_source="backend",
        ).create({
            "name": "Fakultas Stable",
            "kode": "FST",
        })
        before = self.env["erpobe.audit.log"].sudo().search_count([
            ("model_name", "=", "erpobe.master.fakultas"),
            ("record_id", "=", faculty.id),
            ("action_type", "=", "UPDATE"),
        ])
        faculty.sudo().with_context(
            audit_actor_id=self.admin.id,
            audit_source="backend",
        ).write({"name": "Fakultas Stable"})
        after = self.env["erpobe.audit.log"].sudo().search_count([
            ("model_name", "=", "erpobe.master.fakultas"),
            ("record_id", "=", faculty.id),
            ("action_type", "=", "UPDATE"),
        ])
        self.assertEqual(before, after)

    def test_rollback_does_not_persist_log(self):
        try:
            with self.env.cr.savepoint():
                faculty = self.env["erpobe.master.fakultas"].sudo().with_context(
                    audit_actor_id=self.admin.id,
                    audit_source="backend",
                ).create({
                    "name": "Fakultas Rollback",
                    "kode": "FRB",
                })
                raise RuntimeError("force rollback")
        except RuntimeError:
            pass
        self.assertFalse(self.env["erpobe.audit.log"].sudo().search([
            ("model_name", "=", "erpobe.master.fakultas"),
            ("record_name_snapshot", "=", "Fakultas Rollback"),
        ]))

    def test_archive_restore_and_recent_dashboard(self):
        faculty = self.env["erpobe.master.fakultas"].sudo().with_context(
            audit_actor_id=self.admin.id,
            audit_source="backend",
        ).create({
            "name": "Fakultas Lifecycle",
            "kode": "FLC",
        })
        faculty.sudo().with_context(
            audit_actor_id=self.admin.id,
            audit_source="backend",
        ).write({"active": False})
        archived = self.env["erpobe.audit.log"].sudo().search([
            ("model_name", "=", "erpobe.master.fakultas"),
            ("record_id", "=", faculty.id),
            ("action_type", "=", "ARCHIVE"),
        ], limit=1)
        self.assertTrue(archived)

        faculty.sudo().with_context(
            audit_actor_id=self.admin.id,
            audit_source="backend",
        ).write({"active": True})
        restored = self.env["erpobe.audit.log"].sudo().search([
            ("model_name", "=", "erpobe.master.fakultas"),
            ("record_id", "=", faculty.id),
            ("action_type", "=", "RESTORE"),
        ], limit=1)
        self.assertTrue(restored)

        dashboard = self.env["erpobe.audit.dashboard"].create({})
        dashboard._compute_recent_logs()
        self.assertLessEqual(len(dashboard.recent_log_ids), 20)
        dashboard._compute_kpis()
        self.assertGreaterEqual(dashboard.total_today, 0)

    def test_update_and_delete_roll_back_with_savepoint(self):
        faculty = self.env["erpobe.master.fakultas"].sudo().with_context(
            audit_actor_id=self.admin.id,
            audit_source="backend",
        ).create({
            "name": "Fakultas Transaction",
            "kode": "FTX",
        })
        try:
            with self.env.cr.savepoint():
                faculty.sudo().with_context(
                    audit_actor_id=self.admin.id,
                    audit_source="backend",
                ).write({"name": "Nama Tidak Bertahan"})
                raise RuntimeError("rollback update")
        except RuntimeError:
            pass
        self.assertFalse(self.env["erpobe.audit.log"].sudo().search([
            ("model_name", "=", "erpobe.master.fakultas"),
            ("record_id", "=", faculty.id),
            ("record_name_snapshot", "=", "Nama Tidak Bertahan"),
        ], limit=1))

        try:
            with self.env.cr.savepoint():
                faculty.sudo().with_context(
                    audit_actor_id=self.admin.id,
                    audit_source="backend",
                ).unlink()
                raise RuntimeError("rollback delete")
        except RuntimeError:
            pass
        self.assertTrue(faculty.exists())
        self.assertFalse(self.env["erpobe.audit.log"].sudo().search([
            ("model_name", "=", "erpobe.master.fakultas"),
            ("action_type", "=", "DELETE"),
            ("record_id", "=", faculty.id),
        ], limit=1))

    def test_role_security_for_audit_log(self):
        log = self.env["erpobe.audit.log"].sudo().log_event(
            "CREATE",
            model_name="erpobe.master.fakultas",
            description="Security test",
        )
        lecturer = self.env["res.users"].with_context(no_reset_password=True).create({
            "name": "Audit Dosen",
            "login": "audit.dosen@example.test",
            "group_ids": [Command.set([self.env.ref("erpobe.group_dosen").id])],
        })
        student = self.env["res.users"].with_context(no_reset_password=True).create({
            "name": "Audit Mahasiswa",
            "login": "audit.mahasiswa@example.test",
            "group_ids": [Command.set([self.env.ref("erpobe.group_mahasiswa").id])],
        })
        ordinary = self.env["res.users"].with_context(no_reset_password=True).create({
            "name": "Audit Internal Biasa",
            "login": "audit.internal@example.test",
            "group_ids": [Command.set([self.env.ref("base.group_user").id])],
        })
        ordinary_admin = self.env["res.users"].with_context(no_reset_password=True).create({
            "name": "Admin ERP Biasa",
            "login": "audit.admin.regular@example.test",
            "group_ids": [Command.set([self.env.ref("erpobe.group_admin").id])],
        })
        public = self.env.ref("base.public_user")

        self.assertTrue(self.env["erpobe.audit.log"].with_user(self.admin).search([("id", "=", log.id)]))
        for user in (lecturer, student, ordinary, ordinary_admin):
            with self.assertRaises(AccessError):
                self.env["erpobe.audit.log"].with_user(user).search([("id", "=", log.id)])
        with self.assertRaises(AccessError):
            self.env["erpobe.audit.log"].with_user(public).search([("id", "=", log.id)])

    def test_authentication_success_and_failed(self):
        user = self.env["res.users"].sudo().with_context(no_reset_password=True).create({
            "name": "Audit Login User",
            "login": "audit.login@example.test",
            "password": "audit-pass",
            "group_ids": [Command.set([self.env.ref("erpobe.group_admin").id])],
        })
        auth_info = self.env["res.users"].sudo().authenticate(
            {"type": "password", "login": user.login, "password": "audit-pass"},
            {"REMOTE_ADDR": "127.0.0.1", "HTTP_USER_AGENT": "AuditTest"},
        )
        self.assertTrue(auth_info["uid"])
        success = self.env["erpobe.audit.log"].sudo().search([
            ("action_type", "=", "LOGIN_SUCCESS"),
            ("user_id", "=", user.id),
        ], limit=1)
        self.assertTrue(success)

        with self.assertRaises(AccessDenied):
            self.env["res.users"].sudo().authenticate(
                {"type": "password", "login": user.login, "password": "wrong-pass"},
                {"REMOTE_ADDR": "127.0.0.1", "HTTP_USER_AGENT": "AuditTest"},
            )
        failed_count = 0
        with Registry(self.env.registry.db_name).cursor() as cr:
            cr.execute(
                "SELECT count(*) FROM erpobe_audit_log "
                "WHERE action_type = 'LOGIN_FAILED'"
            )
            failed_count = cr.fetchone()[0]
        self.assertGreaterEqual(failed_count, 1)

    def test_report_and_retention_monitoring(self):
        report_action = self.env.ref("erpobe.action_report_rps", raise_if_not_found=False)
        if report_action:
            report_action._render_qweb_html("erpobe.action_report_rps", [], data={})
            report_log = self.env["erpobe.audit.log"].sudo().search([
                ("action_type", "=", "REPORT_GENERATION"),
                ("model_name", "=", "erpobe.akademik.rps"),
            ], limit=1)
            self.assertTrue(report_log)

        ordinary = self.env["erpobe.audit.log"].sudo().log_event(
            "CREATE",
            model_name="erpobe.master.fakultas",
            description="Retention ordinary",
            severity="info",
        )
        critical = self.env["erpobe.audit.log"].sudo().log_event(
            "DELETE",
            model_name="erpobe.master.fakultas",
            description="Retention critical",
            severity="critical",
        )
        ordinary.sudo().with_context(allow_audit_mutation=True).write({
            "timestamp": fields.Datetime.now() - timedelta(days=181),
        })
        critical.sudo().with_context(allow_audit_mutation=True).write({
            "timestamp": fields.Datetime.now() - timedelta(days=366),
        })
        dashboard = self.env["erpobe.audit.dashboard"].create({})
        dashboard._compute_retention_monitor()
        self.assertGreaterEqual(dashboard.expired_ordinary_records, 1)
        self.assertGreaterEqual(dashboard.expired_critical_records, 1)
        self.env["erpobe.audit.log"].cleanup_expired_logs()
