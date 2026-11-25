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
from .list_helpers import PAGE_SIZES, TritonListHelpers


class TritonPublicHelpers(TritonListHelpers):

    def _read_domain_page(self, model_name, domain, page, serializer, order='name asc'):
        model = request.env[model_name].sudo()
        args = request.httprequest.args
        page_size = self._page_size(args.get("limit"))
        total = model.search_count(domain)
        page = min(max(1, page), max(1, math.ceil(total / page_size)))
        records = model.search(
            domain,
            order=order,
            limit=page_size,
            offset=(page - 1) * page_size,
        )
        return ([serializer(record) for record in records], total)

    def _safe_prodi(self, record):
        values = record.sudo().read(['name', 'kode', 'fakultas_id'])[0]
        faculty = values['fakultas_id']
        return {'id': record.id, 'name': values['name'], 'kode': values['kode'], 'fakultas': faculty[1] if faculty else ''}

    def _public_stats(self, comparison=None):
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
        summary = comparison['summary'] if comparison else {}
        return {'faculties': Faculty.search_count([('active', '=', True)]), 'prodis': Prodi.search_count([('active', '=', True)]), 'dosen': Dosen.search_count([('active', '=', True)]), 'mahasiswa_aktif': Student.search_count(students_domain), 'courses': Course.search_count([]), 'cpl_count': Cpl.search_count([]), 'cpmk_count': Cpmk.search_count([]), 'rps_final': Rps.search_count([('status', '=', 'final')]), 'institutional_average': self._institutional_average(comparison), 'cpl_valid_count': summary.get('cpl_valid_count', 0), 'cpl_met_count': summary.get('cpl_met_count', 0), 'cpl_not_met_count': summary.get('cpl_not_met_count', 0)}

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

    def _institutional_average(self, comparison=None):
        if comparison is None:
            comparison = self._comparison_data(default_latest=True)
        overall_average = comparison['summary']['overall_average']
        return round(overall_average, 1) if overall_average is not None else False

    def _comparison_data(self, year_start=None, year_end=None, semester=None, faculty_id=None, prodi_ids=None, jenis_cpl=None, default_latest=False):
        env = request.env
        Year = env['erpobe.akademik.tahunajaran'].sudo()
        Prodi = env['erpobe.master.prodi'].sudo()
        Offer = env['erpobe.akademik.penawaran'].sudo()
        OfferLine = env['erpobe.akademik.penawaran.line'].sudo()
        Rps = env['erpobe.akademik.rps'].sudo()
        KrsLine = env['erpobe.akademik.krs.line'].sudo()
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
        institutional_cpl_scores = []
        offer_lines = OfferLine.search([('penawaran_id', 'in', offers.ids), ('prodi_id', 'in', candidates.ids)]) if offers and candidates else OfferLine
        eligible_lines = []
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
            eligible_lines.append(line)

        krs_lines = KrsLine.search([
            ('penawaran_line_id', 'in', [line.id for line in eligible_lines]),
            ('krs_id.state', '=', 'approved'),
        ]) if eligible_lines else KrsLine
        krs_lines_by_offer = {}
        for krs_line in krs_lines:
            krs_lines_by_offer.setdefault(krs_line.penawaran_line_id.id, []).append(krs_line)
        student_ids = krs_lines.mapped('mahasiswa_id').ids
        cpl_grades = env['erpobe.grade.cpl'].sudo().search([
            ('mahasiswa_id', 'in', student_ids),
            ('is_available', '=', True),
        ]) if student_ids else env['erpobe.grade.cpl']
        cpl_grades_by_student = {}
        for grade in cpl_grades:
            cpl_grades_by_student.setdefault(grade.mahasiswa_id.id, []).append(grade)
        cpls = cpl_grades.mapped('cpl_id')
        cpl_types = {row['id']: row['jenis_cpl'] for row in cpls.read(['jenis_cpl'])}

        seen_attempts = set()
        cpl_valid_count = 0
        cpl_met_count = 0
        cpl_not_met_count = 0
        for line in eligible_lines:
            line_krs = krs_lines_by_offer.get(line.id, [])
            if not line_krs:
                continue
            prodi_id = line.prodi_id.id
            year_name = line.tahun_ajaran_id.tahun_ajaran
            year_accumulators.setdefault(year_name, {})
            for krs_line in line_krs:
                student_cpl_grades = cpl_grades_by_student.get(krs_line.mahasiswa_id.id, [])
                for grade in student_cpl_grades:
                    if grade.cpl_id.prodi_id.id != prodi_id:
                        continue
                    if grade.is_available is not True:
                        continue
                    attempt_key = (year_name, prodi_id, krs_line.mahasiswa_id.id, grade.cpl_id.id)
                    if attempt_key in seen_attempts:
                        continue
                    seen_attempts.add(attempt_key)
                    cpl_id = grade.cpl_id.id
                    score = grade.nilai_cpl
                    institutional_cpl_scores.append(score)
                    cpl_valid_count += 1
                    if grade.status_capaian == 'tercapai':
                        cpl_met_count += 1
                    else:
                        cpl_not_met_count += 1
                    kind = cpl_types.get(cpl_id) or 'lainnya'
                    if jenis_cpl and kind != jenis_cpl:
                        continue
                    accumulators[prodi_id][kind].append(score)
                    year_accumulators[year_name].setdefault((prodi_id, kind), []).append(score)
        prodi_results = []
        all_category_scores = []
        highest_category = None
        lowest_category = None
        for prodi in candidates:
            scores = []
            for kind in _CPL_TYPES:
                values = accumulators[prodi.id][kind]
                scores.append(round(sum(values) / len(values), 2) if values else None)
            prodi_results.append({'id': prodi.id, 'name': prodi.name, 'kode': prodi.kode, 'scores': scores, 'warning': warnings[prodi.id]})
        categories = [{'key': key, 'name': value} for key, value in _CPL_TYPES.items() if not jenis_cpl or key == jenis_cpl]
        selected_indexes = [index for index, key in enumerate(_CPL_TYPES) if not jenis_cpl or key == jenis_cpl]
        category_totals = {}
        for result in prodi_results:
            for index, category in enumerate(categories):
                score = result['scores'][selected_indexes[index]]
                if score is not None:
                    all_category_scores.append(score)
                    category_totals.setdefault(category['key'], []).append(score)
        for result in prodi_results:
            result['scores'] = [result['scores'][index] for index in selected_indexes]
            n = len(result['scores'])
            points = []
            for index, score in enumerate(result['scores']):
                angle = 2 * math.pi * index / max(n, 1) - math.pi / 2
                radius = (score or 0) * 0.78
                points.append(f'{100 + math.cos(angle) * radius:.2f},{100 + math.sin(angle) * radius:.2f}')
            result['radar_points'] = ' '.join(points)
        available_category_names = {
            item['key']: item['name'] for item in categories
        }
        category_averages = {
            kind: round(sum(values) / len(values), 2)
            for kind, values in category_totals.items()
            if values
        }
        if category_averages:
            highest_category = available_category_names.get(
                max(category_averages, key=category_averages.get)
            )
            lowest_category = available_category_names.get(
                min(category_averages, key=category_averages.get)
            )
        target_values = cpl_grades.mapped('target_nilai')
        target = round(sum(target_values) / len(target_values), 2) if target_values else None
        overall_average = (
            round(sum(institutional_cpl_scores) / len(institutional_cpl_scores), 2)
            if institutional_cpl_scores
            else None
        )
        summary = {
            'program_count': len(prodi_results),
            'category_count': len(categories),
            'overall_average': overall_average,
            'highest_category': highest_category,
            'attention_category': lowest_category,
            'cpl_valid_count': cpl_valid_count,
            'cpl_met_count': cpl_met_count,
            'cpl_not_met_count': cpl_not_met_count,
        }
        trend = []
        for year in sorted(year_accumulators):
            year_values = [score for (prodi_id, kind), values in year_accumulators[year].items() if prodi_id in candidates.ids and (not jenis_cpl or kind == jenis_cpl) for score in values]
            if year_values:
                trend.append({'year': year, 'average': round(sum(year_values) / len(year_values), 2)})
        return {
            'prodis': prodi_results,
            'categories': categories,
            'summary': summary,
            'warnings': [result['name'] for result in prodi_results if result['warning']],
            'years': available_years,
            'year_start': year_start or '',
            'year_end': year_end or '',
            'semester': semester or '',
            'faculty_id': int(faculty_id) if str(faculty_id or '').isdigit() else 0,
            'prodi_ids': candidates.ids,
            'jenis_cpl': jenis_cpl or '',
            'trend': trend,
            'target': target,
            'methodology': (
                'Nilai CPMK dihitung dari komponen yang dinilai dan alokasi bobotnya pada RPS final. '
                'Nilai CPL menggunakan CPMK yang terpetakan ke CPL dan berbobot sesuai bobot CPMK→mata kuliah '
                'pada RPS yang sama; setiap mahasiswa dihitung satu kali per CPL dalam periode yang dipilih.'
            ),
        }

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
        page_size = self._page_size(page_size)
        page_count = max(1, math.ceil(total / page_size))
        page = min(max(page, 1), page_count)
        preserved = dict(args or {})
        preserved.pop('page', None)

        def link(target):
            query = {**preserved, 'page': target}
            return f'{base}?{url_encode(query)}'
        return {'page': page, 'page_count': page_count, 'page_size': page_size, 'page_sizes': PAGE_SIZES, 'total': total, 'start': (page - 1) * page_size + 1 if total else 0, 'end': min(page * page_size, total), 'previous': link(page - 1) if page > 1 else False, 'next': link(page + 1) if page < page_count else False}

    def _page_size(self, value):
        try:
            page_size = int(value)
        except (TypeError, ValueError):
            return PAGE_SIZES[0]
        return page_size if page_size in PAGE_SIZES else PAGE_SIZES[0]

    def _safe_faculty(self, record):
        values = record.sudo().read(['name', 'kode'])[0]
        return {'id': record.id, 'name': values['name'], 'kode': values['kode']}

    def _safe_student(self, record):
        values = record.sudo().read(['name', 'nim', 'prodi_id', 'angkatan', 'status_akademik'])[0]
        prodi = values['prodi_id']
        return {'id': record.id, 'name': values['name'], 'identifier': self._mask_identifier(values['nim']), 'prodi': prodi[1] if prodi else '', 'angkatan': values['angkatan'] or '', 'status': dict(record._fields['status_akademik'].selection).get(values['status_akademik'], 'Aktif')}

    def _public_person_domain(self):
        return [('active', '=', True), ('is_public_visible', '=', True), ('public_opt_out', '=', False)]
