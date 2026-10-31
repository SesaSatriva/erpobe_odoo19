import csv
import io

from odoo import http
from odoo.http import request

from .const import _CPL_TYPES
from .helpers import TritonPublicHelpers


class TritonPerbandingan(http.Controller, TritonPublicHelpers):

    @http.route(['/perbandingan-cpl', '/triton/perbandingan'], type='http', auth='public', website=True)
    def triton_comparison(self, **kwargs):
        self._rate_limit()
        params = self._comparison_params()
        comparison = self._comparison_data(**params)
        faculties = request.env['erpobe.master.fakultas'].sudo().search([('active', '=', True)], order='name asc')
        prodis = request.env['erpobe.master.prodi'].sudo().search([('active', '=', True)], order='name asc')
        return request.render('erpobe.triton_comparison_page', {'comparison': comparison, 'faculties': [self._safe_faculty(item) for item in faculties], 'prodis': [self._safe_prodi(item) for item in prodis], 'cpl_types': [{'key': key, 'name': value} for key, value in _CPL_TYPES.items()], 'params': params})

    @http.route('/triton/api/perbandingan-cpl', type='http', auth='public', website=True, methods=['GET'])
    def triton_comparison_json(self, **kwargs):
        self._rate_limit()
        return request.make_json_response(self._comparison_data(**self._comparison_params()))

    @http.route('/perbandingan-cpl.csv', type='http', auth='public', website=True, methods=['GET'])
    def triton_comparison_csv(self, **kwargs):
        self._rate_limit()
        data = self._comparison_data(**self._comparison_params())
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Program Studi', *[row['name'] for row in data['categories']]])
        for prodi in data['prodis']:
            writer.writerow([prodi['name'], *[score if score is not None else '' for score in prodi['scores']]])
        return request.make_response(output.getvalue(), headers=[('Content-Type', 'text/csv; charset=utf-8'), ('Content-Disposition', 'attachment; filename="perbandingan-cpl.csv"')])
