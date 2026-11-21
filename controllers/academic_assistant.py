from odoo import http
from odoo.exceptions import AccessError
from odoo.http import request

from .academic_assistant_service import AcademicAssistantService


class AcademicAssistantController(http.Controller):
    @http.route(
        "/web/erpobe/assistant/query",
        type="jsonrpc",
        auth="user",
        methods=["POST"],
    )
    def academic_assistant_query(
        self, question=None, context=None, page_context=None, **kwargs
    ):
        if not request.env.user.has_group("base.group_user"):
            raise AccessError("Academic Assistant hanya tersedia bagi pengguna internal.")
        if kwargs:
            return {
                "type": "warning",
                "title": "Permintaan tidak valid",
                "message": "Permintaan memuat parameter yang tidak didukung.",
                "data": {},
                "source": "",
                "context": {},
                "suggested_questions": [],
            }
        if not isinstance(question, str) or not question.strip():
            return {
                "type": "clarification",
                "title": "Pertanyaan kosong",
                "message": "Tulis pertanyaan akademik terlebih dahulu.",
                "data": {},
                "source": "",
                "context": {},
                "suggested_questions": [],
            }
        question = question.strip()
        if len(question) > 500:
            return {
                "type": "clarification",
                "title": "Pertanyaan terlalu panjang",
                "message": "Pertanyaan maksimal 500 karakter.",
                "data": {},
                "source": "",
                "context": {},
                "suggested_questions": [],
            }
        try:
            return AcademicAssistantService(request.env).answer(
                question,
                conversation_context=context,
                page_context=page_context,
            )
        except AccessError:
            return {
                "type": "warning",
                "title": "Akses data tidak tersedia",
                "message": (
                    "Akun Anda tidak memiliki izin untuk membaca data yang "
                    "diminta. Periksa akses model dan cakupan record Anda."
                ),
                "data": {},
                "source": "",
                "context": {},
                "suggested_questions": [],
            }
