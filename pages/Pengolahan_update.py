import os
import numpy as np
import matplotlib.pyplot as plt
from obspy import read, read_inventory
from obspy.signal import PPSD
from obspy.signal.spectral_estimation import get_nlnm, get_nhnm
from obspy.signal.konnoohmachismoothing import konno_ohmachi_smoothing
from obspy.signal.util import next_pow_2
from obspy.signal import spectral_estimation
from obspy.signal.hvsr import hvsr
from datetime import datetime


# ==========================
# FOLDER OUTPUT
# ==========================
OUTPUT_DIR = os.path.join(os.getcwd(), "analysis_results")
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ==========================
# FUNGSI UTAMA
# ==========================
def process_mseed_and_xml(
    mseed_path,
    xml_path,
    psd_percentile=50,
    ko_smooth_factor=40,
    hvsr_window_len=30
):
    """
    Memproses file MiniSEED dan StationXML untuk menghasilkan:
    - PSD (Power Spectral Density)
    - HVSR (Horizontal-to-Vertical Spectral Ratio)
    Semua parameter dapat diatur dari dashboard Streamlit.
    """

    print("\n============================")
    print("📂 MULAI PROSES DATA MSEED")
    print("============================")

    # --- Validasi file ---
    if not os.path.exists(mseed_path) or not os.path.exists(xml_path):
        print("❌ File MiniSEED atau StationXML tidak ditemukan.")
        return None

    # --- Baca data & metadata ---
    print(f"📘 Membaca data: {mseed_path}")
    st = read(mseed_path)
    inv = read_inventory(xml_path)

    station_code = st[0].stats.station
    network_code = st[0].stats.network

    print(f"📡 Stasiun: {network_code}.{station_code}")
    print(f"🕒 Durasi: {st[0].stats.starttime} s/d {st[0].stats.endtime}")

    # ===============================
    # 1️⃣ PSD (Power Spectral Density)
    # ===============================
    print("\n🔹 Menghitung Power Spectral Density (PSD)...")

    tr = st[0]
    ppsd = PPSD(tr.stats, metadata=inv, ppsd_length=3600, overlap=0.5)
    ppsd.add(st)

    fig_psd, ax_psd = plt.subplots(figsize=(8, 5))
    ppsd.plot(show=False, ax=ax_psd, percentiles=[psd_percentile])
    psd_out = os.path.join(OUTPUT_DIR, f"{station_code}_PSD.png")
    fig_psd.savefig(psd_out, dpi=150, bbox_inches="tight")
    plt.close(fig_psd)
    print(f"✅ PSD disimpan: {psd_out}")

    # ===============================
    # 2️⃣ HVSR (Horizontal to Vertical)
    # ===============================
    print("\n🔹 Menghitung HVSR...")

    # Validasi parameter input
    if ko_smooth_factor < 5:
        ko_smooth_factor = 5.0
    if hvsr_window_len < 5.0:
        hvsr_window_len = 5.0

    # Ekstraksi komponen
    try:
        tr_e = st.select(component="E")[0]
        tr_n = st.select(component="N")[0]
        tr_z = st.select(component="Z")[0]
    except IndexError:
        print("❌ Komponen E/N/Z tidak lengkap.")
        return None

    # Potong data agar panjang sama
    npts = min(len(tr_e.data), len(tr_n.data), len(tr_z.data))
    tr_e.data = tr_e.data[:npts]
    tr_n.data = tr_n.data[:npts]
    tr_z.data = tr_z.data[:npts]

    # Hitung spektrum
    fs = tr_e.stats.sampling_rate
    nfft = next_pow_2(int(hvsr_window_len * fs))
    freq, psd_e = spectral_estimation.get_psd(tr_e.data, fs, nfft)
    _, psd_n = spectral_estimation.get_psd(tr_n.data, fs, nfft)
    _, psd_z = spectral_estimation.get_psd(tr_z.data, fs, nfft)

    psd_h = (psd_e + psd_n) / 2
    hvsr_ratio = np.sqrt(psd_h / psd_z)
    hvsr_smooth = konno_ohmachi_smoothing(hvsr_ratio, freq, bandwidth=ko_smooth_factor)

    # Simpan plot HVSR
    fig_hvsr, ax_hvsr = plt.subplots(figsize=(8, 5))
    ax_hvsr.semilogx(freq, hvsr_smooth, color="darkgreen", lw=2)
    ax_hvsr.set_xlabel("Frekuensi (Hz)")
    ax_hvsr.set_ylabel("HVSR")
    ax_hvsr.set_title(f"HVSR - {station_code}")
    ax_hvsr.grid(True, which="both", linestyle="--", alpha=0.5)
    hvsr_out = os.path.join(OUTPUT_DIR, f"{station_code}_HVSR.png")
    fig_hvsr.savefig(hvsr_out, dpi=150, bbox_inches="tight")
    plt.close(fig_hvsr)
    print(f"✅ HVSR disimpan: {hvsr_out}")

    # ===============================
    # 3️⃣ SIMPAN PARAMETER
    # ===============================
    param_file = os.path.join(OUTPUT_DIR, f"{station_code}_parameters.txt")
    with open(param_file, "w") as f:
        f.write("# Parameter Analisis\n")
        f.write(f"Waktu Proses          : {datetime.now()}\n")
        f.write(f"Stasiun               : {network_code}.{station_code}\n")
        f.write(f"PSD Percentile        : {psd_percentile}\n")
        f.write(f"KO Smoothing Factor   : {ko_smooth_factor}\n")
        f.write(f"HVSR Window Length(s) : {hvsr_window_len}\n")

    print(f"⚙️ Parameter analisis disimpan: {param_file}")

    # ===============================
    # 4️⃣ RINGKASAN
    # ===============================
    print("\n====================================")
    print("🎯 PROSES SELESAI")
    print(f"📁 Hasil disimpan di folder: {OUTPUT_DIR}")
    print("====================================\n")

    return {
        "station": station_code,
        "network": network_code,
        "psd_file": psd_out,
        "hvsr_file": hvsr_out,
        "params_used": {
            "psd_percentile": psd_percentile,
            "ko_smooth_factor": ko_smooth_factor,
            "hvsr_window_len": hvsr_window_len
        }
    }


# ==========================
# EKSEKUSI LANGSUNG (opsional)
# ==========================
#if __name__ == "__main__":
    # Contoh penggunaan manual:
#    process_mseed_and_xml(
#        mseed_path="contoh_data/ABCD.mseed",
#        xml_path="contoh_data/ABCD.xml",
#        psd_percentile=75,
#        ko_smooth_factor=40,
#        hvsr_window_len=30
#    )
