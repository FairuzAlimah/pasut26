# Dashboard Analisis, Prediksi, dan Validasi Pasang Surut

**Analisis data radar 2026, prediksi pasang surut 2027–2029, serta validasi model GOT4.10 dan EOT20 di wilayah pesisir selatan Yogyakarta.**

---

## Daftar Isi

1. [Gambaran Umum](#1-gambaran-umum)
2. [Fitur](#2-fitur)
3. [Teknologi dan Library](#3-teknologi-dan-library)
4. [Struktur Repository](#4-struktur-repository)
5. [Persiapan Komputer](#5-persiapan-komputer)
6. [Instalasi Library](#6-instalasi-library)
7. [Persiapan Data dan Model Pasut](#7-persiapan-data-dan-model-pasut)
8. [Metode Pengolahan](#8-metode-pengolahan)
9. [Urutan Menjalankan Program](#9-urutan-menjalankan-program)
10. [Menjalankan Dashboard](#10-menjalankan-dashboard)
11. [Menghubungkan dan Mengunggah Proyek ke GitHub](#11-menghubungkan-dan-mengunggah-proyek-ke-github)
12. [Konfigurasi Path dan Data Eksternal](#12-konfigurasi-path-dan-data-eksternal)
13. [Keluaran Program](#13-keluaran-program)
14. [Pemecahan Masalah](#14-pemecahan-masalah)
15. [Catatan Reproduksibilitas dan Lisensi Data](#15-catatan-reproduksibilitas-dan-lisensi-data)
16. [Referensi](#16-referensi)

---

## 1. Gambaran Umum

Proyek ini terdiri atas empat program utama:

| Skrip | Peran |
|---|---|
| `t__tide.py` | Membersihkan data radar dan melakukan analisis harmonik menggunakan T_TIDE. |
| `analisisS.py` | Membandingkan data radar dengan model GOT4.10 dan EOT20, termasuk analisis konstanta harmonik dan sensitivitas ambang kecocokan. |
| `pengolahan.py` | Menghitung prediksi pasang surut 2027–2029 menggunakan GOT4.10 serta validasi silang terhadap EOT20 pada 13 stasiun. |
| `dasbor2026.py` | Membaca hasil pengolahan, menyajikan dashboard interaktif, peta, grafik, tabel, dan ekspor laporan PDF. |

### Cakupan analisis

- **Analisis radar:** Januari–Agustus 2026.
- **Stasiun radar:** Baron dan Panggang (Gesing).
- **Prediksi model:** tahun 2027, 2028, dan 2029.
- **Stasiun prediksi:** 13 titik di pesisir selatan Yogyakarta.
- **Model pasut:** GOT4.10 dan EOT20.
- **Dashboard:** prediksi 2027–2029, validasi GOT4.10–EOT20, validasi radar 2026, analisis harmonik, dan panduan pemanfaatan sesuai ketersediaan berkas hasil.

---

## 2. Fitur

- Pengolahan data pengamatan radar dengan pemeriksaan kualitas (*quality control/QC*).
- Analisis harmonik radar menggunakan T_TIDE dan UTide sebagai sumber cadangan pada skrip analisis gabungan.
- Perbandingan elevasi radar terhadap prediksi GOT4.10 dan EOT20.
- Perhitungan RMSE, MAE, korelasi Pearson, Willmott's Index of Agreement, dan analisis lag.
- Perbandingan amplitudo dan fase konstanta harmonik.
- Analisis sensitivitas ambang kecocokan konstanta harmonik.
- Prediksi pasang surut per jam untuk 2027–2029.
- Validasi silang GOT4.10 terhadap EOT20.
- Statistik mingguan, grafik, peta stasiun, tabel, dan ekspor PDF pada dashboard.

---

## 3. Teknologi dan Library

| Komponen | Kegunaan |
|---|---|
| Python | Bahasa pemrograman utama |
| NumPy | Operasi numerik dan array |
| Pandas | Pengelolaan data tabular dan deret waktu |
| SciPy | Statistik dan perhitungan numerik |
| Matplotlib | Pembuatan grafik hasil pengolahan |
| pyTMD | Perhitungan prediksi pasang surut berbasis model global |
| timescale | Pembuatan rentang waktu untuk prediksi |
| T_TIDE (`ttide`) | Analisis harmonik data radar |
| UTide | Analisis harmonik alternatif/cadangan pada `analisisS.py` |
| OpenPyXL | Membaca dan menulis berkas Excel |
| Plotly | Grafik interaktif dashboard |
| Dash | Kerangka aplikasi dashboard |
| dash-leaflet | Peta interaktif |
| ReportLab | Pembuatan laporan PDF |
| IPython | Preview tabel ketika skrip dijalankan di lingkungan interaktif (opsional) |

---

## 4. Struktur Repository

Struktur yang disarankan untuk repository:

```text
dashboard-pasut-radar-pytmd/
│
├── README.md
├── requirements.txt
├── .gitignore
│
├── analisisS.py
├── pengolahan.py
├── t__tide.py
├── dasbor2026.py
│
├── OLAH/
│   ├── dataPB.xlsx
│   ├── hasil_pasut_2027/
│   ├── hasil_pasut_2028/
│   ├── hasil_pasut_2029/
│   ├── hasil_validasi_eot20_2027/
│   ├── hasil_validasi_eot20_2028/
│   └── hasil_validasi_eot20_2029/
│
├── logo_brin.png
├── logo_dkp_diy.png
├── foto_panduan/
│   ├── nelayan.jpg
│   ├── pemancing.jpg
│   ├── pengelola.jpg
│   └── wisata.jpg
│
├── HASIL_NAN0/
│   ├── hasil_harmonik_Baron_Jan.xlsx
│   ├── hasil_harmonik_Panggang_Jan.xlsx
│   ├── rekap_semua_bulan.xlsx
│   └── ANALISIS_GABUNGAN_8B_TANPA_DB_SENSITIVITAS/
│       ├── analisis_pasut_gabungan_2026.xlsx
│       └── grafik hasil analisis
│
└── pytmd_data/                 # data model lokal; tidak disarankan diunggah
```

**Catatan struktur:**

1. `OLAH/dataPB.xlsx` merupakan lokasi yang dicari oleh `analisisS.py` dan `t__tide.py`. `pengolahan.py` menggunakan folder `OLAH` untuk menyimpan hasil prediksi dan validasi.
2. `HASIL_NAN0/` merupakan folder keluaran `t__tide.py` dan `analisisS.py`.
3. `dasbor2026.py` mencari hasil prediksi dan validasi pada subfolder `OLAH`, serta hasil analisis radar dan harmonik pada `HASIL_NAN0`.
4. Dashboard mencari `logo_brin.png` dan `logo_dkp_diy.png` di folder yang sama dengan skrip dashboard, serta folder `foto_panduan` pada lokasi tersebut. Sesuaikan lokasi aset atau fungsi pencarian aset apabila struktur repository diubah.
5. `pytmd_data/` berisi data model yang dapat berukuran besar. Simpan di komputer lokal dan jangan mengunggah seluruh direktori model ke repository biasa.
6. Folder hasil hanya perlu berisi keluaran yang dibutuhkan untuk menjalankan dashboard atau yang memang ingin dibagikan. Hasil mentah/antara yang besar dapat disimpan di penyimpanan terpisah.

---

## 5. Persiapan Komputer

### 5.1 Perangkat lunak

Siapkan:

- Windows 10/11, Linux, atau macOS.
- Python 3.10 atau versi yang kompatibel dengan versi pyTMD dan library yang digunakan.
- Anaconda/Miniconda atau Python resmi.
- Git.
- Akun GitHub.

Periksa instalasi Python dan Git melalui terminal/Anaconda Prompt:

```bash
python --version
python -m pip --version
git --version
```

### 5.2 Unduh repository

Setelah repository dibuat di GitHub:

```bash
git clone https://github.com/USERNAME/REPOSITORY.git
cd REPOSITORY
```

Ganti `USERNAME` dan `REPOSITORY` sesuai alamat repository milik pengguna.

Alternatif tanpa Git: buka halaman repository, pilih **Code → Download ZIP**, lalu ekstrak berkasnya.

### 5.3 Buat lingkungan virtual

Menggunakan `venv`:

```bash
python -m venv .venv
```

Aktifkan pada Windows:

```bash
.venv\Scripts\activate
```

Aktifkan pada Linux/macOS:

```bash
source .venv/bin/activate
```

Jika menggunakan Anaconda:

```bash
conda create -n pasut python=3.11 -y
conda activate pasut
```

Gunakan satu lingkungan Python yang sama untuk instalasi library, pengolahan, dan dashboard agar tidak terjadi perbedaan interpreter.

---

## 6. Instalasi Library

### 6.1 Perbarui pip

```bash
python -m pip install --upgrade pip
```

### 6.2 Instalasi seluruh library

```bash
python -m pip install -r requirements.txt
```

Jika instalasi dilakukan satu per satu:

```bash
python -m pip install numpy pandas scipy matplotlib
python -m pip install pyTMD timescale
python -m pip install utide ttide openpyxl
python -m pip install dash dash-leaflet plotly
python -m pip install reportlab
```

`IPython` diperlukan hanya apabila ingin menggunakan fasilitas preview tabel di lingkungan interaktif:

```bash
python -m pip install ipython
```

**Catatan T_TIDE:** skrip memanggil `from ttide.t_tide import t_tide`. Pastikan paket/distribusi T_TIDE yang dipasang benar-benar menyediakan modul tersebut. Nama distribusi paket pada pengelola paket dapat berbeda dari nama modul Python. Jika instalasi `ttide` dari PyPI tidak menyediakan modul yang sesuai, gunakan distribusi T_TIDE yang menjadi sumber lingkungan kerja proyek dan dokumentasikan versi/asal instalasinya.

### 6.3 Periksa library

```bash
python -c "import numpy, pandas, scipy, matplotlib, pyTMD, timescale, utide, dash, dash_leaflet, plotly, reportlab; print('Library utama berhasil diimpor')"
```

Periksa T_TIDE secara terpisah:

```bash
python -c "from ttide.t_tide import t_tide; print('T_TIDE berhasil diimpor')"
```

Jika terjadi `ModuleNotFoundError`, periksa interpreter yang sedang aktif:

```bash
python -c "import sys; print(sys.executable)"
```

---

## 7. Persiapan Data dan Model Pasut

### 7.1 Data radar

Letakkan data pengamatan radar dengan nama:

```text
OLAH/dataPB.xlsx
```

Skrip `analisisS.py` dan `t__tide.py` membaca data tersebut. Data harus memiliki lembar kerja (*sheet*) untuk stasiun dan bulan yang sesuai dengan pola nama yang dikenali program.

Stasiun yang digunakan:

- Baron.
- Panggang (Gesing).

Periode yang dikonfigurasi pada `analisisS.py` adalah Januari–Agustus 2026. Pastikan format waktu, kolom elevasi radar, satuan, dan keterangan zona waktu pada lembar kerja sesuai dengan data sumber.

### 7.2 Model GOT4.10

Model GOT4.10 diunduh melalui fungsi pyTMD pada `pengolahan.py`:

```python
pyTMD.datasets.fetch_gsfc_got(
    "GOT4.10",
    directory=MODEL_DIR,
    format="netcdf"
)
```

Model akan disimpan di folder `pytmd_data/` relatif terhadap lokasi skrip.

### 7.3 Model EOT20

Pada program ini, EOT20 tidak diunduh secara otomatis oleh `pengolahan.py`. Unduh arsip model dari PANGAEA:

- DOI: https://doi.org/10.17882/79489

Setelah diunduh dan diekstrak, pastikan susunan direktori mengikuti pola berikut:

```text
pytmd_data/
└── EOT20/
    ├── ocean_tides/
    │   └── *.nc
    └── load_tides/
        └── *.nc
```

Folder `ocean_tides` diperlukan untuk perhitungan pasang surut laut pada proses validasi. Program memeriksa ketersediaan berkas NetCDF EOT20 sebelum menjalankan bagian validasi silang. Jika model tidak tersedia, bagian validasi EOT20 akan dilewati dan program memberikan informasi pada terminal.

### 7.4 Data hasil T_TIDE

Untuk mengisi informasi harmonik radar pada dashboard, jalankan `t__tide.py` terlebih dahulu. Skrip menghasilkan berkas seperti:

```text
HASIL_NAN0/
├── hasil_harmonik_Baron_Jan.xlsx
├── hasil_harmonik_Panggang_Jan.xlsx
├── rekap_semua_bulan.xlsx
└── tabel_elevasi_muka_laut.xlsx
```

Nama berkas aktual mengikuti stasiun dan bulan yang berhasil diproses.

---

## 8. Metode Pengolahan

### 8.1 Analisis harmonik data radar — `t__tide.py`

Skrip ini mengolah data radar dari interval pengamatan satu menit menjadi deret waktu per jam, kemudian melakukan analisis harmonik menggunakan T_TIDE.

Tahapan pengolahan:

1. Membaca data waktu, kanal baterai, dan elevasi radar dari Excel.
2. Menghapus waktu yang tidak valid dan waktu duplikat.
3. Melakukan pemeriksaan lonjakan (*spike*) menggunakan median bergerak 31 menit. Nilai yang menyimpang lebih dari 1,5 m terhadap median ditandai sebagai spike.
4. Mengubah data menjadi interval per jam dengan kebutuhan minimal 10 sampel pada setiap kelompok jam.
5. Menginterpolasi kekosongan data yang memenuhi batas maksimum 12 jam.
6. Menghitung analisis harmonik menggunakan fungsi `t_tide`.
7. Menghitung rasio sinyal terhadap derau (*Signal-to-Noise Ratio/SNR*) menggunakan `(amplitudo / error amplitudo)^2`.
8. Menandai konstanta harmonik signifikan jika SNR lebih besar dari 1.
9. Menghitung Formzahl untuk mengidentifikasi tipe pasang surut apabila konstanta penyusunnya tersedia.
10. Menghitung parameter elevasi penting dan menyimpan tabel serta grafik.

Pada konfigurasi saat ini, nilai NaN yang masih tersisa pada anomali diubah menjadi 0 sebelum masuk ke T_TIDE. Nilai 0 tersebut merepresentasikan anomali terhadap rata-rata, bukan hasil pengamatan baru.

Parameter elevasi yang dihitung mencakup Z0, S0/MSL, HHWL, MHWL, LLWL, dan MLWL. Rumus dan konstanta penyusunnya mengikuti konfigurasi pada skrip.

### 8.2 Analisis radar terhadap GOT4.10 dan EOT20 — `analisisS.py`

Skrip ini membandingkan data pengamatan radar dengan hasil model pasang surut GOT4.10 dan EOT20 untuk stasiun Baron dan Panggang selama Januari–Agustus 2026.

Tahapan utama:

1. Membaca data radar dari `OLAH/dataPB.xlsx`.
2. Mengidentifikasi sheet berdasarkan nama stasiun dan bulan.
3. Melakukan QC untuk mendeteksi nilai macet dan lonjakan.
4. Mengubah data radar menjadi rata-rata per jam.
5. Menginterpolasi kekosongan data sesuai batas konfigurasi.
6. Menyesuaikan waktu data ke UTC.
7. Membaca konstanta harmonik radar dari hasil T_TIDE. Jika berkas tidak ditemukan dan pengaturan cadangan aktif, konstanta dihitung menggunakan UTide.
8. Mengekstrak konstanta harmonik dari GOT4.10 dan EOT20.
9. Membandingkan deret waktu radar dan model pada waktu yang sama.
10. Menghitung metrik statistik dan membandingkan amplitudo serta fase konstanta harmonik.
11. Melakukan analisis sensitivitas ambang kecocokan konstanta.
12. Menyimpan ringkasan, detail, grafik, dan berkas Excel.

Parameter QC utama yang dikonfigurasi:

| Parameter | Nilai |
|---|---:|
| Jendela median bergerak | 31 menit |
| Batas robust sigma | 4 |
| Ambang minimum lonjakan | 0,5 m |
| Durasi nilai datar untuk dianggap macet | 30 menit |
| Sampel minimum per jam | 20 |
| Batas interpolasi | 6 jam |
| Lag maksimum yang diperiksa | 8 jam |
| SNR minimum | 1 |

Metrik perbandingan:

- **RMSE:** akar dari rata-rata kuadrat selisih antara data radar dan model.
- **MAE:** rata-rata nilai absolut selisih.
- **Pearson r:** tingkat korelasi linear antara dua deret.
- **Willmott's d:** indeks kesesuaian antara dua deret.
- **Lag:** pergeseran waktu yang menghasilkan kecocokan korelasi terbaik dalam batas pencarian program.

Analisis sensitivitas menggunakan tiga skenario ambang:

| Skenario | Selisih amplitudo | Selisih amplitudo relatif | Selisih fase |
|---|---:|---:|---:|
| Ketat | 1 cm | 10% | 10° |
| Dasar | 2 cm | 20% | 20° |
| Longgar | 3 cm | 30% | 30° |

Aturan kecocokan yang digunakan adalah selisih amplitudo memenuhi batas absolut **atau** batas relatif, serta selisih fase memenuhi batas skenario.

### 8.3 Prediksi dan validasi silang — `pengolahan.py`

Skrip ini menghasilkan prediksi pasang surut per jam untuk tahun 2027, 2028, dan 2029 menggunakan GOT4.10, serta membandingkannya dengan EOT20.

Stasiun yang dikonfigurasi:

1. Congot
2. Glagah
3. Bugel
4. Trisik
5. Ngenthak
6. Kuwaru
7. Goa Cemara
8. Samas
9. Depok
10. Baron
11. Jungwok
12. Sadeng
13. Gesing

Tahapan pengolahan:

1. Memeriksa dan mengunduh model GOT4.10 melalui pyTMD.
2. Memeriksa posisi stasiun menggunakan *tide mask*.
3. Jika koordinat awal tidak berada pada sel laut yang valid, program mencari titik laut terdekat dalam radius pencarian yang dikonfigurasi.
4. Membuat deret waktu per jam untuk setiap tahun.
5. Menghitung prediksi elevasi pasang surut GOT4.10.
6. Menyimpan data prediksi bulanan dalam CSV dan grafik mingguan.
7. Menghitung statistik mingguan, termasuk nilai minimum, maksimum, rata-rata, rentang, dan jumlah data valid.
8. Memeriksa ketersediaan EOT20.
9. Menghitung EOT20 untuk satu tahun dan menyimpan hasilnya dalam cache per stasiun agar pembacaan model tidak diulang untuk setiap bulan.
10. Membandingkan GOT4.10 dan EOT20 pada waktu yang sama.
11. Menghitung metrik validasi dan menyimpan CSV, grafik, serta metadata sumber pengolahan.

Validasi GOT4.10–EOT20 merupakan validasi silang antar-model, bukan validasi terhadap pengamatan lapangan. Interpretasi hasil harus mempertimbangkan bahwa kedua model merupakan produk model pasang surut.

### 8.4 Dashboard — `dasbor2026.py`

Dashboard menggunakan hasil pengolahan yang telah tersimpan sebagai berkas, bukan menjalankan ulang seluruh perhitungan model setiap kali halaman dibuka.

Komponen dashboard meliputi:

- Menu prediksi pasang surut tahun 2027–2029.
- Peta interaktif lokasi stasiun.
- Grafik dan statistik mingguan.
- Menu validasi GOT4.10 terhadap EOT20.
- Menu validasi data radar 2026 terhadap GOT4.10 dan EOT20.
- Informasi konstanta harmonik dan parameter elevasi penting jika hasil T_TIDE tersedia.
- Panduan pemanfaatan.
- Ekspor laporan PDF, termasuk grafik dan informasi stasiun sesuai menu yang dipilih.

Dashboard dijalankan pada alamat lokal `http://127.0.0.1:8050/`.

---

## 9. Urutan Menjalankan Program

Pastikan seluruh data masukan dan model sudah tersedia sebelum menjalankan skrip.

### Tahap 1 — Analisis harmonik radar

```bash
python t__tide.py
```

Hasilnya disimpan pada `HASIL_NAN0/`, termasuk berkas konstanta harmonik dan rekap.

### Tahap 2 — Analisis radar vs model dan sensitivitas

```bash
python analisisS.py
```

Hasilnya disimpan pada:

```text
HASIL_NAN0/ANALISIS_GABUNGAN_8B_TANPA_DB_SENSITIVITAS/
```

Pastikan berkas Excel `analisis_pasut_gabungan_2026.xlsx` berhasil terbentuk.

### Tahap 3 — Prediksi 2027–2029 dan validasi EOT20

```bash
python pengolahan.py
```

Program memproses tahun yang terdaftar pada `YEARS = [2027, 2028, 2029]`. Proses dapat memerlukan waktu dan memori cukup besar karena perhitungan model dilakukan untuk banyak stasiun dan waktu.

### Tahap 4 — Jalankan dashboard

```bash
python dasbor2026.py
```

Buka alamat berikut jika peramban tidak terbuka otomatis:

```text
http://127.0.0.1:8050/
```

Hentikan dashboard melalui terminal dengan `Ctrl + C`.

**Penting:** dashboard memerlukan hasil pengolahan yang sesuai. Jika berkas prediksi, validasi, Excel analisis radar, atau hasil harmonik belum tersedia, menu terkait dapat kosong atau menampilkan peringatan. Jalankan tahapan pengolahan terlebih dahulu.

---

## 10. Menjalankan Dashboard

Dashboard berbasis Dash merupakan aplikasi web Python. Untuk menjalankannya:

1. Aktifkan lingkungan Python.
2. Pindah ke direktori repository.
3. Pastikan folder hasil pengolahan sudah tersedia.
4. Jalankan `python dasbor2026.py`.
5. Buka `http://127.0.0.1:8050/`.

Dashboard berjalan pada komputer yang menjalankan Python. Pengguna lain tidak dapat mengaksesnya hanya dengan membuka repository GitHub.

### Jika ingin dashboard dapat diakses publik

Terdapat dua pendekatan:

- **Hosting aplikasi Python:** deploy aplikasi Dash ke layanan hosting yang mendukung proses Python dan server web. Siapkan kebutuhan penyimpanan hasil, aset, model, dan konfigurasi environment.
- **Dashboard statis:** buat lapisan tampilan HTML/CSS/JavaScript yang membaca CSV/JSON hasil pengolahan, kemudian publikasikan melalui GitHub Pages. Pendekatan ini memerlukan pengembangan atau konversi dashboard; skrip Dash saat ini tidak otomatis menjadi website GitHub Pages.

---

## 11. Menghubungkan dan Mengunggah Proyek ke GitHub

### 11.1 Buat repository

1. Masuk ke https://github.com/.
2. Klik **New repository**.
3. Isi nama repository, misalnya `dashboard-pasut-radar-pytmd`.
4. Tambahkan deskripsi proyek.
5. Pilih Public atau Private sesuai kebutuhan.
6. Klik **Create repository**.

Jika folder proyek lokal sudah berisi berkas, repository dapat dibuat tanpa menambahkan README otomatis agar tidak terjadi konflik berkas awal.

### 11.2 Hubungkan folder lokal ke GitHub

Buka terminal pada folder proyek:

```bash
git init
git branch -M main
git add README.md requirements.txt .gitignore
git add analisisS.py pengolahan.py t__tide.py dasbor2026.py
git add OLAH
git add logo_brin.png logo_dkp_diy.png foto_panduan
git commit -m "Initial commit: dashboard analisis pasang surut"
```

Tambahkan alamat repository:

```bash
git remote add origin https://github.com/USERNAME/REPOSITORY.git
```

Unggah:

```bash
git push -u origin main
```

Ganti alamat tersebut dengan URL repository yang benar.

### 11.3 Pembaruan berikutnya

Setelah mengubah kode atau dokumentasi:

```bash
git status
git add .
git commit -m "Update pengolahan dan dashboard pasang surut"
git push
```

Sebelum menggunakan `git add .`, periksa kembali agar model berukuran besar, lingkungan virtual, data privat, dan berkas sementara tidak ikut terunggah.

### 11.4 Alternatif menggunakan GitHub Desktop

Jika tidak ingin menggunakan terminal:

1. Instal GitHub Desktop.
2. Login menggunakan akun GitHub.
3. Pilih **Add an Existing Repository** atau **Create a New Repository**.
4. Pilih folder proyek.
5. Isi ringkasan perubahan (*summary*).
6. Klik **Commit to main**.
7. Klik **Publish repository** atau **Push origin**.

---

## 12. Konfigurasi Path dan Data Eksternal

Skrip menggunakan `Path(__file__).resolve().parent` untuk menentukan folder dasar berdasarkan lokasi skrip. Dengan demikian, folder proyek dapat dipindahkan ke komputer lain tanpa mengubah path absolut seperti `D:\MAGANG`.

Struktur dasar yang diharapkan:

```python
BASE_DIR = Path(__file__).resolve().parent
MODEL_DIR = BASE_DIR / "pytmd_data"
OLAH_DIR = BASE_DIR / "OLAH"
```

Dashboard juga menyediakan environment variable untuk memilih sumber hasil analisis radar dan folder T_TIDE secara eksplisit:

**Windows Command Prompt:**

```bat
set PASUT_RADAR_XLSX=C:\lokasi\hasil\analisis_pasut_gabungan_2026.xlsx
set PASUT_TTIDE_DIR=C:\lokasi\HASIL_NAN0
python dasbor2026.py
```

**PowerShell:**

```powershell
$env:PASUT_RADAR_XLSX = "C:\lokasi\hasil\analisis_pasut_gabungan_2026.xlsx"
$env:PASUT_TTIDE_DIR = "C:\lokasi\HASIL_NAN0"
python dasbor2026.py
```

Sesuaikan lokasi dengan komputer masing-masing. Environment variable tersebut hanya diperlukan jika hasil tidak berada pada lokasi yang berhasil ditemukan otomatis oleh dashboard.

---

## 13. Keluaran Program

### `t__tide.py`

- Berkas Excel konstanta harmonik per stasiun dan bulan.
- Rekapitulasi harmonik seluruh periode yang berhasil diproses.
- Tabel elevasi penting.
- Grafik prediksi, residu, amplitudo, fase, dan konstanta signifikan.

### `analisisS.py`

- `analisis_pasut_gabungan_2026.xlsx`.
- Ringkasan perbandingan deret waktu.
- Ringkasan dan detail konstanta harmonik.
- Ringkasan sensitivitas skenario ketat, dasar, dan longgar.
- Grafik deret waktu, sebaran, konstanta, dan rekapitulasi.

### `pengolahan.py`

- CSV prediksi GOT4.10 per stasiun dan bulan.
- Grafik mingguan.
- CSV koordinat stasiun.
- CSV statistik mingguan.
- CSV hasil validasi GOT4.10 terhadap EOT20.
- Grafik validasi.
- Ringkasan metrik dan metadata provenance.

### `dasbor2026.py`

- Dashboard interaktif berbasis browser lokal.
- Peta lokasi stasiun.
- Grafik dan tabel sesuai menu.
- Laporan PDF sesuai fitur yang tersedia.

---

## 14. Pemecahan Masalah

| Kendala | Penyebab yang mungkin | Solusi |
|---|---|---|
| `ModuleNotFoundError` | Library belum terpasang pada interpreter aktif | Aktifkan environment yang benar dan jalankan `python -m pip install -r requirements.txt`. |
| `dataPB.xlsx` tidak ditemukan | Lokasi atau nama berkas tidak sesuai | Letakkan di `OLAH/dataPB.xlsx`. |
| Model GOT4.10 gagal diunduh | Koneksi internet atau layanan sumber model bermasalah | Periksa koneksi dan jalankan ulang pemeriksaan model. |
| EOT20 tidak ditemukan | Model belum diunduh atau struktur folder salah | Periksa `pytmd_data/EOT20/ocean_tides/`. |
| Hasil T_TIDE tidak ditemukan | `t__tide.py` belum dijalankan atau nama berkas tidak sesuai | Jalankan analisis harmonik dan periksa `HASIL_NAN0/`. |
| Menu validasi radar kosong | Excel gabungan radar belum tersedia atau belum terbaca | Jalankan `analisisS.py` dan periksa `analisis_pasut_gabungan_2026.xlsx`. |
| Menu prediksi kosong | CSV hasil prediksi belum tersedia | Jalankan `pengolahan.py` untuk tahun yang diperlukan. |
| Logo tidak tampil | Lokasi aset berbeda dari lokasi pencarian dashboard | Letakkan logo di folder skrip atau sesuaikan fungsi pencarian aset. |
| PDF gagal dibuat | Library ReportLab atau gambar pendukung bermasalah | Periksa instalasi ReportLab dan lokasi gambar. |
| Port 8050 digunakan | Ada aplikasi lain yang memakai port tersebut | Tutup aplikasi lain atau ubah port pada bagian `app.run`. |
| Memori tidak cukup | Proses model dan deret waktu berukuran besar | Tutup aplikasi lain, proses tahun secara bertahap, dan gunakan komputer dengan RAM memadai. |

---

## 15. Catatan Reproduksibilitas dan Lisensi Data

- Hasil pengolahan bergantung pada versi library, berkas model, data masukan, konfigurasi parameter, dan koordinat stasiun.
- Catat versi Python dan library pada setiap rilis agar proses dapat direproduksi.
- Jangan mengunggah kata sandi, token, kredensial, atau data privat.
- Periksa ketentuan distribusi data radar dan model sebelum mengunggah data mentah atau berkas model ke repository publik.
- Untuk model EOT20, ikuti ketentuan penggunaan dan atribusi dari sumber PANGAEA.
- Repository publik tidak otomatis memberikan lisensi penggunaan ulang. Tambahkan berkas `LICENSE` setelah menentukan lisensi yang sesuai dan memiliki hak untuk melisensikan kode/data terkait.
- Berkas model NetCDF dan hasil antara berukuran besar sebaiknya disimpan di penyimpanan terpisah atau Git LFS jika memang perlu dikelola melalui Git.

---

## 16. Referensi

1. pyTMD — https://github.com/pyTMD/pyTMD
2. Dokumentasi pyTMD — https://pytmd.readthedocs.io/
3. PANGAEA EOT20 — https://doi.org/10.17882/79489
4. UTide — https://github.com/wesleybowman/UTide
5. T_TIDE — dokumentasi/distribusi paket yang digunakan pada lingkungan pengolahan.
6. Plotly Dash — https://dash.plotly.com/
7. dash-leaflet — https://github.com/emilhe/dash-leaflet
8. ReportLab — https://www.reportlab.com/docs/reportlab-userguide.pdf

---

**Dashboard Analisis, Prediksi, dan Validasi Pasang Surut**  
Pengolahan data radar 2026 dan prediksi pasang surut 2027–2029.

