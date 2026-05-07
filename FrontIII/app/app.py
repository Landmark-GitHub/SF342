import streamlit as st
import pandas as pd
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.services.data_loader import prepare_all_data

st.set_page_config(page_title="ระบบวิเคราะห์ความเชี่ยวชาญ", page_icon="🔍")

STORAGE_PATH = os.path.join("storage", "raw_data", "data_api.csv")

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
# if "global_data" not in st.session_state:
#     with st.spinner("กำลังโหลดข้อมูลระบบ..."):
#         try:
#             data = prepare_all_data()
            
#             # ตรวจสอบว่า df_raw มีข้อมูลหรือไม่
#             if data["df_raw"].empty:
#                 st.warning("⚠️ ไม่พบข้อมูลในระบบ กรุณาอัปโหลดไฟล์ที่หน้า 'อัปโหลดข้อมูล'")
#                 st.session_state.global_data = data # เก็บก้อนข้อมูลว่างไว้ก่อน
#                 st.stop() # หยุดการทำงานของหน้าเพจที่เหลือ
#             else:
#                 st.session_state.global_data = data
                
#         except Exception as e:
#             st.error(f"เกิดข้อผิดพลาดในการโหลดข้อมูล: {e}")
#             st.stop()

# pg.run()

# preload ทุก page
if "global_data" not in st.session_state:

    with st.spinner("กำลังโหลดข้อมูลระบบ..."):

        try:
            data = prepare_all_data()

            # ตรวจสอบว่า df_raw มีข้อมูลหรือไม่
            if data["df_raw"].empty:

                st.warning(
                    "⚠️ ไม่พบข้อมูลในระบบ กรุณาอัปโหลดไฟล์ CSV"
                )

                uploaded_file = st.file_uploader(
                    "อัปโหลดไฟล์ CSV",
                    type=["csv"]
                )

                # ถ้ามีการอัปโหลดไฟล์
                if uploaded_file is not None:

                    df = pd.read_csv(uploaded_file)

                    # save ลง storage
                    os.makedirs(
                        os.path.dirname(STORAGE_PATH),
                        exist_ok=True
                    )

                    df.to_csv(STORAGE_PATH, index=False)

                    # clear cache
                    st.cache_data.clear()
                    
                    # ล้าง session เดิม
                    if "global_data" in st.session_state:
                        del st.session_state["global_data"]
                        
                    st.success("✅ อัปโหลดสำเร็จ กรุณารีเฟรชหน้า")

                st.stop()

            else:
                st.session_state.global_data = data

        except Exception as e:

            st.error(
                f"เกิดข้อผิดพลาดในการโหลดข้อมูล: {e}"
            )

            st.stop()

pg.run()
