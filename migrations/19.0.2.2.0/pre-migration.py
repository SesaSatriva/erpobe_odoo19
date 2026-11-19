def migrate(cr, version):
    cr.execute(
        """
        SELECT old_data.id, old_data.res_id, old_data.model,
               CASE WHEN industry.id IS NOT NULL THEN industry_data.id END,
               industry_data.res_id, industry_data.model
          FROM ir_model_data AS old_data
          JOIN erpobe_master_prodi AS old_program
            ON old_data.model = 'erpobe.master.prodi'
           AND old_program.id = old_data.res_id
           AND old_program.kode = 'IF'
     LEFT JOIN ir_model_data AS industry_data
            ON industry_data.module = 'erpobe'
           AND industry_data.name = 'prodi_ind'
           AND industry_data.model = 'erpobe.master.prodi'
     LEFT JOIN erpobe_master_prodi AS industry
            ON industry.id = industry_data.res_id
           AND industry.kode = 'IN'
         WHERE old_data.module = 'erpobe'
           AND old_data.name = 'prodi_ti'
        """
    )
    rows = cr.fetchall()
    if not rows:
        return
    if len(rows) != 1:
        raise ValueError("Multiple legacy program IDs found; refusing migration")

    old_data_id, _, _, industry_data_id, industry_id, _ = rows[0]
    cr.execute(
        "UPDATE ir_model_data SET name = %s WHERE id = %s",
        ("legacy_prodi_ti_19_0_2_2_0", old_data_id),
    )
    if industry_data_id:
        cr.execute(
            "UPDATE ir_model_data SET name = 'prodi_ti' WHERE id = %s",
            (industry_data_id,),
        )
        cr.execute(
            """
            SELECT data.id, data.name, data.res_id
              FROM ir_model_data AS data
              JOIN erpobe_master_rombel AS rombel ON rombel.id = data.res_id
             WHERE data.module = 'erpobe'
               AND data.model = 'erpobe.master.rombel'
               AND data.name ~ '^rombel_ind_'
               AND rombel.prodi_id = %s
            """,
            (industry_id,),
        )
        for data_id, old_name, res_id in cr.fetchall():
            new_name = old_name.replace("rombel_ind_", "rombel_in_", 1)
            cr.execute(
                """
                SELECT id, res_id FROM ir_model_data
                 WHERE module = 'erpobe' AND name = %s
                """,
                (new_name,),
            )
            existing = cr.fetchone()
            if existing and existing[1] != res_id:
                raise ValueError(f"Conflicting roster XML IDs for {new_name}")
            if existing:
                cr.execute("DELETE FROM ir_model_data WHERE id = %s", (data_id,))
            else:
                cr.execute(
                    "UPDATE ir_model_data SET name = %s WHERE id = %s",
                    (new_name, data_id),
                )
