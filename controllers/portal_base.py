from urllib.parse import quote

from odoo import http
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal

from .list_helpers import TritonListHelpers


class TritonPortalBase(CustomerPortal, TritonListHelpers):

    def _teacher_lines(self, teacher):
        return request.env['erpobe.akademik.penawaran.line'].sudo().search(['|', ('matakuliah_id.koordinator_id', '=', teacher.id), ('matakuliah_id.tim_pengampu_ids', 'in', teacher.id)], order='tahun_ajaran_id desc, matakuliah_id asc')

    def _require_teacher(self):
        teacher = self._teacher()
        if not teacher:
            raise AccessError('Akun ini tidak terhubung ke profil dosen.')
        return teacher

    def _authorized_teacher_line(self, line_id):
        teacher = self._require_teacher()
        line = request.env['erpobe.akademik.penawaran.line'].sudo().browse(line_id)
        if not line.exists() or (line.matakuliah_id.koordinator_id != teacher and teacher not in line.matakuliah_id.tim_pengampu_ids):
            raise AccessError('Penawaran ini bukan kelas yang Anda ampu.')
        return (teacher, line)

    def _require_student(self):
        student = self._student()
        if not student:
            raise AccessError('Akun ini tidak terhubung ke profil mahasiswa.')
        return student

    def _teacher(self):
        if not request.env.user.has_group('erpobe.group_dosen'):
            return request.env['erpobe.master.dosen']
        return request.env['erpobe.master.dosen'].sudo().search([('user_id', '=', request.env.user.id)], limit=1)

    def _student(self):
        if not request.env.user.has_group('erpobe.group_mahasiswa'):
            return request.env['erpobe.master.mahasiswa']
        return request.env['erpobe.master.mahasiswa'].sudo().search([('user_id', '=', request.env.user.id)], limit=1)

    def _assessment_summary(self, line):
        rps = line.latest_rps_id
        krs_lines = request.env['erpobe.akademik.krs.line'].sudo().search([
            ('penawaran_line_id', '=', line.id),
            ('krs_id.state', '=', 'approved'),
        ])
        if not rps or rps.status != 'final':
            return {
                'rps': rps,
                'components': request.env['erpobe.akademik.komponen'],
                'krs_lines': krs_lines,
                'completed': krs_lines.browse(),
                'incomplete': krs_lines.browse(),
                'not_started': krs_lines,
                'ungraded': krs_lines.browse(),
                'component_count': 0,
                'record_count': 0,
                'actual_count': 0,
                'ungraded_count': 0,
                'unlinked_count': 0,
            }

        components = rps.komponen_ids
        grade_rows = request.env['erpobe.grade.komponen'].sudo().search([
            ('krs_line_id', 'in', krs_lines.ids),
            ('rps_id', '=', rps.id),
        ])
        actual_rows = grade_rows.filtered(
            lambda grade:
                grade.is_graded
                and grade.origin == 'actual'
                and grade.komponen_id in components
        )
        ungraded_rows = grade_rows.filtered(
            lambda grade:
                not grade.is_graded
                and grade.komponen_id in components
        )
        unlinked_rows = request.env['erpobe.grade.komponen'].sudo().search([
            ('krs_line_id', 'in', krs_lines.ids),
            ('rps_id', '=', False),
        ])

        actual_ids_by_line = {}
        for grade in actual_rows:
            actual_ids_by_line.setdefault(grade.krs_line_id.id, set()).add(
                grade.komponen_id.id
            )
        ungraded_ids_by_line = set(ungraded_rows.mapped('krs_line_id').ids)
        all_ids_by_line = set(grade_rows.mapped('krs_line_id').ids)

        completed = krs_lines.browse()
        incomplete = krs_lines.browse()
        not_started = krs_lines.browse()
        ungraded = krs_lines.browse()
        for krs_line in krs_lines:
            if components and set(components.ids).issubset(
                actual_ids_by_line.get(krs_line.id, set())
            ):
                completed |= krs_line
            else:
                if krs_line.id not in all_ids_by_line:
                    not_started |= krs_line
                else:
                    incomplete |= krs_line
            if krs_line.id in ungraded_ids_by_line:
                ungraded |= krs_line

        return {
            'rps': rps,
            'components': components,
            'krs_lines': krs_lines,
            'completed': completed,
            'incomplete': incomplete,
            'not_started': not_started,
            'ungraded': ungraded,
            'component_count': len(components),
            'record_count': len(krs_lines) * len(components),
            'actual_count': len(actual_rows),
            'ungraded_count': len(ungraded_rows),
            'unlinked_count': len(unlinked_rows),
        }
