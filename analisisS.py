"""
ANALISIS PASUT TERPADU: DATA RADAR (dataPB.xlsx) vs pyTMD (GOT4.10 & EOT20)
Stasiun : Baron dan Panggang (Gesing)
Periode : Januari - Agustus 2026
Analisis tambahan: sensitivitas ambang kecocokan konstanta harmonik.
"""

import os
import pathlib
import warnings
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats

import pyTMD

warnings.filterwarnings("ignore")

def _lokasi_skrip():
    try:
        return Path(__file__).resolve().parent
    except NameError:  # __file__ tidak ada (mis. run cell / interactive)
        return Path.cwd().resolve()


BASE_DIR = _lokasi_skrip()
MODEL_DIR = BASE_DIR / "pytmd_data"
OLAH_DIR = BASE_DIR / "OLAH"
HASIL_DIR = BASE_DIR / "HASIL_NAN0"
FILE_RADAR_PATH = OLAH_DIR / "dataPB.xlsx"

# PENGATURAN
FILE_RADAR = str(FILE_RADAR_PATH)                                      # data radar 
DIR_MODEL = str(MODEL_DIR)                                             # folder model pyTMD 
DIR_OUT = str(HASIL_DIR / "ANALISIS_SENSITIVITAS")  # folder hasil 

TAHUN = 2026
BULAN = {1: "Januari", 2: "Februari", 3: "Maret", 4: "April", 5: "Mei", 6: "Juni", 7: "Juli", 8: "Agustus"}

# koordinat stasiun: (lon, lat)
STASIUN = {
    "Baron":    (110.548490, -8.131006),
    "Panggang": (110.468404, -8.107678),   # Gesing
}
KUNCI_SHEET_STASIUN = {"Baron": ["baron"], "Panggang": ["panggang", "gesing"]}
KUNCI_SHEET_BULAN = {
    1: ["jan"], 2: ["feb"], 3: ["mar"], 4: ["apr"],
    5: ["mei", "may"], 6: ["jun"], 7: ["jul"], 8: ["agu", "aug"],
}

MODELS = {"GOT4.10": "GOT4.10_nc", "EOT20": "EOT20"}
KATA_KUNCI = {"GOT4.10_nc": "got4.10", "GOT4.10": "got4.10", "EOT20": "eot20"}
METODE_INTERPOLASI = "nearest"   # untuk prediksi deret waktu
CUTOFF_KM = 50.0                 # ekstrapolasi deret waktu
CUTOFF_KONSTANTA_KM = 100.0      # ekstrapolasi konstanta

# zona waktu cadangan jika header sheet tidak menyebut UTC/WIB
TZ_RADAR_JAM = 0
TZ_AKTIF = TZ_RADAR_JAM

# QC data radar per menit (disamakan dengan t__tide.py)
QC_AKTIF = True
QC_JENDELA_MENIT = 31
QC_N_SIGMA = 4.0
QC_MIN_AMBANG_M = 0.5
QC_RUN_DATAR_MENIT = 30
MIN_SAMPEL_PER_JAM = 20
INTERP_METODE = "time"
INTERP_LIMIT_JAM = 6
MAKS_LAG_JAM = 8

# NaN yang tersisa setelah interpolasi gap pendek menjadi anomali 0.
# Artinya setara muka air rata-rata, bukan elevasi absolut 0 m.
NAN_JADI_NOL = True

# analisis harmonik radar
HARMONIK_SUMBER = "ttide_file"
DIR_TTIDE = str(HASIL_DIR)                  
POLA_FILE_TTIDE = "hasil_harmonik_{stasiun}_{bulan}.xlsx"
KODE_BULAN_TTIDE = {1: "Jan", 2: "Feb", 3: "Maret", 4: "April",
                    5: "Mei", 6: "Juni", 7: "Juli", 8: "Agust"}
# bila file T_TIDE suatu bulan tidak ada: True = hitung dengan UTide, False = lewati konstanta bulan itu
HARMONIK_CADANGAN_AKTIF = True
SNR_MIN = 1.0

# kriteria "cocok" (perbandingan konstanta)
TOL_AMP_CM = 2.0
TOL_AMP_PCT = 20.0
TOL_FASE_DEG = 20.0
KONSTANTA_UTAMA = ["M2", "S2", "N2", "K2", "K1", "O1", "P1", "Q1", "M4"]

if not os.path.isfile(FILE_RADAR):
    raise FileNotFoundError(
        "Berkas data radar tidak ditemukan:\n  " + str(FILE_RADAR) + "\n"
        "Letakkan 'dataPB.xlsx' di dalam folder 'OLAH' yang berada satu folder dengan skrip ini."
    )
print("Folder skrip :", BASE_DIR)
print("Data radar   :", FILE_RADAR)
os.makedirs(DIR_OUT, exist_ok=True)
WARNA = {"Radar": "#1f77b4", "GOT4.10": "#2ca02c", "EOT20": "#ff7f0e"}

#FUNGSI BANTU
ALIAS = {
    "lda2": "lambda2", "lam2": "lambda2", "alp1": "alpha1", "bet1": "beta1",
    "sig1": "sigma1", "the1": "theta1", "ups1": "upsilon1",
    "2q1": "2q1", "2n2": "2n2", "mu2": "mu2", "nu2": "nu2", "l2": "l2", "t2": "t2",
}


def norm_nama(x):
    s = str(x).strip().lower().replace(" ", "")
    return ALIAS.get(s, s)


def sel_fase(a, b):
    """Selisih fase sirkular a-b dalam derajat (-180..180)."""
    return (np.asarray(a) - np.asarray(b) + 180.0) % 360.0 - 180.0


def rmse(x):
    x = np.asarray(x, dtype=float)
    x = x[~np.isnan(x)]
    return np.sqrt(np.mean(x ** 2)) if x.size else np.nan

#TAHAP 1: BACA & QC RADAR
def _pilih_sheet(nama_sheet, stasiun, bulan):
    s_low = {s: s.lower() for s in nama_sheet}
    cocok_stn = [s for s, l in s_low.items() if any(k in l for k in KUNCI_SHEET_STASIUN[stasiun])]
    cocok_both = [s for s in cocok_stn if any(k in s_low[s] for k in KUNCI_SHEET_BULAN[bulan])]
    if cocok_both:
        return cocok_both[0], False
    if len(cocok_stn) == 1:
        return cocok_stn[0], True
    raise ValueError(f"Sheet untuk {stasiun} bulan {bulan} tidak ditemukan. Daftar sheet: {nama_sheet}")

def _parse_waktu(kolom, bulan):
    w1 = pd.to_datetime(kolom, errors="coerce")
    w2 = pd.to_datetime(kolom, errors="coerce", dayfirst=True)
    s1 = ((w1.dt.year == TAHUN) & (w1.dt.month == bulan)).mean()
    s2 = ((w2.dt.year == TAHUN) & (w2.dt.month == bulan)).mean()
    return w2 if s2 > s1 else w1

def baca_radar(stasiun, bulan):
    """Baca sheet radar (baris judul + header 'Time (UTC) | bat(V) | rad(m)')."""
    global TZ_AKTIF
    xls = pd.ExcelFile(FILE_RADAR)
    sheet, filter_tanggal = _pilih_sheet(xls.sheet_names, stasiun, bulan)
    raw = xls.parse(sheet, header=None)

    awal = None
    for i in range(min(40, len(raw))):
        w = pd.to_datetime(pd.Series([raw.iat[i, 0]]), errors="coerce").iloc[0]
        angka = pd.to_numeric(raw.iloc[i, 1:], errors="coerce").notna().any()
        if pd.notna(w) and angka and not isinstance(raw.iat[i, 0], (int, float)):
            awal = i
            break
    if awal is None:
        print(raw.head(15).to_string())
        raise ValueError(f"Baris data tidak ditemukan di sheet {sheet}.")

    header_teks = []
    for i in range(max(0, awal - 5), awal):
        header_teks.append([str(x) if pd.notna(x) else "" for x in raw.iloc[i]])
    nama_kol = [" | ".join(t for t in (h[j] for h in header_teks) if t) or f"kolom{j}"
                for j in range(raw.shape[1])]
    print(f"  [KOLOM TERDETEKSI] sheet='{sheet}' | data mulai baris {awal + 1}")
    for j, n in enumerate(nama_kol):
        print(f"     kolom {j}: {n}")

    low = [n.lower() for n in nama_kol]
    c_val = next((j for j in range(1, raw.shape[1]) if "rad" in low[j]), None)
    if c_val is None:
        c_val = next((j for j in range(1, raw.shape[1])
                      if pd.to_numeric(raw.iloc[awal:, j], errors="coerce").notna().mean() > 0.5), None)
        print(f"  (header 'rad' tidak ada -> memakai kolom {c_val})")
    if c_val is None:
        raise ValueError(f"Kolom radar tidak ditemukan di sheet {sheet}.")
    print(f"  Kolom radar dipakai: kolom {c_val} ({nama_kol[c_val]})")

    teks_all = " ".join(low[:2]) + " " + " ".join(" ".join(h).lower() for h in header_teks)
    TZ_AKTIF = TZ_RADAR_JAM
    if "utc" in teks_all or ("gmt" in teks_all and "+7" not in teks_all):
        TZ_AKTIF = 0
        print("  Header menyebut UTC/GMT -> zona waktu radar = 0")
    elif "wib" in teks_all or "+7" in teks_all or "+07" in teks_all:
        TZ_AKTIF = 7
        print("  Header menyebut WIB/+7 -> zona waktu radar = 7")
    else:
        print(f"  Zona waktu tidak tertulis -> memakai TZ_RADAR_JAM = {TZ_RADAR_JAM}")

    data = raw.iloc[awal:]
    waktu = _parse_waktu(data.iloc[:, 0], bulan)
    seri = pd.Series(
        pd.to_numeric(data.iloc[:, c_val], errors="coerce").values,
        index=waktu.values
    )
    # Pertahankan NaN agar dihitung sebagai sampel kosong saat agregasi per jam,
    # bukan menghapusnya sebelum proses QC.
    seri = seri[seri.index.notna()].sort_index()
    seri = seri[~seri.index.duplicated()]
    seri.index = pd.DatetimeIndex(seri.index)
    # selalu batasi ke bulan target: beberapa sheet memuat 1 baris dari bulan berikutnya
    # (mis. Baron Mei s/d 1 Juni 00:00, Panggang Agustus s/d 1 September 00:00)
    n_sebelum = len(seri)
    seri = seri[(seri.index.year == TAHUN) & (seri.index.month == bulan)]
    if len(seri) < n_sebelum:
        print(f"  Filter bulan {bulan}/{TAHUN}: {n_sebelum - len(seri)} baris di luar bulan dibuang")
    print(f"  Data mentah: {len(seri)} baris | {seri.index.min()} s/d {seri.index.max()}")
    return seri

def bersihkan_radar(seri):
    """QC per menit: (1) buang nilai macet, (2) buang lonjakan dari median berjalan."""
    n0 = len(seri)
    x = seri.copy()

    sama = x.diff().eq(0)
    grup = (sama != sama.shift()).cumsum()
    panjang = sama.groupby(grup).transform("sum")
    macet = sama & (panjang >= QC_RUN_DATAR_MENIT - 1)
    macet = macet | (macet.shift(-1, fill_value=False) & ~macet)
    n_macet = int(macet.sum())
    x = x[~macet]

    med = x.rolling(QC_JENDELA_MENIT, center=True, min_periods=5).median()
    res = x - med
    sigma = 1.4826 * np.nanmedian(np.abs(res - np.nanmedian(res)))
    ambang = max(QC_MIN_AMBANG_M, QC_N_SIGMA * sigma)
    lonjakan = res.abs() > ambang
    n_lonjakan = int(lonjakan.sum())
    x = x[~lonjakan]

    print(f"  QC: {n0} -> {len(x)} data | macet dibuang: {n_macet} | "
          f"lonjakan dibuang: {n_lonjakan} (ambang {ambang:.2f} m)")
    return x

def radar_per_jam(seri):
    """Rata-rata per jam pada interval [hh:00, hh+1:00), label hh:30.
    Minimal 20 sampel per jam; interpolasi hanya untuk gap utuh <= 6 jam.
    Algoritma disamakan dengan ke_per_jam() dan isi_gap() pada t__tide.py.
    """
    g = seri.resample("1h", closed="left", label="left")
    h = g.mean()
    jml = g.count()
    h[jml < MIN_SAMPEL_PER_JAM] = np.nan

    # Pastikan semua jam dalam rentang waktu tersedia.
    if len(h) == 0:
        return h, 0, 0
    penuh = pd.date_range(h.index[0], h.index[-1], freq="1h")
    h = h.reindex(penuh)

    n_kosong = int(h.isna().sum())

    # Interpolasi berbasis waktu, tetapi hanya untuk gap utuh <= 6 jam.
    kosong = h.isna().values
    terinterpolasi = h.interpolate(
        method=INTERP_METODE,
        limit_area="inside"
    )
    boleh = np.zeros(len(h), dtype=bool)
    i = 0
    while i < len(h):
        if kosong[i]:
            j = i
            while j < len(h) and kosong[j]:
                j += 1
            if (j - i) <= INTERP_LIMIT_JAM:
                boleh[i:j] = True
            i = j
        else:
            i += 1

    h_interp = h.copy()
    h_interp[ boleh ] = terinterpolasi[ boleh ]
    n_interp = int((boleh & h_interp.notna().values).sum())

    # Label waktu di tengah interval jam.
    h_interp.index = h_interp.index + pd.Timedelta(minutes=30)
    return h_interp, n_kosong, n_interp

#TAHAP 2: HARMONIK RADAR
def harmonik_utide(jam_utc, lat):
    """Analisis harmonik deret per jam (UTC) dengan UTide -> Konstanta, Amp_cm, Fase, SNR."""
    from utide import solve
    s = jam_utc.dropna()
    coef = solve(s.index.to_numpy(), (s - s.mean()).values, lat=lat,
                 method="ols", conf_int="linear", trend=False, nodal=True,
                 constit="auto", Rayleigh_min=1.0, verbose=False)
    snr = (np.asarray(coef["A"]) / np.asarray(coef["A_ci"])) ** 2   # definisi T_TIDE: (A/galat95)^2
    out = pd.DataFrame({
        "Konstanta": [str(n).strip().upper() for n in coef["name"]],
        "Amp_cm": np.asarray(coef["A"]) * 100.0,
        "Fase": np.asarray(coef["g"]) % 360.0,
        "SNR": snr,
    })
    out["Signifikan"] = out["SNR"] > SNR_MIN
    out["key"] = out["Konstanta"].map(norm_nama)
    return out

def cari_kolom(cols, kunci, kecuali=()):
    for c in cols:
        lc = str(c).lower()
        if any(k in lc for k in kunci) and not any(e in lc for e in kecuali):
            return c
    return None

def harmonik_file_ttide(path):
    """Alternatif: baca Excel hasil T_TIDE (jika HARMONIK_SUMBER = 'ttide_file')."""
    xls = pd.ExcelFile(path)
    df = None
    for sh in xls.sheet_names:
        tmp = xls.parse(sh)
        if cari_kolom(tmp.columns, ["amp"], ["err", "galat"]) is not None:
            df = tmp
            break
    if df is None:
        raise ValueError(f"Kolom amplitudo tidak ditemukan di {path}")
    cols = list(df.columns)
    c_nm = cari_kolom(cols, ["konst", "const", "nama", "name", "tide"], ["err"]) or cols[0]
    c_amp = cari_kolom(cols, ["amp"], ["err", "galat"])
    c_fas = cari_kolom(cols, ["fase", "phase", "pha"], ["err", "galat"])
    c_snr = cari_kolom(cols, ["snr"])
    out = pd.DataFrame({
        "Konstanta": df[c_nm].astype(str).str.strip().str.upper(),
        "Amp_raw": pd.to_numeric(df[c_amp], errors="coerce"),
        "Fase": pd.to_numeric(df[c_fas], errors="coerce") % 360.0,
    })
    out["SNR"] = pd.to_numeric(df[c_snr], errors="coerce") if c_snr else np.nan
    out["Signifikan"] = (out["SNR"] > SNR_MIN) if c_snr else True
    h = str(c_amp).lower()
    if "(cm)" in h or " cm" in h:
        unit = "cm"
    elif "(m)" in h or " m)" in h:
        unit = "m"
    else:
        m2 = out.loc[out["Konstanta"] == "M2", "Amp_raw"]
        ref = m2.iloc[0] if len(m2) else out["Amp_raw"].max()
        unit = "cm" if ref > 5 else "m"
    out["Amp_cm"] = out["Amp_raw"] * (1.0 if unit == "cm" else 100.0)
    out = out.dropna(subset=["Amp_cm", "Fase"]).copy()
    out["key"] = out["Konstanta"].map(norm_nama)
    return out.drop(columns=["Amp_raw"])

#TAHAP 3: KONSTANTA pyTMD
def _cari_file_model(f, direktori, kata_kunci):
    f = pathlib.Path(f)
    nama = f.name[:-3] if f.name.endswith(".gz") else f.name
    for cand in (f, f.with_name(nama), f.with_name(nama + ".gz")):
        if cand.exists():
            return cand
    for p in pathlib.Path(direktori).rglob(nama + "*"):
        if p.is_file() and kata_kunci.lower() in str(p).lower() \
                and p.name in (nama, nama + ".gz"):
            return p
    return None

def _ekstrak_v3(nama_model, lon, lat, direktori):
    """pyTMD >= 3.0 (xarray)."""
    import pyTMD.io
    m = pyTMD.io.model(direktori, verify=False).from_database(nama_model, group="z")
    kunci = KATA_KUNCI.get(nama_model, nama_model)
    ada, hilang = [], []
    for f in list(m.z.model_file):
        hit = _cari_file_model(f, direktori, kunci)
        if hit is None:
            hilang.append(pathlib.Path(f).name)
        else:
            ada.append(hit)
    if hilang:
        print(f"   [!] {nama_model}: file tidak ditemukan -> {', '.join(hilang)}")
    if not ada:
        raise FileNotFoundError(f"Tidak ada file {nama_model} di {direktori}.")
    m.z.model_file = ada
    ds = m.open_dataset(group="z", compressed=None)
    X, Y = ds.tmd.coords_as(lon, lat)
    try:
        local = ds.tmd.interp(X, Y, method="linear", extrapolate=True, cutoff=CUTOFF_KONSTANTA_KM)
    except ImportError:
        print("   [!] dask tidak ada -> ekstrapolasi dimatikan (pip install dask)")
        local = ds.tmd.interp(X, Y, method="linear", extrapolate=False)
    rows = []
    for c in local.tmd.constituents:
        z = np.asarray(local[c].values).squeeze()
        if np.isnan(z.real) or np.isnan(z.imag):
            continue
        rows.append({"key": norm_nama(c),
                     "Amp_cm": float(np.abs(z)) * 100.0,
                     "Fase": float(np.degrees(np.arctan2(-z.imag, z.real)) % 360.0)})
    return pd.DataFrame(rows)

def _ekstrak_v2(nama_model, lon, lat, direktori):
    """pyTMD 2.x (API lama)."""
    import pyTMD.io
    mdl = pyTMD.io.model(direktori, compressed=False)
    mdl = mdl.from_database(nama_model) if hasattr(mdl, "from_database") else mdl.elevation(nama_model)
    fmt = mdl.format
    if fmt in ("GOT-ascii", "GOT-netcdf"):
        amp, ph, D, cons = pyTMD.io.GOT.extract_constants(
            [lon], [lat], mdl.model_file, grid=fmt, method="spline",
            extrapolate=True, cutoff=CUTOFF_KONSTANTA_KM, scale=mdl.scale,
            compressed=mdl.compressed)
    elif fmt in ("FES-ascii", "FES-netcdf"):
        mfile = mdl.model_file["z"] if isinstance(mdl.model_file, dict) else mdl.model_file
        amp, ph, D, cons = pyTMD.io.FES.extract_constants(
            [lon], [lat], mfile, type=mdl.type, version=mdl.version,
            method="spline", extrapolate=True, cutoff=CUTOFF_KONSTANTA_KM,
            scale=mdl.scale, compressed=mdl.compressed)
    else:
        raise NotImplementedError(f"Format model '{fmt}' belum didukung.")
    amp = np.ma.filled(np.ma.array(amp), np.nan).reshape(-1)
    ph = np.ma.filled(np.ma.array(ph), np.nan).reshape(-1)
    return pd.DataFrame({"key": [norm_nama(c) for c in cons],
                         "Amp_cm": amp * 100.0, "Fase": ph % 360.0}).dropna()
def ekstrak_pytmd(nama_model, lon, lat, direktori):
    import pyTMD.io
    if hasattr(pyTMD.io.model, "open_dataset"):
        return _ekstrak_v3(nama_model, lon, lat, direktori)
    return _ekstrak_v2(nama_model, lon, lat, direktori)

def prediksi_pytmd(nama_db, lon, lat, waktu_utc):
    """Elevasi (m) pasut pyTMD pada array waktu UTC (datetime64)."""
    tide = pyTMD.compute.tide_elevations(
        np.array([lon]), np.array([lat]), waktu_utc,
        directory=DIR_MODEL, model=nama_db, crs=4326,
        type="time series", standard="datetime", method=METODE_INTERPOLASI,
        extrapolate=True, cutoff=CUTOFF_KM)
    try:
        v = np.asarray(tide.values).squeeze()
    except Exception:
        v = np.asarray(tide).squeeze()
    return np.asarray(v, dtype=float).flatten()

#TAHAP 4 & 5: METRIK
def bandingkan_konstanta(tt_sig, dfm):
    """Gabung konstanta radar (signifikan) dengan model -> tabel selisih."""
    m = tt_sig.merge(dfm, on="key", how="inner", suffixes=("_tt", "_md"))
    if m.empty:
        return m
    m["dAmp_cm"] = m["Amp_cm_md"] - m["Amp_cm_tt"]
    m["dAmp_%"] = 100.0 * m["dAmp_cm"] / m["Amp_cm_tt"]
    m["dFase_deg"] = sel_fase(m["Fase_md"], m["Fase_tt"])
    m["dVektor_cm"] = np.sqrt(np.clip(
        m["Amp_cm_tt"] ** 2 + m["Amp_cm_md"] ** 2
        - 2 * m["Amp_cm_tt"] * m["Amp_cm_md"] * np.cos(np.deg2rad(m["dFase_deg"])), 0, None))
    m["Cocok"] = (((m["dAmp_cm"].abs() <= TOL_AMP_CM) | (m["dAmp_%"].abs() <= TOL_AMP_PCT))
                  & (m["dFase_deg"].abs() <= TOL_FASE_DEG)).map({True: "Ya", False: "Tidak"})
    return m

def hitung_metrik(obs, mod):
    """obs = radar (anomali), mod = model (anomali). Selisih = model - radar."""
    d = mod - obs
    r = stats.pearsonr(obs, mod)[0] if np.std(obs) > 0 and np.std(mod) > 0 else np.nan
    om = np.mean(obs)
    den = np.sum((np.abs(mod - om) + np.abs(obs - om)) ** 2)
    willmott = 1 - np.sum(d ** 2) / den if den else np.nan
    slope = stats.linregress(obs, mod).slope if np.std(obs) > 0 else np.nan
    return {
        "n_jam": len(obs),
        "Bias_cm": np.mean(d) * 100,
        "RMSE_cm": np.sqrt(np.mean(d ** 2)) * 100,
        "MAE_cm": np.mean(np.abs(d)) * 100,
        "r": r, "R2": r ** 2 if r == r else np.nan,
        "Willmott_d": willmott,
        "Kemiringan_model_vs_radar": slope,
        "Rentang_radar_cm": (obs.max() - obs.min()) * 100,
        "Rentang_model_cm": (mod.max() - mod.min()) * 100,
    }

def lag_terbaik(obs, mod, maks=MAKS_LAG_JAM):
    """Selisih waktu (jam) yang memaksimalkan korelasi.
    k > 0 : pola model muncul k jam LEBIH AWAL daripada radar.
    k < 0 : pola model muncul |k| jam LEBIH LAMBAT. Idealnya 0."""
    hasil = {}
    for k in range(-maks, maks + 1):
        a = obs
        b = mod.shift(k)
        ok = a.notna() & b.notna()
        if ok.sum() > 24:
            hasil[k] = np.corrcoef(a[ok], b[ok])[0, 1]
    if not hasil:
        return np.nan, np.nan
    k = max(hasil, key=hasil.get)
    return k, hasil[k]

#GRAFIK
def grafik_deret(df, stasiun, label_bulan, metrik, path):
    fig, ax = plt.subplots(2, 1, figsize=(15, 8), sharex=True,
                           gridspec_kw={"height_ratios": [3, 1.6]})
    ax[0].plot(df.index, df["Radar_m"], color=WARNA["Radar"], lw=1.3, label="Radar (anomali)")
    for m in MODELS:
        ax[0].plot(df.index, df[f"{m}_m"], color=WARNA[m], lw=1.0, ls="--", label=m)
    ax[0].set_ylabel("Elevasi terhadap rata-rata bulan (m)")
    ax[0].set_title(f"{stasiun} - {label_bulan} {TAHUN}: prediksi pyTMD vs data radar")
    ax[0].grid(alpha=.3)
    ax[0].legend(loc="upper right")
    for m in MODELS:
        ax[1].plot(df.index, df[f"{m}_m"] - df["Radar_m"], color=WARNA[m], lw=0.9,
                   label=f"{m}: RMSE {metrik[m]['RMSE_cm']:.1f} cm, r {metrik[m]['r']:.3f}")
    ax[1].axhline(0, color="k", lw=.6)
    ax[1].set_ylabel("Model - radar (m)")
    ax[1].set_xlabel("Waktu (UTC)")
    ax[1].grid(alpha=.3)
    ax[1].legend(loc="upper right", fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)

def grafik_sebar(df, stasiun, label_bulan, metrik, path):
    fig, ax = plt.subplots(1, len(MODELS), figsize=(5.5 * len(MODELS), 5), sharex=True, sharey=True)
    ax = np.atleast_1d(ax)
    lim = max(df["Radar_m"].abs().max(), *(df[f"{m}_m"].abs().max() for m in MODELS)) * 1.05
    for a, m in zip(ax, MODELS):
        a.scatter(df["Radar_m"], df[f"{m}_m"], s=6, alpha=.5, color=WARNA[m])
        a.plot([-lim, lim], [-lim, lim], "k--", lw=.8)
        a.set_xlim(-lim, lim); a.set_ylim(-lim, lim)
        a.set_xlabel("Radar (m)"); a.set_ylabel(f"{m} (m)")
        a.set_title(f"{m}: r={metrik[m]['r']:.3f}, kemiringan={metrik[m]['Kemiringan_model_vs_radar']:.2f}")
        a.grid(alpha=.3)
        a.set_aspect("equal")
    fig.suptitle(f"{stasiun} - {label_bulan} {TAHUN}")
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)

def grafik_konstanta(d, stasiun, label_bulan, path):
    """Bar amplitudo & fase: radar vs model (konstanta signifikan)."""
    base = d.drop_duplicates("Konstanta").sort_values("Amp_Radar_cm", ascending=False)
    kons = base["Konstanta"].tolist()
    x = np.arange(len(kons))
    w = 0.27
    fig, ax = plt.subplots(2, 1, figsize=(max(9, 0.7 * len(kons) + 4), 8), sharex=True)
    ax[0].bar(x - w, base["Amp_Radar_cm"], w, label="Radar (harmonik)", color=WARNA["Radar"])
    ax[1].bar(x - w, base["Fase_Radar_deg"], w, label="Radar (harmonik)", color=WARNA["Radar"])
    for i, mdl in enumerate(MODELS):
        dm = d[d["Model"] == mdl].set_index("Konstanta").reindex(kons)
        ax[0].bar(x + i * w, dm["Amp_pyTMD_cm"], w, label=mdl, color=WARNA.get(mdl))
        ax[1].bar(x + i * w, dm["Fase_pyTMD_deg"], w, label=mdl, color=WARNA.get(mdl))
    ax[0].set_ylabel("Amplitudo (cm)")
    ax[1].set_ylabel("Fase Greenwich (derajat)")
    ax[1].set_ylim(0, 360)
    ax[1].set_xticks(x)
    ax[1].set_xticklabels(kons, rotation=45)
    ax[0].set_title(f"{stasiun} - {label_bulan} {TAHUN}: konstanta harmonik radar vs pyTMD")
    ax[0].legend()
    ax[0].grid(axis="y", alpha=.3)
    ax[1].grid(axis="y", alpha=.3)
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)

def grafik_rekap(df_ring, df_kons, path):
    """Rekap: deret waktu (RMSE, r, d) dan konstanta (RMSE amp, fase, vektor).
    Ukuran gambar menyesuaikan jumlah stasiun x bulan."""
    df_ring = df_ring.assign(L=df_ring["Stasiun"] + "\n" + df_ring["Bulan"])
    labels = df_ring["L"].drop_duplicates().tolist()
    x = np.arange(len(labels))
    w = 0.38
    panel = [(df_ring, "RMSE_cm", "Deret waktu: RMSE (cm)"),
             (df_ring, "r", "Deret waktu: korelasi r"),
             (df_ring, "Willmott_d", "Deret waktu: Willmott d")]
    if not df_kons.empty:
        dk = df_kons.assign(L=df_kons["Stasiun"] + "\n" + df_kons["Bulan"])
        panel += [(dk, "RMSE_Amp_cm", "Konstanta: RMSE amplitudo (cm)"),
                  (dk, "RMSE_Fase_deg", "Konstanta: RMSE fase (derajat)"),
                  (dk, "RMSE_Vektor_cm", "Konstanta: RMSE vektor (cm)")]
    ncol = 2
    nb = int(np.ceil(len(panel) / ncol))
    lebar = max(16.0, 0.6 * len(labels) * ncol + 3)
    fig, axs = plt.subplots(nb, ncol, figsize=(lebar, 4.6 * nb))
    axs = np.atleast_1d(axs).flatten()
    for a, (dat, kol, judul) in zip(axs, panel):
        for i, m in enumerate(MODELS):
            d = dat[dat["Model"] == m].set_index("L").reindex(labels)
            a.bar(x + (i - 0.5) * w, d[kol], w, label=m, color=WARNA[m])
        a.set_xticks(x); a.set_xticklabels(labels, fontsize=7)
        a.set_title(judul); a.grid(axis="y", alpha=.3)
    for a in axs[len(panel):]:
        a.axis("off")
    axs[0].legend()
    fig.suptitle(f"Radar vs pyTMD {TAHUN}")
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)

#PROSES UTAMA
konst_model = {}
for stn, (lon, lat) in STASIUN.items():
    for nama, nama_db in MODELS.items():
        try:
            konst_model[(stn, nama)] = ekstrak_pytmd(nama_db, lon, lat, DIR_MODEL)
            print(f"[OK] konstanta pyTMD {nama} @ {stn}: {len(konst_model[(stn, nama)])} konstanta")
        except Exception as e:
            print(f"[GAGAL] konstanta pyTMD {nama} @ {stn}: {e}")

ringkas_deret, ringkas_kons, detail_kons, harmonik_radar = [], [], [], []
semua_data = {}
sumber_harmonik_log = []

for stasiun, (lon, lat) in STASIUN.items():
    for bln, label in BULAN.items():
        print("\n" + "=" * 70)
        print(f"{stasiun} | {label} {TAHUN}")
        print("=" * 70)

        # TAHAP 1: baca, QC, per jam, UTC
        try:
            mentah = baca_radar(stasiun, bln)
        except Exception as e:
            print(f"  [GAGAL baca radar] {e}")
            continue
        if QC_AKTIF:
            mentah = bersihkan_radar(mentah)
        jam, n_kosong, n_interp = radar_per_jam(mentah)
        jam.index = jam.index - pd.Timedelta(hours=TZ_AKTIF)     # ke UTC (naive)
        # NaN yang tersisa dipertahankan sampai pembentukan anomali.
        if jam.notna().sum() < 48:
            print("  Data per jam terlalu sedikit, dilewati.")
            continue
        print(f"  Jam total: {len(jam)} | jam valid: {int(jam.notna().sum())} | "
              f"jam kosong awal: {n_kosong} | diinterpolasi: {n_interp}")

        #TAHAP 2: harmonik radar
        sumber_hr = HARMONIK_SUMBER
        try:
            if HARMONIK_SUMBER == "utide":
                hr = harmonik_utide(jam, lat)
                sumber_hr = "UTide"
            else:
                f = os.path.join(DIR_TTIDE, POLA_FILE_TTIDE.format(
                    stasiun=stasiun, bulan=KODE_BULAN_TTIDE[bln]))
                if os.path.exists(f):
                    hr = harmonik_file_ttide(f)
                    sumber_hr = "T_TIDE (file)"
                elif HARMONIK_CADANGAN_AKTIF:
                    print(f"  [!] File T_TIDE tidak ada: {f}")
                    print("      -> konstanta radar bulan ini dihitung ulang dengan UTide.")
                    hr = harmonik_utide(jam, lat)
                    sumber_hr = "UTide"
                else:
                    raise FileNotFoundError(f"File T_TIDE tidak ada: {f}")
            hr_sig = hr[hr["Signifikan"]]
            print(f"  Harmonik radar ({sumber_hr}): {len(hr)} konstanta, {len(hr_sig)} signifikan")
            sumber_harmonik_log.append((stasiun, label, sumber_hr))
            tmp = hr.drop(columns="key").copy()
            tmp.insert(0, "Bulan", label); tmp.insert(0, "Stasiun", stasiun)
            harmonik_radar.append(tmp)
        except Exception as e:
            print(f"  [GAGAL harmonik radar] {e}")
            hr_sig = pd.DataFrame()

        # TAHAP 4: perbandingan konstanta
        if not hr_sig.empty:
            for nama in MODELS:
                if (stasiun, nama) not in konst_model:
                    continue
                m = bandingkan_konstanta(hr_sig, konst_model[(stasiun, nama)])
                if m.empty:
                    continue
                for _, r in m.iterrows():
                    detail_kons.append({
                        "Stasiun": stasiun, "Bulan": label, "Model": nama,
                        "Konstanta": r["Konstanta"], "SNR": r["SNR"],
                        "Amp_Radar_cm": r["Amp_cm_tt"], "Amp_pyTMD_cm": r["Amp_cm_md"],
                        "dAmp_cm": r["dAmp_cm"], "dAmp_%": r["dAmp_%"],
                        "Fase_Radar_deg": r["Fase_tt"], "Fase_pyTMD_deg": r["Fase_md"],
                        "dFase_deg": r["dFase_deg"], "dVektor_cm": r["dVektor_cm"],
                        "Cocok": r["Cocok"]})
                r_amp = np.corrcoef(m["Amp_cm_tt"], m["Amp_cm_md"])[0, 1] if len(m) > 2 else np.nan
                ringkas_kons.append({
                    "Stasiun": stasiun, "Bulan": label, "Model": nama,
                    "N_signifikan_radar": len(hr_sig), "N_dibandingkan": len(m),
                    "N_cocok": int((m["Cocok"] == "Ya").sum()),
                    "RMSE_Amp_cm": rmse(m["dAmp_cm"]), "MAE_Amp_cm": m["dAmp_cm"].abs().mean(),
                    "Bias_Amp_cm": m["dAmp_cm"].mean(),
                    "RMSE_Fase_deg": rmse(m["dFase_deg"]), "MAE_Fase_deg": m["dFase_deg"].abs().mean(),
                    "RMSE_Vektor_cm": rmse(m["dVektor_cm"]), "r_Amplitudo": r_amp,
                    "Tidak_ada_di_model": ", ".join(sorted(set(hr_sig["Konstanta"]) - set(m["Konstanta"])))})
                print(f"  [Konstanta] {nama:8s} N={len(m)} | RMSE amp={rmse(m['dAmp_cm']):.2f} cm | "
                      f"RMSE fase={rmse(m['dFase_deg']):.1f} deg | RMSE vektor={rmse(m['dVektor_cm']):.2f} cm")

        # TAHAP 5: perbandingan deret waktu
        df = pd.DataFrame({"Radar_raw_m": jam})
        waktu = df.index.values.astype("datetime64[ns]")
        gagal = False
        for nama, nama_db in MODELS.items():
            try:
                df[f"{nama}_raw_m"] = prediksi_pytmd(nama_db, lon, lat, waktu)
            except Exception as e:
                print(f"  [GAGAL prediksi {nama}] {e}")
                gagal = True
        if gagal:
            continue

        # Buang hanya waktu ketika prediksi model tidak tersedia.
        # NaN radar tetap dipertahankan untuk diubah menjadi anomali 0.
        kolom_model = [f"{nama}_raw_m" for nama in MODELS]
        df = df.dropna(subset=kolom_model).copy()

        # Anomali radar: NaN diisi dengan rata-rata radar sehingga anomali = 0.
        msl_radar = df["Radar_raw_m"].mean()
        if NAN_JADI_NOL:
            df["Radar_raw_m"] = df["Radar_raw_m"].fillna(msl_radar)
        df["Radar_m"] = df["Radar_raw_m"] - msl_radar

        # Anomali masing-masing model dihitung dari rata-rata bulan tersebut.
        for nama in MODELS:
            kol = f"{nama}_raw_m"
            df[f"{nama}_m"] = df[kol] - df[kol].mean()

        metrik = {}
        for nama in MODELS:
            m = hitung_metrik(df["Radar_m"], df[f"{nama}_m"])
            lag, r_lag = lag_terbaik(df["Radar_m"], df[f"{nama}_m"])
            m["Lag_terbaik_jam"] = lag
            m["r_pada_lag_terbaik"] = r_lag
            metrik[nama] = m
            ringkas_deret.append({"Stasiun": stasiun, "Bulan": label, "Model": nama, **m,
                                  "Jam_diinterpolasi": n_interp})
            print(f"  [Deret]    {nama:8s} RMSE={m['RMSE_cm']:.2f} cm | MAE={m['MAE_cm']:.2f} cm | "
                  f"r={m['r']:.3f} | d={m['Willmott_d']:.3f} | kemiringan={m['Kemiringan_model_vs_radar']:.2f} | "
                  f"lag={lag} jam")
            if lag == lag and abs(lag) >= 1:
                print(f"    [!] Lag {lag} jam: periksa zona waktu radar.")

        semua_data[(stasiun, label)] = df
        grafik_deret(df, stasiun, label, metrik, os.path.join(DIR_OUT, f"deret_{stasiun}_{label}.png"))
        grafik_sebar(df, stasiun, label, metrik, os.path.join(DIR_OUT, f"sebar_{stasiun}_{label}.png"))
        dk = pd.DataFrame(detail_kons)
        if not dk.empty:
            dk = dk[(dk["Stasiun"] == stasiun) & (dk["Bulan"] == label)]
            if not dk.empty:
                grafik_konstanta(dk, stasiun, label,
                                 os.path.join(DIR_OUT, f"konstanta_{stasiun}_{label}.png"))

#TAHAP 6: SIMPAN
if not ringkas_deret and not ringkas_kons:
    raise SystemExit("\nTidak ada hasil. Cek pesan [GAGAL ...] di atas.")

df_deret = pd.DataFrame(ringkas_deret)
df_kons = pd.DataFrame(ringkas_kons)
df_detail = pd.DataFrame(detail_kons)
df_harm = pd.concat(harmonik_radar, ignore_index=True) if harmonik_radar else pd.DataFrame()
df_model = pd.concat(
    [d.assign(Stasiun=s, Model=m) for (s, m), d in konst_model.items()],
    ignore_index=True) if konst_model else pd.DataFrame()

#TAHAP 6: ANALISIS SENSITIVITAS AMBANG KECOCOKAN KONSTANTA
# Ketiga skenario memakai struktur aturan yang sama:
# (|dAmp_cm| <= batas cm ATAU |dAmp_%| <= batas %) DAN |dFase_deg| <= batas fase.
SKENARIO_AMBANG = {
    "Ketat":   (1.0, 10.0, 10.0),
    "Dasar":   (TOL_AMP_CM, TOL_AMP_PCT, TOL_FASE_DEG),
    "Longgar": (3.0, 30.0, 30.0),
}


def cocok_skenario_sensitivitas(data, tol_cm, tol_pct, tol_fase):
    """Menghasilkan True jika konstanta memenuhi ambang skenario."""
    return (((data["dAmp_cm"].abs() <= tol_cm) |
             (data["dAmp_%"].abs() <= tol_pct)) &
            (data["dFase_deg"].abs() <= tol_fase))


def hitung_sensitivitas(df_detail):
    """Ringkasan sensitivitas per stasiun-bulan-model dan agregat per model."""
    if df_detail.empty:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    bagian = []
    for nama_skenario, (tol_cm, tol_pct, tol_fase) in SKENARIO_AMBANG.items():
        tmp = df_detail.copy()
        tmp["Cocok_skenario"] = cocok_skenario_sensitivitas(
            tmp, tol_cm, tol_pct, tol_fase)
        g = (tmp.groupby(["Stasiun", "Bulan", "Model"])["Cocok_skenario"]
                .agg(N_dibandingkan="size", N_cocok="sum").reset_index())
        g["Persen_cocok"] = np.where(
            g["N_dibandingkan"] > 0,
            100.0 * g["N_cocok"] / g["N_dibandingkan"], np.nan)
        g.insert(0, "Skenario", nama_skenario)
        g["Toleransi_amp_cm"] = tol_cm
        g["Toleransi_amp_persen"] = tol_pct
        g["Toleransi_fase_derajat"] = tol_fase
        bagian.append(g)

    df_sens = pd.concat(bagian, ignore_index=True)

    # Agregat seluruh stasiun dan bulan, tetapi tetap dipisahkan menurut model.
    agregat = (df_sens.groupby(["Model", "Skenario"])
               [["N_dibandingkan", "N_cocok"]].sum().reset_index())
    agregat["Persen_cocok"] = np.where(
        agregat["N_dibandingkan"] > 0,
        100.0 * agregat["N_cocok"] / agregat["N_dibandingkan"], np.nan)

    pivot = agregat.pivot(index="Model", columns="Skenario", values="Persen_cocok")
    pivot = pivot.reindex(columns=list(SKENARIO_AMBANG.keys()))
    pivot = pivot.reset_index()

    # Model dengan persentase konstanta cocok paling tinggi untuk setiap skenario.
    p = agregat.pivot(index="Skenario", columns="Model", values="Persen_cocok")
    p = p.reindex(index=list(SKENARIO_AMBANG.keys()))
    terbaik = []
    for skenario in p.index:
        baris = p.loc[skenario].dropna()
        terbaik.append({
            "Skenario": skenario,
            "Model_terbaik": baris.idxmax() if not baris.empty else "Tidak dapat ditentukan",
            "Persen_cocok_tertinggi": baris.max() if not baris.empty else np.nan,
        })
    df_terbaik = pd.DataFrame(terbaik)
    return df_sens, pivot, df_terbaik


df_sens, tabel_sens, df_model_terbaik = hitung_sensitivitas(df_detail)
if not df_sens.empty:
    print("\n=== ANALISIS SENSITIVITAS AMBANG KONSTANTA ===")
    print("Ambang (amplitudo cm, amplitudo %, fase derajat):", SKENARIO_AMBANG)
    print("\nPersentase konstanta cocok per model:")
    print(tabel_sens.round(2).to_string(index=False))
    print("\nModel terbaik pada setiap skenario:")
    print(df_model_terbaik.round(2).to_string(index=False))
    model_terpilih = df_model_terbaik["Model_terbaik"].dropna()
    model_terpilih = model_terpilih[model_terpilih != "Tidak dapat ditentukan"]
    if not model_terpilih.empty and model_terpilih.nunique() == 1:
        print("-> Model dengan persentase cocok tertinggi KONSISTEN pada semua skenario.")
    elif not model_terpilih.empty:
        print("-> Model dengan persentase cocok tertinggi BERUBAH antar skenario; interpretasi perlu mempertimbangkan ambang.")
else:
    print("\n[!] Sensitivitas tidak dihitung karena tidak ada detail konstanta yang dapat dibandingkan.")

print("\n=== RINGKASAN DERET WAKTU ===")
print(df_deret.round(3).to_string(index=False))
if not df_kons.empty:
    print("\n=== RINGKASAN KONSTANTA ===")
    print(df_kons.round(3).to_string(index=False))
if sumber_harmonik_log:
    print("\n=== SUMBER HARMONIK RADAR PER BULAN ===")
    for s_, b_, m_ in sumber_harmonik_log:
        print(f"  {s_:9s} {b_:9s} {m_}")
    if len({m_ for _, _, m_ in sumber_harmonik_log}) > 1:
        print("[!] Sumber harmonik radar tidak seragam antar bulan (T_TIDE vs UTide). "
              "Bandingkan konstanta antar bulan dengan hati-hati.")

grafik_rekap(df_deret, df_kons, os.path.join(DIR_OUT, "rekap_gabungan.png"))

f_xlsx = os.path.join(DIR_OUT, f"analisis_pasut_gabungan_{TAHUN}.xlsx")
with pd.ExcelWriter(f_xlsx, engine="openpyxl") as xw:
    df_deret.round(4).to_excel(xw, sheet_name="Ringkasan_DeretWaktu", index=False)
    if not df_deret.empty:
        df_deret.groupby("Model")[["RMSE_cm", "MAE_cm", "r", "Willmott_d",
                                   "Kemiringan_model_vs_radar"]].mean().round(4)\
            .to_excel(xw, sheet_name="Rata2_per_model")
        df_deret.groupby(["Stasiun", "Model"])[["RMSE_cm", "MAE_cm", "r", "Willmott_d",
                                                "Kemiringan_model_vs_radar"]].mean().round(4)\
            .to_excel(xw, sheet_name="Rata2_per_stasiun_model")
    if not df_kons.empty:
        df_kons.round(4).to_excel(xw, sheet_name="Ringkasan_Konstanta", index=False)
        df_detail.round(4).to_excel(xw, sheet_name="Detail_Konstanta", index=False)
        df_detail[df_detail["Konstanta"].isin(KONSTANTA_UTAMA)].round(4)\
            .to_excel(xw, sheet_name="Konstanta_Utama", index=False)
    if sumber_harmonik_log:
        pd.DataFrame(sumber_harmonik_log, columns=["Stasiun", "Bulan", "Sumber_harmonik"]) \
            .to_excel(xw, sheet_name="Sumber_Harmonik", index=False)
    if not df_harm.empty:
        df_harm.round(4).to_excel(xw, sheet_name="Harmonik_Radar", index=False)
    if not df_model.empty:
        df_model.round(4).to_excel(xw, sheet_name="Konstanta_pyTMD", index=False)
    for (stn, lab), d in semua_data.items():
        d.reset_index(names="waktu_utc").round(5).to_excel(
            xw, sheet_name=f"{stn}_{lab}"[:31], index=False)
    if not df_sens.empty:
        df_sens.round(4).to_excel(xw, sheet_name="Sensitivitas_Detail", index=False)
        tabel_sens.round(4).to_excel(xw, sheet_name="Sensitivitas_Model", index=False)
        df_model_terbaik.round(4).to_excel(xw, sheet_name="Model_Terbaik_Sens", index=False)
    pd.DataFrame({
        "Parameter": ["Tahun", "Bulan dianalisis", "Zona waktu radar default (jam dari UTC)",
                      "Metode interpolasi deret waktu",
                      "Batas interpolasi jam kosong", "Sumber harmonik radar", "SNR_MIN",
                      "TOL_AMP_CM", "TOL_AMP_PCT", "TOL_FASE_DEG", "Skenario_sensitivitas", "Model"],
        "Nilai": [TAHUN, ", ".join(BULAN.values()), TZ_RADAR_JAM, METODE_INTERPOLASI,
                  INTERP_LIMIT_JAM, HARMONIK_SUMBER,
                  SNR_MIN, TOL_AMP_CM, TOL_AMP_PCT, TOL_FASE_DEG, str(SKENARIO_AMBANG), ", ".join(MODELS.values())],
    }).to_excel(xw, sheet_name="Parameter", index=False)

print(f"\nExcel tersimpan : {f_xlsx}")
print(f"Grafik          : {DIR_OUT}")
