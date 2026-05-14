import sys
import os
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
import pandas as pd
import math
import time
import ast

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
DATA_PATH = os.path.join("FrontIII/storage", "raw_data", "data_api.csv")

if not os.path.exists(DATA_PATH):
    st.error(f"❌ ไม่พบไฟล์: {DATA_PATH}")
    st.stop()

@st.cache_data(show_spinner=False)
def load_data(path):
    return pd.read_csv(path)

df = load_data(DATA_PATH)


def get_taxonomy_reference_path() -> str:
    candidates = [
        os.path.join(
            "storage",
            "drive-download-20260206T091016Z-1-001",
            "keyword_dictionary_10000.csv",
        ),
        r"FrontIII/storage/drive-download-20260206T091016Z-1-001/keyword_dictionary_10000.csv",
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    raise FileNotFoundError("ไม่พบไฟล์ keyword_dictionary_10000.csv")


@st.cache_data(show_spinner=False)
def load_taxonomy_data() -> pd.DataFrame:
    tax_path = get_taxonomy_reference_path()
    tax_df = pd.read_csv(tax_path)
    cols = ["taxonomy_id", "l1_field", "l2_domain", "subfield_name"]
    existing = [c for c in cols if c in tax_df.columns]
    return tax_df[existing].drop_duplicates(subset=["taxonomy_id"])


@st.cache_data(show_spinner=False)
def prepare_taxonomy_summary(df_data: pd.DataFrame, tax_df: pd.DataFrame) -> pd.DataFrame:
    if df_data.empty:
        out = tax_df.copy()
        out["researcher_count"] = 0
        out["paper_count"] = 0
        out["has_data"] = False
        return out

    agg = (
        df_data.groupby("taxonomy_id", as_index=False)
        .agg(
            researcher_count=("author_id", "nunique"),
            paper_count=("paper_count", "sum"),
        )
        .fillna(0)
    )
    out = tax_df.merge(agg, on="taxonomy_id", how="left").fillna(0)
    out["researcher_count"] = out["researcher_count"].astype(int)
    out["paper_count"] = out["paper_count"].astype(int)
    out["has_data"] = out["researcher_count"] > 0
    return out.sort_values(
        by=["has_data", "researcher_count", "paper_count"],
        ascending=[False, False, False],
    ).reset_index(drop=True)


def parse_list(value):
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return []
    if isinstance(value, list):
        return [str(v) for v in value if str(v).strip()]
    text = str(value).strip()
    if not text:
        return []
    try:
        parsed = ast.literal_eval(text)
        if isinstance(parsed, list):
            return [str(v) for v in parsed if str(v).strip()]
    except (SyntaxError, ValueError):
        pass
    return [x.strip() for x in text.split(";") if x.strip()]


def render_researcher_modal(row: pd.Series):
    @st.dialog("👨‍🔬 รายละเอียดนักวิจัย", width="large")
    def _modal():
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Expertise", f"{float(row.get('expertise_score', 0.0)):.3f}")
        c2.metric("Paper", int(row.get("paper_count", 0)))
        c3.metric("First Author", int(row.get("first_author_papers", 0)))
        c4.metric("Corresponding", int(row.get("corresponding_papers", 0)))

        for field in [
            "author_id",
            "author_name",
            "taxonomy_id",
            "l1_field",
            "l2_domain",
            "subfield_name",
            "author_papers",
            "avg_similarity",
            "profile",
        ]:
            st.markdown(f"**{field}:** {row.get(field, '-')}")

        with st.expander("📄 Evidence Titles"):
            titles = parse_list(row.get("evidence_titles"))
            if not titles:
                st.caption("ไม่มีข้อมูล")
            for t in titles:
                st.markdown(f"- {t}")

    _modal()

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
        | filtered["evidence_paper_ids"].str.contains(search, case=False, na=False)
    ]
    st.session_state.page = 1


# # =========================
# # 📄 PAGINATION
# # =========================
# page_size = 16
# total_pages = max(math.ceil(len(filtered.groupby("author_name")) / page_size), 1)
# page = st.number_input(f"หน้า", 1, total_pages, value=st.session_state.page)
# st.session_state.page = page
# # แสดงข้อความบอกจำนวนหน้าและรายการ
# st.markdown(f"""
#     <div style='text-align: right; color: #64748B; font-size: 14px;'>
#         หน้า {page} จากทั้งหมด {total_pages} หน้า
#         <br>(รวม {len(filtered)} รายการ)
#     </div>
# """, unsafe_allow_html=True)
# st.session_state.page = page
# page_data = filtered.iloc[(page - 1) * page_size : page * page_size].groupby("author_name").first().reset_index()


# =========================
# 📄 PAGINATION
# =========================

page_size = 16

# จำนวนคนทั้งหมด
total_people = filtered["author_name"].nunique()

# จำนวนหน้า
total_pages = max(
    math.ceil(total_people / page_size),
    1
)

# current page
page = st.number_input(
    "หน้า",
    min_value=1,
    max_value=total_pages,
    value=st.session_state.page,
    step=1
)

st.session_state.page = page

# =========================
# GROUP AUTHORS
# =========================

grouped_data = (
    filtered
    .groupby("author_name")
    .first()
    .reset_index()
)

# pagination
start_idx = (page - 1) * page_size
end_idx = page * page_size

page_data = grouped_data.iloc[start_idx:end_idx]

# จำนวนคนที่กำลังแสดง
showing_people = len(page_data)

# =========================
# INFO
# =========================

st.markdown(
    f"""
    <div style='text-align: right; color: #64748B; font-size: 14px;'>
        แสดง {showing_people} คน
        <br>
        จากทั้งหมด {total_people} คน
    </div>
    """,
    unsafe_allow_html=True
)


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
if st.session_state.get("selected_author") is not None:

    selected = st.session_state.selected_author

    # clear state ก่อน
    st.session_state.selected_author = None

    author_modal(df, selected)


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


def render_taxonomy_cards(summary_df: pd.DataFrame, df_filtered: pd.DataFrame) -> None:
    st.markdown("### 🌳 แผนผัง Taxonomy ความเชี่ยวชาญ")
    if summary_df.empty:
        st.info("ไม่พบ taxonomy สำหรับแสดงผล")
        return

    cards_per_row = 3
    visible_limit = st.slider("จำนวน Taxonomy ที่แสดง", min_value=6, max_value=min(120, len(summary_df)), value=min(24, len(summary_df)), step=3)
    view_df = summary_df.head(visible_limit)

    for i in range(0, len(view_df), cards_per_row):
        cols = st.columns(cards_per_row, gap="large")
        for j, (_, row) in enumerate(view_df.iloc[i : i + cards_per_row].iterrows()):
            with cols[j]:
                has_data = bool(row.get("has_data", False))
                card_class = "glass-card" if has_data else "glass-card muted-card"
                st.markdown(
                    f"""
                    <div class="{card_class}">
                        <div class="taxonomy-title">{row.get("subfield_name", "-")}</div>
                        <div style="margin-bottom:0.45rem;">
                            <span class="meta-badge">Field: {row.get("l1_field", "-")}</span>
                            <span class="meta-badge">Domain: {row.get("l2_domain", "-")}</span>
                            <span class="meta-badge">ID: {row.get("taxonomy_id", "-")}</span>
                        </div>
                        <div>👨‍🔬 นักวิจัย: <b>{int(row.get("researcher_count", 0))}</b></div>
                        <div>📄 บทความ: <b>{int(row.get("paper_count", 0)):,}</b></div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                if st.button("ดูรายละเอียด Taxonomy", key=f"tax_btn_{row['taxonomy_id']}", use_container_width=True, type="primary" if has_data else "secondary"):
                    st.session_state["selected_taxonomy"] = row["taxonomy_id"]

    selected = st.session_state.get("selected_taxonomy")
    if selected:
        tax_rows = df_filtered[df_filtered["taxonomy_id"] == selected].sort_values("expertise_score", ascending=False)
        info_row = summary_df[summary_df["taxonomy_id"] == selected].head(1)
        if not info_row.empty:
            st.markdown("---")
            st.subheader(f"รายละเอียด Taxonomy: {info_row.iloc[0]['subfield_name']}")
            st.caption(f"{info_row.iloc[0]['l1_field']}  >  {info_row.iloc[0]['l2_domain']}  >  {info_row.iloc[0]['subfield_name']}")

        if tax_rows.empty:
            st.info("taxonomy นี้ยังไม่มีนักวิจัยในข้อมูลปัจจุบัน")
            return

        max_show = 20
        top_rows = tax_rows.head(max_show)
        for idx, (_, r) in enumerate(top_rows.iterrows()):
            c1, c2 = st.columns([4, 1])
            with c1:
                st.markdown(f"**{idx + 1}. {r.get('author_name', '-')}**  |  Expertise: `{float(r.get('expertise_score', 0.0)):.3f}`  | Papers: `{int(r.get('paper_count', 0))}`")
            with c2:
                if st.button("เปิดโปรไฟล์", key=f"researcher_modal_{selected}_{idx}", use_container_width=True):
                    render_researcher_modal(r)

        remaining = len(tax_rows) - len(top_rows)
        if remaining > 0:
            with st.expander(f"ดูเพิ่มเติมอีก {remaining} คน"):
                for idx, (_, r) in enumerate(tax_rows.iloc[max_show:].iterrows()):
                    c1, c2 = st.columns([4, 1])
                    with c1:
                        st.markdown(f"- {r.get('author_name', '-')} | Score `{float(r.get('expertise_score', 0.0)):.3f}`")
                    with c2:
                        if st.button("รายละเอียด", key=f"researcher_more_modal_{selected}_{idx}", use_container_width=True):
                            render_researcher_modal(r)


@st.cache_resource(show_spinner=False)
def get_sentence_model():
    try:
        from sentence_transformers import SentenceTransformer
    except Exception:
        return None
    return SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")


@st.cache_data(show_spinner=False)
def get_taxonomy_embeddings(taxonomy_texts: Tuple[str, ...]) -> Optional[np.ndarray]:
    model = get_sentence_model()
    if model is None:
        return None
    embeds = model.encode(list(taxonomy_texts), normalize_embeddings=True, convert_to_numpy=True, show_progress_bar=False)
    return embeds.astype(np.float32, copy=False)


def calculate_similarity(query_text: str, taxonomy_texts: List[str]) -> Optional[np.ndarray]:
    model = get_sentence_model()
    if model is None or not query_text.strip():
        return None
    tax_emb = get_taxonomy_embeddings(tuple(taxonomy_texts))
    if tax_emb is None:
        return None
    q_emb = model.encode([query_text], normalize_embeddings=True, convert_to_numpy=True, show_progress_bar=False).astype(np.float32)
    sim = np.dot(tax_emb, q_emb[0])
    return sim


def render_top_matches(top_df: pd.DataFrame, filtered_df: pd.DataFrame) -> None:
    st.markdown("#### ผลการจับคู่ Taxonomy")
    cols = st.columns(min(3, max(1, len(top_df))))
    for idx, (_, row) in enumerate(top_df.iterrows()):
        with cols[idx % len(cols)]:
            confidence = float(row["similarity"]) * 100
            st.markdown(
                f"""
                <div class="glass-card">
                    <div class="taxonomy-title">{row['subfield_name']}</div>
                    <div><span class="meta-badge">{row['l1_field']}</span><span class="meta-badge">{row['l2_domain']}</span></div>
                    <div>Taxonomy: <b>{row['taxonomy_id']}</b></div>
                    <div>ความมั่นใจ: <b>{confidence:.2f}%</b></div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("#### นักวิจัยที่เกี่ยวข้อง")
    match_ids = top_df["taxonomy_id"].tolist()
    recs = (
        filtered_df[filtered_df["taxonomy_id"].isin(match_ids)]
        .sort_values(["expertise_score", "paper_count"], ascending=False)
        .drop_duplicates(subset=["author_id"])
        .head(12)
    )
    if recs.empty:
        st.warning("ยังไม่พบนักวิจัยที่เกี่ยวข้องในเงื่อนไขตัวกรองปัจจุบัน")
        return

    for i, (_, r) in enumerate(recs.iterrows()):
        c1, c2 = st.columns([4, 1])
        with c1:
            st.markdown(
                f"**{r.get('author_name', '-')}** | {r.get('subfield_name', '-')} | "
                f"Expertise `{float(r.get('expertise_score', 0.0)):.3f}`"
            )
            with st.expander(f"ดู Evidence: {r.get('author_name', '-')}"):
                for title in parse_list(r.get("evidence_titles"))[:8]:
                    st.markdown(f"- {title}")
        with c2:
            if st.button("ดูข้อมูล", key=f"ai_modal_{i}", use_container_width=True):
                render_researcher_modal(r)


def render_ai_matching(df_filtered: pd.DataFrame, summary_df: pd.DataFrame) -> None:
    st.title("เทียบ Taxonomy")
    user_idea = st.text_area(
        "เนื้อหางานวิจัยของคุณ",
        placeholder="เช่น งานวิจัยเรื่องการใช้ AI วิเคราะห์โรคพืชจากภาพถ่าย...",
        height=130,
    )
    run = st.button("🔍 วิเคราะห์งานวิจัย", type="primary", use_container_width=True)
    if not run:
        return
    if not user_idea.strip():
        st.warning("กรุณากรอกแนวคิดวิจัยก่อนวิเคราะห์")
        return

    taxonomy_texts = (
        summary_df["l1_field"].fillna("").astype(str)
        + " | "
        + summary_df["l2_domain"].fillna("").astype(str)
        + " | "
        + summary_df["subfield_name"].fillna("").astype(str)
    ).tolist()
    with st.spinner("กำลังวิเคราะห์ความใกล้เคียงด้วย embedding similarity..."):
        sim = calculate_similarity(user_idea, taxonomy_texts)

    if sim is None:
        st.error("ไม่สามารถโหลด sentence-transformers ได้ในสภาพแวดล้อมนี้")
        return

    ranked = summary_df.copy()
    ranked["similarity"] = sim
    top_df = ranked.sort_values("similarity", ascending=False).head(3)
    render_top_matches(top_df, df_filtered)

with st.spinner("กำลังเตรียมข้อมูล taxonomy และ researcher..."):
    tax_df = load_taxonomy_data()
    summary_df = prepare_taxonomy_summary(df, tax_df)

render_ai_matching(filtered, summary_df)
