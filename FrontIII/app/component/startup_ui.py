import streamlit as st
import time

from src.services.loader import step_load_model, step_load_taxonomy


@st.dialog("🚀 กำลังเตรียมระบบ", width="large")
def startup_modal():

    progress = st.progress(0)
    status = st.empty()

    result = {
        "model": None,
        "df_tax": None,
        "tax_embeddings": None,
        "device": None,
        "model_load_seconds": None,
        "taxonomy_load_seconds": None,
        "errors": []
    }

    # ================= STEP 1 =================
    status.info("🔄 Step 1/2: Loading model...")
    try:
        model, device, t_model = step_load_model()
        result["model"] = model
        result["device"] = device
        result["model_load_seconds"] = t_model
        progress.progress(50)
    except Exception as e:
        status.error(f"Model error: {e}")
        st.stop()

    # ================= STEP 2 =================
    status.info("🔄 Step 2/2: Encoding taxonomy...")
    try:
        df, emb, t_tax = step_load_taxonomy(model)
        result["df_tax"] = df
        result["tax_embeddings"] = emb
        result["taxonomy_load_seconds"] = t_tax
        progress.progress(100)
    except Exception as e:
        status.error(f"Taxonomy error: {e}")
        st.stop()

    status.success(f"✅ Ready | Model {t_model}s | Tax {t_tax}s")

    st.session_state["resources"] = result

    time.sleep(0.5)
    st.rerun()