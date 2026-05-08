import streamlit as st
import pandas as pd
import ast


@st.dialog("ข้อมูลนักวิจัย", width="large")
def author_modal(df, selected_author):

    a = selected_author
    if not a:
        return

    # ── inject CSS ────────────────────────────────────────────────────────────
    st.markdown("""
    <style>
    /* base font */
    .author-modal-wrap { font-size: 16px; line-height: 1.7; }

    /* header card */
    .profile-header {
        background: linear-gradient(135deg, #1a1f3c 0%, #0d2137 100%);
        border: 1px solid #2e4a6e;
        border-radius: 14px;
        padding: 20px 24px;
        margin-bottom: 8px;
    }
    .profile-name {
        font-size: 24px;
        font-weight: 700;
        color: #e8f4fd;
        margin: 0 0 4px 0;
    }
    .profile-meta {
        font-size: 14px;
        color: #8ab4d4;
        margin: 2px 0;
    }

    /* metric card */
    .metric-card {
        background: #111827;
        border: 1px solid #1e3a5f;
        border-radius: 12px;
        padding: 16px;
        text-align: center;
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-3px);
        border-color: #3b82f6;
    }
    .metric-value {
        font-size: 28px;
        font-weight: 700;
        color: #60a5fa;
        display: block;
    }
    .metric-label {
        font-size: 13px;
        color: #94a3b8;
        margin-top: 4px;
    }

    /* role card */
    .role-first  { border-top: 3px solid #22c55e !important; }
    .role-corr   { border-top: 3px solid #f59e0b !important; }
    .role-co     { border-top: 3px solid #8b5cf6 !important; }
    .role-first  .metric-value { color: #22c55e; }
    .role-corr   .metric-value { color: #f59e0b; }
    .role-co     .metric-value { color: #8b5cf6; }

    /* section header */
    .section-title {
        font-size: 17px;
        font-weight: 600;
        color: #cbd5e1;
        border-left: 4px solid #3b82f6;
        padding-left: 10px;
        margin: 20px 0 12px 0;
    }

    /* tag pill */
    .tag-pill {
        display: inline-block;
        background: #1e3a5f;
        color: #93c5fd;
        border-radius: 20px;
        padding: 4px 12px;
        font-size: 13px;
        margin: 3px 4px 3px 0;
        border: 1px solid #2563eb44;
    }
    .tag-domain  { background: #14532d; color: #86efac; border-color: #16a34a44; }
    .tag-subject { background: #1e3a5f; color: #93c5fd; border-color: #2563eb44; }
    .tag-topic   { background: #3b1f5e; color: #c4b5fd; border-color: #7c3aed44; }

    /* publication item */
    .pub-item {
        background: #0f172a;
        border: 1px solid #1e293b;
        border-left: 4px solid #3b82f6;
        border-radius: 8px;
        padding: 14px 16px;
        margin-bottom: 10px;
        transition: border-left-color 0.2s ease;
        font-size: 15px;
    }
    .pub-item:hover { border-left-color: #60a5fa; }
    .pub-number { color: #3b82f6; font-weight: 700; margin-right: 8px; }
    .pub-title  { color: #e2e8f0; line-height: 1.5; }
    .pub-meta   { color: #64748b; font-size: 12px; margin-top: 6px; }
    .pub-link   {
        display: inline-block;
        color: #38bdf8;
        font-size: 12px;
        margin-top: 4px;
        text-decoration: none;
    }
    .pub-link:hover { color: #7dd3fc; text-decoration: underline; }
    </style>
    <div class="author-modal-wrap">
    """, unsafe_allow_html=True)

    # ── load data ─────────────────────────────────────────────────────────────
    author_id = a.get("author_id")
    df_author = df[df["author_id"] == author_id].copy().reset_index(drop=True)

    if df_author.empty:
        st.warning("ไม่พบข้อมูลนักวิจัย")
        return

    first_row   = df_author.iloc[0]
    author_name = first_row.get("author_name", "-")
    affiliation = first_row.get("profile", "-")
    country     = affiliation.split(",")[-1].strip() if isinstance(affiliation, str) and "," in affiliation else "-"

    # ── helper: parse list column ─────────────────────────────────────────────
    def parse_list_col(row, col):
        val = row.get(col, [])
        if isinstance(val, str):
            try:
                val = ast.literal_eval(val)
            except Exception:
                val = [val]
        return val if isinstance(val, list) else []

    # ── parse papers (รวม link) ───────────────────────────────────────────────
    papers = []
    for _, row in df_author.iterrows():
        titles = parse_list_col(row, "evidence_titles")
        eids   = parse_list_col(row, "evidence_paper_ids")
        links  = parse_list_col(row, "link")

        # padding links ให้ยาวเท่า titles เผื่อข้อมูลไม่ครบ
        links += [""] * max(0, len(titles) - len(links))

        for t, e, l in zip(titles, eids, links):
            papers.append({"title": t, "eid": e, "link": l})

    paper_df = pd.DataFrame(papers).drop_duplicates(subset=["eid"]).reset_index(drop=True)
    total_pubs = len(paper_df)

    # ── metrics ───────────────────────────────────────────────────────────────
    expertise_score     = round(float(df_author["expertise_score"].max()), 1)
    avg_sim             = round(float(df_author["avg_similarity"].fillna(0).mean()), 3)
    first_author_count  = int(df_author["first_author_papers"].fillna(0).sum())
    corresponding_count = int(df_author["corresponding_papers"].fillna(0).sum())
    coauthor_count      = max(total_pubs - first_author_count - corresponding_count, 0)

    domains  = df_author["l1_field"].dropna().unique().tolist()
    subjects = df_author["l2_domain"].dropna().unique().tolist()
    topics   = df_author["subfield_name"].dropna().unique().tolist()
    tax_ids  = df_author["taxonomy_id"].dropna().astype(str).unique().tolist()

    tax_table  = df_author[["taxonomy_id","l1_field","l2_domain","subfield_name"]].drop_duplicates().reset_index(drop=True)
    tax_table.columns = ["รหัส Taxonomy", "สาขาหลัก", "กลุ่มวิชา", "หัวข้อวิจัย"]

    top_domains = (
        df_author.groupby("l2_domain")["expertise_score"]
        .sum().sort_values(ascending=False).head(5).reset_index()
    )
    top_domains.columns = ["กลุ่มวิชา (l2_domain)", "คะแนนความเชี่ยวชาญ"]

    # =========================================================
    # HEADER
    # =========================================================
    st.markdown(f"""
    <div class="profile-header">
        <div class="profile-name">👤 {author_name}</div>
        <div class="profile-meta">🆔 รหัสนักวิจัย: {author_id} &nbsp;·&nbsp; 📍 ประเทศ: {country}</div>
        <div class="profile-meta">🏛️ สังกัด: {affiliation}</div>
    </div>
    """, unsafe_allow_html=True)

    # =========================================================
    # METRICS
    # =========================================================
    st.markdown('<div class="section-title">📊 ภาพรวมผลงาน</div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    for col, val, label in [
        (c1, total_pubs,       "📄 ผลงานวิจัย"),
        (c2, expertise_score,  "⭐ คะแนนความเชี่ยวชาญ"),
        (c3, avg_sim,          "🎯 ค่าความใกล้เคียงเฉลี่ย"),
        (c4, len(tax_ids),     "🏷️ จำนวน Taxonomy"),
    ]:
        col.markdown(f"""
        <div class="metric-card">
            <span class="metric-value">{val}</span>
            <div class="metric-label">{label}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("")

    # =========================================================
    # AUTHOR ROLE
    # =========================================================
    st.markdown('<div class="section-title">👥 บทบาทในการเขียนบทความ</div>', unsafe_allow_html=True)
    r1, r2, r3 = st.columns(3)
    for col, val, label, cls in [
        (r1, first_author_count,  "✍️ ผู้แต่งหลัก",           "role-first"),
        (r2, corresponding_count, "📬 ผู้ติดต่อประสานงาน",    "role-corr"),
        (r3, coauthor_count,      "🤝 ผู้ร่วมแต่ง",           "role-co"),
    ]:
        col.markdown(f"""
        <div class="metric-card {cls}">
            <span class="metric-value">{val}</span>
            <div class="metric-label">{label}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("")

    # =========================================================
    # RESEARCH AREAS
    # =========================================================
    st.markdown('<div class="section-title">🔬 สาขาความเชี่ยวชาญ</div>', unsafe_allow_html=True)

    domain_tags  = "".join(f'<span class="tag-pill tag-domain">{x}</span>'  for x in domains)
    subject_tags = "".join(f'<span class="tag-pill tag-subject">{x}</span>' for x in subjects)
    topic_tags   = "".join(f'<span class="tag-pill tag-topic">{x}</span>'   for x in topics)

    st.markdown(f"""
    <div style="margin-bottom:10px">
        <div style="font-size:13px;color:#64748b;margin-bottom:6px">🌐 สาขาหลัก</div>
        {domain_tags}
    </div>
    <div style="margin-bottom:10px">
        <div style="font-size:13px;color:#64748b;margin-bottom:6px">🧪 กลุ่มวิชา</div>
        {subject_tags}
    </div>
    <div style="margin-bottom:10px">
        <div style="font-size:13px;color:#64748b;margin-bottom:6px">🧠 หัวข้อวิจัย</div>
        {topic_tags}
    </div>
    """, unsafe_allow_html=True)

    # =========================================================
    # TAXONOMY TABLE
    # =========================================================
    st.markdown('<div class="section-title">🏷️ ตาราง Taxonomy</div>', unsafe_allow_html=True)
    st.dataframe(tax_table, use_container_width=True, hide_index=True)

    # =========================================================
    # TOP DOMAINS
    # =========================================================
    st.markdown('<div class="section-title">🏆 สาขาที่มีความเชี่ยวชาญสูงสุด 5 ลำดับ</div>', unsafe_allow_html=True)
    st.dataframe(top_domains, use_container_width=True, hide_index=True)

    # =========================================================
    # PUBLICATIONS
    # =========================================================
    st.markdown(f'<div class="section-title">📚 รายการผลงานวิจัย ({total_pubs} รายการ)</div>', unsafe_allow_html=True)

    if paper_df.empty:
        st.info("ไม่พบรายการผลงานวิจัย")
    else:
        pub_html = ""
        for i, row in enumerate(paper_df.itertuples(), 1):
            # สร้าง link tag ถ้ามี URL, ถ้าไม่มีแสดง EID อย่างเดียว
            link_html = (
                f'<a class="pub-link" href="{row.link}" target="_blank" rel="noopener noreferrer">'
                f'🔗 เปิดบทความใน Scopus</a>'
                if row.link else ""
            )
            pub_html += f"""
            <div class="pub-item">
                <span class="pub-number">{i}.</span>
                <span class="pub-title">{row.title}</span>
                <div class="pub-meta">EID: {row.eid}</div>
                {link_html}
            </div>
            """
        st.markdown(pub_html, unsafe_allow_html=True)

    # st.markdown("")
    # if st.button("✖ ปิด", use_container_width=True):
    #     st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)
