from pathlib import Path

from lxml import etree

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestErpObeUiViews(TransactionCase):
    def test_public_home_exposes_cpl_valid_counts(self):
        template_path = (
            Path(__file__).resolve().parents[1]
            / "views"
            / "website"
            / "public"
            / "website_home.xml"
        )
        arch = etree.parse(str(template_path))
        text = " ".join(arch.xpath("string(.)").split())
        self.assertIn("Capaian CPL valid belum tersedia", text)

    def test_public_and_student_rps_templates_remain_separate(self):
        base = Path(__file__).resolve().parents[1]
        home_arch = etree.parse(str(base / "views" / "website" / "public" / "website_home.xml"))
        self.assertTrue(
            home_arch.xpath(
                "//*[contains(@t-if, 'institutional_average') "
                "or contains(@t-att-value, 'institutional_average')]"
            )
        )
        student_arch = etree.parse(
            str(base / "views" / "website" / "portal" / "student" / "portal_courses.xml")
        )
        templates = student_arch.xpath("//template/@id")
        self.assertIn("triton_student_rps_detail_page", templates)
        self.assertNotIn("triton_rps_detail_page", templates)

    def test_teacher_dashboard_links_assessment_detail_statuses(self):
        template_path = (
            Path(__file__).resolve().parents[1]
            / "views"
            / "website"
            / "portal"
            / "portal_dashboard.xml"
        )
        arch = etree.parse(str(template_path))
        status_links = arch.xpath(
            "//a[contains(@t-att-href, '/nilai?status=')]"
        )
        self.assertGreaterEqual(len(status_links), 3)

    def test_portal_monitoring_templates_use_professional_tables(self):
        template_files = (
            "views/website/portal/teacher/portal_rps.xml",
            "views/website/portal/teacher/portal_rps_edit.xml",
            "views/website/portal/student/portal_courses.xml",
            "views/website/portal/student/portal_cpl.xml",
        )
        base = Path(__file__).resolve().parents[1]
        for relative_path in template_files:
            arch = etree.parse(str(base / relative_path))
            root = arch.getroot()
            table_count = len(root.xpath("//table"))
            self.assertGreater(table_count, 0, relative_path)

    def test_student_cpl_uses_compact_list_and_notebook_detail(self):
        template_path = (
            Path(__file__).resolve().parents[1]
            / "views"
            / "website"
            / "portal"
            / "student"
            / "portal_cpl.xml"
        )
        arch = etree.parse(str(template_path))
        list_template = arch.xpath(
            "//template[@id='triton_student_cpl_page']"
        )[0]
        list_headers = [
            " ".join(header.itertext()).strip()
            for header in list_template.xpath(".//table/thead/tr/th")
        ]
        self.assertEqual(
            list_headers,
            ["CPL", "Jenis", "Capaian / Target", "Status", "Aksi"],
        )
        self.assertFalse(
            list_template.xpath(
                ".//th[contains(., 'CPMK kontributor') "
                "or contains(., 'Mata kuliah dan keterlacakan')]"
            )
        )

        detail_template = arch.xpath(
            "//template[@id='triton_student_cpl_detail_page']"
        )[0]
        self.assertEqual(
            detail_template.xpath("//ul[@role='tablist']/li/button/@data-bs-target"),
            [
                "#cpl-summary",
                "#cpl-cpmk",
                "#cpl-courses",
                "#cpl-calculation",
            ],
        )
        self.assertEqual(
            detail_template.xpath("//div[contains(@class, 'tab-content')]/section/@id"),
            ["cpl-summary", "cpl-cpmk", "cpl-courses", "cpl-calculation"],
        )

    def test_portal_profile_exposes_native_security_route(self):
        profile_path = (
            Path(__file__).resolve().parents[1]
            / "views"
            / "website"
            / "portal"
            / "portal_profile.xml"
        )
        arch = etree.parse(str(profile_path))
        security_links = arch.xpath("//a[@href='/my/security']")
        self.assertEqual(len(security_links), 1)
        self.assertIn("kata sandi", " ".join(security_links[0].itertext()).lower())

    def test_owl_templates_key_foreach_loops(self):
        template_root = Path(__file__).resolve().parents[1] / "static" / "src"
        unkeyed_loops = []

        for template_path in template_root.rglob("*.xml"):
            arch = etree.parse(str(template_path))
            for loop in arch.xpath("//*[@t-foreach and not(@t-key)]"):
                unkeyed_loops.append(
                    f"{template_path.relative_to(template_root)}: "
                    f'{loop.get("t-foreach")}'
                )

        self.assertFalse(unkeyed_loops, "\n".join(unkeyed_loops))

    def test_actions_load_all_configured_views(self):
        action_data = self.env["ir.model.data"].search(
            [
                ("module", "=", "erpobe"),
                ("model", "=", "ir.actions.act_window"),
            ]
        )
        actions = self.env["ir.actions.act_window"].browse(
            action_data.mapped("res_id")
        ).exists()

        for action in actions.filtered(
            lambda record: record.res_model.startswith("erpobe.")
        ):
            view_types = set(action.view_mode.split(",")) | {"search"}
            result = self.env[action.res_model].get_views(
                [(False, view_type) for view_type in sorted(view_types)],
                options={"action_id": action.id},
            )
            for view_type in view_types:
                self.assertIn(view_type, result["views"], action.display_name)

    def test_cpmk_and_cpl_analytics_can_filter_by_cohort_and_class(self):
        for action_xmlid, model_name in (
            ("erpobe.action_erpobe_summary_cpmk", "erpobe.summary.cpmk"),
            ("erpobe.action_erpobe_summary_cpl", "erpobe.summary.cpl"),
        ):
            result = self.env[model_name].get_views(
                [(False, "search")],
                options={"action_id": self.env.ref(action_xmlid).id},
            )
            arch = etree.fromstring(result["views"]["search"]["arch"].encode())
            fields = set(arch.xpath("//field/@name"))
            self.assertTrue({"angkatan", "rombel_id"} <= fields, model_name)

    def test_analytics_menu_opens_student_khs_with_all_grade_tabs(self):
        menu = self.env.ref("erpobe.menu_erpobe_results")
        action = self.env.ref("erpobe.action_erpobe_khs")
        self.assertEqual(menu.action, action)
        self.assertEqual(action.res_model, "erpobe.report.khs")

        views = self.env["erpobe.report.khs"].get_views(
            [(False, "list"), (False, "form"), (False, "search")],
            options={"action_id": action.id},
        )["views"]
        list_arch = etree.fromstring(views["list"]["arch"].encode())
        form_arch = etree.fromstring(views["form"]["arch"].encode())
        search_arch = etree.fromstring(views["search"]["arch"].encode())

        self.assertIn("mahasiswa_id", list_arch.xpath("//field/@name"))
        self.assertTrue(
            {"angkatan", "rombel_id"} <= set(search_arch.xpath("//field/@name"))
        )
        self.assertEqual(
            form_arch.xpath("//notebook/page/@string"),
            ["Capaian CPL", "Capaian CPMK", "Nilai MK", "Nilai Komponen"],
        )
        self.assertIn(
            "komponen_line_ids",
            form_arch.xpath("//page[@string='Nilai Komponen']/field/@name"),
        )

    def test_faculty_form_only_contains_program_studies(self):
        action = self.env.ref("erpobe.action_erpobe_master_fakultas")
        result = self.env["erpobe.master.fakultas"].get_views(
            [(False, "form")],
            options={"action_id": action.id},
        )
        arch = etree.fromstring(result["views"]["form"]["arch"].encode())
        field_names = set(arch.xpath("//field/@name"))
        self.assertEqual(
            field_names,
            {"active", "kode", "name", "prodi_ids"},
        )
        root_menu = self.env.ref("erpobe.menu_erpobe_root")
        self.assertEqual(
            self.env.ref("erpobe.menu_erpobe_master_fakultas").parent_id,
            root_menu,
        )
        self.assertEqual(
            self.env.ref("erpobe.menu_erpobe_master_prodi").parent_id,
            root_menu,
        )
