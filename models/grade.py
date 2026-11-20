from odoo import models, fields, api, Command, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class ErpObeInputNilai(models.Model):
    _name = "erpobe.input.nilai"
    _description = "Input Nilai Mata Kuliah"
    _rec_name = "penawaran_line_id"

    penawaran_id = fields.Many2one("erpobe.akademik.penawaran", required=True)
    penawaran_line_id = fields.Many2one(
        "erpobe.akademik.penawaran.line",
        required=True,
        domain="[('penawaran_id', '=', penawaran_id)]",
    )

    # Informasi UI
    tahun_ajaran = fields.Many2one(related="penawaran_id.tahun_ajaran", store=True)
    matakuliah_id = fields.Many2one(
        related="penawaran_line_id.matakuliah_id", store=True
    )

    grade_komponen_ids = fields.One2many(
        "erpobe.grade.komponen", "input_nilai_id", string="Daftar Nilai Mahasiswa"
    )

    _uniq_input_penawaran_constraint = models.Constraint('unique(penawaran_line_id)', 'Input nilai untuk kelas ini sudah ada.')

    prodi_id = fields.Many2one(
        related="penawaran_line_id.prodi_id", store=True, readonly=True, index=True
    )

    fakultas_id = fields.Many2one(
        related="prodi_id.fakultas_id", store=True, readonly=True, index=True
    )

    def action_calculate_grades_and_khs(self, krs_lines=None):
        """
        Orchestrator: Memastikan record Grade tersedia & MEMAKSA hitung ulang (Recompute).
        """
        GradeCpmk = self.env["erpobe.grade.cpmk"]
        GradeMk = self.env["erpobe.grade.mk"]
        GradeCpl = self.env["erpobe.grade.cpl"]
        BobotCpmkCpl = self.env["erpobe.bobot.cpmk.cpl"]
        Rps = self.env["erpobe.akademik.rps"]

        # 1. Fallback Data KRS
        if not krs_lines:
            krs_lines = self.grade_komponen_ids.mapped("krs_line_id")

        if not krs_lines:
            raise ValidationError(
                _("Tidak ada data mahasiswa (KRS) di kelas ini untuk dihitung.")
            )

        # 2. Validasi RPS: gunakan RPS yang melekat pada kelas, bukan RPS terbaru lintas kelas.
        current_mk_id = self.penawaran_line_id.matakuliah_id.id
        rps = self.penawaran_line_id.latest_rps_id
        if rps and rps.status == "final":
            rps = rps
        else:
            rps = Rps.search(
                [
                    ("penawaran_line_id", "=", self.penawaran_line_id.id),
                    ("status", "=", "final"),
                ],
                order="version desc, id desc",
                limit=1,
            )

        if not rps:
            raise ValidationError(
                _(
                    "Gagal Menghitung Nilai: RPS (Rencana Pembelajaran Semester) untuk mata kuliah '%s' belum dibuat."
                )
                % self.penawaran_line_id.matakuliah_id.name
            )

        # 3. Preparasi Data
        mahasiswa_to_update = set()
        cpmk_list = rps.cpmk_ids
        bobot_cpl_lines = BobotCpmkCpl.search([("cpmk_id", "in", cpmk_list.ids)])
        relevant_cpls = bobot_cpl_lines.mapped("cpl_id")

        # Container untuk record yang perlu di-recompute
        recompute_cpmk = self.env["erpobe.grade.cpmk"]
        recompute_mk = self.env["erpobe.grade.mk"]
        recompute_cpl = self.env["erpobe.grade.cpl"]

        # 4. Loop & Create/Collect Grade Records
        for krs in krs_lines:
            mahasiswa = krs.mahasiswa_id
            mahasiswa_to_update.add(mahasiswa.id)

            # a. Ensure Grade CPMK
            for cpmk in cpmk_list:
                g_cpmk = GradeCpmk.search(
                    [
                        ("mahasiswa_id", "=", mahasiswa.id),
                        ("cpmk_id", "=", cpmk.id),
                        ("krs_line_id", "=", krs.id),
                    ],
                    limit=1,
                )
                if not g_cpmk:
                    g_cpmk = GradeCpmk.create(
                        {
                            "mahasiswa_id": mahasiswa.id,
                            "cpmk_id": cpmk.id,
                            "krs_line_id": krs.id,
                            "rps_id": rps.id,
                        }
                    )
                else:
                    g_cpmk.write({"krs_line_id": krs.id, "rps_id": rps.id})
                recompute_cpmk += g_cpmk  # Kumpulkan record

            # b. Ensure Grade MK
            g_mk = GradeMk.search(
                [
                    ("mahasiswa_id", "=", mahasiswa.id),
                    ("mk_id", "=", current_mk_id),
                    ("krs_line_id", "=", krs.id),
                ],
                limit=1,
            )
            if not g_mk:
                g_mk = GradeMk.create(
                    {
                        "mahasiswa_id": mahasiswa.id,
                        "mk_id": current_mk_id,
                        "krs_line_id": krs.id,
                        "rps_id": rps.id,
                    }
                )
            else:
                g_mk.write({"krs_line_id": krs.id, "rps_id": rps.id})
            recompute_mk += g_mk  # Kumpulkan record

            # c. Ensure Grade CPL
            for cpl in relevant_cpls:
                g_cpl = GradeCpl.search(
                    [
                        ("mahasiswa_id", "=", mahasiswa.id),
                        ("cpl_id", "=", cpl.id),
                        ("krs_line_id", "=", krs.id),
                    ],
                    limit=1,
                )
                if not g_cpl:
                    g_cpl = GradeCpl.create(
                        {
                            "mahasiswa_id": mahasiswa.id,
                            "cpl_id": cpl.id,
                            "krs_line_id": krs.id,
                            "rps_id": rps.id,
                        }
                    )
                else:
                    g_cpl.write({"krs_line_id": krs.id, "rps_id": rps.id})
                recompute_cpl += g_cpl  # Kumpulkan record

        # === FORCE RECOMPUTE (SOLUSI UTAMA) ===
        # Memaksa Odoo menghitung ulang nilai berdasarkan input komponen terbaru
        _logger.info("Forcing recompute for Grades...")
        if recompute_cpmk:
            recompute_cpmk._compute_nilai_cpmk()
        if recompute_mk:
            recompute_mk._compute_nilai_mk()
        if recompute_cpl:
            recompute_cpl._compute_nilai_cpl()

        # 5. Trigger Update Report KHS
        if mahasiswa_to_update:
            mhs_ids_list = list(mahasiswa_to_update)
            if "erpobe.report.khs" in self.env:
                self.env["erpobe.report.khs"].sudo().action_generate_khs(mhs_ids_list)
            else:
                _logger.warning("Modul erpobe.report.khs belum terinstall.")

    @api.constrains("penawaran_id", "penawaran_line_id")
    def _check_input_faculty(self):
        for record in self:
            if (
                record.penawaran_line_id
                and record.penawaran_line_id.penawaran_id != record.penawaran_id
            ):
                raise ValidationError(
                    "Baris nilai harus berasal dari penawaran yang dipilih."
                )

    @api.onchange("penawaran_line_id")
    def _onchange_generate_students(self):
        """
        Smart Onchange:
        1. Ambil mahasiswa dari KRS.
        2. Cek apakah Nilai Komponen SUDAH ADA di database?
           - Jika YA: Tampilkan nilai lamanya (jangan di-nol-kan).
           - Jika TIDAK: Baru set 0.0.
        """
        if not self.penawaran_line_id:
            self.grade_komponen_ids = [Command.clear()]
            return

        Komponen = self.env["erpobe.akademik.komponen"]
        active_components = Komponen.search([("aktif", "=", True)])
        rps = self.penawaran_line_id.latest_rps_id

        if not active_components:
            return

        KrsLine = self.env["erpobe.akademik.krs.line"]
        krs_lines = KrsLine.search(
            [("penawaran_line_id", "=", self.penawaran_line_id.id)]
        )

        # Load Model Grade Komponen untuk cek data lama
        GradeKomponen = self.env["erpobe.grade.komponen"]

        new_lines = [Command.clear()]
        for krs in krs_lines:
            for comp in active_components:
                snapshot = (
                    rps.rps_komponen_ids.filtered(
                        lambda item: item.komponen_id == comp
                    )[:1]
                    if rps else self.env["erpobe.akademik.rps.komponen"]
                )
                # Cek database: Apakah mahasiswa ini sudah punya nilai komponen ini?
                existing_grade = GradeKomponen.search(
                    [
                        ("krs_line_id", "=", krs.id),
                        ("komponen_id", "=", comp.id),
                        ("rps_id", "=", rps.id if rps else False),
                    ],
                    limit=1,
                )

                if existing_grade:
                    # KASUS 1: Data Lama Ada -> Load nilainya
                    # Kita tidak pakai Command.link() karena ini One2many dengan parent berbeda bisa tricky,
                    # tapi karena ini form input, kita tampilkan saja nilainya.
                    # Jika user save, dia akan update record tersebut atau membuat baru (tergantung constraint).
                    # Dengan struktur InputNilai yang 'unique per kelas', ini aman.
                    val_nilai = existing_grade.nilai
                else:
                    # KASUS 2: Data Baru -> 0.0
                    val_nilai = 0.0

                new_lines.append(
                    Command.create(
                        {
                            "krs_line_id": krs.id,
                            "komponen_id": comp.id,
                            "nilai": val_nilai,  # Gunakan nilai cerdas
                            "rps_id": rps.id if rps else False,
                            "rps_komponen_id": snapshot.id if snapshot else False,
                        }
                    )
                )

        self.grade_komponen_ids = new_lines

class ErpObeGradeKomponen(models.Model):
    _name = "erpobe.grade.komponen"
    _description = "Nilai Komponen Mahasiswa"

    # Header Info
    input_nilai_id = fields.Many2one("erpobe.input.nilai", ondelete="cascade")

    # Store True pada related fields penting untuk performa pencarian
    krs_line_id = fields.Many2one(
        "erpobe.akademik.krs.line", required=True, ondelete="restrict", index=True
    )
    mahasiswa_id = fields.Many2one(
        related="krs_line_id.mahasiswa_id", store=True, index=True
    )

    # Core Data
    komponen_id = fields.Many2one("erpobe.akademik.komponen", required=True, index=True)
    nilai = fields.Float(string="Nilai Angka", default=0.0, digits=(16, 2))
    rps_id = fields.Many2one(
        "erpobe.akademik.rps", string="RPS Penilaian", ondelete="restrict", index=True
    )
    rps_komponen_id = fields.Many2one(
        "erpobe.akademik.rps.komponen",
        string="Komponen RPS",
        ondelete="restrict",
        index=True,
    )
    origin = fields.Selection(
        [
            ("legacy", "Legacy"),
            ("actual", "Nilai Aktual"),
            ("simulated", "Nilai Simulasi"),
        ],
        default="actual",
        required=True,
        index=True,
    )
    is_graded = fields.Boolean(
        string="Sudah Dinilai", default=True, index=True
    )

    _uniq_nilai_komp_constraint = models.Constraint('unique(krs_line_id, komponen_id)', 'Nilai komponen duplikat untuk mahasiswa ini.')
    _nilai_range_constraint = models.Constraint(
        "CHECK(nilai >= 0 AND nilai <= 100)",
        "Nilai komponen harus berada pada rentang 0–100.",
    )

    prodi_id = fields.Many2one(
        related="mahasiswa_id.prodi_id", store=True, readonly=True, index=True
    )

    fakultas_id = fields.Many2one(
        related="prodi_id.fakultas_id", store=True, readonly=True, index=True
    )

    def write(self, vals):
        if "nilai" in vals:
            Audit = self.env["erpobe.grade.komponen.audit"].sudo()
            for grade in self:
                old_value = grade.nilai
                new_value = float(vals["nilai"])
                if old_value != new_value:
                    Audit.create({
                        "grade_id": grade.id,
                        "krs_line_id": grade.krs_line_id.id,
                        "komponen_id": grade.komponen_id.id,
                        "mahasiswa_id": grade.mahasiswa_id.id,
                        "penawaran_line_id": grade.krs_line_id.penawaran_line_id.id,
                        "user_id": self.env.user.id,
                        "old_value": old_value,
                        "new_value": new_value,
                        "reason": vals.get("audit_reason", ""),
                    })
        vals.pop("audit_reason", None)
        return super().write(vals)

    @api.model_create_multi
    def create(self, vals_list):
        vals_list = [dict(values) for values in vals_list]
        reasons = [values.pop("audit_reason", "") for values in vals_list]
        records = super().create(vals_list)
        Audit = self.env["erpobe.grade.komponen.audit"].sudo()
        for grade, reason in zip(records, reasons):
            if grade.nilai:
                Audit.create({
                    "grade_id": grade.id,
                    "krs_line_id": grade.krs_line_id.id,
                    "komponen_id": grade.komponen_id.id,
                    "mahasiswa_id": grade.mahasiswa_id.id,
                    "penawaran_line_id": grade.krs_line_id.penawaran_line_id.id,
                    "user_id": self.env.user.id,
                    "old_value": 0.0,
                    "new_value": grade.nilai,
                    "reason": reason or "Initial grade entry",
                })
        return records


class ErpObeGradeKomponenAudit(models.Model):
    _name = "erpobe.grade.komponen.audit"
    _description = "Riwayat Perubahan Nilai Komponen"
    _order = "create_date desc, id desc"

    grade_id = fields.Many2one(
        "erpobe.grade.komponen", required=True, ondelete="restrict", readonly=True
    )
    krs_line_id = fields.Many2one(
        "erpobe.akademik.krs.line", required=True, ondelete="restrict", readonly=True
    )
    penawaran_line_id = fields.Many2one(
        "erpobe.akademik.penawaran.line", required=True, ondelete="restrict", readonly=True
    )
    komponen_id = fields.Many2one(
        "erpobe.akademik.komponen", required=True, ondelete="restrict", readonly=True
    )
    mahasiswa_id = fields.Many2one(
        "erpobe.master.mahasiswa", required=True, ondelete="restrict", readonly=True
    )
    user_id = fields.Many2one("res.users", required=True, readonly=True)
    old_value = fields.Float(digits=(16, 2), readonly=True)
    new_value = fields.Float(digits=(16, 2), readonly=True)
    reason = fields.Char(readonly=True)

    def write(self, vals):
        raise ValidationError("Riwayat penilaian bersifat immutable.")

    def unlink(self):
        raise ValidationError("Riwayat penilaian tidak boleh dihapus.")
