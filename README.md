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
11. [Konfigurasi Path dan Data Eksternal](#11-konfigurasi-path-dan-data-eksternal)
12. [Berkas yang Dihasilkan](#12-berkas-yang-dihasilkan)
13. [Pemecahan Masalah](#13-pemecahan-masalah)
14. [Catatan Reproduksibilitas dan Lisensi Data](#14-catatan-reproduksibilitas-dan-lisensi-data)
15. [Referensi](#15-referensi)
---

## 1. Gambaran Umum

Proyek ini terdiri atas empat program utama:

| Skrip | Peran |
|---|---|
| `pengolahan.py` | Menghitung prediksi pasang surut 2027–2029 menggunakan GOT4.10 serta validasi silang terhadap EOT20 pada 13 stasiun. |
| `t__tide.py` | Membersihkan data radar dan melakukan analisis harmonik menggunakan T_TIDE. |
| `analisisS.py` | Membandingkan data radar dengan model GOT4.10 dan EOT20, termasuk analisis konstanta harmonik dan sensitivitas ambang kecocokan. |
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
├── pengolahan.py
├── t__tide.py
├── analisisS.py
├── dasbor2026.py
│
├── OLAH/
│   ├── dataPB.xlsx
│   ├── hasil_pasut_2027/                 # dibuat saat pengolahan
│   ├── hasil_pasut_2028/                 # dibuat saat pengolahan
│   ├── hasil_pasut_2029/                 # dibuat saat pengolahan
│   ├── hasil_validasi_eot20_2027/        # dibuat saat pengolahan
│   ├── hasil_validasi_eot20_2028/        # dibuat saat pengolahan
│   └── hasil_validasi_eot20_2029/        # dibuat saat pengolahan
│
├── logo_brin.png
├── logo_dkp_diy.png
├── foto_panduan/
│   ├── nelayan.jpg
│   ├── pemancing.jpg
│   ├── pengelola.jpg
│   └── wisata.jpg
│
├── HASIL_NAN0/                           # dibuat oleh skrip analisis
│   ├── hasil_harmonik_Baron_Jan.xlsx
│   ├── hasil_harmonik_Panggang_Jan.xlsx
│   ├── rekap_semua_bulan.xlsx
│   └── ANALISIS_GABUNGAN_8B_TANPA_DB_SENSITIVITAS/
│       ├── analisis_pasut_gabungan_2026.xlsx
│       └── grafik/
│
└── pytmd_data/                           # model lokal, tidak perlu diunggah
```

**Keterangan struktur:**

- `OLAH/dataPB.xlsx` merupakan berkas masukan pengamatan radar yang digunakan oleh skrip.
- `OLAH/` menjadi folder kerja untuk program prediksi dan validasi.
- `HASIL_NAN0/` digunakan sebagai folder kerja analisis harmonik dan analisis gabungan.
- `logo_brin.png`, `logo_dkp_diy.png`, dan `foto_panduan/` merupakan aset tampilan dashboard. Letakkan pada lokasi tersebut agar dapat ditemukan oleh aplikasi.
- `pytmd_data/` menyimpan data model pasang surut secara lokal. Folder ini tidak perlu diunggah ke repository karena ukuran data model dapat besar.
- Folder hasil di dalam `OLAH/` dan `HASIL_NAN0/` akan dibuat ketika skrip dijalankan. Folder hasil tidak wajib diunggah seluruhnya; cukup siapkan data masukan, skrip, dokumentasi, dan aset yang diperlukan.

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
python -m pip install utide openpyxl
python -m pip install dash dash-leaflet plotly
python -m pip install reportlab
```

`IPython` diperlukan hanya apabila ingin menggunakan fasilitas preview tabel di lingkungan interaktif:

```bash
python -m pip install ipython
```

### 6.3 Instalasi T_TIDE Python (`ttide_py`)

Skrip `t__tide.py` menggunakan modul `ttide_py` melalui pemanggilan `from ttide.t_tide import t_tide`. Panduan pengenalan tersedia pada [artikel Python for Oceanographers](https://ocefpaf.github.io/python4oceanographers/blog/2015/01/19/ttide_py/), sedangkan kode sumbernya tersedia di [repository moflaher/ttide_py](https://github.com/moflaher/ttide_py).

Pasang T_TIDE dari repository sumber berikut. Pastikan environment Python proyek sudah aktif.

**Cara A — menggunakan Git**

1. Unduh kode sumber:

   ```bash
   git clone https://github.com/moflaher/ttide_py.git
   ```

2. Masuk ke folder hasil unduhan:

   ```bash
   cd ttide_py
   ```

**Cara B — tanpa Git**

1. Buka [repository ttide_py](https://github.com/moflaher/ttide_py).
2. Klik tombol **Code**, lalu pilih **Download ZIP**.
3. Ekstrak ZIP, kemudian buka terminal pada folder hasil ekstraksi yang berisi file `setup.py`.

Setelah menggunakan salah satu cara di atas, instal paket ke environment Python yang sedang aktif:

   ```bash
   python -m pip install .
   ```

   Jika cara tersebut tidak berhasil, repository sumber juga menyediakan instalasi menggunakan `setup.py`:

   ```bash
   python setup.py install
   ```

4. Kembali ke folder proyek dashboard, lalu uji apakah modul dapat diimpor:

   ```bash
   python -c "from ttide.t_tide import t_tide; print('T_TIDE berhasil diimpor')"
   ```

Pastikan proses instalasi dan pengujian menggunakan interpreter Python yang sama dengan yang digunakan untuk menjalankan skrip. Repository `ttide_py` menyebutkan bahwa proyek ini merupakan konversi T_TIDE yang masih dalam pengembangan dan pengujiannya terbatas. Oleh karena itu, lakukan pengujian pada environment yang digunakan sebelum menjalankan keseluruhan proses.

### 6.4 Periksa library

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

Jalankan `t__tide.py` pada tahap kedua untuk menyiapkan data harmonik radar yang digunakan oleh dashboard. Pastikan lokasi folder hasil tetap mengikuti struktur repository pada bagian 4.

---

## 8. Metode Pengolahan

### 8.1 Prediksi dan validasi silang — `pengolahan.py`

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

### 8.2 Analisis harmonik data radar — `t__tide.py`

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

### 8.3 Analisis radar terhadap GOT4.10 dan EOT20 — `analisisS.py`

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

Jalankan keempat program secara berurutan. Pastikan data masukan, library, dan model pasang surut yang diperlukan sudah disiapkan.

### Tahap 1 — Prediksi pasang surut dan validasi silang GOT4.10–EOT20

```bash
python pengolahan.py
```

Program menjalankan pengolahan prediksi pasang surut tahun 2027, 2028, dan 2029 pada 13 stasiun. Model GOT4.10 disiapkan melalui pyTMD, sedangkan validasi EOT20 dijalankan apabila data model EOT20 sudah tersedia.

### Tahap 2 — Analisis harmonik data radar menggunakan T_TIDE

```bash
python t__tide.py
```

Program membaca data radar dari `OLAH/dataPB.xlsx`. Pastikan T_TIDE Python sudah berhasil dipasang dan dapat diimpor sebelum menjalankan tahap ini.

### Tahap 3 — Analisis radar terhadap GOT4.10 dan EOT20

```bash
python analisisS.py
```

Program menjalankan analisis gabungan data radar dan model, termasuk perbandingan deret waktu, konstanta harmonik, metrik statistik, dan sensitivitas ambang kecocokan.

### Tahap 4 — Menjalankan dashboard

```bash
python dasbor2026.py
```

Buka alamat berikut melalui browser:

```text
http://127.0.0.1:8050/
```

**Catatan:** dashboard membaca berkas yang sudah tersedia dari tahapan sebelumnya. Jika suatu menu belum menampilkan data, periksa apakah tahap terkait sudah dijalankan dan berkas yang dibutuhkan tersedia pada folder yang sesuai.

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

## 11. Konfigurasi Path dan Data Eksternal

Agar proyek dapat dijalankan dari lokasi folder yang berbeda, gunakan path relatif terhadap lokasi file Python. Dengan pendekatan ini, folder proyek dapat disimpan di `Documents`, `Projects`, atau drive lain tanpa menuliskan alamat folder komputer secara permanen di dalam skrip.

Contoh penentuan folder dasar:

```python
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
OLAH_DIR = BASE_DIR / "OLAH"
HASIL_DIR = BASE_DIR / "HASIL_NAN0"
MODEL_DIR = BASE_DIR / "pytmd_data"
```

Python akan mencari folder `OLAH`, `HASIL_NAN0`, dan `pytmd_data` berdasarkan lokasi file skrip. Karena itu, pertahankan susunan folder proyek seperti pada bagian 4.

Dashboard juga menyediakan environment variable untuk menentukan sumber hasil analisis radar dan folder T_TIDE secara eksplisit jika diperlukan.

**Windows Command Prompt:**

```bat
set PASUT_RADAR_XLSX=lokasi_folder_proyek\HASIL_NAN0\ANALISIS_GABUNGAN_8B_TANPA_DB_SENSITIVITAS\analisis_pasut_gabungan_2026.xlsx
set PASUT_TTIDE_DIR=lokasi_folder_proyek\HASIL_NAN0
python dasbor2026.py
```

**PowerShell:**

```powershell
$env:PASUT_RADAR_XLSX = "lokasi_folder_proyek\HASIL_NAN0\ANALISIS_GABUNGAN_8B_TANPA_DB_SENSITIVITAS\analisis_pasut_gabungan_2026.xlsx"
$env:PASUT_TTIDE_DIR = "lokasi_folder_proyek\HASIL_NAN0"
python dasbor2026.py
```

Ganti `lokasi_folder_proyek` dengan lokasi folder proyek pada komputer yang digunakan. Pengaturan environment variable hanya diperlukan apabila file tidak ditemukan secara otomatis oleh dashboard.

---

## 12. Berkas yang Dihasilkan

Folder hasil pengolahan akan dibuat oleh program sesuai tahapan yang dijalankan. Folder tersebut dapat disimpan secara lokal dan tidak harus diunggah seluruhnya ke GitHub. Untuk menjalankan dashboard, pastikan berkas yang dibutuhkan oleh menu dashboard sudah tersedia pada lokasi yang sesuai.

---

## 13. Pemecahan Masalah

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

## 14. Catatan Reproduksibilitas dan Lisensi Data

- Hasil pengolahan bergantung pada versi library, berkas model, data masukan, konfigurasi parameter, dan koordinat stasiun.
- Catat versi Python dan library pada setiap rilis agar proses dapat direproduksi.
- Jangan mengunggah kata sandi, token, kredensial, atau data privat.
- Periksa ketentuan distribusi data radar dan model sebelum mengunggah data mentah atau berkas model ke repository publik.
- Untuk model EOT20, ikuti ketentuan penggunaan dan atribusi dari sumber PANGAEA.
- Repository publik tidak otomatis memberikan lisensi penggunaan ulang. Tambahkan berkas `LICENSE` setelah menentukan lisensi yang sesuai dan memiliki hak untuk melisensikan kode/data terkait.
- Berkas model NetCDF dan hasil antara berukuran besar sebaiknya disimpan di penyimpanan terpisah atau Git LFS jika memang perlu dikelola melalui Git.

---

## 15. Referensi

1. pyTMD — https://github.com/pyTMD/pyTMD
2. Dokumentasi pyTMD — https://pytmd.readthedocs.io/
3. PANGAEA EOT20 — https://doi.org/10.17882/79489
4. UTide — https://github.com/wesleybowman/UTide
5. T_TIDE Python (`ttide_py`) — https://github.com/moflaher/ttide_py
6. Python for Oceanographers, “t_tide for python” — https://ocefpaf.github.io/python4oceanographers/blog/2015/01/19/ttide_py/
7. UTide — https://github.com/wesleybowman/UTide
8. Plotly Dash — https://dash.plotly.com/
9. dash-leaflet — https://github.com/emilhe/dash-leaflet
10. ReportLab — https://www.reportlab.com/docs/reportlab-userguide.pdf

---

**Dashboard Analisis, Prediksi, dan Validasi Pasang Surut**  
Pengolahan data radar 2026 dan prediksi pasang surut 2027–2029.


