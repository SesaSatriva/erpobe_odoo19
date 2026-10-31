from urllib.parse import quote

from odoo import http
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.http import request

from .portal_base import TritonPortalBase


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
        active_offers = request.env['erpobe.akademik.penawaran'].sudo().search([('tahun_ajaran.aktif', '=', True), ('prodi_id', '=', student.prodi_id.id), ('rombel_ids', 'in', student.rombel_id.id)], order='name asc')
        offer_data = []
        for offer in active_offers:
            offer_data.append({'id': offer.id, 'name': offer.name, 'lines': [{'id': line.id, 'name': line.matakuliah_id.name, 'kode': line.matakuliah_id.kode_mk, 'sks': line.matakuliah_id.sks, 'selected': bool(krs and line in krs.line_ids.mapped('penawaran_line_id'))} for line in offer.line_ids.filtered(lambda item: student.rombel_id in item.rombel_ids)]})
        return request.render('erpobe.triton_krs_page', {'student': student, 'krs': krs, 'offers': offer_data, 'error': error, 'message': request.httprequest.args.get('error', '')})

    @http.route('/my/krs/<int:krs_id>/submit', type='http', auth='user', website=True, methods=['POST'])
    def triton_submit_krs(self, krs_id, **kwargs):
        student = self._require_student()
        krs = request.env['erpobe.akademik.krs'].sudo().search([('id', '=', krs_id), ('mahasiswa_id', '=', student.id)], limit=1)
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
        reports = request.env['erpobe.report.khs'].sudo().search([('mahasiswa_id', '=', student.id)], order='tahun_ajaran_id desc')
        data = []
        for report in reports:
            data.append({'year': report.tahun_ajaran_id.display_name if report.tahun_ajaran_id else 'Transkrip', 'id': report.id, 'ipk': report.ipk, 'sks': report.total_sks_lulus, 'courses': [{'name': line.mk_id.name, 'kode': line.kode_mk, 'sks': line.sks, 'score': line.nilai_angka, 'grade': line.nilai_huruf} for line in report.mk_line_ids]})
        return request.render('erpobe.triton_khs_page', {'reports': data})

    @http.route('/my/mata-kuliah', type='http', auth='user', website=True)
    def triton_student_courses(self, **kwargs):
        student = self._require_student()
        krs_lines = request.env['erpobe.akademik.krs.line'].sudo().search([('mahasiswa_id', '=', student.id), ('krs_id.state', '=', 'approved')], order='penawaran_line_id.tahun_ajaran_id desc, matakuliah_id asc')
        courses = []
        for line in krs_lines:
            final_rps = line.penawaran_line_id.rps_ids.filtered(lambda record: record.status == 'final').sorted(key=lambda record: (record.version, record.id), reverse=True)[:1]
            component_grades = request.env['erpobe.grade.komponen'].sudo().search([('krs_line_id', '=', line.id)])
            courses.append({'name': line.matakuliah_id.name, 'kode': line.matakuliah_id.kode_mk, 'sks': line.sks, 'year': line.penawaran_line_id.tahun_ajaran_id.tahun_ajaran, 'semester': line.penawaran_line_id.tahun_ajaran_id.semester, 'rps': bool(final_rps), 'components': [{'name': grade.komponen_id.name, 'score': grade.nilai} for grade in component_grades], 'cpmk': [{'name': cpmk.name, 'description': cpmk.name} for cpmk in (final_rps.cpmk_ids if final_rps else [])]})
        return request.render('erpobe.triton_student_courses_page', {'courses': courses})

    @http.route('/my/capaian-cpl', type='http', auth='user', website=True)
    def triton_student_cpl(self, **kwargs):
        student = self._require_student()
        grades = request.env['erpobe.grade.cpl'].sudo().search([('mahasiswa_id', '=', student.id)], order='cpl_id asc')
        values = [{'name': grade.cpl_id.kode_cpl, 'description': grade.cpl_id.name, 'score': grade.nilai_cpl, 'target': 75, 'met': grade.nilai_cpl >= 75} for grade in grades]
        return request.render('erpobe.triton_student_cpl_page', {'grades': values})

    @http.route('/my/profil', type='http', auth='user', website=True, methods=['GET', 'POST'])
    def triton_student_profile(self, **kwargs):
        student = self._student()
        teacher = self._teacher() if not student else request.env['erpobe.master.dosen']
        if not student and (not teacher):
            raise AccessError('Akun ini tidak terhubung ke profil akademik.')
        message = ''
        if request.httprequest.method == 'POST':
            profile = student or teacher
            profile.sudo().write({'public_opt_out': request.httprequest.form.get('public_opt_out') == '1'})
            message = 'Preferensi privasi berhasil disimpan.'
        return request.render('erpobe.triton_student_profile_page', {'student': student, 'teacher': teacher, 'message': message})
