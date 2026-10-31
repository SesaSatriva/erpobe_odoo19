from lxml import etree

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestErpObeUiViews(TransactionCase):
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
        self.assertEqual(
            self.env.ref("erpobe.menu_erpobe_master_prodi").parent_id,
            self.env.ref("erpobe.menu_erpobe_master_fakultas"),
        )
