from odoo import Command, fields, models


class ErpObeWeightMonitor(models.TransientModel):
    _name = "erpobe.weight.monitor"
    _description = "Monitoring Kelengkapan Bobot"

    prodi_id = fields.Many2one(
        "erpobe.master.prodi", required=True, readonly=True
    )
    relation = fields.Selection(
        [
            ("all", "Semua relasi"),
            ("cpmk_cpl", "CPMK → CPL"),
            ("cpl_cpmk", "CPL ← CPMK"),
            ("cpmk_mk", "CPMK → Mata Kuliah"),
            ("komponen_cpmk", "Komponen → CPMK"),
        ],
        default="all",
        required=True,
    )
    only_problems = fields.Boolean(string="Hanya yang bermasalah", default=True)
    matakuliah_id = fields.Many2one("erpobe.master.matakuliah")
    cpl_id = fields.Many2one("erpobe.akademik.cpl")
    line_ids = fields.One2many(
        "erpobe.weight.monitor.line", "monitor_id", string="Ringkasan Bobot"
    )
    summary = fields.Char(readonly=True)
    total_groups = fields.Integer(readonly=True)
    incomplete_groups = fields.Integer(readonly=True)
    complete_ratio = fields.Float(readonly=True)

    def action_refresh(self):
        self.ensure_one()
        validator = self.env["erpobe.weight.validation"]
        rps_records = self.env["erpobe.akademik.rps"].search(
            [("prodi_id", "=", self.prodi_id.id)]
        )
        groups = [
            group
            for rps in rps_records
            for group in validator.get_rps_summary(rps)
            if self.relation == "all" or group["relation"] == self.relation
            if not self.matakuliah_id
            or group["matakuliah_id"] == self.matakuliah_id.id
            if not self.cpl_id
            or group.get("cpl_id") == self.cpl_id.id
            or self.cpl_id.id in group.get("cpl_ids", [])
        ]
        if self.only_problems:
            groups = [group for group in groups if group["status"] != "complete"]
        groups.sort(
            key=lambda item: abs(item["difference"]), reverse=True
        )
        self.line_ids = [Command.clear()] + [
            Command.create(
                {
                    "rps_id": group["rps_id"],
                    "relation": group["relation"],
                    "item_name": group["item_name"],
                    "total": group["total"],
                    "difference": group["difference"],
                    "status": group["status"],
                    "severity": abs(group["difference"]),
                    "message": self._group_message(group),
                }
            )
            for group in groups
        ]
        all_groups = [
            group
            for rps in rps_records
            for group in validator.get_rps_summary(rps)
            if self.relation == "all" or group["relation"] == self.relation
            if not self.matakuliah_id
            or group["matakuliah_id"] == self.matakuliah_id.id
            if not self.cpl_id
            or group.get("cpl_id") == self.cpl_id.id
            or self.cpl_id.id in group.get("cpl_ids", [])
        ]
        self.total_groups = len(all_groups)
        self.incomplete_groups = sum(
            group["status"] != "complete" for group in all_groups
        )
        self.summary = (
            f"{self.incomplete_groups} dari {self.total_groups} kelompok "
            "bobot belum 100%."
        )
        self.complete_ratio = (
            100.0 * (self.total_groups - self.incomplete_groups) / self.total_groups
            if self.total_groups
            else 0.0
        )
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "current",
        }

    def action_open_export_list(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Ekspor Kelengkapan Bobot",
            "res_model": "erpobe.weight.monitor.line",
            "view_mode": "list",
            "domain": [("monitor_id", "=", self.id)],
            "target": "current",
        }

    @staticmethod
    def _group_message(group):
        labels = {
            "cpmk_cpl": "ke CPL",
            "cpl_cpmk": "dari CPMK pendukung",
            "cpmk_mk": "ke mata kuliah",
            "komponen_cpmk": "ke CPMK",
        }
        relation_label = labels[group["relation"]]
        if group["status"] == "under":
            return (
                f"{group['item_name']} baru terbobot {group['total']:.2f}% "
                f"{relation_label}, kurang {group['difference']:.2f}%."
            )
        return (
            f"{group['item_name']} terbobot {group['total']:.2f}% "
            f"{relation_label}, melebihi 100% sebesar "
            f"{abs(group['difference']):.2f}%."
        )


class ErpObeWeightMonitorLine(models.TransientModel):
    _name = "erpobe.weight.monitor.line"
    _description = "Baris Monitoring Kelengkapan Bobot"
    _order = "severity desc, id"

    monitor_id = fields.Many2one(
        "erpobe.weight.monitor", required=True, ondelete="cascade"
    )
    rps_id = fields.Many2one("erpobe.akademik.rps", readonly=True)
    relation = fields.Selection(
        [
            ("cpmk_cpl", "CPMK → CPL"),
            ("cpl_cpmk", "CPL ← CPMK"),
            ("cpmk_mk", "CPMK → Mata Kuliah"),
            ("komponen_cpmk", "Komponen → CPMK"),
        ],
        readonly=True,
    )
    item_name = fields.Char(readonly=True)
    total = fields.Float(string="Total (%)", readonly=True, digits=(5, 2))
    difference = fields.Float(
        string="Selisih ke 100% (+ kurang / - lebih)",
        readonly=True,
        digits=(5, 2),
    )
    status = fields.Selection(
        [
            ("complete", "Lengkap"),
            ("under", "Kurang"),
            ("over", "Melebihi"),
        ],
        readonly=True,
    )
    severity = fields.Float(readonly=True)
    message = fields.Char(readonly=True)

    def action_open_rps(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Perbaiki Bobot RPS",
            "res_model": "erpobe.akademik.rps",
            "res_id": self.rps_id.id,
            "view_mode": "form",
            "target": "current",
        }
