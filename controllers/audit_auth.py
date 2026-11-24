from odoo import http
from odoo.http import request
from odoo.addons.web.controllers.session import Session


class ErpObeAuditSession(Session):

    @http.route('/web/session/logout', type='http', auth='none', readonly=True)
    def logout(self, redirect='/odoo'):
        uid = request.session.uid
        if uid:
            request.env["erpobe.audit.log"].with_context(
                audit_actor_id=uid,
                audit_source="security",
                audit_ip=request.httprequest.remote_addr,
                audit_user_agent=request.httprequest.headers.get("User-Agent"),
            ).log_event(
                "LOGOUT",
                event_type="SECURITY",
                source="security",
                status="success",
                description="Logout berhasil",
            )
        return super().logout(redirect=redirect)

    @http.route('/web/session/destroy', type='jsonrpc', auth='user', readonly=True)
    def destroy(self):
        uid = request.session.uid
        if uid:
            request.env["erpobe.audit.log"].with_context(
                audit_actor_id=uid,
                audit_source="security",
                audit_ip=request.httprequest.remote_addr,
                audit_user_agent=request.httprequest.headers.get("User-Agent"),
            ).log_event(
                "LOGOUT",
                event_type="SECURITY",
                source="security",
                status="success",
                description="Session destroyed",
            )
        return super().destroy()
