import os
import time
import torch
import pandas as pd
import streamlit as st
from sentence_transformers import SentenceTransformer

# ================= CONFIG =================
BASE_DIR = r"..\SF342\Program\SF342\BACK"
MODEL_DIR = os.path.join(BASE_DIR, "model_cache")
SPECIFIC_MODEL_PATH = os.path.join(
    MODEL_DIR,
    "models--sentence-transformers--all-MiniLM-L6-v2"
)
TAXONOMY_PATH = os.path.join(
    BASE_DIR, "analytics",
    "drive-download-20260206T091016Z-1-001",
    "keyword_dictionary_10000.csv"
)
MODEL_NAME = "all-MiniLM-L6-v2"


# ================= UTILS =================
def normalize_text(text):
    return str(text).lower().strip()


def resolve_taxonomy_path() -> str:
    env_path = os.getenv("TAXONOMY_PATH")
    if env_path and os.path.exists(env_path):
        return env_path
    if os.path.exists(TAXONOMY_PATH):
        return TAXONOMY_PATH
    project_root = os.path.dirname(BASE_DIR)
    for root in [BASE_DIR, project_root]:
        for dirpath, _, filenames in os.walk(root):
            if "keyword_dictionary_10000.csv" in filenames:
                return os.path.join(dirpath, "keyword_dictionary_10000.csv")
    raise RuntimeError("Taxonomy file NOT FOUND.")


# ================= STARTUP LOADER =================
# ใช้ @st.cache_resource เพื่อ load ครั้งเดียวตลอด session (เหมือน lifespan ของ FastAPI)
@st.cache_resource(show_spinner=False)
def load_resources():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    result = {
        "model": None,
        "tax_embeddings": None,
        "df_tax": None,
        "model_load_seconds": None,
        "taxonomy_load_seconds": None,
        "startup_total_seconds": None,
        "device": device,
        "errors": []
    }
    startup_t0 = time.time()

    # --- STEP 1: Load Model ---
    step1_t0 = time.time()
    try:
        model = SentenceTransformer(MODEL_NAME, device=device, cache_folder=MODEL_DIR)
        result["model"] = model
        result["model_load_seconds"] = round(time.time() - step1_t0, 3)
    except Exception as e:
        result["errors"].append(f"Model load failed: {e}")
        result["startup_total_seconds"] = round(time.time() - startup_t0, 3)
        return result

    # --- STEP 2: Load Taxonomy ---
    step2_t0 = time.time()
    try:
        path = resolve_taxonomy_path()
        df_tax = pd.read_csv(path)
        df_tax["keyword_norm"] = df_tax["keyword_norm"].fillna("").apply(normalize_text)
        texts = df_tax["keyword_norm"].tolist()

        embeddings = model.encode(
            texts,
            batch_size=512,
            show_progress_bar=False,  # ปิดใน Streamlit เพราะ tqdm ไม่ render ใน UI
            convert_to_tensor=True,
            normalize_embeddings=True
        )
        result["df_tax"] = df_tax
        result["tax_embeddings"] = embeddings
        result["taxonomy_load_seconds"] = round(time.time() - step2_t0, 3)
    except Exception as e:
        result["errors"].append(f"Taxonomy load failed: {e}")

    result["startup_total_seconds"] = round(time.time() - startup_t0, 3)
    return result


# ================= MAIN APP =================
st.set_page_config(page_title="SF342 System", layout="wide")

# Load ครั้งเดียว (cached)
with st.spinner("⏳ Loading model and taxonomy... please wait"):
    resources = load_resources()

# เก็บลง session_state เพื่อให้ทุกหน้าเข้าถึงได้
if "resources" not in st.session_state:
    st.session_state["resources"] = resources

# แสดง error ถ้ามี
if resources["errors"]:
    for err in resources["errors"]:
        st.error(f"❌ {err}")
    st.stop()

# ================= NAVIGATION =================
main_page = st.Page("main_page.py", title="Main Page", icon="🎈")
page_2    = st.Page("page_2.py",    title="Page 2",    icon="❄️")
page_3    = st.Page("page_3.py",    title="Page 3",    icon="🎉")

pg = st.navigation([main_page, page_2, page_3])
pg.run()