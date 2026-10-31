from urllib.parse import quote

from odoo import http
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.http import request

from .portal_base import TritonPortalBase


class TritonPortalHome(TritonPortalBase):

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
        else:
            tasks = [{'title': 'Hubungkan profil akademik', 'description': 'Hubungi administrator agar akun dikaitkan dengan profil ERP OBE.', 'url': '/my'}]
            role = 'Pengguna'
        return request.render('erpobe.triton_portal_home_page', {'role': role, 'tasks': tasks, 'user_name': request.env.user.name})
