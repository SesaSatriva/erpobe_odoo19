from odoo import models, fields, api

class ResPartner(models.Model):
    _inherit = "res.partner"

    # Field baru untuk menampung Role dan Nomor Induk
    obe_role = fields.Selection([
        ('dosen', 'Dosen'),
        ('mahasiswa', 'Mahasiswa'),
        ('umum', 'Umum')
    ], string="Peran ERP OBE", compute="_compute_obe_identity")

    obe_nomor_induk = fields.Char(string="NIP / NIM", compute="_compute_obe_identity")

    def _compute_obe_identity(self):
        # Mengambil ID partner yang sedang di-load view
        partner_ids = self.ids
        if not partner_ids:
            self.obe_role = 'umum'
            self.obe_nomor_induk = False
            return

        # Bulk search ke tabel Dosen agar performa cepat (menghindari N+1 query loop)
        dosen_recs = self.env['erpobe.master.dosen'].search_read(
            [('partner_id', 'in', partner_ids)], ['partner_id', 'nip']
        )
        # Dictionary mapping: {partner_id: nip}
        dosen_map = {d['partner_id'][0]: d['nip'] for d in dosen_recs}

        # Bulk search ke tabel Mahasiswa
        mhs_recs = self.env['erpobe.master.mahasiswa'].search_read(
            [('partner_id', 'in', partner_ids)], ['partner_id', 'nim']
        )
        # Dictionary mapping: {partner_id: nim}
        mhs_map = {m['partner_id'][0]: m['nim'] for m in mhs_recs}

        # Assign nilai ke setiap record
        for rec in self:
            if rec.id in dosen_map:
                rec.obe_role = 'dosen'
                rec.obe_nomor_induk = dosen_map[rec.id]
            elif rec.id in mhs_map:
                rec.obe_role = 'mahasiswa'
                rec.obe_nomor_induk = mhs_map[rec.id]
            else:
                rec.obe_role = 'umum'
                rec.obe_nomor_induk = False