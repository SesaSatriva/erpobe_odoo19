from pathlib import Path

from lxml import etree

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestErpObeUiViews(TransactionCase):
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
