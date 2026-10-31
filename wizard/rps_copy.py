from odoo import api, fields, models
from odoo.exceptions import UserError


class ErpObeRpsCopyWizard(models.TransientModel):
    _name = "erpobe.wizard.rps.copy"
    _description = "Salin RPS dari Tahun Ajaran Sebelumnya"

    penawaran_line_id = fields.Many2one(
        "erpobe.akademik.penawaran.line", required=True, readonly=True
    )
    source_rps_id = fields.Many2one(
        "erpobe.akademik.rps",
        string="RPS Sumber",
        required=True,
        domain="[('matakuliah_id', '=', matakuliah_id)]",
    )
    matakuliah_id = fields.Many2one(
        related="penawaran_line_id.matakuliah_id", readonly=True
    )
    tahun_ajaran_id = fields.Many2one(
        related="penawaran_line_id.tahun_ajaran_id", readonly=True
    )

    @api.onchange("penawaran_line_id")
    def _onchange_penawaran_line_id(self):
        if not self.penawaran_line_id:
            return
        line = self.penawaran_line_id
        previous = self.env["erpobe.akademik.rps"].search(
            [
                ("matakuliah_id", "=", line.matakuliah_id.id),
                ("tahun_ajaran_id.semester", "=", line.tahun_ajaran_id.semester),
                (
                    "tahun_ajaran_id.tahun_ajaran",
                    "<",
                    line.tahun_ajaran_id.tahun_ajaran,
                ),
            ],
        )
        previous = previous.sorted(
            key=lambda record: (
                record.tahun_ajaran_id.tahun_ajaran,
                record.version,
                record.id,
            ),
            reverse=True,
        )
        return {"domain": {"source_rps_id": [("id", "in", previous.ids)]}}

    def action_copy(self):
        self.ensure_one()
        line = self.penawaran_line_id
        source = self.source_rps_id
        if (
            source.matakuliah_id != line.matakuliah_id
            or not source.tahun_ajaran_id
            or source.tahun_ajaran_id.semester != line.tahun_ajaran_id.semester
            or source.tahun_ajaran_id.tahun_ajaran
            >= line.tahun_ajaran_id.tahun_ajaran
        ):
            raise UserError(
                "Pilih RPS mata kuliah dan semester yang sama dari tahun ajaran "
                "sebelumnya."
            )
        new_rps = source.copy(
            {
                "matakuliah_id": line.matakuliah_id.id,
                "penawaran_line_id": line.id,
                "version": max(line.rps_ids.mapped("version"), default=0) + 1,
                "status": "review",
            }
        )
        return {
            "type": "ir.actions.act_window",
            "name": "RPS Salinan",
            "res_model": "erpobe.akademik.rps",
            "res_id": new_rps.id,
            "view_mode": "form",
            "target": "current",
        }


class ErpObeRpsBulkCopyWizard(models.TransientModel):
    _name = "erpobe.wizard.rps.bulk.copy"
    _description = "Salin Semua RPS dari Tahun Ajaran Sebelumnya"

    penawaran_id = fields.Many2one(
        "erpobe.akademik.penawaran", required=True, readonly=True
    )
    line_ids = fields.Many2many(
        "erpobe.akademik.penawaran.line",
        compute="_compute_line_ids",
        string="Penawaran tanpa RPS",
    )
    source_rps_ids = fields.Many2many(
        "erpobe.akademik.rps",
        compute="_compute_source_rps_ids",
        string="RPS Sumber yang Akan Disalin",
    )
    confirm_copy = fields.Boolean(
        string="Saya menyetujui penyalinan ke semua penawaran di atas",
        required=True,
        default=False,
    )
    result_summary = fields.Char(readonly=True)

    @api.depends("penawaran_id")
    def _compute_line_ids(self):
        for wizard in self:
            wizard.line_ids = wizard.penawaran_id.line_ids.filtered(
                lambda line: not line.rps_ids
            )

    @api.depends("penawaran_id", "line_ids")
    def _compute_source_rps_ids(self):
        for wizard in self:
            sources = self.env["erpobe.akademik.rps"]
            for line in wizard.line_ids:
                sources |= wizard._find_previous_rps(line)
            wizard.source_rps_ids = sources

    def _find_previous_rps(self, line):
        year = line.tahun_ajaran_id
        candidates = self.env["erpobe.akademik.rps"].search(
            [
                ("matakuliah_id", "=", line.matakuliah_id.id),
                ("tahun_ajaran_id.semester", "=", year.semester),
                ("tahun_ajaran_id.tahun_ajaran", "<", year.tahun_ajaran),
            ],
        )
        return candidates.sorted(
            key=lambda record: (
                record.tahun_ajaran_id.tahun_ajaran,
                record.version,
                record.id,
            ),
            reverse=True,
        )[:1]

    def action_copy(self):
        self.ensure_one()
        if not self.confirm_copy:
            raise UserError("Centang persetujuan sebelum menjalankan salin massal.")

        copied = 0
        without_source = []
        for line in self.line_ids:
            source = self._find_previous_rps(line)
            if not source:
                without_source.append(line.matakuliah_id.display_name)
                continue
            source.copy(
                {
                    "matakuliah_id": line.matakuliah_id.id,
                    "penawaran_line_id": line.id,
                    "version": 1,
                    "status": "review",
                }
            )
            copied += 1

        message = f"{copied} RPS disalin sebagai Perlu Ditinjau."
        if without_source:
            message += (
                " Tidak ada RPS tahun sebelumnya untuk: "
                + ", ".join(sorted(set(without_source)))
                + "."
            )
        self.result_summary = message
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        }
