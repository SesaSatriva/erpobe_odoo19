from odoo import http
from odoo.http import request

from .const import _CPL_TYPES, _PAGE_SIZE
from .helpers import TritonPublicHelpers


class TritonMain(http.Controller, TritonPublicHelpers):

    @http.route(['/', '/triton'], type='http', auth='public', website=True, sitemap=True)
    def triton_home(self, **kwargs):
        self._rate_limit()
        comparison = self._comparison_data()
        stats = self._public_stats(comparison)
        faculties = request.env['erpobe.master.fakultas'].sudo().search([('active', '=', True)], order='name asc', limit=6)
        featured = request.env['erpobe.master.prodi'].sudo().search([('active', '=', True)], order='name asc', limit=6)
        return request.render('erpobe.triton_home_page', {'stats': stats, 'comparison': comparison, 'faculties': [self._safe_faculty(item) for item in faculties], 'featured_prodi': [self._safe_prodi(item) for item in featured], 'people_enabled': self._people_enabled()})

    @http.route(['/cari', '/triton/cari'], type='http', auth='public', website=True)
    def triton_search(self, q='', category='all', page=1, **kwargs):
        self._rate_limit()
        q = (q or '').strip()[:100]
        category = category if category in {'all', 'mahasiswa', 'dosen', 'prodi', 'fakultas', 'mata-kuliah', 'cpl'} else 'all'
        try:
            page_number = max(1, int(page))
        except (TypeError, ValueError):
            page_number = 1
        page_size = self._page_size(request.httprequest.args.get('limit'))
        models = {'mahasiswa': ('erpobe.master.mahasiswa', self._safe_student), 'dosen': ('erpobe.master.dosen', self._safe_dosen), 'prodi': ('erpobe.master.prodi', self._safe_prodi), 'fakultas': ('erpobe.master.fakultas', self._safe_faculty), 'mata-kuliah': ('erpobe.master.matakuliah', None), 'cpl': ('erpobe.akademik.cpl', None)}
        categories = []
        for key in ('mahasiswa', 'dosen', 'prodi', 'fakultas', 'mata-kuliah', 'cpl'):
            categories.append({'key': key, 'label': {'mahasiswa': 'Mahasiswa', 'dosen': 'Dosen', 'prodi': 'Program Studi', 'fakultas': 'Fakultas', 'mata-kuliah': 'Mata Kuliah', 'cpl': 'CPL'}[key]})
        results = []
        totals = 0
        chosen = [category] if category != 'all' else list(models)
        datasets = []
        for key in chosen:
            if key in ('mahasiswa', 'dosen') and (not self._people_enabled()):
                continue
            model_name, serializer = models[key]
            model = request.env[model_name].sudo()
            domain = []
            if key in ('mahasiswa', 'dosen'):
                domain.extend(self._public_person_domain())
            if key == 'mahasiswa':
                domain.append(('status_akademik', 'in', ['aktif', 'lulus', 'cuti']))
            if q:
                search_fields = {
                    'mahasiswa': ('name', 'nim'),
                    'dosen': ('name', 'nip'),
                    'prodi': ('name', 'kode'),
                    'fakultas': ('name', 'kode'),
                    'mata-kuliah': ('name', 'kode_mk'),
                    'cpl': ('name', 'kode_cpl'),
                }[key]
                if len(search_fields) > 1:
                    domain.extend(['|'] * (len(search_fields) - 1))
                for field in search_fields:
                    domain.append((field, 'ilike', q))
            total = model.search_count(domain)
            datasets.append((key, model, serializer, domain, total))
            totals += total
        pager = self._pager(
            '/cari',
            page_number,
            totals,
            {'q': q, 'category': category, 'limit': page_size},
            page_size=page_size,
        )
        global_start = (pager['page'] - 1) * page_size
        global_cursor = 0
        category_labels = {item['key']: item['label'] for item in categories}
        for key, model, serializer, domain, total in datasets:
            overlap_start = max(global_start, global_cursor)
            overlap_end = min(global_start + page_size, global_cursor + total)
            records = model.browse()
            if overlap_end > overlap_start:
                records = model.search(
                    domain,
                    order='name asc',
                    limit=overlap_end - overlap_start,
                    offset=overlap_start - global_cursor,
                )
            global_cursor += total
            for record in records:
                if serializer:
                    item = serializer(record)
                elif key == 'mata-kuliah':
                    fields = record.read(['name', 'kode_mk', 'sks', 'prodi_id'])[0]
                    item = {'id': record.id, 'name': fields['name'], 'kode': fields['kode_mk'], 'sks': fields['sks'], 'prodi': fields['prodi_id'][1] if fields['prodi_id'] else ''}
                else:
                    fields = record.read(['kode_cpl', 'name', 'jenis_cpl', 'prodi_id'])[0]
                    item = {'id': record.id, 'name': fields['name'], 'kode': fields['kode_cpl'], 'jenis': _CPL_TYPES.get(fields['jenis_cpl'], 'Lainnya'), 'prodi': fields['prodi_id'][1] if fields['prodi_id'] else ''}
                item['category'] = key
                item['category_label'] = category_labels.get(key, key)
                results.append(item)
        return request.render('erpobe.triton_search_page', {
            'q': q,
            'category': category,
            'categories': categories,
            'results': results,
            'total': totals,
            'page': pager['page'],
            'page_count': pager['page_count'],
            'page_size': pager['page_size'],
            'page_sizes': pager['page_sizes'],
            'range_start': pager['start'],
            'range_end': pager['end'],
            'previous_url': pager['previous'],
            'next_url': pager['next'],
            'people_enabled': self._people_enabled(),
        })

    @http.route(['/tentang', '/triton/tentang'], type='http', auth='public', website=True)
    def triton_about(self, **kwargs):
        self._rate_limit()
        return request.render('erpobe.triton_about_page')

    @http.route(['/panduan', '/triton/panduan'], type='http', auth='public', website=True)
    def triton_guide(self, **kwargs):
        self._rate_limit()
        return request.render('erpobe.triton_guide_page')

    @http.route(['/faq', '/triton/faq'], type='http', auth='public', website=True)
    def triton_faq(self, **kwargs):
        self._rate_limit()
        return request.render('erpobe.triton_faq_page')

    @http.route(['/kontak', '/triton/kontak'], type='http', auth='public', website=True)
    def triton_contact(self, **kwargs):
        self._rate_limit()
        return request.render('erpobe.triton_contact_page')

    @http.route(['/privasi', '/kebijakan-privasi', '/triton/kebijakan-privasi'], type='http', auth='public', website=True)
    def triton_privacy(self, **kwargs):
        self._rate_limit()
        return request.render('erpobe.triton_privacy_page', {'people_enabled': self._people_enabled()})

    @http.route(['/metodologi', '/triton/metodologi'], type='http', auth='public', website=True)
    def triton_methodology(self, **kwargs):
        self._rate_limit()
        return request.render('erpobe.triton_methodology_page')
