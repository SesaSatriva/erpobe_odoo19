def migrate(cr, version):
    cr.execute("DROP TABLE IF EXISTS erpobe_grade_subcpmk_component_rel CASCADE")
    cr.execute("DROP TABLE IF EXISTS erpobe_grade_subcpmk CASCADE")
    cr.execute("DROP TABLE IF EXISTS erpobe_akademik_subcpmk CASCADE")

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
        UPDATE erpobe_akademik_rps_komponen snapshot
           SET tipe = COALESCE(component.tipe, 'other')
          FROM erpobe_akademik_komponen component
         WHERE snapshot.komponen_id = component.id
        """
    )
