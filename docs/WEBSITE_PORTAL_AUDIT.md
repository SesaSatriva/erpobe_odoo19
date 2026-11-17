# ERP OBE Website & Portal Audit

## 1. Scope and audit basis

Dokumen ini dibuat berdasarkan audit langsung terhadap modul `erpobe` di workspace saat ini, meliputi:

- `__manifest__.py`
- `controllers/`
- `models/`
- `views/`
- `security/`
- `static/src/scss/`
- `static/src/js/`
- `README.md` dan dokumentasi teknis yang tersedia

Tujuan audit adalah menilai kondisi existing website publik, portal user, keamanan akses, dan kesiapan implementasi redesign enterprise yang konsisten dengan prinsip Odoo 19 native website + portal framework.

---

## 2. Executive summary

Modul `erpobe` adalah modul aplikasi akademik yang cukup lengkap dan sudah memiliki arsitektur website publik serta portal user. Struktur modul sudah jauh lebih matang daripada modul sederhana: ada website landing page, halaman fakultas/prodi, halaman tracking, halaman pencarian, halaman publik untuk profil dan perbandingan CPL, serta portal mahasiswa/dosen yang mencakup KRS, KHS, RPS, kelas, perwalian, dan profil.

Secara umum, komponen inti sudah ada dan secara konsep sesuai dengan kebutuhan OBE akademik. Namun dari sisi desain dan keamanan, masih ada beberapa hal yang perlu dibenahi agar sesuai dengan arahan enterprise software / institutional information system yang professional.

Temuan utama:

- Website publik sudah terstruktur dan memiliki banyak halaman, tetapi visualnya masih perlu konsolidasi untuk mencapai gaya enterprise yang konsisten.
- Portal user sudah dibangun dengan controller terpisah dan template khusus, tetapi beberapa bagian masih terlalu “custom landing-page focused” dan perlu dikuatkan dengan pola portal Odoo native yang lebih konsisten.
- Akses security terpotensi terlalu longgar di beberapa titik karena penggunaan `sudo()` pada operasi yang seharusnya di-filter berdasarkan profil/user context.
- Beberapa ACL/record rules bersifat granular namun masih perlu verifikasi eksekusi di lapangan, terutama untuk model yang digunakan di portal dan public pages.
- Desain SCSS sudah mencoba membangun sistem visual, tetapi masih tersebar dan berpotensi terjadi tumpang tindih gaya karena komponen yang dipecah ke beberapa file partial.

Dengan kata lain, modul sudah berada di tahap implementasi fungsional yang kuat, namun masih butuh polishing operasional, konsistensi tata letak, dan hardening akses agar siap untuk production-grade portal.

---

## 3. Current structure and module architecture

### 3.1 Manifest overview

`__manifest__.py` menunjukkan modul aplikasi pendidikan dengan dependencies utama:

- `base`, `web`, `website`, `portal`, `contacts`, `mail`
- asset frontend dideklarasikan pada `web.assets_frontend`
- data XML meliputi security, view, templates, dan menu

Ini sesuai arahan Odoo 19: penggunaan `website` dan `portal` adalah native dan tepat. Asset style dan JS diikat ke frontend Odoo, bukan app standalone.

### 3.2 Directory structure

Modul terdiri dari bagian utama berikut:

- `controllers/`: website/public + portal controllers
- `models/`: model data akademik utama
- `views/`: XML views dan templates
- `security/`: groups, ACL, record rules
- `static/src/scss/`: design system & partial styles
- `static/src/js/`: JS helper (misal `print.js`)
- `wizard/`: importer/exporter
- `tests/`: unit testing

Struktur ini sudah sesuai dengan arsitektur Odoo module yang sehat.

---

## 4. Existing website pages and portal landscape

### 4.1 Public website pages already present

Berdasarkan controller dan template, halaman yang tersedia meliputi:

- `/` atau `/triton`: landing page
- `/fakultas` dan `/prodi/<id>`: halaman fakultas/prodi
- `/perbandingan-cpl`: agregat CPL per program studi
- `/tracking`: tracking data akademik agregat
- `/tentang`: overview institusi / OBE
- `/panduan`: guidance/information
- `/faq`: bantuan umum
- `/kontak`: contact page
- `/kebijakan-privasi`: privacy statement
- `/metodologi`: methodology description
- `/cari`: search page
- profil publik dosen dan mahasiswa

Halaman ini menunjukkan cakupan publik yang sudah cukup matang untuk kebutuhan informasi akademik institusi.

### 4.2 Portal pages already present

Portal sudah dibangun untuk dua role utama:

- Mahasiswa:
  - `/my/krs`
  - `/my/khs`
  - `/my/mata-kuliah`
  - `/my/capaian-cpl`
  - `/my/profil`
- Dosen:
  - `/my/rps`
  - `/my/kelas`
  - `/my/perwalian`
  - `/my/analisis`

Portal home juga dibuat di `/my/triton` dan memanfaatkan `request.render('erpobe.triton_portal_home_page')`.

Kesimpulan: portal user tidak hanya sekadar halaman publik, tetapi sudah benar-benar menjadi area yang terpisah dan berfungsi sebagai workspace user-specific.

---

## 5. Internal-user vs portal-user exposure review

### 5.1 Features that are internal/user-specific

Berdasarkan `security/ir.model.access.csv` dan record rules, banyak model berikut pada dasarnya lebih cocok untuk internal admin/dosen:

- `erpobe.akademik.rps`
- `erpobe.akademik.penawaran`
- `erpobe.akademik.penawaran.line`
- `erpobe.akademik.krs` (beberapa akses masih terbatas)
- `erpobe.weight.monitor`
- wizard import/export
- master data akademik seperti fakultas, prodi, dosen, matakuliah, rombel

Hal ini wajar karena modul adalah sistem akademik operasional. Tidak semua fitur seharusnya dibuka untuk portal publik.

### 5.2 Features that can be exposed to portal user

Fitur yang paling layak dibuka ke portal user adalah:

- KRS draft & submit
- KHS dan transkrip mahasiswa
- Mata kuliah yang sudah disetujui
- Capaian CPL pribadi
- Profil/opt-out privasi
- RPS review/finalisasi untuk dosen pengampu
- Kelas yang diampu
- Perwalian dan keputusan KRS mahasiswa bimbingan

Ini sudah sesuai dengan prinsip portal: portal user harus membuka fitur yang memang relevan, bukan seluruh sistem administrasi internal.

### 5.3 Current gap

Meskipun fitur tersebut ada, perlu penguatan lagi terkait:

- menyinkronkan semua route portal dengan `CustomerPortal` patterns yang lebih native
- memastikan akses user dilakukan dengan logika yang eksplisit dan bukan hanya berdasarkan `has_group`
- memastikan `sudo()` tidak digunakan untuk operasi non-konteks yang bisa mengabaikan data ownership

---

## 6. Security and access architecture review

### 6.1 Groups

`security/groups.xml` sudah membentuk 4 level utama:

- `group_mahasiswa` => implied `base.group_portal`
- `group_dosen` => implied `base.group_portal`
- `group_admin`
- `group_superadmin`

Ini adalah struktur yang benar untuk Odoo portal-based access.

### 6.2 ACLs

`ir.model.access.csv` menunjukkan kebijakan akses yang cukup detail. Ada beberapa hal penting:

- admin memiliki write/create/unlink paling banyak
- dosen biasanya memiliki read/write/create pada model operasional
- mahasiswa diberi akses read minimal pada model yang relevan

Namun, ada beberapa potensi issue:

- `access_krs_mahasiswa` hanya memberi `perm_create=1`, bukan `perm_read` atau `perm_write` dari sisi record ownership (ini mungkin disengaja karena logic di controller diselesaikan via record rules atau `sudo()`).
- beberapa model secara ACL tidak memberikan `read` untuk kelompok mahasiswa, meskipun halaman portal membutuhkan data tertentu; jika controller mengandalkan `sudo()`, maka ini menjadi area yang perlu dikaji lebih lanjut.
- beberapa model public / portal data dapat terlalu mudah diakses bila query tidak dibatasi dengan domain yang jelas.

### 6.3 Record rules

`security/rules.xml` menunjukkan domain rule berdasarkan `user.erpobe_prodi_ids`, yang merupakan cara yang masuk akal untuk membatasi data fakultas/prodi. Ini sangat baik untuk data akademik terbatas organisasi.

Namun, rule ini juga memunculkan kebutuhan verifikasi berikut:

- apakah semua model yang digunakan portal memiliki rule yang memadai?
- apakah `user.erpobe_prodi_ids` selalu ada dan terisi untuk mahasiswa/dosen yang terhubung?
- apakah `group_mahasiswa` dengan rule `('user_id', '=', user.id)` benar-benar mengunci akses ke data dirinya hanya, tanpa bocor ke record lain?

### 6.4 Security risks identified

Potensi risiko utama:

1. Overuse of `sudo()` in portal controllers.
   - Banyak controller dan helper cenderung melakukan `sudo()` untuk search/read data mahasiswa/dosen, terutama untuk portal user.
   - Ini bisa mengaburkan ownership boundaries jika tidak dibarengi validasi akses yang eksplisit.

2. Akses public page terhadap data agregat bisa menjadi terlalu lebar.
   - public pages sebaiknya hanya menampilkan data yang dipastikan aman dan sesuai kebijakan privasi.
   - jika query memuat data mahasiswa/dosen tanpa filter `public_opt_out` atau `people_enabled`, risiko privacy meningkat.

3. Portal home route and custom templates can bypass native portal standard patterns.
   - Meskipun fungsional, struktur custom dapat menyebabkan disparate UX dan keamanan yang tidak konsisten bila route tidak mengikuti pola `portal.portal_layout` atau `portal.portal_my_home` secara native.

4. Missing explicit controller-side validation on some sensitive operations.
   - Beberapa endpoint mengubah status atau data akademik (misalnya submit KRS, finalize RPS, edit nilai) perlu verifikasi yang tegas: ownership, role, state, user membership, record existence.

---

## 7. Website design assessment

### 7.1 Strengths

- Navigation sudah jelas dan ada landing page yang memiliki struktur informasi.
- Page sections terorganisir dengan heading, panel, CTA, dan data stats.
- Ada upaya membangun design system melalui SCSS partials.
- Landing page dan portal sudah berusaha mengurangi template generik Odoo default.

### 7.2 Weaknesses

- Visual design still feels like a multi-component custom style experiment rather than one coherent design system.
- Some files are fragmented (`_navigation.scss`, `_hero.scss`, `_professional.scss`, `_portal.scss`, etc.) and risk style duplication.
- Repeated class naming patterns (`o_triton_*`) may be useful but can lead to visual drift if not centralized.
- There is a risk of conflicting selectors when multiple partials define similar base rules.

### 7.3 Best-fit design direction

Untuk mencapai enterprise institutional look, prioritas desain yang tepat adalah:

- gunakan 1-2 font family maksimum
- pilih 1 primary brand color + neutral scale + semantic colors
- batasi penggunaan card/container dekoratif
- konsisten spacing system dan grid container
- jadikan informasi dan fungsi sebagai pusat perhatian, bukan ornament
- gunakan hero + stat + section heading secara terukur

---

## 8. Template and asset review

### 8.1 Public templates

File `views/triton_public_templates.xml` sudah memuat:

- `triton_main_nav`
- `triton_footer`
- home page
- search page
- pages for about/help/contact/privacy/methodology

Ini untuk website publik sudah cukup lengkap dan konsisten di level struktural.

### 8.2 Portal templates

File `views/triton_portal_templates.xml` memuat:

- nav portal
- home dashboard
- KRS, KHS, mata kuliah, CPL, profil
- RPS editor, kelas dosen, perwalian, analisis

Secara konseptual, ini sudah benar sebagai portal user-specific.

### 8.3 CSS/SCSS assessment

Partial SCSS yang ada:

- `_tokens.scss`
- `components/_navigation.scss`
- `components/_hero.scss`
- `components/_components.scss`
- `components/_portal.scss`
- `components/_responsive.scss`
- `components/_states.scss`
- `pages/_professional.scss`

Kelebihan: modular.
Kekurangan: perlu finalisasi token naming dan audit duplicate selectors supaya tidak ada gaya yang saling bertabrakan antara halaman website dan portal.

---

## 9. Controller review

### 9.1 Public controllers

- `main.py`: homepage, search, static pages
- `fakultas.py`: faculty/prodi detail pages
- `tracking.py`: tracking pages
- `profil.py`: public person profile pages
- `perbandingan.py`: comparison API and CSV export

Semua route public sudah dibangun untuk website Odoo native.

### 9.2 Portal controllers

- `portal.py`: portal home dashboard
- `portal_mahasiswa.py`: mahasiswa workflow
- `portal_dosen.py`: dosen workflow
- `portal_base.py`: helper for user role detection

Fungsi ini jelas dan memisahkan ruang akses sesuai peran.

Namun, validasi role-based yang dilakukan dengan `has_group` dan `search` harus ditingkatkan dengan pemeriksaan yang lebih eksplisit di setiap endpoint yang mengubah data atau menampilkan data pribadi.

---

## 10. Findings by category

### 10.1 Good implementation already present

- Modular Odoo architecture
- Use of native `website` and `portal`
- Dedicated public templates and portal templates
- Role separation between student and lecturer flows
- Use of `website.menu` for public navigation
- Search and public inquiry pages for institution information
- Privacy notes and opt-out preference in portal profile

### 10.2 Problems to address

- Visual consistency still uneven across sections and components
- Risk of style collision between website and portal SCSS partials
- Some routes rely on `sudo()` without strong ownership validation
- Portal UX should better follow `CustomerPortal` canonical patterns
- Security review needed on access boundaries and data visibility
- Some internal/admin-only features might remain accessible through custom route logic if not hardened

---

## 11. Recommended design and implementation direction

### 11.1 Website redesign priorities

1. Consolidate design tokens.
2. Standardize typography, spacing, and container widths.
3. Remove decorative or duplicated elements.
4. Align hero, stats, cards, and CTA buttons to a single visual language.
5. Use a predictable section rhythm across all pages.

### 11.2 Portal development priorities

1. Keep portal access user-specific and role-based.
2. Normalize menu pattern and breadcrumb behavior.
3. Ensure all sensitive endpoints validate current user + related record ownership.
4. Improve empty states and dashboard summaries.
5. Use Odoo portal standard layout where possible.

### 11.3 Security hardening priorities

1. Minimize `sudo()` usage for sensitive actions.
2. Add explicit model-level checks before updates.
3. Validate that public pages never expose private record data.
4. Keep access based on `user_id`, `prodi_id`, and `teacher/student profile` instead of broad profile assumptions.
5. Re-audit record rules after any portal expansion.

---

## 12. Implementation plan

### Phase A — Audit closure and design stabilization

- finalize token and palette system
- tidy duplicate styles
- ensure public pages use consistent section headers and cards
- reconcile portal and website styling in a single design vocabulary

### Phase B — Access hardening

- audit every controller method handling writes
- add ownership validation and state checks
- verify `sudo()` calls are necessary and limited
- validate access rules for KRS, KHS, RPS, perwalian, grading

### Phase C — Portal experience refinement

- align dashboard cards with actual data available from models
- add empty states for account not yet linked to academic profile
- standardize page architecture and CTA patterns
- improve quick navigation with role-aware links only

### Phase D — QA and regression check

- run module import validation
- test public route rendering
- test portal route rendering for student and teacher users
- verify access denial for unauthorized records
- confirm static assets compile without CSS conflict

---

## 13. Final assessment

Modul `erpobe` sudah menunjukkan fondasi yang kuat untuk website publik dan portal user yang profesional. Fungsionalitas inti sudah tersedia dan berorientasi pada kebutuhan akademik institusi. Namun, agar sesuai dengan target enterprise-grade redesign dan portal maturity, modul perlu pendekatan yang lebih konsisten pada:

- visual design system
- access hardening
- controller validation
- native portal patterns
- CSS conflict reduction

Dengan fokus tersebut, modul ini berpotensi menjadi website akademik dan portal user yang sangat baik, sekaligus tetap sesuai dengan arsitektur native Odoo 19.
