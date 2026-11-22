# PANDUAN PENGOPERASIAN DAN DOKUMENTASI TEKNIS SISTEM INFORMASI TRITON PENILAIAN KURIKULUM OUTCOME-BASED EDUCATION

## Identitas Dokumen dan Batasan Audit

Dokumen ini adalah revisi 1.1 atas draft awal (v1.0), dengan koreksi
formula dan penambahan catatan teknis yang diverifikasi langsung ke
source code modul erpobe.

| Item \| Nilai \|

| --- \| --- \|

| Nama dokumen \| Panduan Pengoperasian dan Dokumentasi Teknis Sistem
  ERP OBE \|

| Versi \| 1.1 (revisi atas v1.0) \|

| Tanggal \| 22 November 2026 \|

| Dasar penyusunan \| Audit source code, tanpa akses database produksi
  \|

| Penyusun / reviewer \| (isi) \|

| Versi source yang diaudit \| (isi commit hash atau tag) \|

| Platform \| Odoo 19, PostgreSQL \|

Tingkat verifikasi. Tidak semua bagian dokumen sudah dicocokkan dengan
kode. Setiap bab diberi penanda berikut:

| Penanda \| Arti \|

| --- \| --- \|

| Terverifikasi \| Dicocokkan baris demi baris dengan file yang disebut
  \|

| Belum diverifikasi \| Berasal dari draft awal; file terkait belum
  diperiksa pada audit ini \|

File yang sudah diperiksa: grade_cpl.py, grade_cpmk.py, grade_mk.py,
report_khs.py. File lain (RPS, KRS, input nilai, portal, security, view)
belum diperiksa.

| Versi \| Tanggal \| Keterangan \|

| --- \| --- \| --- \|

| 1.0 \| 22 Nov 2026 \| Draft awal berdasarkan audit source code \|

| 1.1 \| 22 Nov 2026 \| Koreksi rumus IPK, penjelasan jalur legacy,
  penambahan Bab IX (batasan dan catatan teknis), penanda tingkat
  verifikasi \|

## BAB I - Pendahuluan

ERP OBE adalah aplikasi Odoo custom yang menghitung capaian pembelajaran
dari nilai komponen penilaian: komponen menjadi nilai CPMK, CPMK menjadi
nilai mata kuliah dan nilai CPL, lalu hasilnya ditampilkan di transkrip
dan analisis.

Kerangka OBE. Rantai kurikulum adalah mata kuliah ↔ CPMK ↔ CPL. Dua
jenis bobot menghubungkan rantai itu: alokasi komponen penilaian
terhadap CPMK, dan bobot CPMK terhadap mata kuliah.

Ruang lingkup. Backend Odoo untuk administrator dan dosen, serta portal
website untuk dosen dan mahasiswa. Dokumen ini hanya menggambarkan fitur
yang ditemukan di source. Fitur approval atau integrasi yang tidak
ditemukan tidak diklaim ada.

Cara membaca. Bab V (formula) dan Bab IX (batasan teknis) adalah bagian
yang sudah diverifikasi ke kode. Bab III, IV, VI, dan VIII masih
bersumber dari draft awal dan perlu verifikasi lanjutan sebelum
dijadikan acuan resmi.

## BAB II - Arsitektur Sistem

Sistem berjalan di atas Odoo 19 dengan logika Python/ORM, penyimpanan
PostgreSQL, antarmuka XML/QWeb, dan modul website untuk portal.

| Aspek \| Keterangan \|

| --- \| --- \|

| Modul custom \| erpobe \|

| Dependensi Odoo (manifest) \| base, web, website, portal, contacts,
  mail \|

| Nilai tersimpan \| Field compute dengan store=True di model
  erpobe.grade.\* \|

| Laporan agregat \| Enam model \_auto = False berbasis SQL view yang
  sudah diperiksa (lihat 5.8); report_summary.py belum diperiksa \|

| Transkrip \| erpobe.report.khs memakai mail.thread dan
  mail.activity.mixin \|

| Pembatasan data \| Constraint prodi pada model nilai, ditambah record
  rule \|

Pola data yang penting dipahami. Model nilai (grade.cpmk, grade.mk,
grade.cpl) masing-masing memiliki constraint unik per mahasiswa,
sehingga hanya ada satu baris per mahasiswa untuk tiap CPMK, MK, atau
CPL. Riwayat per attempt tidak disimpan di tabel ini; baris yang ada
merujuk ke attempt aktif lewat krs_line_id dan rps_id.

## BAB III - Struktur Modul dan Fitur

Tabel berikut memuat fitur menurut draft awal. Kolom Verifikasi
menunjukkan apakah file terkait sudah dibuka pada audit ini.

| Fitur \| Pengguna \| Lokasi \|

| --- \| --- \| --- \|

| Fakultas dan Program Studi \| Administrator; dosen/mahasiswa akses
  baca \| akademik_fakultas.py, master_prodi.py \|

| Dosen, Mahasiswa, Rombel \| Administrator; dosen/mahasiswa terbatas \|
  master_user.py \|

| Kurikulum \| Administrator \| views/menus.xml dan model kurikulum
  (nama file tepat perlu dicek) \|

| Mata Kuliah \| Administrator \| master_akademik.py \|

| CPL dan CPMK \| Administrator CRUD; dosen sesuai ACL \|
  akademik_cpl.py, akademik_cpmk.py \|

| RPS dan penguncian final \| Administrator; dosen pengampu \|
  akademik_rps.py, rps_lock.py \|

| Komponen penilaian \| Administrator; dosen pada RPS \|
  rps_komponen.py, akademik_komponen.py \|

| Validasi bobot \| Sistem \| weight_validation.py,
  bobot_komponen_cpmk.py, bobot_cpmk_mk.py \|

| KRS \| Mahasiswa mengajukan; dosen wali memutuskan \| akademik_krs.py,
  portal_mahasiswa.py \|

| Input nilai komponen \| Administrator, dosen \| grade.py,
  portal_dosen.py \|

| Nilai CPMK \| Sistem (otomatis) \| grade_cpmk.py \|

| Nilai mata kuliah \| Sistem (otomatis) \| grade_mk.py \|

| Nilai CPL \| Sistem (otomatis) \| grade_cpl.py \|

| Transkrip (KHS/IPK) \| Administrator; mahasiswa \| report_khs.py \|

| Analisis rata-rata \| Administrator; dosen \| grade\_\*.py,
  report_summary.py \|

Catatan istilah. Model erpobe.report.khs berlabel "Rekap Hasil Studi
(Transkrip)" dan bersifat kumulatif, satu dokumen per mahasiswa. Ia
bukan KHS per semester. Tidak ada perhitungan IPS di file yang
diperiksa. Tahun Ajaran dan Penawaran Mata Kuliah juga belum ditinjau.

## BAB IV - Alur Data dan Proses Bisnis

Nilai mengalir satu arah dari komponen ke CPL, lalu disalin ke
transkrip.

Urutan menurut draft awal: Fakultas, Program Studi, Rombel/Angkatan,
Kurikulum/Mata Kuliah, CPL/CPMK, RPS, Penawaran kelas, KRS, nilai
komponen, CPMK, mata kuliah, CPL, lalu KHS/analisis.

Urutan persiapan (setup).

Isi master: Fakultas, Prodi, Rombel, Dosen, Mahasiswa, Tahun Ajaran.

Isi kurikulum: Mata Kuliah, CPL, CPMK, beserta pemetaan MK-CPL dan
CPL-MK-CPMK.

Buat RPS dari penawaran mata kuliah; isi komponen, alokasi
komponen-CPMK, dan bobot CPMK-MK.

Pastikan total bobot komponen 100% (toleransi 0,01), lalu finalkan RPS.
RPS final bersifat read-only; versi baru dibuat dengan salin.

Mahasiswa mengajukan KRS; dosen wali menyetujui atau mengembalikan.

Dosen menginput nilai komponen. Sistem menghitung CPMK, MK, dan CPL.

Transkrip diperbarui lewat action_generate_khs atau tombol manual (lihat
5.7).

Syarat nilai CPL muncul: grade CPMK tersedia, RPS final, KRS approved,
dan penawaran kelas memiliki RPS final. Syarat ini tidak berlaku untuk
nilai CPMK dan MK (lihat Bab IX).

## BAB V - Formula dan Mekanisme Perhitungan

Bab ini sudah dicocokkan dengan grade_cpmk.py, grade_mk.py,
grade_cpl.py, dan report_khs.py, kecuali 5.1 yang berasal dari draft
awal. Semua nilai bertipe float dengan presisi tampilan 2 desimal.

### 5.1 Validasi bobot komponen (belum diverifikasi)

Bobot komponen aktif pada RPS dianggap lengkap jika totalnya berada
dalam toleransi 0,01 dari 100.

Setiap bobot komponen dan setiap alokasi komponen terhadap CPMK dibatasi
0-100%. Lokasi menurut draft awal: weight_validation.py,
rps_komponen.py, bobot_komponen_cpmk.py, bobot_cpmk_mk.py.

### 5.2 Nilai CPMK mahasiswa

Fungsi: erpobe.grade.cpmk.\_compute_nilai_cpmk(). Ada dua jalur, dipilih
per baris.

Jalur exact, dipakai jika baris memiliki rps_id dan krs_line_id. Untuk
setiap alokasi komponen i terhadap CPMK, kontribusinya adalah bobot
komponen di RPS dikalikan alokasi:

Keterangan: = bobot komponen i pada RPS, = alokasi komponen i terhadap
CPMK, = nilai komponen i mahasiswa.

Komponen ikut dihitung hanya jika snapshot komponen RPS berstatus aktif
dan nilai komponen mahasiswa sudah is_graded = True. Jika penyebut 0,
maka is_available = False dan nilai CPMK 0,0.

Penting: renormalisasi. Penyebut hanya menjumlahkan komponen yang sudah
dinilai. Jika baru sebagian komponen dinilai, nilai CPMK adalah
rata-rata tertimbang atas komponen itu saja dan langsung berstatus
tersedia. Nilai CPMK, dan turunannya, bisa bersifat sementara sebelum
seluruh komponen dinilai (lihat 5.9, skenario B).

Jalur legacy, untuk baris lama tanpa rps_id atau krs_line_id.
Perbedaannya dari jalur exact:

Bobot yang dipakai hanya alokasi komponen terhadap CPMK. Bobot komponen
di RPS () tidak ikut.

RPS dipilih dari semua RPS mata kuliah itu, tanpa filter status final
dan tanpa filter komponen aktif. Bila beberapa RPS memuat CPMK yang
sama, alokasi dari RPS yang terbaca terakhir menimpa yang lain, sehingga
hasilnya bergantung urutan pencarian.

Nilai komponen dicocokkan berdasarkan (mahasiswa, mata kuliah,
komponen), dan bila ada lebih dari satu, yang pertama ditemukan dipakai.

Tidak ada pemeriksaan status KRS.

### 5.3 Ketercapaian CPMK

CPMK memiliki target_nilai (default 70 menurut draft awal; nilai default
di model CPMK belum diperiksa).

| Kondisi \| Status \|

| --- \| --- \|

| is_available = False \| belum_tersedia \|

| Nilai CPMK \>= target \| tercapai \|

| Nilai tersedia tetapi di bawah target \| belum \|

Tidak ada field tersimpan untuk persentase mahasiswa yang mencapai
target. Analisis per rombel/angkatan hanya berupa rata-rata (5.8).

### 5.4 Nilai mata kuliah

Fungsi: erpobe.grade.mk.\_compute_nilai_mk(). Jalur exact memakai bobot
CPMK terhadap MK dari tabel erpobe.bobot.cpmk.mk milik RPS yang dipakai.

Keterangan: = bobot CPMK j terhadap MK (dalam persen; pembagian 100 pada
pembilang dan penyebut saling meniadakan). Hanya CPMK dengan \> 0 dan
grade CPMK is_available = True (untuk KRS dan RPS yang sama) yang
dihitung. Jika penyebut 0, nilai 0,0 dan is_available = False.

Ketentuan lain:

Nilai MK tidak dijepit ke 0-100.

Tidak ada syarat RPS final atau KRS approved. Syarat itu hanya ada pada
nilai CPL.

Jalur legacy memakai bobot CPMK dari semua RPS mata kuliah (urutan
menurut id desc, tetapi pemetaan bobot ditimpa menurut urutan pembacaan
bobot), dan tidak memfilter is_available pada grade CPMK. CPMK yang
belum tersedia (nilai 0,0) tetap masuk hitungan sebagai nol.

Satu baris per (mahasiswa, mata kuliah); constraint unik
unique(mahasiswa_id, mk_id).

### 5.5 Nilai CPL mahasiswa

Fungsi: erpobe.grade.cpl.\_compute_nilai_cpl(). Nilai CPL adalah
rata-rata tertimbang nilai CPMK, dengan bobot CPMK terhadap MK dari RPS
pada grade CPMK tersebut.

Berbeda dari rumus MK, rumus ini menjumlahkan CPMK dari semua mata
kuliah yang berkontribusi ke CPL. Bobot adalah bobot di dalam
masing-masing MK, tidak dinormalisasi antar-MK. Akibatnya, CPMK dari MK
yang bobotnya besar atau jumlah CPMK-nya sedikit mendominasi (lihat 5.9,
skenario C).

Sebuah CPMK ikut dihitung jika memenuhi semua syarat berikut:

CPMK ada di pemetaan erpobe.akademik.cpl.mk.cpmk untuk CPL itu.

Prodi CPMK sama dengan prodi CPL. Jika berbeda, CPMK dilewati (tidak
disebut di draft awal).

Jika CPL memiliki pemetaan MK (erpobe.akademik.mk.cpl), MK dari CPMK
harus ada di pemetaan itu. Jika CPL belum memiliki pemetaan MK sama
sekali, syarat ini dilewati dan semua MK dari pemetaan CPMK dipakai.

Grade CPMK is_available = True, RPS-nya berstatus final, KRS-nya
approved, dan penawaran kelas pada KRS line memiliki RPS final.

Bobot CPMK terhadap MK pada RPS tersebut lebih dari 0.

Jika tidak ada CPMK yang lolos, is_available = False dan nilai 0,0.
Hasil dijepit ke 0-100.

Status capaian CPL (\_compute_status_capaian):

| Kondisi \| Status \|

| --- \| --- \|

| Data tersedia dan nilai \>= target_nilai CPL \| tercapai \|

| Data tersedia dan nilai \< target \| belum \|

| Data belum tersedia, dan mahasiswa memiliki KRS line pada salah satu
  MK kontributor \| dalam_proses \|

| Data belum tersedia, tanpa KRS line di MK kontributor \|
  belum_tersedia \|

KRS line yang dicek tidak difilter menurut status, sehingga KRS draftt
atau ditolak pun membuat status menjadi dalam_proses.

### 5.6 Konversi nilai angka ke huruf

Dilakukan di erpobe.report.khs.mk.\_compute_grade() memakai master
erpobe.master.grade. Baris master diurutkan menurut nilai_min menurun.
Baris pertama dengan nilai_min kurang dari atau sama dengan nilai angka
MK dipakai untuk mengisi huruf (name) dan bobot. Jika tidak ada yang
cocok, hasilnya huruf E dengan bobot 0. Skala konkret (batas nilai dan
bobot per huruf) berada di data master, bukan di kode, sehingga harus
dicantumkan dari data aktual institusi.

### 5.7 Transkrip, IPK, dan SKS lulus

Model erpobe.report.khs adalah transkrip kumulatif, satu dokumen per
mahasiswa (unique(mahasiswa_id)). Tidak ada IPS per semester. Field
tahun_ajaran_id ada tetapi tidak dipakai dalam perhitungan.

Untuk setiap kode MK dipilih satu baris dengan bobot huruf tertinggi
(relevan bila kode MK yang sama muncul lebih dari sekali). Baris dengan
SKS 0 atau tanpa kode MK dilewati.

Keterangan: = SKS, = bobot huruf MK unik k. Penyebut IPK adalah semua
SKS MK unik, termasuk yang bernilai E. Hanya SKS lulus yang membatasi
bobot lebih dari 0. Tidak ada batas nilai minimal kelulusan selain bobot
di atas 0, jadi huruf berbobot positif (misalnya D, jika demikian di
master) dihitung lulus. Jika total SKS 0, IPK = 0,0.

Cara transkrip terisi. Metode \_sync_from_grades menghapus lalu membuat
ulang seluruh baris MK, CPMK, CPL, dan komponen (komponen hanya yang
is_graded = True) dari tabel erpobe.grade.\* milik mahasiswa itu, tanpa
filter is_available pada MK, CPMK, dan CPL. Sinkronisasi berjalan saat
dokumen dibuat, lewat action_generate_khs, tombol manual
action_fetch_nilai, dan saat write() pada erpobe.grade.mk dipanggil.

### 5.8 Analisis rata-rata per rombel dan angkatan

Enam SQL view menghitung AVG tanpa menampilkan jumlah mahasiswa (N).
Perbedaan filternya penting saat membaca hasil:

| View \| Dikelompokkan per \| Filter is_available \| Filter lain \|
  Kolom id \|

| --- \| --- \| --- \| --- \| --- \|

| grade.cpl.rombel \| rombel, CPL \| Ya \| - \| MIN(id) \|

| grade.cpl.angkatan \| angkatan, CPL \| Ya \| - \| MIN(id) \|

| grade.mk.rombel \| rombel, MK \| Tidak \| rombel tidak kosong \|
  MIN(id) \|

| grade.mk.angkatan \| angkatan, MK \| Tidak \| - \| MIN(id) \|

| cpmk.rombel \| rombel, CPMK \| Ya \| rombel tidak kosong \|
  ROW_NUMBER() \|

| cpmk.angkatan \| angkatan, CPMK \| Ya \| angkatan tidak kosong \|
  ROW_NUMBER() \|

Nilai rata-rata MK menyertakan baris yang belum tersedia (bernilai 0,0),
sehingga rata-rata bisa terlalu rendah (lihat Bab IX, poin 2).

### 5.9 Simulasi (ilustrasi, bukan data produksi)

Data. MK-X memiliki tiga komponen aktif dengan RPS final dan KRS
approved. Nilai mahasiswa: Tugas 80, UTS 70, UAS 90.

| Komponen \| Bobot di RPS (w) \| Alokasi ke CPMK-01 \| Alokasi ke
  CPMK-02 \| Nilai \|

| --- \| --- \| --- \| --- \| --- \|

| Tugas \| 30 \| 100 \| - \| 80 \|

| UTS \| 30 \| 100 \| - \| 70 \|

| UAS \| 40 \| - \| 100 \| 90 \|

Bobot CPMK terhadap MK-X: CPMK-01 = 60, CPMK-02 = 40.

Skenario A: semua komponen dinilai.

CPMK-01: A(Tugas) = 30, A(UTS) = 30. Nilai = (80 x 30 + 70 x 30) / 60 =
75,0.

CPMK-02: A(UAS) = 40. Nilai = 90 x 40 / 40 = 90,0.

MK-X = (75 x 60 + 90 x 40) / (60 + 40) = 81,0.

Skenario B: UAS belum dinilai. CPMK-02 tidak memiliki komponen ternilai,
sehingga tidak tersedia. MK-X dihitung hanya dari CPMK-01: (75 x 60) /
60 = 75,0, berstatus tersedia, meskipun 40% bobot mata kuliah belum
dinilai. Jika baru Tugas yang dinilai, CPMK-01 = 80 dan MK-X = 80,0.
Nilai sementara ini ikut masuk ke transkrip.

Skenario C: dua mata kuliah ke satu CPL. MK-Y memiliki satu CPMK
(CPMK-03, nilai 60, bobot CPMK terhadap MK-Y = 100). CPL-01 dipetakan ke
CPMK-01 dan CPMK-03.

CPL-01 = (75 x 60 + 60 x 100) / (60 + 100) = 10.500 / 160 = 65,63.

Dengan target 70, CPMK-01 tercapai (75), CPMK-03 belum (60), dan CPL-01
belum tercapai.

Karena bobot 100 pada MK-Y lebih besar dari bobot 60 pada MK-X, MK-Y
menarik nilai CPL lebih kuat meskipun kedua MK sama pentingnya bagi CPL.
Jika institusi menghendaki bobot antar-MK yang eksplisit, ini perlu
diatur ulang (lihat Bab IX, poin 5).

## BAB VI - Panduan Pengguna

Bab ini bersumber dari draft awal dan belum dicocokkan dengan
controller, view, dan security. Nama menu backend, langkah klik, dan
tangkapan layar perlu ditambahkan setelah file views/, controllers/, dan
security/ diperiksa.

### 6.1 Administrator

Akses. Login ke backend Odoo dengan akun yang memiliki grup
administrator modul ERP OBE. Nama grup yang tepat perlu diisi dari
security/.

Tugas utama.

Kelola master: Fakultas, Program Studi, Rombel, Dosen, Mahasiswa, Mata
Kuliah, Kurikulum, Tahun Ajaran.

Kelola CPL, CPMK, dan pemetaannya (MK-CPL, CPL-MK-CPMK).

Kelola RPS, komponen penilaian, alokasi komponen-CPMK, dan bobot
CPMK-MK.

Kelola Penawaran Mata Kuliah, input nilai, dan laporan.

Perhatikan. Prodi pada mahasiswa, mata kuliah, CPL, dan CPMK harus
konsisten. Model nilai menolak data lintas prodi (lihat Bab IX, poin 9).
RPS hanya dapat difinalkan setelah total bobot mencapai 100% (toleransi
0,01). RPS final tidak dapat diubah; buat versi baru dengan salin.

### 6.2 Dosen

Akses. Portal website. Rute yang disebut di draft awal: /my/rps,
/my/kelas, /my/perwalian, /my/analisis. Rute /my/triton perlu dipastikan
di controller, apakah memang ada atau sisa penamaan.

Membuat, mengubah, menyalin, dan memfinalkan RPS hanya untuk mata kuliah
yang diampu (koordinator atau tim pengampu).

Input nilai hanya setelah RPS final dan bobot lengkap.

Dosen wali meninjau dan memutuskan KRS mahasiswa bimbingan.

Melihat analisis capaian CPMK, MK, dan CPL.

### 6.3 Mahasiswa

Akses. Portal website. Rute dari draft awal: /my/krs, /my/khs,
/my/mata-kuliah, /my/rps/`<id>`{=html}, /my/capaian-cpl, /my/profil.

Mengisi dan mengajukan KRS pada penawaran aktif untuk rombel/prodinya.

Melihat mata kuliah, komponen nilai, RPS final yang relevan, transkrip,
dan capaian CPL.

Tidak memiliki hak backend untuk mengubah master atau nilai.

Cara membaca tampilan nilai. Nilai CPMK, MK, dan CPL dapat sementara
jika komponen belum semuanya dinilai (5.2 dan 5.9). Nilai 0,0 pada
transkrip dapat berarti nilai nol atau data belum tersedia; keduanya
belum dibedakan di tampilan transkrip (Bab IX, poin 1).

## BAB VII - Diagram Sistem

Gambar 1. Alur nilai dari komponen ke CPL dan transkrip

Nilai CPMK, MK, dan CPL dihitung dari nilai komponen secara terpisah.
Hanya CPL yang mensyaratkan RPS final dan KRS approved, dan transkrip
menyalin semua baris tanpa menyaring ketersediaan data (Bab IX, poin 1).

Sumber diagram lain (ERD, alur KRS, alur finalisasi RPS) berada di
folder diagrams/ pada repositori dalam format Mermaid dan belum ditinjau
pada audit ini. Disarankan menyisipkan hasil render-nya ke bab ini.

## BAB VIII - Troubleshooting

Penyebab di kolom Pemeriksaan untuk masalah nilai sudah selaras dengan
kode yang diperiksa. Baris akses dan portal masih dari draft awal.

| Masalah \| Pemeriksaan \| Solusi \| Penanggung jawab \|

| --- \| --- \| --- \| --- \|

| Tidak dapat login \| Login/email/NIM/NIP dan status akun aktif \|
  Periksa relasi profil; reset password lewat administrasi Odoo \|
  Administrator \|

| Tidak ada akses menu \| Grup dan record rule per prodi;
  erpobe_prodi_ids \| Tambahkan grup yang tepat \| Administrator \|

| Fakultas/prodi tidak muncul \| Relasi fakultas_id, prodi_id,
  erpobe_prodi_ids \| Perbaiki master lewat antarmuka, bukan SQL \|
  Administrator \|

| RPS tidak dapat difinalkan \| Total bobot komponen dan alokasi CPMK \|
  Lengkapi bobot hingga 100 (toleransi 0,01) \| Dosen / Administrator \|

| Nilai CPMK kosong atau 0,0 \| Belum ada komponen is_graded = True;
  alokasi komponen-CPMK belum diisi; komponen tidak aktif \| Nilai
  komponen, atau lengkapi alokasi \| Dosen \|

| Nilai MK kosong \| Tidak ada CPMK tersedia dengan bobot CPMK-MK \> 0
  \| Lengkapi bobot CPMK-MK dan nilai komponen \| Dosen / Administrator
  \|

| Nilai CPL tidak muncul \| Pemetaan CPL-CPMK dan MK-CPL; RPS final; KRS
  approved; prodi CPMK sama dengan prodi CPL; bobot CPMK-MK \> 0 \|
  Perbaiki pemetaan, finalkan RPS, setujui KRS \| Administrator \|

| Status CPL dalam_proses padahal KRS belum disetujui \| Query status
  tidak memfilter status KRS \| Abaikan, atau perbaiki kode (Bab IX,
  poin 3) \| Pengembang \|

| Nilai CPL tidak berubah setelah bobot RPS diubah \| Dependensi compute
  tidak mencakup bobot RPS dan status \| Picu hitung ulang nilai CPMK
  atau tulis ulang baris CPL \| Pengembang \|

| Mata kuliah baru tidak muncul di transkrip \| Sinkronisasi hanya
  berjalan saat create, action_generate_khs, atau tombol manual \| Klik
  tombol Fetch Nilai pada transkrip \| Administrator \|

| IPK lebih rendah dari perkiraan \| Baris MK tidak tersedia (nilai 0,0)
  tercatat sebagai E dan masuk penyebut \| Periksa baris erpobe.grade.mk
  dengan is_available = False \| Administrator / Pengembang \|

| Rata-rata MK per rombel/angkatan rendah \| View MK tidak memfilter
  is_available \| Perbaiki view (Bab IX, poin 2) \| Pengembang \|

| Data portal tidak muncul \| Relasi user-profil dan scope rombel/prodi;
  \_require_student() / \_require_teacher() \| Periksa profil dan rule
  \| Administrator \|

## BAB IX - Batasan dan Catatan Teknis

Sepuluh temuan dari pemeriksaan grade_cpmk.py, grade_mk.py,
grade_cpl.py, dan report_khs.py. Prioritas Tinggi berarti dapat mengubah
angka yang dilihat mahasiswa atau dilaporkan ke akreditasi. Poin yang
bertanda (uji) berasal dari pembacaan kode dan sebaiknya dikonfirmasi di
instance uji sebelum dianggap pasti.

| No \| Temuan \| Dampak \| Saran \| Prioritas \|

| --- \| --- \| --- \| --- \| --- \|

| 1 \| Nilai sementara dan nilai 0,0 masuk ke transkrip. Penyebut CPMK
  hanya mencakup komponen yang sudah dinilai, dan grade.mk tidak
  mensyaratkan RPS final atau KRS approved. Transkrip menyalin semua
  baris grade.mk, grade.cpmk, dan grade.cpl tanpa filter is_available.
  Baris MK yang tidak tersedia (0,0) menjadi huruf E dan SKS-nya masuk
  penyebut IPK. \| IPK dapat terisi nilai parsial, atau terdeflasi oleh
  baris tidak tersedia. Transkrip tidak membedakan nilai nol dari data
  belum ada. \| Filter is_available saat sinkronisasi; tampilkan "belum
  tersedia"; tentukan apakah nilai parsial boleh masuk transkrip.
  Periksa di mana baris grade.mk dibuat. \| Tinggi \|

| 2 \| View rata-rata MK tidak memfilter is_available (grade.mk.rombel,
  grade.mk.angkatan). \| Rata-rata MK per rombel/angkatan terlalu rendah
  bila ada baris 0,0. \| Tambahkan WHERE gm.is_available IS TRUE. \|
  Tinggi \|

| 3 \| Status CPL dalam_proses longgar dan dapat basi. Query KRS tidak
  memfilter status, dan KRS tidak ada di @api.depends. \| KRS draftt
  atau ditolak pun menghasilkan dalam_proses; status tidak berubah saat
  mahasiswa mendaftar (uji). \| Filter KRS approved; tambahkan
  dependensi. \| Sedang \|

| 4 \| Dependensi compute tidak lengkap. Nilai CPL tidak mendengarkan
  rps_id.status, status KRS, atau bobot CPMK-MK; nilai MK dan CPMK tidak
  mendengarkan komponen aktif atau perubahan krs_line_id/rps_id. \|
  Nilai tersimpan dapat basi setelah RPS dikunci atau bobot diubah
  (uji). \| Lengkapi @api.depends, atau sediakan aksi hitung ulang
  massal. \| Tinggi \|

| 5 \| Bobot tidak dinormalisasi antar-MK. CPL memakai bobot CPMK di
  dalam masing-masing MK. \| MK dengan bobot CPMK besar atau CPMK
  tunggal mendominasi CPL (5.9, skenario C). \| Tetapkan kebijakan
  resmi: normalisasi per MK, atau bobot MK-CPL eksplisit. Dokumentasikan
  keputusan. \| Sedang \|

| 6 \| Jalur legacy tidak seketat jalur exact. Tidak memfilter RPS
  final, komponen aktif, status KRS, atau is_available (MK); bobot
  antar-RPS saling menimpa. \| Hasil bergantung urutan pencarian bila
  data lama masih ada. \| Migrasikan data lama ke jalur exact, lalu
  hapus jalur legacy. \| Sedang \|

| 7 \| Sinkronisasi transkrip tidak sepenuhnya otomatis. Pemicu ada pada
  create dan write eksplisit; recompute field tersimpan kemungkinan
  tidak melewati write (uji). Setiap sinkronisasi menghapus dan membuat
  ulang semua baris. \| Baris baru dapat tidak muncul sampai tombol
  manual ditekan; beban tinggi bila sering dipanggil. \| Pemicu
  eksplisit saat nilai berubah, dan sinkronisasi diferensial. \| Sedang
  \|

| 8 \| Populasi data tidak seragam, dan id view tidak stabil. View CPL
  hanya berisi nilai dari RPS final dan KRS approved (lewat compute),
  sedangkan CPMK dan MK tidak. View CPMK memakai ROW_NUMBER() OVER()
  sebagai id. \| Rata-rata CPMK dan CPL per rombel berasal dari populasi
  berbeda; id dapat berubah antar-query dan mengganggu pivot atau
  drill-down. \| Samakan syarat data; ganti dengan MIN(id) atau kunci
  komposit. \| Sedang \|

| 9 \| Constraint prodi dan pesan galat. Constraint membandingkan prodi,
  tetapi pesan galat menyebut "fakultas". Constraint prodi pada grade.mk
  juga menolak mata kuliah lintas prodi (misalnya MK umum). \| Pesan
  membingungkan; MK umum lintas prodi tidak dapat dinilai. \| Perbaiki
  pesan; putuskan kebijakan MK lintas prodi. \| Rendah \|

| 10 \| Catatan lain. (a) Huruf dan bobot di baris transkrip tidak ikut
  berubah bila skala erpobe.master.grade diubah. (b) Tidak ada batas
  nilai minimal kelulusan selain bobot \> 0. (c) View tidak menampilkan
  jumlah mahasiswa (N). (d) Sumber prodi berbeda antar view (m.prodi_id
  vs cpl.prodi_id). (e) krs_line_id dan rps_id pada grade.cpl tidak
  diisi oleh compute. (f) Riwayat attempt tidak disimpan karena
  constraint unik per mahasiswa. \| Menurunkan akurasi laporan historis.
  \| Tambahkan kolom N; dokumentasikan atau perbaiki masing-masing. \|
  Rendah \|

### Pemeriksaan lanjutan yang disarankan

File tempat erpobe.grade.mk dan erpobe.grade.komponen dibuat atau diubah
(kemungkinan grade.py / input nilai), untuk memastikan poin 1 dan
perilaku retake.

bobot_komponen_cpmk.py, bobot_cpmk_mk.py, weight_validation.py: apakah
alokasi komponen terhadap CPMK dan bobot CPMK-MK wajib berjumlah 100.

security/ (ACL dan record rule), controllers/ (portal), dan
report_summary.py.

Jalankan skenario 5.9 di instance uji untuk memastikan angkanya sama.

## BAB X - Glosarium dan Referensi

| Istilah \| Arti \|

| --- \| --- \|

| OBE \| Outcome-Based Education, pendidikan berbasis capaian \|

| CPL \| Capaian Pembelajaran Lulusan \|

| CPMK \| Capaian Pembelajaran Mata Kuliah \|

| RPS \| Rencana Pembelajaran Semester \|

| KRS \| Kartu Rencana Studi; pengambilan mata kuliah oleh mahasiswa per
  semester \|

| KHS \| Kartu Hasil Studi. Pada sistem ini modelnya berupa transkrip
  kumulatif \|

| IPK \| Indeks Prestasi Kumulatif \|

| IPS \| Indeks Prestasi Semester (tidak dihitung di sistem ini) \|

| SKS \| Satuan Kredit Semester \|

| Rombel \| Rombongan belajar; kelompok mahasiswa, memiliki angkatan \|

| Prodi \| Program Studi \|

| Dosen wali \| Dosen yang menyetujui KRS mahasiswa bimbingannya \|

| Penawaran mata kuliah \| Daftar kelas atau mata kuliah yang dibuka
  pada periode tertentu \|

| Snapshot komponen \| Salinan komponen penilaian pada RPS tertentu
  (rps_komponen) yang dipakai sebagai dasar bobot \|

| is_graded \| Penanda bahwa nilai komponen mahasiswa sudah diisi \|

| is_available \| Penanda bahwa penyebut bobot lebih dari 0, sehingga
  nilai dapat dihitung \|

| Rata-rata tertimbang \| Jumlah (nilai x bobot) dibagi jumlah bobot
  yang dipakai \|

| Renormalisasi \| Penyebut hanya memuat unsur yang tersedia, sehingga
  bobot yang hilang tidak dihitung nol \|

| ORM \| Object-Relational Mapping milik Odoo \|

| ACL \| Hak CRUD per model (ir.model.access) \|

| Record rule \| Pembatasan record berdasarkan domain \|

| Portal \| Antarmuka website untuk pengguna login \|

| QWeb \| Mesin template XML milik Odoo \|
