import json

from urllib.parse import quote

from odoo import http
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.http import request

from .portal_base import TritonPortalBase


class TritonPortalHome(TritonPortalBase):

    @http.route()
    def home(self, **kwargs):
        return request.redirect('/my/triton')

    @http.route('/my/triton', type='http', auth='user', website=True)
    def triton_portal_home(self, **kwargs):
        student = self._student()
        teacher = self._teacher()
        if student:
            krs_records = request.env['erpobe.akademik.krs'].sudo().search([('mahasiswa_id', '=', student.id)], order='tahun_ajaran desc')
            pending = krs_records.filtered(lambda record: record.state == 'rejected')
            tasks = [{'title': 'Tinjau KRS', 'description': 'Periksa mata kuliah dan ajukan KRS tahun ajaran aktif.', 'url': '/my/krs'}]
            if pending:
                tasks.insert(0, {'title': 'Perbaiki KRS', 'description': 'Dosen wali mengembalikan KRS untuk diperbaiki.', 'url': '/my/krs'})
            role = 'Mahasiswa'
            report = request.env['erpobe.report.khs'].sudo().search(
                [('mahasiswa_id', '=', student.id)], limit=1
            )
            current_krs_records = request.env['erpobe.akademik.krs'].sudo().search(
                [
                    ('mahasiswa_id', '=', student.id),
                    ('penawaran_id.tahun_ajaran.aktif', '=', True),
                ],
                order='id desc',
            )
            courses_by_id = {}
            for line in current_krs_records.mapped('line_ids'):
                courses_by_id.setdefault(line.matakuliah_id.id, {
                    'name': line.matakuliah_id.name,
                    'code': line.matakuliah_id.kode_mk or '',
                    'sks': line.sks,
                })
            course_lines = list(courses_by_id.values())
            grade_lines = report.mk_line_ids if report else request.env['erpobe.report.khs.mk']
            grade_counts = {}
            for line in grade_lines:
                letter = line.nilai_huruf
                if letter:
                    grade_counts[letter] = grade_counts.get(letter, 0) + 1
            grade_labels = sorted(grade_counts)

            cpl_grades = request.env['erpobe.grade.cpl'].sudo().search(
                [('mahasiswa_id', '=', student.id)]
            )
            cpl_labels = []
            cpl_values = []
            if cpl_grades:
                cpl_labels = cpl_grades.mapped('cpl_id.kode_cpl')
                cpl_values = cpl_grades.mapped('nilai_cpl')
            dashboard = {
                'ipk': report.ipk if report else None,
                'credits_passed': report.total_sks_lulus if report else None,
                'krs_credits': sum(course['sks'] for course in course_lines) if current_krs_records else None,
                'krs_label': ', '.join(dict.fromkeys(
                    current_krs_records.mapped('penawaran_id.name')
                )),
                'courses': course_lines,
                'grade_labels_json': json.dumps(grade_labels),
                'grade_values_json': json.dumps([grade_counts[label] for label in grade_labels]),
                'cpl_labels_json': json.dumps(cpl_labels),
                'cpl_values_json': json.dumps(cpl_values),
            }
        elif teacher:
            lines = self._teacher_lines(teacher)
            pending_rps = lines.filtered(lambda line: line.latest_rps_id and line.latest_rps_id.status != 'final')
            advised = request.env['erpobe.master.mahasiswa'].sudo().search([('dosen_wali_id', '=', teacher.id)])
            pending_krs = request.env['erpobe.akademik.krs'].sudo().search_count([('mahasiswa_id', 'in', advised.ids), ('state', '=', 'submitted')])
            tasks = []
            if pending_rps:
                tasks.append({'title': 'Lengkapi atau tinjau RPS', 'description': f'{len(pending_rps)} penawaran masih memerlukan tindak lanjut RPS.', 'url': '/my/rps'})
            if pending_krs:
                tasks.append({'title': 'Persetujuan KRS perwalian', 'description': f'{pending_krs} KRS mahasiswa bimbingan menunggu keputusan.', 'url': '/my/perwalian'})
            tasks.append({'title': 'Pantau kelas yang diampu', 'description': 'Tinjau peserta kelas dan kelengkapan nilai.', 'url': '/my/kelas'})
            role = 'Dosen'
            krs_lines = request.env['erpobe.akademik.krs.line'].sudo().search(
                [
                    ('penawaran_line_id', 'in', lines.ids),
                    ('krs_id.state', '=', 'approved'),
                ]
            )
            grade_components = request.env['erpobe.grade.komponen'].sudo().search(
                [('krs_line_id', 'in', krs_lines.ids)]
            )
            graded_components = {}
            for grade in grade_components:
                graded_components.setdefault(grade.krs_line_id.id, set()).add(
                    grade.komponen_id.id
                )
            student_ids = krs_lines.mapped('mahasiswa_id').ids
            course_ids = lines.mapped('matakuliah_id').ids
            course_grades = request.env['erpobe.grade.mk'].sudo().search(
                [('mahasiswa_id', 'in', student_ids), ('mk_id', 'in', course_ids)]
            ) if student_ids and course_ids else request.env['erpobe.grade.mk']
            grade_by_student_course = {
                (grade.mahasiswa_id.id, grade.mk_id.id): grade.nilai_mk
                for grade in course_grades
            }
            class_rows = []
            total_students = 0
            completed_students = 0
            for line in lines:
                enrolled_lines = krs_lines.filtered(
                    lambda krs_line: krs_line.penawaran_line_id == line
                )
                component_ids = set(line.latest_rps_id.komponen_ids.ids) if line.latest_rps_id else set()
                finished = sum(
                    1
                    for krs_line in enrolled_lines
                    if component_ids
                    and component_ids.issubset(graded_components.get(krs_line.id, set()))
                )
                scores = [
                    grade_by_student_course[(krs_line.mahasiswa_id.id, line.matakuliah_id.id)]
                    for krs_line in enrolled_lines
                    if (krs_line.mahasiswa_id.id, line.matakuliah_id.id) in grade_by_student_course
                ]
                total_students += len(enrolled_lines)
                completed_students += finished
                class_rows.append({
                    'name': line.matakuliah_id.name,
                    'code': line.matakuliah_id.kode_mk or '',
                    'term': line.tahun_ajaran_id.tahun_ajaran,
                    'students': len(enrolled_lines),
                    'average': round(sum(scores) / len(scores), 2) if scores else None,
                    'graded': finished,
                    'line_id': line.id,
                    'can_grade': bool(
                        line.latest_rps_id
                        and line.latest_rps_id.status == 'final'
                        and line.latest_rps_id.weight_status == 'complete'
                    ),
                })
            classes_with_average = [
                row for row in class_rows if row['average'] is not None
            ]
            dashboard = {
                'course_count': len(lines.mapped('matakuliah_id')),
                'class_count': len(lines),
                'student_count': len(set(student_ids)),
                'pending_assessments': max(total_students - completed_students, 0),
                'completed_assessments': completed_students,
                'classes': class_rows,
                'class_averages_json': json.dumps([
                    row['average'] for row in classes_with_average
                ]),
                'class_labels_json': json.dumps([
                    row['code'] or row['name'] for row in classes_with_average
                ]),
            }
        else:
            tasks = [{'title': 'Hubungkan profil akademik', 'description': 'Hubungi administrator agar akun dikaitkan dengan profil ERP OBE.', 'url': '/my'}]
            role = 'Pengguna'
            dashboard = {}
        return request.render('erpobe.triton_portal_home_page', {
            'role': role,
            'tasks': tasks,
            'dashboard': dashboard,
            'user_name': request.env.user.name,
        })
