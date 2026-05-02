# import time
# import hashlib
# import streamlit as st
# import pandas as pd

# from src.services.encode import mapping_hybrid


# def file_upload(resources):

#     uploaded_file = st.file_uploader(
#         "Upload CSV",
#         type=["csv"],
#         label_visibility="collapsed"
#     )

#     if uploaded_file is None:
#         return None

#     # =========================
#     # 🔑 CREATE FILE ID
#     # =========================
#     file_bytes = uploaded_file.getvalue()
#     file_id = hashlib.md5(file_bytes).hexdigest()

#     # =========================
#     # ✅ RETURN CACHE RESULT
#     # =========================
#     if (
#         "uploaded_result" in st.session_state
#         and st.session_state.get("uploaded_file_id") == file_id
#     ):
#         return st.session_state.uploaded_result

#     try:

#         # ⏱ START TIMER
#         t0 = time.time()

#         df_scopus = pd.read_csv(uploaded_file)

#         st.success("✅ อัปโหลดไฟล์สำเร็จ!")

#         with st.spinner("🚀 กำลังวิเคราะห์ความเชี่ยวชาญ..."):

#             df_result = mapping_hybrid(
#                 df_scopus=df_scopus, 
#                 model=resources["model"],
#                 df_tax=resources["df_tax"],
#                 tax_emb_matrix=resources["tax_embeddings"]
#             )

#         # ⏱ END TIMER
#         total_time = time.time() - t0

#         minutes = int(total_time // 60)
#         seconds = int(total_time % 60)

#         st.success(
#             f"✅ Mapping completed in {minutes}m {seconds}s"
#         )

#         # =========================
#         # 💾 SAVE CACHE
#         # =========================
#         st.session_state.uploaded_file_id = file_id
#         st.session_state.uploaded_result = df_result

#         return df_result

#     except Exception as e:

#         st.error(f"❌ Error: {e}")

#         return None


import time
import hashlib
import streamlit as st
import pandas as pd

from src.services.encode import mapping_hybrid


REQUIRED_COLUMNS = [
    "Authors",
    "Author full names",
    "Author(s) ID",
    "Title",
    "Year",
    "Source title",
    "Volume",
    "Issue",
    "Art. No.",
    "Page start",
    "Page end",
    "Cited by",
    "DOI",
    "Link",
    "Affiliations",
    "Authors with affiliations",
    "Abstract",
    "Author Keywords",
    "Index Keywords",
    "Correspondence Address",
    "Editors",
    "Publisher",
    "ISSN",
    "ISBN",
    "CODEN",
    "PubMed ID",
    "Language of Original Document",
    "Abbreviated Source Title",
    "Document Type",
    "Publication Stage",
    "Open Access",
    "Source",
    "EID"
]


def file_upload(resources):

    uploaded_file = st.file_uploader(
        "Upload CSV",
        type=["csv"],
        label_visibility="collapsed"
    )

    if uploaded_file is None:
        return None

    # =========================
    # 🔑 CREATE FILE ID
    # =========================
    file_bytes = uploaded_file.getvalue()
    file_id = hashlib.md5(file_bytes).hexdigest()

    # =========================
    # ✅ RETURN CACHE RESULT
    # =========================
    if (
        "uploaded_result" in st.session_state
        and st.session_state.get("uploaded_file_id") == file_id
    ):
        return st.session_state.uploaded_result

    try:

        # ⏱ START TIMER
        t0 = time.time()

        df_scopus = pd.read_csv(uploaded_file)

        # =========================
        # ✅ CHECK REQUIRED COLUMNS
        # =========================
        missing_cols = [
            col for col in REQUIRED_COLUMNS
            if col not in df_scopus.columns
        ]

        if missing_cols:

            st.error("❌ ไฟล์ CSV ไม่ถูกต้อง")

            st.warning("Missing columns:")

            st.code("\n".join(missing_cols))

            return None

        st.success("✅ อัปโหลดไฟล์สำเร็จ!")

        with st.spinner("🚀 กำลังวิเคราะห์ความเชี่ยวชาญ..."):

            df_result = mapping_hybrid(
                df_scopus=df_scopus,
                model=resources["model"],
                df_tax=resources["df_tax"],
                tax_emb_matrix=resources["tax_embeddings"]
            )

        # ⏱ END TIMER
        total_time = time.time() - t0

        minutes = int(total_time // 60)
        seconds = int(total_time % 60)

        st.success(
            f"✅ Mapping completed in {minutes}m {seconds}s"
        )

        # =========================
        # 💾 SAVE CACHE
        # =========================
        st.session_state.uploaded_file_id = file_id
        st.session_state.uploaded_result = df_result

        return df_result

    except Exception as e:

        st.error(f"❌ Error: {e}")

        return None