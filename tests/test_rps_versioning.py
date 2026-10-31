from odoo import Command
from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestErpObeRpsVersioning(TransactionCase):
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
        cls.Year = cls.env["erpobe.akademik.tahunajaran"]
        cls.Offer = cls.env["erpobe.akademik.penawaran"]
        cls.OfferLine = cls.env["erpobe.akademik.penawaran.line"]
        cls.CopyWizard = cls.env["erpobe.wizard.rps.copy"]

        faculty = cls.Faculty.create({"name": "Fakultas Versi", "kode": "FVS"})
        prodi = cls.Prodi.create(
            {"name": "Prodi Versi", "kode": "PVS", "fakultas_id": faculty.id}
        )
        cls.course = cls.Matakuliah.create(
            {
                "name": "Mata Kuliah Versi",
                "kode_mk": "MKV",
                "sks": 3,
                "semester": 1,
                "prodi_id": prodi.id,
            }
        )
        cpl = cls.CPL.create(
            {"name": "CPL Versi", "kode_cpl": "CPLV", "prodi_id": prodi.id}
        )
        cpmk = cls.CPMK.create(
            {"mk_id": cls.course.id, "kode_cpmk": "CPMKV", "name": "CPMK Versi"}
        )
        cls.env["erpobe.akademik.cpl.mk.cpmk"].create(
            {"cpl_id": cpl.id, "cpmk_id": cpmk.id}
        )
        cls.component = cls.Component.create(
            {"name": "Komponen Versi", "tipe": "kognitif"}
        )
        cls.old_year = cls.Year.create(
            {"tahun_ajaran": "2024/2025", "semester": "ganjil"}
        )
        cls.new_year = cls.Year.create(
            {"tahun_ajaran": "2025/2026", "semester": "ganjil"}
        )
        cls.old_offer = cls.Offer.create({"tahun_ajaran": cls.old_year.id})
        cls.new_offer = cls.Offer.create({"tahun_ajaran": cls.new_year.id})
        rombel = cls.env["erpobe.master.rombel"].create(
            {"name": "A", "angkatan": 2024, "prodi_id": prodi.id}
        )
        cls.old_line = cls.OfferLine.create(
            {
                "penawaran_id": cls.old_offer.id,
                "matakuliah_id": cls.course.id,
                "rombel_ids": [(6, 0, [rombel.id])],
            }
        )
        cls.new_line = cls.OfferLine.create(
            {
                "penawaran_id": cls.new_offer.id,
                "matakuliah_id": cls.course.id,
                "rombel_ids": [(6, 0, [rombel.id])],
            }
        )

    def _final_rps(self):
        rps = self.old_line.action_create_rps()
        source = self.RPS.browse(rps["res_id"])
        source.write({"komponen_ids": [Command.set([self.component.id])]})
        source.bobot_cpmk_cpl_ids.write({"bobot_cpmk_cpl": 100.0})
        source.bobot_cpmk_mk_ids.write({"bobot_cpmk_mk": 100.0})
        source.bobot_komponen_cpmk_ids.write({"bobot_komponen_cpmk": 100.0})
        source.action_mark_for_review()
        source.action_finalize()
        return source

    def test_new_offer_requires_a_new_rps_review(self):
        self.assertEqual(self.new_line.rps_status, "missing")
        created = self.new_line.action_create_rps()
        rps = self.RPS.browse(created["res_id"])
        self.assertEqual(rps.status, "draft")
        self.assertEqual(rps.tahun_ajaran_id, self.new_year)
        self.assertEqual(self.new_line.rps_status, "draft")

    def test_copy_is_independent_and_final_source_is_read_only(self):
        source = self._final_rps()
        with self.assertRaises(UserError):
            source.write({"media_software": "ubah arsip"})
        with self.assertRaises(UserError):
            source.bobot_cpmk_mk_ids.write({"bobot_cpmk_mk": 80.0})

        wizard = self.CopyWizard.create(
            {
                "penawaran_line_id": self.new_line.id,
                "source_rps_id": source.id,
            }
        )
        action = wizard.action_copy()
        copied = self.RPS.browse(action["res_id"])
        self.assertEqual(copied.status, "review")
        self.assertEqual(copied.version, 1)
        self.assertEqual(copied.source_rps_id, source)
        self.assertEqual(copied.penawaran_line_id, self.new_line)
        self.assertEqual(copied.tahun_ajaran_id, self.new_year)
        self.assertNotEqual(
            copied.bobot_cpmk_mk_ids.ids, source.bobot_cpmk_mk_ids.ids
        )

        copied.bobot_cpmk_mk_ids.write({"bobot_cpmk_mk": 90.0})
        self.assertEqual(source.bobot_cpmk_mk_ids.bobot_cpmk_mk, 100.0)
        self.assertEqual(copied.status, "draft")

    def test_finalization_requires_review_and_complete_weights(self):
        action = self.new_line.action_create_rps()
        rps = self.RPS.browse(action["res_id"])
        with self.assertRaises(UserError):
            rps.action_finalize()
        rps.action_mark_for_review()
        with self.assertRaises(UserError):
            rps.action_finalize()

    def test_bulk_copy_requires_confirmation_and_previews_sources(self):
        source = self._final_rps()
        wizard = self.env["erpobe.wizard.rps.bulk.copy"].create(
            {"penawaran_id": self.new_offer.id}
        )
        self.assertEqual(wizard.line_ids, self.new_line)
        self.assertIn(source, wizard.source_rps_ids)
        with self.assertRaises(UserError):
            wizard.action_copy()

        wizard.confirm_copy = True
        wizard.action_copy()
        self.assertEqual(self.new_line.rps_status, "review")
        self.assertEqual(self.new_line.latest_rps_id.source_rps_id, source)
