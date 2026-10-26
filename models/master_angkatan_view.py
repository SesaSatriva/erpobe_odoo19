from odoo import models, fields, api, tools

class ErpObeMasterAngkatanView(models.Model):
    _name = "erpobe.master.angkatan.view"
    _description = "View Master Angkatan (Virtual)"
    _auto = False  # Penting: Agar tidak membuat tabel fisik, tapi membaca dari SQL View
    _rec_name = "name"
    _order = "name desc"

    # Kolom yang akan dibaca dari SQL
    name = fields.Char(string="Tahun")       # Untuk label (misal: "2023")
    angkatan = fields.Integer(string="Nilai") # Untuk logic (misal: 2023)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW erpobe_master_angkatan_view AS (
                SELECT
                    min(id) as id,           -- ID unik (dummy)
                    CAST(angkatan AS VARCHAR) as name, -- Ubah integer ke string untuk label
                    angkatan                 -- Nilai asli
                FROM
                    erpobe_master_rombel
                GROUP BY
                    angkatan
            )
        """)