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
