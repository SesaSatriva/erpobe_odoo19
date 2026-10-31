from odoo import http
from werkzeug.exceptions import NotFound
from odoo.http import request

from .const import _CPL_TYPES
from .helpers import TritonPublicHelpers


class TritonFakultas(http.Controller, TritonPublicHelpers):

    @http.route(['/fakultas', '/triton/fakultas'], type='http', auth='public', website=True)
    def triton_faculties(self, **kwargs):
        self._rate_limit()
        faculties = request.env['erpobe.master.fakultas'].sudo().search([('active', '=', True)], order='name asc')
        results = []
        for faculty in faculties:
            prodis = faculty.prodi_ids.filtered('active')
            results.append({**self._safe_faculty(faculty), 'prodi_count': len(prodis), 'student_count': request.env['erpobe.master.mahasiswa'].sudo().search_count([('prodi_id', 'in', prodis.ids), ('active', '=', True), ('status_akademik', '=', 'aktif')]), 'prodis': [self._safe_prodi(item) for item in prodis]})
        return request.render('erpobe.triton_faculty_list_page', {'faculties': results})

    @http.route(['/fakultas/<int:faculty_id>', '/triton/fakultas/<int:faculty_id>'], type='http', auth='public', website=True)
    def triton_faculty_detail(self, faculty_id, **kwargs):
        self._rate_limit()
        faculty = request.env['erpobe.master.fakultas'].sudo().browse(faculty_id)
        if not faculty.exists() or not faculty.active:
            raise NotFound()
        prodis = faculty.prodi_ids.filtered('active')
        stats = {'prodi_count': len(prodis), 'dosen_count': request.env['erpobe.master.dosen'].sudo().search_count([('prodi_ids', 'in', prodis.ids), ('active', '=', True)]), 'student_count': request.env['erpobe.master.mahasiswa'].sudo().search_count([('prodi_id', 'in', prodis.ids), ('active', '=', True), ('status_akademik', '=', 'aktif')])}
        return request.render('erpobe.triton_faculty_detail_page', {'faculty': self._safe_faculty(faculty), 'stats': stats, 'prodis': [self._safe_prodi(item) for item in prodis]})

    @http.route(['/prodi/<int:prodi_id>', '/triton/prodi/<int:prodi_id>'], type='http', auth='public', website=True)
    def triton_prodi_detail(self, prodi_id, tab='profil', q='', angkatan='', status='', page=1, **kwargs):
        self._rate_limit()
        prodi = request.env['erpobe.master.prodi'].sudo().browse(prodi_id)
        if not prodi.exists() or not prodi.active:
            raise NotFound()
        tab = tab if tab in {'profil', 'dosen', 'mahasiswa', 'cpl', 'mata-kuliah'} else 'profil'
        try:
            page_number = max(1, int(page))
        except (TypeError, ValueError):
            page_number = 1
        data = {'prodi': self._safe_prodi(prodi), 'tab': tab, 'query': (q or '').strip()[:100], 'angkatan_filter': angkatan, 'status_filter': status, 'people_enabled': self._people_enabled(), 'stats': {'dosen': request.env['erpobe.master.dosen'].sudo().search_count([('prodi_ids', 'in', prodi.id), ('active', '=', True)]), 'mahasiswa': request.env['erpobe.master.mahasiswa'].sudo().search_count([('prodi_id', '=', prodi.id), ('active', '=', True)]), 'cpl': request.env['erpobe.akademik.cpl'].sudo().search_count([('prodi_id', '=', prodi.id)])}, 'results': [], 'pager': False, 'years': request.env['erpobe.master.rombel'].sudo().search_read([('prodi_id', '=', prodi.id)], ['angkatan'], order='angkatan desc', limit=100)}
        query_args = {key: value for key, value in {'tab': tab, 'q': q, 'angkatan': angkatan, 'status': status}.items() if value}
        if tab in ('dosen', 'mahasiswa') and (not data['people_enabled']):
            data['privacy_disabled'] = True
            return request.render('erpobe.triton_prodi_detail_page', data)
        if tab == 'dosen':
            domain = [('prodi_ids', 'in', prodi.id), *self._public_person_domain()]
            if q:
                domain.append(('name', 'ilike', (q or '').strip()[:100]))
            records, total = self._read_domain_page('erpobe.master.dosen', domain, page_number, self._safe_dosen)
            data['results'] = records
            data['pager'] = self._pager(f'/prodi/{prodi.id}', page_number, total, query_args)
        elif tab == 'mahasiswa':
            domain = [('prodi_id', '=', prodi.id), *self._public_person_domain()]
            if q:
                domain.append(('name', 'ilike', (q or '').strip()[:100]))
            if angkatan.isdigit():
                domain.append(('angkatan', '=', int(angkatan)))
            if status in ('aktif', 'lulus', 'cuti'):
                domain.append(('status_akademik', '=', status))
            records, total = self._read_domain_page('erpobe.master.mahasiswa', domain, page_number, self._safe_student)
            data['results'] = records
            data['pager'] = self._pager(f'/prodi/{prodi.id}', page_number, total, query_args)
        elif tab == 'cpl':
            records = request.env['erpobe.akademik.cpl'].sudo().search([('prodi_id', '=', prodi.id)], order='kode_cpl asc')
            data['results'] = [{'id': item.id, 'name': item.name, 'kode': item.kode_cpl, 'jenis': _CPL_TYPES.get(item.jenis_cpl, 'Lainnya'), 'cpmk': [mapping.cpmk_id.display_name for mapping in item.cpmk_mapping_ids]} for item in records]
        elif tab == 'mata-kuliah':
            rps_records = request.env['erpobe.akademik.rps'].sudo().search([('prodi_id', '=', prodi.id), ('status', '=', 'final')], order='tahun_ajaran_id desc, matakuliah_id asc')
            data['results'] = [{'name': rps.matakuliah_id.name, 'kode': rps.matakuliah_id.kode_mk, 'sks': rps.matakuliah_id.sks, 'tahun_ajaran': rps.tahun_ajaran_id.tahun_ajaran or '', 'semester': rps.semester_akademik or ''} for rps in rps_records]
        return request.render('erpobe.triton_prodi_detail_page', data)
