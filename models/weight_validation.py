from decimal import Decimal

from odoo import api, models


WEIGHT_TARGET = 100.0
WEIGHT_TOLERANCE = 0.01


def _weight_status(total):
    difference = WEIGHT_TARGET - total
    if abs(Decimal(str(total)) - Decimal(str(WEIGHT_TARGET))) <= Decimal(
        str(WEIGHT_TOLERANCE)
    ):
        return "complete", difference
    if difference < 0:
        return "over", difference
    return "under", difference


class ErpObeWeightValidation(models.AbstractModel):
    _name = "erpobe.weight.validation"
    _description = "Validasi dan Monitoring Kelengkapan Bobot"

    @api.model
    def get_rps_summary(self, rps):
        rps.ensure_one()
        groups = []

        for cpmk in rps.cpmk_ids:
            lines = rps.bobot_cpmk_cpl_ids.filtered(
                lambda line: line.cpmk_id == cpmk
            )
            total = sum(lines.mapped("bobot_cpmk_cpl"))
            status, difference = _weight_status(total)
            groups.append(
                self._group_result(
                    rps,
                    "cpmk_cpl",
                    cpmk.display_name,
                    total,
                    difference,
                    status,
                    cpmk_id=cpmk.id,
                    cpl_ids=lines.mapped("cpl_id").ids,
                )
            )

        for cpl in rps.cpl_ids:
            lines = rps.bobot_cpmk_cpl_ids.filtered(
                lambda line: line.cpl_id == cpl
            )
            total = sum(lines.mapped("bobot_cpmk_cpl"))
            status, difference = _weight_status(total)
            groups.append(
                self._group_result(
                    rps,
                    "cpl_cpmk",
                    cpl.display_name,
                    total,
                    difference,
                    status,
                    cpl_id=cpl.id,
                )
            )

        mk_total = sum(rps.bobot_cpmk_mk_ids.mapped("bobot_cpmk_mk"))
        status, difference = _weight_status(mk_total)
        groups.append(
            self._group_result(
                rps,
                "cpmk_mk",
                rps.matakuliah_id.display_name,
                mk_total,
                difference,
                status,
                mk_id=rps.matakuliah_id.id,
            )
        )

        for cpmk in rps.cpmk_ids:
            lines = rps.bobot_komponen_cpmk_ids.filtered(
                lambda line: line.cpmk_id == cpmk
            )
            total = sum(lines.mapped("bobot_komponen_cpmk"))
            status, difference = _weight_status(total)
            groups.append(
                self._group_result(
                    rps,
                    "komponen_cpmk",
                    cpmk.display_name,
                    total,
                    difference,
                    status,
                    cpmk_id=cpmk.id,
                )
            )

        return groups

    @api.model
    def _group_result(
        self, rps, relation, item_name, total, difference, status, **record_ids
    ):
        return {
            "rps_id": rps.id,
            "rps_name": rps.display_name,
            "prodi_id": rps.prodi_id.id,
            "matakuliah_id": rps.matakuliah_id.id,
            "relation": relation,
            "item_name": item_name,
            "total": total,
            "difference": difference,
            "status": status,
            **record_ids,
        }

    @api.model
    def get_problem_items(
        self, prodi_id, relation=None, matakuliah_id=None, cpl_id=None
    ):
        domain = [("prodi_id", "=", prodi_id)]
        if matakuliah_id:
            domain.append(("matakuliah_id", "=", matakuliah_id))
        rps_records = self.env["erpobe.akademik.rps"].search(
            domain, order="matakuliah_id, tahun_ajaran_id, version desc, id desc"
        )
        problems = []
        for rps in rps_records:
            for group in self.get_rps_summary(rps):
                if group["status"] == "complete":
                    continue
                if relation and group["relation"] != relation:
                    continue
                if cpl_id and (
                    group.get("cpl_id") != cpl_id
                    and cpl_id not in group.get("cpl_ids", [])
                ):
                    continue
                problems.append(group)
        return sorted(
            problems,
            key=lambda item: (abs(item["difference"]), item["item_name"]),
            reverse=True,
        )

    @api.model
    def validate_rps(self, rps):
        groups = self.get_rps_summary(rps)
        problems = [group for group in groups if group["status"] != "complete"]
        return {
            "complete": not problems,
            "groups": groups,
            "problems": problems,
        }
