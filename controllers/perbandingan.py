import csv
import io
from urllib.parse import urlencode

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
        csv_args = []
        if params['year_start']:
            csv_args.append(('tahun_awal', params['year_start']))
        if params['year_end']:
            csv_args.append(('tahun_akhir', params['year_end']))
        if params['semester']:
            csv_args.append(('semester', params['semester']))
        if params['faculty_id']:
            csv_args.append(('fakultas_id', params['faculty_id']))
        for prodi_id in params['prodi_ids']:
            csv_args.append(('prodi_id', prodi_id))
        if params['jenis_cpl']:
            csv_args.append(('jenis_cpl', params['jenis_cpl']))
        csv_url = '/perbandingan-cpl.csv'
        if csv_args:
            csv_url += '?' + urlencode(csv_args)
        return request.render('erpobe.triton_comparison_page', {'comparison': comparison, 'faculties': [self._safe_faculty(item) for item in faculties], 'prodis': [self._safe_prodi(item) for item in prodis], 'cpl_types': [{'key': key, 'name': value} for key, value in _CPL_TYPES.items()], 'params': params, 'csv_url': csv_url})

    @http.route('/triton/api/perbandingan-cpl', type='http', auth='public', website=True, methods=['GET'])
    def triton_comparison_json(self, **kwargs):
        self._rate_limit()
        return request.make_json_response(self._comparison_data(**self._comparison_params()))

    @http.route('/triton/api/perbandingan-cpl/detail', type='http', auth='public', website=True, methods=['GET'])
    def triton_comparison_detail_json(self, **kwargs):
        self._rate_limit()
        params = self._comparison_params()
        category_key = params['jenis_cpl']
        if not category_key:
            category_key = kwargs.get('jenis_cpl')
        if category_key not in _CPL_TYPES:
            category_key = None
        params['jenis_cpl'] = category_key
        comparison = self._comparison_data(**params)
        detail = next(
            (item for item in comparison['details'] if item['key'] == category_key),
            None,
        )
        return request.make_json_response({
            'category': detail,
            'prodis': [
                {'id': prodi['id'], 'name': prodi['name'], 'kode': prodi['kode']}
                for prodi in comparison['prodis']
            ],
            'params': {
                'year_start': comparison['year_start'],
                'year_end': comparison['year_end'],
                'semester': comparison['semester'],
                'prodi_ids': comparison['prodi_ids'],
            },
            'methodology': comparison['methodology'],
        })

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
