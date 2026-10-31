from urllib.parse import quote

from odoo import http
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal



class TritonPortalBase(CustomerPortal):

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
