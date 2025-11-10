import streamlit as st
import os
import base64
from datetime import datetime
from Pengolahan_update import process_mseed_and_xml  # sesuaikan nama file prosesnya

def main():
    # Tombol kembali ke dashboard utama
    if st.button("⬅️ Kembali ke Dashboard Utama"):
        st.switch_page("Dashboard_integrasi_update.py")
        
    # ===============================
    # KONFIGURASI DASAR
    # ===============================
    st.set_page_config(page_title="Dashboard Pengolahan Data Seismik", layout="wide")

    BASE_DIR = os.getcwd()
    OUTPUT_DIR = os.getenv("OUTPUT_DIR") or "Hasil_Analisis"
    # OUTPUT_DIR = r"D:\Dashboard_integrasi2\Hasil_Analisis"
    OUTPUT_DIR = os.path.join(BASE_DIR, OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    ASSET_PATH = os.getenv("ASSET_PATH") or "assets"
    # BASE_DIR = r"D:\Dashboard_integrasi2"
    LOGO_PATH = os.path.join(BASE_DIR,ASSET_PATH, "LogoBMKG.png")

    # ===============================
    # UTILITAS
    # ===============================
    def reset_file_uploaders():
        """Ganti key uploader supaya reset"""
        suffix = datetime.now().strftime("%H%M%S")
        st.session_state["xml_key"] = f"xml_uploader_{suffix}"
        st.session_state["mseed_key"] = f"mseed_uploader_{suffix}"

    def clear_all(preserve_message=None):
        """Reset total dashboard (setelah penyimpanan)"""
        saved_message = preserve_message
        st.session_state.clear()
        reset_file_uploaders()
        if saved_message:
            st.session_state["final_message"] = saved_message


    # ===============================
    # INISIALISASI
    # ===============================
    if "xml_key" not in st.session_state:
        st.session_state["xml_key"] = "xml_uploader_default"
    if "mseed_key" not in st.session_state:
        st.session_state["mseed_key"] = "mseed_uploader_default"

    # ==========================
    # PAGE CONFIG
    # ==========================
    st.set_page_config(
        page_title="SISTEM PENGOLAHAN DATA PSD & HVSR",
        layout="wide",
        page_icon="📋",
    )

    # ==========================
    # STYLE
    # ==========================
    st.markdown(
        """
        <style>
        body {background-color: #f5f9fc; font-family: "Segoe UI", sans-serif;}
        .header-container {display:flex; align-items:center; gap:1.2rem; padding:1.8rem 2rem 1rem 2rem; background-color:#fff; border-radius:10px;}
        .header-logo img {width:85px; height:auto; display:block;}
        .header-text h1 {font-weight:700; font-size:1.6rem; margin:0; color:#111;}
        .header-text p {margin:0.25rem 0 0 0; color:#555;}
        .header-divider {height:12px; width:100%; background: linear-gradient(90deg,#007ACC 0%, #00AEEF 100%); border-radius:0 0 20px 20px; margin:18px 0 24px 0;}
        .card {background:#fff; border-radius:12px; padding:18px; box-shadow:0 3px 10px rgba(0,0,0,0.05); margin-bottom:18px;}
        .footer {text-align:center; color:#555; padding:14px 0; margin-top:24px; border-top:1px solid #eee;}
        </style>
        """,
        unsafe_allow_html=True,
    )

    # ==========================
    # HELPER
    # ==========================
    def force_rerun():
        st.session_state["_rerun_trigger"] = not st.session_state.get("_rerun_trigger", False)
        st.rerun()

    def load_logo_b64(path):
        if os.path.exists(path):
            with open(path, "rb") as f:
                return base64.b64encode(f.read()).decode()
        return None

    # ==========================
    # HEADER
    # ==========================
    logo_b64 = load_logo_b64(LOGO_PATH)
    logo_img_html = (
        f'<img src="data:image/png;base64,{logo_b64}" alt="BMKG Logo">'
        if logo_b64
        else "<div style='color:#999'>[Logo tidak ditemukan]</div>"
    )
    st.markdown(
        f"""
        <div class="header-container">
            <div class="header-logo">{logo_img_html}</div>
            <div class="header-text">
                <h1>SISTEM PENGOLAHAN DATA PSD & HVSR</h1>
                <p>Direktorat Gempabumi dan Tsunami • BMKG</p>
            </div>
        </div>
        <div class="header-divider"></div>
        """,
        unsafe_allow_html=True,
    )

    # ===============================
    # PESAN AKHIR (SETELAH RESET)
    # ===============================
    if "final_message" in st.session_state:
        st.success(st.session_state["final_message"])
        st.session_state.pop("final_message")

    # ===============================
    # UPLOAD SECTION
    # ===============================
    st.subheader("📂 Upload Data")
    col1, col2 = st.columns(2)

    uploaded_xml = st.file_uploader("Upload File XML", type=["xml"], key=st.session_state["xml_key"])
    uploaded_mseed = st.file_uploader("Upload File MSEED", type=["mseed"], key=st.session_state["mseed_key"])

    # ===============================
    # INPUT PARAMETER
    # ===============================
    st.subheader("Input Parameter Analisis")
    col3, col4, col5 = st.columns(3)

    psd_percentile = st.slider("Percentile (PSD)", 0, 100, 50)
    ko_smooth_factor = st.number_input("Konno-Ohmachi Smoothing Factor", value=40.0)
    hvsr_window_len = st.number_input("Panjang Window HVSR (detik)", value=20.0)

    # ===============================
    # RUN ANALISIS
    # ===============================
    st.markdown("---")
    st.subheader("Jalankan Analisis")

    run_btn = st.button("Run Analysis")

    if run_btn:
        if uploaded_xml is None or uploaded_mseed is None:
            st.warning("⚠️ Harap upload kedua file XML dan MSEED terlebih dahulu.")
            st.stop()

        with st.spinner("Analisis sedang berjalan..."):
            tmp_dir = "temp_files"
            os.makedirs(tmp_dir, exist_ok=True)

            xml_path = os.path.join(tmp_dir, uploaded_xml.name)
            mseed_path = os.path.join(tmp_dir, uploaded_mseed.name)

            print(mseed_path,"def")
            print(xml_path,"abc")

            with open(xml_path, "wb") as f:
                f.write(uploaded_xml.read())
            with open(mseed_path, "wb") as f:
                f.write(uploaded_mseed.read())

            try:
                results = process_mseed_and_xml(
                    mseed_file=mseed_path,
                    xml_file=xml_path,
                    psd_percentile=psd_percentile,
                    ko_smooth_factor=ko_smooth_factor,
                    hvsr_window_len=hvsr_window_len,
                )

                # tampilkan pesan hasil analisis
                if isinstance(results, dict):
                    if "error" in results:
                        st.error(f"❌ {results['error']}")
                    elif "message" in results:
                        st.info(results["message"])
                    else:
                        st.success("✅ Analisis selesai tanpa error.")
                else:
                    st.success("✅ Analisis selesai!")

                # simpan hasil di session
                st.session_state["analysis_results"] = results
                st.session_state["analysis_done"] = True

                # clear hanya file uploader
                reset_file_uploaders()

            except Exception as e:
                st.error(f"❌ Terjadi kesalahan saat analisis: {e}")
                st.stop()

    # ===============================
    # SIMPAN HASIL
    # ===============================
    if st.session_state.get("analysis_done", False):
        st.markdown("---")
        st.subheader("💾 Simpan Hasil Analisis")

        parent_dir = OUTPUT_DIR
        folder_choice = st.radio(
            "Pilih lokasi penyimpanan:",
            ("Gunakan folder utama", "Buat folder baru di dalamnya"),
        )

        if folder_choice == "Buat folder baru di dalamnya":
            new_folder_name = st.text_input("Nama folder baru:", "")
            save_dir = os.path.join(parent_dir, new_folder_name) if new_folder_name else None
        else:
            save_dir = parent_dir

        if st.button("💾 Simpan Semua Hasil", type="primary"):
            if not save_dir:
                st.warning("⚠️ Harap tentukan folder penyimpanan terlebih dahulu.")
            else:
                try:
                    os.makedirs(save_dir, exist_ok=True)

                    analysis_result_dir = "analysis_results"
                    if os.path.exists(analysis_result_dir):
                        for file in os.listdir(analysis_result_dir):
                            src = os.path.join(analysis_result_dir, file)
                            dst = os.path.join(save_dir, file)
                            if os.path.isfile(src):
                                with open(src, "rb") as fsrc, open(dst, "wb") as fdst:
                                    fdst.write(fsrc.read())

                    # set flag refresh biar rerun otomatis
                    st.session_state["refresh"] = True
                    st.session_state["saved_message"] = "✅ Hasil berhasil disimpan dan dashboard telah direset!"

                except Exception as e:
                    st.error(f"❌ Gagal menyimpan hasil: {e}")

    # ===============================
    # AUTO REFRESH SETELAH SIMPAN
    # ===============================
    if st.session_state.get("refresh", False):
        saved_message = st.session_state.get("saved_message", None)
        clear_all(saved_message)
        st.session_state["refresh"] = False

    # ==========================
    # FOOTER
    # ==========================
    st.markdown(
        """
        <div class='footer'>
            © 2025 Direktorat Gempabumi dan Tsunami • BMKG — Dibuat untuk mendukung kegiatan survei Tim Observasi Gempabumi dan Tsunami.
        </div>
        """,
        unsafe_allow_html=True,
    )
if __name__ == "__main__":
    main()