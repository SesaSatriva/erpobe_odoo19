def migrate(cr, version):
    cr.execute(
        """
        ALTER TABLE erpobe_master_fakultas
        DROP COLUMN IF EXISTS dekan_id
        """
    )
    cr.execute(
        """
        WITH line_candidates AS (
            SELECT matakuliah_id,
                   MIN(id) AS penawaran_line_id,
                   COUNT(DISTINCT id) AS candidate_count
              FROM erpobe_akademik_penawaran_line
             GROUP BY matakuliah_id
        ),
        rps_counts AS (
            SELECT matakuliah_id, COUNT(*) AS rps_count
              FROM erpobe_akademik_rps
             WHERE penawaran_line_id IS NULL
             GROUP BY matakuliah_id
        )
        UPDATE erpobe_akademik_rps AS rps
           SET penawaran_line_id = line_candidates.penawaran_line_id,
               version = 1,
               status = 'review'
          FROM line_candidates, rps_counts
         WHERE line_candidates.matakuliah_id = rps.matakuliah_id
           AND rps_counts.matakuliah_id = rps.matakuliah_id
           AND line_candidates.candidate_count = 1
           AND rps_counts.rps_count = 1
           AND rps.penawaran_line_id IS NULL
        """
    )
    cr.execute(
        """
        WITH program_scopes AS (
            SELECT penawaran_id,
                   MIN(prodi_id) AS prodi_id,
                   COUNT(DISTINCT prodi_id) AS prodi_count
              FROM erpobe_akademik_penawaran_line
             WHERE prodi_id IS NOT NULL
             GROUP BY penawaran_id
        )
        UPDATE erpobe_akademik_penawaran AS offer
           SET prodi_id = program_scopes.prodi_id
          FROM program_scopes
         WHERE program_scopes.penawaran_id = offer.id
           AND program_scopes.prodi_count = 1
           AND offer.prodi_id IS NULL
        """
    )
