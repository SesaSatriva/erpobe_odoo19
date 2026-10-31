from odoo import http
from odoo.http import request

from .helpers import TritonPublicHelpers


class TritonTracking(http.Controller, TritonPublicHelpers):

    @http.route(['/tracking', '/triton/tracking'], type='http', auth='public', website=True)
    def triton_tracking(self, **kwargs):
        self._rate_limit()
        prodis = request.env['erpobe.master.prodi'].sudo().search([('active', '=', True)], order='name asc')
        students = request.env['erpobe.master.mahasiswa'].sudo()
        teachers = request.env['erpobe.master.dosen'].sudo()
        offers = request.env['erpobe.akademik.penawaran'].sudo().search([], order='tahun_ajaran desc')
        validator = request.env['erpobe.weight.validation'].sudo()
        tracking = []
        for prodi in prodis:
            tracking.append({'name': prodi.name, 'kode': prodi.kode, 'active_students': students.search_count([('prodi_id', '=', prodi.id), ('status_akademik', '=', 'aktif'), ('active', '=', True)]), 'graduated_students': students.search_count([('prodi_id', '=', prodi.id), ('status_akademik', '=', 'lulus')]), 'teachers': teachers.search_count([('prodi_ids', 'in', prodi.id), ('active', '=', True)]), 'weight_complete_percent': self._weight_completion(prodi.id, validator)})
        final_rps_by_year = {}
        for offer in offers:
            year = offer.tahun_ajaran.tahun_ajaran
            final_rps_by_year.setdefault(year, 0)
            final_rps_by_year[year] += offer.line_ids.filtered(lambda line: line.latest_rps_id.status == 'final').__len__()
        cohorts = []
        grouped = students._read_group([('active', '=', True)], groupby=['prodi_id', 'angkatan'], aggregates=['__count'])
        for prodi, angkatan, count in grouped:
            cohorts.append({'prodi': prodi.display_name if prodi else '', 'angkatan': angkatan or '', 'jumlah': count})
        return request.render('erpobe.triton_tracking_page', {'tracking': tracking, 'cohorts': cohorts, 'rps_years': [{'year': year, 'count': count} for year, count in sorted(final_rps_by_year.items(), reverse=True)]})
