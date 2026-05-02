import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
import pandas as pd
import math
import time

ROOT_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../..")
)

if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from src.services.loader import load_resources
from component.upload import file_upload
from component.detail import author_modal

st.set_page_config(layout="wide")


# 🎨 Custom CSS สำหรับ design ที่อ่านง่าย
st.markdown("""
<style>
    /* ===== Font Size ทั่วไป ===== */
    html, body, [class*="css"] {
        font-family: 'Sarabun', sans-serif;
        background: #0E1117;
        color: #F5F7FA;
        font-size: 22px;
        line-height: 1.7;
    }
    
    /* ===== Header ===== */
    h1 {
        font-size: 32px !important;
        font-weight: 600 !important;
    }
    h2, .stMarkdown h3 {
        font-size: 24px !important;
        font-weight: 500 !important;
    }
    
/* ===== ปุ่ม Card นักวิจัย ===== */
    .stButton > button {
        font-size: 18px !important;
        padding: 1rem 1.5rem !important;
        border-radius: 12px !important;
        
        /* ใช้ตัวแปรสีจาก Theme ของ Streamlit */
        border: 1px solid rgba(128, 128, 128, 0.2) !important; 
        background-color: var(--secondary-background-color) !important;
        color: var(--text-color) !important;
        
        transition: all 0.2s ease !important;
        min-height: 80px !important;
        width: 100% !important;
    }

    .stButton > button:hover {
        border-color: #4a90d9 !important;
        background-color: var(--background-color) !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1) !important;
    }
    
    /* ===== Search Box ===== */
    .stTextInput input {
        font-size: 18px !important;
        padding: 0.75rem 1rem !important;
        border-radius: 10px !important;
    }
    
    /* ===== Table ===== */
    .stDataFrame {
        font-size: 16px !important;
    }
    .stDataFrame th {
        font-size: 16px !important;
        font-weight: 600 !important;
        background: #f5f5f5 !important;
    }
    .stDataFrame td {
        padding: 0.75rem !important;
    }
    
    /* ===== Status Messages ===== */
    .stAlert {
        font-size: 16px !important;
        padding: 1rem !important;
        border-radius: 8px !important;
    }
    
    /* ===== Number Input (Pagination) ===== */
    .stNumberInput label {
        font-size: 16px !important;
    }
    .stNumberInput input {
        font-size: 18px !important;
    }
</style>
""", unsafe_allow_html=True)



# =========================
# 🚀 STARTUP LOADER (มี STEP)
# =========================
def startup_loader():
    progress = st.progress(0)
    status = st.empty()

    status.info("🔄 Step 1/2: Loading model...")
    progress.progress(30)

    res = load_resources()

    progress.progress(100)

    if res["errors"]:
        for e in res["errors"]:
            status.error(e)
        st.stop()

    status.success(
        f"✅ Ready | Model {res['model_load_seconds']}s | Tax {res['taxonomy_load_seconds']}s"
    )

    return res


# =========================
# 🧠 INIT RESOURCE (ครั้งเดียว)
# =========================
@st.cache_resource(show_spinner=False)
def get_resources():
    return load_resources()


resources = get_resources()

# store to session_state
if "resources" not in st.session_state:
    st.session_state["resources"] = resources

# =========================
# 📂 LOAD DATA (แก้ path)
# =========================
DATA_PATH = os.path.join("storage", "raw_data", "data_api.csv")

if not os.path.exists(DATA_PATH):
    st.error(f"❌ ไม่พบไฟล์: {DATA_PATH}")
    st.stop()

@st.cache_data(show_spinner=False)
def load_data(path):
    return pd.read_csv(path)

df = load_data(DATA_PATH)

# =========================
# 🧠 SESSION STATE
# =========================
if "selected_author" not in st.session_state:
    st.session_state.selected_author = None

if "page" not in st.session_state:
    st.session_state.page = 1


# 🧭 HEADER
st.markdown("""
<div style="
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 2rem;
    border-radius: 16px;
    margin-bottom: 2rem;
">
    <h1 style="color: white; margin: 0; font-size: 28px;">
        📊 ระบบวิเคราะห์ความเชี่ยวชาญจากงานวิจัย
    </h1>
    <p style="color: rgba(255,255,255,0.8); margin-top: 0.5rem; font-size: 18px;">
        ค้นหาและวิเคราะห์ผู้เชี่ยวชาญตามสาขาวิจัย
    </p>
</div>
""", unsafe_allow_html=True)
col1, col2 = st.columns([3, 1])
with col1:
    search = st.text_input(
        "🔍 ค้นหา", 
        placeholder="ชื่อนักวิจัย, สาขา, โดเมน...",
        label_visibility="collapsed"
    )
with col2:
    file_upload_com = file_upload(resources)
    if file_upload_com is not None:
        df = file_upload_com.copy()  # อัปเดต df ด้วยข้อมูลใหม่จากการอัปโหลด
        df.to_csv(DATA_PATH, index=False)  # บันทึกข้อมูลใหม่ลงไฟล์
        st.cache_data.clear()  # ล้าง cache เพื่อให้โหลดข้อมูลใหม่

# =========================
# 🔎 FILTER
# =========================
filtered = df.copy()

for col in ["author_name", "l1_field", "l2_domain"]:
    if col in filtered.columns:
        filtered[col] = filtered[col].astype(str)

if search:
    filtered = filtered[
        filtered["author_name"].str.contains(search, case=False, na=False)
        | filtered["l1_field"].str.contains(search, case=False, na=False)
        | filtered["l2_domain"].str.contains(search, case=False, na=False)
    ]
    st.session_state.page = 1


# =========================
# 📄 PAGINATION
# =========================
page_size = 16
total_pages = max(math.ceil(len(filtered) / page_size), 1)
page = st.number_input(f"หน้า", 1, total_pages, value=st.session_state.page)
st.session_state.page = page
# แสดงข้อความบอกจำนวนหน้าและรายการ
st.markdown(f"""
    <div style='text-align: right; color: #64748B; font-size: 14px;'>
        หน้า {page} จากทั้งหมด {total_pages} หน้า
        <br>(รวม {len(filtered)} รายการ)
    </div>
""", unsafe_allow_html=True)
st.session_state.page = page
page_data = filtered.iloc[(page - 1) * page_size : page * page_size].groupby("author_name").first().reset_index()


# =========================
# 🧱 GRID
# =========================
# 🧱 GRID
st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)

cols = st.columns(4, gap="medium")

for i, (_, row) in enumerate(page_data.iterrows()):
    with cols[i % 4]:
        # Card with more info
        author = row['author_name']
        field = row.get('l1_field', '-')
        
        if st.button(
            f"👤 {author}",
            key=f"card_{i}",
            use_container_width=True
        ):
            st.session_state.selected_author = row.to_dict()



# =========================
# 👤 MODAL FUNCTION
# =========================
if st.session_state.selected_author:
    author_modal(df)

# =========================
# 📊 TABLE
# =========================
if len(filtered) == 0:
    st.warning("ไม่พบข้อมูล")
else:
    st.dataframe(filtered, use_container_width=True)
    
csv_data = filtered.to_csv(index=False).encode("utf-8-sig")

st.download_button(
    label="📥 ดาวน์โหลดข้อมูล (CSV)",
    data=csv_data,
    file_name="data.csv",
    mime="text/csv"
)