def migrate(cr, version):
    cr.execute(
        """
        SELECT column_name
          FROM information_schema.columns
         WHERE table_schema = current_schema()
           AND table_name = 'erpobe_akademik_cpl'
           AND column_name IN ('code', 'description', 'kode_cpl', 'name')
        """
    )
    columns = {row[0] for row in cr.fetchall()}

    if "code" in columns and "kode_cpl" in columns:
        cr.execute(
            """
            UPDATE erpobe_akademik_cpl
               SET kode_cpl = code
             WHERE (kode_cpl IS NULL OR BTRIM(kode_cpl) = '')
               AND code IS NOT NULL
               AND BTRIM(code) <> ''
            """
        )
        cr.execute(
            """
            SELECT id
              FROM erpobe_akademik_cpl
             WHERE code IS NOT NULL
               AND BTRIM(code) <> ''
               AND kode_cpl IS NOT NULL
               AND BTRIM(kode_cpl) <> ''
               AND code <> kode_cpl
             LIMIT 1
            """
        )
        if cr.fetchone():
            raise ValueError(
                "CPL legacy code differs from kode_cpl; refusing to discard data."
            )

    if "description" in columns and "name" in columns:
        cr.execute(
            """
            UPDATE erpobe_akademik_cpl
               SET name = description
             WHERE (name IS NULL OR BTRIM(name) = '')
               AND description IS NOT NULL
               AND BTRIM(description) <> ''
            """
        )
        cr.execute(
            """
            SELECT id
              FROM erpobe_akademik_cpl
             WHERE description IS NOT NULL
               AND BTRIM(description) <> ''
               AND name IS NOT NULL
               AND BTRIM(name) <> ''
               AND description <> name
             LIMIT 1
            """
        )
        if cr.fetchone():
            raise ValueError(
                "CPL legacy description differs from name; refusing to discard data."
            )

    if "code" in columns:
        cr.execute("ALTER TABLE erpobe_akademik_cpl DROP COLUMN code")
    if "description" in columns:
        cr.execute("ALTER TABLE erpobe_akademik_cpl DROP COLUMN description")
