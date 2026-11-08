"""
Analisis harmonik pasut (t_tide) - data radar Panggang (Gesing) & Baron.
NaN yang tersisa (setelah interpolasi gap pendek) diubah menjadi 0.
"""
import os
import warnings
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from ttide.t_tide import t_tide

warnings.filterwarnings("ignore")
np.random.seed(42)
def _lokasi_skrip():
    try:
        return Path(__file__).resolve().parent
    except NameError:  # __file__ tidak ada (mis. run cell / interactive)
        return Path.cwd().resolve()


BASE_DIR = _lokasi_skrip()
OLAH_DIR = BASE_DIR / "OLAH"
HASIL_DIR = BASE_DIR / "HASIL_NAN0"
FILE_RADAR_PATH = OLAH_DIR / "dataPB.xlsx"

# 1. PENGATURAN
FILE_XLSX = str(FILE_RADAR_PATH)      
OUT_DIR   = str(HASIL_DIR)            

# Panggang = Gesing Beach (lon 110.468404), Baron = Baron Beach (lon 110.54849)
LAT_PANGGANG = -8.107678
LAT_BARON    = -8.131006
DAFTAR = [
    ("panggang_Jan26",    "Panggang", "Jan",   LAT_PANGGANG),
    ("panggang_April26",  "Panggang", "April", LAT_PANGGANG),
    ("panggang_Agust26",  "Panggang", "Agust", LAT_PANGGANG),
    ("panggang_Feb26",    "Panggang", "Feb",   LAT_PANGGANG),
    ("panggang_Maret26",  "Panggang", "Maret", LAT_PANGGANG),
    ("panggang_Mei26",  "Panggang", "Mei", LAT_PANGGANG),
    ("panggang_Juni26",    "Panggang", "Juni",   LAT_PANGGANG),
    ("panggang_Juli26",  "Panggang", "Juli", LAT_PANGGANG),
    ("baron_Jan26",       "Baron",    "Jan",   LAT_BARON),
    ("baron_April26",     "Baron",    "April", LAT_BARON),
    ("baron_Agust26",     "Baron",    "Agust", LAT_BARON),
    ("baron_Feb26",       "Baron",    "Feb",   LAT_BARON),
    ("baron_Maret26",     "Baron",    "Maret", LAT_BARON),
    ("baron_Mei26",     "Baron",    "Mei", LAT_BARON),
    ("baron_Juni26",       "Baron",    "Juni",   LAT_BARON),
    ("baron_Juli26",     "Baron",    "Juli", LAT_BARON),
]

# Parameter QC radar disamakan dengan analisisS.py
QC_JENDELA_MENIT   = 31
QC_N_SIGMA         = 4.0
QC_MIN_AMBANG_M    = 0.5
QC_RUN_DATAR_MENIT = 30
MIN_SAMPEL_PER_JAM = 20
INTERP_METODE      = "time"
INTERP_MAX_JAM     = 6
SNR_MIN            = 1.0
KONSTA_UTAMA       = ["S2", "O1", "M2", "K1"]
RESIDU_SUMBU_KANAN = False

# True  = NaN yang tersisa dijadikan 0 pada anomali (0 = setara muka air rata-rata)
# False = NaN dibiarkan seperti semula
NAN_JADI_NOL       = True

KONSTA_Z0          = ["M2", "S2", "K2", "K1", "O1", "P1"]
KONSTA_MHWL        = ["M2", "K1", "O1"]
ELEVASI_SIGNIFIKAN_SAJA = False
ACUAN_MHWL_MLWL    = "S0"

if not os.path.isfile(FILE_XLSX):
    raise FileNotFoundError(
        "Berkas data radar tidak ditemukan:\n  " + str(FILE_XLSX) + "\n"
        "Letakkan 'dataPB.xlsx' di dalam folder 'OLAH' yang berada satu folder dengan skrip ini."
    )
print("Folder skrip :", BASE_DIR)
print("Data radar   :", FILE_XLSX)
os.makedirs(OUT_DIR, exist_ok=True)

# 2. FUNGSI BANTU
def baca_sheet(path, sheet):
    """Baca sheet: baris 1 = judul, baris 2 = header, data mulai baris 3."""
    df = pd.read_excel(path, sheet_name=sheet, header=1)
    df = df.iloc[:, :3]
    df.columns = ["waktu", "bat", "rad"]
    df["waktu"] = pd.to_datetime(df["waktu"], errors="coerce")
    df["rad"] = pd.to_numeric(df["rad"], errors="coerce")
    df = df.dropna(subset=["waktu"]).sort_values("waktu")
    df = df.drop_duplicates("waktu")
    return df

def buang_spike(df):
    """QC per menit: buang flatline >=30 menit dan spike berbasis median/MAD.
    Parameter dan algoritma disamakan dengan bersihkan_radar() pada analisisS.py.
    """
    s = df.set_index("waktu")["rad"].astype(float).copy()

    # Deteksi data macet/flatline
    sama = s.diff().eq(0)
    grup = (sama != sama.shift()).cumsum()
    panjang = sama.groupby(grup).transform("sum")
    macet = sama & (panjang >= QC_RUN_DATAR_MENIT - 1)
    macet = macet | (macet.shift(-1, fill_value=False) & ~macet)
    n_macet = int(macet.sum())
    s = s[~macet]

    # Deteksi lonjakan dengan rolling median dan robust sigma (MAD)
    med = s.rolling(QC_JENDELA_MENIT, center=True, min_periods=5).median()
    residu = s - med
    sigma = 1.4826 * np.nanmedian(np.abs(residu - np.nanmedian(residu)))
    ambang = max(QC_MIN_AMBANG_M, QC_N_SIGMA * sigma)
    spike = residu.abs() > ambang
    n_spike = int(spike.sum())
    s = s[~spike]

    print(f"  QC radar: flatline dibuang={n_macet}; spike dibuang={n_spike}; "
          f"ambang spike={ambang:.3f} m")
    return s.rename("rad").reset_index(), n_macet + n_spike


def ke_per_jam(df):
    """Rata-rata per jam pada interval [hh:00, hh+1:00), label di hh:30.
    Sama dengan radar_per_jam() pada analisisS.py.
    """
    s = df.set_index("waktu")["rad"]
    grup = s.resample("1h", closed="left", label="left")
    rata = grup.mean()
    n = grup.count()
    rata[n < MIN_SAMPEL_PER_JAM] = np.nan
    rata.index = rata.index + pd.Timedelta(minutes=30)
    penuh = pd.date_range(rata.index[0], rata.index[-1], freq="1h")
    return rata.reindex(penuh)


def isi_gap(h):
    """Interpolasi berbasis waktu hanya untuk gap utuh <= 6 jam.
    Gap lebih panjang dibiarkan NaN agar penanganannya konsisten di kedua skrip.
    """
    kosong = h.isna().values
    terinterpolasi = h.interpolate(method=INTERP_METODE, limit_area="inside")
    boleh = np.zeros(len(h), dtype=bool)
    i = 0
    while i < len(h):
        if kosong[i]:
            j = i
            while j < len(h) and kosong[j]:
                j += 1
            if (j - i) <= INTERP_MAX_JAM:
                boleh[i:j] = True
            i = j
        else:
            i += 1
    hasil = h.copy()
    hasil[boleh] = terinterpolasi[boleh]
    interp = pd.Series(boleh & hasil.notna().values, index=h.index)
    return hasil, interp

def jalankan_ttide(anomali, stime, lintang):
    """Panggil t_tide dan seragamkan hasilnya menjadi dict:
       nameu, fu, tidecon (amp, amp_err, fase, fase_err), snr, xout.(tuple, seperti artikel)(dict)."""
    lat = np.array(lintang)
    try:
        hasil = t_tide(anomali, dt=1, stime=stime, lat=lat,
                       out_style=None, synth=SNR_MIN)
    except TypeError:
        try:
            hasil = t_tide(anomali, dt=1, stime=stime, lat=lat)
        except TypeError:
            hasil = t_tide(anomali, dt=1, lat=lat)

    if isinstance(hasil, dict):
        out = dict(hasil)
    else:                                        # tuple: nameu, fu, tideconout, xout
        nameu, fu, tidecon, xout = hasil[:4]
        out = {"nameu": nameu, "fu": fu, "tidecon": tidecon, "xout": xout}

    tc = np.asarray(out["tidecon"], dtype=float)
    if "snr" not in out or out["snr"] is None:
        # definisi t_tide: SNR = (amp / amp_err)^2
        with np.errstate(divide="ignore", invalid="ignore"):
            out["snr"] = (tc[:, 0] / tc[:, 1]) ** 2
    return out

def analisis(h, lintang):
    """Jalankan t_tide pada deret per jam h (pandas Series, index jam-an, UTC)."""
    np.random.seed(42)
    # anomali (rata-rata dibuang; mean() mengabaikan NaN), array NumPy
    anomali = (h - h.mean()).values.astype(float)
    if NAN_JADI_NOL:
        # NaN yang tersisa -> 0 (pada anomali, 0 = muka air rata-rata)
        anomali = np.nan_to_num(anomali, nan=0.0)
    out = jalankan_ttide(anomali, h.index[0].to_pydatetime(), lintang)

    nama = [n.decode().strip() if isinstance(n, bytes) else str(n).strip()
            for n in np.asarray(out["nameu"]).ravel()]
    tc = np.asarray(out["tidecon"], dtype=float)   # amp, amp_err, fase, fase_err
    fu = np.asarray(out["fu"], dtype=float).ravel()
    tabel = pd.DataFrame({
        "Konstanta": nama,
        "Frekuensi (cph)": fu,
        "Periode (jam)": 1.0 / fu,
        "Amplitudo (m)": tc[:, 0],
        "Amplitudo (cm)": tc[:, 0] * 100,
        "Error Amp (m)": tc[:, 1],
        "Error Amp (cm)": tc[:, 1] * 100,
        "Fase (deg)": tc[:, 2],
        "Error Fase (deg)": tc[:, 3],
        "SNR": np.asarray(out["snr"], dtype=float).ravel(),
    })
    tabel["Signifikan (SNR>1)"] = np.where(tabel["SNR"] > SNR_MIN, "Ya", "Tidak")
    tabel = tabel.sort_values("Frekuensi (cph)").reset_index(drop=True)
    tabel.insert(0, "No", np.arange(1, len(tabel) + 1))

    # xout (prediksi t_tide) tidak memuat muka air rata-rata -> tambahkan dari kuadrat terkecil
    pasut = np.asarray(out["xout"]).squeeze()      # (n,1) -> (n,)
    msl = float(np.nanmean(h.values - pasut))
    pred = pasut + msl
    return out, tabel, pred, msl

def formzahl(tabel):
    amp = dict(zip(tabel["Konstanta"], tabel["Amplitudo (cm)"]))
    if all(k in amp for k in ["K1", "O1", "M2", "S2"]):
        F = (amp["K1"] + amp["O1"]) / (amp["M2"] + amp["S2"])
        if F < 0.25:
            tipe = "harian ganda (semidiurnal)"
        elif F < 1.5:
            tipe = "campuran, condong harian ganda"
        elif F < 3.0:
            tipe = "campuran, condong harian tunggal"
        else:
            tipe = "harian tunggal (diurnal)"
        return F, tipe
    return np.nan, "-"


def elevasi_penting(tabel, msl):
    """Z0, S0/MSL, HHWL, MHWL, LLWL, MLWL (meter) dari konstanta harmonik.
    S0   = MSL (muka air rata-rata hasil fit, terhadap datum sensor radar)
    Z0   = jumlah amplitudo konstanta di KONSTA_Z0
    HHWL = S0 + Z0          LLWL = S0 - Z0
    MHWL = acuan + jumlah amplitudo KONSTA_MHWL
    MLWL = acuan - jumlah amplitudo KONSTA_MHWL
   """
    t = tabel
    if ELEVASI_SIGNIFIKAN_SAJA:
        t = t[t["SNR"] > SNR_MIN]
    amp = dict(zip(t["Konstanta"], t["Amplitudo (m)"]))
    z0 = float(sum(amp.get(k, 0.0) for k in KONSTA_Z0))
    s3 = float(sum(amp.get(k, 0.0) for k in KONSTA_MHWL))
    acuan = msl if ACUAN_MHWL_MLWL == "S0" else z0
    return {"Z0": z0, "S0/MSL": msl, "HHWL": msl + z0, "MHWL": acuan + s3,
            "LLWL": msl - z0, "MLWL": acuan - s3}


def rangkuman(label, h, tabel, msl, n_interp, n_spike, n_outlier, lintang):
    sig = tabel["Signifikan (SNR>1)"] == "Ya"
    baris = {
        "Stasiun - bulan": label,
        "Lintang (deg)": lintang,
        "Periode data (UTC)": f"{h.index[0]:%Y-%m-%d %H:%M} s/d {h.index[-1]:%Y-%m-%d %H:%M}",
        "Titik spike dibuang (data 1 menit)": n_spike,
        "Jam outlier residu dibuang": n_outlier,
        "Jumlah jam total": len(h),
        "Jumlah jam data asli (bukan interpolasi)": int(h.notna().sum() - n_interp),
        "Jumlah jam hasil interpolasi": int(n_interp),
        "Jumlah jam masih kosong (NaN -> 0 di t_tide)" if NAN_JADI_NOL
        else "Jumlah jam masih kosong (NaN)": int(h.isna().sum()),
        "Muka air rata-rata (m)": round(msl, 4),
        "Jumlah konstanta total": len(tabel),
        "Konstanta signifikan (SNR>1)": int(sig.sum()),
        "Konstanta tidak signifikan": int((~sig).sum()),
        "Daftar signifikan": ", ".join(tabel.loc[sig, "Konstanta"]),
        "Daftar tidak signifikan": ", ".join(tabel.loc[~sig, "Konstanta"]),
    }
    amp = dict(zip(tabel["Konstanta"], tabel["Amplitudo (cm)"]))
    snr = dict(zip(tabel["Konstanta"], tabel["SNR"]))
    for k in KONSTA_UTAMA:
        if k in amp:
            status = "signifikan" if snr[k] > SNR_MIN else "TIDAK signifikan"
            baris[f"{k}: amplitudo (cm) / SNR"] = f"{amp[k]:.2f} / {snr[k]:.1f} ({status})"
        else:
            baris[f"{k}"] = "tidak dianalisis (record kurang panjang)"
    F, tipe = formzahl(tabel)
    if not np.isnan(F):
        baris["Bilangan Formzahl F = (K1+O1)/(M2+S2)"] = f"{F:.2f} -> {tipe}"
    ev = elevasi_penting(tabel, msl)
    for k, v in ev.items():
        baris[f"{k} (m)"] = round(v, 4)
    return pd.DataFrame({"Parameter": list(baris.keys()),
                         "Nilai": list(baris.values())})


def baris_rekap(stasiun, bulan, h, tabel, msl, n_interp, n_outlier):
    sig = tabel["Signifikan (SNR>1)"] == "Ya"
    d = {"Stasiun": stasiun, "Bulan": bulan,
         "Jam total": len(h), "Jam interpolasi": int(n_interp),
         "Jam outlier dibuang": int(n_outlier),
         "Jam NaN": int(h.isna().sum()), "MSL (m)": round(msl, 4),
         "Konstanta total": len(tabel), "Signifikan": int(sig.sum()),
         "Tidak signifikan": int((~sig).sum())}
    t = tabel.set_index("Konstanta")
    for k in KONSTA_UTAMA:
        if k in t.index:
            d[f"{k} amp (cm)"] = round(t.loc[k, "Amplitudo (cm)"], 2)
            d[f"{k} fase (deg)"] = round(t.loc[k, "Fase (deg)"], 1)
            d[f"{k} SNR"] = round(t.loc[k, "SNR"], 1)
    F, tipe = formzahl(tabel)
    d["Formzahl"] = round(F, 2)
    d["Tipe pasut"] = tipe
    return d


def tabel_amp_signifikan(tabels):
    """Baris = konstanta signifikan di salah satu data set (urut frekuensi),
    kolom = data set (amplitudo cm; 0 bila tidak signifikan)."""
    frek = {}
    for t in tabels.values():
        for _, r in t.iterrows():
            if r["SNR"] > SNR_MIN:
                frek[r["Konstanta"]] = r["Frekuensi (cph)"]
    nama = sorted(frek, key=lambda k: frek[k])
    data = {}
    for lab, t in tabels.items():
        d = {r["Konstanta"]: (r["Amplitudo (cm)"] if r["SNR"] > SNR_MIN else 0.0)
             for _, r in t.iterrows()}
        data[lab] = [d.get(k, 0.0) for k in nama]
    return pd.DataFrame(data, index=nama)


# 3. GRAFIK
def grafik_deret(label, h, pred, resid, interp):
    fig, ax = plt.subplots(2, 1, figsize=(13, 7.5), sharex=True,
                           gridspec_kw={"height_ratios": [2.2, 1]})
    ax[0].plot(h.index, h.values, color="0.55", lw=1.0, label="Data asli (rata-rata per jam)")
    ax[0].plot(h.index, pred, color="tab:red", lw=1.3, label="Prediksi pasut (SNR > 1)")
    if interp.any():
        ax[0].plot(h.index[interp.values], h.values[interp.values], "o",
                   color="tab:orange", ms=3, label="Jam hasil interpolasi")
    ax[0].set_ylabel("Elevasi muka air (m)")
    ax[0].set_title(f"{label} - data asli vs prediksi pasut")
    ax[0].legend(loc="upper right", ncol=3)
    ax[0].grid(alpha=0.3)

    ax[1].plot(h.index, resid, color="tab:blue", lw=0.9)
    ax[1].axhline(0, color="k", lw=0.6)
    ax[1].set_ylabel("Residu (m)")
    ax[1].set_xlabel("Waktu (UTC)")
    ax[1].set_title("Elevasi residu = data asli - prediksi", fontsize=10)
    ax[1].grid(alpha=0.3)
    fig.autofmt_xdate()
    fig.tight_layout()
    f = os.path.join(OUT_DIR, f"{label.replace(' ', '_')}_prediksi_residu.png")
    fig.savefig(f, dpi=300)
    return f


def grafik_gabungan(label, h, pred, resid, interp):
    """Satu panel: data asli, prediksi pasut, dan residu sebagai grafik garis."""
    fig, ax = plt.subplots(figsize=(13, 5.8))
    l1, = ax.plot(h.index, h.values, color="0.55", lw=1.0,
                  label="Data asli (rata-rata per jam)")
    l2, = ax.plot(h.index, pred, color="tab:red", lw=1.3,
                  label="Prediksi pasut (SNR > 1)")
    handles = [l1, l2]
    if interp.any():
        l4, = ax.plot(h.index[interp.values], h.values[interp.values], "o",
                      color="tab:orange", ms=3, label="Jam hasil interpolasi")
        handles.append(l4)

    if RESIDU_SUMBU_KANAN:
        ax2 = ax.twinx()
        l3, = ax2.plot(h.index, resid, color="tab:blue", lw=0.9,
                       label="Residu (data - prediksi), sumbu kanan")
        ax2.set_ylabel("Residu (m)", color="tab:blue")
        ax2.tick_params(axis="y", colors="tab:blue")
        lim = np.nanmax(np.abs(resid)) * 1.15
        ax2.set_ylim(-lim, lim)
    else:
        l3, = ax.plot(h.index, resid, color="tab:blue", lw=0.9,
                      label="Residu (data - prediksi)")
        ax.axhline(0, color="k", lw=0.6)
    handles.insert(2, l3)

    ax.set_ylabel("Elevasi muka air / residu (m)" if not RESIDU_SUMBU_KANAN
                  else "Elevasi muka air (m)")
    ax.set_xlabel("Waktu (UTC)")
    ax.set_title(f"{label} - data asli, prediksi pasut, dan residu")
    ax.grid(alpha=0.3)
    ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.27),
              ncol=len(handles), frameon=False)
    fig.autofmt_xdate()
    fig.tight_layout()
    f = os.path.join(OUT_DIR, f"{label.replace(' ', '_')}_gabungan.png")
    fig.savefig(f, dpi=300, bbox_inches="tight")
    return f


def grafik_batang(label, tabel):
    x = np.arange(len(tabel))
    warna = np.where(tabel["SNR"] > SNR_MIN, "tab:blue", "lightgrey")
    fig, ax = plt.subplots(2, 1, figsize=(13, 8), sharex=True)

    ax[0].bar(x, tabel["Amplitudo (cm)"], yerr=tabel["Error Amp (cm)"],
              color=warna, edgecolor="k", lw=0.4, capsize=2)
    ax[0].set_ylabel("Amplitudo (cm)")
    ax[0].set_title(f"{label} - amplitudo konstanta harmonik "
                    f"(biru: SNR>1, abu-abu: tidak signifikan)")
    ax[0].grid(axis="y", alpha=0.3)

    ax[1].bar(x, tabel["Fase (deg)"], yerr=tabel["Error Fase (deg)"],
              color=warna, edgecolor="k", lw=0.4, capsize=2)
    ax[1].set_ylabel("Fase (derajat)")
    ax[1].set_ylim(0, 360)
    ax[1].set_title("Fase konstanta harmonik (Greenwich, UTC)", fontsize=10)
    ax[1].grid(axis="y", alpha=0.3)
    ax[1].set_xticks(x)
    ax[1].set_xticklabels(tabel["Konstanta"], rotation=60, ha="right")
    fig.tight_layout()
    f = os.path.join(OUT_DIR, f"{label.replace(' ', '_')}_amplitudo_fase.png")
    fig.savefig(f, dpi=300)
    return f


def grafik_fase(label, tabel):
    """Grafik batang fase saja (semua konstanta)."""
    x = np.arange(len(tabel))
    warna = np.where(tabel["SNR"] > SNR_MIN, "tab:green", "lightgrey")
    fig, ax = plt.subplots(figsize=(13, 5.5))
    ax.bar(x, tabel["Fase (deg)"], yerr=tabel["Error Fase (deg)"],
           color=warna, edgecolor="k", lw=0.4, capsize=2)
    ax.set_ylim(0, 360)
    ax.set_yticks(range(0, 361, 60))
    ax.set_ylabel("Fase (derajat, Greenwich/UTC)")
    ax.set_title(f"{label} - fase konstanta harmonik "
                 f"(hijau: SNR>1, abu-abu: tidak signifikan)")
    ax.set_xticks(x)
    ax.set_xticklabels(tabel["Konstanta"], rotation=60, ha="right")
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    f = os.path.join(OUT_DIR, f"{label.replace(' ', '_')}_fase.png")
    fig.savefig(f, dpi=300)
    return f


def grafik_rekap_fase(rekap):
    """Batang berkelompok: fase S2, O1, M2, K1 untuk semua stasiun-bulan."""
    lab = (rekap["Stasiun"] + " " + rekap["Bulan"]).tolist()
    x = np.arange(len(KONSTA_UTAMA))
    w = 0.8 / max(len(lab), 1)
    fig, ax = plt.subplots(figsize=(11, 5.5))
    for i, (_, r) in enumerate(rekap.iterrows()):
        v = [r.get(f"{k} fase (deg)", np.nan) for k in KONSTA_UTAMA]
        ax.bar(x + (i - (len(lab) - 1) / 2) * w, v, w, label=lab[i], edgecolor="k", lw=0.4)
    ax.set_xticks(x)
    ax.set_xticklabels(KONSTA_UTAMA)
    ax.set_ylim(0, 360)
    ax.set_yticks(range(0, 361, 60))
    ax.set_ylabel("Fase (derajat)")
    ax.set_title("Perbandingan fase konstanta utama antar stasiun dan bulan")
    ax.grid(axis="y", alpha=0.3)
    ax.legend(ncol=2)
    fig.tight_layout()
    f = os.path.join(OUT_DIR, "rekap_fase_utama.png")
    fig.savefig(f, dpi=300)
    return f


def grafik_rekap(rekap):
    """Batang berkelompok: amplitudo S2, O1, M2, K1 untuk semua stasiun-bulan."""
    lab = (rekap["Stasiun"] + " " + rekap["Bulan"]).tolist()
    x = np.arange(len(KONSTA_UTAMA))
    w = 0.8 / max(len(lab), 1)
    fig, ax = plt.subplots(figsize=(11, 5.5))
    for i, (_, r) in enumerate(rekap.iterrows()):
        v = [r.get(f"{k} amp (cm)", np.nan) for k in KONSTA_UTAMA]
        ax.bar(x + (i - (len(lab) - 1) / 2) * w, v, w, label=lab[i], edgecolor="k", lw=0.4)
    ax.set_xticks(x)
    ax.set_xticklabels(KONSTA_UTAMA)
    ax.set_ylabel("Amplitudo (cm)")
    ax.set_title("Perbandingan amplitudo konstanta utama antar stasiun dan bulan")
    ax.grid(axis="y", alpha=0.3)
    ax.legend(ncol=2)
    fig.tight_layout()
    f = os.path.join(OUT_DIR, "rekap_amplitudo_utama.png")
    fig.savefig(f, dpi=300)
    return f


def grafik_konstanta_signifikan(df_amp):
    """Batang berkelompok: amplitudo konstanta signifikan, semua data set."""
    n = df_amp.shape[1]
    x = np.arange(len(df_amp))
    w = 0.8 / max(n, 1)
    fig, ax = plt.subplots(figsize=(max(12, 0.7 * len(df_amp) + 4), 6))
    for i, lab in enumerate(df_amp.columns):
        ax.bar(x + (i - (n - 1) / 2) * w, df_amp[lab].values, w, label=lab,
               edgecolor="k", lw=0.3)
    ax.set_xticks(x)
    ax.set_xticklabels(["*" + k for k in df_amp.index], rotation=60, ha="right")
    ax.set_ylabel("Amplitudo (cm)")
    ax.set_xlabel("Konstanta signifikan (SNR > 1)")
    ax.set_title(f"Konstanta Signifikan dari ke {n} Data Set")
    ax.grid(axis="y", alpha=0.3)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.28), ncol=min(n, 6), frameon=True)
    fig.tight_layout()
    f = os.path.join(OUT_DIR, "rekap_konstanta_signifikan.png")
    fig.savefig(f, dpi=300, bbox_inches="tight")
    return f


def tabel_ke_gambar(df, judul, nama_file):
    """Simpan DataFrame sebagai gambar tabel."""
    fig, ax = plt.subplots(figsize=(10, 0.55 * (len(df) + 2)))
    ax.axis("off")
    ax.set_title(judul, loc="left", fontsize=11)
    isi = df.round(4).reset_index().values.tolist()
    kolom = [df.index.name or "Data set"] + list(df.columns)
    tb = ax.table(cellText=isi, colLabels=kolom, loc="center", cellLoc="center")
    tb.auto_set_font_size(False)
    tb.set_fontsize(10)
    tb.scale(1, 1.5)
    fig.tight_layout()
    f = os.path.join(OUT_DIR, nama_file)
    fig.savefig(f, dpi=300, bbox_inches="tight")
    return f


# 4. PROGRAM UTAMA
rekap_baris = []
elev_baris = {}
tabel_semua = {}

for sheet, stasiun, bulan, lintang in DAFTAR:
    label = f"{stasiun} {bulan}"
    print("=" * 70)
    print(f"{label}  (sheet: {sheet})")

    raw = baca_sheet(FILE_XLSX, sheet)

    raw, n_spike = buang_spike(raw)
    h_asli = ke_per_jam(raw)
    h, interp = isi_gap(h_asli)
    n_outlier = 0  # QC residual harmonik dinonaktifkan agar QC kedua skrip identik
    print(f"  data mentah : {len(raw)} baris (flatline/spike dibuang: {n_spike})  ->  per jam : {len(h)} jam")
    print(f"  jam kosong  : {int(h_asli.isna().sum())}  |  diinterpolasi : "
          f"{int(interp.sum())}  |  masih NaN : {int(h.isna().sum())}")
    if NAN_JADI_NOL:
        print(f"  NAN_JADI_NOL aktif: {int(h.isna().sum())} jam NaN dijadikan 0 (anomali) untuk t_tide")

    out, tabel, pred, msl = analisis(h, lintang)
    resid = h.values - pred

    tabel_semua[label] = tabel
    elev_baris[label] = elevasi_penting(tabel, msl)
    ev = elev_baris[label]
    if ev["MHWL"] < ev["S0/MSL"] or ev["LLWL"] > ev["MHWL"]:
        print("  !! PERINGATAN elevasi: MHWL berada di bawah MSL atau LLWL > MHWL. "
              "Itu akibat acuan Z0 pada rumus MHWL/MLWL, bukan fenomena laut "
              "(coba ACUAN_MHWL_MLWL = 'S0').")

    ring = rangkuman(label, h, tabel, msl, int(interp.sum()), n_spike, n_outlier, lintang)
    print(ring.to_string(index=False))
    print()
    print(tabel[["No", "Konstanta", "Frekuensi (cph)", "Amplitudo (cm)",
                 "Error Amp (cm)", "Fase (deg)", "Error Fase (deg)", "SNR",
                 "Signifikan (SNR>1)"]].round(4).to_string(index=False))

    deret = pd.DataFrame({
        "Waktu (UTC)": h.index,
        "Observasi (m)": h.values,
        "Interpolasi?": np.where(interp.values, "Ya", ""),
        "Prediksi (m)": pred,
        "Residu (m)": resid,
    })

    file_xlsx = os.path.join(OUT_DIR, f"hasil_harmonik_{stasiun}_{bulan}.xlsx")
    with pd.ExcelWriter(file_xlsx, engine="openpyxl") as w:
        tabel.to_excel(w, sheet_name="Konstanta harmonik", index=False)
        ring.to_excel(w, sheet_name="Ringkasan", index=False)
        deret.to_excel(w, sheet_name="Deret waktu per jam", index=False)
        for ws in w.book.worksheets:
            for kol in ws.columns:
                lebar = max(len(str(c.value)) if c.value is not None else 0 for c in kol)
                ws.column_dimensions[kol[0].column_letter].width = min(lebar + 2, 60)
    print(f"\n  tersimpan: {file_xlsx}")

    print("  tersimpan:", grafik_deret(label, h, pred, resid, interp))
    print("  tersimpan:", grafik_gabungan(label, h, pred, resid, interp))
    print("  tersimpan:", grafik_batang(label, tabel))
    print("  tersimpan:", grafik_fase(label, tabel))

    rekap_baris.append(baris_rekap(stasiun, bulan, h, tabel, msl, int(interp.sum()), n_outlier))

#rekap semua bulan
if rekap_baris:
    rekap = pd.DataFrame(rekap_baris)

    df_amp = tabel_amp_signifikan(tabel_semua)
    df_amp.index.name = "Konstanta"

    df_elev = pd.DataFrame(elev_baris).T[["Z0", "S0/MSL", "HHWL", "MHWL", "LLWL", "MLWL"]]
    df_elev.index.name = "Data set"

    f_rekap = os.path.join(OUT_DIR, "rekap_semua_bulan.xlsx")
    with pd.ExcelWriter(f_rekap, engine="openpyxl") as w:
        rekap.to_excel(w, sheet_name="Rekap", index=False)
        df_elev.round(6).to_excel(w, sheet_name="Elevasi penting")
        df_amp.round(4).to_excel(w, sheet_name="Amp signifikan")
        for ws in w.book.worksheets:
            for kol in ws.columns:
                lebar = max(len(str(c.value)) if c.value is not None else 0 for c in kol)
                ws.column_dimensions[kol[0].column_letter].width = min(lebar + 2, 40)

    f_elev = os.path.join(OUT_DIR, "tabel_elevasi_muka_laut.xlsx")
    df_elev.round(6).to_excel(f_elev)

    print("=" * 70)
    print(rekap.to_string(index=False))
    print()
    print("Elevasi muka laut penting (m)  [acuan MHWL/MLWL = %s]" % ACUAN_MHWL_MLWL)
    print(df_elev.round(4).to_string())
    print("tersimpan:", f_rekap)
    print("tersimpan:", f_elev)
    print("tersimpan:", grafik_rekap(rekap))
    print("tersimpan:", grafik_rekap_fase(rekap))
    print("tersimpan:", grafik_konstanta_signifikan(df_amp))
    print("tersimpan:", tabel_ke_gambar(df_elev, "Tabel. Elevasi muka laut penting (m) pada tiap data set",
                                         "tabel_elevasi_muka_laut.png"))

plt.show()
print("\nSelesai. Semua hasil ada di folder:", os.path.abspath(OUT_DIR))
