from odoo import models, fields, api, Command

class ErpObeAkademikRps(models.Model):
    _name = "erpobe.akademik.rps"
    _description = "Rencana Pembelajaran Semester (RPS)"
    _rec_name = "matakuliah_id"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    # === 1. Header & Identitas MK ===
    matakuliah_id = fields.Many2one(
        "erpobe.master.matakuliah", string="Mata Kuliah", required=True, tracking=True
    )

    # Field Related Wajib Store=True untuk Report/Search
    kode_mk = fields.Char(related="matakuliah_id.kode_mk", store=True)
    sks = fields.Integer(related="matakuliah_id.sks", store=True)
    semester = fields.Integer(related="matakuliah_id.semester", store=True)
    deskripsi_mk = fields.Text(
        related="matakuliah_id.deskripsi_mk",
        string="Deskripsi Mata Kuliah",
        readonly=False,
    )

    # Related Info (Sesuai kode asli Anda)
    mk_prasyarat_ids = fields.Many2many(
        related="matakuliah_id.mk_prasyarat_ids", readonly=True
    )
    tipe_mk = fields.Selection(related="matakuliah_id.tipe_mk", store=True)
    jenis_mk = fields.Selection(related="matakuliah_id.jenis_mk", store=True)
    bahasa = fields.Selection(related="matakuliah_id.bahasa", store=True)
    koordinator_id = fields.Many2one(related="matakuliah_id.koordinator_id", store=True)
    tim_pengampu_ids = fields.Many2many(
        related="matakuliah_id.tim_pengampu_ids", readonly=True
    )
    media_software = fields.Char(string="Media software")
    media_hardware = fields.Char(string="Media Hardware")

    # === 2. Komponen & CPMK ===
    # Komponen Penilaian yang dipakai di RPS ini
    komponen_ids = fields.Many2many(
        "erpobe.akademik.komponen",
        string="Komponen Penilaian",
        help="Pilih komponen penilaian yang digunakan dalam semester ini.",
    )

    cpmk_ids = fields.Many2many(
        "erpobe.akademik.cpmk",
        string="CPMK yang Diajarkan",
        compute="_compute_cpmk_ids",
        store=True,
        readonly=False,
        precompute=True, 
    )

    @api.depends("matakuliah_id")
    def _compute_cpmk_ids(self):
        for rec in self:
            if rec.matakuliah_id:
                # Mengambil semua CPMK master milik MK ini
                cpmks = self.env["erpobe.akademik.cpmk"].search(
                    [("mk_id", "=", rec.matakuliah_id.id)]
                )
                rec.cpmk_ids = [Command.set(cpmks.ids)]
            else:
                rec.cpmk_ids = [Command.clear()]

    cpl_ids = fields.Many2many(
        "erpobe.akademik.cpl",
        string="CPL Terkait",
        compute="_compute_cpl_ids",
        store=True,
        readonly=False
    )

    @api.depends("cpmk_ids", "cpmk_ids.cpl_mapping_ids")
    def _compute_cpl_ids(self):
        for rec in self:
            rec.cpl_ids = rec.cpmk_ids.mapped("cpl_mapping_ids.cpl_id")

    bobot_cpmk_mk_ids = fields.One2many(
        "erpobe.bobot.cpmk.mk", "rps_id", string="Bobot CPMK -> MK"
    )
    bobot_cpmk_cpl_ids = fields.One2many(
        "erpobe.bobot.cpmk.cpl", "rps_id", string="Bobot CPMK -> CPL"
    )
    bobot_komponen_cpmk_ids = fields.One2many(
        "erpobe.bobot.komponen.cpmk", "rps_id", string="Bobot Komponen -> CPMK"
    )

    # === 4. Detail Aktivitas ===
    kegiatan_perkuliahan_ids = fields.One2many(
        "erpobe.akademik.kegiatan.perkuliahan", "rps_id", string="Kegiatan Perkuliahan"
    )
    rubrik_penilaian_ids = fields.One2many(
        "erpobe.akademik.rubrik.penilaian", "rps_id", string="Rubrik Penilaian"
    )

    # === 5. Logic Sinkronisasi Aman ===
    def _sync_bobot_tables(self):
        """
        Sinkronisasi tabel bobot tanpa menghapus nilai yang sudah diinput user.
        Hanya menambah baris baru atau menghapus baris yang validitasnya hilang.
        """
        for rps in self:
            if not rps.cpmk_ids:
                continue

            # --- A. Sync Bobot CPMK -> MK ---
            existing_cpmk_mk = rps.bobot_cpmk_mk_ids.mapped("cpmk_id")
            new_cpmk = rps.cpmk_ids - existing_cpmk_mk
            obsolete_cpmk = existing_cpmk_mk - rps.cpmk_ids

            cmds_mk = []
            if new_cpmk:
                cmds_mk.extend(
                    [
                        Command.create({"cpmk_id": c.id, "bobot_cpmk_mk": 0.0})
                        for c in new_cpmk
                    ]
                )
            if obsolete_cpmk:
                to_remove = rps.bobot_cpmk_mk_ids.filtered(
                    lambda l: l.cpmk_id in obsolete_cpmk
                )
                cmds_mk.extend([Command.delete(l.id) for l in to_remove])
            if cmds_mk:
                rps.write({"bobot_cpmk_mk_ids": cmds_mk})

            # --- B. Sync Bobot CPMK -> CPL ---
            # Cari mapping valid: {(cpmk_id, cpl_id)} berdasarkan CPMK terpilih
            valid_mappings = set()
            for cpmk in rps.cpmk_ids:
                for mapping in (
                    cpmk.cpl_mapping_ids
                ):  # Asumsi ada field One2many di CPMK ke mapping
                    valid_mappings.add((cpmk.id, mapping.cpl_id.id))

            existing_mappings = {
                (l.cpmk_id.id, l.cpl_id.id) for l in rps.bobot_cpmk_cpl_ids
            }

            cmds_cpl = []
            # Add New
            for cpmk_id, cpl_id in valid_mappings:
                if (cpmk_id, cpl_id) not in existing_mappings:
                    cmds_cpl.append(
                        Command.create(
                            {
                                "cpmk_id": cpmk_id,
                                "cpl_id": cpl_id,
                                "bobot_cpmk_cpl": 0.0,
                            }
                        )
                    )
            # Remove Obsolete
            for line in rps.bobot_cpmk_cpl_ids:
                if (line.cpmk_id.id, line.cpl_id.id) not in valid_mappings:
                    cmds_cpl.append(Command.delete(line.id))

            if cmds_cpl:
                rps.write({"bobot_cpmk_cpl_ids": cmds_cpl})

            # --- C. Sync Bobot Komponen -> CPMK ---
            # Cross Product: CPMK Terpilih x Komponen Terpilih (komponen_ids)
            if not rps.komponen_ids:
                continue

            valid_komp_cpmk = set()
            for cpmk in rps.cpmk_ids:
                for komp in rps.komponen_ids:
                    valid_komp_cpmk.add((cpmk.id, komp.id))

            existing_komp_cpmk = {
                (l.cpmk_id.id, l.komponen_penilaian.id)
                for l in rps.bobot_komponen_cpmk_ids
            }

            cmds_komp = []
            # Add New
            for cpmk_id, komp_id in valid_komp_cpmk:
                if (cpmk_id, komp_id) not in existing_komp_cpmk:
                    cmds_komp.append(
                        Command.create(
                            {
                                "cpmk_id": cpmk_id,
                                "komponen_penilaian": komp_id,
                                "bobot_komponen_cpmk": 0.0,
                            }
                        )
                    )
            # Remove Obsolete
            for line in rps.bobot_komponen_cpmk_ids:
                if (line.cpmk_id.id, line.komponen_penilaian.id) not in valid_komp_cpmk:
                    cmds_komp.append(Command.delete(line.id))

            if cmds_komp:
                rps.write({"bobot_komponen_cpmk_ids": cmds_komp})

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._sync_bobot_tables()
        return records

    def write(self, vals):
        res = super().write(vals)
        # Trigger sync jika ada perubahan pada MK, CPMK, atau Komponen
        if any(f in vals for f in ["matakuliah_id", "cpmk_ids", "komponen_ids"]):
            self._sync_bobot_tables()
        return res


class ErpObeAkademikKegiatanPerkuliahan(models.Model):
    _name = "erpobe.akademik.kegiatan.perkuliahan"
    _description = "Kegiatan Perkuliahan"
    _order = "minggu asc"

    rps_id = fields.Many2one("erpobe.akademik.rps", required=True, ondelete="cascade")
    minggu = fields.Integer(string="Minggu Ke", required=True)

    cpmk_id = fields.Many2one(
        "erpobe.akademik.cpmk",
        string="CPMK",
        required=True,
        domain="[('mk_id', '=', parent.matakuliah_id)]",
    )

    bahan_kajian = fields.Text(required=True)
    metode_pembelajaran_id = fields.Many2one(
        "erpobe.akademik.metode.pembelajaran", required=True
    )

    pengalaman_belajar = fields.Text()
    indikator_penilaian = fields.Text()
    estimasi_waktu = fields.Integer(string="Waktu (Menit)", default=170)

    # FIX: Definisikan 'relation' secara manual agar nama tabel pendek
    referensi_ids = fields.Many2many(
        comodel_name="erpobe.akademik.referensi",
        relation="erpobe_kegiatan_ref_rel",
        column1="kegiatan_id",
        column2="referensi_id",
        string="Referensi",
    )
    teknik_penilaian = fields.Char(
        string="teknik penilaian"
    )


class ErpObeAkademikMetodePembelajaran(models.Model):
    _name = "erpobe.akademik.metode.pembelajaran"
    _description = "Master Metode Pembelajaran"
    name = fields.Char(string="Nama Metode", required=True)
    kode = fields.Char(string="Kode", size=5)
    active = fields.Boolean(default=True)

    _uniq_name_constraint = models.Constraint('unique(name)', 'Nama metode sudah ada')


class ErpObeAkademikReferensi(models.Model):
    _name = "erpobe.akademik.referensi"  # Fix Typo
    _description = "Master Referensi / Pustaka"
    _rec_name = "judul"

    kode = fields.Char(
        string="Kode Pustaka"
    )  # Integer tidak fleksibel untuk ISBN/Kode Unik
    judul = fields.Char(required=True)
    penulis = fields.Char()
    tahun = fields.Char(size=4)
    link = fields.Char(string="URL")
    jenis = fields.Selection(
        [("utama", "Utama"), ("pendukung", "Pendukung")], default="pendukung"
    )


class ErpObeAkademikRubrikPenilaian(models.Model):
    _name = "erpobe.akademik.rubrik.penilaian"
    _description = "Item Rubrik (Baris)"
    _order = "sequence, id"

    rps_id = fields.Many2one("erpobe.akademik.rps", required=True, ondelete="cascade")
    sequence = fields.Integer(default=10)

    materi_soal = fields.Text(required=True)
    komponen_id = fields.Many2one("erpobe.akademik.komponen", required=True)
    cpmk_id = fields.Many2one("erpobe.akademik.cpmk", required=True)
    bobot = fields.Float(string="Bobot (%)", required=True)

    # === FIXED RELATION ===
    kriteria_ids = fields.One2many(
        "erpobe.akademik.kriteria", "rubrik_id", string="Detail Kriteria"
    )
    def action_open_kriteria(self):
        """ Membuka form view rubrik untuk mengedit kriteria secara detail """
        self.ensure_one()
        return {
            'name': 'Detail Kriteria Penilaian',
            'type': 'ir.actions.act_window',
            'res_model': 'erpobe.akademik.rubrik.penilaian',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }
    
class ErpObeAkademikKriteria(models.Model):
    _name = "erpobe.akademik.kriteria"
    _description = "Kriteria Penilaian RPS"

    # === FIXED RELATION ===
    rubrik_id = fields.Many2one(
        "erpobe.akademik.rubrik.penilaian", required=True, ondelete="cascade"
    )

    # Relasi ke Master Grade Global
    grade_id = fields.Many2one("erpobe.master.grade", string="Grade", required=True)

    # Data Readonly dari Global
    nilai_min = fields.Float(related="grade_id.nilai_min", readonly=True)
    nilai_max = fields.Float(related="grade_id.nilai_max", readonly=True)

    # Data Spesifik
    deskripsi = fields.Text(string="Deskripsi Spesifik", required=True)

    _uniq_grade_item_constraint = models.Constraint('unique(rubrik_id, grade_id)', 'Grade duplikat dalam satu item soal')

    @api.onchange("grade_id")
    def _onchange_grade(self):
        if self.grade_id and not self.deskripsi:
            self.deskripsi = self.grade_id.keterangan_standar
