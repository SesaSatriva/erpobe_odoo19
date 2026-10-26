from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class ErpObeMasterFakultas(models.Model):
    _name = "erpobe.master.fakultas"
    _description = "Master Fakultas"
    _order = "name"

    name = fields.Char(required=True, index=True)
    kode = fields.Char(required=True, index=True)
    active = fields.Boolean(default=True)
    dekan_id = fields.Many2one(
        "erpobe.master.dosen", ondelete="set null", string="Dekan"
    )
    prodi_ids = fields.One2many(
        "erpobe.master.prodi", "fakultas_id", string="Program Studi"
    )

    _kode_unique = models.Constraint("UNIQUE (kode)", "Kode fakultas harus unik.")
    _name_unique = models.Constraint("UNIQUE (name)", "Nama fakultas harus unik.")

    @api.depends("kode", "name")
    def _compute_display_name(self):
        for record in self:
            record.display_name = f"{record.kode} - {record.name}"

    @api.constrains("dekan_id")
    def _check_dekan_faculty(self):
        for record in self:
            if (
                record.dekan_id
                and record not in record.dekan_id.prodi_ids.mapped("fakultas_id")
            ):
                raise ValidationError("Dekan harus berasal dari fakultas yang sama.")

    @api.constrains("dekan_id", "name", "kode")
    def _check_unique_values(self):
        for record in self:
            duplicate = self.search(
                [
                    ("id", "!=", record.id),
                    "|",
                    ("name", "=", record.name),
                    ("kode", "=", record.kode),
                ],
                limit=1,
            )
            if duplicate:
                raise ValidationError("Nama dan kode fakultas harus unik.")

    @api.ondelete(at_uninstall=False)
    def _unlink_if_used(self):
        if self.mapped("prodi_ids"):
            raise UserError(
                "Fakultas yang masih memiliki program studi tidak dapat dihapus."
            )
