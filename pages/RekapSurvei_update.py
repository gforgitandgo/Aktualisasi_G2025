import streamlit as st
import pandas as pd
import sqlite3
import os
import base64
from datetime import datetime
import platform
from io import BytesIO

REKAP_PATH= os.getenv("REKAP_PATH") or "/"
local = os.getenv("LOCAL") or True

if local == "false" or local== "False" or str(local) == "0":
    local = False
    
    
    
def main():
    # Tombol kembali ke dashboard utama
    if st.button("⬅️ Kembali ke Dashboard Utama"):
        st.switch_page("Dashboard_integrasi_update.py")
        
    # ==========================
    # KONFIGURASI FOLDER & DB
    # ==========================
    # BASE_DIR = r"D:\Dashboard_integrasi2"
    BASE_DIR = os.getcwd()
    DATA_DIR = os.path.join(BASE_DIR, "data")
    REKAP_DIR = os.path.join(BASE_DIR, "Rekapitulasi Hasil Survei")
    DB_PATH = os.path.join(BASE_DIR, "rekap.db")
    LOGO_PATH = os.path.join(BASE_DIR, "logo_bmkg.png")

    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(REKAP_DIR, exist_ok=True)

    # ==========================
    # INISIALISASI DB
    # ==========================
    def init_db():
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS rekap (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nama_survei TEXT,
                lokasi TEXT,
                tanggal TEXT,
                alat TEXT,
                hasil TEXT,
                folder TEXT,
                lampiran TEXT
            )
            """
        )
        conn.commit()
        conn.close()

    init_db()

    # ==========================
    # PAGE CONFIG
    # ==========================
    st.set_page_config(
        page_title="Dashboard Rekapitulasi Hasil Survei",
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
        .hint {color:#555; font-size:0.9rem; margin-top:4px;}
        </style>
        """,
        unsafe_allow_html=True,
    )

    # ==========================
    # HELPERS
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
                <h1>Dashboard Rekapitulasi Hasil Survei</h1>
                <p>Direktorat Gempabumi dan Tsunami • BMKG</p>
            </div>
        </div>
        <div class="header-divider"></div>
        """,
        unsafe_allow_html=True,
    )

    # ==========================
    # DATABASE HANDLER
    # ==========================
    @st.cache_data(ttl=30)
    def fetch_df():
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query("SELECT * FROM rekap ORDER BY id DESC", conn)
        conn.close()
        return df

    # ==========================
    # FORM INPUT (2 opsi, tanpa disabled)
    # ==========================
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("📋 Input Data Survei")

    with st.form("form_input", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        nama_survei = col1.text_input("Nama Survei", key="inp_nama_survei")
        lokasi = col2.text_input("Lokasi Survei", key="inp_lokasi")
        tanggal = col3.date_input("Tanggal Survei", value=datetime.today(), key="inp_tanggal")

        col4, col5 = st.columns(2)
        alat = col4.text_input("Alat Survei", key="inp_alat")
        lampiran_files = col5.file_uploader("Lampiran (boleh lebih dari satu)", accept_multiple_files=True, key="inp_lampiran")

        hasil = st.text_area("Hasil Pengamatan / Catatan", height=120, key="inp_hasil")

        st.markdown("---")
        st.write("📂 Pilih lokasi penyimpanan:")

        # 2 opsi: Gunakan folder utama atau Buat folder baru
        opsi_folder = st.radio(
            "Opsi penyimpanan:",
            ["Gunakan folder utama", "Buat folder baru"],
            index=0,
            key="opsi_folder_radio"
        )

        # Tampilkan input nama folder baru selalu (tidak disabled)
        nama_folder_baru = st.text_input(
            "Nama Folder Baru (hanya isi jika memilih 'Buat folder baru')",
            value="",
            placeholder="Contoh: 2025-09-Survei-Jawa",
            key="input_folder_baru_no_disabled"
        )
        st.markdown("<div class='hint'>Catatan: field di atas hanya akan digunakan jika opsi 'Buat folder baru' dipilih.</div>", unsafe_allow_html=True)

        submitted = st.form_submit_button("💾 Simpan Data Hasil Survei")

        if submitted:
            # Tentukan folder tujuan berdasarkan opsi
            if opsi_folder == "Buat folder baru":
                if not nama_folder_baru or not nama_folder_baru.strip():
                    st.error("Nama folder baru kosong — silakan isi nama folder sebelum menyimpan.")
                else:
                    folder_tujuan = os.path.join(REKAP_DIR, nama_folder_baru.strip())
                    try:
                        os.makedirs(folder_tujuan, exist_ok=True)
                    except Exception as e:
                        st.error(f"Gagal membuat folder baru: {e}")
                        folder_tujuan = REKAP_DIR
            else:
                folder_tujuan = REKAP_DIR

            # Pastikan folder tujuan ada
            if os.path.exists(folder_tujuan):
                lampiran_names = []
                if lampiran_files:
                    for f in lampiran_files:
                        safe_name = f.name
                        save_path = os.path.join(folder_tujuan, safe_name)
                        try:
                            with open(save_path, "wb") as out:
                                out.write(f.getbuffer())
                            lampiran_names.append(safe_name)
                        except Exception as e:
                            st.error(f"Gagal menyimpan lampiran {safe_name}: {e}")

                # Simpan ke DB
                try:
                    conn = sqlite3.connect(DB_PATH)
                    c = conn.cursor()
                    c.execute(
                        "INSERT INTO rekap (nama_survei, lokasi, tanggal, alat, hasil, folder, lampiran) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (
                            nama_survei or "-",
                            lokasi or "-",
                            tanggal.strftime("%Y-%m-%d"),
                            alat or "-",
                            hasil or "-",
                            os.path.basename(folder_tujuan),
                            ", ".join(lampiran_names) if lampiran_names else "-",
                        ),
                    )
                    conn.commit()
                    conn.close()
                    st.success(f"✅ Data hasil survei tersimpan di folder: **{os.path.basename(folder_tujuan)}**")
                    st.cache_data.clear()
                    force_rerun()
                except Exception as e:
                    st.error(f"Gagal menyimpan data ke database: {e}")
            else:
                st.error("Folder tujuan tidak ditemukan. Data tidak disimpan.")

    st.markdown("</div>", unsafe_allow_html=True)

    # ==========================
    # TABEL REKAP + PAGINATION
    # ==========================
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("📂 Rekapitulasi Data Tersimpan")

    df = fetch_df()
    if not df.empty:
        df["tanggal"] = pd.to_datetime(df["tanggal"], errors="coerce").dt.strftime("%d-%m-%Y").fillna(df["tanggal"])
        df.insert(0, "No", range(1, len(df) + 1))

        search = st.text_input("🔍 Cari data (ketik kata kunci, tekan Enter)", key="search_rekap")
        if search:
            mask = df.apply(lambda row: row.astype(str).str.contains(search, case=False).any(), axis=1)
            df_filtered = df[mask]
        else:
            df_filtered = df

        display_cols = ["No", "nama_survei", "lokasi", "tanggal", "alat", "hasil", "folder", "lampiran"]
        df_show = df_filtered[display_cols].copy()
        df_show.rename(
            columns={
                "nama_survei": "Nama Survei",
                "lokasi": "Lokasi",
                "tanggal": "Tanggal",
                "alat": "Alat",
                "hasil": "Hasil",
                "folder": "Folder",
                "lampiran": "Lampiran",
            },
            inplace=True,
        )

        entries_per_page = st.selectbox("Tampilkan jumlah baris:", [5, 10, 15], index=1, key="entries_per_page")
        total_rows = len(df_show)
        total_pages = (total_rows - 1) // entries_per_page + 1
        if "page" not in st.session_state:
            st.session_state.page = 1

        start_idx = (st.session_state.page - 1) * entries_per_page
        end_idx = start_idx + entries_per_page
        df_page = df_show.iloc[start_idx:end_idx]

        st.dataframe(df_page, use_container_width=True, hide_index=True)

        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            if st.button("⬅️ Prev") and st.session_state.page > 1:
                st.session_state.page -= 1
                st.rerun()
        with col3:
            if st.button("Next ➡️") and st.session_state.page < total_pages:
                st.session_state.page += 1
                st.rerun()

        st.write(f"Halaman {st.session_state.page} dari {total_pages}")

        if not local:
            st.divider()
            st.markdown("### 📁 Akses Folder Rekapitulasi")

            st.link_button("View my results folder",REKAP_PATH)
        else:
            st.divider()
            st.markdown("### 📁 Akses Folder Rekapitulasi")
            if platform.system() == "Windows":
                if st.button("🔍 Buka Folder Rekapitulasi Utama"):
                    if os.path.exists(REKAP_DIR):
                        os.startfile(REKAP_DIR)
                    else:
                        st.warning("Folder rekapitulasi utama tidak ditemukan.")
            else:
                st.code(REKAP_DIR)   

    else:
        st.info("Belum ada data rekapitulasi tersimpan.")

    st.markdown("</div>", unsafe_allow_html=True)

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
