<div align="center">
   
# Dashboard Analisis, Prediksi, dan Validasi Pasang Surut
**Analisis data radar tahun 2026, prediksi pasang surut periode 2027–2029, serta validasi model GOT4.10 dan EOT20 di wilayah pesisir selatan Daerah Istimewa Yogyakarta.**

---
</div>

<p align="justify">
Data pengamatan muka air laut diperoleh dari sensor radar pada stasiun pasang surut milik <b>BMKG</b>, yaitu Stasiun Baron dan Gesing, yang diakses melalui <i>IOC Sea Level Station Monitoring Facility</i> (UNESCO/IOC) dan dikelola oleh VLIZ. Prediksi pasang surut dilakukan menggunakan <b>pyTMD</b> dengan model <b>GOT4.10</b> dan <b>EOT20</b> pada 13 titik stasiun di sepanjang pesisir selatan Daerah Istimewa Yogyakarta. Hasil pengolahan dilengkapi dengan analisis perbandingan, validasi silang antarmodel, serta validasi terhadap data pengamatan radar BMKG.
</p>

---

## Daftar Isi

1. [Gambaran Umum](#1-gambaran-umum)
2. [Fitur](#2-fitur)
3. [Teknologi dan Library](#3-teknologi-dan-library)
4. [Struktur Repository](#4-struktur-repository)
5. [Persiapan Lingkungan Kerja](#5-persiapan-lingkungan-kerja)
6. [Instalasi Library](#6-instalasi-library)
7. [Persiapan Data dan Model Pasut](#7-persiapan-data-dan-model-pasut)
8. [Metode Pengolahan](#8-metode-pengolahan)
9. [Urutan Menjalankan Program](#9-urutan-menjalankan-program)
10. [Konfigurasi Path dan Data Eksternal](#10-konfigurasi-path-dan-data-eksternal)
11. [Berkas yang Dihasilkan](#11-berkas-yang-dihasilkan)
12. [Pemecahan Masalah](#12-pemecahan-masalah)
13. [Referensi](#13-referensi)
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

Proyek ini dikembangkan menggunakan Python dengan sejumlah library untuk pengolahan data numerik, analisis harmonik pasang surut, visualisasi, pengembangan dashboard interaktif, dan pembuatan laporan PDF.

Versi berikut merupakan versi yang terpasang pada environment pengembangan yang digunakan.

| Komponen | Versi | Kegunaan |
|---|---:|---|
| Python | 3.10.21 | Bahasa pemrograman utama |
| NumPy | 2.2.6 | Operasi numerik dan array |
| Pandas | 2.3.3 | Pengelolaan data tabular dan deret waktu |
| SciPy | 1.15.2 | Statistik dan perhitungan numerik |
| Matplotlib | 3.10.9 | Pembuatan grafik hasil pengolahan |
| pyTMD | 3.0.9 | Perhitungan prediksi pasang surut berbasis model global |
| timescale | 0.1.3 | Pengelolaan skala waktu untuk prediksi |
| T_TIDE (`ttide`) | 0.3.dev2 | Analisis harmonik data radar |
| UTide | 0.4.0 | Analisis harmonik alternatif/cadangan pada `analisisS.py` |
| OpenPyXL | 3.1.5 | Membaca dan menulis berkas Excel |
| Plotly | 7.1.0 | Pembuatan grafik interaktif |
| Dash | 4.5.0 | Kerangka pengembangan dashboard |
| dash-leaflet | 1.0.15 | Pembuatan peta interaktif |
| ReportLab | 5.1.0 | Pembuatan laporan PDF |
| IPython | 8.37.0 | Preview tabel pada lingkungan interaktif (opsional) |

---

## 4. Struktur Repository

Struktur yang disarankan untuk repository:

```text
pasut26/
│
├── README.md
├── requirements.txt
├── pengolahan.py
├── t__tide.py
├── analisisS.py
├── dasbor2026.py
│
├── assets/
│   ├── logo_brin.png
│   ├── logo_dkp_diy.png
│   │
│   └── panduan/
│       ├── nelayan.jpg
│       ├── pemancing.jpg
│       ├── wisata.jpg
│       └── pengelola.jpg
|
├── OLAH/
│   ├── dataPB.xlsx
│   ├── hasil_pasut_2027/                 # dibuat saat pengolahan
│   ├── hasil_pasut_2028/                 # dibuat saat pengolahan
│   ├── hasil_pasut_2029/                 # dibuat saat pengolahan
│   ├── hasil_validasi_eot20_2027/        # dibuat saat pengolahan
│   ├── hasil_validasi_eot20_2028/        # dibuat saat pengolahan
│   └── hasil_validasi_eot20_2029/        # dibuat saat pengolahan
│
├── HASIL_NAN0/                           # dibuat oleh skrip analisisS
│   ├── hasil_harmonik_Baron_Jan.xlsx
│   ├── hasil_harmonik_Panggang_Jan.xlsx
│   ├── rekap_semua_bulan.xlsx
│   └── ANALISIS_SENSITIVITAS/
│       ├── analisis_pasut_gabungan_2026.xlsx
│       └── grafik/
│
└── pytmd_data/                           # model lokal, tidak perlu diunggah
```

**Keterangan struktur:**

- `OLAH/dataPB.xlsx` merupakan berkas masukan pengamatan radar yang digunakan oleh skrip.
- `OLAH/` menjadi folder kerja untuk program prediksi dan validasi.
- `HASIL_NAN0/` digunakan sebagai folder kerja analisis harmonik dan analisis gabungan.
- Folder `assets/` menyimpan seluruh aset tampilan dashboard, meliputi `logo_brin.png` dan `logo_dkp_diy.png` yang diletakkan langsung di dalam folder `assets/`, serta foto pendukung menu panduan pemanfaatan dashboard (`nelayan.jpg`, `pemancing.jpg`, `wisata.jpg`, dan `pengelola.jpg`) yang diletakkan di dalam subfolder `assets/panduan/`. Skrip dashboard memanggil logo dan foto tersebut secara langsung berdasarkan lokasi penyimpanannya, sehingga nama berkas dan struktur folder harus sesuai agar seluruh aset dapat ditampilkan dengan benar.
- `pytmd_data/` menyimpan data model pasang surut secara lokal. Folder ini tidak perlu diunggah ke repository karena ukuran data model dapat besar.
- Folder hasil di dalam `OLAH/` dan `HASIL_NAN0/` akan dibuat ketika skrip dijalankan. Folder hasil tidak wajib diunggah seluruhnya; cukup siapkan data masukan, skrip, dokumentasi, dan aset yang diperlukan.

---

## 5. Persiapan Lingkungan Kerja

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

### 6.1. Perbarui pip

Pastikan environment Python proyek sudah aktif. Jika menggunakan Anaconda, buka **Anaconda Prompt**. Jika menggunakan Python biasa, gunakan **Command Prompt**, PowerShell, atau terminal yang sesuai.

```bash
python -m pip install --upgrade pip
```

### 6.2. Instalasi library utama

Pastikan terminal berada di folder utama repository `pasut26`, yaitu folder yang berisi file `requirements.txt`. Jalankan perintah berikut:

```bash
python -m pip install -r requirements.txt
```

Perintah tersebut akan memasang library utama beserta versi yang telah ditentukan di dalam `requirements.txt`.

Jika ingin memasang library satu per satu, gunakan perintah berikut:

```bash
python -m pip install numpy pandas scipy matplotlib
python -m pip install pyTMD timescale
python -m pip install utide openpyxl
python -m pip install dash dash-leaflet plotly
python -m pip install reportlab
python -m pip install ipython
```

IPython dapat digunakan untuk kebutuhan interaktif atau preview tabel di lingkungan IPython/Jupyter. Jika tidak menggunakan fasilitas tersebut, IPython tidak wajib dipasang untuk menjalankan script Python biasa.

### 6.3. Instalasi T_TIDE Python (`ttide_py`)

T_TIDE perlu dipasang secara terpisah karena kode sumber yang digunakan proyek diambil dari repository GitHub [moflaher/ttide_py](https://github.com/moflaher/ttide_py).

Skrip `t__tide.py` menggunakan modul T_TIDE melalui pemanggilan:

```python
from ttide.t_tide import t_tide
```

Terdapat dua cara untuk memasang T_TIDE.

**Cara A. Menggunakan Git**

1. Pastikan Git sudah terinstal dan dapat dijalankan melalui terminal.
2. Buka Anaconda Prompt, Command Prompt, PowerShell, atau terminal.
3. Aktifkan environment Python proyek.
4. Jalankan perintah berikut:

```bash
git clone https://github.com/moflaher/ttide_py.git
```

5. Masuk ke folder hasil unduhan:

```bash
cd ttide_py
```

6. Pasang T_TIDE ke environment Python yang sedang aktif:

```bash
python -m pip install .
```

**Cara B. Tanpa Git**

Jika Git belum tersedia, T_TIDE dapat diunduh secara manual:

1. Buka repository [moflaher/ttide_py](https://github.com/moflaher/ttide_py).
2. Klik tombol **Code**, kemudian pilih **Download ZIP**.
3. Ekstrak file ZIP yang telah diunduh.
4. Buka terminal pada folder hasil ekstraksi yang berisi file `setup.py`.
5. Pastikan environment Python proyek sudah aktif, kemudian jalankan:

```bash
python -m pip install .
```

Jika perintah tersebut tidak berhasil, repository sumber juga menyediakan metode instalasi berikut:

```bash
python setup.py install
```

Setelah instalasi selesai, kembali ke folder utama repository `pasut26`, kemudian uji apakah modul T_TIDE dapat diimpor:

```bash
python -c "from ttide.t_tide import t_tide; print('T_TIDE berhasil diimpor')"
```

Pastikan instalasi dan pengujian menggunakan environment/interpreter Python yang sama dengan yang digunakan untuk menjalankan skrip. Repository `ttide_py` menyebutkan bahwa proyek ini merupakan konversi T_TIDE yang masih dalam pengembangan dan pengujiannya terbatas. Oleh karena itu, lakukan pengujian pada environment yang digunakan sebelum menjalankan keseluruhan proses pengolahan.

### 6.4. Memeriksa instalasi dan versi library

Pemeriksaan dapat dilakukan langsung melalui **Anaconda Prompt**, **Command Prompt**, **PowerShell**, atau **terminal/console** pada editor seperti VS Code. Pemeriksaan tidak harus dilakukan melalui Jupyter Notebook atau IPython.

**Cara A. Memeriksa library melalui terminal/console**

Pastikan environment proyek sudah aktif, kemudian jalankan:

```bash
python --version
python -m pip show numpy pandas scipy matplotlib pyTMD timescale UTide openpyxl plotly dash dash-leaflet reportlab ipython
```

Perintah `pip show` menampilkan informasi paket, termasuk versi yang terpasang. Jika suatu paket tidak ditemukan, paket tersebut belum terinstal pada environment yang sedang aktif.

Untuk menguji T_TIDE secara terpisah, jalankan:

```bash
python -c "from ttide.t_tide import t_tide; print('T_TIDE berhasil diimpor')"
```

**Cara B. Memeriksa seluruh library menggunakan script Python**

Buat file bernama `cek_library.py` di folder utama repository, lalu isi dengan kode berikut:

```python
import sys
from importlib.metadata import version, PackageNotFoundError

libraries = {
    "numpy": "NumPy",
    "pandas": "Pandas",
    "scipy": "SciPy",
    "matplotlib": "Matplotlib",
    "pyTMD": "pyTMD",
    "timescale": "timescale",
    "ttide": "T_TIDE",
    "UTide": "UTide",
    "openpyxl": "OpenPyXL",
    "plotly": "Plotly",
    "dash": "Dash",
    "dash-leaflet": "dash-leaflet",
    "reportlab": "ReportLab",
    "ipython": "IPython"
}

print("PEMERIKSAAN ENVIRONMENT DAN VERSI LIBRARY")
print("-" * 65)
print(f"Versi Python       : {sys.version.split()[0]}")
print(f"Lokasi interpreter : {sys.executable}")

for package, name in libraries.items():
    try:
        print(f"{name:22} : {version(package)}")
    except PackageNotFoundError:
        print(f"{name:22} : Belum terinstal")

```

Jalankan script tersebut dari terminal/console dengan environment proyek yang sudah aktif:

```bash
python cek_library.py
```

Skrip menampilkan versi Python, lokasi interpreter, versi setiap library, dan informasi apabila suatu library belum terinstal.

**Penting:** jika hasil pemeriksaan menunjukkan library belum terinstal atau muncul pesan `ModuleNotFoundError`, periksa apakah environment yang benar sudah aktif. Untuk melihat interpreter Python yang sedang digunakan, jalankan:

```bash
python -c "import sys; print(sys.executable)"
```

Lokasi interpreter tersebut harus sesuai dengan environment yang digunakan untuk memasang library dan menjalankan skrip.

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

### 8.1 Prediksi dan validasi silang, `pengolahan.py`

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

### 8.2 Analisis Harmonik Data Radar (`t__tide.py`)

Skrip `t__tide.py` digunakan untuk mengolah data pengamatan radar pasang surut pada stasiun Baron dan Panggang (Gesing) selama Januari–Agustus 2026. Data pengamatan dengan interval satu menit diolah menjadi deret waktu rata-rata per jam, kemudian dianalisis menggunakan metode **T_TIDE** untuk memperoleh konstanta harmonik, karakteristik pasang surut, serta parameter elevasi muka air laut.

Tahapan pengolahan yang dilakukan adalah sebagai berikut:

1. Membaca data pengamatan radar dari berkas `OLAH/dataPB.xlsx` berdasarkan nama sheet stasiun dan bulan. Data yang digunakan meliputi waktu pengamatan, kanal baterai, dan elevasi radar.
2. Melakukan pemeriksaan validitas waktu, menghapus data dengan waktu tidak valid, mengurutkan data berdasarkan waktu, serta menangani waktu duplikat.
3. Melakukan pemeriksaan kualitas data (*quality control*/QC) untuk mendeteksi nilai yang macet (*flatline*) dan lonjakan (*spike*). Deteksi flatline dilakukan terhadap rangkaian nilai yang sama selama minimal 30 menit. Deteksi spike menggunakan median bergerak dengan jendela 31 menit dan metode robust sigma berbasis Median Absolute Deviation (MAD). Ambang penghapusan spike ditentukan berdasarkan nilai terbesar antara 0,5 m dan empat kali robust sigma.
4. Mengagregasikan data menjadi rata-rata per jam menggunakan interval `[hh:00, hh+1:00)`, dengan label waktu pada menit ke-30. Setiap kelompok jam harus memiliki sedikitnya 20 sampel agar nilai rata-ratanya digunakan. Jam yang tidak memenuhi persyaratan tersebut ditandai sebagai `NaN`.
5. Melakukan interpolasi berbasis waktu menggunakan metode `time` untuk mengisi kekosongan data yang berada di antara data valid. Interpolasi hanya diterapkan pada gap utuh dengan durasi maksimal 6 jam, sedangkan gap yang lebih panjang tetap dipertahankan sebagai `NaN`.
6. Mengubah deret waktu menjadi anomali muka air dengan mengurangi setiap nilai pengamatan terhadap nilai rata-rata deret waktu. Perhitungan rata-rata mengabaikan nilai `NaN`.
7. Mengubah nilai `NaN` yang masih tersisa menjadi 0 pada deret anomali sebelum diproses oleh T_TIDE, sesuai konfigurasi `NAN_JADI_NOL = True`. Nilai 0 menunjukkan anomali sebesar nol atau kondisi pada nilai rata-rata muka air, bukan penambahan hasil pengamatan baru.
8. Menjalankan analisis harmonik menggunakan fungsi `t_tide` dengan interval data satu jam (`dt=1`) dan memasukkan koordinat lintang masing-masing stasiun.
9. Mengekstrak konstanta harmonik yang meliputi nama konstanta, frekuensi, periode, amplitudo, fase, serta galat amplitudo dan fase.
10. Menghitung rasio sinyal terhadap derau (*Signal-to-Noise Ratio*/SNR) menggunakan rumus:

    `SNR = (Amplitudo / Galat Amplitudo)^2`

    Konstanta harmonik dinyatakan signifikan apabila nilai SNR lebih besar dari 1.
11. Menghitung bilangan Formzahl menggunakan perbandingan amplitudo konstanta K1, O1, M2, dan S2 untuk mengidentifikasi tipe pasang surut apabila seluruh konstanta tersebut tersedia.
12. Menghitung parameter elevasi muka air laut, meliputi Z0, S0/MSL, HHWL, MHWL, LLWL, dan MLWL berdasarkan konstanta harmonik yang diperoleh.
13. Membandingkan data pengamatan per jam dengan hasil prediksi harmonik T_TIDE untuk memperoleh deret prediksi dan residu. Residu dihitung sebagai selisih antara data pengamatan dan prediksi pasang surut.
14. Menyimpan hasil pengolahan dalam bentuk tabel Excel, grafik deret waktu, grafik amplitudo dan fase, serta rekapitulasi hasil analisis seluruh stasiun dan bulan.

#### Parameter QC dan pengolahan

Parameter yang digunakan pada konfigurasi `t__tide.py` adalah sebagai berikut.

| Parameter | Nilai |
|---|---:|
| Jendela median bergerak | 31 menit |
| Batas robust sigma | 4 |
| Ambang minimum lonjakan | 0,5 m |
| Durasi nilai datar untuk dianggap macet | 30 menit |
| Sampel minimum per jam | 20 |
| Metode interpolasi | Time |
| Batas interpolasi | 6 jam |
| SNR minimum | 1 |
| Pengisian NaN pada anomali | 0 |

#### Perhitungan parameter elevasi

Parameter elevasi dihitung berdasarkan konstanta harmonik yang diperoleh dari hasil analisis T_TIDE.

| Parameter | Perhitungan |
|---|---|
| Z0 | Jumlah amplitudo M2, S2, K2, K1, O1, dan P1 |
| S0/MSL | Muka air rata-rata hasil penyesuaian prediksi harmonik terhadap data pengamatan |
| HHWL | S0 + Z0 |
| MHWL | S0 + jumlah amplitudo M2, K1, dan O1 |
| LLWL | S0 - Z0 |
| MLWL | S0 - jumlah amplitudo M2, K1, dan O1 |

Perhitungan MHWL dan MLWL menggunakan S0 sebagai nilai acuan melalui konfigurasi `ACUAN_MHWL_MLWL = "S0"`. Seluruh amplitudo yang digunakan dalam perhitungan parameter elevasi dinyatakan dalam meter.

#### Keluaran pengolahan

Hasil pengolahan disimpan pada folder `HASIL_NAN0/`, meliputi:

- `hasil_harmonik_<stasiun>_<bulan>.xlsx`: tabel konstanta harmonik, ringkasan hasil analisis, dan deret waktu per jam.
- `rekap_semua_bulan.xlsx`: rekapitulasi konstanta harmonik, elevasi penting, dan amplitudo konstanta signifikan seluruh data.
- `tabel_elevasi_muka_laut.xlsx`: rekapitulasi parameter elevasi muka air laut.
- Grafik perbandingan data pengamatan dan prediksi harmonik.
- Grafik amplitudo dan fase konstanta harmonik.
- Grafik rekapitulasi amplitudo dan fase konstanta utama antarstasiun dan bulan.

---

### 8.3 Analisis Radar terhadap GOT4.10 dan EOT20 (`analisisS.py`)

Skrip `analisisS.py` digunakan untuk membandingkan data pengamatan radar dengan hasil prediksi model pasang surut **GOT4.10** dan **EOT20** pada stasiun Baron dan Panggang (Gesing) selama Januari–Agustus 2026.

Pengolahan dilakukan menggunakan pustaka `pyTMD` untuk memperoleh prediksi deret waktu dan konstanta harmonik dari kedua model. Analisis mencakup perbandingan deret waktu pengamatan dengan model, evaluasi statistik, perbandingan karakteristik konstanta harmonik, serta analisis sensitivitas terhadap ambang kecocokan konstanta harmonik.

Tahapan utama pengolahan adalah sebagai berikut:

1. Membaca data pengamatan radar dari `OLAH/dataPB.xlsx` dengan mengidentifikasi sheet berdasarkan nama stasiun dan bulan pengamatan.
2. Melakukan pemeriksaan validitas waktu, mengidentifikasi kolom elevasi radar, menghapus waktu duplikat, serta membatasi data sesuai bulan dan tahun analisis.
3. Melakukan pemeriksaan kualitas data (QC) untuk mendeteksi nilai macet (*flatline*) dan lonjakan (*spike*) menggunakan metode median bergerak dan robust sigma berbasis MAD.
4. Mengagregasikan data radar menjadi rata-rata per jam dengan persyaratan minimal 20 sampel pada setiap jam.
5. Menginterpolasi kekosongan data menggunakan metode `time` untuk gap utuh maksimal 6 jam. Kekosongan yang lebih panjang tetap dipertahankan sebagai `NaN`.
6. Menyesuaikan waktu pengamatan ke UTC berdasarkan informasi zona waktu pada header sheet. Apabila informasi zona waktu tidak tersedia, skrip menggunakan konfigurasi cadangan `TZ_RADAR_JAM = 0`.
7. Mengambil konstanta harmonik radar dari berkas hasil analisis `t__tide.py` yang tersimpan dalam folder `HASIL_NAN0/`. Apabila berkas T_TIDE tidak ditemukan, skrip secara otomatis menghitung ulang konstanta harmonik menggunakan UTide karena `HARMONIK_CADANGAN_AKTIF = True`.
8. Mengekstrak konstanta harmonik dari model GOT4.10 dan EOT20 menggunakan `pyTMD` berdasarkan koordinat geografis stasiun. Konstanta yang diperoleh meliputi amplitudo dan fase masing-masing komponen harmonik.
9. Menghitung prediksi deret waktu pasang surut dari GOT4.10 dan EOT20 pada waktu pengamatan radar menggunakan metode interpolasi `nearest`.
10. Membentuk anomali data radar dan masing-masing model terhadap nilai rata-rata bulanannya. Apabila `NAN_JADI_NOL = True`, nilai radar yang masih `NaN` diisi dengan rata-rata radar sehingga menghasilkan anomali sebesar nol.
11. Menyamakan waktu pengamatan radar dan prediksi model, kemudian membandingkan deret waktu pada waktu yang bersesuaian.
12. Menghitung metrik statistik untuk mengevaluasi kesesuaian antara data radar dan masing-masing model.
13. Membandingkan amplitudo dan fase konstanta harmonik radar yang signifikan dengan konstanta harmonik GOT4.10 dan EOT20.
14. Melakukan analisis sensitivitas menggunakan tiga skenario ambang kecocokan konstanta harmonik, yaitu ketat, dasar, dan longgar.
15. Menyimpan hasil pengolahan berupa tabel ringkasan, data detail, grafik perbandingan, dan berkas Excel.

#### Parameter QC dan pengolahan

Parameter utama yang digunakan pada konfigurasi `analisisS.py` adalah sebagai berikut.

| Parameter | Nilai |
|---|---:|
| Jendela median bergerak | 31 menit |
| Batas robust sigma | 4 |
| Ambang minimum lonjakan | 0,5 m |
| Durasi nilai datar untuk dianggap macet | 30 menit |
| Sampel minimum per jam | 20 |
| Metode interpolasi radar | Time |
| Batas interpolasi | 6 jam |
| Metode interpolasi model | Nearest |
| Batas ekstrapolasi deret waktu | 50 km |
| Batas ekstrapolasi konstanta harmonik | 100 km |
| Lag maksimum yang diperiksa | 8 jam |
| SNR minimum | 1 |
| Zona waktu radar default | UTC (0 jam) |

#### Metrik perbandingan deret waktu

Evaluasi kesesuaian data radar dan model dilakukan menggunakan beberapa metrik statistik sebagai berikut.

- **Bias:** rata-rata selisih antara prediksi model dan pengamatan radar. Nilai positif menunjukkan model cenderung menghasilkan nilai lebih tinggi daripada radar.
- **RMSE (Root Mean Square Error):** akar dari rata-rata kuadrat selisih antara data model dan radar. Nilai yang lebih kecil menunjukkan kesalahan prediksi yang lebih rendah.
- **MAE (Mean Absolute Error):** rata-rata nilai absolut selisih antara data model dan radar.
- **Pearson r:** mengukur kekuatan dan arah hubungan linear antara data radar dan model. Nilai yang mendekati 1 menunjukkan korelasi positif yang kuat.
- **R²:** kuadrat koefisien korelasi Pearson yang menggambarkan kekuatan hubungan linear.
- **Willmott's d:** indeks kesesuaian antara data pengamatan dan model. Nilai yang mendekati 1 menunjukkan tingkat kesesuaian yang lebih baik.
- **Kemiringan (Slope):** menggambarkan perubahan nilai model terhadap perubahan nilai radar berdasarkan regresi linear.
- **Lag:** pergeseran waktu yang menghasilkan korelasi terbaik antara data radar dan model dalam rentang pencarian maksimal ±8 jam. Nilai lag positif menunjukkan pola model muncul lebih awal daripada radar, sedangkan nilai negatif menunjukkan pola model muncul lebih lambat.

Metrik kesalahan dihitung dalam satuan sentimeter, sedangkan korelasi, R², Willmott's d, dan kemiringan merupakan nilai tanpa satuan.

#### Perbandingan konstanta harmonik

Perbandingan konstanta harmonik dilakukan terhadap konstanta radar yang memenuhi kriteria signifikan, yaitu SNR lebih besar dari 1. Konstanta radar tersebut dicocokkan dengan konstanta harmonik yang tersedia pada model GOT4.10 dan EOT20.

Parameter yang dibandingkan meliputi:

- Amplitudo harmonik radar dan model dalam sentimeter.
- Selisih amplitudo absolut dalam sentimeter.
- Selisih amplitudo relatif dalam persen.
- Fase harmonik radar dan model dalam derajat.
- Selisih fase sirkular dalam rentang -180° hingga 180°.
- Selisih vektor harmonik yang mempertimbangkan perbedaan amplitudo dan fase.

Ringkasan evaluasi konstanta harmonik meliputi jumlah konstanta yang dibandingkan, jumlah konstanta yang memenuhi kriteria kecocokan, RMSE amplitudo, MAE amplitudo, bias amplitudo, RMSE fase, MAE fase, dan RMSE vektor.

#### Analisis sensitivitas ambang kecocokan konstanta harmonik

Analisis sensitivitas dilakukan untuk mengetahui pengaruh perubahan toleransi amplitudo dan fase terhadap persentase konstanta harmonik yang dinyatakan cocok antara radar dan model.

Terdapat tiga skenario ambang yang digunakan sebagai berikut.

| Skenario | Selisih amplitudo absolut | Selisih amplitudo relatif | Selisih fase |
|---|---:|---:|---:|
| Ketat | 1 cm | 10% | 10° |
| Dasar | 2 cm | 20% | 20° |
| Longgar | 3 cm | 30% | 30° |

Suatu konstanta harmonik dinyatakan cocok apabila memenuhi dua ketentuan berikut:

1. Selisih amplitudo absolut memenuhi batas toleransi dalam sentimeter **atau** selisih amplitudo relatif memenuhi batas toleransi dalam persen.
2. Selisih fase memenuhi batas toleransi dalam derajat pada skenario yang sama.

Dengan demikian, rumus penentuan kecocokan adalah:

`(|dAmp_cm| <= toleransi_cm ATAU |dAmp_%| <= toleransi_persen) DAN |dFase_deg| <= toleransi_fase`

Hasil analisis sensitivitas digunakan untuk menghitung jumlah dan persentase konstanta harmonik yang cocok pada setiap skenario, baik berdasarkan kombinasi stasiun-bulan-model maupun secara agregat untuk masing-masing model.

Persentase kecocokan dihitung menggunakan rumus:

`Persentase kecocokan = (Jumlah konstanta cocok / Jumlah konstanta dibandingkan) x 100%`

Hasil ketiga skenario kemudian dibandingkan untuk mengidentifikasi model dengan persentase kecocokan tertinggi. Perbandingan ini juga digunakan untuk mengetahui apakah pemilihan model terbaik tetap konsisten ketika toleransi kecocokan diperketat atau diperlonggar.

#### Keluaran pengolahan

Seluruh hasil analisis disimpan pada folder `HASIL_NAN0/ANALISIS_SENSITIVITAS/`, meliputi:

- `analisis_pasut_gabungan_2026.xlsx`: berkas utama yang berisi ringkasan deret waktu, ringkasan konstanta harmonik, detail perbandingan konstanta, data harmonik radar, konstanta model, hasil sensitivitas, dan parameter pengolahan.
- Grafik deret waktu radar terhadap GOT4.10 dan EOT20 beserta residu perbandingan.
- Grafik sebar (*scatter plot*) antara radar dan masing-masing model.
- Grafik perbandingan amplitudo dan fase konstanta harmonik.
- `rekap_gabungan.png`: grafik rekapitulasi hasil evaluasi deret waktu dan konstanta harmonik untuk seluruh stasiun dan bulan.

### 8.4 Dashboard, `dasbor2026.py`

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

### Tahap 1. Prediksi pasang surut dan validasi silang GOT4.10–EOT20

```bash
python pengolahan.py
```

Program menjalankan pengolahan prediksi pasang surut tahun 2027, 2028, dan 2029 pada 13 stasiun. Model GOT4.10 disiapkan melalui pyTMD, sedangkan validasi EOT20 dijalankan apabila data model EOT20 sudah tersedia.

### Tahap 2. Analisis harmonik data radar menggunakan T_TIDE

```bash
python t__tide.py
```

Program membaca data radar dari `OLAH/dataPB.xlsx`. Pastikan T_TIDE Python sudah berhasil dipasang dan dapat diimpor sebelum menjalankan tahap ini.

### Tahap 3. Analisis radar terhadap GOT4.10 dan EOT20

```bash
python analisisS.py
```

Program menjalankan analisis gabungan data radar dan model, termasuk perbandingan deret waktu, konstanta harmonik, metrik statistik, dan sensitivitas ambang kecocokan.

### Tahap 4. Menjalankan dashboard

```bash
python dasbor2026.py
```

Buka alamat berikut melalui browser:

```text
http://127.0.0.1:8050/
```

**Catatan:** dashboard membaca berkas yang sudah tersedia dari tahapan sebelumnya. Jika suatu menu belum menampilkan data, periksa apakah tahap terkait sudah dijalankan dan berkas yang dibutuhkan tersedia pada folder yang sesuai.

---


## 10. Konfigurasi Path dan Data Eksternal

Agar proyek dapat dijalankan dari lokasi folder yang berbeda, gunakan path relatif terhadap lokasi file Python. Dengan pendekatan ini, folder proyek dapat disimpan di `Documents`, `Projects`, atau drive lain tanpa menuliskan alamat folder perangkat secara permanen di dalam skrip.

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
set PASUT_RADAR_XLSX=lokasi_folder_proyek\HASIL_NAN0\ANALISIS_SENSITIVITAS\analisis_pasut_gabungan_2026.xlsx
set PASUT_TTIDE_DIR=lokasi_folder_proyek\HASIL_NAN0
python dasbor2026.py
```

**PowerShell:**

```powershell
$env:PASUT_RADAR_XLSX = "lokasi_folder_proyek\HASIL_NAN0\ANALISIS_SENSITIVITAS\analisis_pasut_gabungan_2026.xlsx"
$env:PASUT_TTIDE_DIR = "lokasi_folder_proyek\HASIL_NAN0"
python dasbor2026.py
```

Ganti `lokasi_folder_proyek` dengan lokasi folder proyek pada perangkat keras yang digunakan. Pengaturan environment variable hanya diperlukan apabila file tidak ditemukan secara otomatis oleh dashboard.

---

## 11. Berkas yang Dihasilkan

Folder hasil pengolahan akan dibuat oleh program sesuai tahapan yang dijalankan. Folder tersebut disimpan secara lokal. Untuk menjalankan dashboard, pastikan berkas yang dibutuhkan oleh menu dashboard sudah tersedia pada lokasi yang sesuai.

---

## 12. Pemecahan Masalah

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
| Memori tidak cukup | Proses model dan deret waktu berukuran besar | Tutup aplikasi lain, proses tahun secara bertahap, dan gunakan perangkat keras dengan RAM memadai. |

---

## 13. Referensi

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


**Pusat Riset Iklim dan Atmosfer, BRIN**

Homebase Yogyakarta, KSTE Achmad Baiquni
