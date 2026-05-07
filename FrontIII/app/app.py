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

page_3 = st.Page(
    "pages/page_3.py",
    title="การแยกความเชี่ยวชาญ",
    icon="🌳"
)

pg = st.navigation([
    home_page,
    page_1,
    page_2,
])


# preload ทุก page
if "global_data" not in st.session_state:
    with st.spinner("กำลังโหลดข้อมูลระบบ..."):
        try:
            data = prepare_all_data()
            
            # ตรวจสอบว่า df_raw มีข้อมูลหรือไม่
            if data["df_raw"].empty:
                st.warning("⚠️ ไม่พบข้อมูลในระบบ กรุณาอัปโหลดไฟล์ที่หน้า 'อัปโหลดข้อมูล'")
                st.session_state.global_data = data # เก็บก้อนข้อมูลว่างไว้ก่อน
                st.stop() # หยุดการทำงานของหน้าเพจที่เหลือ
            else:
                st.session_state.global_data = data
                
        except Exception as e:
            st.error(f"เกิดข้อผิดพลาดในการโหลดข้อมูล: {e}")
            st.stop()

pg.run()