def migrate(cr, version):
    cr.execute(
        """
        UPDATE erpobe_akademik_komponen
           SET tipe = CASE
               WHEN lower(name) ~ '(hadir|presensi)' THEN 'attendance'
               WHEN lower(name) LIKE '%kuis%' THEN 'quiz'
               WHEN lower(name) LIKE '%tugas%' THEN 'assignment'
               WHEN lower(name) ~ '(uts|tengah)' THEN 'midterm'
               WHEN lower(name) ~ '(uas|akhir)' THEN 'final_exam'
               WHEN lower(name) LIKE '%presentasi%' THEN 'presentation'
               WHEN lower(name) ~ '(praktik|praktikum)' THEN 'practicum'
               WHEN lower(name) LIKE '%kasus%' THEN 'case_study'
               WHEN lower(name) LIKE '%proyek%' THEN 'project'
               WHEN lower(name) LIKE '%tbp%' THEN 'tbp'
               ELSE 'other'
           END
         WHERE tipe IN ('kognitif', 'partisipatif')
        """
    )
    cr.execute(
        """
        UPDATE erpobe_akademik_rps rps
           SET status = 'review'
          FROM ir_model_data data
         WHERE data.module = 'erpobe'
           AND data.model = 'erpobe.akademik.rps'
           AND data.name LIKE 'fixture_rps_%'
           AND data.res_id = rps.id
           AND rps.status = 'final'
        """
    )
    cr.execute(
        """
        INSERT INTO ir_config_parameter (key, value, create_uid, write_uid, create_date, write_date)
        VALUES ('erpobe.fixture.2022_cohort_seed_version', '2', 1, 1, NOW(), NOW())
        ON CONFLICT (key)
        DO UPDATE SET value = '2', write_uid = 1, write_date = NOW()
        """
    )
