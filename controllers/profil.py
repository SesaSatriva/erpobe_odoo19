from odoo import http
from werkzeug.exceptions import NotFound
from odoo.http import request

from .helpers import TritonPublicHelpers


class TritonProfil(http.Controller, TritonPublicHelpers):

    @http.route(['/dosen/<int:dosen_id>', '/triton/dosen/<int:dosen_id>'], type='http', auth='public', website=True)
    def triton_dosen_profile(self, dosen_id, **kwargs):
        self._rate_limit()
        data = self._person_profile('dosen', dosen_id)
        if not data:
            raise NotFound()
        return request.render('erpobe.triton_person_profile_page', data)

    @http.route(['/mahasiswa/<int:mahasiswa_id>', '/triton/mahasiswa/<int:mahasiswa_id>'], type='http', auth='public', website=True)
    def triton_mahasiswa_profile(self, mahasiswa_id, **kwargs):
        self._rate_limit()
        data = self._person_profile('mahasiswa', mahasiswa_id)
        if not data:
            raise NotFound()
        return request.render('erpobe.triton_person_profile_page', data)
