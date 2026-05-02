import streamlit as st
import pandas as pd
import os
import math
from streamlit_agraph import agraph, Node, Edge, Config
# =========================
# 🎨 CONFIG & STYLE
# =========================
st.set_page_config(page_title="Knowledge Graph Explorer", layout="wide")
st.title(
    '🌐 กราฟความสัมพันธ์ของนักวิจัย'
)
st.markdown(
    """
    <style>
    html, body, [class*="css"] {
    font-family: 'Sarabun', sans-serif;
    background: #0E1117;
    color: #F5F7FA;
    font-size: 22px;
    line-height: 1.7;
}
    .main-title { font-size: 28px !important; font-weight: 700; color: #1E293B; }
    .label-text { font-size: 18px !important; font-weight: 600; color: #334155; }
    .stCaption { font-size: 14px !important; }
    </style>
""",
    unsafe_allow_html=True,
)
# =========================
# 📂 DATA LOADING (200k Rows)
# =========================
STORAGE_PATH = os.path.join("storage", "raw_data", "data_api.csv")

@st.cache_data(show_spinner="กำลังโหลดข้อมูลขนาดใหญ่...")
def load_and_prep_data(path):
    data = st.session_state.global_data
    df = data["df"].copy()
    # ล้างข้อมูล ID ให้เป็น String เพื่อป้องกันปัญหาตอนสร้าง Graph
    df["author_id"] = df["author_id"].astype(str)
    # ดึงชื่อประเทศจาก Profile (สมมติว่าเป็นคำสุดท้ายหลังเครื่องหมาย comma)
    df["country_extracted"] = df["profile"].apply(
        lambda x: str(x).split(",")[-1].strip() if pd.notnull(x) else "Unknown"
    )
    return df


df = load_and_prep_data(STORAGE_PATH)

if df.empty:
    st.error("❌ ไม่พบไฟล์ข้อมูล data_api.csv")
    st.stop()


# =========================
# 🧭 FILTER BY COUNTRY/REGION
# =========================


# เลือกประเทศ/ทวีป เพื่อลดปริมาณข้อมูลเหลือหลักร้อย/พัน
countries = sorted(df["country_extracted"].unique().tolist())
selected_country = st.selectbox(
    "🌍 เลือกประเทศ/พื้นที่เพื่อวิเคราะห์ (Filter by Region)", countries
)

# กรองข้อมูลตามที่เลือก
filtered_df = df[df["country_extracted"] == selected_country].copy()
# เลือกสาขาเพิ่มเติมเพื่อความชัดเจน
fields = ["All"] + sorted(filtered_df["l1_field"].unique().tolist())
selected_field = st.selectbox("🎯 สาขาวิชาหลัก (Field)", fields)

if selected_field != "All":
    filtered_df = filtered_df[filtered_df["l1_field"] == selected_field]

# สรุปจำนวนหน้าและรายการ
st.caption(f"🔎 พบนักวิจัย {len(filtered_df):,} ท่านในพื้นที่ {selected_country}")
# จำกัดจำนวน Node ที่จะแสดงผล (แนะนำไม่เกิน 100-150 เพื่อป้องกัน Browser ค้าง)

limit = st.slider("จำนวน Node ที่แสดงผล (Top Expertise)", 20, 200, 100)
graph_df = filtered_df.sort_values(by="expertise_score", ascending=False).head(limit)
st.divider()

# =========================
# 🕸️ GRAPH CONSTRUCTION (Fix Duplicate ID)
# =========================


def build_graph(data, root_label):
    nodes = []
    edges = []
    
    # 1. สร้าง Root Node (ขนาดตัวอักษร 24)
    nodes.append(Node(
        id="ROOT_NODE", 
        label=root_label, 
        size=35, 
        color="#FF4B4B",
        font={'size': 24, 'color': 'white', 'strokeWidth': 2, 'strokeColor': '#000000'}
    ))
    
    seen_nodes = set(["ROOT_NODE"])
    
    for _, row in data.iterrows():
        a_id = row["author_id"]
        field_id = f"FIELD_{row['l1_field']}"
        
        # 2. เพิ่ม Node สาขา (ขนาดตัวอักษร 20)
        if field_id not in seen_nodes:
            nodes.append(Node(
                id=field_id, 
                label=row["l1_field"], 
                size=25, 
                color="#1E88E5",
                font={'size': 20, 'color': '#E2E8F0'}
            ))
            edges.append(Edge(source="ROOT_NODE", target=field_id, color="#475569", width=2))
            seen_nodes.add(field_id)
            
        # 3. เพิ่ม Node นักวิจัย (ขนาดตัวอักษร 16)
        if a_id not in seen_nodes:
            # คำนวณขนาด Node ตามคะแนน
            dynamic_size = 12 + (min(row["expertise_score"], 50) / 2)
            
            nodes.append(Node(
                id=a_id,
                label=row["author_name"],
                size=dynamic_size,
                color="#FFFFFF",
                title=f"Score: {row['expertise_score']} | Subfield: {row['subfield_name']}",
                font={'size': 16, 'color': '#CBD5E1'}
            ))
            edges.append(Edge(source=field_id, target=a_id, color="#334155", width=1))
            seen_nodes.add(a_id)
            
    return nodes, edges


# ค่าคอนฟิกสำหรับ Graph

config = Config(
    width="100%",
    height=700,
    directed=True,
    physics=True,
    hierarchical=False,
    nodeHighlightBehavior=True,
    highlightColor="#F7AD19",
    # เพิ่มการตั้งค่าแรงดึงดูดเพื่อให้ Node กระจายตัวสวยงาม
    d3={
        "gravity": -200,
        "linkLength": 150,
        "charge": -500,
    },
    # บังคับให้ Label แสดงตลอดเวลา (ถ้า Library ที่ใช้รองรับ)
    staticGraph=False 
)


# วาดกราฟ

# วาดกราฟ
if not graph_df.empty:
    nodes, edges = build_graph(graph_df, selected_country)
    clicked_id = agraph(nodes=nodes, edges=edges, config=config)

    # === ส่วนที่แก้ไข/เพิ่มเติม: แสดงรายละเอียดเมื่อคลิก ===
    if clicked_id:
        
        # 1. กรณีคลิกที่ "Node สาขา" (ID จะขึ้นต้นด้วย FIELD_)
        if str(clicked_id).startswith("FIELD_"):
            field_name = str(clicked_id).replace("FIELD_", "")
            
            # กรองข้อมูลนักวิจัยที่มีสาขาตรงกับที่คลิก (จากกราฟที่แสดงอยู่)
            authors_in_field = graph_df[graph_df["l1_field"] == field_name]
            
            st.sidebar.markdown(f"### 🎯 สาขา: {field_name}")
            st.sidebar.info(f"พบนันวิจัยทั้งหมด {len(authors_in_field)} ท่านในหน้านี้")
            
            # แสดงรายชื่อนักวิจัยใน Sidebar
            for idx, row in authors_in_field.iterrows():
                with st.sidebar.expander(f"👤 {row['author_name']}"):
                    st.write(f"**Score:** {row['expertise_score']:.2f}")
                    st.write(f"**Subfield:** {row['subfield_name']}")
                    st.write(f"**Affiliation:** {row['profile']}")

        # 2. กรณีคลิกที่ "Node นักวิจัย" (ID ปกติ)
        else:
            info = df[df["author_id"] == str(clicked_id)]
            if not info.empty:
                res = info.iloc[0]
                st.sidebar.markdown(f"### 👤 ข้อมูลนักวิจัย")
                st.sidebar.success(f"**{res['author_name']}**")
                st.sidebar.markdown(f"**ID:** `{res['author_id']}`")
                st.sidebar.markdown(f"**Field (L1):** {res['l1_field']}")
                st.sidebar.markdown(f"**Domain (L2):** {res['l2_domain']}")
                st.sidebar.markdown(f"**Subfield:** {res['subfield_name']}")
                st.sidebar.divider()
                st.sidebar.markdown(f"**สังกัด:** {res['profile']}")
                
                st.sidebar.divider()
                c1, c2 = st.sidebar.columns(2)
                c1.metric("Expertise", f"{res['expertise_score']:.2f}")
                c2.metric("Papers", f"{int(res['paper_count'])}")

else:

    st.warning("ไม่มีข้อมูลสำหรับเงื่อนไขที่เลือก")
