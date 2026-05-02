import streamlit as st
import pandas as pd
import ast
import os

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


# ══════════════════════════════════════════════════════════════════
# ตรวจจับทวีปจาก profile
# ══════════════════════════════════════════════════════════════════
CONTINENT_KEYWORDS = {
    "เอเชีย": [
        "thailand", "thai", "bangkok", "chiang mai", "chulalongkorn",
        "mahidol", "thammasat", "khon kaen", "chiang rai", "naresuan",
        "singapore", "malaysia", "kuala lumpur", "indonesia", "jakarta",
        "vietnam", "hanoi", "ho chi minh", "philippines", "manila",
        "cambodia", "phnom penh", "myanmar", "yangon", "laos", "brunei",
        "china", "beijing", "shanghai", "guangzhou", "hong kong", "macau",
        "japan", "tokyo", "osaka", "kyoto", "yokohama",
        "korea", "seoul", "busan", "south korea", "taiwan", "taipei",
        "mongolia", "ulaanbaatar",
        "india", "new delhi", "mumbai", "kolkata", "bangalore", "chennai",
        "pakistan", "islamabad", "karachi", "lahore",
        "bangladesh", "dhaka", "sri lanka", "colombo", "nepal", "kathmandu",
        "bhutan", "maldives", "kazakhstan", "uzbekistan", "kyrgyzstan",
        "iran", "tehran", "iraq", "baghdad",
        "saudi arabia", "riyadh", "jeddah",
        "turkey", "ankara", "istanbul",
        "israel", "tel aviv", "jerusalem",
        "jordan", "amman", "lebanon", "beirut",
        "uae", "dubai", "abu dhabi", "united arab emirates",
        "qatar", "doha", "kuwait", "bahrain", "oman",
        "yemen", "syria", "cyprus", "afghanistan",
    ],
    "ยุโรป": [
        "switzerland", "bern", "zurich", "geneva",
        "germany", "berlin", "munich", "hamburg", "cologne",
        "france", "paris", "lyon", "marseille",
        "uk", "united kingdom", "london", "england", "scotland", "wales",
        "netherlands", "amsterdam", "rotterdam",
        "italy", "rome", "milan", "naples",
        "spain", "madrid", "barcelona",
        "sweden", "stockholm", "norway", "oslo",
        "denmark", "copenhagen", "finland", "helsinki",
        "belgium", "brussels", "austria", "vienna",
        "poland", "warsaw", "portugal", "lisbon",
        "czech", "prague", "hungary", "budapest",
        "romania", "bucharest", "greece", "athens",
        "russia", "moscow", "saint petersburg",
        "ukraine", "kyiv", "ireland", "dublin",
        "croatia", "serbia", "slovakia", "slovenia",
        "bulgaria", "luxembourg", "malta", "iceland",
        "estonia", "latvia", "lithuania", "moldova", "belarus",
        "albania", "north macedonia", "bosnia", "montenegro", "kosovo",
    ],
    "อเมริกาเหนือ": [
        "usa", "united states", "u.s.", "u.s.a.", "america",
        "new york", "los angeles", "chicago", "houston", "phoenix",
        "philadelphia", "san antonio", "san diego", "dallas", "san jose",
        "atlanta", "boston", "seattle", "washington", "miami",
        "san francisco", "denver", "detroit", "minneapolis", "portland",
        "california", "texas", "florida", "ohio", "georgia",
        "massachusetts", "michigan", "illinois",
        "canada", "toronto", "montreal", "vancouver", "ottawa", "calgary",
        "mexico", "mexico city", "guadalajara", "monterrey",
        "cuba", "havana", "dominican republic", "puerto rico", "jamaica",
        "haiti", "honduras", "guatemala", "el salvador", "nicaragua",
        "costa rica", "panama", "belize", "bahamas", "trinidad",
    ],
    "อเมริกาใต้": [
        "brazil", "sao paulo", "rio de janeiro", "brasilia",
        "argentina", "buenos aires", "cordoba",
        "colombia", "bogota", "medellin",
        "chile", "santiago", "peru", "lima",
        "venezuela", "caracas", "ecuador", "quito",
        "bolivia", "la paz", "paraguay", "uruguay", "guyana", "suriname",
    ],
    "แอฟริกา": [
        "south africa", "johannesburg", "cape town", "pretoria", "durban",
        "nigeria", "lagos", "abuja", "kenya", "nairobi",
        "ethiopia", "addis ababa", "egypt", "cairo", "alexandria",
        "ghana", "accra", "tanzania", "dar es salaam",
        "uganda", "kampala", "senegal", "dakar",
        "morocco", "casablanca", "rabat", "algeria", "algiers",
        "tunisia", "tunis", "angola", "luanda",
        "mozambique", "zimbabwe", "zambia", "cameroon",
        "ivory coast", "sudan", "somalia", "mali", "niger",
        "rwanda", "burundi", "madagascar", "namibia", "botswana",
        "malawi", "liberia", "sierra leone", "guinea", "congo",
        "djibouti", "eritrea", "comoros", "mauritius", "seychelles",
    ],
    "โอเชียเนีย": [
        "australia", "sydney", "melbourne", "brisbane", "perth", "adelaide",
        "new zealand", "auckland", "wellington", "christchurch",
        "fiji", "suva", "papua new guinea", "port moresby",
        "samoa", "tonga", "vanuatu", "solomon islands", "pacific", "oceania",
    ],
}

CONTINENT_COLORS = {
    "เอเชีย":        "#F0803C",
    "ยุโรป":         "#4A90D9",
    "อเมริกาเหนือ":  "#27AE60",
    "อเมริกาใต้":    "#8E44AD",
    "แอฟริกา":       "#E74C3C",
    "โอเชียเนีย":    "#16A085",
    "ไม่ทราบ":       "#666666",
}

CONTINENT_FLAGS = {
    "เอเชีย":        "🌏",
    "ยุโรป":         "🌍",
    "อเมริกาเหนือ":  "🌎",
    "อเมริกาใต้":    "🌎",
    "แอฟริกา":       "🌍",
    "โอเชียเนีย":    "🌏",
    "ไม่ทราบ":       "❓",
}


@st.cache_data
def detect_continent(profile: str) -> str:
    if not profile or pd.isna(profile):
        return "ไม่ทราบ"
    text = str(profile).lower()
    for continent, keywords in CONTINENT_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                return continent
    return "ไม่ทราบ"


@st.cache_data
def enrich_with_continent(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["continent"] = df["profile"].apply(detect_continent)
    return df


def get_unique_authors(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.sort_values("expertise_score", ascending=False)
        .drop_duplicates(subset="author_id")
        .reset_index(drop=True)
    )


def safe_list(val):
    if isinstance(val, list):
        return val
    try:
        return ast.literal_eval(str(val))
    except Exception:
        return []


# ══════════════════════════════════════════════════════════════════
# Page Config
# ══════════════════════════════════════════════════════════════════
st.set_page_config(page_title="การกระจายตัวของนักวิจัย", page_icon="🌍", layout="wide")

if "modal_author_id" not in st.session_state:
    st.session_state.modal_author_id = None

# ══════════════════════════════════════════════════════════════════
# CSS
# ══════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;700;800&family=IBM+Plex+Mono:wght@400;600&family=Sarabun:wght@300;400;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Sarabun', sans-serif; }

.page-title {
    font-size: 2.4rem; font-weight: 800;
    letter-spacing: -1px; margin-bottom: .15rem;
    font-family: 'Syne', sans-serif; color: #fff;
}
.page-sub {
    font-size: .92rem; color: #777;
    font-family: 'IBM Plex Mono', monospace; margin-bottom: 1.8rem;
}
.stat-card {
    background: #111; border: 1px solid #222; border-radius: 12px;
    padding: 1.2rem 1.4rem; text-align: center;
    position: relative; overflow: hidden; transition: transform .15s;
}
.stat-card:hover { transform: translateY(-3px); }
.stat-card .accent-bar {
    position: absolute; top: 0; left: 0; right: 0;
    height: 4px; border-radius: 12px 12px 0 0;
}
.stat-card .label {
    font-size: .72rem; letter-spacing: .1em; text-transform: uppercase;
    color: #666; font-family: 'IBM Plex Mono', monospace;
}
.stat-card .value {
    font-size: 2.2rem; font-weight: 800; color: #fff;
    line-height: 1.1; margin: .2rem 0; font-family: 'Syne', sans-serif;
}
.stat-card .sub { font-size: .8rem; color: #555; }
.cont-row {
    display: flex; align-items: center; gap: .7rem;
    padding: .5rem 0; border-bottom: 1px solid #1a1a1a;
}
.cont-dot { width: 13px; height: 13px; border-radius: 50%; flex-shrink: 0; }
.cont-name { flex: 0 0 130px; font-weight: 700; font-size: .92rem; color: #eee; }
.cont-bar-bg { flex: 1; background: #1a1a1a; border-radius: 4px; height: 10px; overflow: hidden; }
.cont-bar-fill { height: 100%; border-radius: 4px; }
.cont-pct {
    flex: 0 0 50px; text-align: right;
    font-family: 'IBM Plex Mono', monospace; font-size: .82rem; color: #aaa; font-weight: 600;
}
.cont-cnt {
    flex: 0 0 70px; text-align: right;
    font-family: 'IBM Plex Mono', monospace; font-size: .78rem; color: #555;
}
.sec-header {
    font-size: 1.05rem; font-weight: 700; color: #ddd;
    letter-spacing: .03em; border-left: 4px solid #F0803C;
    padding-left: .7rem; margin: 1.6rem 0 .8rem 0;
}
.author-card {
    background: #111; border: 1px solid #1e1e1e; border-radius: 10px;
    padding: .65rem .85rem; margin-bottom: .35rem;
}
.author-name { font-weight: 700; font-size: .88rem; color: #eee; }
.author-meta { font-size: .74rem; color: #777; font-family: 'IBM Plex Mono', monospace; margin: .1rem 0; }
.author-aff { font-size: .72rem; color: #555; line-height: 1.35; }
.metric-grid { display: grid; grid-template-columns: repeat(4,1fr); gap: .7rem; margin: .8rem 0; }
.metric-item {
    background: #161616; border: 1px solid #222; border-radius: 8px;
    padding: .6rem .8rem; text-align: center;
}
.metric-label { font-size: .68rem; color: #555; text-transform: uppercase; letter-spacing: .08em; }
.metric-value { font-size: 1.5rem; font-weight: 800; color: #fff; font-family: 'Syne', sans-serif; }
.metric-sub { font-size: .68rem; color: #444; }
.modal-badge {
    display: inline-block; padding: .2rem .7rem; border-radius: 20px;
    font-size: .75rem; font-weight: 700; margin-right: .4rem; margin-bottom: .3rem;
    font-family: 'IBM Plex Mono', monospace;
}
.modal-section-title {
    font-size: .78rem; letter-spacing: .12em; text-transform: uppercase;
    color: #555; font-family: 'IBM Plex Mono', monospace;
    border-bottom: 1px solid #1e1e1e; padding-bottom: .3rem; margin: 1.2rem 0 .6rem 0;
}
.expertise-row {
    display: flex; align-items: center; gap: .5rem;
    padding: .35rem 0; border-bottom: 1px solid #181818; font-size: .82rem;
}
.expertise-l1 { flex: 0 0 180px; color: #777; font-size: .73rem; }
.expertise-name { flex: 1; color: #ddd; font-weight: 600; }
.expertise-score {
    flex: 0 0 90px; text-align: right;
    font-family: 'IBM Plex Mono', monospace; color: #F0803C; font-size: .8rem;
}
.expertise-bar-bg { flex: 0 0 70px; background: #1a1a1a; border-radius: 3px; height: 6px; }
.expertise-bar-fill { height: 100%; border-radius: 3px; background: #F0803C; }
.paper-item {
    background: #131313; border: 1px solid #1e1e1e; border-radius: 7px;
    padding: .5rem .8rem; margin-bottom: .3rem; font-size: .8rem;
    color: #bbb; line-height: 1.45;
}
.paper-id { font-family: 'IBM Plex Mono', monospace; font-size: .68rem; color: #444; margin-top: .2rem; }
section[data-testid="stSidebar"] { background: #0d0d0d; border-right: 1px solid #1a1a1a; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# โหลดและ Enrich ข้อมูล
# ══════════════════════════════════════════════════════════════════
df_raw = load_initial_data()
if df_raw.empty:
    st.warning("ไม่มีข้อมูล กรุณาตรวจสอบแหล่งข้อมูล")
    st.stop()

df = enrich_with_continent(df_raw)
authors = get_unique_authors(df)

# ══════════════════════════════════════════════════════════════════
# Sidebar
# ══════════════════════════════════════════════════════════════════
st.sidebar.markdown("## 🌍 การกระจายตัวของนักวิจัย")
st.sidebar.markdown("---")

all_continents = sorted(df["continent"].unique().tolist())
selected_continents = st.sidebar.multiselect(
    "🗺️ กรองตามทวีป", options=all_continents, default=all_continents,
)
all_l1 = sorted(df["l1_field"].unique().tolist())
selected_fields = st.sidebar.multiselect(
    "📚 กรองตามสาขา (L1 Field)", options=all_l1, default=[], placeholder="ทุกสาขา",
)
min_papers = st.sidebar.slider(
    "📄 จำนวนบทความขั้นต่ำ (author_papers)",
    min_value=1,
    max_value=int(authors["author_papers"].quantile(0.95)),
    value=1,
)
st.sidebar.markdown("---")
st.sidebar.caption("🔍 ระบุทวีปจากการจับคู่ keyword ใน profile affiliation")
st.sidebar.caption("📌 กด 'ดูรายละเอียด' หรือเลือกชื่อนักวิจัยเพื่อดู Modal เชิงลึก")

# กรองข้อมูล
filtered_authors = authors[authors["continent"].isin(selected_continents)].copy()
filtered_authors = filtered_authors[filtered_authors["author_papers"] >= min_papers]
if selected_fields:
    valid_ids = df[df["l1_field"].isin(selected_fields)]["author_id"].unique()
    filtered_authors = filtered_authors[filtered_authors["author_id"].isin(valid_ids)]
filtered_df = df[df["author_id"].isin(filtered_authors["author_id"])]


# ══════════════════════════════════════════════════════════════════
# ฟังก์ชัน Modal รายละเอียดนักวิจัย
# ══════════════════════════════════════════════════════════════════
@st.dialog("👤 Author Profile", width="large")
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


# ══════════════════════════════════════════════════════════════════
# แสดง Modal ถ้ามีการเลือก
# ══════════════════════════════════════════════════════════════════
if st.session_state.modal_author_id:
    with st.container(border=True):
        render_author_modal(st.session_state.modal_author_id)
    st.divider()

# ══════════════════════════════════════════════════════════════════
# หัวหน้าหน้า
# ══════════════════════════════════════════════════════════════════
st.markdown('<div class="page-title">🌍 Authors อยู่ทวีปไหนกัน?</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="page-sub">'
    'การกระจายตัวทางภูมิศาสตร์ของนักวิจัย · จำแนกจาก profile affiliation · '
    'คลิก "ดูรายละเอียด" เพื่อเปิด Modal ข้อมูลเชิงลึก'
    '</div>',
    unsafe_allow_html=True,
)

# ══════════════════════════════════════════════════════════════════
# KPI
# ══════════════════════════════════════════════════════════════════
total_authors = len(filtered_authors)
total_records = len(filtered_df)
n_continents  = filtered_authors["continent"].nunique()
unknown_pct   = (filtered_authors["continent"] == "ไม่ทราบ").mean() * 100

kpi_cols = st.columns(4)
kpi_data = [
    ("#F0803C", "นักวิจัยทั้งหมด",   f"{total_authors:,}",   "นักวิจัยที่ไม่ซ้ำกัน"),
    ("#4A90D9", "ความเชี่ยวชาญ",     f"{total_records:,}",   "แถว taxonomy records"),
    ("#27AE60", "จำนวนทวีป",          str(n_continents),      "ทวีปที่พบในข้อมูล"),
    ("#E74C3C", "ระบุทวีปไม่ได้",    f"{unknown_pct:.1f}%",  "ของนักวิจัยทั้งหมด"),
]
for col, (color, label, value, sub) in zip(kpi_cols, kpi_data):
    with col:
        st.markdown(f"""
        <div class="stat-card">
          <div class="accent-bar" style="background:{color}"></div>
          <div class="label">{label}</div>
          <div class="value">{value}</div>
          <div class="sub">{sub}</div>
        </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# Bar Chart + ตารางสถิติ
# ══════════════════════════════════════════════════════════════════
cont_counts = (
    filtered_authors["continent"].value_counts().reset_index()
    .rename(columns={"continent": "ทวีป", "count": "จำนวนนักวิจัย"})
)
cont_counts["สัดส่วน (%)"] = cont_counts["จำนวนนักวิจัย"] / cont_counts["จำนวนนักวิจัย"].sum() * 100
cont_counts["สี"]   = cont_counts["ทวีป"].map(CONTINENT_COLORS)
cont_counts["Flag"] = cont_counts["ทวีป"].map(CONTINENT_FLAGS)

col_bar, col_stat = st.columns([1, 1], gap="large")

with col_bar:
    st.markdown('<div class="sec-header">📊 สัดส่วนนักวิจัยตามทวีป</div>', unsafe_allow_html=True)
    max_cnt = cont_counts["จำนวนนักวิจัย"].max()
    bars_html = ""
    for _, row in cont_counts.iterrows():
        bar_w = (row["จำนวนนักวิจัย"] / max_cnt) * 100
        bars_html += f"""
        <div class="cont-row">
          <div class="cont-dot" style="background:{row['สี']}"></div>
          <div class="cont-name">{row['Flag']} {row['ทวีป']}</div>
          <div class="cont-bar-bg">
            <div class="cont-bar-fill" style="width:{bar_w:.1f}%;background:{row['สี']}"></div>
          </div>
          <div class="cont-pct">{row['สัดส่วน (%)']:.1f}%</div>
          <div class="cont-cnt">{row['จำนวนนักวิจัย']:,} คน</div>
        </div>"""
    st.markdown(bars_html, unsafe_allow_html=True)

with col_stat:
    st.markdown('<div class="sec-header">📋 สถิติสรุปรายทวีป</div>', unsafe_allow_html=True)
    detail_rows = []
    for _, row in cont_counts.iterrows():
        cont = row["ทวีป"]
        sub  = filtered_authors[filtered_authors["continent"] == cont]
        avg_papers = sub["author_papers"].mean()
        avg_score  = filtered_df[filtered_df["author_id"].isin(sub["author_id"])]["expertise_score"].mean()
        top_author = sub.sort_values("expertise_score", ascending=False).iloc[0]["author_name"] if len(sub) else "—"
        n_fields   = filtered_df[filtered_df["author_id"].isin(sub["author_id"])]["l1_field"].nunique()
        detail_rows.append({
            "ทวีป":              f"{row['Flag']} {cont}",
            "นักวิจัย (คน)":     row["จำนวนนักวิจัย"],
            "บทความเฉลี่ย":      f"{avg_papers:.0f}",
            "คะแนนเฉลี่ย":       f"{avg_score:,.0f}",
            "สาขาที่ครอบคลุม":   n_fields,
            "อันดับ 1":           top_author,
        })
    st.dataframe(pd.DataFrame(detail_rows), use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════════
# Heatmap
# ══════════════════════════════════════════════════════════════════
st.markdown('<div class="sec-header">🗂️ การกระจายตัวตามสาขาวิชา (L1 Field) รายทวีป</div>', unsafe_allow_html=True)

pivot = (
    filtered_df[filtered_df["author_id"].isin(filtered_authors["author_id"])]
    .drop_duplicates(subset=["author_id", "l1_field"])
    .groupby(["continent", "l1_field"]).size().reset_index(name="count")
    .pivot(index="l1_field", columns="continent", values="count")
    .fillna(0).astype(int)
)
ordered_cols = [c for c in cont_counts["ทวีป"].tolist() if c in pivot.columns]
pivot = pivot[ordered_cols]
pivot["รวม"] = pivot.sum(axis=1)
pivot = pivot.sort_values("รวม", ascending=False).drop(columns="รวม")
pivot.index.name = "สาขาวิชา (L1)"
st.dataframe(
    pivot.style.background_gradient(cmap="YlOrRd", axis=None),
    use_container_width=True,
    height=min(40 + len(pivot) * 36, 520),
)

# ══════════════════════════════════════════════════════════════════
# Top 5 รายทวีป — พร้อมปุ่ม Modal
# ══════════════════════════════════════════════════════════════════
st.markdown('<div class="sec-header">🏆 นักวิจัยชั้นนำ 5 อันดับแรก รายทวีป</div>', unsafe_allow_html=True)
st.caption("👆 กดปุ่ม 🔍 ดูรายละเอียด เพื่อเปิด Modal ข้อมูลเชิงลึกของนักวิจัย")

n_cols_top = min(len(cont_counts), 3)
top_groups = [cont_counts.iloc[i:i+n_cols_top] for i in range(0, len(cont_counts), n_cols_top)]

for group in top_groups:
    cols = st.columns(len(group))
    for col, (_, crow) in zip(cols, group.iterrows()):
        cont  = crow["ทวีป"]
        color = crow["สี"]
        flag  = crow["Flag"]
        sub   = filtered_authors[filtered_authors["continent"] == cont].copy()
        top5  = sub.sort_values("expertise_score", ascending=False).head(5)

        with col:
            st.markdown(f"**{flag} {cont}**")
            for rank, (_, arow) in enumerate(top5.iterrows(), 1):
                aff = str(arow.get("profile", "")).strip()
                if len(aff) > 55:
                    aff = aff[:52] + "…"
                st.markdown(f"""
                <div class='author-card' style='border-left:3px solid {color}'>
                  <div class='author-name'>#{rank} {arow['author_name']}</div>
                  <div class='author-meta'>
                    คะแนน: {arow['expertise_score']:,.0f} · บทความ: {arow['author_papers']}
                  </div>
                  <div class='author-aff'>{aff}</div>
                </div>""", unsafe_allow_html=True)
                if st.button(
                    "🔍 ดูรายละเอียด",
                    key=f"btn_{arow['author_id']}_{rank}_{cont}",
                    use_container_width=True,
                ):
                    st.session_state.modal_author_id = arow["author_id"]
                    st.rerun()

# ══════════════════════════════════════════════════════════════════
# ตารางค้นหานักวิจัย
# ══════════════════════════════════════════════════════════════════
st.markdown('<div class="sec-header">🔍 ค้นหาและเปิดรายละเอียดนักวิจัย</div>', unsafe_allow_html=True)

col_s1, col_s2 = st.columns([3, 1])
with col_s1:
    search = st.text_input(
        "ค้นหา", placeholder="ชื่อนักวิจัย / สังกัด / ทวีป …",
        label_visibility="collapsed",
    )
with col_s2:
    sort_by = st.selectbox(
        "เรียงตาม",
        ["คะแนนความเชี่ยวชาญ ↓", "จำนวนบทความ ↓", "ชื่อ A→Z"],
        label_visibility="collapsed",
    )

table_df = filtered_authors[[
    "author_id", "author_name", "continent", "profile",
    "author_papers", "first_author_papers", "corresponding_papers", "expertise_score"
]].copy()
table_df.columns = [
    "author_id", "ชื่อนักวิจัย", "ทวีป", "สังกัด",
    "บทความทั้งหมด", "1st Author", "Corresponding", "คะแนนความเชี่ยวชาญ",
]
table_df["คะแนนความเชี่ยวชาญ"] = table_df["คะแนนความเชี่ยวชาญ"].round(1)

if sort_by == "คะแนนความเชี่ยวชาญ ↓":
    table_df = table_df.sort_values("คะแนนความเชี่ยวชาญ", ascending=False)
elif sort_by == "จำนวนบทความ ↓":
    table_df = table_df.sort_values("บทความทั้งหมด", ascending=False)
else:
    table_df = table_df.sort_values("ชื่อนักวิจัย")

if search:
    mask = (
        table_df["ชื่อนักวิจัย"].str.contains(search, case=False, na=False) |
        table_df["สังกัด"].str.contains(search, case=False, na=False) |
        table_df["ทวีป"].str.contains(search, case=False, na=False)
    )
    table_df = table_df[mask]

st.dataframe(
    table_df.drop(columns=["author_id"]).reset_index(drop=True),
    use_container_width=True, height=400, hide_index=True,
)
st.caption(f"แสดง {len(table_df):,} รายการ จากทั้งหมด {len(filtered_authors):,} นักวิจัย")

# เลือกนักวิจัยจากตารางเพื่อเปิด Modal
st.markdown("**เปิดรายละเอียดนักวิจัยจากตาราง:**")
col_pick, col_open = st.columns([4, 1])
with col_pick:
    name_opts = ["— เลือกนักวิจัย —"] + table_df["ชื่อนักวิจัย"].tolist()
    chosen_name = st.selectbox("เลือก", options=name_opts, label_visibility="collapsed")
with col_open:
    if st.button("🔍 เปิดรายละเอียด", use_container_width=True, type="primary"):
        if chosen_name != "— เลือกนักวิจัย —":
            match_row = table_df[table_df["ชื่อนักวิจัย"] == chosen_name]
            if not match_row.empty:
                st.session_state.modal_author_id = match_row.iloc[0]["author_id"]
                st.rerun()

# ══════════════════════════════════════════════════════════════════
# Unknown Profiles
# ══════════════════════════════════════════════════════════════════
unknown_count = (filtered_authors["continent"] == "ไม่ทราบ").sum()
with st.expander(f"❓ ดู profiles ที่ระบุทวีปไม่ได้ ({unknown_count:,} ราย)"):
    unknown_df = filtered_authors[filtered_authors["continent"] == "ไม่ทราบ"]
    st.info(
        f"พบ **{len(unknown_df):,}** นักวิจัยที่ไม่สามารถระบุทวีปได้ · "
        f"คิดเป็น **{len(unknown_df)/len(filtered_authors)*100:.1f}%** ของทั้งหมด"
    )
    st.dataframe(
        unknown_df[["author_name", "profile", "author_papers", "expertise_score"]]
        .sort_values("expertise_score", ascending=False)
        .head(100).reset_index(drop=True),
        use_container_width=True, height=300, hide_index=True,
    )
    st.caption("แสดงสูงสุด 100 แถว เรียงตามคะแนนความเชี่ยวชาญ")