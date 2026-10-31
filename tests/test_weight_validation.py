from odoo import Command
from odoo.tests import TransactionCase, tagged

from ..models.weight_validation import _weight_status


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

    def _create_rps(self, components=None):
        rps = self.RPS.create(
            {
                "matakuliah_id": self.course.id,
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

    def test_draft_groups_allow_incomplete_weights_and_report_totals(self):
        rps = self._create_rps()
        summary = self.Validator.get_rps_summary(rps)
        self.assertEqual(
            {group["status"] for group in summary},
            {"under"},
        )
        self.assertEqual(rps.weight_status, "incomplete")
        self.assertEqual(
            self.Validator.get_problem_items(rps.prodi_id.id)[0]["difference"],
            100.0,
        )

        rps.bobot_cpmk_cpl_ids.write({"bobot_cpmk_cpl": 100.0})
        rps.bobot_cpmk_mk_ids.write({"bobot_cpmk_mk": 100.0})
        rps.bobot_komponen_cpmk_ids.write({"bobot_komponen_cpmk": 100.0})
        self.assertTrue(
            all(
                group["status"] == "complete"
                for group in self.Validator.get_rps_summary(rps)
            )
        )
        self.assertEqual(rps.weight_status, "complete")

    def test_over_allocation_and_empty_groups_are_reported(self):
        second_cpl = self.CPL.create(
            {
                "name": "CPL Bobot Kedua",
                "kode_cpl": "CPL-B2",
                "prodi_id": self.course.prodi_id.id,
            }
        )
        self.env["erpobe.akademik.cpl.mk.cpmk"].create(
            {"cpl_id": second_cpl.id, "cpmk_id": self.cpmk.id}
        )
        rps = self._create_rps()
        rps.bobot_cpmk_cpl_ids.write({"bobot_cpmk_cpl": 60.0})
        cpmk_to_cpl = next(
            group
            for group in self.Validator.get_rps_summary(rps)
            if group["relation"] == "cpmk_cpl"
        )
        self.assertEqual(cpmk_to_cpl["status"], "over")
        self.assertEqual(cpmk_to_cpl["total"], 120.0)

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
        second_component = self.Component.create(
            {"name": "Komponen Bobot Kedua", "tipe": "partisipatif"}
        )
        rps = self._create_rps(self.component | second_component)
        lines = rps.bobot_komponen_cpmk_ids
        lines.write({"bobot_komponen_cpmk": 50.0})
        result = next(
            group
            for group in self.Validator.get_rps_summary(rps)
            if group["relation"] == "komponen_cpmk"
        )
        self.assertEqual(result["status"], "complete")
        lines[0].write({"bobot_komponen_cpmk": 40.0})
        result = next(
            group
            for group in self.Validator.get_rps_summary(rps)
            if group["relation"] == "komponen_cpmk"
        )
        self.assertEqual(result["total"], 90.0)
        self.assertEqual(result["status"], "under")
        lines[1].unlink()
        result = next(
            group
            for group in self.Validator.get_rps_summary(rps)
            if group["relation"] == "komponen_cpmk"
        )
        self.assertEqual(result["total"], 40.0)
