def migrate(cr, version):
    cr.execute(
        """
        DROP TABLE IF EXISTS erpobe_grade_subcpmk_component_rel CASCADE
        """
    )
    cr.execute("DROP TABLE IF EXISTS erpobe_grade_subcpmk CASCADE")
    cr.execute("DROP TABLE IF EXISTS erpobe_akademik_subcpmk CASCADE")
