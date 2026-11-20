from odoo import Command
from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged

from ..models.weight_validation import _distribute_percent, _weight_status


@tagged("post_install", "-at_install")
class TestErpObeWeightValidation(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Faculty = cls.env["erpobe.master.fakultas"]
        cls.Prodi = cls.env["erpobe.master.prodi"]
        cls.Matakuliah = cls.env["erpobe.master.matakuliah"]
        cls.CPL = cls.env["erpobe.akademik.cpl"]
        cls.CPMK = cls.env["erpobe.akademik.cpmk"]
        cls.RPS = cls.env["erpobe.akademik.rps"]
        cls.Component = cls.env["erpobe.akademik.komponen"]
        cls.Validator = cls.env["erpobe.weight.validation"]

        faculty = cls.Faculty.create({"name": "Fakultas Bobot", "kode": "FBT"})
        prodi = cls.Prodi.create(
            {"name": "Prodi Bobot", "kode": "PBT", "fakultas_id": faculty.id}
        )
        cls.course = cls.Matakuliah.create(
            {
                "name": "Mata Kuliah Bobot",
                "kode_mk": "MKB",
                "sks": 3,
                "semester": 1,
                "prodi_id": prodi.id,
            }
        )
        cls.cpl = cls.CPL.create(
            {"name": "CPL Bobot", "kode_cpl": "CPL-B", "prodi_id": prodi.id}
        )
        cls.cpmk = cls.CPMK.create(
            {"mk_id": cls.course.id, "kode_cpmk": "CPMK-B", "name": "CPMK Bobot"}
        )
        cls.env["erpobe.akademik.cpl.mk.cpmk"].create(
            {"cpl_id": cls.cpl.id, "cpmk_id": cls.cpmk.id}
        )
        cls.component = cls.Component.create(
            {"name": "Komponen Bobot", "tipe": "kognitif"}
        )

    def _create_course_with_cpmks(self, count, suffix):
        course = self.Matakuliah.create(
            {
                "name": f"Mata Kuliah Bobot {suffix}",
                "kode_mk": f"MK-{suffix}",
                "sks": 3,
                "semester": 1,
                "prodi_id": self.course.prodi_id.id,
            }
        )
        self.CPMK.create(
            [
                {
                    "mk_id": course.id,
                    "kode_cpmk": f"CPMK-{suffix}-{index}",
                    "name": f"CPMK {suffix}-{index}",
                }
                for index in range(1, count + 1)
            ]
        )
        return course

    def _create_rps(self, components=None, course=None):
        rps = self.RPS.create(
            {
                "matakuliah_id": (course or self.course).id,
                "komponen_ids": [Command.set((components or self.component).ids)],
            }
        )
        rps._sync_bobot_tables()
        return rps

    def test_exact_under_over_and_decimal_tolerance(self):
        self.assertEqual(_weight_status(100.0), ("complete", 0.0))
        self.assertEqual(_weight_status(80.0), ("under", 20.0))
        self.assertEqual(_weight_status(120.0), ("over", -20.0))
        self.assertEqual(_weight_status(100.01)[0], "complete")
        self.assertEqual(_weight_status(99.99)[0], "complete")
        self.assertEqual(_weight_status(100.011)[0], "over")

    def test_percent_distribution_handles_one_two_and_three_cpmks(self):
        self.assertEqual(_distribute_percent(100, 1), [100.0])
        self.assertEqual(_distribute_percent(100, 2), [50.0, 50.0])
        self.assertEqual(_distribute_percent(100, 3), [33.33, 33.33, 33.34])
        self.assertEqual(sum(_distribute_percent(100, 3)), 100.0)

    def test_component_allocations_accept_one_two_or_three_cpmks(self):
        scenarios = ((1, [100.0]), (2, [50.0, 50.0]), (3, [40.0, 30.0, 30.0]))
        for scenario_index, (count, weights) in enumerate(scenarios, start=1):
            course = self._create_course_with_cpmks(count, f"A{scenario_index}")
            rps = self._create_rps(course=course)
            snapshot = rps.rps_komponen_ids[:1]
            allocations = snapshot.allocation_ids.sorted("cpmk_id")
            self.assertEqual(len(allocations), count)
            snapshot.write({"bobot": 100.0})
            for allocation, weight in zip(allocations, weights):
                allocation.write({"bobot_komponen_cpmk": weight})
            summary = self.Validator.get_rps_summary(rps)
            self.assertTrue(all(group["status"] == "complete" for group in summary))
            rps.action_mark_for_review()
            rps.action_finalize()
            self.assertEqual(rps.status, "final")

    def test_incomplete_or_excess_component_allocation_blocks_finalization(self):
        for scenario_index, (weights, expected) in enumerate(
            (([45.0, 45.0], "under"), ([60.0, 60.0], "over")),
            start=1,
        ):
            course = self._create_course_with_cpmks(2, f"B{scenario_index}")
            rps = self._create_rps(course=course)
            snapshot = rps.rps_komponen_ids[:1]
            snapshot.write({"bobot": 100.0})
            allocations = snapshot.allocation_ids.sorted("cpmk_id")
            for allocation, weight in zip(allocations, weights):
                allocation.write({"bobot_komponen_cpmk": weight})
            component_group = next(
                group
                for group in self.Validator.get_rps_summary(rps)
                if group["relation"] == "rps_component_cpmk"
            )
            self.assertEqual(component_group["status"], expected)
            self.assertAlmostEqual(component_group["total"], sum(weights))
            rps.action_mark_for_review()
            with self.assertRaises(UserError):
                rps.action_finalize()

    def test_component_course_weight_must_total_one_hundred(self):
        rps = self._create_rps()
        snapshot = rps.rps_komponen_ids[:1]
        snapshot.write({"bobot": 99.0})
        snapshot.allocation_ids.write({"bobot_komponen_cpmk": 100.0})
        component_group = next(
            group
            for group in self.Validator.get_rps_summary(rps)
            if group["relation"] == "rps_component_total"
        )
        self.assertEqual(component_group["status"], "under")
        rps.action_mark_for_review()
        with self.assertRaises(UserError):
            rps.action_finalize()

    def test_rps_snapshot_component_weights_are_validated(self):
        rps = self._create_rps()
        snapshot = rps.rps_komponen_ids[:1]
        self.assertTrue(snapshot)
        snapshot.write({"bobot": 50.0, "aktif": True})

        summary = self.Validator.get_rps_summary(rps)
        component_total = next(
            group for group in summary if group["relation"] == "rps_component_total"
        )
        self.assertEqual(component_total["status"], "under")
        self.assertEqual(component_total["total"], 50.0)

        snapshot.write({"bobot": 100.0})
        allocation = snapshot.allocation_ids[:1]
        if allocation:
            allocation.write({"bobot_komponen_cpmk": 100.0})
        summary = self.Validator.get_rps_summary(rps)
        component_total = next(
            group for group in summary if group["relation"] == "rps_component_total"
        )
        self.assertEqual(component_total["status"], "complete")

    def test_sync_repairs_existing_component_allocation_snapshot_links(self):
        rps = self._create_rps()
        allocation = rps.bobot_komponen_cpmk_ids[:1]
        allocation.write(
            {"rps_komponen_id": False, "bobot_komponen_cpmk": 73.0}
        )
        allocation_count = len(rps.bobot_komponen_cpmk_ids)

        rps._sync_bobot_tables()

        self.assertEqual(len(rps.bobot_komponen_cpmk_ids), allocation_count)
        self.assertEqual(
            allocation.rps_komponen_id,
            rps.rps_komponen_ids.filtered(
                lambda snapshot: snapshot.komponen_id == allocation.komponen_penilaian
            ),
        )
        self.assertEqual(allocation.bobot_komponen_cpmk, 73.0)

    def test_draft_groups_allow_incomplete_weights_and_report_totals(self):
        rps = self._create_rps()
        summary = self.Validator.get_rps_summary(rps)
        self.assertEqual(
            {group["status"] for group in summary},
            {"under"},
        )
        self.assertEqual(rps.weight_status, "incomplete")
        rps.rps_komponen_ids.write({"bobot": 100.0})
        rps.rps_komponen_ids.mapped("allocation_ids").write(
            {"bobot_komponen_cpmk": 100.0}
        )
        self.assertTrue(
            all(
                group["status"] == "complete"
                for group in self.Validator.get_rps_summary(rps)
            )
        )
        self.assertEqual(rps.weight_status, "complete")

    def test_over_allocation_and_empty_groups_are_reported(self):
        course = self._create_course_with_cpmks(2, "OVER")
        rps = self._create_rps(course=course)
        snapshot = rps.rps_komponen_ids[:1]
        snapshot.write({"bobot": 100.0})
        snapshot.allocation_ids.write({"bobot_komponen_cpmk": 60.0})
        component_allocation = next(
            group
            for group in self.Validator.get_rps_summary(rps)
            if group["relation"] == "rps_component_cpmk"
        )
        self.assertEqual(component_allocation["status"], "over")
        self.assertEqual(component_allocation["total"], 120.0)

        empty_course = self.Matakuliah.create(
            {
                "name": "Mata Kuliah Kosong",
                "kode_mk": "MKK",
                "sks": 2,
                "semester": 2,
                "prodi_id": self.course.prodi_id.id,
            }
        )
        empty_rps = self.RPS.create({"matakuliah_id": empty_course.id})
        empty_group = next(
            group
            for group in self.Validator.get_rps_summary(empty_rps)
            if group["relation"] == "cpmk_mk"
        )
        self.assertEqual(empty_group["total"], 0.0)
        self.assertEqual(empty_group["status"], "under")

    def test_update_and_delete_recalculate_totals(self):
        course = self._create_course_with_cpmks(2, "SECOND")
        rps = self._create_rps(course=course)
        lines = rps.rps_komponen_ids[:1].allocation_ids.sorted("cpmk_id")
        lines.write({"bobot_komponen_cpmk": 50.0})
        result = next(
            group
            for group in self.Validator.get_rps_summary(rps)
            if group["relation"] == "rps_component_cpmk"
        )
        self.assertEqual(result["status"], "complete")
        lines[0].write({"bobot_komponen_cpmk": 40.0})
        result = next(
            group
            for group in self.Validator.get_rps_summary(rps)
            if group["relation"] == "rps_component_cpmk"
        )
        self.assertEqual(result["total"], 90.0)
        self.assertEqual(result["status"], "under")
        lines[1].unlink()
        result = next(
            group
            for group in self.Validator.get_rps_summary(rps)
            if group["relation"] == "rps_component_cpmk"
        )
        self.assertEqual(result["total"], 40.0)
