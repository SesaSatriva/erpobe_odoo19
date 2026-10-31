import csv
import io
import math
import re
import threading
import time

from werkzeug.exceptions import NotFound, TooManyRequests
from werkzeug.urls import url_encode

from odoo import http
from odoo.http import request

from .const import _CPL_TYPES, _PAGE_SIZE, _RATE_HITS, _RATE_LIMIT, _RATE_LOCK, _RATE_WINDOW



class TritonPublicHelpers:

    def _read_domain_page(self, model_name, domain, page, serializer, order='name asc'):
        model = request.env[model_name].sudo()
        total = model.search_count(domain)
        page = max(1, page)
        records = model.search(domain, order=order, limit=_PAGE_SIZE, offset=(page - 1) * _PAGE_SIZE)
        return ([serializer(record) for record in records], total)

    def _safe_prodi(self, record):
        values = record.sudo().read(['name', 'kode', 'fakultas_id'])[0]
        faculty = values['fakultas_id']
        return {'id': record.id, 'name': values['name'], 'kode': values['kode'], 'fakultas': faculty[1] if faculty else ''}

    def _public_stats(self):
        env = request.env
        Faculty = env['erpobe.master.fakultas'].sudo()
        Prodi = env['erpobe.master.prodi'].sudo()
        Student = env['erpobe.master.mahasiswa'].sudo()
        Dosen = env['erpobe.master.dosen'].sudo()
        Course = env['erpobe.master.matakuliah'].sudo()
        Cpl = env['erpobe.akademik.cpl'].sudo()
        Cpmk = env['erpobe.akademik.cpmk'].sudo()
        Rps = env['erpobe.akademik.rps'].sudo()
        students_domain = [('active', '=', True), ('status_akademik', '=', 'aktif')]
        return {'faculties': Faculty.search_count([('active', '=', True)]), 'prodis': Prodi.search_count([('active', '=', True)]), 'dosen': Dosen.search_count([('active', '=', True)]), 'mahasiswa_aktif': Student.search_count(students_domain), 'courses': Course.search_count([]), 'cpl_count': Cpl.search_count([]), 'cpmk_count': Cpmk.search_count([]), 'rps_final': Rps.search_count([('status', '=', 'final')]), 'institutional_average': self._institutional_average()}

    def _comparison_params(self):
        args = request.httprequest.args
        values = args.getlist('prodi_id') or args.getlist('prodi_ids')
        prodi_ids = []
        for value in values[:6]:
            if value.isdigit():
                prodi_ids.append(int(value))
        year_start = args.get('tahun_awal') or None
        year_end = args.get('tahun_akhir') or None
        if year_start and (not re.fullmatch('\\d{4}/\\d{4}', year_start)):
            year_start = None
        if year_end and (not re.fullmatch('\\d{4}/\\d{4}', year_end)):
            year_end = None
        semester = args.get('semester') or None
        if semester not in ('ganjil', 'genap', 'pendek'):
            semester = None
        faculty_id = args.get('fakultas_id') or None
        if faculty_id and (not faculty_id.isdigit()):
            faculty_id = None
        jenis_cpl = args.get('jenis_cpl') or None
        if jenis_cpl not in _CPL_TYPES:
            jenis_cpl = None
        return {'year_start': year_start, 'year_end': year_end, 'semester': semester, 'faculty_id': faculty_id, 'prodi_ids': prodi_ids, 'jenis_cpl': jenis_cpl}

    def _people_enabled(self):
        return request.env['ir.config_parameter'].sudo().get_param('erpobe.triton.public_people_enabled', 'False').lower() in ('1', 'true', 'yes')

    def _person_profile(self, kind, record_id):
        if not self._people_enabled():
            return False
        if kind == 'dosen':
            record = request.env['erpobe.master.dosen'].sudo().browse(record_id)
            if not record.exists() or not record.active or (not record.is_public_visible) or record.public_opt_out:
                return False
            courses = request.env['erpobe.master.matakuliah'].sudo().search(['|', ('koordinator_id', '=', record.id), ('tim_pengampu_ids', 'in', record.id)], order='name asc', limit=50)
            return {'person': self._safe_dosen(record), 'courses': [{'name': course.name, 'kode': course.kode_mk, 'prodi': course.prodi_id.name} for course in courses], 'kind': kind}
        record = request.env['erpobe.master.mahasiswa'].sudo().browse(record_id)
        if not record.exists() or not record.active or (not record.is_public_visible) or record.public_opt_out:
            return False
        return {'person': self._safe_student(record), 'courses': [], 'kind': kind}

    def _safe_dosen(self, record):
        values = record.sudo().read(['name', 'nip', 'jabatan_fungsional', 'prodi_ids'])[0]
        prodis = request.env['erpobe.master.prodi'].sudo().browse(values['prodi_ids'])
        return {'id': record.id, 'name': values['name'], 'identifier': self._mask_identifier(values['nip']), 'jabatan': values['jabatan_fungsional'] or 'Belum diatur', 'prodis': [self._safe_prodi(prodi) for prodi in prodis]}

    def _weight_completion(self, prodi_id, validator):
        rps_records = request.env['erpobe.akademik.rps'].sudo().search([('prodi_id', '=', prodi_id)])
        if not rps_records:
            return None
        complete = sum((bool(validator.validate_rps(rps)['complete']) for rps in rps_records))
        return round(complete * 100.0 / len(rps_records), 1)

    def _institutional_average(self):
        comparison = self._comparison_data(default_latest=True)
        scores = [score for prodi in comparison['prodis'] for score in prodi['scores'] if score is not None]
        return round(sum(scores) / len(scores), 1) if scores else False

    def _comparison_data(self, year_start=None, year_end=None, semester=None, faculty_id=None, prodi_ids=None, jenis_cpl=None, default_latest=False):
        env = request.env
        Year = env['erpobe.akademik.tahunajaran'].sudo()
        Prodi = env['erpobe.master.prodi'].sudo()
        Offer = env['erpobe.akademik.penawaran'].sudo()
        OfferLine = env['erpobe.akademik.penawaran.line'].sudo()
        Rps = env['erpobe.akademik.rps'].sudo()
        KrsLine = env['erpobe.akademik.krs.line'].sudo()
        GradeComponent = env['erpobe.grade.komponen'].sudo()
        validator = env['erpobe.weight.validation'].sudo()
        years = Year.search([], order='tahun_ajaran asc, semester asc')
        if default_latest and years:
            active = Year.search([('aktif', '=', True)], limit=1)
            year_start = year_end = active.tahun_ajaran if active else years[-1].tahun_ajaran
        if year_start and year_end and (year_start > year_end):
            year_start, year_end = (year_end, year_start)
        year_domain = []
        if year_start:
            year_domain.append(('tahun_ajaran', '>=', year_start))
        if year_end:
            year_domain.append(('tahun_ajaran', '<=', year_end))
        if semester in ('ganjil', 'genap', 'pendek'):
            year_domain.append(('semester', '=', semester))
        selected_years = Year.search(year_domain, order='tahun_ajaran asc, semester asc')
        available_years = sorted(set(years.mapped('tahun_ajaran')))
        offer_domain = [('tahun_ajaran', 'in', selected_years.ids)]
        offers = Offer.search(offer_domain) if selected_years else Offer
        prodi_domain = [('active', '=', True)]
        if faculty_id:
            prodi_domain.append(('fakultas_id', '=', faculty_id))
        candidates = Prodi.search(prodi_domain, order='name asc')
        selected_ids = list(dict.fromkeys(prodi_ids or []))[:6]
        if selected_ids:
            candidates = candidates.filtered(lambda record: record.id in selected_ids)
        else:
            candidates = candidates[:6]
        accumulators = {prodi.id: {kind: [] for kind in _CPL_TYPES} for prodi in candidates}
        warnings = {prodi.id: False for prodi in candidates}
        year_accumulators = {}
        offer_lines = OfferLine.search([('penawaran_id', 'in', offers.ids), ('prodi_id', 'in', candidates.ids)]) if offers and candidates else OfferLine
        for line in offer_lines:
            prodi_id = line.prodi_id.id
            final_versions = line.rps_ids.filtered(lambda item: item.status == 'final').sorted(key=lambda item: (item.version, item.id), reverse=True)
            if not final_versions:
                warnings[prodi_id] = True
                continue
            rps = final_versions[0]
            if not validator.validate_rps(rps)['complete']:
                warnings[prodi_id] = True
                continue
            krs_lines = KrsLine.search([('penawaran_line_id', '=', line.id), ('krs_id.state', '=', 'approved')])
            if not krs_lines:
                continue
            grade_rows = GradeComponent.search_read([('krs_line_id', 'in', krs_lines.ids)], ['krs_line_id', 'komponen_id', 'nilai'])
            grades_by_line = {}
            for row in grade_rows:
                grades_by_line.setdefault(row['krs_line_id'][0], {})[row['komponen_id'][0]] = row['nilai']
            component_weights = {}
            for row in rps.bobot_komponen_cpmk_ids:
                component_weights.setdefault(row.cpmk_id.id, []).append((row.komponen_penilaian.id, row.bobot_komponen_cpmk))
            cpl_weights = {}
            for row in rps.bobot_cpmk_cpl_ids:
                cpl_weights.setdefault(row.cpl_id.id, []).append((row.cpmk_id.id, row.bobot_cpmk_cpl))
            cpls = env['erpobe.akademik.cpl'].sudo().browse(list(cpl_weights))
            cpl_types = {row['id']: row['jenis_cpl'] for row in cpls.read(['jenis_cpl'])}
            year_name = line.tahun_ajaran_id.tahun_ajaran
            year_accumulators.setdefault(year_name, {})
            for krs_line in krs_lines:
                student_grades = grades_by_line.get(krs_line.id, {})
                cpmk_scores = {}
                for cpmk_id, weights in component_weights.items():
                    cpmk_scores[cpmk_id] = sum((student_grades.get(component_id, 0.0) * weight / 100.0 for component_id, weight in weights))
                for cpl_id, weights in cpl_weights.items():
                    total_weight = sum((weight for _, weight in weights))
                    if not total_weight:
                        continue
                    score = sum((cpmk_scores.get(cpmk_id, 0.0) * weight for cpmk_id, weight in weights)) / total_weight
                    kind = cpl_types.get(cpl_id) or 'lainnya'
                    if jenis_cpl and kind != jenis_cpl:
                        continue
                    accumulators[prodi_id][kind].append(score)
                    year_accumulators[year_name].setdefault((prodi_id, kind), []).append(score)
        prodi_results = []
        for prodi in candidates:
            scores = []
            for kind in _CPL_TYPES:
                values = accumulators[prodi.id][kind]
                scores.append(round(sum(values) / len(values), 2) if values else None)
            prodi_results.append({'id': prodi.id, 'name': prodi.name, 'kode': prodi.kode, 'scores': scores, 'warning': warnings[prodi.id]})
        categories = [{'key': key, 'name': value} for key, value in _CPL_TYPES.items() if not jenis_cpl or key == jenis_cpl]
        selected_indexes = [index for index, key in enumerate(_CPL_TYPES) if not jenis_cpl or key == jenis_cpl]
        for result in prodi_results:
            result['scores'] = [result['scores'][index] for index in selected_indexes]
            n = len(result['scores'])
            points = []
            for index, score in enumerate(result['scores']):
                angle = 2 * math.pi * index / max(n, 1) - math.pi / 2
                radius = (score or 0) * 0.78
                points.append(f'{100 + math.cos(angle) * radius:.2f},{100 + math.sin(angle) * radius:.2f}')
            result['radar_points'] = ' '.join(points)
        trend = []
        for year in sorted(year_accumulators):
            year_values = [score for (prodi_id, kind), values in year_accumulators[year].items() if prodi_id in candidates.ids and (not jenis_cpl or kind == jenis_cpl) for score in values]
            if year_values:
                trend.append({'year': year, 'average': round(sum(year_values) / len(year_values), 2)})
        return {'prodis': prodi_results, 'categories': categories, 'warnings': [result['name'] for result in prodi_results if result['warning']], 'years': available_years, 'year_start': year_start or '', 'year_end': year_end or '', 'semester': semester or '', 'faculty_id': int(faculty_id) if str(faculty_id or '').isdigit() else 0, 'prodi_ids': candidates.ids, 'jenis_cpl': jenis_cpl or '', 'trend': trend, 'target': 75, 'methodology': 'Nilai CPMK dihitung dari jumlah nilai komponen dikalikan bobot komponen pada RPS final. Nilai CPL dihitung dengan rumus Σ(nilai CPMK × bobot CPMK→CPL) / Σ bobot. Hanya RPS dengan seluruh kelompok bobot 100% dan KRS berstatus disetujui yang dihitung; agregat prodi adalah rata-rata pengamatan mahasiswa pada penawaran yang terpilih.'}

    def _mask_identifier(self, value):
        text = (value or '').strip()
        if not text:
            return ''
        if len(text) <= 4:
            return '*' * len(text)
        return f'{text[:4]}****{text[-2:]}'

    def _rate_limit(self):
        now = time.monotonic()
        ip = request.httprequest.remote_addr or 'unknown'
        with _RATE_LOCK:
            for key, hits in list(_RATE_HITS.items()):
                retained = [stamp for stamp in hits if now - stamp < _RATE_WINDOW]
                if retained:
                    _RATE_HITS[key] = retained
                else:
                    _RATE_HITS.pop(key, None)
            if len(_RATE_HITS) > 2048 and ip not in _RATE_HITS:
                _RATE_HITS.pop(next(iter(_RATE_HITS)))
            hits = _RATE_HITS.setdefault(ip, [])
            if len(hits) >= _RATE_LIMIT:
                raise TooManyRequests('Batas permintaan publik tercapai. Coba lagi nanti.')
            hits.append(now)

    def _pager(self, base, page, total, args=None, page_size=_PAGE_SIZE):
        page_count = max(1, math.ceil(total / page_size))
        page = min(max(page, 1), page_count)
        preserved = dict(args or {})
        preserved.pop('page', None)

        def link(target):
            query = {**preserved, 'page': target}
            return f'{base}?{url_encode(query)}'
        return {'page': page, 'page_count': page_count, 'total': total, 'previous': link(page - 1) if page > 1 else False, 'next': link(page + 1) if page < page_count else False}

    def _safe_faculty(self, record):
        values = record.sudo().read(['name', 'kode'])[0]
        return {'id': record.id, 'name': values['name'], 'kode': values['kode']}

    def _safe_student(self, record):
        values = record.sudo().read(['name', 'nim', 'prodi_id', 'angkatan', 'status_akademik'])[0]
        prodi = values['prodi_id']
        return {'id': record.id, 'name': values['name'], 'identifier': self._mask_identifier(values['nim']), 'prodi': prodi[1] if prodi else '', 'angkatan': values['angkatan'] or '', 'status': dict(record._fields['status_akademik'].selection).get(values['status_akademik'], 'Aktif')}

    def _public_person_domain(self):
        return [('active', '=', True), ('is_public_visible', '=', True), ('public_opt_out', '=', False)]
