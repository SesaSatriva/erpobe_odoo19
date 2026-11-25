# Ringkasan Hasil Pengujian Black-Box

## Rekapitulasi

| Keterangan | Jumlah |
|---|---:|
| Total skenario pengujian | 42 |
| Pengujian berhasil (PASS) | 11 |
| Pengujian gagal (FAIL) | 2 |
| Pengujian terblokir (BLOCKED) | 7 |
| Belum diuji (NOT TESTED) | 22 |
| Persentase keberhasilan | 84.62% |

Persentase keberhasilan dihitung sebagai:

`Jumlah PASS / (PASS + FAIL) × 100% = 11 / (11 + 2) × 100% = 84.62%`

Skenario berstatus BLOCKED dan NOT TESTED tidak dihitung sebagai sukses maupun gagal.

## Cakupan Pelaksanaan

Pengujian aktual dilaksanakan pada database pengembangan `erpobe` setelah modul diperbarui agar skema tabel sesuai source code. Pelaksanaan mencakup:

- Login mahasiswa dan dosen fixture.
- Portal dashboard mahasiswa.
- Portal dashboard dosen.
- Halaman KRS, KHS, daftar mata kuliah, dan capaian CPL mahasiswa.
- Daftar RPS dosen.
- Pembatasan akses lintas role.
- Respons sistem saat input nilai dibuka untuk RPS yang belum final.
- Halaman publik perbandingan CPL.
- Eksekusi parsial rangkaian test Odoo ERP OBE.

## Fungsi yang Berjalan Sesuai Harapan

1. Login mahasiswa dan dosen berhasil dengan akun fixture yang aktif.
2. Dashboard mahasiswa dan dosen menampilkan konteks masing-masing.
3. Akun mahasiswa tidak dapat membuka endpoint khusus dosen dan menerima HTTP 403.
4. KRS mahasiswa menampilkan status Disetujui dan total 19/24 SKS.
5. KHS menampilkan data milik akun yang login, filter/paginasi, dan tautan PDF.
6. Portal mata kuliah menampilkan 63 record milik mahasiswa beserta komponen nilai pada sampel.
7. Portal CPL menampilkan 10 CPL pribadi dengan perlakuan `0.0%` untuk capaian tanpa data penilaian.
8. Portal RPS dosen membatasi daftar pada 16 penawaran yang diampu.
9. Halaman perbandingan CPL publik dapat dibuka dan tidak menampilkan data mahasiswa pribadi.

## Fungsi yang Mengalami Kegagalan atau Kendala

- Rangkaian test asisten akademik menghasilkan dua ERROR:
  - `TestAcademicAssistantIntent.test_context_and_unknown_questions`
  - `TestAcademicAssistantService.test_query_respects_model_access`
- Rute input nilai dosen pada kelas dengan RPS belum final merespons HTTP 422 sebagai validasi yang dimaksudkan. Ini merupakan pembatasan proses, bukan kegagalan validasi, tetapi belum dapat melanjutkan pengujian input nilai pada fixture saat ini.
- Analitik publik menampilkan bahwa keempat prodi belum memiliki data valid agregat pada periode yang dipilih. Halaman bekerja, tetapi hasil numerik agregat belum tersedia.
- Pembaruan database awal menghasilkan 500 pada login karena tabel audit belum tersedia. Upgrade modul berhasil menyelaraskan skema; login berikutnya berhasil.

## Dampak Permasalahan

- Kegagalan pada dua test asisten akademik dapat memengaruhi keandalan respons konteks dan pembatasan data asisten akademik.
- Ketersediaan RPS final yang terbatas menghambat pengujian input nilai, perhitungan CPMK, nilai mata kuliah, dan capaian CPL.
- Tidak tersedianya nilai agregat pada halaman publik membatasi bukti validasi hasil perbandingan antarprodi.
- Suite test menyeluruh sangat berat pada database pengembangan dan harus dihentikan setelah 33 menit karena regenerasi laporan dalam skala besar. Oleh karena itu, sejumlah skenario belum diuji akhir.

## Rekomendasi

1. Perbaiki dan eksekusi ulang dua test asisten akademik yang menghasilkan ERROR, khususnya konteks pertanyaan dan pembatasan model access.
2. Siapkan fixture terisolasi dengan satu RPS final, bobot lengkap, KRS disetujui, dan nilai komponen pada rentang 0–100 untuk pengujian perhitungan OBE.
3. Jalankan test bobot/RPS, KRS, dan fakultas secara terpisah agar tidak terhambat regenerasi laporan skala besar.
4. Lakukan pengujian nilai batas 0 dan 100 serta nilai invalid -1 dan 101 pada fixture RPS final.
5. Eksekusi pengujian lintas role dengan mahasiswa, dosen, admin prodi, dan superadmin pada database pengujian terisolasi.
6. Verifikasi ulang halaman detail, portal mahasiswa, dan dashboard untuk konsistensi nilai CPMK, mata kuliah, dan CPL.
7. Lakukan unduhan PDF/CSV serta respons gagal login, logout, dan reset password pada browser.
8. Jangan memperbarui source code aplikasi sebagai bagian pekerjaan dokumentasi ini.
