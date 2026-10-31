def migrate(cr, version):
    cr.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                  FROM information_schema.columns
                 WHERE table_name = 'erpobe_master_fakultas'
                   AND column_name = 'dekan_id'
            ) THEN
                CREATE TABLE IF NOT EXISTS erpobe_master_fakultas_dekan_archive (
                    fakultas_id integer PRIMARY KEY,
                    dekan_id integer
                );
                INSERT INTO erpobe_master_fakultas_dekan_archive
                    (fakultas_id, dekan_id)
                SELECT id, dekan_id
                  FROM erpobe_master_fakultas
                 WHERE dekan_id IS NOT NULL
                ON CONFLICT (fakultas_id) DO UPDATE
                    SET dekan_id = EXCLUDED.dekan_id;
            END IF;
        END
        $$;
        """
    )
