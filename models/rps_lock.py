from odoo import api, models
from odoo.exceptions import UserError


class ErpObeRpsLockMixin(models.AbstractModel):
    _name = "erpobe.rps.lock.mixin"
    _description = "Perlindungan RPS Final"

    _rps_link_field = "rps_id"

    def _check_rps_editable(self):
        rps_records = self.mapped(self._rps_link_field)
        if any(rps.status == "final" for rps in rps_records):
            raise UserError(
                "Isi RPS berstatus Final bersifat read-only. Salin RPS untuk membuat versi baru."
            )

    def _reset_review_status(self):
        if self.env.context.get("preserve_rps_review_status"):
            return
        rps_records = self.mapped(self._rps_link_field).filtered(
            lambda rps: rps.status == "review"
        )
        if rps_records:
            rps_records.write({"status": "draft"})

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._check_rps_editable()
        records._reset_review_status()
        return records

    def write(self, vals):
        self._check_rps_editable()
        result = super().write(vals)
        self._check_rps_editable()
        self._reset_review_status()
        return result

    def unlink(self):
        self._check_rps_editable()
        return super().unlink()
