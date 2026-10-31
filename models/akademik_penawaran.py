from odoo import models, fields, api, Command
from odoo.exceptions import ValidationError


class ErpObeAkademikPenawaran(models.Model):
    _name = "erpobe.akademik.penawaran"
    _description = "Penawaran Mata Kuliah"
    _rec_name = "name"
    _order = "id desc"

    name = fields.Char(
        string="Nama Penawaran",
        compute="_compute_name",
        store=True,
    )
    tahun_ajaran = fields.Many2one(
        "erpobe.akademik.tahunajaran",
        string="Tahun Ajaran",
        required=True,
        default=lambda self: self._default_tahun_ajaran(),
    )
    prodi_id = fields.Many2one(
        "erpobe.master.prodi",
        string="Program Studi",
        index=True,
        default=lambda self: self.env.context.get("default_prodi_id"),
    )
    semester_akademik = fields.Selection(
        related="tahun_ajaran.semester",
        store=True,
        readonly=True,
    )
    rombel_ids = fields.Many2many(
        "erpobe.master.rombel",
        "erpobe_penawaran_rombel_rel",
        "penawaran_id",
        "rombel_id",
        string="Rombel Tersedia",
    )
    line_ids = fields.One2many(
        "erpobe.akademik.penawaran.line",
        "penawaran_id",
        string="Detail Penawaran",
    )
    rps_pending_count = fields.Integer(
        string="RPS Belum Final", compute="_compute_rps_pending_count"
    )
    filter_angkatan_ids = fields.Many2many(
        "erpobe.master.angkatan.view",
        string="Filter Angkatan",
    )
    temp_matakuliah_ids = fields.Many2many(
        "erpobe.master.matakuliah",
        string="Ambil Mata Kuliah",
        store=False,
    )

    def _default_tahun_ajaran(self):
        return self.env["erpobe.akademik.tahunajaran"].search(
            [("aktif", "=", True)], order="id desc", limit=1
        )

    @api.depends("tahun_ajaran", "semester_akademik", "rombel_ids")
    def _compute_name(self):
        for rec in self:
            if not rec.tahun_ajaran:
                rec.name = "Penawaran Baru"
                continue

            ta = rec.tahun_ajaran.tahun_ajaran
            smt = (rec.semester_akademik or "").capitalize()
            angkatan_list = sorted(set(rec.rombel_ids.mapped("angkatan")))

            suffix = ""
            if angkatan_list:
                angkatan_str = ", ".join(str(a) for a in angkatan_list)
                suffix = f" - Angkatan {angkatan_str}"

            rec.name = f"Penawaran {ta} ({smt}){suffix}"

    @api.depends("line_ids.rps_status")
    def _compute_rps_pending_count(self):
        for record in self:
            record.rps_pending_count = len(
                record.line_ids.filtered(lambda line: line.rps_status != "final")
            )

    def action_open_bulk_rps_copy(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Salin RPS dari Tahun Sebelumnya",
            "res_model": "erpobe.wizard.rps.bulk.copy",
            "view_mode": "form",
            "target": "new",
            "context": {"default_penawaran_id": self.id},
        }

    @api.constrains("prodi_id", "line_ids")
    def _check_offer_prodi(self):
        for offer in self:
            if offer.prodi_id and any(
                line.prodi_id != offer.prodi_id for line in offer.line_ids
            ):
                raise ValidationError(
                    "Semua mata kuliah dalam penawaran harus berasal dari prodi yang sama."
                )

    @api.onchange("filter_angkatan_ids")
    def _onchange_filter_angkatan_ids(self):
        selected_years = self.filter_angkatan_ids.mapped("angkatan")
        if not selected_years:
            # Optional: Clear rombel if filter cleared
            # self.rombel_ids = [Command.clear()]
            return

        rombels = self.env["erpobe.master.rombel"].search(
            [("angkatan", "in", selected_years)]
        )
        self.rombel_ids = [Command.set(rombels.ids)]

    @api.onchange("temp_matakuliah_ids")
    def _onchange_temp_matakuliah_ids(self):
        if not self.temp_matakuliah_ids:
            return

        if not self.rombel_ids:
            self.temp_matakuliah_ids = [Command.clear()]
            return {
                "warning": {
                    "title": "Validasi",
                    "message": "Mohon pilih Rombel di Header terlebih dahulu.",
                }
            }

        header_rombel_ids = self.rombel_ids.ids
        existing_mks = self.line_ids.mapped("matakuliah_id.id")
        new_lines = []

        for mk in self.temp_matakuliah_ids:
            if mk.id in existing_mks:
                continue
            new_lines.append(
                Command.create(
                    {
                        "matakuliah_id": mk.id,
                        "rombel_ids": [Command.set(header_rombel_ids)],
                    }
                )
            )

        if new_lines:
            self.line_ids = new_lines

        self.temp_matakuliah_ids = [Command.clear()]

    def _sync_master_data(self):
        """Update relasi M2M di Master Rombel dan Master MK"""
        for penawaran in self:
            for line in penawaran.line_ids:
                if not line.matakuliah_id or not line.rombel_ids:
                    continue

                # Link MK ke semua Rombel yang ada di line ini
                line.rombel_ids.write(
                    {"matakuliah_ids": [Command.link(line.matakuliah_id.id)]}
                )

                # Link Rombel ke Master MK
                line.matakuliah_id.write(
                    {"rombel_ids": [Command.link(r.id) for r in line.rombel_ids]}
                )

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._sync_master_data()
        return records

    def write(self, vals):
        res = super().write(vals)
        if any(f in vals for f in ["rombel_ids", "line_ids"]):
            self._sync_master_data()
        return res


class ErpObeAkademikPenawaranLine(models.Model):
    _name = "erpobe.akademik.penawaran.line"
    _description = "Detail Kelas Penawaran"
    _rec_name = "matakuliah_id"
    _order = "matakuliah_id asc"

    penawaran_id = fields.Many2one(
        "erpobe.akademik.penawaran",
        string="Penawaran",
        required=True,
        ondelete="cascade",
    )
    matakuliah_id = fields.Many2one(
        "erpobe.master.matakuliah",
        string="Mata Kuliah",
        required=True,
    )
    rombel_ids = fields.Many2many(
        "erpobe.master.rombel",
        "erpobe_penawaran_line_rombel_rel",
        "line_id",
        "rombel_id",
        string="Kelas / Rombel",
        required=True,
    )
    semester_kurikulum = fields.Integer(
        related="matakuliah_id.semester",
        string="Smt. Kurikulum",
        store=True,
    )
    tahun_ajaran_id = fields.Many2one(
        related="penawaran_id.tahun_ajaran",
        string="Tahun Ajaran",
        store=True,
        readonly=True,
        index=True,
    )
    rps_ids = fields.One2many(
        "erpobe.akademik.rps",
        "penawaran_line_id",
        string="Versi RPS",
    )
    latest_rps_id = fields.Many2one(
        "erpobe.akademik.rps",
        string="RPS Aktif",
        compute="_compute_rps_status",
    )
    rps_status = fields.Selection(
        [
            ("missing", "Belum Ada"),
            ("draft", "Draft"),
            ("review", "Perlu Ditinjau"),
            ("final", "Final"),
        ],
        string="Status RPS",
        compute="_compute_rps_status",
    )
    rps_weight_status = fields.Selection(
        [
            ("complete", "Bobot Lengkap"),
            ("incomplete", "Bobot Belum Lengkap"),
        ],
        string="Kelengkapan Bobot",
        related="latest_rps_id.weight_status",
    )
    dosen_id = fields.Many2one(
        "erpobe.master.dosen",
        related="matakuliah_id.koordinator_id",
        string="Koordinator",
        readonly=True,
    )
    pengampu_ids = fields.Many2many(
        "erpobe.master.dosen",
        related="matakuliah_id.tim_pengampu_ids",
        readonly=True,
    )
    mahasiswa_ids = fields.Many2many(
        "erpobe.master.mahasiswa",
        "erpobe_penawaran_line_mahasiswa_rel",
        "penawaran_line_id",
        "mahasiswa_id",
        string="Mahasiswa",
        readonly=True,
    )

    prodi_id = fields.Many2one(
        related="matakuliah_id.prodi_id", store=True, readonly=True, index=True
    )

    fakultas_id = fields.Many2one(
        related="prodi_id.fakultas_id", store=True, readonly=True, index=True
    )

    @api.depends("rps_ids.version", "rps_ids.status", "rps_ids.write_date")
    def _compute_rps_status(self):
        for line in self:
            latest = line.rps_ids.sorted(
                key=lambda record: (record.version, record.id), reverse=True
            )[:1]
            line.latest_rps_id = latest
            line.rps_status = latest.status if latest else "missing"

    def action_create_rps(self):
        self.ensure_one()
        rps = self.env["erpobe.akademik.rps"].create(
            {
                "matakuliah_id": self.matakuliah_id.id,
                "penawaran_line_id": self.id,
                "version": max(self.rps_ids.mapped("version"), default=0) + 1,
                "status": "draft",
            }
        )
        return {
            "type": "ir.actions.act_window",
            "name": "RPS Baru",
            "res_model": "erpobe.akademik.rps",
            "res_id": rps.id,
            "view_mode": "form",
            "target": "current",
        }

    def action_copy_previous_rps(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Salin RPS Tahun Sebelumnya",
            "res_model": "erpobe.wizard.rps.copy",
            "view_mode": "form",
            "target": "new",
            "context": {"default_penawaran_line_id": self.id},
        }

    @api.constrains(
        "matakuliah_id", "rombel_ids", "dosen_id", "pengampu_ids", "mahasiswa_ids"
    )
    def _check_penawaran_faculty(self):
        for record in self:
            if any(
                rombel.prodi_id != record.prodi_id
                for rombel in record.rombel_ids
            ):
                raise ValidationError(
                    "Rombel penawaran harus berasal dari prodi mata kuliah."
                )
            dosen = record.pengampu_ids | record.dosen_id
            if any(
                record.prodi_id not in teacher.prodi_ids for teacher in dosen
            ):
                raise ValidationError(
                    "Dosen pengampu harus terdaftar pada prodi mata kuliah."
                )
            if any(
                student.prodi_id != record.prodi_id
                for student in record.mahasiswa_ids
            ):
                raise ValidationError(
                    "Mahasiswa penawaran harus berasal dari prodi mata kuliah."
                )

    @api.constrains("penawaran_id", "matakuliah_id")
    def _check_offer_prodi(self):
        for record in self:
            if (
                record.penawaran_id.prodi_id
                and record.penawaran_id.prodi_id != record.prodi_id
            ):
                raise ValidationError(
                    "Mata kuliah penawaran harus berasal dari prodi penawaran."
                )

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        offers = records.mapped("penawaran_id")
        for offer in offers.filtered(lambda record: not record.prodi_id):
            prodis = offer.line_ids.mapped("prodi_id")
            if len(prodis) == 1:
                offer.prodi_id = prodis.id
        return records

    def write(self, vals):
        # 1. SNAPSHOT: Simpan kondisi ID Rombel sebelum perubahan
        old_rombel_map = {}
        if 'rombel_ids' in vals:
            for line in self:
                old_rombel_map[line.id] = line.rombel_ids.ids

        # 2. EXECUTE: Jalankan penyimpanan standard Odoo
        res = super().write(vals)

        # 3. COMPARE: Cek apakah ada Rombel yang dihapus
        if 'rombel_ids' in vals:
            for line in self:
                # Ambil ID lama dari snapshot
                old_ids = set(old_rombel_map.get(line.id, []))
                # Ambil ID baru dari database (setelah save)
                new_ids = set(line.rombel_ids.ids)

                removed_ids = old_ids - new_ids             
                added_ids = new_ids - old_ids

                # EKSEKUSI HAPUS RELASI DI MASTER
                if removed_ids:
                    # Cari record rombel yang dibuang tadi
                    rombels_to_remove = self.env['erpobe.master.rombel'].browse(list(removed_ids))
                    # Hapus Mata Kuliah ini dari Rombel tersebut
                    rombels_to_remove.write({
                        'matakuliah_ids': [Command.unlink(line.matakuliah_id.id)]
                    })
                if added_ids:
                    rombels_to_add = self.env['erpobe.master.rombel'].browse(list(added_ids))
                    rombels_to_add.write({
                        'matakuliah_ids': [Command.link(line.matakuliah_id.id)]
                    })

        return res
    def unlink(self):
        """Hapus relasi di Master saat Line dihapus"""
        for line in self:
            if line.rombel_ids and line.matakuliah_id:
                line.rombel_ids.write(
                    {"matakuliah_ids": [Command.unlink(line.matakuliah_id.id)]}
                )
        return super().unlink()
