from odoo import http
from werkzeug.exceptions import NotFound
from odoo.http import request

from .const import _CPL_TYPES
from .helpers import TritonPublicHelpers


class TritonFakultas(http.Controller, TritonPublicHelpers):

    @http.route(['/fakultas', '/triton/fakultas'], type='http', auth='public', website=True)
    def triton_faculties(self, **kwargs):
        self._rate_limit()
        faculties, pagination = self._list_page(
            request.env['erpobe.master.fakultas'].sudo(),
            [('active', '=', True)],
            '/fakultas',
            {'name': ('name asc, id asc', 'Nama A–Z'), 'code': ('kode asc, id asc', 'Kode')},
            'name asc, id asc',
            ('name', 'kode'),
        )
        results = []
        for faculty in faculties:
            prodis = faculty.prodi_ids.filtered('active')
            results.append({**self._safe_faculty(faculty), 'prodi_count': len(prodis), 'student_count': request.env['erpobe.master.mahasiswa'].sudo().search_count([('prodi_id', 'in', prodis.ids), ('active', '=', True), ('status_akademik', '=', 'aktif')]), 'prodis': [self._safe_prodi(item) for item in prodis]})
        return request.render('erpobe.triton_faculty_list_page', {
            'faculties': results,
            'pagination': pagination,
            'list_action': '/fakultas',
        })

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
    def triton_prodi_detail(self, prodi_id, tab='profil', q='', angkatan='', status='', **kwargs):
        self._rate_limit()
        prodi = request.env['erpobe.master.prodi'].sudo().browse(prodi_id)
        if not prodi.exists() or not prodi.active:
            raise NotFound()
        tab = tab if tab in {'profil', 'dosen', 'mahasiswa', 'cpl', 'mata-kuliah'} else 'profil'
        data = {'prodi': self._safe_prodi(prodi), 'tab': tab, 'query': (q or '').strip()[:100], 'angkatan_filter': angkatan, 'status_filter': status, 'people_enabled': self._people_enabled(), 'stats': {'dosen': request.env['erpobe.master.dosen'].sudo().search_count([('prodi_ids', 'in', prodi.id), ('active', '=', True)]), 'mahasiswa': request.env['erpobe.master.mahasiswa'].sudo().search_count([('prodi_id', '=', prodi.id), ('active', '=', True)]), 'cpl': request.env['erpobe.akademik.cpl'].sudo().search_count([('prodi_id', '=', prodi.id)])}, 'results': [], 'pagination': False, 'list_action': f'/prodi/{prodi.id}', 'years': request.env['erpobe.master.rombel'].sudo().search_read([('prodi_id', '=', prodi.id)], ['angkatan'], order='angkatan desc', limit=100)}
        if tab in ('dosen', 'mahasiswa') and (not data['people_enabled']):
            data['privacy_disabled'] = True
            return request.render('erpobe.triton_prodi_detail_page', data)
        if tab == 'dosen':
            domain = [('prodi_ids', 'in', prodi.id), *self._public_person_domain()]
            records, pagination = self._list_page(
                request.env['erpobe.master.dosen'].sudo(),
                domain,
                f'/prodi/{prodi.id}',
                {'name': ('name asc, id asc', 'Nama A–Z'), 'title': ('jabatan_fungsional asc, name asc', 'Jabatan')},
                'name asc, id asc',
                ('name', 'nip'),
            )
            data['results'] = [self._safe_dosen(record) for record in records]
            data['pagination'] = pagination
        elif tab == 'mahasiswa':
            domain = [('prodi_id', '=', prodi.id), *self._public_person_domain()]
            if angkatan.isdigit():
                domain.append(('angkatan', '=', int(angkatan)))
            if status in ('aktif', 'lulus', 'cuti'):
                domain.append(('status_akademik', '=', status))
            cohort_options = [('', 'Semua angkatan')] + [
                (str(year['angkatan']), str(year['angkatan']))
                for year in data['years']
            ]
            records, pagination = self._list_page(
                request.env['erpobe.master.mahasiswa'].sudo(),
                domain,
                f'/prodi/{prodi.id}',
                {'name': ('name asc, id asc', 'Nama A–Z'), 'cohort': ('angkatan desc, name asc', 'Angkatan terbaru')},
                'name asc, id asc',
                ('name', 'nim'),
                (
                    ('angkatan', 'Angkatan', cohort_options),
                    ('status', 'Status', (
                        ('', 'Semua status'),
                        ('aktif', 'Aktif'),
                        ('lulus', 'Lulus'),
                        ('cuti', 'Cuti'),
                    )),
                ),
            )
            data['results'] = [self._safe_student(record) for record in records]
            data['pagination'] = pagination
        elif tab == 'cpl':
            records, data['pagination'] = self._list_page(
                request.env['erpobe.akademik.cpl'].sudo(),
                [('prodi_id', '=', prodi.id)],
                f'/prodi/{prodi.id}',
                {'code': ('kode_cpl asc, id asc', 'Kode CPL'), 'name': ('name asc, id asc', 'Nama A–Z')},
                'kode_cpl asc, id asc',
                ('name', 'kode_cpl'),
            )
            data['results'] = [{'id': item.id, 'name': item.name, 'kode': item.kode_cpl, 'jenis': _CPL_TYPES.get(item.jenis_cpl, 'Lainnya'), 'cpmk': [mapping.cpmk_id.display_name for mapping in item.cpmk_mapping_ids]} for item in records]
        elif tab == 'mata-kuliah':
            rps_records, data['pagination'] = self._list_page(
                request.env['erpobe.akademik.rps'].sudo(),
                [('prodi_id', '=', prodi.id), ('status', '=', 'final')],
                f'/prodi/{prodi.id}',
                {'course': ('matakuliah_name asc, id asc', 'Mata kuliah A–Z'), 'term': ('tahun_ajaran_id desc, matakuliah_name asc, id asc', 'Tahun ajaran terbaru')},
                'tahun_ajaran_id desc, matakuliah_id asc, id asc',
                ('matakuliah_name', 'kode_mk'),
            )
            data['results'] = [{'name': rps.matakuliah_id.name, 'kode': rps.matakuliah_id.kode_mk, 'sks': rps.matakuliah_id.sks, 'tahun_ajaran': rps.tahun_ajaran_id.tahun_ajaran or '', 'semester': rps.semester_akademik or ''} for rps in rps_records]
        return request.render('erpobe.triton_prodi_detail_page', data)
