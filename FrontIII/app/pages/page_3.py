import ast
import os
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(layout="wide")

PRIMARY = "#667eea"
SECONDARY = "#764ba2"


def inject_css() -> None:
    st.markdown(
        f"""
        <style>
        html, body, [class*="css"] {{
            font-family: "Sarabun", "Prompt", sans-serif;
            font-family: 'Sarabun', sans-serif;
            background: #0E1117;
            color: #F5F7FA;
            font-size: 22px;
            line-height: 1.7;
        }}
        .hero {{
            background: linear-gradient(135deg, {PRIMARY} 0%, {SECONDARY} 100%);
            border-radius: 20px;
            padding: 1.25rem 1.4rem;
            color: white;
            box-shadow: 0 14px 34px rgba(102, 126, 234, 0.25);
            margin-bottom: 1rem;
        }}
        .glass-card {{
            background: rgba(255, 255, 255, 0.08);
            border: 1px solid rgba(255, 255, 255, 0.20);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 0.95rem;
            box-shadow: 0 10px 24px rgba(0,0,0,0.10);
            transition: transform 0.25s ease, box-shadow 0.25s ease, border-color 0.25s ease;
            height: 100%;
        }}
        .glass-card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 16px 30px rgba(95, 112, 196, 0.25);
            border-color: rgba(102, 126, 234, 0.45);
        }}
        .muted-card {{
            opacity: 0.86;
            border-color: rgba(140, 140, 140, 0.35);
            background: rgba(120, 120, 120, 0.09);
        }}
        .meta-badge {{
            display: inline-block;
            background: rgba(255, 255, 255, 0.20);
            border: 1px solid rgba(255,255,255,0.35);
            border-radius: 999px;
            padding: 0.18rem 0.65rem;
            margin-right: 0.4rem;
            margin-bottom: 0.35rem;
            font-size: 0.8rem;
        }}
        .taxonomy-title {{
            font-size: 1.03rem;
            font-weight: 700;
            margin-bottom: 0.25rem;
        }}
        .scroll-chip {{
            max-height: 155px;
            overflow-y: auto;
            border: 1px solid rgba(128, 128, 128, 0.2);
            border-radius: 12px;
            padding: 0.5rem;
            background: rgba(255,255,255,0.04);
        }}
        @media (max-width: 900px) {{
            .hero {{ padding: 1rem; }}
            .glass-card {{ border-radius: 16px; }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def get_taxonomy_reference_path() -> str:
    candidates = [
        r"SF342/Program/SF342/FrontIII/storage/drive-download-20260206T091016Z-1-001/keyword_dictionary_10000.csv",
        os.path.join(
            "storage",
            "drive-download-20260206T091016Z-1-001",
            "keyword_dictionary_10000.csv",
        ),
        os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "storage",
            "drive-download-20260206T091016Z-1-001",
            "keyword_dictionary_10000.csv",
        ),
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    raise FileNotFoundError("ไม่พบไฟล์ keyword_dictionary_10000.csv")


@st.cache_data(show_spinner=False)
def load_taxonomy_data() -> pd.DataFrame:
    path = get_taxonomy_reference_path()
    tax_df = pd.read_csv(path)
    keep_cols = ["taxonomy_id", "l1_field", "l2_domain", "subfield_name", "keyword_norm"]
    existing = [col for col in keep_cols if col in tax_df.columns]
    tax_df = tax_df[existing].copy()
    return tax_df


@st.cache_data(show_spinner=False)
def prepare_taxonomy_summary(df_data: pd.DataFrame, tax_df: pd.DataFrame) -> pd.DataFrame:
    base_tax = (
        tax_df[["taxonomy_id", "l1_field", "l2_domain", "subfield_name"]]
        .drop_duplicates(subset=["taxonomy_id"])
        .copy()
    )
    if df_data.empty:
        base_tax["researcher_count"] = 0
        base_tax["paper_count"] = 0
        base_tax["has_data"] = False
        return base_tax.sort_values(["has_data", "l1_field"], ascending=[False, True]).reset_index(drop=True)

    agg = (
        df_data.groupby("taxonomy_id", as_index=False)
        .agg(
            researcher_count=("author_id", "nunique"),
            paper_count=("paper_count", "sum"),
        )
        .fillna(0)
    )
    merged = base_tax.merge(agg, how="left", on="taxonomy_id")
    merged["researcher_count"] = merged["researcher_count"].fillna(0).astype(int)
    merged["paper_count"] = merged["paper_count"].fillna(0).astype(int)
    merged["has_data"] = merged["researcher_count"] > 0
    merged = merged.sort_values(
        by=["has_data", "researcher_count", "paper_count", "l1_field", "l2_domain", "subfield_name"],
        ascending=[False, False, False, True, True, True],
    ).reset_index(drop=True)
    return merged


def parse_list(value: Any) -> List[str]:
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
    except (ValueError, SyntaxError):
        pass
    return [chunk.strip() for chunk in text.split(";") if chunk.strip()]


def render_researcher_modal(row: pd.Series) -> None:
    @st.dialog("👨‍🔬 รายละเอียดนักวิจัย", width="large")
    def _dialog() -> None:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Expertise Score", f"{float(row.get('expertise_score', 0.0)):.3f}")
        c2.metric("Paper Count", int(row.get("paper_count", 0)))
        c3.metric("First Author", int(row.get("first_author_papers", 0)))
        c4.metric("Corresponding", int(row.get("corresponding_papers", 0)))

        detail_cols = [
            "author_id",
            "author_name",
            "taxonomy_id",
            "l1_field",
            "l2_domain",
            "subfield_name",
            "expertise_score",
            "paper_count",
            "first_author_papers",
            "corresponding_papers",
            "author_papers",
            "avg_similarity",
            "profile",
            "link",
        ]
        view_data = {col: row.get(col, "-") for col in detail_cols}
        st.dataframe(pd.DataFrame(view_data.items(), columns=["หัวข้อ", "ข้อมูล"]), use_container_width=True, hide_index=True)

        ids = parse_list(row.get("evidence_paper_ids"))
        titles = parse_list(row.get("evidence_titles"))

        st.markdown("#### โปรไฟล์")
        st.markdown(
            f"""
            <div class="glass-card">
                {str(row.get("profile", "ไม่มีข้อมูล"))}
            </div>
            """,
            unsafe_allow_html=True,
        )
        link = str(row.get("link", "")).strip()
        if link and link.lower() != "nan":
            st.link_button("🔗 เปิดลิงก์โปรไฟล์", link, use_container_width=True)

        with st.expander("📄 หลักฐานเอกสาร (Evidence Titles)"):
            if not titles:
                st.info("ไม่มีชื่อบทความประกอบ")
            for idx, t in enumerate(titles, start=1):
                st.markdown(f"{idx}. {t}")

        st.markdown("#### Evidence Paper IDs")
        if ids:
            id_text = "<br>".join(ids)
            st.markdown(
                f"""
                <div class="scroll-chip">
                    {id_text}
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.info("ไม่พบ Evidence Paper IDs")

    _dialog()


def render_filters(df_data: pd.DataFrame) -> pd.DataFrame:
    c1, c2, c3, c4 = st.columns([1.1, 1.1, 1.1, 2.2])
    fields = ["ทั้งหมด"] + sorted(df_data["l1_field"].dropna().astype(str).unique().tolist())
    domains = ["ทั้งหมด"] + sorted(df_data["l2_domain"].dropna().astype(str).unique().tolist())
    subs = ["ทั้งหมด"] + sorted(df_data["subfield_name"].dropna().astype(str).unique().tolist())

    with c1:
        f1 = st.selectbox("Field", fields, index=0)
    with c2:
        f2 = st.selectbox("Domain", domains, index=0)
    with c3:
        f3 = st.selectbox("Subdomain", subs, index=0)
    with c4:
        q = st.text_input("ค้นหา (นักวิจัย / taxonomy / keyword)", placeholder="เช่น chemistry, machine learning, ชื่อนักวิจัย")

    filtered = df_data.copy()
    if f1 != "ทั้งหมด":
        filtered = filtered[filtered["l1_field"] == f1]
    if f2 != "ทั้งหมด":
        filtered = filtered[filtered["l2_domain"] == f2]
    if f3 != "ทั้งหมด":
        filtered = filtered[filtered["subfield_name"] == f3]

    if q:
        query = q.strip().lower()
        text_cols = ["author_name", "taxonomy_id", "l1_field", "l2_domain", "subfield_name", "evidence_titles"]
        text_df = filtered[text_cols].fillna("").astype(str)
        mask = np.column_stack([text_df[col].str.lower().str.contains(query, regex=False) for col in text_cols]).any(axis=1)
        filtered = filtered[mask]

    return filtered


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
    st.markdown("### 🤖 AI Research Matching Assistant")
    st.info(
        "ตอนนี้ท่านทำวิจัยอะไรอยู่ครับ\n"
        "บอกคร่าว ๆ ได้ไหมครับ\n"
        "เดี๋ยวระบบจะช่วยค้นหางานวิจัยและนักวิจัยที่เกี่ยวข้องให้"
    )
    user_idea = st.text_area(
        "แนวคิดวิจัยของท่าน",
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


def main() -> None:
    inject_css()
    st.markdown(
        """
        <div class="hero">
            <h2 style="margin:0;">📌 การแยกความเชี่ยวชาญ</h2>
            <p style="margin:0.35rem 0 0 0;">ระบบสำรวจ Taxonomy ความเชี่ยวชาญ พร้อมค้นหาและจับคู่นักวิจัยแบบอัจฉริยะ</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if "global_data" not in st.session_state:
        st.error("ไม่พบข้อมูลกลางของระบบ (st.session_state.global_data)")
        st.stop()

    gdata = st.session_state.global_data
    df_raw = gdata.get("df_raw", pd.DataFrame()).copy()
    if df_raw.empty:
        st.warning("ยังไม่มีข้อมูลนักวิจัยในระบบ กรุณาอัปโหลดข้อมูลที่หน้าแรก")
        st.stop()

    with st.spinner("กำลังเตรียมข้อมูล taxonomy และ researcher..."):
        tax_df = load_taxonomy_data()
        summary_df = prepare_taxonomy_summary(df_raw, tax_df)

    st.sidebar.markdown("## 🧭 เมนูนำทาง")
    section = st.sidebar.radio(
        "เลือกส่วนที่ต้องการดู",
        ["ทั้งหมด", "Taxonomy", "ค้นหา/Filter", "AI Matching"],
        index=0,
    )

    filtered_df = render_filters(df_raw)
    st.caption(f"ผลลัพธ์หลังกรอง: {len(filtered_df):,} แถวข้อมูล")

    if filtered_df.empty:
        st.markdown(
            """
            <div class="glass-card muted-card">
                <h4 style="margin-top:0;">ไม่พบข้อมูลตามเงื่อนไขที่เลือก</h4>
                <p>ลองปรับตัวกรองใหม่ หรือเคลียร์คำค้นหาเพื่อดูข้อมูลทั้งหมด</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    if section in ("ทั้งหมด", "Taxonomy"):
        render_taxonomy_cards(summary_df, filtered_df)
    if section in ("ทั้งหมด", "AI Matching"):
        st.markdown("---")
        render_ai_matching(filtered_df, summary_df)


if __name__ == "__main__":
    main()
