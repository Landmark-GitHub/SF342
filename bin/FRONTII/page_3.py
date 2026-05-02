import streamlit as st
import pandas as pd
import ast
import os

# ดึง resources ที่ load ไว้แล้ว
res = st.session_state["resources"]
model          = res["model"]
tax_embeddings = res["tax_embeddings"]
df_tax         = res["df_tax"]

st.write(f"✅ Model ready: {model is not None}")
st.write(f"✅ Taxonomy rows: {len(df_tax)}")
st.write(f"⏱ Startup time: {res['startup_total_seconds']}s")

# ══════════════════════════════════════════════════════════════════
# โหลดข้อมูล
# ══════════════════════════════════════════════════════════════════
STORAGE_PATH = os.path.join("Storage", "data_api.csv")

@st.cache_data
def load_initial_data():
    if os.path.exists(STORAGE_PATH):
        try:
            return pd.read_csv(STORAGE_PATH)
        except Exception:
            pass
    try:
        from data_raw import load_data
        return load_data()
    except Exception:
        st.error("ไม่พบไฟล์ข้อมูล กรุณาตรวจสอบ Storage/data_api.csv หรือ data_raw.py")
        return pd.DataFrame()