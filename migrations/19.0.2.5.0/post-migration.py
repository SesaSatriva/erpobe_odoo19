from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    cr.execute(
        """
        UPDATE erpobe_akademik_cpl
           SET jenis_cpl = CASE
               WHEN lower(coalesce(kode_cpl, '') || ' ' || coalesce(name, '') || ' ' || coalesce(indikator_capaian, ''))
                    ~ '(etika|jujur|mandiri|tanggung jawab|kerja sama|kolaborasi|disiplin|nasionalisme|kewarganegaraan)' THEN 'sikap'
               WHEN lower(coalesce(kode_cpl, '') || ' ' || coalesce(name, '') || ' ' || coalesce(indikator_capaian, ''))
                    ~ '(komunikasi|tim|belajar sepanjang hayat|pengambilan keputusan|multidisiplin|manajemen|inovasi)' THEN 'keterampilan_umum'
               WHEN lower(coalesce(kode_cpl, '') || ' ' || coalesce(name, '') || ' ' || coalesce(indikator_capaian, ''))
                    ~ '(merancang|menganalisis|menggunakan alat|perancangan|analisis|rekayasa|teknik|komputasi|eksperimen|laboratorium)' THEN 'keterampilan_khusus'
               WHEN lower(coalesce(kode_cpl, '') || ' ' || coalesce(name, '') || ' ' || coalesce(indikator_capaian, ''))
                    ~ '(pengetahuan|memahami|menerapkan konsep|matematika|sains|prinsip|teori)' THEN 'pengetahuan'
               ELSE 'lainnya'
           END
         WHERE jenis_cpl IS NULL OR jenis_cpl = 'lainnya'
        """
    )

    env = api.Environment(cr, SUPERUSER_ID, {})
    grades = env["erpobe.grade.cpl"].sudo().search([])
    if grades:
        grades._compute_nilai_cpl()
