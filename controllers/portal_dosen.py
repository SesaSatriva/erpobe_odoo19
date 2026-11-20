from urllib.parse import quote

from odoo import http
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.http import request

from .portal_base import TritonPortalBase


class TritonPortalDosen(TritonPortalBase):

    @http.route('/my/riwayat-nilai', type='http', auth='user', website=True)
    def triton_grade_history(self, **kwargs):
        teacher = self._require_teacher()
        line_ids = self._teacher_lines(teacher).ids
        Audit = request.env['erpobe.grade.komponen.audit'].sudo()
        records, pagination = self._list_page(
            Audit,
            [('penawaran_line_id', 'in', line_ids)],
            '/my/riwayat-nilai',
            {'student': ('mahasiswa_id.name asc, id desc', 'Mahasiswa A–Z'), 'latest': ('create_date desc, id desc', 'Terbaru')},
            'create_date desc, id desc',
            ('mahasiswa_id.name', 'mahasiswa_id.nim', 'komponen_id.name'),
        )
        data = [{
            'time': record.create_date,
            'user': record.user_id.name,
            'student': record.mahasiswa_id.name,
            'component': record.komponen_id.name,
            'old': record.old_value,
            'new': record.new_value,
            'reason': record.reason or '',
        } for record in records]
        return request.render('erpobe.triton_grade_history_page', {
            'history': data,
            'pagination': pagination,
            'list_action': '/my/riwayat-nilai',
        })

    @http.route('/my/rps', type='http', auth='user', website=True)
    def triton_teacher_rps(self, **kwargs):
        teacher = self._require_teacher()
        line_domain = ['|', ('matakuliah_id.koordinator_id', '=', teacher.id), ('matakuliah_id.tim_pengampu_ids', 'in', teacher.id)]
        status = request.httprequest.args.get('status', '')
        if status in ('missing', 'draft', 'review', 'final'):
            line_domain.append(('rps_status', '=', status))
        lines, pagination = self._list_page(
            request.env['erpobe.akademik.penawaran.line'].sudo(),
            line_domain,
            '/my/rps',
            {'course': ('matakuliah_id.name asc, id asc', 'Mata kuliah A–Z'), 'term': ('tahun_ajaran_id desc, matakuliah_id.name asc, id asc', 'Tahun ajaran terbaru'), 'status': ('rps_status asc, matakuliah_id.name asc', 'Status RPS')},
            'tahun_ajaran_id desc, matakuliah_id asc, id asc',
            ('matakuliah_id.name', 'matakuliah_id.kode_mk'),
            (('status', 'Status RPS', (
                ('', 'Semua status'),
                ('missing', 'Belum ada'),
                ('draft', 'Draft'),
                ('review', 'Perlu ditinjau'),
                ('final', 'Final'),
            )),),
        )
        data = [{'id': line.id, 'course': line.matakuliah_id.name, 'code': line.matakuliah_id.kode_mk, 'year': line.tahun_ajaran_id.tahun_ajaran, 'semester': line.tahun_ajaran_id.semester, 'status': line.latest_rps_id.status if line.latest_rps_id else 'missing', 'weights': line.latest_rps_id.weight_status if line.latest_rps_id else 'missing', 'rps_id': line.latest_rps_id.id if line.latest_rps_id else 0, 'sources': [{'id': source.id, 'name': source.display_name} for source in request.env['erpobe.akademik.rps'].sudo().search([('matakuliah_id', '=', line.matakuliah_id.id), ('prodi_id', '=', line.prodi_id.id), ('status', '=', 'final'), ('penawaran_line_id', '!=', line.id)], order='tahun_ajaran_id desc, version desc')]} for line in lines]
        return request.render('erpobe.triton_teacher_rps_page', {'lines': data, 'message': request.httprequest.args.get('message', ''), 'pagination': pagination, 'list_action': '/my/rps'})

    @http.route('/my/rps/<int:line_id>/create', type='http', auth='user', website=True, methods=['POST'])
    def triton_create_rps(self, line_id, **kwargs):
        _, line = self._authorized_teacher_line(line_id)
        line.action_create_rps()
        return request.redirect(f'/my/rps/{line.id}/edit')

    @http.route('/my/rps/<int:line_id>/edit', type='http', auth='user', website=True, methods=['GET', 'POST'])
    def triton_edit_rps(self, line_id, **kwargs):
        _, line = self._authorized_teacher_line(line_id)
        rps = line.latest_rps_id
        if not rps:
            raise UserError('Buat atau salin RPS sebelum mengeditnya.')
        error = ''
        if request.httprequest.method == 'POST':
            form = request.httprequest.form
            try:
                with request.env.cr.savepoint():
                    selected_components = []
                    for component_id in form.getlist('komponen_ids'):
                        if component_id.isdigit():
                            selected_components.append(int(component_id))
                    components = request.env['erpobe.akademik.komponen'].sudo().browse(selected_components).exists()
                    if len(components) != len(set(selected_components)):
                        raise ValidationError('Komponen penilaian tidak valid.')
                    rps.write({'deskripsi_mk': form.get('deskripsi_mk', ''), 'media_software': form.get('media_software', ''), 'media_hardware': form.get('media_hardware', ''), 'komponen_ids': [(6, 0, components.ids)]})
                    weight_fields = (('bobot_mk_', 'bobot_cpmk_mk_ids', 'bobot_cpmk_mk'), ('bobot_cpl_', 'bobot_cpmk_cpl_ids', 'bobot_cpmk_cpl'), ('bobot_komponen_', 'bobot_komponen_cpmk_ids', 'bobot_komponen_cpmk'))
                    for prefix, relation, field_name in weight_fields:
                        rows = getattr(rps, relation)
                        for row in rows:
                            raw = form.get(f'{prefix}{row.id}')
                            if raw is None:
                                continue
                            value = float(raw)
                            if value < 0 or value > 100:
                                raise ValidationError('Bobot harus berada pada rentang 0–100.')
                            row.write({field_name: value})
                    if form.get('operation') == 'review':
                        rps.action_mark_for_review()
            except (ValidationError, UserError, ValueError) as exc:
                error = str(exc)
        return request.render('erpobe.triton_rps_edit_page', {'line': line, 'rps': rps, 'components': request.env['erpobe.akademik.komponen'].sudo().search([], order='name asc'), 'error': error, 'message': request.httprequest.args.get('message', '')})

    @http.route('/my/rps/<int:rps_id>/finalize', type='http', auth='user', website=True, methods=['POST'])
    def triton_finalize_rps(self, rps_id, **kwargs):
        rps = request.env['erpobe.akademik.rps'].sudo().browse(rps_id)
        if not rps.exists():
            raise UserError('RPS tidak ditemukan.')
        _, line = self._authorized_teacher_line(rps.penawaran_line_id.id)
        if rps.penawaran_line_id != line:
            raise AccessError('RPS ini bukan bagian dari penawaran yang Anda ampu.')
        try:
            rps.action_finalize()
        except UserError as exc:
            return request.redirect(f'/my/rps?message={quote(str(exc))}')
        return request.redirect('/my/rps?message=RPS+berhasil+difinalisasi')

    @http.route('/my/rps/<int:line_id>/copy', type='http', auth='user', website=True, methods=['POST'])
    def triton_copy_rps(self, line_id, **kwargs):
        _, line = self._authorized_teacher_line(line_id)
        source_id = request.httprequest.form.get('source_rps_id')
        source = request.env['erpobe.akademik.rps'].sudo().browse(int(source_id) if source_id and source_id.isdigit() else 0)
        if not source.exists() or source.matakuliah_id != line.matakuliah_id or source.prodi_id != line.prodi_id or (source.status != 'final'):
            raise UserError('Pilih RPS final mata kuliah yang sama untuk disalin.')
        copy_wizard = request.env['erpobe.wizard.rps.copy'].sudo().create({'penawaran_line_id': line.id, 'source_rps_id': source.id})
        copy_wizard.action_copy()
        return request.redirect(f'/my/rps/{line.id}/edit')

    @http.route('/my/kelas', type='http', auth='user', website=True)
    def triton_teacher_classes(self, **kwargs):
        teacher = self._require_teacher()
        lines, pagination = self._list_page(
            request.env['erpobe.akademik.penawaran.line'].sudo(),
            ['|', ('matakuliah_id.koordinator_id', '=', teacher.id), ('matakuliah_id.tim_pengampu_ids', 'in', teacher.id)],
            '/my/kelas',
            {'course': ('matakuliah_id.name asc, id asc', 'Mata kuliah A–Z'), 'term': ('tahun_ajaran_id desc, matakuliah_id.name asc, id asc', 'Tahun ajaran terbaru')},
            'tahun_ajaran_id desc, matakuliah_id asc, id asc',
            ('matakuliah_id.name', 'matakuliah_id.kode_mk'),
        )
        classes = []
        for line in lines:
            classes.append({'course': line.matakuliah_id.name, 'code': line.matakuliah_id.kode_mk, 'year': line.tahun_ajaran_id.tahun_ajaran, 'student_count': len(line.mahasiswa_ids), 'line_id': line.id})
        return request.render('erpobe.triton_teacher_classes_page', {'classes': classes, 'pagination': pagination, 'list_action': '/my/kelas'})

    @http.route('/my/kelas/<int:line_id>/nilai', type='http', auth='user', website=True, methods=['GET', 'POST'])
    def triton_teacher_grades(self, line_id, **kwargs):
        _, line = self._authorized_teacher_line(line_id)
        rps = line.latest_rps_id
        if not rps or rps.status != 'final' or rps.weight_status != 'complete':
            raise UserError('Input nilai memerlukan RPS final dengan bobot lengkap.')
        components = rps.komponen_ids
        grade_domain = [('penawaran_line_id', '=', line.id), ('krs_id.state', '=', 'approved')]
        completeness = request.httprequest.args.get('status', '')
        if completeness in ('complete', 'incomplete'):
            all_line_ids = request.env['erpobe.akademik.krs.line'].sudo().search(grade_domain).ids
            all_grade_rows = request.env['erpobe.grade.komponen'].sudo().search([
                ('krs_line_id', 'in', all_line_ids),
                ('rps_id', '=', rps.id),
                ('komponen_id', 'in', components.ids),
                ('is_graded', '=', True),
                ('origin', '=', 'actual'),
            ])
            component_ids_by_line = {}
            for grade in all_grade_rows:
                component_ids_by_line.setdefault(grade.krs_line_id.id, set()).add(grade.komponen_id.id)
            complete_ids = [
                line_id for line_id in all_line_ids
                if components and component_ids_by_line.get(line_id, set()) >= set(components.ids)
            ]
            if completeness == 'complete':
                grade_domain.append(('id', 'in', complete_ids))
            else:
                grade_domain.append(('id', 'not in', complete_ids))
        allocations = rps.bobot_komponen_cpmk_ids.filtered("rps_komponen_id")
        component_details = []
        for component in components:
            snapshot = rps.rps_komponen_ids.filtered(
                lambda item: item.komponen_id == component
            )[:1]
            component_allocations = allocations.filtered(
                lambda item: item.rps_komponen_id == snapshot
            )
            component_details.append({
                'id': component.id,
                'name': component.name,
                'weight': snapshot.bobot if snapshot else 0.0,
                'cpmks': [{
                    'name': allocation.cpmk_id.kode_cpmk,
                    'weight': allocation.bobot_komponen_cpmk,
                } for allocation in component_allocations],
            })
        page_krs_lines, pagination = self._list_page(
            request.env['erpobe.akademik.krs.line'].sudo(),
            grade_domain,
            f'/my/kelas/{line.id}/nilai',
            {'student': ('mahasiswa_id.name asc, id asc', 'Mahasiswa A–Z'), 'nim': ('mahasiswa_id.nim asc, id asc', 'NIM')},
            'mahasiswa_id.name asc, id asc',
            ('mahasiswa_id.name', 'mahasiswa_id.nim'),
            (('status', 'Kelengkapan nilai', (
                ('', 'Semua status'),
                ('incomplete', 'Belum lengkap'),
                ('complete', 'Lengkap'),
            )),),
        )
        error = ''
        if request.httprequest.method == 'POST':
            Grade = request.env['erpobe.grade.komponen'].sudo()
            try:
                with request.env.cr.savepoint():
                    audit_reason = request.httprequest.form.get('audit_reason', '').strip()
                    for krs_line in page_krs_lines:
                        for component in components:
                            raw = request.httprequest.form.get(f'grade_{krs_line.id}_{component.id}')
                            if raw is None:
                                continue
                            value = float(raw)
                            if value < 0 or value > 100:
                                raise ValidationError('Nilai harus berada pada rentang 0–100.')
                            grade = Grade.search([('krs_line_id', '=', krs_line.id), ('komponen_id', '=', component.id)], limit=1)
                            snapshot = rps.rps_komponen_ids.filtered(
                                lambda item: item.komponen_id == component
                            )[:1]
                            if grade:
                                grade.write({
                                    'nilai': value,
                                    'audit_reason': audit_reason,
                                    'rps_id': rps.id,
                                    'rps_komponen_id': snapshot.id if snapshot else False,
                                    'origin': 'actual',
                                    'is_graded': True,
                                })
                            else:
                                Grade.create({
                                    'krs_line_id': krs_line.id,
                                    'komponen_id': component.id,
                                    'nilai': value,
                                    'audit_reason': audit_reason,
                                    'rps_id': rps.id,
                                    'rps_komponen_id': snapshot.id if snapshot else False,
                                    'origin': 'actual',
                                    'is_graded': True,
                                })
                    Input = request.env['erpobe.input.nilai'].sudo()
                    input_record = Input.search([('penawaran_line_id', '=', line.id)], limit=1)
                    if not input_record:
                        input_record = Input.create({'penawaran_id': line.penawaran_id.id, 'penawaran_line_id': line.id})
                    all_class_lines = request.env['erpobe.akademik.krs.line'].sudo().search([
                        ('penawaran_line_id', '=', line.id),
                        ('krs_id.state', '=', 'approved'),
                    ])
                    input_record.action_calculate_grades_and_khs(all_class_lines)
            except (ValidationError, UserError, ValueError) as exc:
                error = str(exc)
        grade_rows = request.env['erpobe.grade.komponen'].sudo().search([
            ('krs_line_id', 'in', page_krs_lines.ids),
            ('rps_id', '=', rps.id),
        ])
        grade_map = {(grade.krs_line_id.id, grade.komponen_id.id): grade.nilai for grade in grade_rows}
        graded_map = {
            (grade.krs_line_id.id, grade.komponen_id.id): (
                grade.is_graded and grade.origin == 'actual'
            )
            for grade in grade_rows
        }
        grade_mk_rows = request.env['erpobe.grade.mk'].sudo().search([
            ('krs_line_id', 'in', page_krs_lines.ids),
            ('mk_id', '=', line.matakuliah_id.id),
            ('rps_id', '=', rps.id),
        ])
        final_scores = {
            grade.krs_line_id.id: grade.nilai_mk for grade in grade_mk_rows
        }
        cpmk_rows = request.env['erpobe.grade.cpmk'].sudo().search([
            ('krs_line_id', 'in', page_krs_lines.ids),
            ('rps_id', '=', rps.id),
        ])
        cpmk_scores = {}
        for grade in cpmk_rows:
            cpmk_scores.setdefault(grade.krs_line_id.id, []).append({
                'name': grade.cpmk_id.kode_cpmk,
                'score': grade.nilai_cpmk,
                'met': grade.status_capaian == 'tercapai',
            })
        data = []
        for krs_line in page_krs_lines:
            values = [{
                'id': component.id,
                'name': component.name,
                'value': grade_map.get((krs_line.id, component.id), 0.0),
            } for component in components]
            complete = bool(components) and all(
                graded_map.get((krs_line.id, component.id), False)
                for component in components
            )
            data.append({
                'id': krs_line.id,
                'name': krs_line.mahasiswa_id.name,
                'nim': krs_line.mahasiswa_id.nim,
                'complete': complete,
                'final_score': final_scores.get(krs_line.id),
                'cpmks': cpmk_scores.get(krs_line.id, []),
                'values': values,
            })
        completed_count = sum(1 for student in data if student['complete'])
        return request.render('erpobe.triton_teacher_grades_page', {
            'line_id': line.id,
            'course': line.matakuliah_id.name,
            'course_code': line.matakuliah_id.kode_mk,
            'year': line.tahun_ajaran_id.tahun_ajaran,
            'semester': line.tahun_ajaran_id.semester,
            'students': data,
            'completed_count': completed_count,
            'components': component_details,
            'error': error,
            'pagination': pagination,
            'list_action': f'/my/kelas/{line.id}/nilai',
            'grade_action': f'/my/kelas/{line.id}/nilai?{pagination["query_string"]}',
        })

    @http.route('/my/perwalian', type='http', auth='user', website=True)
    def triton_teacher_advising(self, **kwargs):
        teacher = self._require_teacher()
        students = request.env['erpobe.master.mahasiswa'].sudo().search([('dosen_wali_id', '=', teacher.id)])
        domain = [('mahasiswa_id', 'in', students.ids), ('state', 'in', ['submitted', 'approved', 'rejected'])]
        state = request.httprequest.args.get('state', '')
        if state in ('submitted', 'approved', 'rejected'):
            domain.append(('state', '=', state))
        krs, pagination = self._list_page(
            request.env['erpobe.akademik.krs'].sudo(),
            domain,
            '/my/perwalian',
            {'student': ('mahasiswa_id.name asc, id asc', 'Mahasiswa A–Z'), 'state': ('state asc, tahun_ajaran desc, id desc', 'Status')},
            'state asc, tahun_ajaran desc, id desc',
            ('mahasiswa_id.name', 'mahasiswa_id.nim', 'penawaran_id.name'),
            (('state', 'Status KRS', (
                ('', 'Semua status'),
                ('submitted', 'Menunggu persetujuan'),
                ('approved', 'Disetujui'),
                ('rejected', 'Perlu perbaikan'),
            )),),
        )
        records = [{'id': item.id, 'student': item.mahasiswa_id.name, 'cohort': item.mahasiswa_id.angkatan, 'offer': item.penawaran_id.name, 'sks': item.total_sks, 'state': item.state, 'note': item.advisor_note or '', 'courses': [line.matakuliah_id.name for line in item.line_ids]} for item in krs]
        return request.render('erpobe.triton_advising_page', {'krs_records': records, 'pagination': pagination, 'list_action': '/my/perwalian'})

    @http.route('/my/perwalian/<int:krs_id>/putusan', type='http', auth='user', website=True, methods=['POST'])
    def triton_advising_decision(self, krs_id, **kwargs):
        teacher = self._require_teacher()
        krs = request.env['erpobe.akademik.krs'].sudo().browse(krs_id)
        if not krs.exists() or krs.mahasiswa_id.dosen_wali_id != teacher:
            raise AccessError('KRS ini bukan milik mahasiswa bimbingan Anda.')
        action = request.httprequest.form.get('action')
        note = request.httprequest.form.get('note', '')
        if action == 'approve':
            krs.action_approve()
        elif action == 'reject':
            krs.action_reject(note)
        else:
            raise ValidationError('Keputusan KRS tidak dikenal.')
        return request.redirect('/my/perwalian')

    @http.route('/my/analisis', type='http', auth='user', website=True)
    def triton_teacher_analysis(self, **kwargs):
        teacher = self._require_teacher()
        lines, pagination = self._list_page(
            request.env['erpobe.akademik.penawaran.line'].sudo(),
            ['|', ('matakuliah_id.koordinator_id', '=', teacher.id), ('matakuliah_id.tim_pengampu_ids', 'in', teacher.id)],
            '/my/analisis',
            {'course': ('matakuliah_id.name asc, id asc', 'Mata kuliah A–Z'), 'term': ('tahun_ajaran_id desc, matakuliah_id.name asc, id asc', 'Tahun ajaran terbaru')},
            'tahun_ajaran_id desc, matakuliah_id asc, id asc',
            ('matakuliah_id.name', 'matakuliah_id.kode_mk'),
        )
        analysis = []
        GradeCpmk = request.env['erpobe.grade.cpmk'].sudo()
        for line in lines:
            students = line.mahasiswa_ids
            grades = GradeCpmk.search([('mahasiswa_id', 'in', students.ids), ('mk_id', '=', line.matakuliah_id.id)])
            by_cpmk = {}
            for grade in grades:
                by_cpmk.setdefault(grade.cpmk_id, []).append(grade.nilai_cpmk)
            analysis.append({'course': line.matakuliah_id.name, 'year': line.tahun_ajaran_id.tahun_ajaran, 'results': [{'name': cpmk.name, 'average': round(sum(values) / len(values), 2), 'below_target': sum((value < 75 for value in values))} for cpmk, values in by_cpmk.items()]})
        return request.render('erpobe.triton_teacher_analysis_page', {'analysis': analysis, 'pagination': pagination, 'list_action': '/my/analisis'})
