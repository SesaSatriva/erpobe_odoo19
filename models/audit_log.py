import json
from datetime import timedelta

from odoo import api, fields, models
from odoo.exceptions import AccessError


class ErpObeAuditLog(models.Model):
    _name = "erpobe.audit.log"
    _description = "ERP OBE Centralized Audit Log"
    _order = "timestamp desc, id desc"
    _rec_name = "name"

    name = fields.Char(compute="_compute_name", store=True)
    user_id = fields.Many2one("res.users", string="User", readonly=True, index=True)
    user_name_snapshot = fields.Char(string="User Name", readonly=True)
    user_login_snapshot = fields.Char(string="Login", readonly=True)
    user_role_snapshot = fields.Char(string="Role", readonly=True)

    event_type = fields.Selection(
        [
            ("CRUD", "CRUD"),
            ("WORKFLOW", "Workflow"),
            ("DATA_OPERATION", "Data Operation"),
            ("SECURITY", "Security"),
        ],
        required=True,
        readonly=True,
        index=True,
    )
    action_type = fields.Selection(
        [
            ("CREATE", "Create"), ("UPDATE", "Update"), ("DELETE", "Delete"),
            ("SUBMIT", "Submit"), ("APPROVE", "Approve"), ("REJECT", "Reject"),
            ("VALIDATE", "Validate"), ("CONFIRM", "Confirm"), ("CANCEL", "Cancel"),
            ("PUBLISH", "Publish"), ("UNPUBLISH", "Unpublish"),
            ("ARCHIVE", "Archive"), ("RESTORE", "Restore"), ("RESET", "Reset"),
            ("LOCK", "Lock"), ("UNLOCK", "Unlock"), ("IMPORT", "Import"),
            ("EXPORT", "Export"), ("PRINT", "Print"), ("REPORT_GENERATION", "Report Generation"),
            ("LOGIN_SUCCESS", "Login Success"), ("LOGIN_FAILED", "Login Failed"),
            ("LOGOUT", "Logout"), ("ACCESS_DENIED", "Access Denied"),
            ("SENSITIVE_ACCESS", "Sensitive Access"),
        ],
        required=True,
        readonly=True,
        index=True,
    )
    description = fields.Text(required=True, readonly=True)
    timestamp = fields.Datetime(default=fields.Datetime.now, required=True, readonly=True, index=True)
    severity = fields.Selection(
        [("info", "Info"), ("warning", "Warning"), ("critical", "Critical")],
        default="info",
        required=True,
        readonly=True,
    )
    status = fields.Selection(
        [("success", "Success"), ("failed", "Failed")],
        default="success",
        required=True,
        readonly=True,
    )
    model_name = fields.Char(readonly=True, index=True)
    model_description = fields.Char(readonly=True)
    record_id = fields.Integer(readonly=True, index=True)
    record_name_snapshot = fields.Char(readonly=True)
    module_name = fields.Char(default="erpobe", readonly=True)
    changed_fields = fields.Char(readonly=True)
    old_values = fields.Json(readonly=True)
    new_values = fields.Json(readonly=True)
    changes_json = fields.Json(readonly=True)
    changes_html = fields.Html(string="Perubahan", compute="_compute_changes_html", readonly=True)
    source = fields.Selection(
        [("backend", "Backend"), ("portal", "Portal"), ("import", "Import"),
         ("export", "Export"), ("report", "Report"), ("cron", "Cron"),
         ("security", "Security")],
        default="backend",
        readonly=True,
    )
    ip_address = fields.Char(readonly=True)
    user_agent = fields.Char(readonly=True)
    correlation_id = fields.Char(readonly=True)
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company, readonly=True)
    is_sensitive = fields.Boolean(default=False, readonly=True)
    metadata = fields.Json(readonly=True)

    @api.depends("timestamp", "action_type", "model_name", "record_name_snapshot")
    def _compute_name(self):
        for log in self:
            log.name = "%s %s %s" % (
                log.timestamp or "",
                log.action_type or "",
                log.record_name_snapshot or log.model_name or "",
            )

    @api.depends("changes_json")
    def _compute_changes_html(self):
        for log in self:
            rows = []
            for field_name, change in sorted((log.changes_json or {}).items()):
                old_value = "" if change.get("old") is None else str(change.get("old"))
                new_value = "" if change.get("new") is None else str(change.get("new"))
                rows.append(
                    "<tr><td>%s</td><td>%s</td><td>%s</td></tr>"
                    % (
                        field_name.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"),
                        old_value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")[:2000],
                        new_value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")[:2000],
                    )
                )
            log.changes_html = (
                "<table class='table table-sm table-striped'><thead><tr>"
                "<th>Field</th><th>Nilai Lama</th><th>Nilai Baru</th>"
                "</tr></thead><tbody>%s</tbody></table>" % "".join(rows)
            )

    def write(self, vals):
        if not self.env.context.get("allow_audit_mutation"):
            raise AccessError("Audit log bersifat immutable dan tidak dapat diubah.")
        return super().write(vals)

    def unlink(self):
        if not (
            self.env.context.get("allow_audit_cleanup")
            and (self.env.user._is_system() or self.env.user.has_group("erpobe.group_superadmin"))
        ):
            raise AccessError("Audit log tidak dapat dihapus oleh pengguna biasa.")
        return super().unlink()

    @api.model
    def log_event(self, action_type, model_name=None, record=None, old_values=None,
                  new_values=None, changed_fields=None, description=None,
                  event_type=None, severity="info", status="success",
                  source=None, is_sensitive=False, metadata=None,
                  correlation_id=None, ip_address=None, user_agent=None,
                  record_id=None, record_name_snapshot=None):
        if self.env.context.get("disable_audit"):
            return False

        actor_id = self.env.context.get("audit_actor_id")
        user = self.env["res.users"].sudo().browse(actor_id).exists() if actor_id else self.env.user
        roles = []
        for xmlid, label in (
            ("erpobe.group_superadmin", "Superadmin"),
            ("erpobe.group_admin", "Admin"),
            ("erpobe.group_dosen", "Dosen"),
            ("erpobe.group_mahasiswa", "Mahasiswa"),
        ):
            if user.has_group(xmlid):
                roles.append(label)
        if user._is_system():
            roles.append("System")

        record_id = record.id if record and hasattr(record, "id") else record_id
        record_name = record_name_snapshot
        model_description = False
        if record:
            try:
                record_name = record.display_name
            except Exception:
                record_name = record_name or False
        if model_name:
            model_description = self.env["ir.model"].sudo().search(
                [("model", "=", model_name)], limit=1
            ).name

        old_values = self._sanitize_values(old_values)
        new_values = self._sanitize_values(new_values)
        changes = {}
        for field_name in changed_fields or []:
            changes[field_name] = {
                "old": (old_values or {}).get(field_name),
                "new": (new_values or {}).get(field_name),
            }

        context = self.env.context
        if source is None:
            source = context.get("audit_source") or ("portal" if user.has_group("erpobe.group_portal") else "backend")
        if ip_address is None:
            ip_address = context.get("audit_ip")
        if user_agent is None:
            user_agent = context.get("audit_user_agent")

        event_type = event_type or self._event_type_for_action(action_type)
        vals = {
            "user_id": user.id,
            "user_name_snapshot": user.name,
            "user_login_snapshot": user.login,
            "user_role_snapshot": ", ".join(dict.fromkeys(roles)) or "Internal",
            "event_type": event_type,
            "action_type": action_type,
            "description": (description or "%s %s" % (action_type, model_name or "record"))[:800],
            "timestamp": fields.Datetime.now(),
            "severity": severity,
            "status": status,
            "model_name": model_name,
            "model_description": model_description,
            "record_id": record_id,
            "record_name_snapshot": str(record_name or "")[:512] or False,
            "changed_fields": ", ".join(changed_fields or [])[:1000] or False,
            "old_values": old_values,
            "new_values": new_values,
            "changes_json": changes or False,
            "source": source,
            "ip_address": ip_address,
            "user_agent": (user_agent or "")[:512] or False,
            "correlation_id": (correlation_id or context.get("audit_correlation_id") or "")[:128] or False,
            "company_id": self.env.company.id,
            "is_sensitive": bool(is_sensitive),
            "metadata": self._sanitize_values(metadata),
        }
        if vals["correlation_id"]:
            existing = self.sudo().search([
                ("correlation_id", "=", vals["correlation_id"]),
                ("action_type", "=", vals["action_type"]),
            ], limit=1)
            if existing:
                return existing
        return self.sudo().with_context(disable_audit=True).create(vals)

    @staticmethod
    def _event_type_for_action(action_type):
        if action_type in {"CREATE", "UPDATE", "DELETE"}:
            return "CRUD"
        if action_type in {"SUBMIT", "APPROVE", "REJECT", "VALIDATE", "CONFIRM", "CANCEL",
                           "PUBLISH", "UNPUBLISH", "ARCHIVE", "RESTORE", "RESET", "LOCK", "UNLOCK"}:
            return "WORKFLOW"
        if action_type in {"IMPORT", "EXPORT", "PRINT", "REPORT_GENERATION"}:
            return "DATA_OPERATION"
        return "SECURITY"

    @api.model
    def _sanitize_values(self, values):
        if not values:
            return values
        if not isinstance(values, dict):
            return str(values)[:2000]
        excluded = (
            "password", "passwd", "token", "secret", "api_key", "apikey",
            "access_token", "session", "credential", "binary",
        )
        result = {}
        for key, value in values.items():
            normalized = str(key).lower()
            if any(word in normalized for word in excluded):
                result[key] = "[MASKED]"
            elif isinstance(value, str):
                result[key] = value[:2000]
            elif isinstance(value, (dict, list, tuple)):
                result[key] = json.loads(json.dumps(value, default=str)) if len(str(value)) < 10000 else "[TRUNCATED]"
            else:
                result[key] = value
        return result

    @api.model
    def cleanup_expired_logs(self):
        ordinary_cutoff = fields.Datetime.now() - timedelta(days=180)
        critical_cutoff = fields.Datetime.now() - timedelta(days=365)
        ordinary = self.search([
            ("severity", "!=", "critical"),
            ("timestamp", "<", ordinary_cutoff),
        ], limit=500)
        ordinary.with_context(allow_audit_cleanup=True).sudo().unlink()
        critical = self.search([
            ("severity", "=", "critical"),
            ("timestamp", "<", critical_cutoff),
        ], limit=500)
        critical.with_context(allow_audit_cleanup=True).sudo().unlink()
        return True

    @api.model
    def log_event_separate(self, db_name, **kwargs):
        """Log security event in an independent cursor and commit it safely."""
        import odoo
        import logging
        _logger = logging.getLogger(__name__)
        try:
            with odoo.modules.registry.Registry(db_name).cursor() as cr:
                if kwargs.get("action_type") == "LOGIN_FAILED":
                    metadata = kwargs.get("metadata") or {}
                    now = fields.Datetime.now()
                    cr.execute(
                        """
                        INSERT INTO erpobe_audit_log (
                            create_uid, write_uid, create_date, write_date,
                            name, event_type, action_type, description, timestamp,
                            severity, status, source, user_name_snapshot,
                            user_login_snapshot, user_role_snapshot,
                            ip_address, user_agent, correlation_id,
                            company_id, is_sensitive, metadata
                        )
                        VALUES (
                            1, 1, %s, %s,
                            %s, 'SECURITY', 'LOGIN_FAILED', %s, %s,
                            %s, 'failed', 'security', 'Unknown',
                            %s, 'Internal', %s, %s, NULL,
                            1, TRUE, %s::jsonb
                        )
                        """,
                        (
                            now, now,
                            "Login Failed",
                            kwargs.get("description") or "Login gagal",
                            now,
                            kwargs.get("severity") or "warning",
                            str(metadata.get("login") or "")[:128],
                            kwargs.get("ip_address") or "",
                            kwargs.get("user_agent") or "",
                            json.dumps(metadata, default=str),
                        ),
                    )
                    cr.commit()
                    return True
                from odoo import api
                env = api.Environment(cr, odoo.SUPERUSER_ID, {
                    "disable_audit": False,
                    "audit_source": "security",
                })
                log = env["erpobe.audit.log"].log_event(**kwargs)
                cr.commit()
                return log.id if log else False
        except Exception as exc:
            _logger.error("Cannot persist separate audit event: %s", exc)
            return False


class ErpObeAuditDashboard(models.TransientModel):
    _name = "erpobe.audit.dashboard"
    _description = "ERP OBE Audit Dashboard"

    total_today = fields.Integer(compute="_compute_kpis")
    total_7_days = fields.Integer(compute="_compute_kpis")
    total_month = fields.Integer(compute="_compute_kpis")
    total_create = fields.Integer(compute="_compute_kpis")
    total_update = fields.Integer(compute="_compute_kpis")
    total_delete = fields.Integer(compute="_compute_kpis")
    total_workflow = fields.Integer(compute="_compute_kpis")
    total_sensitive = fields.Integer(compute="_compute_kpis")
    total_active_users = fields.Integer(compute="_compute_kpis")
    recent_log_ids = fields.Many2many(
        "erpobe.audit.log",
        string="Aktivitas Terbaru",
        compute="_compute_recent_logs",
    )
    total_records = fields.Integer(compute="_compute_retention_monitor")
    expired_ordinary_records = fields.Integer(compute="_compute_retention_monitor")
    expired_critical_records = fields.Integer(compute="_compute_retention_monitor")
    growth_last_month = fields.Integer(compute="_compute_retention_monitor")
    retention_cron_status = fields.Char(compute="_compute_retention_monitor")
    retention_cron_last_run = fields.Datetime(compute="_compute_retention_monitor")

    def _compute_kpis(self):
        Log = self.env["erpobe.audit.log"].sudo()
        now = fields.Datetime.now()
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week = now - timedelta(days=7)
        month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        for dashboard in self:
            dashboard.total_today = Log.search_count([("timestamp", ">=", today)])
            dashboard.total_7_days = Log.search_count([("timestamp", ">=", week)])
            dashboard.total_month = Log.search_count([("timestamp", ">=", month)])
            dashboard.total_create = Log.search_count([("action_type", "=", "CREATE")])
            dashboard.total_update = Log.search_count([("action_type", "=", "UPDATE")])
            dashboard.total_delete = Log.search_count([("action_type", "=", "DELETE")])
            dashboard.total_workflow = Log.search_count([("event_type", "=", "WORKFLOW")])
            dashboard.total_sensitive = Log.search_count([("is_sensitive", "=", True)])
            dashboard.total_active_users = len(Log.search([]).mapped("user_id"))

    @api.depends()
    def _compute_recent_logs(self):
        for dashboard in self:
            dashboard.recent_log_ids = self.env["erpobe.audit.log"].sudo().search(
                [], order="timestamp desc, id desc", limit=20
            )

    @api.depends()
    def _compute_retention_monitor(self):
        Log = self.env["erpobe.audit.log"].sudo()
        now = fields.Datetime.now()
        ordinary_cutoff = now - timedelta(days=180)
        critical_cutoff = now - timedelta(days=365)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if now.month == 1:
            previous_month = now.replace(year=now.year - 1, month=12, day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            previous_month = now.replace(month=now.month - 1, day=1, hour=0, minute=0, second=0, microsecond=0)
        cron = self.env.ref("erpobe.ir_cron_erpobe_audit_cleanup", raise_if_not_found=False)
        for dashboard in self:
            dashboard.total_records = Log.search_count([])
            dashboard.expired_ordinary_records = Log.search_count([
                ("severity", "!=", "critical"),
                ("timestamp", "<", ordinary_cutoff),
            ])
            dashboard.expired_critical_records = Log.search_count([
                ("severity", "=", "critical"),
                ("timestamp", "<", critical_cutoff),
            ])
            dashboard.growth_last_month = Log.search_count([
                ("timestamp", ">=", previous_month),
                ("timestamp", "<", month_start),
            ])
            dashboard.retention_cron_status = "Aktif" if cron and cron.active else "Tidak aktif"
            dashboard.retention_cron_last_run = cron.lastcall if cron else False


class ErpObeAuditMixin(models.AbstractModel):
    _name = "erpobe.audit.mixin"
    _description = "ERP OBE Audited Model Mixin"

    def _audit_is_excluded_field(self, field_name):
        if field_name in {
            "write_uid", "write_date", "create_uid", "create_date",
            "activity_ids", "message_ids", "message_follower_ids",
        }:
            return True
        field = self._fields.get(field_name)
        if not field:
            return True
        normalized = field_name.lower()
        if any(word in normalized for word in ("password", "passwd", "token", "secret", "apikey", "api_key", "binary", "attachment")):
            return True
        if field.type in {"binary", "one2many"}:
            return True
        return False

    def _audit_values(self, values):
        result = {}
        for field_name, value in (values or {}).items():
            if self._audit_is_excluded_field(field_name):
                continue
            field = self._fields[field_name]
            if field.type == "many2one":
                if hasattr(value, "id"):
                    value = value.id
                if value:
                    related = self.env[field.comodel_name].browse(value)
                    result[field_name] = related.display_name if related.exists() else False
                else:
                    result[field_name] = False
            elif field.type == "many2many":
                ids = value if isinstance(value, (list, tuple, set)) else []
                result[field_name] = [self.env[field.comodel_name].browse(item).display_name for item in ids if isinstance(item, int)]
            elif field.type == "selection":
                result[field_name] = value
            elif field.type in {"date", "datetime"}:
                result[field_name] = str(value) if value else False
            elif hasattr(value, "ids"):
                result[field_name] = value.ids
            else:
                result[field_name] = value
        return result

    def _audit_record_values(self):
        vals = {}
        for field_name in self._fields:
            if field_name in vals or self._audit_is_excluded_field(field_name):
                continue
            field = self._fields[field_name]
            if len(vals) >= 30:
                break
            try:
                value = getattr(self, field_name)
                if field.type == "many2one":
                    vals[field_name] = value.display_name if value else False
                elif field.type in {"many2many", "one2many"}:
                    vals[field_name] = value.mapped("display_name")[:20]
                elif field.type not in {"binary"}:
                    vals[field_name] = value
            except Exception:
                continue
        return vals

    def _audit_action_for_vals(self, vals):
        if "active" in vals:
            return "RESTORE" if vals["active"] else "ARCHIVE"
        if vals.get("state") == "submitted":
            return "SUBMIT"
        if vals.get("state") == "approved":
            return "APPROVE"
        if vals.get("state") == "rejected":
            return "REJECT"
        if vals.get("status") == "final":
            return "PUBLISH"
        if vals.get("status") == "draft":
            return "UNPUBLISH"
        return "UPDATE"

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        if not self.env.context.get("disable_audit"):
            for record, vals in zip(records, vals_list):
                sanitized = self.env["erpobe.audit.log"]._sanitize_values(
                    record._audit_values(vals)
                )
                self.env["erpobe.audit.log"].log_event(
                    "CREATE", record._name, record,
                    new_values=sanitized,
                    changed_fields=list(sanitized),
                    description="Record dibuat: %s" % (record.display_name or record.id),
                    is_sensitive=record._name in {
                        "erpobe.master.mahasiswa", "erpobe.master.dosen",
                        "erpobe.grade.komponen", "erpobe.report.khs",
                        "erpobe.input.nilai",
                    },
                )
        return records

    def write(self, vals):
        if self.env.context.get("disable_audit"):
            return super().write(vals)
        snapshots = {}
        for record in self:
            snapshots[record.id] = record._audit_record_values()
        result = super().write(vals)
        for record in self:
            old_values = snapshots[record.id]
            new_values = record._audit_record_values()
            changed_fields = [
                field_name for field_name in vals
                if field_name in new_values
                and old_values.get(field_name) != new_values.get(field_name)
            ]
            if not changed_fields:
                continue
            action_type = self._audit_action_for_vals(vals)
            old_subset = {field_name: old_values.get(field_name) for field_name in changed_fields}
            new_subset = {field_name: new_values.get(field_name) for field_name in changed_fields}
            self.env["erpobe.audit.log"].log_event(
                action_type, record._name, record,
                old_values=old_subset,
                new_values=new_subset,
                changed_fields=changed_fields,
                description="%s record: %s" % (action_type, record.display_name or record.id),
                is_sensitive=record._name in {
                    "erpobe.master.mahasiswa", "erpobe.master.dosen",
                    "erpobe.grade.komponen", "erpobe.report.khs",
                    "erpobe.input.nilai",
                },
            )
        return result

    def unlink(self):
        snapshots = []
        if not self.env.context.get("disable_audit"):
            snapshots = [(record.id, record.display_name, record._audit_record_values()) for record in self]
        result = super().unlink()
        if result:
            for record_id, record_name, old_values in snapshots:
                self.env["erpobe.audit.log"].log_event(
                    "DELETE", self._name, None,
                    old_values=old_values,
                    changed_fields=list(old_values),
                    description="Record dihapus: %s" % (record_name or record_id),
                    severity="warning",
                    record_id=record_id,
                    record_name_snapshot=record_name,
                )
        return result
