from decimal import Decimal, ROUND_DOWN

from odoo import api, models


WEIGHT_TARGET = 100.0
WEIGHT_TOLERANCE = 0.01


def _weight_status(total):
    total_decimal = Decimal(str(total))
    difference = float(Decimal(str(WEIGHT_TARGET)) - total_decimal)
    if abs(total_decimal - Decimal(str(WEIGHT_TARGET))) <= Decimal(
        str(WEIGHT_TOLERANCE)
    ):
        return "complete", difference
    if difference < 0:
        return "over", difference
    return "under", difference


def _distribute_percent(total, count, precision=2):
    if count <= 0:
        raise ValueError("count must be positive")
    quantum = Decimal(1).scaleb(-precision)
    total_decimal = Decimal(str(total))
    base = (total_decimal / count).quantize(quantum, rounding=ROUND_DOWN)
    values = [base] * (count - 1)
    values.append(total_decimal - sum(values, Decimal("0")))
    return [float(value) for value in values]


class ErpObeWeightValidation(models.AbstractModel):
    _name = "erpobe.weight.validation"
    _description = "Validasi dan Monitoring Kelengkapan Bobot"

    @api.model
    def get_rps_summary(self, rps):
        rps.ensure_one()
        groups = []

        if rps.rps_komponen_ids:
            active_components = rps.rps_komponen_ids.filtered(
                lambda component: component.aktif
            )
            component_total = sum(active_components.mapped("bobot"))
            status, difference = _weight_status(component_total)
            groups.append(
                self._group_result(
                    rps,
                    "rps_component_total",
                    rps.matakuliah_id.display_name,
                    component_total,
                    difference,
                    status,
                    mk_id=rps.matakuliah_id.id,
                )
            )
            for component in active_components:
                allocations = component.allocation_ids.filtered(
                    lambda line: line.rps_id == rps
                )
                allocation_total = sum(
                    (Decimal(str(value)) for value in allocations.mapped(
                        "bobot_komponen_cpmk"
                    )),
                    Decimal("0"),
                )
                status, difference = _weight_status(allocation_total)
                groups.append(
                    self._group_result(
                        rps,
                        "rps_component_cpmk",
                        component.name,
                        allocation_total,
                        difference,
                        status,
                        rps_komponen_id=component.id,
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
            return groups

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
