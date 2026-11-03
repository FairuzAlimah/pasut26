# DASHBOARD PASANG SURUT (pemanggilan FILE)

import time as _time
_T0 = _time.perf_counter()   

# 1. IMPORT LIBRARY
import io
import os
import shutil
import threading
import webbrowser
from pathlib import Path
from urllib.parse import quote

import numpy as np
import pandas as pd

from dash import Dash, dcc, html, dash_table, Input, Output, State, no_update
import dash_leaflet as dl
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors as rl_colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    Image as RLImage,
)

# 2. PENGATURAN UMUM
YEARS = [2027, 2028, 2029]
YEAR_LABEL = f"{YEARS[0]}-{YEARS[-1]}"
YEAR_VALIDASI_RADAR = 2026   

# 2b. PALET WARNA
COLOR_TIDE_LINE = "#1f6f8b"
COLOR_MODEL_A = "#1f6f8b"
COLOR_MODEL_B = "#e08e2b"
COLOR_RESIDUAL = "#8e44ad"
COLOR_MSL = "#34495e"
COLOR_HIGH = "#1e8449"
COLOR_LOW = "#c0392b"
COLOR_ACCENT = "#0D1C42"
COLOR_ACCENT_DARK = "#010736"
COLOR_RADAR = "#6c757d"   

COLOR_TITLE_MAIN = "#010736"
COLOR_TITLE_SUB = "#22396F"

UI_NAVY_DARK = "#010736"
UI_NAVY = "#0D1C42"
UI_NAVY_MID = "#22396F"
UI_BLUE_SOFT = "#2E4A8A"
UI_TINT = "#eef1f8"        
UI_LINE = "#e3e7f1"        
UI_TEXT = "#33415c"        
UI_MUTED = "#6b7590"       

# 3. FOLDER HASIL
# Simpan keempat skrip dalam satu folder:
def _lokasi_skrip():
    try:
        return Path(__file__).resolve().parent
    except NameError:  # __file__ tidak ada (mis. run cell / interactive)
        return Path.cwd().resolve()
BASE_DIR = _lokasi_skrip()
MODEL_DIR = BASE_DIR / "pytmd_data"
OLAH_DIR = BASE_DIR / "OLAH"

if not OLAH_DIR.is_dir():
    print(
        "\nPERINGATAN: folder 'OLAH' tidak ditemukan.\n"
        f"  Skrip berada di : {BASE_DIR}\n"
        "  Letakkan folder 'OLAH' (hasil pengolahan.py) di folder yang sama dengan skrip ini."
    )

OUTPUT_DIR_BY_YEAR = {y: OLAH_DIR / f"hasil_pasut_{y}" for y in YEARS}
VALIDASI_DIR_BY_YEAR = {y: OLAH_DIR / f"hasil_validasi_eot20_{y}" for y in YEARS}

# Logo & foto panduan: dicari di folder skrip
def _cari_aset(nama, folder_pencarian):
    for folder in folder_pencarian:
        p = folder / nama
        if p.exists():
            return p
    return folder_pencarian[0] / nama  # path default (belum ada -> dilewati otomatis)

_FOLDER_ASET = [BASE_DIR]

def csv_dir_prediksi(year):
    return OUTPUT_DIR_BY_YEAR[year] / "csv"
def csv_dir_validasi(year):
    return VALIDASI_DIR_BY_YEAR[year] / "csv"
def coord_file_year(year):
    return OUTPUT_DIR_BY_YEAR[year] / f"koordinat_stasiun_{year}.csv"
def metrics_file_year(year):
    return VALIDASI_DIR_BY_YEAR[year] / f"ringkasan_validasi_eot20_vs_got410_{year}.csv"

print("\n" + "=" * 70)
print("DASHBOARD PASANG SURUT WILAYAH SELATAN YOGYAKARTA")
print("=" * 70)
print("Folder skrip          :", BASE_DIR)
print("Folder OLAH           :", OLAH_DIR)
for _y in YEARS:
    print(f"Folder hasil {_y}      :", OUTPUT_DIR_BY_YEAR[_y])
    print(f"Folder validasi {_y}   :", VALIDASI_DIR_BY_YEAR[_y])

# 4. CEK FILE KOORDINAT
coord_file = next((coord_file_year(y) for y in YEARS if coord_file_year(y).exists()), None)
if coord_file is None:
    daftar_dicari = "\n".join(f"  {coord_file_year(y)}" for y in YEARS)
    raise FileNotFoundError(
        "File koordinat stasiun tidak ditemukan. Lokasi yang dicari:\n"
        f"{daftar_dicari}\n\n"
        "Jalankan dahulu skrip pengolahan pasut 2027-2029 "
        "supaya file koordinat dan hasil prediksi tersedia.\n"
        "Pastikan folder 'OLAH' berada di folder yang sama dengan skrip ini."
    )

# 5. BACA KOORDINAT STASIUN
coord_df = pd.read_csv(coord_file)
valid_stations = {
    row["station"]: (row["longitude"], row["latitude"])
    for _, row in coord_df.iterrows()
}
if not valid_stations:
    raise RuntimeError(f"File koordinat stasiun kosong: {coord_file}")
print("\nJumlah stasiun terbaca dari file koordinat:", len(valid_stations))
print("File koordinat yang dipakai:", coord_file)
for name, (lon, lat) in valid_stations.items():
    print(f"  {name:<15}Lon={lon:.6f}  Lat={lat:.6f}")

# BAGIAN DASHBOARD
# 6. PENGATURAN DASHBOARD
DASHBOARD_DIR = OLAH_DIR / "dashboard"
try:
    DASHBOARD_DIR.mkdir(parents=True, exist_ok=True)
except OSError as e:
    print(f"[PERINGATAN] Folder dashboard tidak dapat dibuat: {e}")
LOGO_BRIN = _cari_aset("logo_brin.png", _FOLDER_ASET)
LOGO_DKP = _cari_aset("logo_dkp_diy.png", _FOLDER_ASET)
PANDUAN_IMG_DIR = _cari_aset("foto_panduan", _FOLDER_ASET)
INSTANSI_NAMA = "Pusat Riset Iklim dan Atmosfer, BRIN"
INSTANSI_HOMEBASE = "Homebase Yogyakarta, KSTE Achmad Baiquni"
KETERANGAN_MSL = (
    "Elevasi pasang surut ditampilkan sebagai deviasi terhadap "
    "MSL (Mean Sea Level/muka laut rata-rata), dalam satuan meter (m)."
)
KETERANGAN_PASANG_SURUT = (
    "Perlu diperhatikan: 0/MSL adalah muka laut RATA-RATA, bukan kondisi "
    "surut. Nilai di atas 0 (MSL) berarti muka laut sedang lebih TINGGI "
    "dari rata-rata, dan nilai di bawah 0 (MSL) berarti muka laut sedang "
    "lebih RENDAH dari rata-rata. Kondisi PASANG (high tide) yang "
    "sebenarnya adalah titik puncak tertinggi pada tiap siklus kurva, "
    "sedangkan SURUT (low tide) adalah titik lembah terendah pada tiap "
    "siklus dan keduanya ditandai pada grafik."
)
KETERANGAN_VALIDASI = (
    "Validasi silang membandingkan hasil prediksi model utama (GOT4.10) "
    "terhadap model independen EOT20 pada titik dan waktu yang sama. "
    "Semakin kecil RMSE/MAE dan semakin dekat r & Willmott's d ke angka 1, "
    "semakin konsisten kedua model."
)
KETERANGAN_VALIDASI_RADAR = (   # [RADAR]
    "Menu ini membandingkan prediksi dua model pasang surut global (GOT4.10 dan EOT20) "
    "dengan data pengamatan muka air dari sensor radar pada stasiun Baron dan Panggang "
    "(Gesing) tahun 2026, pada stasiun dan waktu yang sama. Elevasi radar maupun model "
    "dinyatakan sebagai anomali terhadap rata-rata bulan, sehingga yang dibandingkan adalah "
    "bentuk dan amplitudo pasang surut, bukan tinggi absolut. Semakin kecil RMSE/MAE dan "
    "semakin dekat r & Willmott's d ke angka 1, semakin dekat model dengan data radar."
)
SUMBER_DATA_RADAR = (
    "Data pengamatan muka air berasal dari sensor radar (sampling 1 menit) pada stasiun pasang surut "
    "milik BMKG: Baron (kode TASJI, Baron Beach) dan Panggang (kode GESJI, Gesing Beach), "
    "diakses melalui IOC Sea Level Station Monitoring Facility (UNESCO/IOC, dikelola VLIZ)."
)


# 6b. DAFTAR BULAN
month_order = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]
month_indonesia = {
    "January": "Januari", "February": "Februari", "March": "Maret",
    "April": "April", "May": "Mei", "June": "Juni", "July": "Juli",
    "August": "Agustus", "September": "September", "October": "Oktober",
    "November": "November", "December": "Desember",
}
MONTH_NAME_TO_NUMBER = {name: i + 1 for i, name in enumerate(month_order)}

# 6b-2. FUNGSI DAFTAR MINGGU
# (sama dengan skrip pengolahan pasut 2027-2029: Senin s.d. Minggu)
def create_monthly_weeks(year, month):
    start_month = pd.Timestamp(year=year, month=month, day=1)
    end_month = (pd.Timestamp(year=year + 1, month=1, day=1) if month == 12
                 else pd.Timestamp(year=year, month=month + 1, day=1))

    # Senin pertama pada atau sebelum awal bulan (weekday(): Senin=0 ... Minggu=6)
    first_monday = start_month - pd.Timedelta(days=start_month.weekday())
    weeks = []
    current_monday = first_monday
    week_number = 1

    while current_monday < end_month:
        calendar_week_end = current_monday + pd.Timedelta(days=7)
        week_start = max(current_monday, start_month)
        week_end = min(calendar_week_end, end_month)
        if week_start < week_end:
            weeks.append({
                "week_in_month": week_number,
                "week_start": week_start,
                "week_end": week_end,
                "display_end": week_end - pd.Timedelta(hours=1),
            })
            week_number += 1
        current_monday = calendar_week_end
    return weeks

# 6b-3. MEMBANGUN DAFTAR MINGGU UNTUK SEMUA TAHUN
def build_all_weeks_by_year(years):
    all_weeks_by_year = {}
    for year in years:
        weeks_by_month = {}
        global_week = 1
        for month in range(1, 13):
            month_name = pd.Timestamp(year=year, month=month, day=1).strftime("%B")
            weeks = create_monthly_weeks(year, month)
            for week in weeks:
                week["week_of_year"] = global_week
                global_week += 1
            weeks_by_month[month] = {"month_name": month_name, "weeks": weeks}
        all_weeks_by_year[year] = weeks_by_month
    return all_weeks_by_year
ALL_WEEKS_BY_YEAR = build_all_weeks_by_year(YEARS)
_total_minggu_semua_tahun = sum(
    len(bulan_info["weeks"])
    for tahun_info in ALL_WEEKS_BY_YEAR.values()
    for bulan_info in tahun_info.values()
)

# 6b-4. FUNGSI PELABELAN MINGGU + STATISTIK MINGGUAN
def assign_weeks_and_stats(month_df, month_info, station_name, year, month_name, month_number):
    if month_df.empty or month_info is None:
        return month_df.copy(), []
    df = month_df.copy()
    week_numbers, week_of_years = [], []
    for dt in df["datetime_wib"]:
        assigned_week, assigned_global_week = None, None
        for week in month_info["weeks"]:
            if week["week_start"] <= dt < week["week_end"]:
                assigned_week = week["week_in_month"]
                assigned_global_week = week["week_of_year"]
                break
        week_numbers.append(assigned_week)
        week_of_years.append(assigned_global_week)
    df["week_in_month"] = week_numbers
    df["week_of_year"] = week_of_years
    df = df.dropna(subset=["week_in_month"]).reset_index(drop=True)
    if df.empty:
        return df, []
    df["week_in_month"] = df["week_in_month"].astype(int)
    df["week_of_year"] = df["week_of_year"].astype(int)
    stats_list = []
    for week in month_info["weeks"]:
        week_df = df[df["week_in_month"] == week["week_in_month"]]
        if week_df.empty:
            continue
        minimum = week_df["tide_m"].min()
        maximum = week_df["tide_m"].max()
        mean = week_df["tide_m"].mean()
        stats_list.append({
            "year": year,
            "station": station_name,
            "month": month_name,
            "month_number": month_number,
            "week_in_month": week["week_in_month"],
            "week_of_year": week["week_of_year"],
            "start_date": week["week_start"].strftime("%Y-%m-%d"),
            "end_date": week["display_end"].strftime("%Y-%m-%d"),
            "jumlah_data_valid": len(week_df),
            "minimum_m": minimum,
            "maximum_m": maximum,
            "mean_m": mean,
            "range_m": maximum - minimum,
        })
    return df, stats_list

# 7. BACA DATA CSV BULANAN GOT4.10 (hasil pengolahan pasut 2027-2029)
monthly_data = []
for station_name in valid_stations.keys():
    station_slug = station_name.lower().replace(" ", "_")
    for year in YEARS:
        year_csv_dir = csv_dir_prediksi(year) / station_slug
        if not year_csv_dir.exists():
            continue
        for csv_file in year_csv_dir.glob("*.csv"):
            try:
                temp_df = pd.read_csv(csv_file)
                if temp_df.empty:
                    continue
                temp_df["station"] = station_name
                if "year" not in temp_df.columns:
                    temp_df["year"] = year
                monthly_data.append(temp_df)
            except Exception as e:
                print(f"Gagal membaca {csv_file}: {e}")
if monthly_data:
    tide_dashboard_df = pd.concat(monthly_data, ignore_index=True)
else:
    tide_dashboard_df = pd.DataFrame(
        columns=["station", "year", "datetime_utc", "datetime_wib", "tide_m"]
    )
if not tide_dashboard_df.empty:
    tide_dashboard_df["datetime_wib"] = pd.to_datetime(
        tide_dashboard_df["datetime_wib"], errors="coerce"
    )
    tide_dashboard_df["tide_m"] = pd.to_numeric(
        tide_dashboard_df["tide_m"], errors="coerce"
    )
    tide_dashboard_df["year"] = pd.to_numeric(
        tide_dashboard_df["year"], errors="coerce"
    )
    tide_dashboard_df = (
        tide_dashboard_df
        .replace([np.inf, -np.inf], np.nan)
        .dropna(subset=["datetime_wib", "tide_m", "year"])
        .copy()
    )
    tide_dashboard_df["year"] = tide_dashboard_df["year"].astype(int)
    tide_dashboard_df["month_number"] = tide_dashboard_df["datetime_wib"].dt.month
print(f"\nData prediksi GOT4.10 terbaca: {len(tide_dashboard_df):,} baris")

# 7b. BACA DATA VALIDASI EOT20 (ringkasan metrik + deret perbandingan bulanan)
METRICS_FILES_ADA = [metrics_file_year(y) for y in YEARS if metrics_file_year(y).exists()]
if METRICS_FILES_ADA:
    metrics_dashboard_df = pd.concat(
        [pd.read_csv(f) for f in METRICS_FILES_ADA], ignore_index=True
    )
    if not metrics_dashboard_df.empty and "year" in metrics_dashboard_df.columns:
        metrics_dashboard_df["year"] = metrics_dashboard_df["year"].astype(int)
else:
    metrics_dashboard_df = pd.DataFrame()
    print(
        "\nCatatan: file ringkasan validasi EOT20 belum ditemukan di folder "
        "hasil_validasi_eot20_{tahun} (dicari mis.):\n ",
        metrics_file_year(YEARS[0]),
    )
    print("Bagian 'Validasi Silang: GOT4.10 vs EOT20' akan tampil kosong sampai file tersebut tersedia.")

validation_monthly_data = []
for station_name in valid_stations.keys():
    station_slug = station_name.lower().replace(" ", "_")
    for year in YEARS:
        year_val_dir = csv_dir_validasi(year) / station_slug
        if not year_val_dir.exists():
            continue
        for csv_file in year_val_dir.glob("*_perbandingan.csv"):
            try:
                temp_df = pd.read_csv(csv_file, parse_dates=["datetime_utc"])
                if temp_df.empty:
                    continue
                if "year" not in temp_df.columns:
                    temp_df["year"] = year
                validation_monthly_data.append(temp_df)
            except Exception as e:
                print(f"Gagal membaca {csv_file}: {e}")
if validation_monthly_data:
    validation_dashboard_df = pd.concat(validation_monthly_data, ignore_index=True)
else:
    validation_dashboard_df = pd.DataFrame()
if not validation_dashboard_df.empty and "year" in validation_dashboard_df.columns:
    validation_dashboard_df["year"] = validation_dashboard_df["year"].astype(int)
VALIDASI_ADA_DATA = not validation_dashboard_df.empty


# 7c. PENGAMBIL DATA (dari memori; nama fungsi sama dengan dasbordb.py)
def ambil_prediksi(station, year, month_number):
    if tide_dashboard_df.empty:
        return tide_dashboard_df.copy()
    d = tide_dashboard_df
    d = d[(d["station"] == station) & (d["year"] == int(year)) & (d["month_number"] == int(month_number))]
    return d.sort_values("datetime_wib").reset_index(drop=True)

def ambil_validasi_eot20(station, year, month_number):
    if not VALIDASI_ADA_DATA:
        return pd.DataFrame()
    nama_bulan = month_order[int(month_number) - 1]
    d = validation_dashboard_df
    d = d[(d["station"] == station) & (d["year"] == int(year)) & (d["month"] == nama_bulan)]
    return d.sort_values("datetime_utc").reset_index(drop=True)

def ambil_metrik_eot20(station, year, month_number):
    if metrics_dashboard_df.empty:
        return pd.DataFrame()
    nama_bulan = month_order[int(month_number) - 1]
    d = metrics_dashboard_df
    return d[(d["station"] == station) & (d["year"] == int(year)) & (d["month"] == nama_bulan)]

# 7a. OPTIONS STASIUN DAN TAHUN
station_options = sorted(valid_stations.keys())
if not tide_dashboard_df.empty:
    year_options = sorted(int(y) for y in tide_dashboard_df["year"].dropna().unique().tolist())
else:
    year_options = list(YEARS)
if not year_options:
    year_options = list(YEARS)
print("Tahun tersedia pada menu prediksi:", year_options)

# 8. MENU VALIDASI 2026 (RADAR vs GOT4.10 vs EOT20) - DATA DARI HASIL GOT123s.py DAN tes0.py
RADAR_MODELS = ["GOT4.10", "EOT20"]
RADAR_MODEL_COLOR = {"GOT4.10": COLOR_MODEL_A, "EOT20": COLOR_MODEL_B}
RADAR_LABEL_STASIUN = {"Baron": "Baron", "Panggang": "Panggang (Gesing)"}
STASIUN = {
    "Baron":    (110.548490, -8.131006),
    "Panggang": (110.468404, -8.107678),  # Gesing
}
RADAR_BEDA_RMSE_CM = 0.5   # selisih RMSE di bawah ini dianggap setara

# 8-1. Parameter pengolahan.
PARAMETER_BAWAAN_RADAR = {
    "QC_AKTIF": "True",
    "QC_JENDELA_MENIT": "31",
    "QC_N_SIGMA": "4.0",
    "QC_MIN_AMBANG_M": "0.5",
    "QC_RUN_DATAR_MENIT": "30",
    "MIN_SAMPEL_PER_JAM": "20",
    "INTERP_LIMIT_JAM": "6",
    "MAKS_LAG_JAM": "8",
    "SNR_MIN": "1.0",
    "METODE_INTERPOLASI": "nearest",
    "HARMONIK_SUMBER": "ttide_file",
    #"TZ_RADAR_JAM": "0",
    "MODEL": "GOT4.10, EOT20",
}
_PETA_PARAMETER_XLSX = {   # nama pada lembar "Parameter" -> nama yang dipakai dashboard
    "Model": "MODEL",
    "Metode interpolasi deret waktu": "METODE_INTERPOLASI",
    "Batas interpolasi jam kosong": "INTERP_LIMIT_JAM",
    "Sumber harmonik radar": "HARMONIK_SUMBER",
    #"Zona waktu radar default (jam dari UTC)": "TZ_RADAR_JAM",
    "SNR_MIN": "SNR_MIN",
}

# 8-2. Mencari berkas keluaran GOT123s.py dan tes0.py
def _daftar_folder_hasil_nan0():
    """Folder-folder yang mungkin menyimpan hasil tes0.py / GOT123s.py (folder 'HASIL_NAN0')."""
    kandidat = [BASE_DIR / "HASIL_NAN0", BASE_DIR]    # sama dengan HASIL_DIR pada tes0.py dan GOT123s.py
    unik = []
    for k in kandidat:
        if k not in unik and k.is_dir():
            unik.append(k)
    return unik

def _cari_xlsx_gabungan():
    """Cari analisis_pasut_gabungan_{tahun}.xlsx (keluaran GOT123s.py); ambil yang paling baru."""
    env = os.environ.get("PASUT_RADAR_XLSX")
    if env:
        p = Path(env).expanduser()
        if p.is_file():
            return p.resolve()
        print(f"Peringatan: PASUT_RADAR_XLSX='{env}' bukan berkas yang valid, diabaikan.")
    pola = f"analisis_pasut_gabungan_{YEAR_VALIDASI_RADAR}*.xlsx"
    ditemukan = []
    for folder in _daftar_folder_hasil_nan0():
        if folder.name.upper() == "HASIL_NAN0":
            # telusur sampai 3 tingkat di bawah HASIL_NAN0 (mis. ANALISIS_GABUNGAN_8B_...)
            for root, dirs, files in os.walk(str(folder)):
                if len(Path(root).relative_to(folder).parts) >= 3:
                    dirs[:] = []
                    continue
                ditemukan += [Path(root) / f for f in files if Path(f).match(pola) and not f.startswith("~$")]
        else:
            ditemukan += [p for p in folder.glob(pola) if not p.name.startswith("~$")]
    if not ditemukan:
        return None
    return max(ditemukan, key=lambda p: p.stat().st_mtime).resolve()

def _cari_folder_ttide(xlsx_gabungan):
    """Folder keluaran tes0.py (berisi rekap_semua_bulan.xlsx dan hasil_harmonik_*.xlsx)."""
    env = os.environ.get("PASUT_TTIDE_DIR")
    if env:
        p = Path(env).expanduser()
        if p.is_dir():
            return p.resolve()
        print(f"Peringatan: PASUT_TTIDE_DIR='{env}' bukan folder yang valid, diabaikan.")
    kandidat = []
    if xlsx_gabungan is not None:
        kandidat += [xlsx_gabungan.parent, *list(xlsx_gabungan.parents)[:3]]
    kandidat += _daftar_folder_hasil_nan0()
    for k in kandidat:
        if (k / "rekap_semua_bulan.xlsx").is_file() or any(k.glob("hasil_harmonik_*.xlsx")):
            return k.resolve()
    return None

RADAR_XLSX = _cari_xlsx_gabungan()
TTIDE_DIR = _cari_folder_ttide(RADAR_XLSX)

# 8-3. Membaca analisis pasut gabungan
def _bulan_no_dari_label(label):
    """'Januari' / 'January' / 'Jan' / 'Agust' -> 1..12 (None bila tidak dikenal)."""
    s = str(label).strip().lower()
    peta = {}
    for i, en in enumerate(month_order, start=1):
        peta[en.lower()] = i
        peta[month_indonesia[en].lower()] = i
        peta[en[:3].lower()] = i
    peta.update({"agu": 8, "agust": 8, "mei": 5, "okt": 10, "des": 12, "sept": 9})
    return peta.get(s)

def _normalisasi_kolom(df):
    df = df.copy()
    df.columns = [str(c).strip().lower() for c in df.columns]
    return df.rename(columns={"kemiringan_model_vs_radar": "kemiringan", "damp_%": "damp_persen"})

def _tambah_bulan_no(df):
    if df.empty or "bulan" not in df.columns:
        return df
    df = df.copy()
    df["bulan_no"] = df["bulan"].map(_bulan_no_dari_label)
    df = df.dropna(subset=["bulan_no"]).copy()
    df["bulan_no"] = df["bulan_no"].astype(int)
    return df

def _muat_radar_gabungan(path):
    kosong = {
        "metrik_deret": pd.DataFrame(), "metrik_konstanta": pd.DataFrame(),
        "detail_konstanta": pd.DataFrame(), "deret": {}, "parameter": dict(PARAMETER_BAWAAN_RADAR),
        "diperbarui": None, "sumber_harmonik": pd.DataFrame(),
    }
    if path is None:
        return kosong
    try:
        sheets = pd.read_excel(path, sheet_name=None)
    except Exception as e:
        print(f"[Menu Validasi {YEAR_VALIDASI_RADAR}] Gagal membaca {path}: {e}")
        return kosong

    hasil = dict(kosong)
    hasil["metrik_deret"] = _tambah_bulan_no(_normalisasi_kolom(sheets.get("Ringkasan_DeretWaktu", pd.DataFrame())))
    hasil["metrik_konstanta"] = _tambah_bulan_no(_normalisasi_kolom(sheets.get("Ringkasan_Konstanta", pd.DataFrame())))
    hasil["detail_konstanta"] = _tambah_bulan_no(_normalisasi_kolom(sheets.get("Detail_Konstanta", pd.DataFrame())))
    hasil["sumber_harmonik"] = _normalisasi_kolom(sheets.get("Sumber_Harmonik", pd.DataFrame()))
    hasil["diperbarui"] = pd.Timestamp(Path(path).stat().st_mtime, unit="s")

    # deret waktu per jam: lembar "{Stasiun}_{Bulan}" (mis. Baron_Januari)
    nama_stasiun = set(hasil["metrik_deret"]["stasiun"]) if not hasil["metrik_deret"].empty else set()
    for nama_sheet, df in sheets.items():
        if "_" not in nama_sheet:
            continue
        stn, label = nama_sheet.split("_", 1)
        no = _bulan_no_dari_label(label)
        if stn not in nama_stasiun or no is None:
            continue
        s = df.rename(columns={"Radar_m": "radar_m", "GOT4.10_m": "got410_m", "EOT20_m": "eot20_m"})
        if "waktu_utc" not in s.columns or "radar_m" not in s.columns:
            continue
        s["waktu_utc"] = pd.to_datetime(s["waktu_utc"], errors="coerce")
        kolom = [c for c in ("waktu_utc", "radar_m", "got410_m", "eot20_m") if c in s.columns]
        s = s[kolom].dropna(subset=["waktu_utc", "radar_m"]).sort_values("waktu_utc").reset_index(drop=True)
        hasil["deret"][(stn, no)] = s

    # parameter pengolahan
    par = dict(PARAMETER_BAWAAN_RADAR)
    dpar = sheets.get("Parameter")
    if dpar is not None and not dpar.empty:
        for _, r in dpar.iterrows():
            kunci = str(r.iloc[0]).strip()
            par[_PETA_PARAMETER_XLSX.get(kunci, kunci)] = str(r.iloc[1]).strip()
    par["MODEL"] = par.get("MODEL", "").replace("GOT4.10_nc", "GOT4.10")
    hasil["parameter"] = par
    return hasil

_RADAR = _muat_radar_gabungan(RADAR_XLSX)
_RADAR_TABEL = {
    "radar2026_metrik_deret": "metrik_deret",
    "radar2026_metrik_konstanta": "metrik_konstanta",
    "radar2026_detail_konstanta": "detail_konstanta",
}

def label_stasiun_radar(nama):
    return RADAR_LABEL_STASIUN.get(nama, nama)

def radar_ambil_tabel(tabel, stasiun=None, bulan_no=None, order="stasiun, bulan_no"):
    df = _RADAR.get(_RADAR_TABEL[tabel], pd.DataFrame())
    if df.empty:
        return df.copy()
    m = pd.Series(True, index=df.index)
    if stasiun is not None:
        m &= df["stasiun"] == stasiun
    if bulan_no is not None:
        m &= df["bulan_no"] == int(bulan_no)
    kolom = [c.strip() for c in order.split(",") if c.strip() in df.columns]
    out = df[m]
    if kolom:
        out = out.sort_values(kolom, kind="stable")
    return out.reset_index(drop=True)

def radar_ambil_deret(stasiun, bulan_no):
    d = _RADAR["deret"].get((stasiun, int(bulan_no)))
    return d.copy() if d is not None else pd.DataFrame()

def radar_ambil_parameter():
    return dict(_RADAR["parameter"]), _RADAR["diperbarui"]

def radar_stasiun_tersedia():
    d = _RADAR["metrik_deret"]
    return sorted(d["stasiun"].unique().tolist()) if not d.empty else []

def radar_bulan_tersedia(stasiun):
    d = _RADAR["metrik_deret"]
    if not stasiun or d.empty:
        return []
    nomor = sorted(d.loc[d["stasiun"] == stasiun, "bulan_no"].unique().tolist())
    return [month_order[int(b) - 1] for b in nomor]

def radar_bulan_semua():
    d = _RADAR["metrik_deret"]
    return sorted(int(b) for b in d["bulan_no"].unique()) if not d.empty else []

def teks_rentang_bulan(nomor_bulan):
    """[1..8] -> 'Januari sampai Agustus (8 bulan)'; tidak berurutan -> 'Januari, Februari, Maret, April, Mei, Juni, Juli, dan Agustus'."""
    nomor = sorted(set(int(n) for n in nomor_bulan))
    if not nomor:
        return "(belum ada data bulan)"
    nama = [month_indonesia[month_order[n - 1]] for n in nomor]
    if len(nomor) == 1:
        return nama[0]
    berurutan = nomor == list(range(nomor[0], nomor[-1] + 1))
    if berurutan and len(nomor) >= 3:
        return f"{nama[0]} sampai {nama[-1]} ({len(nomor)} bulan)"
    if len(nama) == 2:
        return f"{nama[0]} dan {nama[1]}"
    return ", ".join(nama[:-1]) + f", dan {nama[-1]}"

radar_station_options = radar_stasiun_tersedia()
VALIDASI_RADAR_TERSEDIA = bool(radar_station_options)
RADAR_BULAN_SEMUA = radar_bulan_semua()
if VALIDASI_RADAR_TERSEDIA:
    print(f"\n[Menu Validasi {YEAR_VALIDASI_RADAR}] Hasil GOT123s.py dibaca dari:", RADAR_XLSX)
else:
    print(
        f"\n[Menu Validasi {YEAR_VALIDASI_RADAR}] Berkas analisis_pasut_gabungan_{YEAR_VALIDASI_RADAR}.xlsx "
        "(keluaran GOT123s.py) belum ditemukan.\n"
        "  Jalankan dahulu tes0.py lalu GOT123s.py, atau set environment variable PASUT_RADAR_XLSX.\n"
        "  Menu tetap muncul di dashboard tetapi kosong sampai berkas tersebut tersedia."
    )
print(f"[Menu Validasi {YEAR_VALIDASI_RADAR}] Stasiun radar tersedia:",
      radar_station_options if radar_station_options else "(belum ada)")
print(f"[Menu Validasi {YEAR_VALIDASI_RADAR}] Bulan radar tersedia:",
      teks_rentang_bulan(RADAR_BULAN_SEMUA))

# 8-4. Membaca hasil analisis harmonik radar t_tide
TTIDE_KODE_BULAN = {1: "Jan", 2: "Feb", 3: "Maret", 4: "April", 5: "Mei", 6: "Juni", 7: "Juli", 8: "Agust"}
# Konstanta penyusun elevasi penting pada tes0.py (KONSTA_Z0 dan KONSTA_MHWL)
TTIDE_KONSTA_Z0 = "M2, S2, K2, K1, O1, P1"
TTIDE_KONSTA_MHWL = "M2, K1, O1"

def _muat_ttide_rekap():
    if TTIDE_DIR is None:
        return pd.DataFrame(), pd.DataFrame()
    f = TTIDE_DIR / "rekap_semua_bulan.xlsx"
    if not f.is_file():
        return pd.DataFrame(), pd.DataFrame()
    try:
        sh = pd.read_excel(f, sheet_name=None)
    except Exception as e:
        print(f"[tes0] Gagal membaca {f}: {e}")
        return pd.DataFrame(), pd.DataFrame()
    rekap = sh.get("Rekap", pd.DataFrame())
    elev = sh.get("Elevasi penting", pd.DataFrame())
    if not elev.empty:
        elev = elev.rename(columns={elev.columns[0]: "Data set"})
    return rekap, elev

_TTIDE_REKAP, _TTIDE_ELEV = _muat_ttide_rekap()
TTIDE_TERSEDIA = TTIDE_DIR is not None and (not _TTIDE_REKAP.empty or any(TTIDE_DIR.glob("hasil_harmonik_*.xlsx")))
print(f"[Menu Validasi {YEAR_VALIDASI_RADAR}] Hasil t_tide (tes0.py) dibaca dari:",
      TTIDE_DIR if TTIDE_TERSEDIA else "(belum ditemukan)")

def ttide_rekap_baris(stasiun, bulan_no):
    kode = TTIDE_KODE_BULAN.get(int(bulan_no))
    if kode is None or _TTIDE_REKAP.empty:
        return None
    sub = _TTIDE_REKAP[(_TTIDE_REKAP["Stasiun"] == stasiun) & (_TTIDE_REKAP["Bulan"] == kode)]
    return sub.iloc[0].to_dict() if not sub.empty else None

def ttide_elevasi(stasiun, bulan_no):
    kode = TTIDE_KODE_BULAN.get(int(bulan_no))
    if kode is None or _TTIDE_ELEV.empty:
        return None
    sub = _TTIDE_ELEV[_TTIDE_ELEV["Data set"] == f"{stasiun} {kode}"]
    return sub.iloc[0].to_dict() if not sub.empty else None

_TTIDE_TABEL_CACHE = {}

def ttide_tabel_konstanta(stasiun, bulan_no):
    """Tabel konstanta harmonik radar (lembar 'Konstanta harmonik' pada hasil_harmonik_{stasiun}_{bulan}.xlsx)."""
    kode = TTIDE_KODE_BULAN.get(int(bulan_no))
    if kode is None or TTIDE_DIR is None:
        return pd.DataFrame()
    kunci = (stasiun, kode)
    if kunci not in _TTIDE_TABEL_CACHE:
        f = TTIDE_DIR / f"hasil_harmonik_{stasiun}_{kode}.xlsx"
        try:
            _TTIDE_TABEL_CACHE[kunci] = (
                pd.read_excel(f, sheet_name="Konstanta harmonik") if f.is_file() else pd.DataFrame()
            )
        except Exception as e:
            print(f"[tes0] Gagal membaca {f}: {e}")
            _TTIDE_TABEL_CACHE[kunci] = pd.DataFrame()
    return _TTIDE_TABEL_CACHE[kunci].copy()

# 8a. FORMAT ANGKA
def _num(v, d=2):
    if v is None or pd.isna(v):
        return "-"
    return f"{float(v):.{d}f}"

def _idn(v, d=2, sign=False):
    """Angka dengan koma desimal (gaya Indonesia) untuk kalimat kesimpulan."""
    if v is None or pd.isna(v):
        return "-"
    teks = f"{float(v):+.{d}f}" if sign else f"{float(v):.{d}f}"
    return teks.replace(".", ",")

def _par_float(par, kunci, default):
    try:
        return float(par.get(kunci, default))
    except (TypeError, ValueError):
        return default

def _per_model(df):
    return {row["model"]: row.to_dict() for _, row in df.iterrows()} if not df.empty else {}

# 8b. PANEL METRIK RINGKAS
# nilai yang lebih baik di antara GOT4.10 dan EOT20 diberi warna hijau.
C_GOT = COLOR_MODEL_A
C_EOT = COLOR_MODEL_B
_HIJAU, _HIJAU_BG = "#1e8449", "#e6f4ea"
_MODEL_WARNA = {"GOT4.10": C_GOT, "EOT20": C_EOT}
_ORANYE = "#F68048"


def _fl(d, k):
    try:
        return float(d.get(k)) if d else np.nan
    except (TypeError, ValueError):
        return np.nan


def _bias_txt(v, d=2):
    """Bias dengan tanda; hindari tampilan '-0,00'."""
    if v is None or pd.isna(v):
        return "-"
    if abs(v) < 0.5 * 10 ** (-d):
        return _idn(0, d)
    return _idn(v, d, sign=True)


def _pemenang(a, b, mode, dec):
    """0 = kolom pertama lebih baik, 1 = kolom kedua, None = sama/tidak dinilai."""
    if mode is None or pd.isna(a) or pd.isna(b):
        return None
    if mode == "one":
        a, b = abs(a - 1), abs(b - 1)
        mode = "min"
    elif mode == "zero":
        a, b = abs(a), abs(b)
        mode = "min"
    a, b = round(a, dec), round(b, dec)
    if a == b:
        return None
    if mode == "min":
        return 0 if a < b else 1
    return 0 if a > b else 1


def _sel_nilai(teks, menang):
    style = {"textAlign": "center", "fontSize": "13.5px", "padding": "3px 6px",
             "borderRadius": "6px", "color": UI_TEXT, "fontWeight": "500"}
    if menang:
        style.update({"backgroundColor": _HIJAU_BG, "color": _HIJAU, "fontWeight": "700"})
    return html.Div(teks, style=style)


def _baris_metrik(label, a, b, dec, mode=None, sign=False, teks=None):
    if teks:
        ta, tb = teks
    elif sign:
        ta, tb = _bias_txt(a, dec), _bias_txt(b, dec)
    else:
        ta, tb = _idn(a, dec), _idn(b, dec)
    w = _pemenang(a, b, mode, dec)
    return html.Div(
        [html.Div(label, style={"fontSize": "13px", "fontWeight": "600", "color": UI_NAVY}),
         _sel_nilai(ta, w == 0), _sel_nilai(tb, w == 1)],
        style={"display": "grid", "gridTemplateColumns": "1.7fr 1fr 1fr", "gap": "6px",
               "alignItems": "center", "padding": "7px 0", "borderTop": f"1px solid {UI_LINE}"},
    )


def _kartu_grup(judul, warna_aksen, baris):
    kepala = html.Div(
        [html.Div(judul, style={"fontSize": "12px", "fontWeight": "700", "letterSpacing": "0.8px",
                                "color": warna_aksen, "textTransform": "uppercase"}),
         html.Div("GOT4.10", style={"textAlign": "center", "fontSize": "12px", "fontWeight": "700", "color": C_GOT}),
         html.Div("EOT20", style={"textAlign": "center", "fontSize": "12px", "fontWeight": "700", "color": C_EOT})],
        style={"display": "grid", "gridTemplateColumns": "1.7fr 1fr 1fr", "gap": "6px", "paddingBottom": "8px"},
    )
    return html.Div(
        [kepala, *baris],
        style={"backgroundColor": "white", "border": f"1px solid {UI_LINE}", "borderTop": f"4px solid {warna_aksen}",
               "borderRadius": "12px", "padding": "14px 16px", "boxShadow": "0 2px 10px rgba(13,28,66,0.06)"},
    )


def _chip_info(label, nilai):
    return html.Span(
        [html.Span(label + " ", style={"color": UI_MUTED}), html.B(nilai, style={"color": UI_NAVY})],
        style={"display": "inline-block", "backgroundColor": UI_TINT, "border": f"1px solid {UI_LINE}",
               "borderRadius": "999px", "padding": "5px 12px", "fontSize": "12.5px", "margin": "0 8px 8px 0"},
    )


def build_radar_metric_table(deret, kons):
    """Panel metrik ringkas. deret/kons: dict model -> baris metrik. Mengembalikan komponen Dash."""
    if not deret:
        return html.P("Data metrik belum tersedia untuk pilihan ini.",
                      style={"color": UI_MUTED, "fontStyle": "italic"})
    g, e = deret.get("GOT4.10", {}), deret.get("EOT20", {})
    kg, ke = kons.get("GOT4.10", {}), kons.get("EOT20", {})

    def cocok(k):
        if not k or pd.isna(k.get("n_dibandingkan")) or not k.get("n_dibandingkan"):
            return np.nan, "-"
        return k["n_cocok"] / k["n_dibandingkan"], f"{int(k['n_cocok'])} dari {int(k['n_dibandingkan'])}"

    rc_g, tc_g = cocok(kg)
    rc_e, tc_e = cocok(ke)

    n_jam = _fl(g, "n_jam") if g else _fl(e, "n_jam")
    lag_g, lag_e = _fl(g, "lag_terbaik_jam"), _fl(e, "lag_terbaik_jam")
    strip = html.Div([
        _chip_info("Data", f"{int(n_jam):,} jam".replace(",", ".") if not pd.isna(n_jam) else "-"),
        _chip_info("Rentang radar", f"{_idn(_fl(g or e, 'rentang_radar_cm'), 1)} cm"),
        _chip_info("Rentang model", f"{_idn(_fl(g, 'rentang_model_cm'), 1)} / {_idn(_fl(e, 'rentang_model_cm'), 1)} cm"),
        _chip_info("Lag terbaik",
                   f"{'-' if pd.isna(lag_g) else int(round(lag_g))} / {'-' if pd.isna(lag_e) else int(round(lag_e))} jam"),
    ], style={"marginBottom": "6px"})

    kartu = [
        _kartu_grup("Besar kesalahan", UI_NAVY, [
            _baris_metrik("RMSE (cm)", _fl(g, "rmse_cm"), _fl(e, "rmse_cm"), 2, "min"),
            _baris_metrik("MAE (cm)", _fl(g, "mae_cm"), _fl(e, "mae_cm"), 2, "min"),
            _baris_metrik("Bias model - radar (cm)", _fl(g, "bias_cm"), _fl(e, "bias_cm"), 2, "zero", sign=True),
        ]),
        _kartu_grup("Kemiripan pola", "#117864", [
            _baris_metrik("Korelasi (r)", _fl(g, "r"), _fl(e, "r"), 3, "max"),
            _baris_metrik("Willmott's d", _fl(g, "willmott_d"), _fl(e, "willmott_d"), 3, "max"),
            _baris_metrik("Kemiringan (ideal 1)", _fl(g, "kemiringan"), _fl(e, "kemiringan"), 3, "one"),
        ]),
        _kartu_grup("Konstanta harmonik", _ORANYE, [
            _baris_metrik("Konstanta cocok", rc_g, rc_e, 3, "max", teks=(tc_g, tc_e)),
            _baris_metrik("RMSE amplitudo (cm)", _fl(kg, "rmse_amp_cm"), _fl(ke, "rmse_amp_cm"), 2, "min"),
            _baris_metrik("RMSE fase (derajat)", _fl(kg, "rmse_fase_deg"), _fl(ke, "rmse_fase_deg"), 1, "min"),
            _baris_metrik("RMSE vektor (cm)", _fl(kg, "rmse_vektor_cm"), _fl(ke, "rmse_vektor_cm"), 2, "min"),
        ]),
    ]
    return html.Div([
        strip,
        html.Div(kartu, style={"display": "grid", "gap": "14px",
                               "gridTemplateColumns": "repeat(auto-fit, minmax(300px, 1fr))"}),
        html.P("Sel hijau = nilai yang lebih baik di antara kedua model (kesalahan lebih kecil; r dan d lebih besar; "
               "kemiringan lebih dekat ke 1; bias lebih dekat ke 0).",
               style={"fontSize": "12px", "color": UI_MUTED, "fontStyle": "italic", "margin": "10px 2px 0 2px"}),
    ])

# 8c. GRAFIK
def _fig_kosong(judul, tinggi=420):
    fig = go.Figure()
    fig.update_layout(title=judul, template="plotly_white", height=tinggi)
    return fig

def build_radar_series_fig(df, judul_stasiun):
    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True, row_heights=[0.65, 0.35], vertical_spacing=0.10,
        subplot_titles=("Perbandingan anomali elevasi: Radar vs GOT4.10 vs EOT20",
                        "Selisih (model - radar)"),
    )
    fig.add_trace(go.Scatter(
        x=df["waktu_utc"], y=df["radar_m"], name="Radar", mode="lines",
        line=dict(color=COLOR_RADAR, width=2.2, dash="dot"), legendgroup="Radar",
        hovertemplate="<b>Radar</b><br>Waktu: %{x}<br>Anomali: %{y:.3f} m<extra></extra>",
    ), row=1, col=1)
    for model, kolom, dash in (("GOT4.10", "got410_m", "solid"), ("EOT20", "eot20_m", "dash")):
        if kolom not in df.columns:
            continue
        warna = RADAR_MODEL_COLOR[model]
        fig.add_trace(go.Scatter(
            x=df["waktu_utc"], y=df[kolom], name=model, mode="lines", legendgroup=model,
            line=dict(color=warna, width=2.0, dash=dash),
            hovertemplate=f"<b>{model}</b><br>Waktu: %{{x}}<br>Anomali: %{{y:.3f}} m<extra></extra>",
        ), row=1, col=1)
        fig.add_trace(go.Scatter(
            x=df["waktu_utc"], y=df[kolom] - df["radar_m"], name=f"{model} - Radar",
            mode="lines", legendgroup=model, showlegend=False,
            line=dict(color=warna, width=1.4),
            hovertemplate=f"<b>{model} - Radar</b><br>Waktu: %{{x}}<br>Selisih: %{{y:.3f}} m<extra></extra>",
        ), row=2, col=1)
    fig.add_hline(y=0, line_dash="dot", line_color="#95a5a6", row=2, col=1)
    fig.update_yaxes(title_text="Anomali elevasi (m)", showgrid=True, gridcolor="#edf1f3", row=1, col=1)
    fig.update_yaxes(title_text="Selisih (m)", showgrid=True, gridcolor="#edf1f3", row=2, col=1)
    fig.update_xaxes(title_text="Tanggal dan Waktu (UTC)", showgrid=True, gridcolor="#edf1f3", row=2, col=1)
    fig.update_layout(
        title=dict(text=f"Deret Waktu Pasang Surut per Jam - {judul_stasiun}",
                   x=0.02, xanchor="left", font=dict(size=17, color="#0D1C42")),
        template="plotly_white", height=640, hovermode="x unified",
        margin=dict(l=65, r=25, t=100, b=70),
        paper_bgcolor="white", plot_bgcolor="white",
        font=dict(family="Poppins, Arial, sans-serif", color="#33415c"),
        legend=dict(orientation="h", yanchor="bottom", y=1.07, xanchor="right", x=1,
                    bgcolor="rgba(255,255,255,0.96)", bordercolor="#d8e0e5", borderwidth=1,
                    font=dict(size=11)),
    )
    return fig

def build_radar_scatter_fig(df, deret):
    model_ada = [m for m in RADAR_MODELS if f"{'got410' if m == 'GOT4.10' else 'eot20'}_m" in df.columns]
    judul = []
    for m in model_ada:
        b = deret.get(m, {})
        judul.append(f"{m} (r = {_num(b.get('r'), 3)}, kemiringan = {_num(b.get('kemiringan'), 2)})")
    fig = make_subplots(rows=1, cols=len(model_ada), subplot_titles=judul)
    kolom_model = {"GOT4.10": "got410_m", "EOT20": "eot20_m"}
    lim = float(max(df["radar_m"].abs().max(),
                    *(df[kolom_model[m]].abs().max() for m in model_ada))) * 1.05
    for i, m in enumerate(model_ada, start=1):
        fig.add_trace(go.Scatter(
            x=df["radar_m"], y=df[kolom_model[m]], mode="markers", name=m,
            marker=dict(size=5, opacity=0.5, color=RADAR_MODEL_COLOR[m]), showlegend=False,
            hovertemplate=f"<b>{m}</b><br>Radar: %{{x:.3f}} m<br>Model: %{{y:.3f}} m<extra></extra>",
        ), row=1, col=i)
        fig.add_trace(go.Scatter(
            x=[-lim, lim], y=[-lim, lim], mode="lines", showlegend=False,
            line=dict(color="#34495e", width=1, dash="dash"), hoverinfo="skip",
        ), row=1, col=i)
        fig.update_xaxes(title_text="Radar (m)", range=[-lim, lim], row=1, col=i,
                         showgrid=True, gridcolor="#edf1f3")
        fig.update_yaxes(title_text=f"{m} (m)", range=[-lim, lim], row=1, col=i,
                         showgrid=True, gridcolor="#edf1f3",
                         scaleanchor=f"x{'' if i == 1 else i}", scaleratio=1)
    fig.update_layout(
        title=dict(text="Diagram Sebar: Model vs Radar (garis putus-putus = 1:1)",
                   x=0.02, xanchor="left", font=dict(size=17, color="#0D1C42")),
        template="plotly_white", height=470, margin=dict(l=65, r=25, t=95, b=60),
        paper_bgcolor="white", plot_bgcolor="white",
        font=dict(family="Poppins, Arial, sans-serif", color="#33415c"),
    )
    return fig

def _urut_konstanta(detail):
    """Konstanta unik diurutkan menurut amplitudo radar (terbesar dulu)."""
    return (detail.drop_duplicates("konstanta")
            .sort_values("amp_radar_cm", ascending=False)["konstanta"].tolist())

def build_radar_constituent_fig(detail, maks=10):
    if detail.empty:
        return _fig_kosong("Data konstanta harmonik tidak tersedia untuk pilihan ini", 420)
    kons = _urut_konstanta(detail)[:maks]
    dasar = detail.drop_duplicates("konstanta").set_index("konstanta").reindex(kons)
    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True, row_heights=[0.55, 0.45], vertical_spacing=0.08,
        subplot_titles=("Amplitudo (cm)", "Fase Greenwich (derajat)"),
    )
    fig.add_trace(go.Bar(x=kons, y=dasar["amp_radar_cm"], name="Radar", marker_color=COLOR_RADAR,
                         legendgroup="Radar",
                         hovertemplate="<b>Radar %{x}</b><br>Amplitudo: %{y:.2f} cm<extra></extra>"),
                  row=1, col=1)
    fig.add_trace(go.Bar(x=kons, y=dasar["fase_radar_deg"], name="Radar", marker_color=COLOR_RADAR,
                         legendgroup="Radar", showlegend=False,
                         hovertemplate="<b>Radar %{x}</b><br>Fase: %{y:.1f} derajat<extra></extra>"),
                  row=2, col=1)
    for model in RADAR_MODELS:
        dm = detail[detail["model"] == model].set_index("konstanta").reindex(kons)
        fig.add_trace(go.Bar(x=kons, y=dm["amp_pytmd_cm"], name=model,
                             marker_color=RADAR_MODEL_COLOR[model], legendgroup=model,
                             hovertemplate=f"<b>{model} %{{x}}</b><br>Amplitudo: %{{y:.2f}} cm<extra></extra>"),
                      row=1, col=1)
        fig.add_trace(go.Bar(x=kons, y=dm["fase_pytmd_deg"], name=model,
                             marker_color=RADAR_MODEL_COLOR[model], legendgroup=model, showlegend=False,
                             hovertemplate=f"<b>{model} %{{x}}</b><br>Fase: %{{y:.1f}} derajat<extra></extra>"),
                      row=2, col=1)
    fig.update_yaxes(title_text="Amplitudo (cm)", showgrid=True, gridcolor="#edf1f3", row=1, col=1)
    fig.update_yaxes(title_text="Fase (derajat)", range=[0, 360], showgrid=True,
                     gridcolor="#edf1f3", row=2, col=1)
    fig.update_xaxes(title_text="Konstanta harmonik", row=2, col=1)
    fig.update_layout(
        title=dict(text=f"Konstanta Harmonik Utama: Radar vs Model (maks. {maks} terbesar)",
                   x=0.02, xanchor="left", font=dict(size=17, color="#0D1C42")),
        template="plotly_white", height=560, barmode="group",
        margin=dict(l=65, r=25, t=100, b=70),
        paper_bgcolor="white", plot_bgcolor="white",
        font=dict(family="Poppins, Arial, sans-serif", color="#33415c"),
        legend=dict(orientation="h", yanchor="bottom", y=1.07, xanchor="right", x=1,
                    bgcolor="rgba(255,255,255,0.96)", bordercolor="#d8e0e5", borderwidth=1,
                    font=dict(size=11)),
    )
    return fig

def build_radar_constituent_table(detail):
    if detail.empty:
        return []
    baris = []
    for k in _urut_konstanta(detail):
        sub = detail[detail["konstanta"] == k]
        dasar = sub.iloc[0]
        row = {
            "konstanta": k,
            "amp_radar": _num(dasar["amp_radar_cm"], 2),
            "fase_radar": _num(dasar["fase_radar_deg"], 1),
            "snr": _num(dasar["snr"], 1),
        }
        for tag, model in (("got", "GOT4.10"), ("eot", "EOT20")):
            m = sub[sub["model"] == model]
            if m.empty:
                row.update({f"amp_{tag}": "-", f"fase_{tag}": "-", f"cocok_{tag}": "-"})
            else:
                m = m.iloc[0]
                row.update({
                    f"amp_{tag}": _num(m["amp_pytmd_cm"], 2),
                    f"fase_{tag}": _num(m["fase_pytmd_deg"], 1),
                    f"cocok_{tag}": m["cocok"] if pd.notna(m["cocok"]) else "-",
                })
        baris.append(row)
    return baris

# 8d. KESIMPULAN PADAT PER PILIHAN (dihitung otomatis dari hasil GOT123s.py)
def _kata_korelasi(r):
    if r is None or pd.isna(r):
        return "tidak dapat dihitung"
    if r >= 0.9:
        return "sangat tinggi"
    if r >= 0.7:
        return "tinggi"
    if r >= 0.5:
        return "sedang"
    return "rendah"

def _kata_amplitudo(k):
    if k is None or pd.isna(k):
        return None
    if k > 1.10:
        return "lebih besar daripada radar"
    if k < 0.90:
        return "lebih kecil daripada radar"
    return "mendekati radar"

def _kata_lag(lag):
    if lag is None or pd.isna(lag):
        return None
    lag = int(round(lag))
    if lag == 0:
        return "tanpa pergeseran waktu (lag 0 jam)"
    if lag > 0:
        return f"pola model muncul {lag} jam lebih awal daripada radar"
    return f"pola model muncul {abs(lag)} jam lebih lambat daripada radar"

def _badge(teks, bg, warna):
    return html.Span(teks, style={"display": "inline-block", "backgroundColor": bg, "color": warna,
                                  "fontSize": "11.5px", "fontWeight": "700", "letterSpacing": "1px",
                                  "padding": "4px 12px", "borderRadius": "999px"})


def _banner_verdict(badge, judul, rincian):
    return html.Div(
        [html.Div(badge, style={"marginBottom": "8px"}),
         html.Div(judul, style={"fontSize": "17px", "fontWeight": "700", "color": "white", "lineHeight": "1.4"}),
         html.Div(rincian, style={"fontSize": "13px", "color": "rgba(255,255,255,0.85)", "marginTop": "6px",
                                  "lineHeight": "1.6"})],
        style={"background": "linear-gradient(135deg, #010736 0%, #0D1C42 60%, #22396F 100%)",
               "borderRadius": "14px", "padding": "18px 22px", "marginBottom": "14px"},
    )


def _kartu_model_ringkas(model, judul_angka, angka, butir):
    warna = _MODEL_WARNA[model]
    return html.Div(
        [html.Div(model, style={"fontSize": "12px", "fontWeight": "700", "letterSpacing": "1px", "color": warna}),
         html.Div([html.Span(angka, style={"fontSize": "26px", "fontWeight": "700", "color": UI_NAVY}),
                   html.Span(" " + judul_angka, style={"fontSize": "12.5px", "color": UI_MUTED})],
                  style={"margin": "4px 0 8px 0"}),
         html.Ul([html.Li(b, style={"marginBottom": "3px"}) for b in butir],
                 style={"margin": "0", "paddingLeft": "18px", "fontSize": "13px", "lineHeight": "1.55",
                        "color": UI_TEXT})],
        style={"backgroundColor": "white", "border": f"1px solid {UI_LINE}", "borderTop": f"4px solid {warna}",
               "borderRadius": "12px", "padding": "14px 16px"},
    )


def build_radar_kesimpulan_pilihan(stasiun, bulan_name, deret, kons, detail, par):
    judul = f"{label_stasiun_radar(stasiun)}, {month_indonesia[bulan_name]} {YEAR_VALIDASI_RADAR}"
    if not deret:
        return info_callout(f"Kesimpulan: {judul}",
                            "Hasil validasi untuk pilihan ini belum tersedia di berkas hasil GOT123s.py.", tone="warn")
    got, eot = deret.get("GOT4.10"), deret.get("EOT20")

    # 1. verdict
    if got and eot:
        selisih = abs(got["rmse_cm"] - eot["rmse_cm"])
        if selisih < RADAR_BEDA_RMSE_CM:
            banner = _banner_verdict(
                _badge("SETARA", "#e6f4ea", _HIJAU),
                f"GOT4.10 dan EOT20 sama baiknya mengikuti radar - {judul}",
                f"RMSE {_idn(got['rmse_cm'])} cm (GOT4.10) vs {_idn(eot['rmse_cm'])} cm (EOT20); "
                f"selisih hanya {_idn(selisih)} cm.")
        else:
            t, l = ("GOT4.10", "EOT20") if got["rmse_cm"] < eot["rmse_cm"] else ("EOT20", "GOT4.10")
            banner = _banner_verdict(
                _badge(f"{t} LEBIH DEKAT", "#fff4ec", "#c4561a"),
                f"{t} lebih dekat dengan radar - {judul}",
                f"RMSE {_idn(deret[t]['rmse_cm'])} cm vs {_idn(deret[l]['rmse_cm'])} cm ({l}); "
                f"r {_idn(deret[t]['r'], 3)} vs {_idn(deret[l]['r'], 3)}.")
    else:
        ada = got or eot
        banner = _banner_verdict(_badge("HANYA 1 MODEL", "#fff4ec", "#c4561a"),
                                 f"Hanya {ada['model']} yang punya hasil - {judul}",
                                 f"RMSE {_idn(ada['rmse_cm'])} cm, r {_idn(ada['r'], 3)}.")

    # 2. kartu per model
    kartu = []
    for model in RADAR_MODELS:
        b = deret.get(model)
        if not b:
            continue
        butir = [f"Korelasi {_kata_korelasi(b['r'])} (r = {_idn(b['r'], 3)})"]
        ka = _kata_amplitudo(b.get("kemiringan"))
        if ka:
            butir.append(f"Amplitudo {ka} (kemiringan {_idn(b['kemiringan'], 2)})")
        butir.append(f"Bias rata-rata {_bias_txt(b['bias_cm'])} cm")
        rr = b.get("rentang_radar_cm")
        if rr and not pd.isna(rr) and rr > 0:
            butir.append(f"RMSE = {_idn(100 * b['rmse_cm'] / rr, 1)}% dari rentang radar ({_idn(rr, 0)} cm)")
        kata_lag = _kata_lag(b.get("lag_terbaik_jam"))
        if kata_lag:
            butir.append(kata_lag[0].upper() + kata_lag[1:])
        k = kons.get(model) if kons else None
        if k and not pd.isna(k.get("n_dibandingkan")):
            butir.append(f"Konstanta cocok {int(k['n_cocok'])}/{int(k['n_dibandingkan'])} "
                         f"(RMSE vektor {_idn(k['rmse_vektor_cm'])} cm)")
        kartu.append(_kartu_model_ringkas(model, "cm RMSE", _idn(b["rmse_cm"]), butir))
    grid_kartu = html.Div(kartu, style={"display": "grid", "gap": "14px",
                                        "gridTemplateColumns": "repeat(auto-fit, minmax(300px, 1fr))"})

    isi = [banner, grid_kartu]

    # 3. konstanta dominan
    if detail is not None and not detail.empty:
        top = detail.sort_values("amp_radar_cm", ascending=False).iloc[0]
        nama_k, amp_r = top["konstanta"], float(top["amp_radar_cm"])
        potong = []
        for model in RADAR_MODELS:
            m = detail[(detail["konstanta"] == nama_k) & (detail["model"] == model)]
            if m.empty:
                continue
            m = m.iloc[0]
            persen = 100 * float(m["damp_cm"]) / amp_r if amp_r else np.nan
            potong.append(html.Span([html.B(f"{model}: ", style={"color": _MODEL_WARNA[model]}),
                                     f"{_idn(m['damp_cm'], 2, sign=True)} cm ({_idn(persen, 1, sign=True)}%), "
                                     f"fase {_idn(m['dfase_deg'], 1, sign=True)}\u00b0   "]))
        # [SITASI] 
        catatan_m2 = []
        if str(nama_k).upper() == "M2":
            catatan_m2 = [
                html.Br(),
                html.Span("Pada studi pembandingan model global dengan stasiun di Indonesia, selisih amplitudo "
                          "atau fase M2 juga tercatat sebagai penyebab utama perbedaan model dan observasi",
                          style={"color": UI_MUTED}),
                radar_cite(1),
                html.Span(".", style={"color": UI_MUTED}),
            ]
        isi.append(html.Div(
            [html.B(f"Konstanta dominan {nama_k} ", style={"color": UI_NAVY}),
             html.Span(f"(radar {_idn(amp_r)} cm) - selisih model terhadap radar: ", style={"color": UI_MUTED}),
             *potong, *catatan_m2],
            style={"marginTop": "14px", "backgroundColor": UI_TINT, "borderRadius": "10px",
                   "padding": "10px 14px", "fontSize": "13px", "lineHeight": "1.7"}))

    # 4. peringatan lag (hanya bila ada)
    lag_besar = [m for m, b in deret.items()
                 if b.get("lag_terbaik_jam") is not None and not pd.isna(b["lag_terbaik_jam"])
                 and abs(int(round(b["lag_terbaik_jam"]))) >= 1]
    if lag_besar:
        isi.append(html.Div(
            f"Terdapat pergeseran waktu pada {' dan '.join(lag_besar)}. Periksa zona waktu data radar; "
            "pergeseran konsisten biasanya berarti beda zona waktu, bukan kesalahan model.",
            style={"marginTop": "10px", "backgroundColor": "#fff8e6", "borderLeft": "4px solid #d68910",
                   "borderRadius": "8px", "padding": "9px 14px", "fontSize": "12.5px", "color": UI_TEXT}))

    return html.Div(isi)


# 8e. KETERANGAN PARAMETER PENGOLAHAN
def catatan_sumber_harmonik():
    """Bila ada bulan yang konstanta radarnya dihitung ulang dengan UTide (berkas t_tide tidak ada)."""
    d = _RADAR.get("sumber_harmonik", pd.DataFrame())
    if d.empty or "sumber_harmonik" not in d.columns:
        return []
    utide = d[d["sumber_harmonik"].astype(str).str.contains("UTide", case=False, na=False)]
    if utide.empty:
        return []
    daftar = "; ".join(f"{r['stasiun']} {r['bulan']}" for _, r in utide.iterrows())
    return [[f"Konstanta radar pada bulan berikut dihitung ulang dengan UTide karena berkas hasil t_tide (tes0.py) "
             f"tidak ditemukan: {daftar}. Bandingkan antar bulan dengan hati-hati."]]

def build_radar_info_parameter(par, diperbarui):
    if not par:
        return html.P("Parameter pengolahan belum tersedia (berkas hasil GOT123s.py belum ditemukan).",
                      style={"fontStyle": "italic", "color": UI_MUTED})
    def p(kunci, default="-"):
        return par.get(kunci, default)
    sumber_kode = str(p("HARMONIK_SUMBER")).strip().lower()
    sumber_harmonik = {
        "ttide_file": "t_tide",
        "ttide_db": "t_tide",
        "utide": "UTide",
    }.get(sumber_kode, sumber_kode)
    # T_Tide -> R3, R4, R6, R7 ; UTide -> R5
    if sumber_kode in ("ttide_file", "ttide_db"):
        sitasi_harmonik = [radar_cite(3, 4, 6, 7)]
    elif sumber_kode == "utide":
        sitasi_harmonik = [radar_cite(5)]
    else:
        sitasi_harmonik = []
    qc_aktif = str(p("QC_AKTIF")).lower() in ("true", "1")
    item = [
        [SUMBER_DATA_RADAR],
        [f"Model yang dibandingkan: {p('MODEL')}; titik model diambil pada koordinat stasiun radar, "
         f"metode interpolasi '{p('METODE_INTERPOLASI')}'."],
        ([f"Kontrol kualitas data radar per menit: nilai macet (datar >= {p('QC_RUN_DATAR_MENIT')} menit) dan "
          f"lonjakan dari median berjalan {p('QC_JENDELA_MENIT')} menit (ambang {p('QC_N_SIGMA')} sigma, "
          f"minimum {p('QC_MIN_AMBANG_M')} m) dibuang. Lonjakan mendadak akibat gangguan sensor atau kesalahan "
          "pengukuran juga diperlakukan sebagai data menyimpang pada studi terdahulu",
          radar_cite(5), "."]
         if qc_aktif else ["Kontrol kualitas data radar per menit tidak diaktifkan pada pengolahan terakhir."]),
        [f"Rata-rata per jam dengan minimal {p('MIN_SAMPEL_PER_JAM')} sampel per jam; jam kosong diinterpolasi "
         f"paling banyak {p('INTERP_LIMIT_JAM')} jam berurutan."],
        [f"Konstanta harmonik radar dari {sumber_harmonik}", *sitasi_harmonik,
         f"; hanya konstanta dengan SNR > {p('SNR_MIN')} yang dibandingkan dengan model", radar_cite(4), "."],
        ["Pembandingan dilakukan per bulan (sekitar 28-31 hari data per stasiun). Rekaman yang terlalu pendek "
         "(5 jam atau 24 jam) terbukti menghasilkan konstanta dan elevasi yang tidak stabil, sehingga disarankan "
         "data minimal 15 hari dan idealnya sekitar 30 hari (satu siklus bulan)", radar_cite(3, 4), "."],
        [f"Pencarian lag terbaik dibatasi sampai +/- {p('MAKS_LAG_JAM')} jam."],
        *catatan_sumber_harmonik(),
        ["Waktu seluruh data ditampilkan dalam UTC."],
        ]
    teks_update = ""
    if diperbarui is not None and not pd.isna(diperbarui):
        teks_update = f"Berkas hasil pengolahan radar terakhir diperbarui pada {pd.Timestamp(diperbarui).strftime('%d/%m/%Y %H:%M')}."
    return html.Div([
        html.Ul([html.Li(t) for t in item], style={"margin": "0 0 8px 0", "paddingLeft": "20px",
                                                    "fontSize": "13.5px", "lineHeight": "1.7"}),
        html.P(teks_update, style={"fontSize": "12.5px", "color": UI_MUTED, "fontStyle": "italic", "margin": "0"}),
    ])

# PANEL HASIL ANALISIS HARMONIK RADAR
def build_ttide_panel(stasiun, bulan_no):
    rk = ttide_rekap_baris(stasiun, bulan_no)
    ev = ttide_elevasi(stasiun, bulan_no)
    if rk is None and ev is None:
        return create_info_card(
            "Hasil analisis harmonik t_tide untuk pilihan ini belum ditemukan. Jalankan 'tes0.py' sampai terbentuk "
            "'rekap_semua_bulan.xlsx' dan 'hasil_harmonik_...xlsx', atau set environment variable PASUT_TTIDE_DIR "
            "ke folder keluarannya."
        )

    isi = []
    if rk is not None:
        def _g(k):
            return rk.get(k)
        formzahl, tipe = _g("Formzahl"), _g("Tipe pasut")
        n_sig, n_tot = _g("Signifikan"), _g("Konstanta total")
        chip = []
        if formzahl is not None and not pd.isna(formzahl):
            chip.append(_chip_info("Formzahl", f"{_idn(formzahl, 2)} ({tipe})"))
        if n_sig is not None and not pd.isna(n_sig):
            chip.append(_chip_info("Konstanta signifikan", f"{int(n_sig)} dari {int(n_tot)}"))
        for label, kunci in (("Jam total", "Jam total"), ("Jam interpolasi", "Jam interpolasi"),
                             ("Jam outlier dibuang", "Jam outlier dibuang"), ("Jam kosong (NaN)", "Jam NaN")):
            v = _g(kunci)
            if v is not None and not pd.isna(v):
                chip.append(_chip_info(label, f"{int(v):,}".replace(",", ".")))
        isi.append(html.Div(chip, style={"marginBottom": "6px"}))

    if ev is not None:
        kartu = [
            create_card("HHWL", _num(ev.get("HHWL"), 3), "m", accent=COLOR_HIGH),
            create_card("MHWL", _num(ev.get("MHWL"), 3), "m", accent="#f5b041"),
            create_card("MSL (S0)", _num(ev.get("S0/MSL"), 3), "m", accent=COLOR_MSL),
            create_card("MLWL", _num(ev.get("MLWL"), 3), "m", accent="#5dade2"),
            create_card("LLWL", _num(ev.get("LLWL"), 3), "m", accent=COLOR_LOW),
            create_card("Z0", _num(ev.get("Z0"), 3), "m", accent=COLOR_ACCENT),
        ]
        isi.append(html.Div(kartu, style={"display": "flex", "gap": "14px", "flexWrap": "wrap",
                                          "margin": "10px 0 4px 0"}))
        isi.append(html.P(
            f"Elevasi penting dihitung dari konstanta harmonik radar terhadap datum sensor radar (bukan terhadap MSL "
            f"model): Z0 = jumlah amplitudo {TTIDE_KONSTA_Z0}; HHWL dan LLWL = MSL \u00b1 Z0; MHWL dan MLWL = MSL "
            f"\u00b1 jumlah amplitudo {TTIDE_KONSTA_MHWL}.",
            style={"fontSize": "12px", "color": UI_MUTED, "fontStyle": "italic", "margin": "6px 2px 0 2px"},
        ))
    return html.Div(isi)

def build_ttide_table(stasiun, bulan_no):
    t = ttide_tabel_konstanta(stasiun, bulan_no)
    if t.empty:
        return []
    kolom = {"Konstanta": "konstanta", "Periode (jam)": "periode", "Amplitudo (cm)": "amp",
             "Error Amp (cm)": "err_amp", "Fase (deg)": "fase", "Error Fase (deg)": "err_fase",
             "SNR": "snr", "Signifikan (SNR>1)": "signifikan"}
    if not all(k in t.columns for k in kolom):
        return []
    t = t[list(kolom)].rename(columns=kolom)
    for k, d in (("periode", 2), ("amp", 2), ("err_amp", 2), ("fase", 1), ("err_fase", 1), ("snr", 1)):
        t[k] = pd.to_numeric(t[k], errors="coerce").round(d)
    return t.to_dict("records")

# 9. FUNGSI KARTU STATISTIK
def create_card(title, value, unit="", accent=COLOR_ACCENT):
    return html.Div(
        [
            html.Div(
                title,
                style={
                    "fontSize": "13px",
                    "fontWeight": "600",
                    "color": "#5b6b73",
                    "marginBottom": "8px",
                    "textTransform": "uppercase",
                    "letterSpacing": "0.4px",
                },
            ),
            html.Div(
                f"{value} {unit}",
                style={"fontSize": "26px", "fontWeight": "700", "color": "#1c2b33"},
            ),
        ],
        className="stat-card",
        style={
            "backgroundColor": "white",
            "padding": "18px 20px",
            "borderRadius": "14px",
            "borderLeft": f"4px solid {accent}",
            "boxShadow": "0 2px 10px rgba(15, 60, 80, 0.08)",
            "textAlign": "left",
            "flex": "1",
            "minWidth": "170px",
        },
    )

def create_info_card(message, tone="info"):
    accent = COLOR_ACCENT if tone == "info" else "#c0392b"
    return html.Div(
        message,
        style={
            "backgroundColor": "#f7f8fd" if tone == "info" else "#fdf1f0",
            "border": f"1px dashed {accent}",
            "borderRadius": "12px",
            "padding": "18px 20px",
            "color": "#48606b" if tone == "info" else "#943126",
            "fontSize": "14px",
            "width": "100%",
        },
    )

# 9b. PETA LOKASI STASIUN
OSM_TILE_URL = "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
OSM_ATTRIBUTION = (
    '&copy; <a href="https://www.openstreetmap.org/copyright">'
    "OpenStreetMap</a> contributors"
)
STATION_MAP_CENTER = [
    sum(lat for _, lat in valid_stations.values()) / len(valid_stations),
    sum(lon for lon, _ in valid_stations.values()) / len(valid_stations),
]
STATION_MAP_ZOOM = 9
COLOR_PIN_SELECTED = "#c0392b"
COLOR_PIN_UNSELECTED = "#154360"
def _pin_icon_options(color, is_selected):
    width, height = (34, 46) if is_selected else (26, 36)
    svg = f"""
    <svg width="{width}" height="{height}" viewBox="0 0 30 42"
         xmlns="http://www.w3.org/2000/svg"
         style="filter: drop-shadow(0 2px 2px rgba(0,0,0,0.35));">
        <path d="M15 0C6.7 0 0 6.7 0 15c0 11.25 15 27 15 27s15-15.75 15-27C30 6.7 23.3 0 15 0z"
              fill="{color}" stroke="#ffffff" stroke-width="1.6"/>
        <circle cx="15" cy="15" r="6" fill="#ffffff"/>
    </svg>
    """
    return dict(
        html=svg,
        className="station-pin-icon",
        iconSize=[width, height],
        iconAnchor=[width / 2, height],
    )
def build_station_markers(selected_station=None):
    markers = []
    for name, (lon, lat) in valid_stations.items():
        is_selected = name == selected_station
        pin_color = COLOR_PIN_SELECTED if is_selected else COLOR_PIN_UNSELECTED
        marker = dl.DivMarker(
            position=[lat, lon],
            iconOptions=_pin_icon_options(pin_color, is_selected),
            children=[
                dl.Tooltip(name),
                dl.Popup(
                    html.Div([html.B(name), html.Br(), f"Lon: {lon:.6f}", html.Br(), f"Lat: {lat:.6f}"])
                ),
            ],
        )
        # DivMarker tidak memperbarui ikonnya bila iconOptions berubah. Pin terpilih dibungkus
        # LayerGroup (tipe komponen berbeda) agar React membuat ulang marker tersebut dan
        # warna merahnya benar-benar berpindah saat stasiun diganti.
        markers.append(dl.LayerGroup(children=[marker]) if is_selected else marker)

    return markers
def build_station_map_layers(selected_station=None):
    return [dl.TileLayer(url=OSM_TILE_URL, attribution=OSM_ATTRIBUTION)] + build_station_markers(selected_station)

# 10. FUNGSI DATA DASHBOARD - PREDIKSI GOT4.10
def compute_dashboard_data(selected_station, selected_year, selected_month):
    # data bulan terpilih diambil dari CSV hasil pengolahan (sudah dimuat di memori)
    month_df = ambil_prediksi(selected_station, selected_year, MONTH_NAME_TO_NUMBER[selected_month])
    if month_df.empty:

        empty_fig = go.Figure()
        empty_fig.update_layout(
            title="Data tidak tersedia",
            xaxis_title="Waktu",
            yaxis_title="Elevasi terhadap MSL (m)",
            template="plotly_white",
        )

        return {
            "minimum": None, "maximum": None, "mean": None, "msl": None,
            "jumlah_data": 0, "tide_fig": empty_fig, "weekly_fig": empty_fig,
            "table_df": pd.DataFrame(),
        }

    minimum = month_df["tide_m"].min()
    maximum = month_df["tide_m"].max()
    mean = month_df["tide_m"].mean()
    msl = mean
    jumlah_data = len(month_df)

    # GRAFIK PASUT
    tide_fig = go.Figure()
    tide_fig.add_trace(
        go.Scatter(
            x=month_df["datetime_wib"],
            y=month_df["tide_m"],
            mode="lines",
            name="Prediksi Pasut",
            line={"width": 2, "color": COLOR_TIDE_LINE},
            hovertemplate="<b>Waktu:</b> %{x}<br><b>Elevasi:</b> %{y:.3f} m<extra></extra>",
        )
    )

    tide_fig.add_trace(
        go.Scatter(
            x=[month_df["datetime_wib"].min(), month_df["datetime_wib"].max()],
            y=[msl, msl],
            mode="lines",
            name=f"MSL (Mean Sea Level) = {msl:.3f} m",
            line=dict(color=COLOR_MSL, dash="dash", width=1.6),
            visible="legendonly",
            hovertemplate=f"MSL (Mean Sea Level): {msl:.3f} m<extra></extra>",
        )
    )

    idx_high = month_df["tide_m"].idxmax()
    idx_low = month_df["tide_m"].idxmin()
    t_high = month_df.loc[idx_high, "datetime_wib"]
    v_high = month_df.loc[idx_high, "tide_m"]
    t_low = month_df.loc[idx_low, "datetime_wib"]
    v_low = month_df.loc[idx_low, "tide_m"]
    tide_fig.add_trace(
        go.Scatter(
            x=[t_high], y=[v_high], mode="markers+text", name="Pasang tertinggi",
            marker={"symbol": "triangle-up", "size": 12, "color": COLOR_HIGH},
            text=[f"Pasang tertinggi: {v_high:.3f} m"], textposition="top center",
            textfont={"size": 10, "color": COLOR_HIGH},
            hovertemplate="<b>Pasang tertinggi</b><br>Waktu: %{x}<br>Elevasi: %{y:.3f} m<extra></extra>",
        )
    )
    tide_fig.add_trace(
        go.Scatter(
            x=[t_low], y=[v_low], mode="markers+text", name="Surut terendah",
            marker={"symbol": "triangle-down", "size": 12, "color": COLOR_LOW},
            text=[f"Surut terendah: {v_low:.3f} m"], textposition="bottom center",
            textfont={"size": 10, "color": COLOR_LOW},
            hovertemplate="<b>Surut terendah</b><br>Waktu: %{x}<br>Elevasi: %{y:.3f} m<extra></extra>",
        )
    )
    tide_fig.update_layout(
        title=(
            f"Prediksi Pasang Surut GOT4.10 - {selected_station} "
            f"{month_indonesia[selected_month]} {selected_year} "
            "(elevasi terhadap MSL, satuan meter)"
        ),
        xaxis_title="Tanggal dan Waktu (WIB)",
        yaxis_title="Elevasi Pasang Surut terhadap MSL (m)",
        hovermode="x unified",
        template="plotly_white",
        height=550,
        legend=dict(bgcolor="rgba(255,255,255,0.85)", bordercolor="#dfe6e9", borderwidth=1),
        font=dict(family="Poppins, Arial, sans-serif"),
    )

    # STATISTIK MINGGUAN
    month_number = MONTH_NAME_TO_NUMBER[selected_month]
    month_info_tahun_ini = ALL_WEEKS_BY_YEAR.get(selected_year, {}).get(month_number)
    if month_info_tahun_ini is not None:
        _, weekly_stats_live = assign_weeks_and_stats(
            month_df, month_info_tahun_ini, selected_station, selected_year,
            selected_month, month_number,
        )
        weekly_df = pd.DataFrame(weekly_stats_live)
    else:
        weekly_df = pd.DataFrame()
    weekly_fig = go.Figure()
    if not weekly_df.empty:
        weekly_fig.add_trace(
            go.Bar(
                x=weekly_df["week_in_month"], y=weekly_df["minimum_m"], name="Minimum (m)",
                marker_color="#5dade2",
                hovertemplate="Minggu %{x}<br>Minimum: %{y:.3f} m<extra></extra>",
            )
        )
        weekly_fig.add_trace(
            go.Bar(
                x=weekly_df["week_in_month"], y=weekly_df["maximum_m"], name="Maksimum (m)",
                marker_color="#f5b041",
                hovertemplate="Minggu %{x}<br>Maksimum: %{y:.3f} m<extra></extra>",
            )
        )
        weekly_fig.add_trace(
            go.Scatter(
                x=weekly_df["week_in_month"], y=weekly_df["mean_m"], mode="lines+markers",
                name="Rata-rata mingguan (m)", line=dict(color="#117864", width=2),
                hovertemplate="Minggu %{x}<br>Rata-rata: %{y:.3f} m<extra></extra>",
            )
        )
        weekly_fig.add_trace(
            go.Scatter(
                x=[weekly_df["week_in_month"].min(), weekly_df["week_in_month"].max()],
                y=[msl, msl],
                mode="lines",
                name=f"MSL bulanan = {msl:.3f} m",
                line=dict(color=COLOR_MSL, dash="dot", width=1.6),
                visible="legendonly",
                hovertemplate=f"MSL bulanan: {msl:.3f} m<extra></extra>",
            )
        )
    weekly_fig.update_layout(
        title=(
            f"Statistik Mingguan - {selected_station} - "
            f"{month_indonesia[selected_month]} {selected_year} "
            "(satuan: meter terhadap MSL)"
        ),
        xaxis_title="Minggu",
        yaxis_title="Elevasi terhadap MSL (m)",
        barmode="group",
        template="plotly_white",
        height=500,
        legend=dict(
            orientation="h", yanchor="bottom", y=1.05, xanchor="right", x=1,
            bgcolor="rgba(255,255,255,0.85)", bordercolor="#dfe6e9", borderwidth=1,
        ),
        font=dict(family="Poppins, Arial, sans-serif"),
    )

    # TABEL MINGGUAN
    table_df = weekly_df.copy()
    if not table_df.empty:
        for col in ["minimum_m", "maximum_m", "mean_m", "range_m"]:
            table_df[col] = table_df[col].round(3)
        table_df = table_df[
            ["week_in_month", "week_of_year", "start_date", "end_date", "jumlah_data_valid",
             "minimum_m", "maximum_m", "mean_m", "range_m"]
        ]

    return {
        "minimum": minimum, "maximum": maximum, "mean": mean, "msl": msl,
        "jumlah_data": jumlah_data, "tide_fig": tide_fig, "weekly_fig": weekly_fig,
        "table_df": table_df,
    }

# 11. FUNGSI DATA VALIDASI SILANG EOT20
def compute_validation_data(selected_station, selected_year, selected_month):
    # data validasi & metrik diambil dari CSV hasil validasi (sudah dimuat di memori)
    month_number = MONTH_NAME_TO_NUMBER[selected_month]
    station_val_df = ambil_validasi_eot20(selected_station, selected_year, month_number)
    if station_val_df.empty:
        return None
    station_val_df = station_val_df.sort_values("datetime_utc")
    metric_row = ambil_metrik_eot20(selected_station, selected_year, month_number)
    if metric_row.empty:
        diff = station_val_df["tide_m_got410"] - station_val_df["tide_m_eot20"]
        metrik = {
            "rmse_m": float(np.sqrt(np.mean(diff ** 2))),
            "mae_m": float(np.mean(np.abs(diff))),
            "korelasi_r": float(
                station_val_df["tide_m_got410"].corr(station_val_df["tide_m_eot20"])
            ),
            "willmott_d": np.nan,
            "n_data": len(station_val_df),
        }
    else:
        metrik = metric_row.iloc[0].to_dict()

    # FIGURE VALIDASI EOT20
    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True, row_heights=[0.65, 0.35],
        vertical_spacing=0.10,
        subplot_titles=("Perbandingan GOT4.10 vs EOT20", "Selisih (GOT4.10 - EOT20)"),
    )
    fig.add_trace(
        go.Scatter(
            x=station_val_df["datetime_utc"], y=station_val_df["tide_m_got410"],
            name="GOT4.10", line=dict(color=COLOR_MODEL_A, width=2),
            hovertemplate="<b>GOT4.10</b><br>Waktu: %{x}<br>Elevasi: %{y:.3f} m<extra></extra>",
        ),
        row=1, col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=station_val_df["datetime_utc"], y=station_val_df["tide_m_eot20"],
            name="EOT20", line=dict(color=COLOR_MODEL_B, width=2, dash="dash"),
            hovertemplate="<b>EOT20</b><br>Waktu: %{x}<br>Elevasi: %{y:.3f} m<extra></extra>",
        ),
        row=1, col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=station_val_df["datetime_utc"], y=station_val_df["selisih_m"],
            name="Selisih", line=dict(color=COLOR_RESIDUAL, width=1.5), fill="tozeroy",
            hovertemplate="Waktu: %{x}<br>Selisih: %{y:.3f} m<extra></extra>",
        ),
        row=2, col=1,
    )
    fig.add_hline(y=0, line_dash="dot", line_color="#95a5a6", row=2, col=1)
    fig.update_yaxes(title_text="Elevasi terhadap MSL (m)", row=1, col=1)
    fig.update_yaxes(title_text="Selisih (m)", row=2, col=1)
    fig.update_xaxes(title_text="Tanggal dan Waktu (UTC)", row=2, col=1)
    fig.update_layout(
        title=(
            f"Validasi Silang - {selected_station} - "
            f"{month_indonesia[selected_month]} {selected_year}"
        ),
        template="plotly_white",
        height=580,
        hovermode="x unified",
        legend=dict(
            orientation="h", yanchor="bottom", y=1.08, xanchor="right", x=1,
            bgcolor="rgba(255,255,255,0.85)", bordercolor="#dfe6e9", borderwidth=1,
        ),
        font=dict(family="Poppins, Arial, sans-serif"),
    )

    return {"fig": fig, "metrik": metrik, "table_df": station_val_df}

# 12. FUNGSI BUAT PDF
def build_pdf_report(selected_station, selected_year, selected_month, data, validation_data):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4, topMargin=1.5 * cm, bottomMargin=1.5 * cm,
        leftMargin=1.5 * cm, rightMargin=1.5 * cm,
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("TitleCustom", parent=styles["Title"], fontSize=16, spaceAfter=4)
    subtitle_style = ParagraphStyle(
        "SubtitleCustom", parent=styles["Normal"], fontSize=11, alignment=1, spaceAfter=2
    )
    instansi_style = ParagraphStyle(
        "InstansiCustom", parent=styles["Normal"], fontSize=9, alignment=1,
        textColor=rl_colors.HexColor("#555555"), spaceAfter=2,
    )
    heading_style = styles["Heading2"]
    elements = []
    # LOGO
    logo_row = []
    if LOGO_BRIN.exists():
        logo_row.append(RLImage(str(LOGO_BRIN), width=2.2 * cm, height=2.2 * cm))
    if LOGO_DKP.exists():
        logo_row.append(RLImage(str(LOGO_DKP), width=2.2 * cm, height=2.2 * cm))
    if logo_row:
        logo_table = Table([logo_row])
        logo_table.setStyle(
            TableStyle([
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ])
        )
        elements.append(logo_table)
        elements.append(Spacer(1, 0.3 * cm))

    # JUDUL PDF
    elements.append(Paragraph("DASHBOARD PREDIKSI & VALIDASI PASANG SURUT LAUT", title_style))
    elements.append(
        Paragraph(f"Model GOT4.10 (utama) & EOT20 (validasi) - Tahun {YEAR_LABEL}", subtitle_style)
    )
    elements.append(Paragraph("13 Stasiun Pantai Selatan Daerah Istimewa Yogyakarta", subtitle_style))
    elements.append(
        Paragraph(f"Prediksi ini dilakukan oleh {INSTANSI_NAMA} - {INSTANSI_HOMEBASE}", instansi_style)
    )
    elements.append(Spacer(1, 0.4 * cm))
    station_lon, station_lat = valid_stations.get(selected_station, (None, None))
    if station_lon is not None and station_lat is not None:
        koordinat_text = f"Lon <b>{station_lon:.6f}</b>, Lat <b>{station_lat:.6f}</b>"
    else:
        koordinat_text = "-"
    elements.append(
        Paragraph(
            f"Stasiun: <b>{selected_station}</b> &nbsp;&nbsp;|&nbsp;&nbsp; "
            f"Tahun: <b>{selected_year}</b> &nbsp;&nbsp;|&nbsp;&nbsp; "
            f"Bulan: <b>{month_indonesia[selected_month]}</b>",
            styles["Normal"],
        )
    )
    elements.append(
        Paragraph(f"Koordinat Stasiun: {koordinat_text}", styles["Normal"])
    )
    elements.append(Spacer(1, 0.2 * cm))
    elements.append(Paragraph(KETERANGAN_MSL, styles["Normal"]))
    elements.append(Spacer(1, 0.4 * cm))
    # RINGKASAN STATISTIK
    elements.append(Paragraph("Ringkasan Statistik Prediksi", heading_style))
    if data["jumlah_data"] > 0:
        summary_table_data = [
            ["Minimum (m)", "Maksimum (m)", "MSL/Rata-rata (m)", "Jumlah Data"],
            [f"{data['minimum']:.3f}", f"{data['maximum']:.3f}", f"{data['msl']:.3f}", f"{data['jumlah_data']:,}"],
        ]
    else:
        summary_table_data = [
            ["Minimum (m)", "Maksimum (m)", "MSL/Rata-rata (m)", "Jumlah Data"],
            ["-", "-", "-", "0"],
        ]
    summary_table = Table(summary_table_data, hAlign="LEFT")
    summary_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), rl_colors.HexColor("#eef1f8")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 0.5, rl_colors.grey),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
        ])
    )
    elements.append(summary_table)
    elements.append(Spacer(1, 0.5 * cm))

    # GRAFIK PREDIKSI
    elements.append(Paragraph("Grafik Prediksi Pasang Surut", heading_style))

    try:
        tide_png = data["tide_fig"].to_image(format="png", width=900, height=450, scale=2)
        elements.append(RLImage(io.BytesIO(tide_png), width=17 * cm, height=8.5 * cm))
    except Exception as e:
        elements.append(
            Paragraph(f"Grafik tidak dapat disertakan (paket 'kaleido' belum terpasang): {e}", styles["Normal"])
        )

    elements.append(Spacer(1, 0.5 * cm))

    # VALIDASI EOT20
    elements.append(Paragraph("Validasi Silang: GOT4.10 vs EOT20", heading_style))
    elements.append(Paragraph(KETERANGAN_VALIDASI, styles["Normal"]))
    elements.append(Spacer(1, 0.2 * cm))

    if validation_data is not None:

        metrik = validation_data["metrik"]

        val_table_data = [
            ["RMSE (m)", "MAE (m)", "Korelasi (r)", "Willmott's d", "Jumlah Data"],
            [
                f"{metrik['rmse_m']:.4f}",
                f"{metrik['mae_m']:.4f}",
                f"{metrik['korelasi_r']:.4f}",
                "-" if pd.isna(metrik.get("willmott_d")) else f"{metrik['willmott_d']:.4f}",
                f"{int(metrik['n_data']):,}",
            ],
        ]
        val_table = Table(val_table_data, hAlign="LEFT")
        val_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), rl_colors.HexColor("#eef1f8")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("GRID", (0, 0), (-1, -1), 0.5, rl_colors.grey),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
            ])
        )
        elements.append(val_table)
        elements.append(Spacer(1, 0.4 * cm))
        try:
            val_png = validation_data["fig"].to_image(format="png", width=1100, height=620, scale=2)
            elements.append(RLImage(io.BytesIO(val_png), width=17 * cm, height=9.6 * cm))
        except Exception as e:
            elements.append(
                Paragraph(
                    f"Grafik deret waktu validasi tidak dapat disertakan: {e}. "
                    "Pastikan paket kaleido tersedia pada environment Python yang menjalankan dashboard.",
                    styles["Normal"],
                )
            )

        # GRAFIK TAMBAHAN VALIDASI: DIAGRAM SEBAR GOT4.10 VS EOT20
        # Sumbu X = GOT4.10, sumbu Y = EOT20. Garis 1:1 menunjukkan
        # kondisi ketika kedua model menghasilkan elevasi yang sama.
        val_df = validation_data.get("table_df", pd.DataFrame()).copy()
        kolom_sebar = ["tide_m_got410", "tide_m_eot20"]
        if all(k in val_df.columns for k in kolom_sebar):
            sebar_df = val_df[kolom_sebar].apply(pd.to_numeric, errors="coerce")
            sebar_df = sebar_df.replace([np.inf, -np.inf], np.nan).dropna()

            if not sebar_df.empty:
                x = sebar_df["tide_m_got410"].to_numpy(dtype=float)
                y = sebar_df["tide_m_eot20"].to_numpy(dtype=float)
                batas_min = float(min(np.min(x), np.min(y)))
                batas_maks = float(max(np.max(x), np.max(y)))
                if batas_min == batas_maks:
                    tambahan = max(abs(batas_min) * 0.05, 0.01)
                    batas_min -= tambahan
                    batas_maks += tambahan

                fig_sebar_validasi = go.Figure()
                fig_sebar_validasi.add_trace(go.Scatter(
                    x=x, y=y, mode="markers", name="Pasangan elevasi",
                    marker=dict(size=5, opacity=0.48, color=COLOR_ACCENT),
                    hovertemplate="GOT4.10: %{x:.4f} m<br>EOT20: %{y:.4f} m<extra></extra>",
                ))
                fig_sebar_validasi.add_trace(go.Scatter(
                    x=[batas_min, batas_maks], y=[batas_min, batas_maks],
                    mode="lines", name="Garis referensi 1:1",
                    line=dict(color="#c0392b", width=2, dash="dash"),
                    hoverinfo="skip",
                ))
                fig_sebar_validasi.update_layout(
                    title="Diagram Sebar Elevasi GOT4.10 vs EOT20",
                    xaxis_title="Elevasi GOT4.10 (m)",
                    yaxis_title="Elevasi EOT20 (m)",
                    template="plotly_white",
                    height=520,
                    width=900,
                    font=dict(family="Helvetica", color="#33415c"),
                    margin=dict(l=65, r=35, t=75, b=65),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02,
                                xanchor="right", x=1),
                )
                fig_sebar_validasi.update_xaxes(
                    range=[batas_min, batas_maks], showgrid=True, gridcolor="#edf1f3"
                )
                fig_sebar_validasi.update_yaxes(
                    range=[batas_min, batas_maks], showgrid=True, gridcolor="#edf1f3",
                    scaleanchor="x", scaleratio=1,
                )

                elements.append(Spacer(1, 0.2 * cm))
                elements.append(Paragraph("Diagram Sebar Kesesuaian Kedua Model", heading_style))
                elements.append(Paragraph(
                    "Setiap titik merepresentasikan pasangan elevasi GOT4.10 dan EOT20 "
                    "pada waktu yang sama. Titik yang semakin dekat dengan garis 1:1 "
                    "menunjukkan nilai kedua model yang semakin berdekatan.",
                    styles["Normal"],
                ))
                try:
                    sebar_png = fig_sebar_validasi.to_image(
                        format="png", width=1000, height=580, scale=2
                    )
                    elements.append(RLImage(
                        io.BytesIO(sebar_png), width=15.5 * cm, height=9.0 * cm
                    ))
                except Exception as e:
                    elements.append(Paragraph(
                        f"Diagram sebar tidak dapat disertakan: {e}. "
                        "Pastikan paket kaleido tersedia pada environment Python dashboard.",
                        styles["Normal"],
                    ))
            else:
                elements.append(Paragraph(
                    "Diagram sebar tidak dibuat karena pasangan data GOT4.10 dan EOT20 "
                    "tidak memiliki nilai numerik yang valid.",
                    styles["Normal"],
                ))
        else:
            elements.append(Paragraph(
                "Diagram sebar tidak dibuat karena kolom tide_m_got410 dan/atau "
                "tide_m_eot20 tidak ditemukan pada data validasi.",
                styles["Normal"],
            ))
    else:
        elements.append(
            Paragraph(
                "Data validasi EOT20 belum tersedia untuk kombinasi stasiun, tahun, dan bulan ini.",
                styles["Normal"],
            )
        )

    elements.append(Spacer(1, 0.5 * cm))

    # STATISTIK MINGGUAN
    elements.append(Paragraph("Statistik Mingguan", heading_style))
    elements.append(Spacer(1, 0.2 * cm))

    try:
        weekly_png = data["weekly_fig"].to_image(format="png", width=900, height=420, scale=2)
        elements.append(RLImage(io.BytesIO(weekly_png), width=17 * cm, height=7.9 * cm))
    except Exception as e:
        elements.append(
            Paragraph(f"Grafik tidak dapat disertakan (paket 'kaleido' belum terpasang): {e}", styles["Normal"])
        )

    elements.append(Spacer(1, 0.5 * cm))

    # TABEL STATISTIK MINGGUAN
    elements.append(Paragraph("Tabel Statistik Mingguan", heading_style))
    table_df = data["table_df"]
    if not table_df.empty:
        header = [
            "Minggu", "Tanggal Mulai", "Tanggal Akhir", "Jumlah Data",
            "Min (m)", "Maks (m)", "MSL/Rata-rata (m)", "Range (m)",
        ]
        rows = table_df.drop(columns=["week_of_year"]).values.tolist()
        pdf_table = Table([header] + rows, hAlign="LEFT", repeatRows=1)
        pdf_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), rl_colors.HexColor("#eef1f8")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("GRID", (0, 0), (-1, -1), 0.5, rl_colors.grey),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
            ])
        )
        elements.append(pdf_table)

    else:
        elements.append(Paragraph("Tidak ada data untuk bulan ini.", styles["Normal"]))

    elements.append(Spacer(1, 0.5 * cm))

    # INFORMASI ANALISIS
    elements.append(Paragraph("Informasi Analisis", heading_style))
    elements.append(Paragraph("Model utama: GOT4.10. Model validasi silang: EOT20.", styles["Normal"]))
    elements.append(
        Paragraph("Data diproses menggunakan pyTMD dengan interval prediksi 1 jam.", styles["Normal"])
    )
    elements.append(
        Paragraph("Waktu prediksi ditampilkan dalam WIB; waktu validasi dalam UTC.", styles["Normal"])
    )
    elements.append(Paragraph(KETERANGAN_MSL, styles["Normal"]))
    elements.append(Paragraph(KETERANGAN_PASANG_SURUT, styles["Normal"]))
    elements.append(Paragraph(KETERANGAN_VALIDASI, styles["Normal"]))
    elements.append(
        Paragraph(f"Prediksi ini dilakukan oleh {INSTANSI_NAMA}, {INSTANSI_HOMEBASE}.", styles["Normal"])
    )

    doc.build(elements)
    buffer.seek(0)

    return buffer


# 12b. [RADAR] PDF VALIDASI RADAR
def _pdf_style_tabel(ukuran=9):
    return TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), rl_colors.HexColor("#eef1f8")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), ukuran),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.5, rl_colors.grey),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ])


def teks_kesimpulan_radar(stasiun, bulan_name, deret):
    """Kesimpulan versi teks (untuk PDF), logikanya sama dengan banner di dashboard."""
    judul = f"{label_stasiun_radar(stasiun)}, {month_indonesia[bulan_name]} {YEAR_VALIDASI_RADAR}"
    got, eot = deret.get("GOT4.10"), deret.get("EOT20")
    out = []
    if got and eot:
        selisih = abs(got["rmse_cm"] - eot["rmse_cm"])
        if selisih < RADAR_BEDA_RMSE_CM:
            out.append(f"<b>GOT4.10 dan EOT20 setara</b> dalam mengikuti radar ({judul}): RMSE "
                       f"{_idn(got['rmse_cm'])} cm vs {_idn(eot['rmse_cm'])} cm, selisih {_idn(selisih)} cm.")
        else:
            t, l = ("GOT4.10", "EOT20") if got["rmse_cm"] < eot["rmse_cm"] else ("EOT20", "GOT4.10")
            out.append(f"<b>{t} lebih dekat dengan radar</b> ({judul}): RMSE {_idn(deret[t]['rmse_cm'])} cm "
                       f"vs {_idn(deret[l]['rmse_cm'])} cm ({l}); r {_idn(deret[t]['r'], 3)} vs "
                       f"{_idn(deret[l]['r'], 3)}.")
    for model in RADAR_MODELS:
        b = deret.get(model)
        if not b:
            continue
        butir = [f"korelasi {_kata_korelasi(b['r'])} (r = {_idn(b['r'], 3)})"]
        ka = _kata_amplitudo(b.get("kemiringan"))
        if ka:
            butir.append(f"amplitudo {ka} (kemiringan {_idn(b['kemiringan'], 2)})")
        butir.append(f"bias rata-rata {_bias_txt(b['bias_cm'])} cm")
        kl = _kata_lag(b.get("lag_terbaik_jam"))
        if kl:
            butir.append(kl)
        out.append(f"<b>{model}</b>: " + "; ".join(butir) + ".")
    return out


def build_radar_pdf_report(stasiun, bulan_name, deret, kons, detail, seri_df, par, diperbarui):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1.5 * cm, bottomMargin=1.5 * cm,
                            leftMargin=1.5 * cm, rightMargin=1.5 * cm)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("TitleRadar", parent=styles["Title"], fontSize=15, spaceAfter=4)
    sub_style = ParagraphStyle("SubRadar", parent=styles["Normal"], fontSize=11, alignment=1, spaceAfter=2)
    kecil = ParagraphStyle("KecilRadar", parent=styles["Normal"], fontSize=8.5, leading=11)
    h2 = styles["Heading2"]
    el = []

    # logo
    logos = []
    if LOGO_BRIN.exists():
        logos.append(RLImage(str(LOGO_BRIN), width=2.2 * cm, height=2.2 * cm))
    if LOGO_DKP.exists():
        logos.append(RLImage(str(LOGO_DKP), width=2.2 * cm, height=2.2 * cm))
    if logos:
        lt = Table([logos])
        lt.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER"), ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
        el += [lt, Spacer(1, 0.3 * cm)]

    judul = f"{label_stasiun_radar(stasiun)}, {month_indonesia[bulan_name]} {YEAR_VALIDASI_RADAR}"
    el.append(Paragraph(f"VALIDASI PASANG SURUT {YEAR_VALIDASI_RADAR}: RADAR vs GOT4.10 vs EOT20", title_style))
    el.append(Paragraph(f"Stasiun dan bulan: <b>{judul}</b>", sub_style))
    lon, lat = STASIUN.get(stasiun, (None, None))

    if lon is not None and lat is not None:
        teks_koordinat = (
            f"Longitude: <b>{lon:.6f}°</b> &nbsp; | &nbsp; "
            f"Latitude: <b>{lat:.6f}°</b>"
        )
    else:
        teks_koordinat = "Koordinat stasiun tidak tersedia."

    el.append(Paragraph(teks_koordinat, sub_style)) 
    el.append(Paragraph(f"Dibuat oleh {INSTANSI_NAMA} - {INSTANSI_HOMEBASE}", kecil))
    el.append(Spacer(1, 0.3 * cm))
    el.append(Paragraph(KETERANGAN_VALIDASI_RADAR + " [1, 2, 5]", styles["Normal"]))
    el.append(Spacer(1, 0.2 * cm))
    el.append(Paragraph(SUMBER_DATA_RADAR, styles["Normal"]))
    el.append(Spacer(1, 0.3 * cm))

    # kesimpulan
    el.append(Paragraph("Kesimpulan", h2))
    for t in teks_kesimpulan_radar(stasiun, bulan_name, deret):
        el += [Paragraph(t, styles["Normal"]), Spacer(1, 0.1 * cm)]

    # metrik deret waktu
    g, e = deret.get("GOT4.10", {}), deret.get("EOT20", {})
    kg, ke = kons.get("GOT4.10", {}), kons.get("EOT20", {})
    el.append(Paragraph("Ringkasan Metrik", h2))

    def _cocok(k):
        if not k or pd.isna(k.get("n_dibandingkan")) or not k.get("n_dibandingkan"):
            return "-"
        return f"{int(k['n_cocok'])} dari {int(k['n_dibandingkan'])}"

    def _lag(d):
        v = _fl(d, "lag_terbaik_jam")
        return "-" if pd.isna(v) else str(int(round(v)))

    baris = [
        ["Metrik", "GOT4.10", "EOT20"],
        ["RMSE (cm)", _idn(_fl(g, "rmse_cm")), _idn(_fl(e, "rmse_cm"))],
        ["MAE (cm)", _idn(_fl(g, "mae_cm")), _idn(_fl(e, "mae_cm"))],
        ["Bias model - radar (cm)", _bias_txt(_fl(g, "bias_cm")), _bias_txt(_fl(e, "bias_cm"))],
        ["Korelasi (r)", _idn(_fl(g, "r"), 3), _idn(_fl(e, "r"), 3)],
        ["Willmott's d", _idn(_fl(g, "willmott_d"), 3), _idn(_fl(e, "willmott_d"), 3)],
        ["Kemiringan (ideal 1)", _idn(_fl(g, "kemiringan"), 3), _idn(_fl(e, "kemiringan"), 3)],
        ["Lag terbaik (jam)", _lag(g), _lag(e)],
        ["Konstanta cocok", _cocok(kg), _cocok(ke)],
        ["RMSE amplitudo (cm)", _idn(_fl(kg, "rmse_amp_cm")), _idn(_fl(ke, "rmse_amp_cm"))],
        ["RMSE fase (derajat)", _idn(_fl(kg, "rmse_fase_deg"), 1), _idn(_fl(ke, "rmse_fase_deg"), 1)],
        ["RMSE vektor (cm)", _idn(_fl(kg, "rmse_vektor_cm")), _idn(_fl(ke, "rmse_vektor_cm"))],
    ]
    tm = Table(baris, hAlign="LEFT", colWidths=[7 * cm, 4 * cm, 4 * cm])
    tm.setStyle(_pdf_style_tabel(9))
    el += [tm, Spacer(1, 0.4 * cm)]

    # grafik
    def _tambah_fig(fig, w, h, rasio_tinggi):
        try:
            png = fig.to_image(format="png", width=w, height=h, scale=2)
            el.append(RLImage(io.BytesIO(png), width=17 * cm, height=17 * cm * rasio_tinggi))
        except Exception as ex:
            el.append(Paragraph(f"Grafik tidak dapat disertakan (paket 'kaleido' belum terpasang): {ex}",
                                styles["Normal"]))
        el.append(Spacer(1, 0.4 * cm))

    if seri_df is not None and not seri_df.empty:
        el.append(Paragraph("Grafik Deret Waktu", h2))
        _tambah_fig(build_radar_series_fig(seri_df, judul), 900, 640, 640 / 900)
        el.append(Paragraph("Diagram Sebar Model vs Radar", h2))
        _tambah_fig(build_radar_scatter_fig(seri_df, deret), 900, 470, 470 / 900)
    if detail is not None and not detail.empty:
        el.append(Paragraph("Konstanta Harmonik: Radar vs Model", h2))
        _tambah_fig(build_radar_constituent_fig(detail), 900, 560, 560 / 900)
        rows = build_radar_constituent_table(detail)[:10]
        header = ["Kons.", "Amp R", "Amp GOT", "Amp EOT", "Fase R", "Fase GOT", "Fase EOT",
                  "SNR", "Cocok GOT", "Cocok EOT"]
        data = [header] + [[r["konstanta"], r["amp_radar"], r["amp_got"], r["amp_eot"], r["fase_radar"],
                            r["fase_got"], r["fase_eot"], r["snr"], r["cocok_got"], r["cocok_eot"]]
                           for r in rows]
        tk = Table(data, hAlign="LEFT", repeatRows=1)
        tk.setStyle(_pdf_style_tabel(7.5))
        el += [tk, Paragraph("Amplitudo dalam cm, fase dalam derajat (Greenwich). Maksimal 10 konstanta terbesar.",
                             kecil), Spacer(1, 0.4 * cm)]

    # parameter pengolahan
    el.append(Paragraph("Parameter Pengolahan", h2))
    p = lambda k: par.get(k, "-") if par else "-"
    for t in [
        f"Model: {p('MODEL')}; interpolasi titik model: {p('METODE_INTERPOLASI')}.",
        f"Rata-rata per jam, minimal {p('MIN_SAMPEL_PER_JAM')} sampel per jam; interpolasi jam kosong maksimal "
        f"{p('INTERP_LIMIT_JAM')} jam berurutan.",
        f"Hanya konstanta dengan SNR > {p('SNR_MIN')} yang dibandingkan [3, 4].",
        f"Pencarian lag terbaik dibatasi +/- {p('MAKS_LAG_JAM')} jam.",
        "Waktu ditampilkan dalam UTC.",
    ]:
        el.append(Paragraph("- " + t, styles["Normal"]))
    if diperbarui is not None and not pd.isna(diperbarui):
        el.append(Paragraph(f"Berkas hasil pengolahan radar terakhir diperbarui pada "
                            f"{pd.Timestamp(diperbarui).strftime('%d/%m/%Y %H:%M')}.", kecil))

    # rujukan
    el.append(Paragraph("Rujukan", h2))
    for i, r in enumerate(RADAR_RUJUKAN, start=1):
        el.append(Paragraph(f"[{i}] {_rujukan_pdf(r)}", kecil))
        el.append(Spacer(1, 0.1 * cm))
    el += [Spacer(1, 0.3 * cm),
           Paragraph(f"Prediksi ini dilakukan oleh {INSTANSI_NAMA}, {INSTANSI_HOMEBASE}.", kecil)]

    doc.build(el)
    buffer.seek(0)
    return buffer


_T_DATA = _time.perf_counter()  

# 13. MEMBUAT APLIKASI DASHBOARD
app = Dash(
    __name__,
    assets_folder=str(BASE_DIR / "assets"),   
    external_stylesheets=[
        "https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap",
        "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css",
    ],
)

app.title = f"Dashboard Prediksi & Validasi Pasang Surut {YEAR_LABEL}"


# 13b. INDEX STRING
app.index_string = """
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            body {
                margin: 0;
                background: linear-gradient(180deg, #eef1f8 0%, #e3e8f2 100%);
            }
            .stat-card {
                transition: transform 0.15s ease, box-shadow 0.15s ease;
            }
            .stat-card:hover {
                transform: translateY(-3px);
                box-shadow: 0 8px 18px rgba(13, 28, 66, 0.18);
            }
            ::-webkit-scrollbar { height: 8px; width: 8px; }
            ::-webkit-scrollbar-thumb { background: #b7c4cc; border-radius: 4px; }
            .station-pin-icon { background: transparent; border: none; }
            /* --- Informasi Analisis --- */
            .info-grid { display: grid; gap: 18px; grid-template-columns: repeat(auto-fit, minmax(340px, 1fr)); }
            .info-grid-3 { display: grid; gap: 12px; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); }
            .info-summary {
                display: flex; align-items: center; justify-content: space-between;
                padding: 18px 28px; border-radius: 14px; cursor: pointer; list-style: none;
                box-shadow: 0 4px 14px rgba(13, 28, 66, 0.20);
                transition: box-shadow 0.2s ease, filter 0.2s ease; user-select: none;
            }
            .info-summary::-webkit-details-marker { display: none; }
            .info-summary::marker { content: ""; }
            .info-summary:hover { filter: brightness(1.07); box-shadow: 0 6px 18px rgba(13, 28, 66, 0.28); }
            .info-summary:focus-visible { outline: 3px solid rgba(13, 28, 66, 0.35); outline-offset: 2px; }
            .info-chevron-wrap {
                width: 34px; height: 34px; border-radius: 50%; background: rgba(255,255,255,0.18);
                display: flex; align-items: center; justify-content: center; flex: 0 0 34px;
            }
            .info-chevron {
                width: 9px; height: 9px; border-right: 2px solid #ffffff; border-bottom: 2px solid #ffffff;
                transform: rotate(45deg); margin-top: -4px; transition: transform 0.25s ease, margin 0.25s ease;
            }
            .info-details[open] .info-chevron { transform: rotate(-135deg); margin-top: 4px; }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
"""


# 14. HEADER LOGO
logo_components = []
if LOGO_BRIN.exists():
    logo_components.append(html.Img(src="/assets/logo_brin.png", style={"height": "58px", "objectFit": "contain"}))
if LOGO_DKP.exists():
    logo_components.append(html.Img(src="/assets/logo_dkp_diy.png", style={"height": "75px", "objectFit": "contain"}))

FONT_FAMILY = "'Poppins', 'Segoe UI', Arial, sans-serif"

# 14b. FUNGSI CONTAINER
def section_container(children):
    return html.Div(
        children,
        style={
            "backgroundColor": "white",
            "padding": "24px",
            "borderRadius": "16px",
            "boxShadow": "0 4px 16px rgba(15, 60, 80, 0.08)",
            "marginBottom": "25px",
        },
    )

def section_title(text, subtitle=None):

    children = [
        html.H2(
            text,
            style={
                "margin": "0 0 4px 0",
                "fontSize": "20px",
                "color": "#0D1C42",
                "paddingLeft": "12px",
            },
        )
    ]
    if subtitle:
        children.append(
            html.P(subtitle, style={"fontSize": "12.5px", "color": "#6b7590", "margin": "6px 0 14px 17px"})
        )
    else:
        children.append(html.Div(style={"marginBottom": "10px"}))

    return html.Div(children)

# 14c. KOMPONEN TAMPILAN "INFORMASI ANALISIS"
INFO_TEXT = "#33415c"
INFO_MUTED = "#6b7590"

def _id_num(value, digits=2):
    """Format angka desimal dengan koma (gaya penulisan Indonesia)."""
    return f"{value:.{digits}f}".replace(".", ",")

def cite(*nums):
    """Penanda sitasi [n] yang menaut ke daftar referensi di bagian bawah."""
    parts = []
    for i, n in enumerate(nums):
        if i:
            parts.append(", ")
        parts.append(
            html.A(
                str(n), href=f"#ref-{n}",
                style={"color": COLOR_ACCENT, "textDecoration": "none", "fontWeight": "700"},
            )
        )
    return html.Sup(["[", *parts, "]"], style={"fontSize": "11px", "marginLeft": "2px"})

# [SITASI]
def radar_cite(*nums):
    parts = []
    for i, n in enumerate(nums):
        if i:
            parts.append(", ")
        parts.append(
            html.A(
                str(n), href=f"#rref-{n}",
                style={"color": COLOR_ACCENT, "textDecoration": "none", "fontWeight": "700"},
            )
        )
    return html.Sup(["[", *parts, "]"], style={"fontSize": "11px", "marginLeft": "2px"})

def ext_link(text, url):
    return html.A(
        text, href=url, target="_blank", rel="noopener noreferrer",
        style={"color": COLOR_ACCENT, "fontWeight": "600", "wordBreak": "break-word"},
    )

def code_tag(text):
    return html.Code(
        text,
        style={
            "backgroundColor": "#eef1f8", "padding": "1px 6px", "borderRadius": "5px",
            "fontSize": "12.5px", "color": "#0D1C42",
        },
    )

def info_heading(title):
    return html.H3(
        title,
        style={
            "margin": "30px 0 14px 0", "paddingBottom": "8px", "fontSize": "16px",
            "color": "#0D1C42", "borderBottom": "1px solid #e3e7f1",
        },
    )

def info_chip(text, bg="#eef1f8", color="#0D1C42", border="#d6dcec"):
    return html.Span(
        text,
        style={
            "display": "inline-block", "backgroundColor": bg, "color": color,
            "border": f"1px solid {border}", "fontSize": "12.5px", "fontWeight": "600",
            "padding": "5px 12px", "borderRadius": "999px", "margin": "0 6px 8px 0",
        },
    )

def info_para(children, **extra_style):
    style = {"fontSize": "14px", "lineHeight": "1.7", "color": INFO_TEXT, "margin": "0 0 12px 0"}
    style.update(extra_style)
    return html.P(children, style=style)

def info_kv(rows):
    """Daftar 'label - isi' bergaya tabel ringan di dalam kartu."""
    items = []
    for label, value in rows:
        items.append(
            html.Div(
                [
                    html.Div(
                        label,
                        style={
                            "fontSize": "11.5px", "fontWeight": "700", "color": INFO_MUTED,
                            "textTransform": "uppercase", "letterSpacing": "0.4px",
                            "marginBottom": "3px",
                        },
                    ),
                    html.Div(value, style={"fontSize": "13.5px", "color": "#33415c", "lineHeight": "1.6"}),
                ],
                style={"padding": "10px 0", "borderTop": "1px solid #edf1f3"},
            )
        )
    return html.Div(items, style={"marginTop": "14px"})

def info_card(children, accent=COLOR_ACCENT):
    return html.Div(
        children,
        style={
            "backgroundColor": "white", "padding": "20px 22px", "borderRadius": "14px",
            "border": "1px solid #e3e7f1", "borderTop": f"4px solid {accent}",
            "boxShadow": "0 2px 10px rgba(15, 60, 80, 0.06)",
        },
    )

def info_callout(title, children, tone="info"):
    palette = {
        "info": ("#eef1f8", COLOR_ACCENT),
        "warn": ("#fff8e6", "#d68910"),
        "alert": ("#fdf1f0", "#c0392b"),
    }
    background, accent = palette[tone]
    return html.Div(
        [
            html.Div(
                title,
                style={"fontWeight": "700", "fontSize": "14px", "color": accent, "marginBottom": "6px"},
            ),
            html.Div(children, style={"fontSize": "13.5px", "lineHeight": "1.7", "color": INFO_TEXT}),
        ],
        style={
            "backgroundColor": background, "borderLeft": f"4px solid {accent}",
            "borderRadius": "10px", "padding": "14px 18px",
        },
    )

def model_card(label, color, title, subtitle, description, rows):
    return info_card(
        [
            html.Div(
                label,
                style={"fontSize": "11px", "fontWeight": "700", "letterSpacing": "1px", "color": color},
            ),
            html.H4(title, style={"margin": "6px 0 2px 0", "fontSize": "20px", "color": "#0D1C42"}),
            html.Div(subtitle, style={"fontSize": "12.5px", "color": INFO_MUTED, "marginBottom": "12px"}),
            info_para(description, margin="0"),
            info_kv(rows),
        ],
        accent=color,
    )

def step_card(number, title, text):
    return html.Div(
        [
            html.Div(
                str(number),
                style={
                    "width": "28px", "height": "28px", "borderRadius": "50%",
                    "backgroundColor": "#eef1f8", "color": COLOR_ACCENT_DARK, "fontWeight": "700",
                    "display": "flex", "alignItems": "center", "justifyContent": "center",
                    "marginBottom": "8px", "fontSize": "13px",
                },
            ),
            html.Div(title, style={"fontWeight": "700", "fontSize": "13.5px", "color": "#0D1C42", "marginBottom": "4px"}),
            html.Div(text, style={"fontSize": "12.5px", "lineHeight": "1.6", "color": "#5b6b73"}),
        ],
        style={
            "backgroundColor": "#f7f8fd", "border": "1px solid #e3e7f1", "borderRadius": "12px",
            "padding": "14px 16px",
        },
    )

def ref_item(number, children, id_prefix="ref"):
    # [SITASI] id_prefix memungkinkan daftar rujukan menu Validasi 2026 memakai id "rref-n"
    return html.Div(
        [
            html.Div(
                f"[{number}]",
                style={
                    "flex": "0 0 auto", "backgroundColor": COLOR_ACCENT_DARK, "color": "white",
                    "fontWeight": "700", "fontSize": "12px", "padding": "3px 9px",
                    "borderRadius": "6px", "height": "fit-content", "marginTop": "2px",
                },
            ),
            html.Div(children, style={"fontSize": "13.3px", "lineHeight": "1.7", "color": INFO_TEXT}),
        ],
        id=f"{id_prefix}-{number}",
        style={"display": "flex", "gap": "12px", "padding": "12px 0", "borderTop": "1px solid #edf1f3"},
    )

def build_info_analisis_section():
    """Bagian 'Informasi Analisis' (ditampilkan langsung di tab sendiri)."""

    # data dinamis dari file koordinat
    n_stasiun = len(valid_stations)
    stasiun_urut = sorted(valid_stations, key=lambda nama: valid_stations[nama][0])
    lon_semua = [lon for lon, _ in valid_stations.values()]
    lat_semua = [lat for _, lat in valid_stations.values()]
    lon_min, lon_max = min(lon_semua), max(lon_semua)
    lat_min, lat_max = abs(max(lat_semua)), abs(min(lat_semua))

    # 1. PASANG SURUT & AREA KAJIAN
    kartu_pasut = info_card(
        [
            html.H4("Apa itu pasang surut?", style={"margin": "0 0 10px 0", "fontSize": "17px", "color": "#0D1C42"}),
            info_para(
                "Pasang surut (pasut) adalah naik-turunnya permukaan laut secara berkala, terutama "
                "akibat gaya tarik gravitasi Bulan dan Matahari pada Bumi yang berputar. Titik "
                "tertinggi dalam satu siklus disebut pasang (high tide), dan titik terendahnya "
                "disebut surut (low tide)."
            ),
            info_para(
                [
                    "Karena bersifat astronomis dan sangat teratur, pasut dapat dihitung jauh hari "
                    "sebelumnya. Pasut diuraikan menjadi konstituen harmonik (misalnya M2, S2, K1, "
                    "dan O1) yang masing-masing punya amplitudo dan fase. Model pasut global "
                    "menyimpan konstanta harmonik itu, lalu perangkat lunak pyTMD",
                    cite(2),
                    " menjumlahkannya menjadi deret waktu elevasi muka laut.",
                ],
                margin="0",
            ),
        ],
    )

    kartu_area = info_card(
        [
            html.H4("Area kajian", style={"margin": "0 0 10px 0", "fontSize": "17px", "color": "#0D1C42"}),
            info_para(
                f"Kajian mencakup {n_stasiun} titik stasiun di pesisir selatan Daerah Istimewa "
                "Yogyakarta yang menghadap Samudra Hindia, membentang dari Kulon Progo di barat "
                f"hingga Gunungkidul di timur (sekitar {_id_num(lon_min)}°-{_id_num(lon_max)}° BT "
                f"dan {_id_num(lat_min)}°-{_id_num(lat_max)}° LS)."
            ),
            html.Div([info_chip(nama) for nama in stasiun_urut], style={"marginTop": "6px"}),
        ],
        accent="#117864",
    )

    # 2. MODEL PASUT
    kartu_got = model_card(
        "MODEL UTAMA", COLOR_MODEL_A, "GOT4.10", "Goddard Ocean Tide, NASA Goddard Space Flight Center (GSFC)",
        [
            "Model pasut laut global dari NASA GSFC yang diturunkan dari analisis harmonik data "
            "altimetri satelit, dibangun dari seri satelit Topex/Poseidon, Jason-1, dan Jason-2",
            cite(3, 5),
            ". Model ini dipakai sebagai sumber prediksi utama pada dashboard.",
        ],
        [
            ("Pengembang", ["Richard D. Ray, NASA GSFC", cite(3, 5)]),
            ("Basis data", ["Altimetri satelit Topex/Poseidon, Jason-1, dan Jason-2", cite(5)]),
            ("Resolusi spasial",
             ["±0,5° (seri GOT4). Cukup kasar untuk perairan dekat pantai, sehingga titik stasiun "
              "disesuaikan ke sel laut terdekat", cite(5)]),
            ("Sumber unduhan",
             ["Server NASA GSFC, diunduh otomatis lewat fungsi ", code_tag("fetch_gsfc_got()"),
              " milik pyTMD", cite(2)]),
        ],
    )

    kartu_eot = model_card(
        "MODEL PEMBANDING", COLOR_MODEL_B, "EOT20", "Empirical Ocean Tide model, DGFI-TUM (Jerman)",
        [
            "Model pasut global terbaru dalam seri model DGFI-TUM. EOT20 dibuat dengan analisis "
            "pasut residual data altimetri multi-misi periode 1992-2019 (11 misi satelit) dengan "
            "FES2014b sebagai model acuan",
            cite(1, 4),
            ". Model ini dipakai untuk validasi silang terhadap GOT4.10.",
        ],
        [
            ("Pengembang",
             ["M. Hart-Davis, G. Piccioni, D. Dettmering, C. Schwatke, M. Passaro, F. Seitz", cite(1)]),
            ("Cakupan dan resolusi",
             ["66°LS-66°LU (lintang lebih tinggi diisi FES2014b), grid 1/8° (0,125°)", cite(1)]),
            ("17 konstituen",
             [html.Div(
                 [info_chip(c, bg="#fdf3e4", color="#8a5a12", border="#f0d9b0")
                  for c in ["2N2", "J1", "K1", "K2", "M2", "M4", "MF", "MM", "N2",
                            "O1", "P1", "Q1", "S1", "S2", "SA", "SSA", "T2"]]
                 + [cite(1)],
                 style={"marginTop": "4px"},
             )]),
            ("Sumber unduhan",
             ["Repositori SEANOE (DOI 10.17882/79489), NetCDF, akses terbuka, lisensi CC BY 4.0. ", cite(1)]),
        ],
    )

    # 3. PERANGKAT LUNAK & ALUR
    kartu_pytmd = info_card(
        [
            html.H4("pyTMD: perangkat lunak prediksi", style={"margin": "0 0 10px 0", "fontSize": "17px", "color": "#0D1C42"}),
            info_para(
                [
                    "pyTMD adalah perangkat lunak prediksi pasut berbasis Python untuk memperkirakan "
                    "pasut laut, load tide, solid Earth tide, dan pole tide, berlisensi MIT",
                    cite(2),
                    ". Pada kajian ini, pyTMD membaca konstanta harmonik GOT4.10 dan EOT20 lalu "
                    "menghitung elevasi pasut per jam di setiap titik stasiun.",
                ],
                margin="0",
            ),
        ],
        accent="#5d6d7e",
    )

    langkah = [
        (1, "Muat model", "GOT4.10 diunduh otomatis lewat pyTMD, sedangkan EOT20 diunduh manual dari SEANOE."),
        (2, "Sesuaikan titik stasiun",
         "Titik yang tidak berada di sel laut model digeser ke sel laut terdekat (radius maksimum 0,05°)."),
        (3, "Prediksi per jam",
         f"Elevasi dihitung tiap 1 jam dalam UTC, per bulan, untuk tahun {YEAR_LABEL}."),
        (4, "Konversi dan statistik",
         "Waktu diubah ke WIB (UTC+7), dibagi per minggu kalender (Senin-Minggu), lalu dihitung nilai minimum, maksimum, dan rata-rata."),
        (5, "Validasi silang",
         "GOT4.10 dibandingkan dengan EOT20 pada waktu dan titik yang sama memakai RMSE, MAE, korelasi (r), dan Willmott's d."),
    ]

    # 4. CATATAN
    catatan_astronomis = info_callout(
        "Prediksi astronomis, bukan pengamatan",
        "Hasil pada dashboard adalah prediksi pasut astronomis dari model global. Pengaruh cuaca "
        "(angin dan tekanan udara), gelombang, dan kondisi lokal seperti muara atau teluk tidak "
        "ikut dihitung, sehingga tinggi muka air sebenarnya dapat berbeda dari prediksi.",
        tone="warn",
    )
    catatan_spasial = info_callout(
        "Catatan spasial",
        "Titik Baron, Gesing, Jungwok, dan Sadeng memiliki posisi koordinat yang relatif lebih jauh dari "
        "garis pantai dibandingkan beberapa titik lainnya. Oleh karena itu, ketiga titik tersebut "
        "perlu diperlakukan sebagai titik representasi perairan lepas pantai, bukan sebagai lokasi "
        "pengamatan pasang surut tepat di garis pantai. Pada proses pemodelan, koordinat dapat "
        "mengalami penyesuaian menuju grid laut terdekat GOT4.10 apabila koordinat awal tidak "
        "berada pada sel laut model. Hasil pada ketiga lokasi tersebut perlu diinterpretasikan "
        "sebagai representasi kondisi pasang surut pada area perairan sekitar titik, bukan sebagai "
        "tinggi muka air tepat di dermaga atau garis pantai.",
        tone="warn",
    )
    catatan_waktu = info_callout(
        "Zona waktu",
        "Waktu prediksi ditampilkan dalam Waktu Indonesia Barat (WIB), sedangkan waktu pada "
        "validasi silang memakai UTC. Interval prediksi 1 jam.",
        tone="info",
    )

    # 5. REFERENSI
    referensi_utama = [
        ref_item(
            1,
            [
                "Hart-Davis, M., Piccioni, G., Dettmering, D., Schwatke, C., Passaro, M., & Seitz, F. (2021). "
                "EOT20 - A global Empirical Ocean Tide model from multi-mission satellite altimetry [Data set]. "
                "SEANOE. ",
                ext_link("https://www.seanoe.org/data/00683/79489/", "https://www.seanoe.org/data/00683/79489/"),
            ],
        ),
        ref_item(
            2,
            [
                "GitHub - pyTMD/pyTMD: Python-based tidal prediction software. ",
                ext_link("https://github.com/pyTMD/pyTMD", "https://github.com/pyTMD/pyTMD"),
            ],
        ),
    ]
    referensi_pendukung = [
        ref_item(
            3,
            [
                "Ray, R. D. (2013). Precise comparisons of bottom-pressure and altimetric ocean tides. ",
                html.Em("Journal of Geophysical Research: Oceans, 118"),
                ", 4570-4584. ",
                ext_link("https://doi.org/10.1002/jgrc.20336", "https://doi.org/10.1002/jgrc.20336"),
            ],
        ),
        ref_item(
            4,
            [
                "Hart-Davis, M. G., Piccioni, G., Dettmering, D., Schwatke, C., Passaro, M., & Seitz, F. (2021). "
                "EOT20: a global ocean tide model from multi-mission satellite altimetry. ",
                html.Em("Earth System Science Data, 13"),
                "(8), 3869-3884. ",
                ext_link("https://doi.org/10.5194/essd-13-3869-2021", "https://doi.org/10.5194/essd-13-3869-2021"),
            ],
        ),
        ref_item(
            5,
            [
                "Ray, R. D. (2025). ",
                html.Em("Documentation for Goddard Ocean Tide Solution GOT5: Global Tides from Multimission "
                        "Satellite Altimetry"),
                " (NASA TM-20250002085). NASA Goddard Space Flight Center. ",
                ext_link(
                    "https://ntrs.nasa.gov/api/citations/20250002085/downloads/GOT5-TechMemo.pdf",
                    "https://ntrs.nasa.gov/api/citations/20250002085/downloads/GOT5-TechMemo.pdf",
                ),
            ],
        ),
    ]

    # 6. ANALISIS HARMONIK RADAR (t_tide)
    par_r, _ = radar_ambil_parameter()
    snr_min = par_r.get("SNR_MIN", "-")
    cf_radar = lambda *n: cite(*[x + 3 for x in n])

    kartu_ttide = info_card(
        [
            html.H4("t_tide: analisis harmonik data radar",
                    style={"margin": "0 0 10px 0", "fontSize": "17px", "color": "#0D1C42"}),
            info_para(
                ["t_tide adalah paket analisis harmonik pasang surut klasik yang menghitung amplitudo dan "
                 "fase tiap konstanta beserta perkiraan galatnya (selang kepercayaan)", cite(11),
                 ". Pada validasi 2026, deret muka air per jam dari sensor radar diurai dengan t_tide menjadi "
                 "konstanta harmonik (M2, S2, K1, O1, dan lainnya), lalu dibandingkan dengan konstanta "
                 "GOT4.10 dan EOT20 pada titik yang sama."],
                margin="0",
            ),
            info_kv([
                ("Masukan",
                 ["Rata-rata per jam dari data radar yang sudah melalui kontrol kualitas (nilai macet dan "
                  "lonjakan dibuang)", cf_radar(5)]),
                ("Konstanta yang dibandingkan",
                 [f"Hanya konstanta signifikan, yaitu dengan SNR > {snr_min}", cf_radar(4)]),
                ("Panjang data",
                 ["Disarankan minimal 15 hari dan idealnya sekitar 30 hari. Rekaman yang terlalu pendek "
                  "(5 jam atau 24 jam) menghasilkan konstanta yang tidak stabil", cf_radar(3, 4)]),
                ("Penilaian kesesuaian",
                 ["Selisih amplitudo, fase, dan vektor (RMSE) terhadap model. Kesesuaian amplitudo juga "
                  "dinilai dengan regresi linier berkemiringan mendekati 1", cf_radar(6, 7)]),
                ("Sumber hasil",
                 "Dibaca dari berkas keluaran t_tide (atau UTide bila dipilih pada pengolahan). Parameter "
                 f"lengkap tampil di menu Validasi {YEAR_VALIDASI_RADAR}."),
            ]),
        ],
        accent="#117864",
    )

    ref_radar_info = html.Details(
        [
            html.Summary(
                "Rujukan analisis harmonik radar (t_tide)",
                style={"cursor": "pointer", "fontWeight": "600", "color": COLOR_ACCENT_DARK,
                       "fontSize": "13px", "padding": "10px 0"},
            ),
            html.Div(
                [ref_item(i + 6, _rujukan_children(r)) for i, r in enumerate(RADAR_RUJUKAN[2:])]
                + [ref_item(11, [
                    "Pawlowicz, R., Beardsley, B., & Lentz, S. (2002). Classical tidal harmonic analysis "
                    "including error estimates in MATLAB using T_TIDE. ",
                    html.Em("Computers & Geosciences, 28"), "(8), 929-937. ",
                    _doi("10.1016/S0098-3004(02)00013-4"),
                ])]
            ),
            
        ],
        open=False, style={"marginTop": "4px"},
    )

    isi = html.Div(
        [
            # JUDUL UTAMA INFORMASI ANALISIS
            html.Div(
                [
                    html.Div(
                        "INFORMASI ANALISIS",
                        style={
                            "fontSize": "11px",
                            "fontWeight": "700",
                            "letterSpacing": "2px",
                            "color": COLOR_ACCENT,
                            "marginBottom": "6px",
                        },
                    ),
                    html.H2(
                        "Pasang Surut dan Area Kajian",
                        style={
                            "margin": "0",
                            "fontSize": "27px",
                            "fontWeight": "700",
                            "color": "#0D1C42",
                        },
                    ),
                    html.P(
                        "Informasi mengenai konsep pasang surut dan area kajian "
                        "yang digunakan dalam analisis.",
                        style={
                            "margin": "8px 0 20px 0",
                            "fontSize": "14px",
                            "lineHeight": "1.6",
                            "color": "#6b7590",
                        },
                    ),
                ],
                style={
                    "padding": "6px 0 4px 0",
                    "marginBottom": "8px",
                },
            ),

            # KARTU PASANG SURUT & AREA KAJIAN
            html.Div(
                [kartu_pasut, kartu_area],
                className="info-grid",
            ),

            info_heading("Model Pasang Surut yang Digunakan"),
            html.Div([kartu_got, kartu_eot], className="info-grid"),

            info_heading("Perangkat Lunak dan Alur Pengolahan"),
            kartu_pytmd,
            html.Div(
                [step_card(n, t, x) for n, t, x in langkah],
                className="info-grid-3",
                style={"marginTop": "14px"},
            ),

            info_heading("Analisis Harmonik Data Radar (t_tide)"),
            kartu_ttide,

            info_heading("Cara Membaca Hasil"),
            html.Div(
                [
                    info_callout("Acuan nol (MSL) dan kondisi pasang surut",
                                 [html.P(KETERANGAN_MSL, style={"margin": "0 0 8px 0"}),
                                  html.P(KETERANGAN_PASANG_SURUT, style={"margin": "0"})]),
                    info_callout("Minggu dan validasi",
                                 [html.P("Minggu dihitung berdasarkan kalender riil (Senin s.d. Minggu) dan dipotong "
                                         "pada batas awal dan akhir bulan.", style={"margin": "0 0 8px 0"}),
                                  html.P(KETERANGAN_VALIDASI, style={"margin": "0"})]),
                ],
                style={"display": "flex", "flexDirection": "column", "gap": "12px"},
            ),

            info_heading("Catatan dan Keterbatasan"),
            html.Div(
                [catatan_astronomis, catatan_spasial, catatan_waktu],
                style={"display": "flex", "flexDirection": "column", "gap": "12px"},
            ),

            info_heading("Referensi"),
            html.Div(referensi_utama),
            html.Details(
                [
                    html.Summary(
                        "Rujukan pendukung (rincian model GOT4.10 dan EOT20)",
                        style={"cursor": "pointer", "fontWeight": "600", "color": COLOR_ACCENT_DARK,
                               "fontSize": "13px", "padding": "10px 0"},
                    ),
                    html.Div(referensi_pendukung),
                ],
                open=True,
                style={"marginTop": "4px"},
            ),
            ref_radar_info,

            html.P(
                f"Prediksi ini dilakukan oleh {INSTANSI_NAMA}, {INSTANSI_HOMEBASE}.",
                style={"fontStyle": "italic", "color": "#6b7590", "fontSize": "13px",
                       "marginTop": "22px", "paddingTop": "14px", "borderTop": "1px solid #edf1f3"},
            ),
        ],
        style={"paddingTop": "6px"},
    )

    return section_container([isi])

# 14d. TAB: PANDUAN PEMANFAATAN (palet navy seragam + aksen oranye)
from datetime import date as _date

PG_BLUE = UI_BLUE_SOFT
PG_NAVY = UI_NAVY
PG_NAVY2 = UI_NAVY_MID
PG_ORANGE = "#F68048"
PG_TEXT = UI_TEXT
PG_MUTED = UI_MUTED
PG_LINE = UI_LINE
PG_GRID = "#e8ebf4"
PG_HIGH = "#3f7d5a"
PG_LOW = "#a8453a"
PG_MSL = "#4a5578"

# GAMBAR PANDUAN
PANDUAN_IMG_EXT = (".jpg", ".jpeg", ".png", ".webp")

def find_panduan_image(name):
    for ext in PANDUAN_IMG_EXT:
        for candidate in (name + ext, name + ext.upper()):
            p = PANDUAN_IMG_DIR / candidate
            if p.exists():
                return p
    return None

def _svg_data_uri(svg):
    return "data:image/svg+xml;utf8," + quote(svg)

def _scene_svg(kind):
    cfg = {
        "hero":      dict(t="#22396F", b="#F9C9A8", sea1="#16295f", sea2="#0D1C42", sun="#FBD6B8", sx=560, sy=210, sr=52),
        "nelayan":   dict(t="#2E4A8A", b="#F6A57A", sea1="#22396F", sea2="#0D1C42", sun="#FDE3CC", sx=590, sy=200, sr=46),
        "pemancing": dict(t="#6f86bd", b="#dfe6fb", sea1="#2E4A8A", sea2="#22396F", sun="#fff1e6", sx=610, sy=170, sr=40),
        "wisata":    dict(t="#93a5d3", b="#fde6d2", sea1="#3b5aa3", sea2="#2E4A8A", sun="#fff3e6", sx=170, sy=150, sr=44),
        "pengelola": dict(t="#5a6fa8", b="#dfe4f7", sea1="#22396F", sea2="#0D1C42", sun="#fbe3d0", sx=640, sy=190, sr=38),
    }[kind]

    waves = (
        '<g fill="none" stroke="#ffffff" stroke-opacity="0.22" stroke-width="2">'
        '<path d="M0 285 Q50 275 100 285 T200 285 T300 285 T400 285 T500 285 T600 285 T700 285 T800 285"/>'
        '<path d="M0 318 Q60 306 120 318 T240 318 T360 318 T480 318 T600 318 T720 318 T840 318"/>'
        '<path d="M0 352 Q70 338 140 352 T280 352 T420 352 T560 352 T700 352 T840 352"/>'
        '</g>'
    )

    extra = ""
    if kind == "hero":
        extra = (
            '<path d="M0 420 L0 215 L70 190 L130 220 L200 250 L260 420 Z" fill="#0d1a4a"/>'
            '<path d="M800 420 L800 235 L730 215 L670 245 L610 290 L580 420 Z" fill="#14246b"/>'
            '<path d="M0 420 L0 380 Q200 360 400 385 T800 375 L800 420 Z" fill="#080f33" opacity="0.55"/>'
        )
    elif kind == "nelayan":
        extra = (
            '<path d="M230 262 L470 262 L436 300 L266 300 Z" fill="#0d1a4a"/>'
            '<rect x="346" y="150" width="4" height="114" fill="#0d1a4a"/>'
            '<path d="M352 158 L352 252 L420 252 Z" fill="#ecdfc6"/>'
            '<path d="M346 150 L346 160 L322 155 Z" fill="#F68048"/>'
            '<path d="M200 318 Q330 306 470 318" stroke="#ffffff" stroke-opacity="0.18" stroke-width="3" fill="none"/>'
        )
    elif kind == "pemancing":
        extra = (
            '<path d="M0 420 L0 245 L80 228 L150 258 L225 300 L300 420 Z" fill="#2a3156"/>'
            '<path d="M0 420 L0 320 L120 310 L200 340 L250 420 Z" fill="#1f2544"/>'
            '<circle cx="118" cy="190" r="9" fill="#0d1a4a"/>'
            '<path d="M118 200 L118 238 M118 210 L138 222 M118 238 L108 262 M118 238 L130 262" stroke="#0d1a4a" stroke-width="5" stroke-linecap="round" fill="none"/>'
            '<path d="M134 214 L352 108" stroke="#0d1a4a" stroke-width="2.5" fill="none"/>'
            '<path d="M352 108 L352 296" stroke="#ffffff" stroke-opacity="0.7" stroke-width="1" fill="none"/>'
            '<circle cx="352" cy="296" r="4" fill="#F68048"/>'
        )
    elif kind == "wisata":
        extra = (
            '<path d="M0 420 L0 338 Q200 316 420 336 T800 322 L800 420 Z" fill="#e6d3a8"/>'
            '<path d="M0 420 L0 372 Q240 352 480 374 T800 362 L800 420 Z" fill="#d9c391"/>'
            '<path d="M0 338 Q200 316 420 336 T800 322" stroke="#ffffff" stroke-opacity="0.65" stroke-width="3" fill="none"/>'
            '<path d="M520 300 Q580 238 660 300 Z" fill="#b5503f"/>'
            '<path d="M560 300 Q590 252 620 300 Z" fill="#f2e6cf"/>'
            '<path d="M590 262 L590 372" stroke="#6b5a45" stroke-width="4"/>'
            '<ellipse cx="520" cy="384" rx="70" ry="9" fill="#bda87a" opacity="0.5"/>'
        )
    elif kind == "pengelola":
        extra = (
            '<path d="M0 420 L0 352 Q200 332 420 354 T800 342 L800 420 Z" fill="#d8c9a3"/>'
            '<path d="M470 352 L490 200 M550 352 L530 200" stroke="#16204f" stroke-width="6" fill="none"/>'
            '<path d="M480 300 L540 300 M484 262 L536 262" stroke="#16204f" stroke-width="3"/>'
            '<rect x="466" y="160" width="88" height="44" fill="#16204f"/>'
            '<rect x="476" y="170" width="68" height="20" fill="#c9d6dc" opacity="0.85"/>'
            '<path d="M458 160 L510 128 L562 160 Z" fill="#a8453a"/>'
            '<path d="M510 128 L510 98" stroke="#16204f" stroke-width="3"/>'
            '<path d="M510 98 L540 108 L510 118 Z" fill="#F68048"/>'
            '<circle cx="300" cy="340" r="24" fill="none" stroke="#f4f0e6" stroke-width="10"/>'
            '<path d="M300 316 A24 24 0 0 1 324 340 M300 364 A24 24 0 0 1 276 340" stroke="#a8453a" stroke-width="10" fill="none"/>'
        )

    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 420" preserveAspectRatio="xMidYMid slice">'
        f'<defs><linearGradient id="sk" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{cfg["t"]}"/>'
        f'<stop offset="1" stop-color="{cfg["b"]}"/></linearGradient></defs>'
        '<rect width="800" height="420" fill="url(#sk)"/>'
        f'<circle cx="{cfg["sx"]}" cy="{cfg["sy"]}" r="{cfg["sr"]}" fill="{cfg["sun"]}" opacity="0.92"/>'
        f'<rect y="250" width="800" height="170" fill="{cfg["sea1"]}"/>'
        f'<rect y="310" width="800" height="110" fill="{cfg["sea2"]}"/>'
        + waves + extra +
        '</svg>'
    )
    return svg

def panduan_image_url(name):
    p = find_panduan_image(name)
    if p is not None:
        return f"/assets/panduan/{p.name}"
    return _svg_data_uri(_scene_svg(name))


# CSS tambahan
PANDUAN_CSS = """
            /* --- Tab Panduan Pemanfaatan --- */
            .pg-hero {
                position: relative; overflow: hidden; border-radius: 18px; padding: 34px 38px;
                color: #ffffff; margin: 25px 0 25px 0;
                background: linear-gradient(135deg, #010736 0%, #0D1C42 55%, #22396F 100%);
                box-shadow: 0 8px 24px rgba(13, 28, 66, 0.28);
            }
            .pg-hero::before, .pg-hero::after {
                content: ""; position: absolute; border-radius: 50%; background: rgba(255,255,255,0.07);
            }
            .pg-hero::before { width: 320px; height: 320px; right: -80px; top: -140px; }
            .pg-hero::after  { width: 220px; height: 220px; right: 140px; bottom: -150px; }
            .pg-hero-eyebrow { font-size: 11.5px; font-weight: 700; letter-spacing: 2px; opacity: 0.8; }
            .pg-hero h2 { margin: 8px 0 10px 0; font-size: 27px; font-weight: 700; line-height: 1.3; max-width: 760px; }
            .pg-hero p  { margin: 0 0 18px 0; font-size: 14.5px; line-height: 1.7; max-width: 720px; opacity: 0.93; }
            .pg-hero-chip {
                display: inline-block; margin: 0 8px 8px 0; padding: 6px 14px; border-radius: 999px;
                font-size: 12.5px; font-weight: 600; background: rgba(255,255,255,0.16);
                border: 1px solid rgba(255,255,255,0.28);
            }
            .pg-grid-4 { display: grid; gap: 18px; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); }
            .pg-grid-steps { display: grid; gap: 12px; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); }
            .pg-user-card {
                background: #ffffff; border: 1px solid #e3e7f1; border-radius: 16px; padding: 22px 22px 20px 22px;
                box-shadow: 0 2px 10px rgba(13, 28, 66, 0.06); overflow: hidden;
                transition: transform 0.18s ease, box-shadow 0.18s ease;
            }
            .pg-user-card:hover { transform: translateY(-4px); box-shadow: 0 12px 26px rgba(46, 74, 138, 0.16); }
            .pg-card-img {
                height: 150px; margin: -22px -22px 16px -22px; background-size: cover; background-position: center;
            }
            .pg-user-card h4 { margin: 0 0 2px 0; font-size: 18px; color: #0D1C42; }
            .pg-tagline { font-size: 12.5px; color: #6b7590; margin-bottom: 12px; }
            .pg-user-card ul { margin: 0 0 14px 0; padding-left: 18px; }
            .pg-user-card li { font-size: 13.3px; line-height: 1.65; color: #33415c; margin-bottom: 6px; }
            .pg-caution {
                font-size: 12.5px; line-height: 1.6; color: #7a3a14; background: #fff4ec;
                border-left: 3px solid #F68048; border-radius: 8px; padding: 9px 12px;
            }
            .pg-table { width: 100%; border-collapse: separate; border-spacing: 0; font-size: 13.3px; }
            .pg-table th {
                text-align: left; background: #0D1C42; color: #ffffff; padding: 12px 14px; font-weight: 600;
            }
            .pg-table th:first-child { border-top-left-radius: 10px; }
            .pg-table th:last-child { border-top-right-radius: 10px; }
            .pg-table td { padding: 12px 14px; border-bottom: 1px solid #e8ebf4; color: #33415c; vertical-align: top; line-height: 1.6; }
            .pg-table tr:nth-child(even) td { background: #f7f8fd; }
            .pg-table td:first-child { font-weight: 600; color: #0D1C42; white-space: nowrap; }
            .pg-check { list-style: none; margin: 0; padding: 0; }
            .pg-check li {
                display: flex; gap: 14px; align-items: flex-start; padding: 12px 4px;
                border-top: 1px solid #e8ebf4; font-size: 13.7px; line-height: 1.65; color: #33415c;
            }
            .pg-check li:first-child { border-top: none; }
            .pg-check-num {
                flex: 0 0 28px; height: 28px; border-radius: 50%; background: #eef1f8; color: #0D1C42;
                font-weight: 700; font-size: 13px; display: flex; align-items: center; justify-content: center;
            }
            .pg-event {
                display: flex; align-items: center; gap: 14px; padding: 12px 16px; border-radius: 12px;
                background: #ffffff; border: 1px solid #e3e7f1; margin-bottom: 10px;
                box-shadow: 0 1px 6px rgba(13, 28, 66, 0.05);
            }
            .pg-event-icon {
                width: 36px; height: 36px; border-radius: 10px; display: flex; align-items: center;
                justify-content: center; font-weight: 700; font-size: 15px; flex: 0 0 36px;
            }
            .pg-event-time { font-size: 18px; font-weight: 700; color: #0D1C42; min-width: 110px; }
            .pg-event-type { font-size: 13px; font-weight: 600; flex: 1; }
            .pg-event-height { font-size: 13.5px; color: #5a6384; font-weight: 600; }
"""
app.index_string = app.index_string.replace("</style>", PANDUAN_CSS + "\n        </style>", 1)

SITASI_JS = """
<script>
document.addEventListener('click', function(e){
  var a = e.target.closest ? e.target.closest('a[href^="#ref-"], a[href^="#rref-"]') : null;
  if(!a) return;
  var t = document.getElementById(a.getAttribute('href').slice(1));
  if(!t) return;
  e.preventDefault();
  var d = t.closest('details');
  while(d){ d.open = true; d = d.parentElement ? d.parentElement.closest('details') : null; }
  setTimeout(function(){ t.scrollIntoView({behavior:'smooth', block:'center'}); }, 60);
});
</script>
"""
app.index_string = app.index_string.replace("</body>", SITASI_JS + "</body>", 1)


# Fungsi bantu: deteksi puncak pasang & lembah surut dari data per jam
def detect_tide_extrema(times, heights):
    """Cari puncak (pasang) dan lembah (surut) dari deret per jam.

    Waktu & tinggi diperhalus dengan interpolasi parabola 3 titik, sehingga
    estimasi waktu tidak terkunci pada jam bulat.
    Mengembalikan list dict: {jenis, waktu, tinggi}.
    """
    events = []
    y = np.asarray(heights, dtype=float)
    for i in range(1, len(y) - 1):
        y0, y1, y2 = y[i - 1], y[i], y[i + 1]
        is_high = (y1 > y0) and (y1 >= y2)
        is_low = (y1 < y0) and (y1 <= y2)
        if not (is_high or is_low):
            continue
        denom = y0 - 2 * y1 + y2
        offset = 0.0 if denom == 0 else 0.5 * (y0 - y2) / denom
        offset = float(np.clip(offset, -1.0, 1.0))
        peak_value = y1 - 0.25 * (y0 - y2) * offset
        events.append({
            "jenis": "Pasang" if is_high else "Surut",
            "waktu": times.iloc[i] + pd.Timedelta(minutes=offset * 60),
            "tinggi": float(peak_value),
        })
    return events


# Komponen tampilan khusus tab Panduan
def pg_section_container(children):
    return html.Div(
        children,
        style={
            "backgroundColor": "white", "padding": "24px", "borderRadius": "16px",
            "boxShadow": "0 4px 16px rgba(13, 28, 66, 0.08)", "marginBottom": "25px",
        },
    )


def pg_section_title(text, subtitle=None):
    children = [
        html.H2(
            text,
            style={"margin": "0 0 4px 0", "fontSize": "20px", "color": PG_NAVY, "paddingLeft": "12px"},
        )
    ]
    if subtitle:
        children.append(
            html.P(subtitle, style={"fontSize": "12.5px", "color": PG_MUTED, "margin": "6px 0 14px 17px"})
        )
    else:
        children.append(html.Div(style={"marginBottom": "10px"}))
    return html.Div(children)


def pg_heading(title):
    return html.H3(
        title,
        style={
            "margin": "30px 0 14px 0", "paddingBottom": "8px", "fontSize": "16px",
            "color": PG_NAVY, "borderBottom": f"1px solid {PG_LINE}",
        },
    )


def pg_step_card(number, title, text):
    return html.Div(
        [
            html.Div(
                str(number),
                style={
                    "width": "28px", "height": "28px", "borderRadius": "50%",
                    "backgroundColor": UI_TINT, "color": PG_NAVY, "fontWeight": "700",
                    "display": "flex", "alignItems": "center", "justifyContent": "center",
                    "marginBottom": "8px", "fontSize": "13px",
                },
            ),
            html.Div(title, style={"fontWeight": "700", "fontSize": "13.5px", "color": PG_NAVY, "marginBottom": "4px"}),
            html.Div(text, style={"fontSize": "12.5px", "lineHeight": "1.6", "color": "#5a6384"}),
        ],
        style={
            "backgroundColor": "#f7f8fd", "border": f"1px solid {PG_LINE}", "borderRadius": "12px",
            "padding": "14px 16px",
        },
    )


def pg_callout(title, children, tone="info"):
    palette = {
        "info": ("#eef1f8", PG_BLUE),
        "warn": ("#fff4ec", "#c4561a"),
        "alert": ("#fdf1f0", "#c0392b"),
    }
    background, accent = palette[tone]
    return html.Div(
        [
            html.Div(
                title,
                style={"fontWeight": "700", "fontSize": "14px", "color": accent, "marginBottom": "6px"},
            ),
            html.Div(children, style={"fontSize": "13.5px", "lineHeight": "1.7", "color": PG_TEXT}),
        ],
        style={
            "backgroundColor": background, "borderLeft": f"4px solid {accent}",
            "borderRadius": "10px", "padding": "14px 18px",
        },
    )


def pg_info_card(message):
    return html.Div(
        message,
        style={
            "backgroundColor": "#f7f8fd", "border": f"1px dashed {PG_BLUE}", "borderRadius": "12px",
            "padding": "18px 20px", "color": PG_TEXT, "fontSize": "14px", "width": "100%",
        },
    )


def pg_stat_card(title, value, unit="", accent=PG_BLUE):
    return html.Div(
        [
            html.Div(
                title,
                style={
                    "fontSize": "13px", "fontWeight": "600", "color": "#5a6384", "marginBottom": "8px",
                    "textTransform": "uppercase", "letterSpacing": "0.4px",
                },
            ),
            html.Div(f"{value} {unit}", style={"fontSize": "26px", "fontWeight": "700", "color": PG_NAVY}),
        ],
        className="stat-card",
        style={
            "backgroundColor": "white", "padding": "18px 20px", "borderRadius": "14px",
            "borderLeft": f"4px solid {accent}", "boxShadow": "0 2px 10px rgba(13, 28, 66, 0.08)",
            "textAlign": "left", "flex": "1", "minWidth": "170px",
        },
    )


def pg_user_card(image_name, title, tagline, points, caution):
    return html.Div(
        [
            html.Div(
                className="pg-card-img",
                style={"backgroundImage": f"url('{panduan_image_url(image_name)}')"},
            ),
            html.H4(title),
            html.Div(tagline, className="pg-tagline"),
            html.Ul([html.Li(p) for p in points]),
            html.Div([html.B("Perhatikan: "), caution], className="pg-caution"),
        ],
        className="pg-user-card",
    )


def pg_check_item(number, text):
    return html.Li([html.Div(str(number), className="pg-check-num"), html.Div(text)])


def pg_table(header, rows):
    return html.Div(
        html.Table(
            [
                html.Thead(html.Tr([html.Th(h) for h in header])),
                html.Tbody([html.Tr([html.Td(c) for c in row]) for row in rows]),
            ],
            className="pg-table",
        ),
        style={"overflowX": "auto", "border": f"1px solid {PG_LINE}", "borderRadius": "10px"},
    )


def build_panduan_section():
    # HERO
    hero = html.Div(
        [
            html.Div("PANDUAN PEMANFAATAN", className="pg-hero-eyebrow"),
            html.H2("Memanfaatkan Prediksi Pasang Surut untuk Aktivitas di Pesisir Selatan DIY"),
            html.P(
                "Prediksi pasang surut membantu menentukan waktu yang tepat untuk berangkat, "
                "kembali, dan beraktivitas di pantai. Halaman ini membantu memahami cara membaca "
                "grafik dashboard untuk nelayan, pemancing, wisatawan, dan pengelola kawasan pantai."
            ),
            html.Div(
                [
                    html.Span("Nelayan", className="pg-hero-chip"),
                    html.Span("Pemancing", className="pg-hero-chip"),
                    html.Span("Wisata Pantai", className="pg-hero-chip"),
                    html.Span("Pengelola & Petugas", className="pg-hero-chip"),
                ]
            ),
        ],
        className="pg-hero",
    )

    # PERINGATAN UTAMA
    peringatan = pg_callout(
        "Pasang surut bukan satu-satunya penentu keselamatan",
        [
            html.P(
                "Dashboard hanya memuat prediksi pasang surut astronomis. Tinggi gelombang, angin, "
                "cuaca, dan arus balik (rip current) tidak termasuk di dalamnya. Pantai selatan "
                "menghadap Samudra Hindia dengan gelombang yang dapat membesar sewaktu-waktu, "
                "sehingga kondisi laut bisa berbahaya meskipun jadwal pasang surut terlihat "
                "\"aman\".",
                style={"margin": "0 0 8px 0"},
            ),
            html.P(
                "Selalu cek prakiraan tinggi gelombang dan cuaca maritim dari BMKG pada hari "
                "yang sama, serta ikuti imbauan petugas di lokasi.",
                style={"margin": "0"},
            ),
        ],
        tone="alert",
    )

    # CARA MEMBACA
    langkah = [
        (1, "Pilih stasiun terdekat", "Gunakan titik yang paling dekat dengan lokasi kegiatan Anda."),
        (2, "Cari puncak dan lembah", "Puncak kurva adalah pasang tertinggi, lembah adalah surut terendah pada tiap siklus."),
        (3, "Catat jamnya", "Waktu pada dashboard sudah dalam WIB, jadi bisa langsung dipakai."),
        (4, "Lihat selisihnya", "Selisih pasang dan surut yang besar berarti muka air berubah lebih cepat."),
    ]

    # KARTU PENGGUNA
    kartu = [
        pg_user_card(
            "nelayan", "Nelayan", "Merencanakan berangkat dan pulang",
            [
                "Gunakan jam puncak pasang dan lembah surut untuk menentukan waktu keluar dan "
                "masuk, terutama bila melewati muara, alur sempit, atau dermaga.",
                "Kedalaman alur dan sandar kapal berubah mengikuti tinggi muka air. Saat surut "
                "rendah, area dangkal bisa menyulitkan kapal berdraft dalam.",
                "Siapkan jam kembali yang longgar, tidak mepet dengan perubahan kondisi laut.",
            ],
            "keputusan melaut tetap bertumpu pada prakiraan gelombang dan angin BMKG, bukan pada "
            "jadwal pasang surut.",
        ),
        pg_user_card(
            "pemancing", "Pemancing", "Memilih waktu dan lokasi memancing",
            [
                "Banyak pemancing memilih waktu saat air sedang bergerak (peralihan antara pasang "
                "dan surut). Kebiasaan ini bervariasi antar lokasi dan jenis ikan, jadi anggap "
                "sebagai acuan, bukan kepastian.",
                "Memancing di karang atau batu: surut rendah membuka area lebih luas, tetapi saat "
                "air kembali naik jalur pulang bisa tertutup. Tentukan batas jam kembali sebelum "
                "air naik.",
                "Pantau terus gelombang yang datang, terutama saat berdiri di batu atau tebing.",
            ],
            "korban terseret gelombang sering terjadi pada pemancing di karang dan tebing. "
            "Gunakan pelampung dan jangan memancing sendirian saat gelombang tinggi.",
        ),
        pg_user_card(
            "wisata", "Wisata Pantai", "Berlibur dengan lebih aman",
            [
                "Saat surut, area pantai dan karang tampak lebih luas. Saat pasang, garis air maju "
                "dan area berpasir menyempit. Atur waktu bermain, foto, atau berjalan di tepi "
                "pantai sesuai kondisi ini.",
                "Hindari berjalan jauh ke area karang menjelang air naik karena jalur kembali bisa "
                "terputus.",
                "Untuk berenang, patuhi bendera dan zona yang ditetapkan petugas. Pasang surut "
                "tidak menggambarkan keberadaan arus balik.",
            ],
            "jangan masuk ke air bila ada larangan atau peringatan, walaupun air tampak tenang "
            "dari tepi.",
        ),
        pg_user_card(
            "pengelola", "Pengelola & Petugas", "Patroli, informasi, dan kesiapsiagaan",
            [
                "Susun jadwal patroli dan penempatan petugas dengan mempertimbangkan jam pasang "
                "tertinggi, saat muka air paling maju ke arah daratan.",
                "Gunakan grafik dan jadwal harian sebagai bahan informasi bagi pengunjung dan "
                "nelayan di papan pengumuman atau kanal komunikasi setempat.",
                "Manfaatkan untuk kegiatan pesisir lain seperti penataan sarana wisata, kerja "
                "bakti pantai, atau acara masyarakat.",
            ],
            "prediksi tidak memuat pengaruh cuaca ekstrem atau gelombang. Gabungkan dengan "
            "peringatan resmi BMKG.",
        ),
    ]

    # TABEL PERTIMBANGAN CEPAT
    tabel = pg_table(
        ["Kondisi", "Arti", "Dampak praktis"],
        [
            ["Mendekati puncak", "Pasang tertinggi pada siklus tersebut",
             "Garis air paling maju. Area berpasir atau karang yang rendah tertutup lebih luas."],
            ["Mendekati lembah", "Surut terendah pada siklus tersebut",
             "Karang dan dasar dangkal terbuka. Alur dan area sandar menjadi lebih dangkal."],
            ["Kurva naik atau turun curam", "Muka air berubah cepat",
             "Arus pasut umumnya lebih terasa. Perlu lebih waspada saat beraktivitas dekat air."],
            ["Kurva melandai di puncak atau lembah", "Perubahan muka air sesaat melambat",
             "Umumnya fase arus pasut lebih lemah, namun kondisi gelombang tetap perlu dipantau."],
            ["Selisih pasang-surut harian besar", "Rentang naik-turun lebih lebar",
             "Perubahan area terbuka dan tertutup lebih besar. Beri cadangan waktu lebih longgar."],
        ],
    )

    # CHECKLIST
    checklist = html.Ul(
        [
            pg_check_item(1, "Cek jadwal pasang surut stasiun terdekat untuk tanggal kegiatan (menu jadwal harian di atas)."),
            pg_check_item(2, "Cek prakiraan tinggi gelombang, angin, dan cuaca maritim dari BMKG pada hari yang sama."),
            pg_check_item(3, "Tentukan batas jam terakhir untuk kembali atau keluar dari area karang, beri cadangan waktu yang cukup."),
            pg_check_item(4, "Beritahu keluarga atau rekan tentang lokasi dan perkiraan jam kembali."),
            pg_check_item(5, "Gunakan pelampung dan perlengkapan keselamatan, lalu hentikan kegiatan bila kondisi laut berubah."),
        ],
        className="pg-check",
    )

    # JADWAL HARIAN INTERAKTIF
    if not tide_dashboard_df.empty:
        _t0 = tide_dashboard_df["datetime_wib"].min()
        _t1 = tide_dashboard_df["datetime_wib"].max()
        # hari pertama: bila data tidak mulai 00:00 WIB, mulai dari hari berikutnya
        tgl_min = (_t0.normalize() if _t0.hour == 0 else _t0.normalize() + pd.Timedelta(days=1)).date()
        # hari terakhir: bila data tidak berakhir 23:00 WIB, mundur satu hari
        tgl_max = (_t1.normalize() if _t1.hour == 23 else _t1.normalize() - pd.Timedelta(days=1)).date()
    else:
        tgl_min, tgl_max = _date(YEARS[0], 1, 1), _date(YEARS[-1], 12, 31)

    kontrol = html.Div(
        [
            html.Div(
                [
                    html.Label("Pilih Stasiun", style={"fontWeight": "600", "color": PG_TEXT}),
                    dcc.Dropdown(
                        id="pg-station",
                        options=[{"label": s, "value": s} for s in station_options],
                        value=station_options[0],
                        clearable=False,
                    ),
                ],
                style={"flex": "1"},
            ),
            html.Div(
                [
                    html.Label("Pilih Tanggal", style={"fontWeight": "600", "color": PG_TEXT, "display": "block"}),
                    dcc.DatePickerSingle(
                        id="pg-date",
                        min_date_allowed=tgl_min,
                        max_date_allowed=tgl_max,
                        initial_visible_month=tgl_min,
                        date=tgl_min,
                        display_format="DD/MM/YYYY",
                        style={"width": "100%"},
                    ),
                ],
                style={"flex": "0 0 220px"},
            ),
        ],
        style={
            "display": "flex", "gap": "20px", "alignItems": "flex-end", "backgroundColor": "#f7f8fd",
            "padding": "16px 18px", "borderRadius": "12px", "border": f"1px solid {PG_LINE}",
            "marginBottom": "18px",
        },
    )

    jadwal = pg_section_container([
        pg_section_title(
            "Jadwal Pasang dan Surut Harian",
            "Pilih stasiun dan tanggal untuk melihat jam perkiraan pasang tertinggi dan surut "
            "terendah pada hari tersebut (WIB).",
        ),
        kontrol,
        html.Div(id="pg-summary", style={"display": "flex", "gap": "18px", "flexWrap": "wrap", "marginBottom": "18px"}),
        dcc.Graph(id="pg-graph"),
        html.H3("Jam Pasang dan Surut", style={"fontSize": "16px", "color": PG_NAVY, "margin": "10px 0 12px 0"}),
        html.Div(id="pg-events"),
        html.P(
            "Jam dan tinggi puncak diestimasi dari data per jam dengan interpolasi, sehingga dapat "
            "bergeser beberapa menit hingga puluhan menit dari kondisi sebenarnya. Gunakan sebagai "
            "gambaran perencanaan.",
            style={"fontSize": "12.5px", "color": PG_MUTED, "fontStyle": "italic", "margin": "12px 0 0 0"},
        ),
    ])

    keterbatasan = pg_callout(
        "Keterbatasan data",
        [
            html.P(
                "Prediksi pasang surut menggunakan model global GOT4.10 yang memiliki resolusi spasial relatif kasar, "
                "terutama untuk wilayah dekat pantai. Titik Baron, Gesing, Jungwok, dan Sadeng merupakan titik "
                "representasi perairan sekitar, bukan lokasi di dermaga atau garis pantai.",
                style={"margin": "0 0 8px 0"},
            ),
            html.P(
                "Untuk kegiatan pelayaran atau aktivitas dengan risiko tinggi, gunakan prediksi ini sebagai referensi "
                "tambahan dan tetap mengacu pada tabel pasang surut resmi dari instansi berwenang serta informasi dan peringatan cuaca laut dari BMKG.",
                style={"margin": "0"},
            ),
        ],
        tone="warn",
    )

    return html.Div(
        [
            hero,
            peringatan,
            html.Div(
                [
                    pg_heading("Cara Membaca Grafik untuk Kegiatan Anda"),
                    html.Div([pg_step_card(n, t, x) for n, t, x in langkah], className="pg-grid-steps"),
                ],
                style={"marginTop": "6px"},
            ),
            pg_heading("Manfaat untuk Setiap Pengguna"),
            html.Div(kartu, className="pg-grid-4"),
            html.Div(style={"height": "26px"}),
            jadwal,
            pg_section_container([
                pg_section_title(
                    "Pertimbangan Cepat",
                    "Rangkuman hubungan bentuk kurva dengan kondisi di lapangan.",
                ),
                tabel,
            ]),
            pg_section_container([
                pg_section_title(
                    "Panduan Singkat Sebelum Beraktivitas di Laut",
                    "Lima langkah singkat sebelum melaut, memancing, atau berwisata.",
                ),
                checklist,
                html.Div(style={"height": "14px"}),
                keterbatasan,
            ]),
            html.P(
                f"Prediksi ini dilakukan oleh {INSTANSI_NAMA}, {INSTANSI_HOMEBASE}.",
                style={"fontStyle": "italic", "color": PG_MUTED, "fontSize": "13px", "margin": "0 4px 20px 4px"},
            ),
        ]
    )


# Callback jadwal harian
@app.callback(
    Output("pg-summary", "children"),
    Output("pg-graph", "figure"),
    Output("pg-events", "children"),
    Input("pg-station", "value"),
    Input("pg-date", "date"),
)
def update_panduan_harian(station, date_str):
    empty_fig = go.Figure()
    empty_fig.update_layout(template="plotly_white", height=360, title="Data tidak tersedia")
    info_kosong = pg_info_card("Data prediksi belum tersedia untuk stasiun dan tanggal ini.")

    if not station or not date_str or tide_dashboard_df.empty:
        return [info_kosong], empty_fig, []

    day_start = pd.Timestamp(date_str).normalize()
    day_end = day_start + pd.Timedelta(days=1)
    margin = pd.Timedelta(hours=3)  # data tambahan agar puncak di tepi hari tetap terdeteksi

    sdf = tide_dashboard_df[
        (tide_dashboard_df["station"] == station)
        & (tide_dashboard_df["datetime_wib"] >= day_start - margin)
        & (tide_dashboard_df["datetime_wib"] <= day_end + margin)
    ].sort_values("datetime_wib").drop_duplicates("datetime_wib").reset_index(drop=True)

    day_df = sdf[(sdf["datetime_wib"] >= day_start) & (sdf["datetime_wib"] < day_end)]
    if day_df.empty:
        return [info_kosong], empty_fig, []

    plot_df = sdf[(sdf["datetime_wib"] >= day_start) & (sdf["datetime_wib"] <= day_end)]

    events_all = detect_tide_extrema(sdf["datetime_wib"], sdf["tide_m"])
    events = sorted(
        [e for e in events_all if day_start <= e["waktu"] < day_end],
        key=lambda e: e["waktu"],
    )
    highs = [e for e in events if e["jenis"] == "Pasang"]
    lows = [e for e in events if e["jenis"] == "Surut"]

    h_max = max((e["tinggi"] for e in highs), default=float(day_df["tide_m"].max()))
    h_min = min((e["tinggi"] for e in lows), default=float(day_df["tide_m"].min()))
    cards = [
        pg_stat_card("Elevasi Tertinggi", f"{h_max:.3f}", "m", accent=PG_HIGH),
        pg_stat_card("Elevasi Terendah", f"{h_min:.3f}", "m", accent=PG_LOW),
        pg_stat_card("Selisih Harian", f"{h_max - h_min:.3f}", "m", accent=PG_BLUE),
        pg_stat_card("Jumlah Pasang", f"{len(highs)}", "kali", accent=PG_MSL),
    ]

    # GRAFIK
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=plot_df["datetime_wib"], y=plot_df["tide_m"], mode="lines", name="Prediksi Pasut",
        line=dict(color=PG_BLUE, width=3, shape="spline", smoothing=0.8),
        fill="tozeroy", fillcolor="rgba(46, 74, 138, 0.10)",
        hovertemplate="<b>%{x|%H:%M} WIB</b><br>Elevasi: %{y:.3f} m<extra></extra>",
    ))
    if highs:
        fig.add_trace(go.Scatter(
            x=[e["waktu"] for e in highs], y=[e["tinggi"] for e in highs],
            mode="markers+text", name="Pasang",
            marker=dict(symbol="triangle-up", size=13, color=PG_HIGH, line=dict(color="white", width=1.5)),
            text=[e["waktu"].strftime("%H:%M") for e in highs], textposition="top center",
            textfont=dict(size=11, color=PG_HIGH),
            hovertemplate="<b>Pasang</b><br>%{text} WIB<br>%{y:.3f} m<extra></extra>",
        ))
    if lows:
        fig.add_trace(go.Scatter(
            x=[e["waktu"] for e in lows], y=[e["tinggi"] for e in lows],
            mode="markers+text", name="Surut",
            marker=dict(symbol="triangle-down", size=13, color=PG_LOW, line=dict(color="white", width=1.5)),
            text=[e["waktu"].strftime("%H:%M") for e in lows], textposition="bottom center",
            textfont=dict(size=11, color=PG_LOW),
            hovertemplate="<b>Surut</b><br>%{text} WIB<br>%{y:.3f} m<extra></extra>",
        ))
    fig.add_hline(y=0, line_dash="dot", line_color="#95a5a6")
    # Rentang sumbu Y mencakup kurva yang digambar dan semua puncak/lembah
    y_lo = min(h_min, float(plot_df["tide_m"].min()))
    y_hi = max(h_max, float(plot_df["tide_m"].max()))
    pad = max((y_hi - y_lo) * 0.18, 0.05)
    fig.update_layout(
        title=dict(
            text=f"Pasang Surut Harian - {station} - {day_start.strftime('%d/%m/%Y')}",
            x=0.02, xanchor="left", font=dict(size=17, color=PG_NAVY),
        ),
        template="plotly_white", height=420,
        xaxis=dict(title="Jam (WIB)", tickformat="%H:%M", dtick=3 * 3600 * 1000,
                   range=[day_start, day_end], gridcolor=PG_GRID),
        yaxis=dict(title="Elevasi terhadap MSL (m)", range=[y_lo - pad, y_hi + pad],
                   gridcolor=PG_GRID, zeroline=False),
        hovermode="x unified",
        margin=dict(l=65, r=25, t=80, b=60),
        legend=dict(orientation="h", yanchor="bottom", y=1.04, xanchor="right", x=1),
        font=dict(family="Poppins, Arial, sans-serif"),
    )

    # DAFTAR JAM
    if not events:
        event_children = [pg_info_card("Tidak ada puncak atau lembah terdeteksi pada tanggal ini.")]
    else:
        event_children = []
        for e in events:
            is_high = e["jenis"] == "Pasang"
            warna = PG_HIGH if is_high else PG_LOW
            event_children.append(
                html.Div(
                    [
                        html.Div("\u25B2" if is_high else "\u25BC", className="pg-event-icon",
                                 style={"backgroundColor": f"{warna}22", "color": warna}),
                        html.Div(f"{e['waktu'].strftime('%H:%M')} WIB", className="pg-event-time"),
                        html.Div("Pasang tertinggi" if is_high else "Surut terendah",
                                 className="pg-event-type", style={"color": warna}),
                        html.Div(f"{e['tinggi']:.3f} m", className="pg-event-height"),
                    ],
                    className="pg-event",
                    style={"borderLeft": f"4px solid {warna}"},
                )
            )

    return cards, fig, event_children


# Isi tab Panduan 
tab_panduan_children = [build_panduan_section()]

# 15a. KONTEN TAB 1
tab_utama_children = [
    # FILTER
    html.Div(
        [
            html.Div(
                [
                    html.Label("Pilih Stasiun", style={"fontWeight": "600", "color": "#33415c"}),
                    dcc.Dropdown(
                        id="station-dropdown",
                        options=[{"label": s, "value": s} for s in station_options],
                        value=station_options[0],
                        clearable=False,
                    ),
                ],
                style={"flex": "1"},
            ),
            html.Div(
                [
                    html.Label("Pilih Bulan", style={"fontWeight": "600", "color": "#33415c"}),
                    dcc.Dropdown(
                        id="month-dropdown",
                        options=[{"label": month_indonesia[m], "value": m} for m in month_order],
                        value="January",
                        clearable=False,
                    ),
                ],
                style={"flex": "1"},
            ),
            html.Div(
                [
                    html.Label("Pilih Tahun", style={"fontWeight": "600", "color": "#33415c"}),
                    dcc.Dropdown(
                        id="year-dropdown",
                        options=[{"label": str(y), "value": y} for y in year_options],
                        value=year_options[0],
                        clearable=False,
                    ),
                ],
                style={"flex": "1"},
            ),
            html.Div(
                [
                    html.Label("\u00a0", style={"display": "block"}),
                    html.Button(
                        "\U0001F4E5 Unduh PDF",
                        id="btn-download-pdf",
                        n_clicks=0,
                        style={
                            "width": "100%", "padding": "10px 16px",
                            "backgroundColor": COLOR_ACCENT_DARK, "color": "white",
                            "border": "none", "borderRadius": "10px", "fontWeight": "600",
                            "cursor": "pointer", "fontFamily": FONT_FAMILY,
                        },
                    ),
                    dcc.Download(id="download-pdf"),
                ],
                style={"flex": "0 0 180px"},
            ),
        ],
        style={
            "display": "flex", "gap": "20px", "marginTop": "25px", "marginBottom": "10px",
            "alignItems": "flex-end", "backgroundColor": "white", "padding": "18px 20px",
            "borderRadius": "14px", "boxShadow": "0 2px 10px rgba(15, 60, 80, 0.06)",
        },
    ),

    # KETERANGAN MSL
    html.Div(
        html.P(KETERANGAN_MSL, style={"margin": "0"}),
        style={"fontSize": "13px", "color": "#6b7590", "fontStyle": "italic", "margin": "16px 4px 22px 4px"},
    ),

    # PETA
    section_container([
        html.Div(
            [
                section_title(
                    "Peta Lokasi Stasiun",
                    "Sebaran 13 titik stasiun pengamatan pasang surut di pantai selatan DIY.",
                ),
                html.Button(
                    "Kembali ke Tampilan Awal",
                    id="btn-map-home",
                    n_clicks=0,
                    title="Kembalikan peta ke posisi dan zoom awal",
                    style={
                        "padding": "9px 18px",
                        "backgroundColor": COLOR_ACCENT_DARK,
                        "color": "white",
                        "border": "none",
                        "borderRadius": "8px",
                        "fontWeight": "600",
                        "fontSize": "13px",
                        "cursor": "pointer",
                        "fontFamily": FONT_FAMILY,
                        "boxShadow": "0 2px 6px rgba(15, 60, 80, 0.18)",
                        "whiteSpace": "nowrap",
                        "flex": "0 0 auto",
                    },
                ),
            ],
            style={
                "display": "flex",
                "justifyContent": "space-between",
                "alignItems": "flex-start",
                "gap": "16px",
                "flexWrap": "wrap",
            },
        ),
        dl.Map(
            id="station-map",
            center=STATION_MAP_CENTER,
            zoom=STATION_MAP_ZOOM,
            viewport=dict(center=STATION_MAP_CENTER, zoom=STATION_MAP_ZOOM),
            style={"width": "100%", "height": "560px", "borderRadius": "12px", "zIndex": 0},
            children=build_station_map_layers(station_options[0]),
        ),
    ]),

    # SUMMARY CARDS
    html.Div(id="summary-cards", style={"display": "flex", "gap": "18px", "flexWrap": "wrap", "marginBottom": "25px"}),

    # GRAFIK PREDIKSI
    section_container([
        section_title("Grafik Prediksi Pasang Surut"),
        dcc.Graph(id="tide-graph"),
    ]),

    # VALIDASI EOT20
    section_container([
        section_title("Validasi Silang: GOT4.10 vs EOT20", KETERANGAN_VALIDASI),
        html.Div(id="validation-cards", style={"display": "flex", "gap": "18px", "flexWrap": "wrap", "marginBottom": "18px"}),
        html.Div(id="validation-graph-wrapper"),
    ]),

    # STATISTIK MINGGUAN
    section_container([
        section_title("Statistik Mingguan"),
        dcc.Graph(id="weekly-graph"),
    ]),

    # TABEL MINGGUAN
    section_container([
        section_title(
            "Tabel Statistik Mingguan",
            "Seluruh nilai elevasi (min, maks, rata-rata/MSL, range) dalam satuan meter (m), "
            "beserta daftar rentang tanggal tiap minggu yang dihitung langsung oleh dashboard.",
        ),
        dash_table.DataTable(
            id="statistics-table",
            columns=[
                {"name": "Minggu ke-", "id": "week_in_month"},
                {"name": "Tanggal Mulai", "id": "start_date"},
                {"name": "Tanggal Akhir", "id": "end_date"},
                {"name": "Jumlah Data", "id": "jumlah_data_valid"},
                {"name": "Minimum (m)", "id": "minimum_m"},
                {"name": "Maksimum (m)", "id": "maximum_m"},
                {"name": "MSL / Rata-rata (m)", "id": "mean_m"},
                {"name": "Range (m)", "id": "range_m"},
            ],
            data=[],
            page_size=10,
            sort_action="native",
            style_table={"overflowX": "auto"},
            style_cell={"textAlign": "center", "padding": "10px", "fontSize": "13px", "fontFamily": FONT_FAMILY},
            style_header={"fontWeight": "700", "backgroundColor": "#eef1f8", "color": "#0D1C42"},
            style_data_conditional=[{"if": {"row_index": "odd"}, "backgroundColor": "#f7f8fd"}],
        ),
    ]),
]


# [RADAR] 15b. KONTEN TAB 2 - VALIDASI RADAR 2026 
_default_station_radar = radar_station_options[0] if radar_station_options else None
_bulan_radar_awal = radar_bulan_tersedia(_default_station_radar)
_default_bulan_radar = _bulan_radar_awal[0] if _bulan_radar_awal else None

_RADAR_TABLE_STYLE = dict(
    style_table={"overflowX": "auto", "border": "1px solid #dfe6e9",
                 "borderRadius": "10px", "overflow": "hidden"},
    style_cell={"textAlign": "center", "padding": "10px 12px", "fontSize": "13px",
                "fontFamily": FONT_FAMILY, "color": "#33415c", "border": "none",
                "borderBottom": "1px solid #edf1f3"},
    style_header={"fontWeight": "700", "backgroundColor": "#0D1C42", "color": "white",
                  "border": "none", "fontSize": "13px"},
)

# [SITASI] 15b-1. DAFTAR RUJUKAN MENU VALIDASI 2026 (R1-R7)
# TODO: lengkapi volume/tahun terbit R1 dan nama jurnal/tahun terbit R2 (tidak tercantum pada berkas PDF).
def _doi(doi):
    return ext_link(f"https://doi.org/{doi}", f"https://doi.org/{doi}")

# Data rujukan menu Validasi 2026 (dipakai oleh tab Validasi, tab Informasi Analisis, dan PDF)
RADAR_RUJUKAN = [
    dict(pre="Umam, C., Pranowo, W. S., & Fatoni, K. I. (2019). Studi Perbandingan Karakteristik Pasang Surut Hasil "
             "Perhitungan Data Lokal dengan Model Pasang Surut Global di Perairan Indonesia. ",
         em="Jurnal Chart Datum", post=", hlm. 97-111."),
    dict(pre="Gultom, F., Harsono, G., Pranowo, W. S., & Adrianto, D. (2017). Sistem Informasi Pasang Surut Berbasis "
             "Android di Wilayah Kerja Pangkalan TNI Angkatan Laut (Studi Kasus Belawan, Tarempa, Sibolga, Natuna dan Cilacap) ", 
         em="Jurnal Chart Datum, 3", post="(2), hlm. 81-92."),
    dict(pre="Maulana, A. I., Pranowo, W. S., & Putra, I. W. S. E. (2025). Penerapan Metode Least Square untuk "
             "Analisis Komponen Pasang Surut di Perairan Omaezaki Jepang Selama Fenomena Blood Moon. ",
         em="Jurnal Hidropilar, 11", post="(2), 61-72. ", doi="10.37875/hidropilar.v11i2.402"),
    dict(pre="Wigasmara, N., Pranowo, W. S., Yulianto, Jaenudin, Alam, T. M., Sukoco, N. B., Jantarto, D., & "
             "Widodo, K. S. (2025). Analisis Konstanta Harmonik dan Pola Pasang Surut di Perairan Pulau "
             "Christmas pada Saat Terjadinya Blood Moon. ",
         em="Jurnal Chart Datum, 11", post="(2), 107-118. ", doi="10.37875/chartdatum.v12i1.401"),
    dict(pre="Fahmi, M. H., Setyadi, J., Santosa, Y. N., Pranowo, W. S., Widodo, K. S., Putra, I. W. S. E., & "
             "Sukoco, N. B. (2025). Model Prediksi Pasang Surut Berbasis Kecerdasan Buatan dengan Pendekatan "
             "Kuadrat Terkecil dan Autoencoder (Studi Kasus Stasiun Pasang Surut Muara Baru). ",
         em="Jurnal Hidropilar, 11", post="(2), 99-110. ", doi="10.37875/hidropilar.v11i2.389"),
    dict(pre="Wibowo, Y., Pranowo, W. S., Yulianto, Jantarto, D., & Alam, T. M. (2025). Komparasi Karakter Pasang "
             "Surut di Perairan Meulaboh Antara Analisis Least Square dan Admiralty. ",
         em="Jurnal Chart Datum, 11", post="(1), 1-8. ", doi="10.37875/chartdatum.v11i1.362"),
    dict(pre="Sutarto, Heriyanto, D., Pranowo, W. S., Yulianto, Sukoco, N. B., Widodo, K. S., & Alam, T. M. (2024). "
             "Analisis Harmonik Konstanta Pasang Surut di Perairan Teluk Banten Menggunakan Metode Least Square "
             "dan Admiralty. ",
         em="Jurnal Hidropilar, 10", post="(2), 73-82. ", doi="10.37875/hidropilar.v10i2.360"),
]

def _rujukan_children(r):
    c = [r["pre"]]
    if r.get("em"):
        c.append(html.Em(r["em"]))
    if r.get("post"):
        c.append(r["post"])
    if r.get("doi"):
        c.append(_doi(r["doi"]))
    return c

def _rujukan_pdf(r):
    t = r["pre"] + (f"<i>{r['em']}</i>" if r.get("em") else "") + r.get("post", "")
    if r.get("doi"):
        t += f"https://doi.org/{r['doi']}"
    return t

def radar_ref_item(number, children):
    return ref_item(number, children, id_prefix="rref")

def build_radar_rujukan():
    return html.Div([radar_ref_item(i + 1, _rujukan_children(r)) for i, r in enumerate(RADAR_RUJUKAN)])

def build_radar_rujukan_collapsible():
    """Daftar rujukan yang bisa dibuka-tutup (default tertutup)."""
    return html.Details(
        [
            html.Summary(
                [
                    html.Div([
                        html.Div("RUJUKAN", style={"fontSize": "11px", "fontWeight": "700",
                                                   "letterSpacing": "2px", "opacity": "0.8"}),
                        html.Div(f"Daftar rujukan menu Validasi {YEAR_VALIDASI_RADAR}",
                                 style={"fontSize": "15px", "fontWeight": "600", "marginTop": "2px"}),
                    ]),
                    html.Div(html.Div(className="info-chevron"), className="info-chevron-wrap"),
                ],
                className="info-summary",
                style={"background": "linear-gradient(135deg, #010736 0%, #0D1C42 60%, #22396F 100%)",
                       "color": "white"},
            ),
            html.Div(build_radar_rujukan(), style={"paddingTop": "8px"}),
        ],
        id="radar-rujukan-details", className="info-details", open=False,
        style={"marginTop": "14px"},
    )

def build_radar_konteks(cf=radar_cite):
    """Konteks dari studi terdahulu. cf = fungsi pembuat sitasi (agar nomor bisa disesuaikan per halaman)."""
    return info_callout(
        "Konteks dari studi terdahulu",
        [
            html.P(
                ["Pembandingan model pasang surut global dengan data stasiun di Indonesia pada 11 lokasi "
                 "(TPXO 7.1 lewat TMD) melaporkan korelasi 0,77-0,98 dan RMSE sekitar 10-58 cm. Tiga stasiun "
                 "dengan korelasi terendah (Marina Ancol, Lembar, Merauke) adalah perairan teluk tertutup, "
                 "dangkal, atau muara, dan selisih amplitudo atau fase M2 menjadi salah satu penyebab utama "
                 "perbedaan tersebut", cf(1), "."],
                style={"margin": "0 0 8px 0"},
            ),
            html.P(
                ["Sebagai pembanding terdekat, di Cilacap (pantai selatan Jawa) prediksi TMD terhadap data IOC "
                 "menghasilkan RMSE 9,0 cm dengan r = 0,976 (data 1 bulan) dan RMSE 16,0 cm dengan r = 0,933 "
                 "(data 3 bulan), bertipe campuran condong harian ganda", cf(2), "."],
                style={"margin": "0 0 8px 0"},
            ),
            html.P(
                ["Penggunaan data muka air dari sensor radar sebagai acuan analisis harmonik dengan t_tide juga "
                 "dilakukan pada studi stasiun IOC di Omaezaki", cf(3),
                 ", dan kesesuaian dua set amplitudo konstanta harmonik dinilai dengan korelasi serta regresi "
                 "linier (kemiringan mendekati 1)", cf(6, 7), "."],
                style={"margin": "0 0 8px 0"},
            ),
            html.P(
                "Catatan: studi-studi tersebut memakai model, lokasi, dan periode data yang berbeda dari menu ini "
                "(GOT4.10 dan EOT20, Baron dan Panggang, 2026), sehingga angkanya hanya gambaran orde besaran, "
                "bukan ambang lulus atau gagal. Nilai RMSE mutlak juga bergantung pada rentang pasang surut lokal; "
                "karena itu kesimpulan di atas turut menampilkan RMSE sebagai persentase rentang radar.",
                style={"margin": "0", "color": UI_MUTED, "fontSize": "12.5px"},
            ),
        ],
        tone="info",
    )

tab_validasi_radar_children = [

    # KETERANGAN
    html.Div(
        html.P(
            [f"Menu ini membaca hasil validasi tahun {YEAR_VALIDASI_RADAR} yang membandingkan data radar "
             f"dengan prediksi GOT4.10 dan EOT20. "
             ],
            style={"margin": "0"},
        ),
        style={"fontSize": "13px", "color": "#6b7590", "fontStyle": "italic", "margin": "16px 4px 22px 4px"},
    ),

    # INFO JIKA DATA TIDAK ADA
    (
        section_container([
            create_info_card(
                f"Hasil validasi radar tahun {YEAR_VALIDASI_RADAR} belum ditemukan. "
                f"Jalankan dahulu 'tes0.py' lalu 'GOT123s.py' sampai terbentuk berkas "
                f"analisis_pasut_gabungan_{YEAR_VALIDASI_RADAR}.xlsx, lalu muat ulang dashboard ini. "
                "Bila berkas ada di folder lain, set environment variable PASUT_RADAR_XLSX "
                "ke path lengkap berkas tersebut.",
                tone="warning",
            )
        ])
        if not VALIDASI_RADAR_TERSEDIA
        else html.Div()
    ),

    # FILTER
    html.Div(
        [
            html.Div(
                [
                    html.Label("Pilih Stasiun", style={"fontWeight": "600", "color": "#33415c"}),
                    dcc.Dropdown(
                        id="radar-station-dropdown",
                        options=[{"label": label_stasiun_radar(s), "value": s} for s in radar_station_options],
                        value=_default_station_radar,
                        clearable=False,
                        placeholder="Tidak ada data stasiun",
                    ),
                ],
                style={"flex": "1"},
            ),
            html.Div(
                [
                    html.Label("Pilih Bulan", style={"fontWeight": "600", "color": "#33415c"}),
                    dcc.Dropdown(
                        id="radar-month-dropdown",
                        options=[{"label": month_indonesia[m], "value": m} for m in _bulan_radar_awal],
                        value=_default_bulan_radar,
                        clearable=False,
                        placeholder="Tidak ada data bulan",
                    ),
                ],
                style={"flex": "1"},
            ),
            html.Div(
                [
                    html.Label(
                        "Tahun",
                        style={"fontWeight": "600", "color": "#33415c", "display": "block", "textAlign": "center"},
                    ),
                    html.Div(
                        str(YEAR_VALIDASI_RADAR),
                        style={
                            "backgroundColor": "#eef1f8", "borderRadius": "8px", "fontWeight": "600",
                            "color": "#0D1C42", "border": "1px solid #dfe6e9", "height": "38px",
                            "boxSizing": "border-box", "display": "flex", "alignItems": "center",
                            "justifyContent": "center",
                        },
                    ),
                ],
                style={"flex": "0 0 140px"},
            ),
            html.Div(
                [
                    html.Label("\u00a0", style={"display": "block"}),
                    html.Button(
                        "\U0001F4E5 Unduh PDF",
                        id="radar-btn-download-pdf",
                        n_clicks=0,
                        style={
                            "width": "100%", "padding": "10px 16px",
                            "backgroundColor": COLOR_ACCENT_DARK, "color": "white",
                            "border": "none", "borderRadius": "10px", "fontWeight": "600",
                            "cursor": "pointer", "fontFamily": FONT_FAMILY,
                        },
                    ),
                    dcc.Download(id="radar-download-pdf"),
                ],
                style={"flex": "0 0 180px"},
            ),
        ],
        style={
            "display": "flex", "gap": "20px", "marginBottom": "10px", "alignItems": "flex-end",
            "backgroundColor": "white", "padding": "18px 20px", "borderRadius": "14px",
            "boxShadow": "0 2px 10px rgba(15, 60, 80, 0.06)",
        },
    ),

    # [RADAR-UI] PANEL METRIK RINGKAS
    section_container([
        section_title(
            f"Validasi {YEAR_VALIDASI_RADAR}: Data Radar vs GOT4.10 vs EOT20",
            ["Ringkasan metrik pada stasiun dan bulan yang dipilih. Selisih dihitung sebagai model dikurangi radar, "
             "pada anomali elevasi terhadap rata-rata bulan. RMSE, MAE, dan bias; "
             "mengikuti definisi pada studi terdahulu", radar_cite(5), "."],
        ),
        html.Div(id="radar-table"),
    ]),

    # GRAFIK DERET WAKTU
    section_container([
        section_title(
            "Grafik Deret Waktu",
            "Perbandingan langsung anomali elevasi radar, GOT4.10, dan EOT20 per jam (UTC), "
            "beserta selisih model terhadap radar.",
        ),
        html.Div(
            dcc.Graph(id="radar-series-fig"),
            style={"backgroundColor": "#ffffff", "border": "1px solid #e3e8eb", "borderRadius": "12px", "padding": "8px"},
        ),
    ]),

    # DIAGRAM SEBAR
    section_container([
        section_title(
            "Diagram Sebar Model vs Radar",
            ["Titik yang mendekati garis 1:1 menunjukkan model mengikuti radar dengan baik. Kemiringan di atas 1 "
             "berarti amplitudo model lebih besar daripada radar, di bawah 1 berarti lebih kecil. Penilaian "
             "dengan regresi linier berkemiringan mendekati 1 serupa dengan yang dipakai untuk membandingkan "
             "dua set amplitudo konstanta harmonik", radar_cite(6, 7), "."],
        ),
        html.Div(
            dcc.Graph(id="radar-scatter-fig"),
            style={"backgroundColor": "#ffffff", "border": "1px solid #e3e8eb", "borderRadius": "12px", "padding": "8px"},
        ),
    ]),

    # KONSTANTA HARMONIK
    section_container([
        section_title(
            "Konstanta Harmonik: Radar vs Model",
            ["Amplitudo dan fase konstanta yang signifikan pada analisis harmonik radar dibandingkan dengan "
             "konstanta model pada titik yang sama. Kolom 'Cocok' mengikuti kriteria toleransi pengolahan. "
             "Konstanta dinilai signifikan menurut SNR atau tingkat kepercayaan 95% pada keluaran t_tide",
             radar_cite(3, 4), "."],
        ),
        html.Div(
            dcc.Graph(id="radar-konstanta-fig"),
            style={"backgroundColor": "#ffffff", "border": "1px solid #e3e8eb", "borderRadius": "12px",
                   "padding": "8px", "marginBottom": "16px"},
        ),
        dash_table.DataTable(
            id="radar-konstanta-table",
            columns=[
                {"name": "Konstanta", "id": "konstanta"},
                {"name": "Amp Radar (cm)", "id": "amp_radar"},
                {"name": "Amp GOT4.10 (cm)", "id": "amp_got"},
                {"name": "Amp EOT20 (cm)", "id": "amp_eot"},
                {"name": "Fase Radar (derajat)", "id": "fase_radar"},
                {"name": "Fase GOT4.10 (derajat)", "id": "fase_got"},
                {"name": "Fase EOT20 (derajat)", "id": "fase_eot"},
                {"name": "SNR Radar", "id": "snr"},
                {"name": "Cocok GOT4.10", "id": "cocok_got"},
                {"name": "Cocok EOT20", "id": "cocok_eot"},
            ],
            data=[], page_size=10, sort_action="native",
            style_data_conditional=[
                {"if": {"row_index": "odd"}, "backgroundColor": "#fbfcfd"},
                {"if": {"filter_query": '{cocok_got} = "Ya"', "column_id": "cocok_got"}, "color": "#1e8449", "fontWeight": "700"},
                {"if": {"filter_query": '{cocok_got} = "Tidak"', "column_id": "cocok_got"}, "color": "#c0392b", "fontWeight": "700"},
                {"if": {"filter_query": '{cocok_eot} = "Ya"', "column_id": "cocok_eot"}, "color": "#1e8449", "fontWeight": "700"},
                {"if": {"filter_query": '{cocok_eot} = "Tidak"', "column_id": "cocok_eot"}, "color": "#c0392b", "fontWeight": "700"},
            ],
            **_RADAR_TABLE_STYLE,
        ),
    ]),


    # KESIMPULAN
    section_container([
        section_title(
            "Kesimpulan",
        ),
        html.Div(id="radar-kesimpulan-pilihan"),
    ]),

    # [SITASI] KONTEKS DARI STUDI TERDAHULU
    section_container([
        section_title(
            "Konteks dari Studi Terdahulu",
            "Rujukan pembanding untuk membaca hasil validasi di atas.",
        ),
        build_radar_konteks(),
    ]),

    # INFORMASI MENU
    section_container([
        html.H3(f"Informasi Menu Validasi {YEAR_VALIDASI_RADAR}", style={"color": "#0D1C42", "marginTop": "0"}),
        html.P([KETERANGAN_VALIDASI_RADAR, radar_cite(1, 2, 5)]),   # [SITASI]
        html.P("Data acuan: pengamatan muka air sensor radar pada stasiun Baron dan Panggang (Gesing), "
               f"bulan {teks_rentang_bulan(RADAR_BULAN_SEMUA)} {YEAR_VALIDASI_RADAR}. " + SUMBER_DATA_RADAR),
        html.P("Model yang dibandingkan: GOT4.10 (Goddard Ocean Tide model) dan EOT20 (Empirical Ocean Tide model)."),
        html.Div(id="radar-info-parameter"),
        # [SITASI] daftar rujukan menu Validasi 2026 (bisa dibuka-tutup)
        build_radar_rujukan_collapsible(),
        html.P(
            f"Prediksi ini dilakukan oleh {INSTANSI_NAMA}, {INSTANSI_HOMEBASE}.",
            style={"fontStyle": "italic", "color": "#6b7590"},
        ),
    ]),
]

tab_informasi_children = [
    html.Div(style={"height": "25px"}),
    build_info_analisis_section(),
]


# 15c. LAYOUT UTAMA
_TAB_STYLE = {"fontFamily": FONT_FAMILY, "fontWeight": "600", "padding": "12px"}
_TAB_SELECTED_STYLE = {
    "fontFamily": FONT_FAMILY, "fontWeight": "700", "padding": "12px",
    "borderTop": f"3px solid {COLOR_ACCENT}", "color": COLOR_ACCENT_DARK,
}

app.layout = html.Div(
    [
        # HEADER
        html.Div(
            [
                html.Div(logo_components, style={"display": "flex", "gap": "20px", "alignItems": "center"}),
                html.Div(
                    [
                        html.H1(
                            "DASHBOARD PREDIKSI & VALIDASI PASANG SURUT LAUT",
                            style={"margin": "0", "fontSize": "26px", "color": COLOR_TITLE_MAIN, "fontWeight": "700"},
                        ),
                        html.H3(
                            f"Model Utama GOT4.10 | Validasi Silang EOT20 Tahun {YEAR_LABEL} | "
                            f"Validasi Radar {YEAR_VALIDASI_RADAR}",
                            style={"margin": "8px 0 0 0", "fontWeight": "500", "color": COLOR_TITLE_SUB},
                        ),
                        html.P(
                            "13 Stasiun Pantai Selatan Daerah Istimewa Yogyakarta",
                            style={"margin": "5px 0 0 0", "color": "#4a5c64"},
                        ),
                        html.P(
                            f"Prediksi ini dilakukan oleh {INSTANSI_NAMA} - {INSTANSI_HOMEBASE}",
                            style={"margin": "6px 0 0 0", "fontSize": "13px", "color": "#8a9aa1", "fontStyle": "italic"},
                        ),
                    ],
                    style={"textAlign": "center", "flex": "1"},
                ),
            ],
            style={
                "display": "flex", "alignItems": "center", "gap": "30px", "padding": "22px 35px",
                "backgroundColor": "white", "borderRadius": "16px",
                "boxShadow": "0 4px 16px rgba(15, 60, 80, 0.10)", "borderTop": f"5px solid {COLOR_ACCENT}",
            },
        ),

        # TABS
        dcc.Tabs(
            id="main-nav-tabs",
            value="tab-utama",
            style={"marginTop": "22px"},
            colors={"border": "#dfe6e9", "primary": COLOR_ACCENT, "background": "#f7f8fd"},
            children=[
                dcc.Tab(
                    label="Dashboard Prediksi & Validasi EOT20",
                    value="tab-utama",
                    children=tab_utama_children,
                    style=_TAB_STYLE,
                    selected_style=_TAB_SELECTED_STYLE,
                ),
                dcc.Tab(
                    label=f"Validasi {YEAR_VALIDASI_RADAR}: Radar vs GOT4.10 vs EOT20",
                    value="tab-validasi-radar",
                    children=tab_validasi_radar_children,
                    style=_TAB_STYLE,
                    selected_style=_TAB_SELECTED_STYLE,
                ),
                dcc.Tab(
                    label="Panduan Pemanfaatan",
                    value="tab-panduan",
                    children=tab_panduan_children,
                    style=_TAB_STYLE,
                    selected_style=_TAB_SELECTED_STYLE,
                ),
                dcc.Tab(
                    label="Informasi Analisis",
                    value="tab-informasi",
                    children=tab_informasi_children,
                    style=_TAB_STYLE,
                    selected_style=_TAB_SELECTED_STYLE,
                ),
            ],
        ),
    ],
    style={"minHeight": "100vh", "padding": "30px 5%", "fontFamily": FONT_FAMILY},
)


# 16. CALLBACK UTAMA
@app.callback(
    Output("summary-cards", "children"),
    Output("tide-graph", "figure"),
    Output("validation-cards", "children"),
    Output("validation-graph-wrapper", "children"),
    Output("weekly-graph", "figure"),
    Output("statistics-table", "data"),
    Input("station-dropdown", "value"),
    Input("month-dropdown", "value"),
    Input("year-dropdown", "value"),
)
def update_dashboard(selected_station, selected_month, selected_year):
    data = compute_dashboard_data(selected_station, selected_year, selected_month)
    validation_data = compute_validation_data(selected_station, selected_year, selected_month)
    # SUMMARY CARDS
    if data["jumlah_data"] == 0:
        cards = [
            create_card("Minimum", "-", "m"),
            create_card("Maksimum", "-", "m"),
            create_card("MSL/Rata-rata", "-", "m"),
            create_card("Jumlah Data", "0", "data"),
        ]
        table_data = []
    else:
        cards = [
            create_card("Elevasi Minimum", f"{data['minimum']:.3f}", "m", accent="#5dade2"),
            create_card("Elevasi Maksimum", f"{data['maximum']:.3f}", "m", accent="#f5b041"),
            create_card("MSL (Mean Sea Level)", f"{data['msl']:.3f}", "m", accent=COLOR_MSL),
            create_card("Jumlah Data", f"{data['jumlah_data']:,}", "data", accent=COLOR_ACCENT),
        ]
        table_data = data["table_df"].to_dict("records")

    # VALIDASI EOT20
    if validation_data is None:
        validation_cards = [
            create_info_card(
                "Data validasi EOT20 belum tersedia untuk kombinasi stasiun, tahun, dan bulan ini. "
                "Pastikan model EOT20 sudah diunduh secara manual dan proses validasi telah dijalankan."
            )
        ]
        empty_val_fig = go.Figure()
        empty_val_fig.update_layout(title="Data validasi tidak tersedia", template="plotly_white", height=300)
        validation_graph = dcc.Graph(figure=empty_val_fig)
    else:
        metrik = validation_data["metrik"]
        willmott_display = "-" if pd.isna(metrik.get("willmott_d")) else f"{metrik['willmott_d']:.4f}"
        validation_cards = [
            create_card("RMSE", f"{metrik['rmse_m']:.4f}", "m", accent=COLOR_MODEL_A),
            create_card("MAE", f"{metrik['mae_m']:.4f}", "m", accent=COLOR_MODEL_B),
            create_card("Korelasi (r)", f"{metrik['korelasi_r']:.4f}", "", accent=COLOR_RESIDUAL),
            create_card("Willmott's d", willmott_display, "", accent=COLOR_ACCENT),
            create_card("Jumlah Data Cocok", f"{int(metrik['n_data']):,}", "", accent="#7f8c8d"),
        ]

        validation_graph = dcc.Graph(figure=validation_data["fig"])

    return cards, data["tide_fig"], validation_cards, validation_graph, data["weekly_fig"], table_data

# 16b. CALLBACK PETA (highlight pin sesuai stasiun terpilih)
@app.callback(Output("station-map", "children"), Input("station-dropdown", "value"))
def update_station_map(selected_station):
    return build_station_map_layers(selected_station)

# 16c. CALLBACK TOMBOL HOME PETA
@app.callback(
    Output("station-map", "viewport"),
    Input("btn-map-home", "n_clicks"),
    prevent_initial_call=True,
)
def reset_station_map_view(n_clicks):
    return dict(center=STATION_MAP_CENTER, zoom=STATION_MAP_ZOOM, transition="flyTo")

# [RADAR] 16d. CALLBACK DROPDOWN BULAN VALIDASI RADAR
@app.callback(
    Output("radar-month-dropdown", "options"),
    Output("radar-month-dropdown", "value"),
    Input("radar-station-dropdown", "value"),
)
def update_radar_month_options(selected_station):
    bulan_list = radar_bulan_tersedia(selected_station) if selected_station else []
    options = [{"label": month_indonesia[m], "value": m} for m in bulan_list]
    value = bulan_list[0] if bulan_list else None
    return options, value

# [RADAR] 16e. CALLBACK TAB VALIDASI RADAR - panel metrik, grafik, kesimpulan pilihan
@app.callback(
    Output("radar-table", "children"),
    Output("radar-konstanta-fig", "figure"),
    Output("radar-konstanta-table", "data"),
    Output("radar-series-fig", "figure"),
    Output("radar-scatter-fig", "figure"),
    Output("radar-kesimpulan-pilihan", "children"),
    Output("radar-info-parameter", "children"),
    Input("radar-station-dropdown", "value"),
    Input("radar-month-dropdown", "value"),
)
def update_radar_page(selected_station, selected_month):
    # bagian yang tidak bergantung pada pilihan (dari lembar 'Parameter' hasil GOT123s.py)
    par, diperbarui = radar_ambil_parameter()
    info_parameter = build_radar_info_parameter(par, diperbarui)

    kosong_konst = _fig_kosong("Pilih stasiun dan bulan untuk menampilkan grafik", 420)
    kosong_series = _fig_kosong("Pilih stasiun dan bulan untuk menampilkan data", 520)
    kosong_sebar = _fig_kosong("Pilih stasiun dan bulan untuk menampilkan data", 420)

    if not selected_station or not selected_month:
        pesan = create_info_card("Pilih stasiun dan bulan untuk melihat kesimpulan khusus pilihan tersebut.")
        return [], kosong_konst, [], kosong_series, kosong_sebar, pesan, info_parameter

    bulan_no = MONTH_NAME_TO_NUMBER[selected_month]
    deret_df = radar_ambil_tabel("radar2026_metrik_deret", selected_station, bulan_no)
    kons_df = radar_ambil_tabel("radar2026_metrik_konstanta", selected_station, bulan_no)
    detail_df = radar_ambil_tabel("radar2026_detail_konstanta", selected_station, bulan_no,
                                  order="konstanta, model")
    seri_df = radar_ambil_deret(selected_station, bulan_no)

    if deret_df.empty and seri_df.empty:
        pesan = create_info_card("Data tidak tersedia untuk kombinasi stasiun dan bulan ini.")
        return [], kosong_konst, [], kosong_series, kosong_sebar, pesan, info_parameter

    deret = _per_model(deret_df)
    kons = _per_model(kons_df)
    judul_stasiun = (f"{label_stasiun_radar(selected_station)}, "
                     f"{month_indonesia[selected_month]} {YEAR_VALIDASI_RADAR}")

    panel_metrik = build_radar_metric_table(deret, kons)
    fig_konst = build_radar_constituent_fig(detail_df)
    tabel_konst = build_radar_constituent_table(detail_df)
    if seri_df.empty:
        fig_series = _fig_kosong("Deret waktu per jam tidak tersedia pada berkas hasil", 520)
        fig_sebar = _fig_kosong("Deret waktu per jam tidak tersedia pada berkas hasil", 420)
    else:
        fig_series = build_radar_series_fig(seri_df, judul_stasiun)
        fig_sebar = build_radar_scatter_fig(seri_df, deret)
    pilihan = build_radar_kesimpulan_pilihan(selected_station, selected_month, deret, kons, detail_df, par)

    return panel_metrik, fig_konst, tabel_konst, fig_series, fig_sebar, pilihan, info_parameter

# 17. CALLBACK DOWNLOAD PDF
@app.callback(
    Output("download-pdf", "data"),
    Input("btn-download-pdf", "n_clicks"),
    State("station-dropdown", "value"),
    State("month-dropdown", "value"),
    State("year-dropdown", "value"),
    prevent_initial_call=True,
)
def download_pdf(n_clicks, selected_station, selected_month, selected_year):
    data = compute_dashboard_data(selected_station, selected_year, selected_month)
    validation_data = compute_validation_data(selected_station, selected_year, selected_month)
    pdf_buffer = build_pdf_report(selected_station, selected_year, selected_month, data, validation_data)
    filename = (
        f"dashboard_pasut_{selected_station}_{selected_year}_{selected_month}.pdf".replace(" ", "_")
    )
    return dcc.send_bytes(pdf_buffer.getvalue(), filename=filename)

# [RADAR] 17b. CALLBACK DOWNLOAD PDF VALIDASI RADAR
@app.callback(
    Output("radar-download-pdf", "data"),
    Input("radar-btn-download-pdf", "n_clicks"),
    State("radar-station-dropdown", "value"),
    State("radar-month-dropdown", "value"),
    prevent_initial_call=True,
)
def download_radar_pdf(n_clicks, selected_station, selected_month):
    if not selected_station or not selected_month:
        return no_update
    bulan_no = MONTH_NAME_TO_NUMBER[selected_month]
    deret_df = radar_ambil_tabel("radar2026_metrik_deret", selected_station, bulan_no)
    if deret_df.empty:
        return no_update
    kons_df = radar_ambil_tabel("radar2026_metrik_konstanta", selected_station, bulan_no)
    detail_df = radar_ambil_tabel("radar2026_detail_konstanta", selected_station, bulan_no,
                                  order="konstanta, model")
    seri_df = radar_ambil_deret(selected_station, bulan_no)
    par, diperbarui = radar_ambil_parameter()
    pdf_buffer = build_radar_pdf_report(
        selected_station, selected_month, _per_model(deret_df), _per_model(kons_df),
        detail_df, seri_df, par, diperbarui,
    )
    filename = f"validasi_radar_{selected_station}_{selected_month}_{YEAR_VALIDASI_RADAR}.pdf".replace(" ", "_")
    return dcc.send_bytes(pdf_buffer.getvalue(), filename=filename)

# 18. SALIN LOGO & FOTO PANDUAN KE ASSETS
ASSETS_DIR = BASE_DIR / "assets"
ASSETS_DIR.mkdir(parents=True, exist_ok=True)
if LOGO_BRIN.exists():
    shutil.copy2(LOGO_BRIN, ASSETS_DIR / "logo_brin.png")
if LOGO_DKP.exists():
    shutil.copy2(LOGO_DKP, ASSETS_DIR / "logo_dkp_diy.png")

(ASSETS_DIR / "panduan").mkdir(parents=True, exist_ok=True)
_foto_ditemukan = []
for _nama in ("nelayan", "pemancing", "wisata", "pengelola"):
    _p = find_panduan_image(_nama)
    if _p is not None:
        shutil.copy2(_p, ASSETS_DIR / "panduan" / _p.name)
        _foto_ditemukan.append(_nama)

# 19. MENJALANKAN DASHBOARD
print("\n" + "=" * 70)
print("DASHBOARD INTERAKTIF :)")
print("=" * 70)
print("Dashboard membaca prediksi GOT4.10 dan validasi EOT20 dari CSV di folder :", OLAH_DIR)
print(
    f"Dashboard membaca data validasi radar {YEAR_VALIDASI_RADAR} (GOT123s.py)    :",
    RADAR_XLSX if VALIDASI_RADAR_TERSEDIA
    else "(belum tersedia - jalankan tes0.py lalu GOT123s.py, atau set PASUT_RADAR_XLSX)",
)
print(
    "Dashboard membaca hasil t_tide radar (tes0.py)                :",
    TTIDE_DIR if TTIDE_TERSEDIA else "(belum tersedia - jalankan tes0.py, atau set PASUT_TTIDE_DIR)",
)
print("Tahun tersedia pada menu prediksi          :", year_options)
print(
    f"Stasiun tersedia pada menu Validasi {YEAR_VALIDASI_RADAR}   :",
    radar_station_options if radar_station_options else "(tidak ada)",
)
print(
    f"Bulan tersedia pada menu Validasi {YEAR_VALIDASI_RADAR}     :",
    teks_rentang_bulan(RADAR_BULAN_SEMUA),
)
print(
    "Foto panduan terpakai                      :",
    _foto_ditemukan if _foto_ditemukan else f"(belum ada; memakai ilustrasi bawaan. Taruh foto di {PANDUAN_IMG_DIR})",
)
print("\nDashboard akan dibuka pada:")
print("http://127.0.0.1:8050/")

# 19b. WAKTU PEMBANGUNAN DASHBOARD
_T_SELESAI = _time.perf_counter()
print("\n" + "=" * 70)
print("WAKTU PEMBANGUNAN DASHBOARD")
print("=" * 70)
print(f"Memuat data & definisi fungsi : {_T_DATA - _T0:8.2f} detik")
print(f"Menyusun layout & komponen    : {_T_SELESAI - _T_DATA:8.2f} detik")
print(f"TOTAL                         : {_T_SELESAI - _T0:8.2f} detik")

# 20. OTOMATIS BUKA BROWSER
def open_browser():
    webbrowser.open("http://127.0.0.1:8050/")
threading.Timer(1.5, open_browser).start()

# 21. RUN DASH
app.run(debug=False, port=8050)