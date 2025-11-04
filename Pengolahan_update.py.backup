import matplotlib
matplotlib.use('Agg')  # Wajib untuk backend non-GUI di server
import os
import numpy as np
import matplotlib.pyplot as plt
from obspy import read, read_inventory, Stream
from obspy.signal import PPSD
from obspy.signal.spectral_estimation import get_nlnm, get_nhnm
from obspy.imaging.cm import pqlx
from obspy.signal.konnoohmachismoothing import konno_ohmachi_smoothing

# Konfigurasi Output
OUTPUT_DIR = "analysis_results"

def calculate_hvsr(st, station_code, smoothing_constant=40.0, window_length=20.0, overlap=0.5):
    """
    Menghitung Horizontal-to-Vertical Spectral Ratio (HVSR).
    Plotting dilakukan di sini dan hasil plot dikembalikan.
    """
    print("🌍 Memproses HVSR...")
    
    # Inisialisasi traces
    tr_z, tr_h1, tr_h2 = None, None, None
    
    # 1. Identifikasi Komponen (Logika yang Lebih Tangguh)
    # Coba identifikasi menggunakan standar (Z, E, N)
    st_z_standard = st.select(component="Z")
    st_h_standard = st.select(component="E") + st.select(component="N")
    
    if len(st_z_standard) > 0 and len(st_h_standard) >= 2:
        # Jika berhasil menggunakan standar Z, E, N
        tr_z = st_z_standard[0]
        tr_h1 = st_h_standard[0]
        tr_h2 = st_h_standard[1]
    else:
        # Fallback: Cari channel berdasarkan nama (misal: "HHZ", "HH1", "HH2")
        print("⚠️ Warning: Mencari komponen Z, E, N standar gagal. Mencoba identifikasi channel berdasarkan pola nama.")
        
        all_channel_names = sorted(list(set(tr.stats.channel for tr in st)))
        
        z_name = next((c for c in all_channel_names if c.upper().endswith('Z')), None)
        
        if z_name:
            # Z ditemukan, sisa adalah kandidat H
            tr_z = st.select(channel=z_name)[0]
            
            # Filter channels yang bukan Z
            h_channels_names = [c for c in all_channel_names if c != z_name]
            
            if len(h_channels_names) >= 2:
                # Ambil 2 channel pertama sebagai H1 dan H2
                tr_h1 = st.select(channel=h_channels_names[0])[0]
                tr_h2 = st.select(channel=h_channels_names[1])[0]
            
    # Final Check
    if tr_z is None or tr_h1 is None or tr_h2 is None:
        print("❌ Gagal HVSR: Tidak dapat mengidentifikasi 1 Vertikal (Z) dan 2 Horizontal (H) trace yang valid.")
        return None, "N/A"

    # Pastikan trim dan preprocessing dilakukan (detrend dan taper)
    # Kita hanya perlu memproses trace yang akan digunakan (Z, H1, H2)
    for tr in [tr_z, tr_h1, tr_h2]:
        tr.detrend("demean")
        tr.taper(max_percentage=0.05, type="hann")
        
    # --- Lanjut Analisis HVSR (Tidak Ada Perubahan Logika) ---
    dt = tr_z.stats.delta
    npts = tr_z.stats.npts
    fs = tr_z.stats.sampling_rate

    # Pengaturan Windowing
    n_window = int(window_length * fs)
    n_overlap = int(n_window * overlap)

    freqs_list = []
    hvsr_list = []

    # Loop melalui semua window
    for start in np.arange(0, npts - n_window + 1, n_window - n_overlap):
        end = start + n_window
        data_z = tr_z.data[start:end]
        data_h1 = tr_h1.data[start:end]
        data_h2 = tr_h2.data[start:end]

        # Hitung FFT (Power Spectrum Density)
        fft_z = np.fft.fft(data_z * np.hanning(n_window))
        fft_h1 = np.fft.fft(data_h1 * np.hanning(n_window))
        fft_h2 = np.fft.fft(data_h2 * np.hanning(n_window))

        psd_z = np.abs(fft_z)**2
        psd_h1 = np.abs(fft_h1)**2
        psd_h2 = np.abs(fft_h2)**2

        # Ambil hanya frekuensi positif
        n_half = n_window // 2
        freqs = np.fft.fftfreq(n_window, d=dt)[:n_half]
        psd_z = psd_z[:n_half]
        psd_h1 = psd_h1[:n_half]
        psd_h2 = psd_h2[:n_half]
        
        # Horizontal Spectrum (rata-rata geometrik)
        psd_h = np.sqrt(psd_h1 * psd_h2)
        
        # HVSR (H/V)
        hvsr_window = np.zeros_like(psd_z)
        valid_indices = psd_z > 1e-15
        hvsr_window[valid_indices] = psd_h[valid_indices] / psd_z[valid_indices]
        
        hvsr_list.append(hvsr_window)
        freqs_list.append(freqs)

    if not hvsr_list:
        print("❌ Gagal HVSR: Tidak ada data window yang diproses.")
        return None, "N/A"

    # Rata-rata Geometrik dari semua window HVSR
    hvsr_avg = np.exp(np.mean(np.log(np.array(hvsr_list)), axis=0))
    freqs = freqs_list[0]

    # Konno-Ohmachi Smoothing
    smoothed_hvsr = konno_ohmachi_smoothing(hvsr_avg, freqs, smoothing_constant)

    # --- Plotting ---
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.loglog(freqs, smoothed_hvsr, color='purple', linewidth=2)
    
    # Deteksi Frekuensi Puncak (f0)
    f_min, f_max = 0.5, 20.0 # Range umum untuk f0
    idx = np.where((freqs >= f_min) & (freqs <= f_max))
    f_peak = 'N/A'
    if len(idx[0]) > 0:
        peak_index = np.argmax(smoothed_hvsr[idx])
        f_peak = freqs[idx][peak_index]
        amp_peak = smoothed_hvsr[idx][peak_index]
        
        ax.axvline(f_peak, color='red', linestyle='--', alpha=0.6, label=f'$f_0$: {f_peak:.2f} Hz')
        ax.scatter(f_peak, amp_peak, color='red', marker='o', zorder=5)
        ax.legend(loc='lower left')
        
    ax.set_title(f"HVSR (H/V) Ratio - {station_code}\nKO Smoothing: {smoothing_constant}", fontsize=14)
    ax.set_xlabel("Frekuensi (Hz)")
    ax.set_ylabel("Rasio H/V")
    ax.grid(True, which="both", ls="-", color='0.7')
    ax.set_xlim(freqs[1], freqs[-1])
    
    # Simpan plot
    hvsr_png = os.path.join(OUTPUT_DIR, f"{station_code}_HVSR.png")
    fig.savefig(hvsr_png)
    plt.close(fig)
    
    # Simpan data HVSR ke file teks
    hvsr_txt = os.path.join(OUTPUT_DIR, f"{station_code}_HVSR.txt")
    with open(hvsr_txt, "w") as f:
        f.write("# Frequency(Hz) HVSR_Ratio\n")
        for i in range(len(freqs)):
            f.write(f"{freqs[i]:.5f} {smoothed_hvsr[i]:.5f}\n")
    
    print(f"📈 HVSR disimpan: {hvsr_png} | f0: {f_peak}")
    return hvsr_png, f_peak

def process_mseed_and_xml(mseed_file: str, xml_file: str, psd_percentile: int = 50, ko_smooth_factor: float = 40.0, hvsr_window_len: float = 20.0):
    """Fungsi utama untuk memproses Waveform, PSD, dan HVSR."""
    
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    # Cek keberadaan file
    if not os.path.exists(mseed_file):
        print(f"❌ File MSEED tidak ditemukan: {mseed_file}")
        return
    if not os.path.exists(xml_file):
        print(f"❌ File XML tidak ditemukan: {xml_file}")
        return

    # Baca waveform & inventory
    try:
        st = read(mseed_file)
        inv = read_inventory(xml_file)
    except Exception as e:
        print(f"❌ Gagal membaca file: {e}")
        return

    # Merge trace yang overlap atau pecah
    st.merge(method=1, fill_value="interpolate")

    # Ambil kode stasiun dari metadata
    station_code = st[0].stats.station
    print(f"✅ Memulai analisis untuk stasiun: {station_code}")

    # --- 1. PLOT WAVEFORM ---
    waveform_png = os.path.join(OUTPUT_DIR, f"{station_code}_waveform.png")
    st.plot(outfile=waveform_png, size=(800, 400), tight_layout=True)
    print(f"📈 Waveform disimpan: {waveform_png}")

    # --- 2. PROSES PSD ---
    for channel in sorted(set(tr.stats.channel for tr in st)):
        tr_channel = st.select(channel=channel)
        if len(tr_channel) == 0: continue

        tr = tr_channel[0]

        try:
            print(f"🔍 Memproses PSD {station_code} - {channel}")
            ppsd = PPSD(tr.stats, metadata=inv)
            ppsd.add(tr)

            # Simpan plot PSD
            psd_png = os.path.join(OUTPUT_DIR, f"{station_code}_PSD_{channel}.png")
            ppsd.plot(
                cmap=pqlx,
                xaxis_frequency=False,
                show_percentiles=True,
                percentiles=[psd_percentile],
                filename=psd_png
            )
            print(f"📊 PSD disimpan: {psd_png}")

            # Simpan data percentile ke file teks
            freqs, psd_median = ppsd.get_percentile(percentile=float(psd_percentile))
            nlnm_freqs, nlnm_vals = get_nlnm()
            nhnm_freqs, nhnm_vals = get_nhnm()

            psd_txt = os.path.join(OUTPUT_DIR, f"{station_code}_PSD_{channel}.psd")
            with open(psd_txt, "w") as f:
                f.write(f"# Frequency(Hz) Median({psd_percentile}th_dB) NLNM(dB) NHNM(dB)\n")
                for i in range(len(freqs)):
                    freq = freqs[i]
                    # Interpolasi NLNM/NHNM (pendekatan sederhana log-log)
                    nlnm = np.interp(np.log10(freq), np.log10(nlnm_freqs), nlnm_vals)
                    nhnm = np.interp(np.log10(freq), np.log10(nhnm_freqs), nhnm_vals)
                    f.write(f"{freq:.5f} {psd_median[i]:.5f} {nlnm:.5f} {nhnm:.5f}\n")
            print(f"📄 Percentile PSD disimpan: {psd_txt}")

        except Exception as e:
            print(f"❌ Gagal memproses PSD {station_code} - {channel} - {e}")

    # --- 3. PROSES HVSR ---
    try:
        calculate_hvsr(
            st.copy(), # Gunakan copy agar stream tidak diubah-ubah fungsi lain
            station_code,
            smoothing_constant=ko_smooth_factor, 
            window_length=hvsr_window_len
        )
    except Exception as e:
        print(f"❌ Gagal memproses HVSR: {e}")
        
    print("\n====================================")
    print("✅ Semua Analisis Selesai.")
    print(f"Lihat hasil plot dan data di folder '{OUTPUT_DIR}'")
    print("====================================")


if __name__ == "__main__":
    # --- Contoh Penggunaan ---
    # GANTI PATH FILE DI SINI dengan path file lo yang sebenarnya!
    example_mseed = "D:/Test_PSD2/Package_AAFM.mseed"
    example_xml = "D:/Test_PSD2/IA.AAFM.xml"
    
    if os.path.exists(example_mseed) and os.path.exists(example_xml):
        # Parameter yang disarankan untuk HVSR:
        analysis_params = {
            "psd_percentile": 50,         # Percentile untuk PSD
            "ko_smooth_factor": 40.0,     # Faktor Konno-Ohmachi Smoothing (default 40)
            "hvsr_window_len": 20.0       # Panjang Window dalam detik (default 20s)
        }
        
        process_mseed_and_xml(
            mseed_file=example_mseed,
            xml_file=example_xml,
            **analysis_params
        )
    else:
        print("❌ ERROR: Tolong ganti 'example_mseed' dan 'example_xml' dengan path file yang benar dan pastikan file ada.")
