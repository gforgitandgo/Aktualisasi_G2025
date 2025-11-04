import streamlit as st
import pandas as pd
import sqlite3
import os
import base64
from datetime import datetime
import platform
from io import BytesIO
import time

# =========================
# KONFIGURASI FOLDER
# =========================
BASE_DIR = os.getcwd()
SOP_FOLDER = os.path.join(BASE_DIR, "data_sop")
os.makedirs(SOP_FOLDER, exist_ok=True)

# ==========================
# KONFIGURASI FOLDER & DB
# ==========================
BASE_DIR = r"D:\Dashboard_integrasi2"
LOGO_PATH = os.path.join(BASE_DIR, "logo_bmkg.png")

# =========================
# KONFIGURASI DASHBOARD
# =========================
st.set_page_config(page_title="Dashboard Integrasi BMKG", layout="wide")

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
    .header-divider {height:12px; width:100%; background: linear-gradient(90deg,#008080 0%, #00ff00 100%); border-radius:0 0 20px 20px; margin:18px 0 24px 0;}
    .card {background:#fff; border-radius:12px; padding:18px; box-shadow:0 3px 10px rgba(0,0,0,0.05); margin-bottom:18px;}
    .footer {text-align:center; color:#555; padding:14px 0; margin-top:24px; border-top:1px solid #eee;}
    table {width:100%; border-collapse:collapse; margin-top:10px;}
    th, td {padding:10px 8px; border-bottom:1px solid #eee; text-align:left; font-size:0.9rem;}
    th {background-color:#e8f5f2; font-weight:600; color:#004d4d;}
    tr:hover {background-color:#f8f8f8;}
    a {text-decoration:none; color:#00796b;}
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
            <h1>Sistem Observasi Gempabumi dan Tsunami</h1>
            <p>Direktorat Gempabumi dan Tsunami • BMKG</p>
        </div>
    </div>
    <div class="header-divider"></div>
    """,
    unsafe_allow_html=True,
)

st.markdown("---")

# =========================
# BAGIAN: UPLOAD & TABEL SOP
# =========================
st.subheader("📄 Manajemen File SOP")

if "refresh" not in st.session_state:
    st.session_state.refresh = False

uploaded_file = st.file_uploader(
    "Pilih file SOP (PDF atau DOCX)",
    type=["pdf", "docx"],
    key="sop_uploader"
)

if uploaded_file is not None:
    if st.button("📤 Upload File SOP"):
        save_path = os.path.join(SOP_FOLDER, uploaded_file.name)
        with open(save_path, "wb") as f:
            f.write(uploaded_file.read())
        st.success(f"✅ File '{uploaded_file.name}' berhasil diunggah ke folder '{SOP_FOLDER}'")

        st.session_state.refresh = True
        st.rerun()

if st.session_state.refresh:
    st.session_state.refresh = False

# =========================
# TABEL SOP (versi tabel rapi)
# =========================
st.subheader("📂 Daftar File SOP")
files = [f for f in os.listdir(SOP_FOLDER) if os.path.isfile(os.path.join(SOP_FOLDER, f))]

if len(files) == 0:
    st.info("Belum ada file SOP yang diunggah.")
else:
    data = []
    for file_name in files:
        file_path = os.path.join(SOP_FOLDER, file_name)
        size_kb = os.path.getsize(file_path) / 1024
        upload_time = datetime.fromtimestamp(os.path.getmtime(file_path)).strftime("%Y-%m-%d %H:%M:%S")

        # Buat link base64 untuk preview
        with open(file_path, "rb") as f:
            file_data = f.read()
        b64 = base64.b64encode(file_data).decode()
        file_ext = os.path.splitext(file_name)[1].lower()
        mime_type = (
            "application/pdf"
            if file_ext == ".pdf"
            else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        file_url = f"data:{mime_type};base64,{b64}"

        data.append({
            "Nama File": file_name,
            "Ukuran (KB)": f"{size_kb:.1f}",
            "Terakhir Diperbarui": upload_time,
            "Preview": f"<a href='{file_url}' target='_blank'>🔍 Lihat</a>",
            "Hapus": f"<a href='?hapus={file_name}' style='color:red;'>🗑️ Hapus</a>"
        })

    df = pd.DataFrame(data, columns=["Nama File", "Ukuran (KB)", "Terakhir Diperbarui", "Preview", "Hapus"])

    # Tampilkan tabel HTML agar link aktif
    st.markdown(df.to_html(escape=False, index=False, justify="left"), unsafe_allow_html=True)

    # Logika hapus file
    query_params = st.query_params
    if "hapus" in query_params:
        target_file = query_params["hapus"]
        file_path = os.path.join(SOP_FOLDER, target_file)
        if os.path.exists(file_path):
            os.remove(file_path)
            st.warning(f"'{target_file}' telah dihapus.")
            time.sleep(0.8)
            st.rerun()

st.markdown("---")

# =========================
# NAVIGASI DASHBOARD
# =========================
st.subheader("Akses Dashboard Lainnya")

col1, col2 = st.columns(2)

with col1:
    if st.button("📄 Dashboard Rekapitulasi Hasil Survei"):
        st.switch_page("pages/RekapSurvei_update.py")

with col2:
    if st.button("⚙️ Dashboard Pengolahan Data PSD & HVSR"):
        st.switch_page("pages/Dashboard_pengolahan_update.py")

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
