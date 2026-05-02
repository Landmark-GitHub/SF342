import streamlit as st
import pandas as pd
import math
import os
import requests
from dotenv import load_dotenv
import time
from data_raw import load_data

# =========================
# 🌐 ENV
# =========================
load_dotenv()
LOCAL_WEB_API = os.getenv("LOCAL_WEB_API", "localhost:8000")

st.set_page_config(layout="wide")

# =========================
# 📦 LOAD DATA
# =========================
@st.cache_data
def get_local_data():
    return load_data()

STORAGE_PATH = os.path.join("Storage", "data_api.csv")

@st.cache_data
def load_initial_data():
    if os.path.exists(STORAGE_PATH):
        try:
            return pd.read_csv(STORAGE_PATH)
        except:
            pass
    return get_local_data()

df = load_initial_data()

# =========================
# 🧠 SESSION STATE (CLEAN FIX)
# =========================
defaults = {
    "upload_done": False,
    "ingest_finished": False,
    "df_api": None,
    "page": 1,

    # 🔥 FIX: ใช้ trigger เดียวพอ
    "ingest_trigger": False,
    "selected_author": None,
    "ingest_ready": False,
}

for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v
 

def render_author_modal(author_id: str):
    author_row = authors[authors["author_id"] == author_id]
    if author_row.empty:
        return
    a = author_row.iloc[0]

    author_expertise = df[df["author_id"] == author_id].sort_values("expertise_score", ascending=False)
    total_score = author_expertise["expertise_score"].sum()
    max_score   = author_expertise["expertise_score"].max() if len(author_expertise) else 1

    cont        = a.get("continent", "ไม่ทราบ")
    cont_color  = CONTINENT_COLORS.get(cont, "#666")
    cont_flag   = CONTINENT_FLAGS.get(cont, "❓")

    evidence_titles = safe_list(a.get("evidence_titles", []))
    evidence_ids    = safe_list(a.get("evidence_paper_ids", []))

    # ── Header Modal ──
    col_close, col_title = st.columns([1, 8])
    with col_close:
        if st.button("✕ ปิด", key="close_modal"):
            st.session_state.modal_author_id = None
            st.rerun()
    with col_title:
        st.markdown(
            f"<h2 style='margin:0 0 .3rem 0;font-family:Syne,sans-serif;color:#fff'>"
            f"{a['author_name']}</h2>",
            unsafe_allow_html=True,
        )

    # Badges
    st.markdown(f"""
    <div style='margin:.2rem 0 1rem 0'>
      <span class='modal-badge' style='background:{cont_color}22;color:{cont_color};border:1px solid {cont_color}55'>
        {cont_flag} {cont}
      </span>
      <span class='modal-badge' style='background:#1a1a1a;color:#888;border:1px solid #2a2a2a'>
        🆔 {a['author_id']}
      </span>
      <span class='modal-badge' style='background:#1a1a1a;color:#888;border:1px solid #2a2a2a'>
        📚 {len(author_expertise)} สาขาความเชี่ยวชาญ
      </span>
      <span class='modal-badge' style='background:#1a1a1a;color:#888;border:1px solid #2a2a2a'>
        📄 {int(a.get('author_papers',0))} บทความ
      </span>
    </div>
    """, unsafe_allow_html=True)

    # ── สังกัด ──
    st.markdown('<div class="modal-section-title">🏛️ สังกัด / Affiliation</div>', unsafe_allow_html=True)
    st.markdown(
        f"<div style='background:#161616;border:1px solid #252525;border-radius:8px;"
        f"padding:.75rem 1rem;color:#ccc;font-size:.88rem;line-height:1.6'>"
        f"{a.get('profile','—')}</div>",
        unsafe_allow_html=True,
    )

    # ── ตัวเลขสถิติ ──
    st.markdown('<div class="modal-section-title">📊 สถิติการตีพิมพ์</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class='metric-grid'>
      <div class='metric-item'>
        <div class='metric-label'>บทความทั้งหมด</div>
        <div class='metric-value'>{int(a.get('author_papers',0)):,}</div>
        <div class='metric-sub'>author_papers</div>
      </div>
      <div class='metric-item'>
        <div class='metric-label'>ผู้เขียนคนแรก</div>
        <div class='metric-value' style='color:#27AE60'>{int(a.get('first_author_papers',0)):,}</div>
        <div class='metric-sub'>first author</div>
      </div>
      <div class='metric-item'>
        <div class='metric-label'>Corresponding</div>
        <div class='metric-value' style='color:#4A90D9'>{int(a.get('corresponding_papers',0)):,}</div>
        <div class='metric-sub'>corresponding author</div>
      </div>
      <div class='metric-item'>
        <div class='metric-label'>คะแนนรวม</div>
        <div class='metric-value' style='color:#F0803C'>{total_score:,.0f}</div>
        <div class='metric-sub'>expertise score</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # อัตราส่วน first / corresponding
    total_p = int(a.get("author_papers", 0))
    if total_p > 0:
        pct_first = int(a.get("first_author_papers", 0)) / total_p * 100
        pct_corr  = int(a.get("corresponding_papers", 0)) / total_p * 100
        st.markdown(
            f"<div style='font-size:.8rem;color:#666;margin-top:-.4rem;margin-bottom:.5rem'>"
            f"สัดส่วน: เป็นผู้เขียนคนแรก <b style='color:#27AE60'>{pct_first:.0f}%</b> · "
            f"Corresponding <b style='color:#4A90D9'>{pct_corr:.0f}%</b> ของบทความทั้งหมด</div>",
            unsafe_allow_html=True,
        )

    # ── ความเชี่ยวชาญ ──
    st.markdown('<div class="modal-section-title">🎓 ความเชี่ยวชาญรายสาขา</div>', unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["📋 รายละเอียดทุก Subfield", "📊 สรุปตาม L1 Field"])

    with tab1:
        rows_html = ""
        for _, erow in author_expertise.iterrows():
            bar_pct = (erow["expertise_score"] / max_score * 100)
            rows_html += f"""
            <div class='expertise-row'>
              <div class='expertise-l1'>{erow['l1_field']}</div>
              <div class='expertise-name'>{erow['subfield_name']}<br>
                <span style='font-size:.7rem;color:#555'>{erow['l2_domain']}</span>
              </div>
              <div class='expertise-bar-bg'>
                <div class='expertise-bar-fill' style='width:{bar_pct:.0f}%'></div>
              </div>
              <div class='expertise-score'>{erow['expertise_score']:,.1f}</div>
            </div>"""
        st.markdown(rows_html, unsafe_allow_html=True)

    with tab2:
        l1_summary = (
            author_expertise.groupby("l1_field")
            .agg(score_sum=("expertise_score","sum"), subfield_count=("subfield_name","count"))
            .sort_values("score_sum", ascending=False).reset_index()
        )
        max_l1 = l1_summary["score_sum"].max() if len(l1_summary) else 1
        l1_html = ""
        for _, lrow in l1_summary.iterrows():
            bar_pct = (lrow["score_sum"] / max_l1 * 100)
            l1_html += f"""
            <div class='expertise-row'>
              <div class='expertise-name' style='flex:1'>{lrow['l1_field']}</div>
              <div style='flex:0 0 55px;text-align:center;font-size:.72rem;color:#555'>
                {lrow['subfield_count']} subfields
              </div>
              <div class='expertise-bar-bg' style='flex:0 0 100px'>
                <div class='expertise-bar-fill' style='width:{bar_pct:.0f}%;background:#4A90D9'></div>
              </div>
              <div class='expertise-score' style='color:#4A90D9'>{lrow['score_sum']:,.1f}</div>
            </div>"""
        st.markdown(l1_html, unsafe_allow_html=True)

    # ── ข้อมูล Taxonomy หลัก ──
    st.markdown('<div class="modal-section-title">🏷️ Taxonomy สาขาหลัก (อันดับ 1)</div>', unsafe_allow_html=True)
    top = author_expertise.iloc[0]
    st.markdown(f"""
    <div style='background:#161616;border:1px solid #252525;border-radius:10px;padding:1rem 1.2rem'>
      <div style='display:grid;grid-template-columns:1fr 1fr;gap:.9rem;font-size:.84rem'>
        <div>
          <div style='color:#555;font-size:.7rem;text-transform:uppercase;margin-bottom:.2rem'>L1 Field</div>
          <div style='color:#eee;font-weight:700'>{top['l1_field']}</div>
        </div>
        <div>
          <div style='color:#555;font-size:.7rem;text-transform:uppercase;margin-bottom:.2rem'>L2 Domain</div>
          <div style='color:#eee;font-weight:700'>{top['l2_domain']}</div>
        </div>
        <div>
          <div style='color:#555;font-size:.7rem;text-transform:uppercase;margin-bottom:.2rem'>Subfield</div>
          <div style='color:#eee;font-weight:700'>{top['subfield_name']}</div>
        </div>
        <div>
          <div style='color:#555;font-size:.7rem;text-transform:uppercase;margin-bottom:.2rem'>Taxonomy ID</div>
          <div style='color:#aaa;font-family:IBM Plex Mono,monospace'>{top['taxonomy_id']}</div>
        </div>
        <div>
          <div style='color:#555;font-size:.7rem;text-transform:uppercase;margin-bottom:.2rem'>Avg Similarity</div>
          <div style='color:#ccc'>{top['avg_similarity']:.4f}</div>
        </div>
        <div>
          <div style='color:#555;font-size:.7rem;text-transform:uppercase;margin-bottom:.2rem'>Paper Count (taxonomy)</div>
          <div style='color:#ccc'>{top['paper_count']}</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── บทความอ้างอิง ──
    st.markdown(
        f'<div class="modal-section-title">📄 บทความหลักฐาน ({len(evidence_titles)} รายการ)</div>',
        unsafe_allow_html=True,
    )
    if evidence_titles:
        show_n = st.slider(
            "จำนวนบทความที่แสดง",
            min_value=5, max_value=min(50, len(evidence_titles)),
            value=min(10, len(evidence_titles)),
            key="paper_slider_modal",
        )
        papers_html = ""
        for i, title in enumerate(evidence_titles[:show_n]):
            pid = evidence_ids[i] if i < len(evidence_ids) else ""
            papers_html += f"""
            <div class='paper-item'>
              <div>📎 {title}</div>
              <div class='paper-id'>{pid}</div>
            </div>"""
        st.markdown(papers_html, unsafe_allow_html=True)
        if len(evidence_titles) > show_n:
            st.caption(f"… และอีก {len(evidence_titles) - show_n} บทความที่เหลือ")
    else:
        st.caption("ไม่มีข้อมูลบทความ")

# =========================
# 👤 AUTHOR MODAL (FIXED)
# =========================
@st.dialog("👤 Author Profile", width="large")
def author_detail_modal():
    a = st.session_state.selected_author
    if not a:
        return

    # =========================
    # 🔝 HEADER
    # =========================
    col1, col2 = st.columns([6,1])

    with col1:
        st.markdown(f"## 👤 {a.get('author_name','-')}")
        st.caption(f"🆔 {a.get('author_id','-')}")

    with col2:
        if st.button("❌", key="close_modal"):
            st.session_state.selected_author = None
            st.rerun()

    st.divider()

    # =========================
    # 🧑‍🎓 PROFILE
    # =========================
    st.markdown("### 🧑‍🎓 Profile")
    st.info(a.get("profile", "No profile"))

    # =========================
    # 📊 MAIN METRICS
    # =========================
    m1, m2, m3, m4 = st.columns(4)

    m1.metric("📚 Field", a.get("l1_field", "-"))
    m2.metric("🔬 Domain", a.get("l2_domain", "-"))
    m3.metric("🧠 Subfield", a.get("subfield_name", "-"))
    m4.metric("📄 Papers", a.get("author_papers", 0))

    # =========================
    # 📈 SCORE VISUAL
    # =========================
    st.markdown("### 📈 Score & Similarity")

    c1, c2 = st.columns(2)

    with c1:
        score = a.get("expertise_score", 0)
        st.metric("Expertise Score", f"{score:,.2f}")

        # fake normalize bar
        st.progress(min(score / 100, 1.0))

    with c2:
        sim = a.get("avg_similarity", 0)
        st.metric("Similarity", f"{sim:.4f}")
        st.progress(min(float(sim), 1.0))

    # =========================
    # 📊 PUBLICATION RATIO
    # =========================
    st.markdown("### 📊 Publication Role")

    total = a.get("author_papers", 0)
    first = a.get("first_author_papers", 0)
    corr  = a.get("corresponding_papers", 0)

    r1, r2, r3 = st.columns(3)

    r1.metric("All Papers", total)
    r2.metric("First Author", first)
    r3.metric("Corresponding", corr)

    if total > 0:
        st.caption(
            f"First Author: {first/total*100:.1f}% | Corresponding: {corr/total*100:.1f}%"
        )

    # =========================
    # 🏷️ TAXONOMY DETAIL
    # =========================
    st.markdown("### 🏷️ Taxonomy Detail")

    t1, t2 = st.columns(2)

    with t1:
        st.write("**L1 Field**")
        st.info(a.get("l1_field", "-"))

        st.write("**L2 Domain**")
        st.info(a.get("l2_domain", "-"))

    with t2:
        st.write("**Subfield**")
        st.info(a.get("subfield_name", "-"))

        st.write("**Paper Count (taxonomy)**")
        st.info(a.get("paper_count", "-"))

    # =========================
    # 📎 EVIDENCE PAPERS
    # =========================
    st.markdown("### 📎 Evidence Papers")

    titles = a.get("evidence_titles", [])
    ids    = a.get("evidence_paper_ids", [])

    # handle string → list
    if isinstance(titles, str):
        try:
            titles = eval(titles)
        except:
            titles = []

    if isinstance(ids, str):
        try:
            ids = eval(ids)
        except:
            ids = []

    if titles:
        show_n = st.slider("Show papers", 5, min(30, len(titles)), 10)

        for i in range(show_n):
            st.markdown(f"📄 {titles[i]}")
            if i < len(ids):
                st.caption(ids[i])

        if len(titles) > show_n:
            st.caption(f"... and {len(titles)-show_n} more papers")

    else:
        st.caption("No evidence papers")

    # =========================
    # 🔚 CLOSE
    # =========================
    st.divider()
    if st.button("Close", use_container_width=True):
        st.session_state.selected_author = None
        st.rerun()
        
        
# =========================
# 📦 INGEST MODAL (SAFE)
# =========================
@st.dialog("🚀 ระบบกำลังประมวลผล")
def process_ingest_modal():

    if st.session_state.ingest_finished:
        return

    st.success("📤 อัพโหลดไฟล์สำเร็จ!")
    st.write("ระบบกำลังวิเคราะห์...")

    status_placeholder = st.empty()
    timer_placeholder = st.empty()

    start_time = time.time()

    try:
        with st.spinner("⏳ กรุณารอ (~20 นาที)..."):
            response = requests.post(
                f"http://{LOCAL_WEB_API}/ingest/",
                timeout=1200
            )

        elapsed = int(time.time() - start_time)
        mins, secs = divmod(elapsed, 60)
        timer_placeholder.success(f"⏱ {mins:02d}:{secs:02d}")

        if response.status_code == 200:
            res = response.json()
            df_api = pd.DataFrame(res.get("data", []))
            SAVE_PATH = os.path.join("Storage", "data_api.csv")
            df_api.to_csv(SAVE_PATH, index=False)

            for col in ["author_name", "l1_field", "l2_domain"]:
                if col not in df_api.columns:
                    df_api[col] = ""

            st.session_state.df_api = df_api
            st.session_state.ingest_finished = True

            status_placeholder.success(f"✅ {len(df_api)} rows")

        else:
            status_placeholder.error(f"❌ {response.status_code}")

    except Exception as e:
        status_placeholder.error(f"Error: {e}")



# =========================
# 🧭 HEADER
# =========================
col1, col2 = st.columns([3, 3])

with col1:
    st.markdown("### 📊 ระบบวิเคราะห์ความเชี่ยวชาญจากงานวิจัย Scopus")

    status_box = st.empty()

    if st.button("🖥️ Check Server", use_container_width=True):
        try:
            with st.spinner("กำลังตรวจสอบเซิร์ฟเวอร์..."):
                res = requests.get(f"http://{LOCAL_WEB_API}/", timeout=5)

            if res.status_code == 200:
                data = res.json()

                if data.get("model_ready") and data.get("taxonomy_ready"):
                    status_box.success("🟢 พร้อมใช้งาน")
                else:
                    status_box.warning("🟡 ยังไม่พร้อม")

            else:
                status_box.error(f"🔴 Server error: {res.status_code}")

        except Exception as e:
            status_box.error(f"Error: {e}")
# =========================
# 📂 UPLOAD
# =========================
with col2:
    search = st.text_input(
        "",
        placeholder="Search author, domain...",
        label_visibility="collapsed"
    )

    uploaded_file = st.file_uploader(
        "Upload", label_visibility="collapsed", type=["csv"]
    )

    if uploaded_file:

        if not st.session_state.upload_done:

            try:
                with st.spinner("Uploading..."):

                    files = {
                        "file": (
                            uploaded_file.name,
                            uploaded_file.getvalue(),
                            uploaded_file.type
                        )
                    }

                    res = requests.post(
                        f"http://{LOCAL_WEB_API}/upload/",
                        files=files,
                        timeout=120
                    )

                    if res.status_code == 200:
                        st.session_state.upload_done = True

                        # 🔥 FIX: trigger dialog แค่ตัวเดียว
                        st.session_state.ingest_trigger = True
                        st.session_state.ingest_ready = False
                        st.rerun()
                    else:
                        st.error("Upload failed")

            except Exception as e:
                st.error(e)

    else:
        st.session_state.upload_done = False
        st.session_state.ingest_finished = False
        st.session_state.ingest_trigger = False


# =========================
# 🔥 SAFE DIALOG ROUTER (FIX CORE BUG)
# =========================

if st.session_state.ingest_trigger:
    st.session_state.ingest_trigger = False  # consume once
    st.session_state.ingest_ready = True

if st.session_state.ingest_ready and not st.session_state.ingest_finished:
    st.session_state.ingest_ready = False
    process_ingest_modal()


# =========================
# 🔎 DATA SOURCE
# =========================
filtered = (
    st.session_state.df_api.copy()
    if st.session_state.df_api is not None
    else df.copy()
)

for col in ["author_name", "l1_field", "l2_domain"]:
    if col in filtered.columns:
        filtered[col] = filtered[col].astype(str)

if search:
    filtered = filtered[
        filtered["author_name"].str.contains(search, case=False, na=False) |
        filtered["l1_field"].str.contains(search, case=False, na=False) |
        filtered["l2_domain"].str.contains(search, case=False, na=False)
    ]
    st.session_state.page = 1


# =========================
# 📄 PAGINATION
# =========================
page_size = 16
total_pages = max(math.ceil(len(filtered) / page_size), 1)

page = st.number_input("Page", 1, total_pages, value=st.session_state.page)
st.session_state.page = page

page_data = filtered.iloc[(page-1)*page_size : page*page_size]

# =========================
# 🧱 GRID
# =========================
cols = st.columns(4)

for i, (_, row) in enumerate(page_data.iterrows()):
    with cols[i % 4]:

        if st.button(f"👤 {row['author_name']}", key=f"card_{i}", use_container_width=True):

            # 🔥 FIX: ใช้ state เดียว
            st.session_state.selected_author = row.to_dict()
            st.rerun()




# =========================
# 🔥 AUTHOR MODAL ROUTER (ONLY ONE WAY)
# =========================
if st.session_state.selected_author:
    author_detail_modal()


# =========================
# 📊 TABLE
# =========================
if len(filtered) == 0:
    st.warning("ไม่พบข้อมูล")
else:
    st.dataframe(filtered, use_container_width=True)