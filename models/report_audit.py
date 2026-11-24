from odoo import models


class ErpObeIrActionsReport(models.Model):
    _inherit = "ir.actions.report"

    def _erpobe_log_report(self, report_ref, res_ids, report_type, status="success"):
        report = self._get_report(report_ref)
        if not (report.report_name or "").startswith("erpobe.") and report.model not in (
            "erpobe.report.khs",
            "erpobe.akademik.rps",
        ):
            return
        record = self.env[report.model].browse(res_ids[0]) if res_ids else None
        if len(res_ids or []) > 1:
            record_name = "%s record(s)" % len(res_ids)
        else:
            record_name = record.display_name if record else False
        self.env["erpobe.audit.log"].with_context(
            audit_source="report",
            audit_correlation_id="report:%s:%s" % (
                report.id,
                ",".join(str(record_id) for record_id in (res_ids or [])),
            ),
        ).log_event(
            "REPORT_GENERATION",
            event_type="DATA_OPERATION",
            model_name=report.model,
            record=record,
            record_id=res_ids[0] if len(res_ids or []) == 1 else False,
            record_name_snapshot=record_name,
            description="Generate report %s" % report.name,
            source="report",
            status=status,
            is_sensitive=report.model in ("erpobe.report.khs", "erpobe.grade.komponen"),
            metadata={
                "report_name": report.name,
                "report_template": report.report_name,
                "format": report_type,
                "record_count": len(res_ids or []),
            },
        )

    def _render_qweb_pdf(self, report_ref, res_ids=None, data=None):
        result = super()._render_qweb_pdf(report_ref, res_ids=res_ids, data=data)
        self._erpobe_log_report(report_ref, res_ids, "pdf")
        return result

    def _render_qweb_text(self, report_ref, docids, data=None):
        result = super()._render_qweb_text(report_ref, docids, data=data)
        self._erpobe_log_report(report_ref, docids, "text")
        return result

    def _render_qweb_html(self, report_ref, docids, data=None):
        result = super()._render_qweb_html(report_ref, docids, data=data)
        self._erpobe_log_report(report_ref, docids, "html")
        return result
