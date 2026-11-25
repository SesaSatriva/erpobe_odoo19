from urllib.parse import quote
import io
import xlsxwriter

from odoo import http
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.http import request

from .portal_base import TritonPortalBase
from .const import _CPL_TYPES


class TritonPortalMahasiswa(TritonPortalBase):

    @http.route(['/my/krs', '/my/krs/<int:krs_id>'], type='http', auth='user', website=True, methods=['GET', 'POST'])
    def triton_student_krs(self, krs_id=None, **kwargs):
        student = self._require_student()
        Krs = request.env['erpobe.akademik.krs'].sudo()
        error = ''
        if request.httprequest.method == 'POST':
            offer_id = request.httprequest.form.get('penawaran_id')
            selected_ids = request.httprequest.form.getlist('penawaran_line_ids')
            offer = request.env['erpobe.akademik.penawaran'].sudo().browse(int(offer_id) if offer_id and offer_id.isdigit() else 0)
            if not offer.exists() or not offer.tahun_ajaran.aktif or student.rombel_id not in offer.rombel_ids or (offer.prodi_id != student.prodi_id):
                error = 'Penawaran tidak aktif atau tidak tersedia untuk rombel Anda.'
            else:
                krs = Krs.search([('mahasiswa_id', '=', student.id), ('penawaran_id', '=', offer.id)], limit=1)
                if krs and krs.state not in ('draft', 'rejected'):
                    error = 'KRS yang sudah diajukan tidak dapat diubah.'
                else:
                    valid_ids = []
                    for selected_id in selected_ids:
                        if selected_id.isdigit():
                            selected_line = request.env['erpobe.akademik.penawaran.line'].sudo().browse(int(selected_id))
                            if selected_line.exists() and selected_line.penawaran_id == offer and (student.rombel_id in selected_line.rombel_ids) and (selected_line.prodi_id == student.prodi_id):
                                valid_ids.append(selected_line.id)
                    try:
                        with request.env.cr.savepoint():
                            if not krs:
                                krs = Krs.create({'mahasiswa_id': student.id, 'penawaran_id': offer.id})
                            krs.line_ids.unlink()
                            for line_id in valid_ids:
                                request.env['erpobe.akademik.krs.line'].sudo().create({'krs_id': krs.id, 'penawaran_line_id': line_id, 'status_pengambilan': 'baru'})
                    except (ValidationError, UserError) as exc:
                        error = str(exc)
        krs = Krs.search([('id', '=', krs_id), ('mahasiswa_id', '=', student.id)], limit=1) if krs_id else Krs.search([('mahasiswa_id', '=', student.id)], order='tahun_ajaran desc', limit=1)
        if krs_id and not krs:
            raise AccessError('KRS tidak ditemukan.')
        active_offers = request.env['erpobe.akademik.penawaran'].sudo().search([('tahun_ajaran.aktif', '=', True), ('prodi_id', '=', student.prodi_id.id), ('rombel_ids', 'in', student.rombel_id.id)], order='name asc')
        offer_data = []
        for offer in active_offers:
            offer_data.append({'id': offer.id, 'name': offer.name, 'lines': [{'id': line.id, 'name': line.matakuliah_id.name, 'kode': line.matakuliah_id.kode_mk, 'sks': line.matakuliah_id.sks, 'selected': bool(krs and line in krs.line_ids.mapped('penawaran_line_id'))} for line in offer.line_ids.filtered(lambda item: student.rombel_id in item.rombel_ids)]})
        return request.render('erpobe.triton_krs_page', {'student': student, 'krs': krs, 'offers': offer_data, 'error': error, 'message': request.httprequest.args.get('error', '')})

    @http.route('/my/krs/<int:krs_id>/submit', type='http', auth='user', website=True, methods=['POST'])
    def triton_submit_krs(self, krs_id, **kwargs):
        student = self._require_student()
        krs = request.env['erpobe.akademik.krs'].sudo().with_context(
            audit_source='portal',
            audit_actor_id=request.env.user.id,
            audit_ip=request.httprequest.remote_addr,
            audit_user_agent=request.httprequest.headers.get('User-Agent'),
        ).search([('id', '=', krs_id), ('mahasiswa_id', '=', student.id)], limit=1)
        if not krs:
            raise AccessError('KRS tidak ditemukan.')
        try:
            krs.action_submit()
        except ValidationError as exc:
            return request.redirect(f'/my/krs?error={quote(str(exc))}')
        return request.redirect('/my/krs')

    @http.route('/my/khs', type='http', auth='user', website=True)
    def triton_student_khs(self, **kwargs):
        student = self._require_student()
        request.env['erpobe.audit.log'].with_context(
            audit_source='portal',
            audit_actor_id=request.env.user.id,
            audit_ip=request.httprequest.remote_addr,
            audit_user_agent=request.httprequest.headers.get('User-Agent'),
        ).log_event(
            'SENSITIVE_ACCESS',
            model_name='erpobe.report.khs',
            description='Mahasiswa mengakses KHS',
            is_sensitive=True,
        )
        reports = request.env['erpobe.report.khs'].sudo().search([('mahasiswa_id', '=', student.id)], order='tahun_ajaran_id desc')
        course_lines, pagination = self._list_page(
            request.env['erpobe.report.khs.mk'].sudo(),
            [('khs_id', 'in', reports.ids)],
            '/my/khs',
            {'course': ('mk_name asc, id asc', 'Mata kuliah A–Z'), 'score': ('nilai_angka desc, mk_name asc', 'Nilai tertinggi')},
            'mk_id asc, id asc',
            ('mk_name', 'kode_mk'),
        )
        data = []
        for report in reports:
            selected_lines = course_lines.filtered(lambda line: line.khs_id == report)
            data.append({'year': report.tahun_ajaran_id.display_name if report.tahun_ajaran_id else 'Transkrip', 'id': report.id, 'ipk': report.ipk, 'sks': report.total_sks_lulus, 'courses': [{'name': line.mk_id.name, 'kode': line.kode_mk, 'sks': line.sks, 'score': line.nilai_angka, 'grade': line.nilai_huruf} for line in selected_lines]})
        return request.render('erpobe.triton_khs_page', {'reports': data, 'pagination': pagination, 'list_action': '/my/khs'})

    @http.route('/my/khs/<int:khs_id>/xlsx', type='http', auth='user', website=True)
    def triton_student_khs_xlsx(self, khs_id, **kwargs):
        student = self._require_student()
        report = request.env['erpobe.report.khs'].sudo().search([
            ('id', '=', khs_id),
            ('mahasiswa_id', '=', student.id),
        ], limit=1)
        if not report:
            raise AccessError('KHS tidak ditemukan untuk akun ini.')

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('KHS')
        title = workbook.add_format({'bold': True, 'font_size': 16})
        header = workbook.add_format({'bold': True, 'bg_color': '#123F59', 'font_color': 'white', 'border': 1})
        sheet.write('A1', 'Kartu Hasil Studi', title)
        sheet.write_row('A3', ['NIM', 'Nama', 'Program Studi', 'Tahun Akademik', 'IPK', 'SKS Lulus'], header)
        sheet.write_row('A4', [
            report.nim,
            report.mahasiswa_id.name,
            report.prodi_id.name,
            report.tahun_ajaran_id.tahun_ajaran if report.tahun_ajaran_id else '',
            report.ipk,
            report.total_sks_lulus,
        ])
        sheet.write_row('A6', ['Semester', 'Kode', 'Mata Kuliah', 'SKS', 'Nilai Angka', 'Nilai Huruf', 'Bobot'], header)
        row = 6
        for course in report.mk_line_ids:
            sheet.write_row(row, 0, [
                course.semester_mk,
                course.kode_mk,
                course.mk_id.name,
                course.sks,
                course.nilai_angka,
                course.nilai_huruf,
                course.bobot,
            ])
            row += 1
        sheet.set_column('A:A', 12)
        sheet.set_column('B:B', 14)
        sheet.set_column('C:C', 48)
        sheet.set_column('D:D', 8)
        sheet.set_column('E:G', 14)
        workbook.close()
        response = request.make_response(
            output.getvalue(),
            headers=[
                ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                ('Content-Disposition', f'attachment; filename=KHS-{student.nim}.xlsx'),
            ],
        )
        return response

    @http.route('/my/mata-kuliah', type='http', auth='user', website=True)
    def triton_student_courses(self, **kwargs):
        student = self._require_student()
        krs_lines, pagination = self._list_page(
            request.env['erpobe.akademik.krs.line'].sudo(),
            [('mahasiswa_id', '=', student.id), ('krs_id.state', '=', 'approved')],
            '/my/mata-kuliah',
            {'course': ('matakuliah_name asc, id asc', 'Mata kuliah A–Z'), 'term': ('krs_id desc, matakuliah_name asc, id asc', 'Tahun ajaran terbaru')},
            'krs_id desc, matakuliah_id asc, id asc',
            ('matakuliah_name', 'matakuliah_kode'),
        )
        courses = []
        for line in krs_lines:
            final_rps = line.penawaran_line_id.rps_ids.filtered(lambda record: record.status == 'final').sorted(key=lambda record: (record.version, record.id), reverse=True)[:1]
            component_grades = request.env['erpobe.grade.komponen'].sudo().search([('krs_line_id', '=', line.id)])
            cpmk_grades = request.env['erpobe.grade.cpmk'].sudo().search([
                ('mahasiswa_id', '=', student.id),
                ('krs_line_id', '=', line.id),
                ('rps_id', '=', final_rps.id),
            ]) if final_rps else request.env['erpobe.grade.cpmk'].sudo()
            cpmk_grade_map = {grade.cpmk_id.id: grade for grade in cpmk_grades}
            courses.append({
                'line_id': line.id,
                'name': line.matakuliah_id.name,
                'code': line.matakuliah_id.kode_mk,
                'sks': line.sks,
                'year': line.penawaran_line_id.tahun_ajaran_id.tahun_ajaran,
                'semester': line.penawaran_line_id.tahun_ajaran_id.semester,
                'rps': bool(final_rps),
                'rps_id': final_rps.id if final_rps else 0,
                'components': [
                    {
                        'name': grade.komponen_id.name,
                        'score': grade.nilai,
                        'origin': grade.origin,
                        'cpmks': [
                            {
                                'code': allocation.cpmk_id.kode_cpmk,
                                'weight': allocation.bobot_komponen_cpmk,
                            }
                            for allocation in final_rps.bobot_komponen_cpmk_ids.filtered(
                                lambda item:
                                    item.rps_komponen_id
                                    and item.komponen_penilaian == grade.komponen_id
                                    and item.cpmk_id
                            )
                        ] if final_rps else [],
                    }
                    for grade in component_grades.filtered(lambda item: item.is_graded)
                ],
                'cpmk': [{
                    'code': cpmk.kode_cpmk,
                    'name': cpmk.name,
                    'score': cpmk_grade_map[cpmk.id].nilai_cpmk if cpmk.id in cpmk_grade_map else 0.0,
                    'available': cpmk.id in cpmk_grade_map and cpmk_grade_map[cpmk.id].is_available,
                    'target': cpmk.target_nilai,
                    'cpl': [mapping.cpl_id.kode_cpl for mapping in cpmk.cpl_mapping_ids],
                } for cpmk in (final_rps.cpmk_ids if final_rps else [])],
            })
        return request.render('erpobe.triton_student_courses_page', {'courses': courses, 'pagination': pagination, 'list_action': '/my/mata-kuliah'})

    @http.route('/my/mata-kuliah/<int:krs_line_id>', type='http', auth='user', website=True)
    def triton_student_course_detail(self, krs_line_id, **kwargs):
        student = self._require_student()
        line = request.env['erpobe.akademik.krs.line'].sudo().search([
            ('id', '=', krs_line_id),
            ('mahasiswa_id', '=', student.id),
            ('krs_id.state', '=', 'approved'),
        ], limit=1)
        if not line:
            raise AccessError('Mata kuliah tidak ditemukan atau bukan milik akun Anda.')

        rps = line.penawaran_line_id.rps_ids.filtered(
            lambda record: record.status == 'final'
        ).sorted(key=lambda record: (record.version, record.id), reverse=True)[:1]
        cpmk_rows = request.env['erpobe.grade.cpmk'].sudo().search([
            ('mahasiswa_id', '=', student.id),
            ('krs_line_id', '=', line.id),
            ('rps_id', '=', rps.id),
        ]) if rps else request.env['erpobe.grade.cpmk'].sudo()
        cpmk_data = []
        valid_scores = []
        for cpmk in (rps.cpmk_ids if rps else request.env['erpobe.akademik.cpmk']):
            grade = cpmk_rows.filtered(lambda item: item.cpmk_id == cpmk)[:1]
            available = bool(grade and grade.is_available)
            if available:
                valid_scores.append(grade.nilai_cpmk)
            cpmk_data.append({
                'id': cpmk.id,
                'code': cpmk.kode_cpmk,
                'name': cpmk.name,
                'target': cpmk.target_nilai,
                'score': grade.nilai_cpmk if grade else 0.0,
                'available': available,
                'met': bool(grade and grade.status_capaian == 'tercapai'),
            })
        return request.render('erpobe.triton_student_course_detail_page', {
            'line': line,
            'rps': rps,
            'cpmks': cpmk_data,
            'valid_count': len(valid_scores),
            'valid_average': round(sum(valid_scores) / len(valid_scores), 2) if valid_scores else None,
        })

    @http.route('/my/mata-kuliah/<int:krs_line_id>/cpmk/<int:cpmk_id>', type='http', auth='user', website=True)
    def triton_student_cpmk_detail(self, krs_line_id, cpmk_id, **kwargs):
        student = self._require_student()
        line = request.env['erpobe.akademik.krs.line'].sudo().search([
            ('id', '=', krs_line_id),
            ('mahasiswa_id', '=', student.id),
            ('krs_id.state', '=', 'approved'),
        ], limit=1)
        if not line:
            raise AccessError('Mata kuliah tidak ditemukan atau bukan milik akun Anda.')
        rps = line.penawaran_line_id.rps_ids.filtered(
            lambda record: record.status == 'final'
        ).sorted(key=lambda record: (record.version, record.id), reverse=True)[:1]
        cpmk = request.env['erpobe.akademik.cpmk'].sudo().browse(cpmk_id)
        if not rps or not cpmk.exists() or cpmk not in rps.cpmk_ids:
            raise AccessError('CPMK tidak tersedia untuk mata kuliah ini.')

        grade = request.env['erpobe.grade.cpmk'].sudo().search([
            ('mahasiswa_id', '=', student.id),
            ('krs_line_id', '=', line.id),
            ('rps_id', '=', rps.id),
            ('cpmk_id', '=', cpmk.id),
        ], limit=1)
        allocations = rps.bobot_komponen_cpmk_ids.filtered(
            lambda item: item.cpmk_id == cpmk
        )
        component_rows = []
        for allocation in allocations:
            snapshot = allocation.rps_komponen_id
            if not snapshot and allocation.komponen_penilaian:
                snapshot = rps.rps_komponen_ids.filtered(
                    lambda item: item.komponen_id == allocation.komponen_penilaian
                )[:1]
            grade_row = request.env['erpobe.grade.komponen'].sudo().search([
                ('krs_line_id', '=', line.id),
                ('rps_id', '=', rps.id),
                ('rps_komponen_id', '=', snapshot.id),
            ], limit=1) if snapshot else request.env['erpobe.grade.komponen'].sudo()
            graded = bool(grade_row and grade_row.is_graded)
            component_rows.append({
                'name': snapshot.name if snapshot else allocation.komponen_penilaian.name,
                'weight': allocation.bobot_komponen_cpmk,
                'snapshot_weight': snapshot.bobot if snapshot else 0.0,
                'score': grade_row.nilai if grade_row else None,
                'graded': graded,
                'origin': grade_row.origin if grade_row else '',
            })
        return request.render('erpobe.triton_student_cpmk_detail_page', {
            'line': line,
            'rps': rps,
            'cpmk': cpmk,
            'grade': grade,
            'components': component_rows,
        })

    @http.route('/my/rps/<int:rps_id>', type='http', auth='user', website=True)
    def triton_student_rps_detail(self, rps_id, **kwargs):
        student = self._require_student()
        rps = request.env['erpobe.akademik.rps'].sudo().browse(rps_id)
        if not rps.exists() or rps.status != 'final':
            raise UserError('RPS tidak ditemukan atau belum final.')
        authorized = request.env['erpobe.akademik.krs.line'].sudo().search_count([
            ('mahasiswa_id', '=', student.id),
            ('krs_id.state', '=', 'approved'),
            ('matakuliah_id', '=', rps.matakuliah_id.id),
            ('penawaran_line_id', '=', rps.penawaran_line_id.id),
        ])
        if not authorized:
            raise AccessError('RPS ini tidak relevan dengan mata kuliah yang Anda ambil.')
        request.env['erpobe.audit.log'].with_context(
            audit_source='portal',
            audit_actor_id=request.env.user.id,
            audit_ip=request.httprequest.remote_addr,
            audit_user_agent=request.httprequest.headers.get('User-Agent'),
        ).log_event(
            'SENSITIVE_ACCESS',
            model_name='erpobe.akademik.rps',
            record=rps,
            description='Mahasiswa mengakses RPS',
            is_sensitive=True,
        )
        return request.render('erpobe.triton_student_rps_detail_page', {'rps': rps})

    @http.route('/my/capaian-cpl', type='http', auth='user', website=True)
    def triton_student_cpl(self, **kwargs):
        student = self._require_student()
        args = request.httprequest.args
        jenis = args.get('jenis', '')
        status = args.get('status', '')
        filter_options = [
            (
                'jenis',
                'Jenis CPL',
                [('', 'Semua jenis')] + [
                    (key, label) for key, label in _CPL_TYPES.items()
                ],
            ),
            (
                'status',
                'Status',
                [
                    ('', 'Semua status'),
                    ('tercapai', 'Tercapai'),
                    ('belum', 'Belum tercapai'),
                    ('dalam_proses', 'Dalam proses'),
                    ('belum_tersedia', 'Belum tersedia'),
                ],
            ),
        ]
        domain = [('mahasiswa_id', '=', student.id)]
        if jenis in _CPL_TYPES:
            domain.append(('cpl_id.jenis_cpl', '=', jenis))
        else:
            jenis = ''
        valid_statuses = {
            'tercapai', 'belum', 'dalam_proses', 'belum_tersedia',
        }
        if status in valid_statuses:
            domain.append(('status_capaian', '=', status))
        else:
            status = ''
        grades, pagination = self._list_page(
            request.env['erpobe.grade.cpl'].sudo(),
            domain,
            '/my/capaian-cpl',
            {
                'cpl': ('cpl_kode asc, id asc', 'Kode CPL A–Z'),
                'score': ('nilai_cpl desc, cpl_kode asc', 'Nilai tertinggi'),
                'status': ('status_capaian asc, cpl_kode asc', 'Status'),
            },
            'cpl_id asc, id asc',
            ('cpl_name', 'cpl_kode'),
            filter_options,
        )
        filter_names = {option[0] for option in filter_options}
        pagination['filters'] = [
            item for item in pagination['filters']
            if item['name'] not in filter_names
        ]
        values = []
        for grade in grades:
            status_labels = {
                'tercapai': 'Tercapai',
                'belum': 'Belum tercapai',
                'dalam_proses': 'Dalam proses',
                'belum_tersedia': 'Belum tersedia',
            }
            values.append({
                'id': grade.cpl_id.id,
                'name': grade.cpl_id.kode_cpl,
                'description': grade.cpl_id.name,
                'jenis': _CPL_TYPES.get(grade.cpl_id.jenis_cpl, 'Lainnya'),
                'score': grade.nilai_cpl,
                'target': grade.target_nilai,
                'available': grade.is_available,
                'status': grade.status_capaian,
                'status_label': status_labels.get(
                    grade.status_capaian, 'Belum tersedia'
                ),
                'met': grade.status_capaian == 'tercapai',
            })
        return request.render('erpobe.triton_student_cpl_page', {
            'grades': values,
            'pagination': pagination,
            'list_action': '/my/capaian-cpl',
        })

    @http.route('/my/capaian-cpl/<int:cpl_id>', type='http', auth='user', website=True)
    def triton_student_cpl_detail(self, cpl_id, **kwargs):
        student = self._require_student()
        grade = request.env['erpobe.grade.cpl'].sudo().search([
            ('cpl_id', '=', cpl_id),
            ('mahasiswa_id', '=', student.id),
        ], limit=1)
        if not grade:
            raise AccessError('CPL tidak ditemukan atau bukan milik akun Anda.')

        cpl = grade.cpl_id
        status_labels = {
            'tercapai': 'Tercapai',
            'belum': 'Belum tercapai',
            'dalam_proses': 'Dalam proses',
            'belum_tersedia': 'Belum tersedia',
        }
        mappings = request.env['erpobe.akademik.cpl.mk.cpmk'].sudo().search(
            [('cpl_id', '=', cpl.id)],
            order='cpmk_id',
        )
        cpmks = mappings.mapped('cpmk_id')
        mapped_course_ids = set(cpl.mk_mapping_ids.mapped('mk_id').ids)
        cpmk_ids = cpmks.ids
        cpmk_grades = request.env['erpobe.grade.cpmk'].sudo().search([
            ('mahasiswa_id', '=', student.id),
            ('cpmk_id', 'in', cpmk_ids),
            ('is_available', '=', True),
            ('rps_id.status', '=', 'final'),
            ('krs_line_id.krs_id.state', '=', 'approved'),
        ]) if cpmk_ids else request.env['erpobe.grade.cpmk']
        best_grade_by_cpmk = {}
        for cpmk_grade in cpmk_grades:
            current = best_grade_by_cpmk.get(cpmk_grade.cpmk_id.id)
            grade_rank = (
                cpmk_grade.rps_id.id or 0,
                cpmk_grade.krs_line_id.id or 0,
                cpmk_grade.id,
            )
            current_rank = (
                current.rps_id.id or 0,
                current.krs_line_id.id or 0,
                current.id,
            ) if current else None
            if (
                not current
                or cpmk_grade.nilai_cpmk > current.nilai_cpmk
                or (
                    cpmk_grade.nilai_cpmk == current.nilai_cpmk
                    and grade_rank > current_rank
                )
            ):
                best_grade_by_cpmk[cpmk_grade.cpmk_id.id] = cpmk_grade

        selected_rps_ids = list({
            cpmk_grade.rps_id.id
            for cpmk_grade in best_grade_by_cpmk.values()
        })
        weight_lines = request.env['erpobe.bobot.cpmk.mk'].sudo().search(
            [
                ('rps_id', 'in', selected_rps_ids),
                ('cpmk_id', 'in', cpmk_ids),
            ],
            order='id asc',
        ) if selected_rps_ids else request.env['erpobe.bobot.cpmk.mk']
        weight_by_rps_cpmk = {}
        for weight_line in weight_lines:
            weight_by_rps_cpmk.setdefault(
                (weight_line.rps_id.id, weight_line.cpmk_id.id),
                weight_line.bobot_cpmk_mk,
            )

        contributions = []
        valid_cpmk_count = 0
        incomplete_cpmk_count = 0
        used_cpmk_count = 0
        calculation_total_weight = 0.0
        calculation_weighted_total = 0.0
        course_rows = {}
        for course in cpl.mk_mapping_ids.mapped('mk_id'):
            course_rows[course.id] = {
                'id': course.id,
                'code': course.kode_mk,
                'name': course.name,
                'cpmks': [],
            }
        for cpmk in cpmks:
            cpmk_grade = best_grade_by_cpmk.get(cpmk.id)
            if cpmk_grade:
                valid_cpmk_count += 1
            else:
                incomplete_cpmk_count += 1
            weight = 0.0
            if cpmk_grade:
                weight = weight_by_rps_cpmk.get(
                    (cpmk_grade.rps_id.id, cpmk.id), 0.0
                )
            included_in_mapping = (
                cpmk.prodi_id == cpl.prodi_id
                and (
                    not mapped_course_ids
                    or cpmk.mk_id.id in mapped_course_ids
                )
            )
            used = bool(cpmk_grade and weight > 0 and included_in_mapping)
            if used:
                used_cpmk_count += 1
                calculation_total_weight += weight
                calculation_weighted_total += cpmk_grade.nilai_cpmk * weight
            if not included_in_mapping:
                calculation_status = 'Di luar pemetaan mata kuliah CPL'
            elif not cpmk_grade:
                calculation_status = 'Nilai belum tersedia'
            elif weight <= 0:
                calculation_status = 'Bobot tidak berkontribusi'
            else:
                calculation_status = 'Digunakan dalam perhitungan'
            contributions.append({
                'id': cpmk.id,
                'code': cpmk.kode_cpmk,
                'name': cpmk.name,
                'target': cpmk.target_nilai,
                'score': cpmk_grade.nilai_cpmk if cpmk_grade else 0.0,
                'available': bool(cpmk_grade),
                'weight': weight,
                'used': used,
                'status': calculation_status,
                'weighted_score': (
                    cpmk_grade.nilai_cpmk * weight if used else False
                ),
                'course_code': cpmk.mk_id.kode_mk,
                'course': cpmk.mk_id.name,
            })
            course_row = course_rows.setdefault(cpmk.mk_id.id, {
                'id': cpmk.mk_id.id,
                'code': cpmk.mk_id.kode_mk,
                'name': cpmk.mk_id.name,
                'cpmks': [],
            })
            course_row['cpmks'].append({
                'code': cpmk.kode_cpmk,
                'score': cpmk_grade.nilai_cpmk if cpmk_grade else False,
                'available': bool(cpmk_grade),
            })
        course_rows = sorted(
            course_rows.values(), key=lambda row: (row['code'] or '', row['id'])
        )
        return request.render('erpobe.triton_student_cpl_detail_page', {
            'grade': grade,
            'jenis_label': _CPL_TYPES.get(cpl.jenis_cpl, 'Lainnya'),
            'status_label': status_labels.get(
                grade.status_capaian, 'Belum tersedia'
            ),
            'contributions': contributions,
            'courses': course_rows,
            'course_count': len(course_rows),
            'valid_cpmk_count': valid_cpmk_count,
            'incomplete_cpmk_count': incomplete_cpmk_count,
            'used_cpmk_count': used_cpmk_count,
            'cpmk_count': len(contributions),
            'calculation_total_weight': calculation_total_weight,
            'calculation_weighted_total': calculation_weighted_total,
            'calculated_score': (
                max(
                    0.0,
                    min(
                        100.0,
                        calculation_weighted_total / calculation_total_weight,
                    ),
                )
                if calculation_total_weight else 0.0
            ),
        })

    @http.route('/my/profil', type='http', auth='user', website=True, methods=['GET', 'POST'])
    def triton_student_profile(self, **kwargs):
        student = self._student()
        teacher = self._teacher() if not student else request.env['erpobe.master.dosen']
        if not student and (not teacher):
            raise AccessError('Akun ini tidak terhubung ke profil akademik.')
        message = ''
        error = ''
        if request.httprequest.method == 'POST':
            profile = student or teacher
            form = request.httprequest.form
            allowed_partner_vals = {
                'name': form.get('name', '').strip(),
                'email': form.get('email', '').strip(),
                'phone': form.get('phone', '').strip(),
                'street': form.get('street', '').strip(),
                'city': form.get('city', '').strip(),
            }
            if not allowed_partner_vals['name']:
                error = 'Nama tidak boleh kosong.'
            elif not allowed_partner_vals['email']:
                error = 'Email tidak boleh kosong.'
            else:
                try:
                    with request.env.cr.savepoint():
                        profile.partner_id.sudo().write(allowed_partner_vals)
                        profile.sudo().write({
                            'public_opt_out': form.get('public_opt_out') == '1',
                        })
                        profile.user_id.sudo().with_context(skip_sync_user_type=True).write({
                            'name': allowed_partner_vals['name'],
                            'email': allowed_partner_vals['email'],
                        })
                    message = 'Profil dan preferensi privasi berhasil disimpan.'
                except (ValidationError, UserError) as exc:
                    error = str(exc)
        profile_partner = (student or teacher).partner_id
        return request.render('erpobe.triton_student_profile_page', {
            'student': student,
            'teacher': teacher,
            'profile_partner': profile_partner,
            'message': message,
            'error': error,
        })
