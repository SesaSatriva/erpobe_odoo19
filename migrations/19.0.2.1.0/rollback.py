def rollback(cr):
    cr.execute(
        """
        UPDATE erpobe_master_fakultas AS faculty
           SET dekan_id = archive.dekan_id
          FROM erpobe_master_fakultas_dekan_archive AS archive
         WHERE archive.fakultas_id = faculty.id
           AND EXISTS (
               SELECT 1
                 FROM erpobe_master_dosen AS dosen
                WHERE dosen.id = archive.dekan_id
           )
        """
    )
