import streamlit as st
import pandas as pd
import ast
import streamlit.components.v1 as components

# ══════════════════════════════════════════════════════════════════
# PAGE CONFIG
# ══════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="การกระจายตัวของนักวิจัย",
    page_icon="🌍",
    layout="wide"
)

# ══════════════════════════════════════════════════════════════════
# CONSTANTS
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
        "yemen", "syria", "cyprus", "afghanistan", "Viet Nam",
    ],
    "ยุโรป": [
        "switzerland", "bern", "zurich", "geneva",
        "germany","Germany", "berlin", "munich", "hamburg", "cologne",
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
    "แอนตาร์กติกา": [
        "antarctica", "mcmurdo", "amundsen-scott", "vostok station", 
        "palmer station", "south pole"
    ],
}

CONTINENT_COLORS = {
    "เอเชีย": "#F0803C",
    "ยุโรป": "#4A90D9",
    "อเมริกาเหนือ": "#27AE60",
    "อเมริกาใต้": "#8E44AD",
    "แอฟริกา": "#E74C3C",
    "โอเชียเนีย": "#16A085",
    "แอนตาร์กติกา": "#AAB7B8",
    "ไม่ทราบ": "#555E6C",
}

CONTINENT_FLAGS = {
    "เอเชีย": "🌏",
    "ยุโรป": "🌍",
    "อเมริกาเหนือ": "🌎",
    "อเมริกาใต้": "🌎",
    "แอฟริกา": "🌍",
    "โอเชียเนีย": "🌏",
    "แอนตาร์กติกา": "❄️",
    "ไม่ทราบ": "❓",
}

# ══════════════════════════════════════════════════════════════════
# LOAD DATA
# ══════════════════════════════════════════════════════════════════

data = st.session_state.global_data
df = data["df"]
authors = data["authors"]

# ══════════════════════════════════════════════════════════════════
# CSS — ULTRA GLASS MOTION UI
# ══════════════════════════════════════════════════════════════════

st.markdown("""
<style>

/* =========================================================
   FONT
========================================================= */

@import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@300;400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Sarabun', sans-serif;
    background: #0E1117;
    color: #F5F7FA;
    font-size: 22px;
    line-height: 1.7;
}

/* =========================================================
   ROOT
========================================================= */

:root{
    --glass: rgba(255,255,255,.04);
    --border: rgba(255,255,255,.08);

    --orange: #F0803C;
    --blue: #4A90D9;

    --shadow:
        0 10px 35px rgba(0,0,0,.25);

    --shadow-hover:
        0 20px 45px rgba(0,0,0,.35);

    --radius: 26px;
}

.author-card{
    position:relative;
    overflow:hidden;

    padding:22px;

    border-radius:24px;

    backdrop-filter:blur(18px);

    border:1px solid rgba(255,255,255,.08);

    box-shadow:
        0 10px 30px rgba(0,0,0,.22);

    transition:all .28s ease;

    animation:fadeUp .7s ease;
}

.author-card::before{
    content:"";

    position:absolute;
    inset:0;

    background:
        linear-gradient(
            135deg,
            rgba(255,255,255,.05),
            transparent 45%
        );

    pointer-events:none;
}

.author-card::after{
    content:"";

    position:absolute;

    top:-40%;
    right:-30%;

    width:180px;
    height:180px;

    border-radius:999px;

    background:var(--card-glow);

    filter:blur(55px);

    opacity:.55;

    pointer-events:none;
}

.author-card:hover{
    transform:
        translateY(-8px)
        scale(1.02);

    box-shadow:
        0 20px 45px rgba(0,0,0,.30),
        0 0 30px var(--card-shadow);

    border:1px solid var(--card-border);
}

.author-rank{
    font-size:13px;
    font-weight:700;

    opacity:.75;

    margin-bottom:10px;

    letter-spacing:.5px;
}

.author-name{
    font-size:24px;
    font-weight:800;

    margin-bottom:12px;

    line-height:1.25;
}

.author-meta{
    font-size:15px;
    opacity:.82;

    margin-bottom:8px;
}

.author-score{
    margin-top:14px;

    font-size:18px;
    font-weight:800;
}

.author-score span{
    opacity:.72;
    font-size:14px;
    font-weight:600;
}

/* =========================================================
   ANIMATION
========================================================= */

@keyframes fadeUp{
    from{
        opacity:0;
        transform:translateY(18px);
    }
    to{
        opacity:1;
        transform:translateY(0);
    }
}

@keyframes shimmer{
    0%{
        transform:translateX(-150%);
    }
    100%{
        transform:translateX(250%);
    }
}

@keyframes glowPulse{
    0%{
        box-shadow:
            0 0 0 rgba(240,128,60,0);
    }

    50%{
        box-shadow:
            0 0 25px rgba(240,128,60,.18),
            0 0 55px rgba(74,144,217,.08);
    }

    100%{
        box-shadow:
            0 0 0 rgba(240,128,60,0);
    }
}

/* =========================================================
   HEADER
========================================================= */

.header-style{
    position:relative;
    overflow:hidden;

    padding:38px;
    border-radius:34px;

    border:1px solid rgba(255,255,255,.08);

    backdrop-filter:blur(18px);

    background:
        linear-gradient(
            135deg,
            rgba(240,128,60,.12),
            rgba(74,144,217,.08),
            rgba(255,255,255,.02)
        );

    font-size:44px;
    font-weight:800;

    margin-bottom:30px;

    box-shadow:
        0 15px 40px rgba(0,0,0,.25);

    animation:fadeUp .7s ease;
}

.header-style::before{
    content:"";

    position:absolute;

    top:0;
    left:-120%;

    width:40%;
    height:100%;

    background:
        linear-gradient(
            90deg,
            transparent,
            rgba(255,255,255,.12),
            transparent
        );

    animation:shimmer 5s linear infinite;
}

/* =========================================================
   FILTER PANEL
========================================================= */

.filter-panel{
    position:relative;

    padding:28px;

    border-radius:28px;

    background:
        linear-gradient(
            145deg,
            rgba(255,255,255,.04),
            rgba(255,255,255,.015)
        );

    border:1px solid rgba(255,255,255,.08);

    backdrop-filter:blur(18px);

    box-shadow:var(--shadow);

    margin-bottom:30px;

    animation:fadeUp .7s ease;
}

/* =========================================================
   SECTION HEADER
========================================================= */

.sec-header{
    position:relative;
    overflow:hidden;

    padding:18px 24px;

    border-radius:22px;

    margin-top:26px;
    margin-bottom:22px;

    font-size:28px;
    font-weight:800;

    background:
        linear-gradient(
            135deg,
            rgba(240,128,60,.10),
            rgba(74,144,217,.06)
        );

    border:1px solid rgba(255,255,255,.08);

    backdrop-filter:blur(14px);

    box-shadow:var(--shadow);

    animation:fadeUp .7s ease;
}

.sec-header::before{
    content:"";

    position:absolute;
    inset:0;

    background:
        linear-gradient(
            120deg,
            transparent,
            rgba(255,255,255,.05),
            transparent
        );

    animation:shimmer 5s linear infinite;
}

/* =========================================================
   KPI CARD
========================================================= */

div[data-testid="metric-container"]{
    position:relative;
    overflow:hidden;

    padding:24px !important;

    border-radius:24px;

    background:
        linear-gradient(
            145deg,
            rgba(255,255,255,.04),
            rgba(255,255,255,.015)
        );

    border:1px solid rgba(255,255,255,.08);

    backdrop-filter:blur(18px);

    box-shadow:var(--shadow);

    transition:all .28s ease;

    animation:fadeUp .7s ease;
}

div[data-testid="metric-container"]:hover{
    transform:
        translateY(-6px)
        scale(1.02);

    box-shadow:
        var(--shadow-hover),
        0 0 30px rgba(240,128,60,.12);

    border:1px solid rgba(240,128,60,.18);

    animation:glowPulse 2s infinite;
}

/* =========================================================
   BUTTON
========================================================= */

.stButton > button{
    position:relative;
    overflow:hidden;

    width:100%;

    height:52px;

    border:none !important;

    border-radius:18px !important;

    background:
        linear-gradient(
            135deg,
            rgba(240,128,60,.16),
            rgba(74,144,217,.10)
        ) !important;

    backdrop-filter:blur(16px);

    box-shadow:
        0 8px 20px rgba(0,0,0,.18);

    transition:all .25s ease;

    font-weight:700;
}

.stButton > button:hover{
    transform:
        translateY(-4px)
        scale(1.01);

    box-shadow:
        0 16px 35px rgba(240,128,60,.20);

    border:1px solid rgba(240,128,60,.18) !important;
}

.stButton > button::before{
    content:"";

    position:absolute;

    top:0;
    left:-140%;

    width:40%;
    height:100%;

    background:
        linear-gradient(
            90deg,
            transparent,
            rgba(255,255,255,.18),
            transparent
        );

    animation:shimmer 4s linear infinite;
}

/* =========================================================
   INPUT
========================================================= */

.stTextInput input,
.stSelectbox > div > div,
.stMultiSelect > div > div{
    border-radius:18px !important;

    border:1px solid rgba(255,255,255,.08) !important;

    background:
        rgba(255,255,255,.03) !important;

    backdrop-filter:blur(14px);

    transition:all .25s ease;
}

.stTextInput input:focus,
.stSelectbox > div > div:hover,
.stMultiSelect > div > div:hover{
    border:1px solid rgba(240,128,60,.18) !important;

    box-shadow:
        0 0 22px rgba(240,128,60,.12);
}

/* =========================================================
   SLIDER
========================================================= */

.stSlider > div > div > div > div{
    background:
        linear-gradient(
            90deg,
            rgba(240,128,60,.9),
            rgba(74,144,217,.9)
        ) !important;
}
/* =========================================================
   BAR CHART
========================================================= */

.chart-glass{
    padding:28px;

    border-radius:28px;

    border:1px solid rgba(255,255,255,.08);

    background:
        linear-gradient(
            145deg,
            rgba(255,255,255,.04),
            rgba(255,255,255,.015)
        );

    backdrop-filter:blur(18px);

    box-shadow:var(--shadow);

    animation:fadeUp .7s ease;
}

.cont-row{
    display:flex;
    align-items:center;
    gap:16px;

    margin-bottom:20px;
}

.cont-dot{
    width:18px;
    height:18px;

    border-radius:999px;

    box-shadow:
        0 0 14px currentColor,
        0 0 24px currentColor;
}

.cont-name{
    width:180px;
    font-weight:700;
}

.cont-bar-bg{
    flex:1;

    height:18px;

    overflow:hidden;

    border-radius:999px;

    background:
        rgba(255,255,255,.05);
}

.cont-bar-fill{
    position:relative;

    height:100%;

    border-radius:999px;

    animation:fadeUp 1s ease;
}

.cont-bar-fill::after{
    content:"";

    position:absolute;

    top:0;
    left:-100%;

    width:40%;
    height:100%;

    background:
        linear-gradient(
            90deg,
            transparent,
            rgba(255,255,255,.35),
            transparent
        );

    animation:shimmer 3s linear infinite;
}

/* =========================================================
   DATAFRAME
========================================================= */

[data-testid="stDataFrame"]{
    border-radius:24px;

    overflow:hidden;

    border:1px solid rgba(255,255,255,.08);

    box-shadow:var(--shadow);

    animation:fadeUp .7s ease;
}

[data-testid="stDataFrame"]:hover{
    box-shadow:
        var(--shadow-hover),
        0 0 30px rgba(240,128,60,.08);
}

/* =========================================================
   DIALOG
========================================================= */

[data-testid="stDialog"] > div{
    border-radius:28px !important;

    border:1px solid rgba(255,255,255,.08);

    backdrop-filter:blur(22px);

    box-shadow:
        0 25px 60px rgba(0,0,0,.45);

    animation:fadeUp .35s ease;
}

/* =========================================================
   SCROLLBAR
========================================================= */

::-webkit-scrollbar{
    width:10px;
    height:10px;
}

::-webkit-scrollbar-thumb{
    background:
        linear-gradient(
            180deg,
            rgba(240,128,60,.7),
            rgba(74,144,217,.7)
        );

    border-radius:999px;
}

/* =========================================================
   MOBILE
========================================================= */

@media (max-width: 900px){

    .header-style{
        font-size:32px;
        padding:28px;
    }

    .cont-name{
        width:110px;
        font-size:15px;
    }

}

</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# MODAL
# ══════════════════════════════════════════════════════════════════

@st.dialog("ข้อมูลนักวิจัย", width="large")
def show_modal(author_id):

    row = authors[authors["author_id"] == author_id]

    if row.empty:
        return

    a = row.iloc[0]

    exp = (
        df[df["author_id"] == author_id]
        .sort_values("expertise_score", ascending=False)
    )

    total_score = exp["expertise_score"].sum()

    st.markdown(f"## {a['author_name']}")
    st.caption(a.get("profile", "—"))

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("บทความ", int(a.get("author_papers", 0)))
    c2.metric("First Author", int(a.get("first_author_papers", 0)))
    c3.metric("Corresponding", int(a.get("corresponding_papers", 0)))
    c4.metric("Score", f"{total_score:,.0f}")

    st.markdown("### ความเชี่ยวชาญ")

    st.dataframe(
        exp[
            ["taxonomy_id","l1_field","l2_domain", "subfield_name", "expertise_score"]
        ],
        use_container_width=True,
        hide_index=True
    )

# ══════════════════════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════════════════════

st.markdown(
    '<div class="header-style">🌍 การกระจายตัวของนักวิจัยรายภูมิภาค</div>',
    unsafe_allow_html=True
)

# ══════════════════════════════════════════════════════════════════
# FILTER PANEL
# ══════════════════════════════════════════════════════════════════

with st.container():

    f1, f2, f3 = st.columns([2,2,2])

    with f1:

        all_conts = sorted(
            authors["continent"].dropna().unique().tolist()
        )

        sel_conts = st.multiselect(
            "🗺️ กรองทวีป",
            options=all_conts,
            default=all_conts
        )

    with f2:

        all_l1 = sorted(
            df["l1_field"].dropna().unique().tolist()
        )

        sel_fields = st.multiselect(
            "📚 กรองสาขาวิชา",
            options=all_l1,
            placeholder="ทุกสาขา"
        )

    with f3:

        max_p = max(
            int(authors["author_papers"].max()),
            2
        )

        min_p = st.slider(
            "📄 จำนวนบทความขั้นต่ำ",
            1,
            max_p,
            1
        )

    st.markdown("</div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# FILTER DATA
# ══════════════════════════════════════════════════════════════════

def get_continent(profile):

    if pd.isna(profile):
        return "ไม่ทราบ"

    text = str(profile).lower()

    for continent, keywords in CONTINENT_KEYWORDS.items():

        # keyword ยาวก่อน
        keywords_sorted = sorted(
            keywords,
            key=len,
            reverse=True
        )

        for kw in keywords_sorted:

            if kw.lower() in text:
                return continent

    return "ไม่ทราบ"


# =========================
# CREATE CONTINENT
# =========================

authors["continent"] = (
    authors["profile"]
    .apply(get_continent)
)

# =========================
# FILTER
# =========================

fa = authors[
    authors["continent"].isin(sel_conts)
].copy()

fa = fa[
    fa["author_papers"] >= min_p
]

if sel_fields:

    valid_ids = df[
        df["l1_field"].isin(sel_fields)
    ]["author_id"].unique()

    fa = fa[
        fa["author_id"].isin(valid_ids)
    ]

fd = df[
    df["author_id"].isin(fa["author_id"])
]

# ══════════════════════════════════════════════════════════════════
# KPI
# ══════════════════════════════════════════════════════════════════

k1, k2, k3, k4 = st.columns(4)

k1.metric("นักวิจัย", f"{len(fa):,}")
k2.metric("ทวีปที่พบ", fa["continent"].nunique())
k3.metric("สาขาวิชา", fd["l1_field"].nunique())
k4.metric(
    "คะแนนเฉลี่ย",
    f"{fd['expertise_score'].mean():,.1f}"
    if not fd.empty else "0"
)

st.divider()

# ══════════════════════════════════════════════════════════════════
# BAR CHART
# ══════════════════════════════════════════════════════════════════

cont_counts = (
    fa["continent"]
    .value_counts()
    .reset_index()
)

cont_counts.columns = [
    "ทวีป",
    "จำนวนนักวิจัย"
]

cont_counts["สี"] = (
    cont_counts["ทวีป"]
    .map(CONTINENT_COLORS)
)

cont_counts["Flag"] = (
    cont_counts["ทวีป"]
    .map(CONTINENT_FLAGS)
)

cont_counts["สัดส่วน"] = (
    cont_counts["จำนวนนักวิจัย"]
    / cont_counts["จำนวนนักวิจัย"].sum()
    * 100
)

col_bar, col_stat = st.columns([1.2, 1])

with col_bar:
    st.markdown('<div class="sec-header">📊 สัดส่วนนักวิจัยตามทวีป</div>', unsafe_allow_html=True)
    max_cnt = cont_counts["จำนวนนักวิจัย"].max()
    bars_html = ""
    for _, row in cont_counts.iterrows():
        bar_w = (row["จำนวนนักวิจัย"] / max_cnt) * 100
        bars_html += f"""
        <div class="cont-row">
          <div class="cont-name">{row['Flag']} {row['ทวีป']}</div>
          <div class="cont-bar-bg">
            <div class="cont-bar-fill" style="width:{bar_w:.1f}%;background:{row['สี']}"></div>
          </div>
          <div class="cont-pct">{row['สัดส่วน']:.1f}%</div>
          <div class="cont-cnt">{row['จำนวนนักวิจัย']:,} คน</div>
        </div>"""
    st.markdown(bars_html, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# TABLE
# ══════════════════════════════════════════════════════════════════

with col_stat:

    st.markdown(
        '<div class="sec-header">📋 สถิติสรุปรายทวีป</div>',
        unsafe_allow_html=True
    )

    detail_rows = []

    for _, row in cont_counts.iterrows():

        cont = row["ทวีป"]

        sub = fa[
            fa["continent"] == cont
        ]

        avg_papers = sub["author_papers"].mean()

        avg_score = fd[
            fd["author_id"].isin(sub["author_id"])
        ]["expertise_score"].mean()

        top_author = (
            sub.sort_values(
                "expertise_score",
                ascending=False
            )
            .iloc[0]["author_name"]
        )

        detail_rows.append({
            "ทวีป": f"{row['Flag']} {cont}",
            "นักวิจัย": row["จำนวนนักวิจัย"],
            "บทความเฉลี่ย": f"{avg_papers:.0f}",
            "คะแนนเฉลี่ย": f"{avg_score:,.0f}",
            "อันดับ 1": top_author
        })

    st.dataframe(
        pd.DataFrame(detail_rows),
        use_container_width=True,
        hide_index=True,
        height=430
    )

# ══════════════════════════════════════════════════════════════════
# Heatmap
# ══════════════════════════════════════════════════════════════════
st.markdown('<div class="sec-header">🗂️ การกระจายตัวตามสาขาวิชา (L1 Field) รายทวีป</div>', unsafe_allow_html=True)

pivot = (
    fd[fd["author_id"].isin(fa["author_id"])]
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
# TOP AUTHORS
# ══════════════════════════════════════════════════════════════════

st.markdown(
    '<div class="sec-header">🏆 นักวิจัยชั้นนำแยกตามทวีป</div>',
    unsafe_allow_html=True
)

selected_tab_cont = st.selectbox(
    "เลือกทวีป",
    sel_conts
)

top_authors = (
    fa[
        fa["continent"] == selected_tab_cont
    ]
    .sort_values(
        "expertise_score",
        ascending=False
    )
    .head(8)
)

if not top_authors.empty:

    cols = st.columns(4)

    continent_color = CONTINENT_COLORS.get(
        selected_tab_cont,
        "#666"
    )

    for idx, (_, row) in enumerate(top_authors.iterrows()):

        with cols[idx % 4]:

            card_html = f"""
            <html>
            <head>

            <style>

            body{{
                margin:2px;
                padding:1px;
                background:transparent;
                font-family:'Sarabun',sans-serif;
            }}

            .author-card{{
                position:relative;
                overflow:hidden;

                height:175px;

                padding:20px;

                border-radius:28px;

                background:
                    linear-gradient(
                        145deg,
                        {continent_color}22,
                        rgba(20,20,20,.92)
                    );

                border:1px solid {continent_color}40;

                backdrop-filter:blur(20px);

                box-shadow:
                    0 10px 35px rgba(0,0,0,.45),
                    0 0 30px {continent_color}22;

                transition:all .35s ease;
            }}

            /* glow */

            .author-card::before{{
                content:"";

                position:absolute;

                top:-40px;
                right:-40px;

                width:170px;
                height:170px;

                border-radius:999px;

                background:{continent_color};

                filter:blur(70px);

                opacity:.28;
            }}

            .author-card::after{{
                content:"";

                position:absolute;

                inset:0;

                background:
                    linear-gradient(
                        135deg,
                        rgba(255,255,255,.08),
                        transparent 45%
                    );
            }}

            /* rank */

            .author-rank{{
                position:relative;
                z-index:2;

                display:inline-block;

                padding:6px 14px;

                border-radius:999px;

                background:{continent_color}22;

                border:1px solid {continent_color}66;

                color:#FFFFFF;

                font-size:12px;
                font-weight:800;

                letter-spacing:1px;

                margin-bottom:16px;

                box-shadow:
                    0 0 18px {continent_color}33;
            }}

            /* name */

            .author-name{{
                position:relative;
                z-index:2;

                font-size:24px;
                font-weight:800;

                line-height:1.2;

                color:#FFFFFF;

                margin-bottom:16px;

                text-shadow:
                    0 2px 10px rgba(0,0,0,.45);
            }}

            /* meta */

            .author-meta{{
                position:relative;
                z-index:2;

                color:rgba(255,255,255,.82);

                font-size:15px;
                font-weight:600;

                margin-bottom:14px;
            }}

            /* score */

            .author-score{{
                position:relative;
                z-index:2;

                font-size:30px;
                font-weight:900;

                color:#FFFFFF;

                text-shadow:
                    0 0 14px {continent_color}55;
            }}

            .author-score span{{
                display:block;

                margin-top:4px;

                font-size:12px;
                font-weight:700;

                letter-spacing:1px;

                color:rgba(255,255,255,.62);
            }}

            </style>

            </head>

            <body>

            <div class="author-card">

                <div class="author-rank">
                    TOP #{idx + 1}
                </div>

                <div class="author-name">
                    {row['author_name']}
                </div>

                <div class="author-meta">
                    📄 {row['author_papers']} papers
                </div>

                <div class="author-score">
                    ⭐ {row['expertise_score']:,.0f}
                    <span>Expertise Score</span>
                </div>

            </div>

            </body>
            </html>
            """

            components.html(
                card_html,
                height=220
            )

            if st.button(
                "ดูข้อมูล",
                key=f"btn_{row['author_id']}"
            ):
                show_modal(row["author_id"])

# ══════════════════════════════════════════════════════════════════
# SEARCH TABLE
# ══════════════════════════════════════════════════════════════════

st.markdown(
    '<div class="sec-header">🔍 ค้นหาข้อมูลทั้งหมด</div>',
    unsafe_allow_html=True
)

search_term = st.text_input(
    "ค้นหาชื่อนักวิจัยหรือสังกัด..."
)

display_df = fa[
    [
        "author_name",
        "continent",
        "profile",
        "author_papers",
        "expertise_score"
    ]
].copy()

if search_term:

    display_df = display_df[
        (
            display_df["author_name"]
            .str.contains(search_term, case=False, na=False)
        )
        |
        (
            display_df["profile"]
            .astype(str)
            .str.contains(search_term, case=False, na=False)
        )
    ]

st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True,
    height=520
)