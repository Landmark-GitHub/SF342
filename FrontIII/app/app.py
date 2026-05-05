import streamlit as st
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.services.data_loader import prepare_all_data

st.set_page_config(page_title="ระบบวิเคราะห์ความเชี่ยวชาญ", page_icon="🔍")

home_page = st.Page(
    "pages/main.py",
    title="อัปโหลดข้อมูล",
    icon="📂",
    default=True
)

page_1 = st.Page(
    "pages/page_1.py",
    title="นักวิจัยและสาขา",
    icon="🏛️"
)

page_2 = st.Page(
    "pages/page_2.py",
    title="กราฟความเชี่ยวชาญ",
    icon="📊"
)

pg = st.navigation([
    home_page,
    page_1,
    page_2
])

# preload ทุก page
if "global_data" not in st.session_state:

    with st.spinner("Loading system..."):

        st.session_state.global_data = (
            prepare_all_data()
        )

pg.run()