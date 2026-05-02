import os
import time
import torch
import pandas as pd
from fastapi import FastAPI
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
from sentence_transformers import SentenceTransformer
from fastapi.staticfiles import StaticFiles

# ================= CONFIG =================
BASE_DIR = r"C:\Users\LandMark\Desktop\SF342\Program\SF342\BACK"

MODEL_DIR = os.path.join(BASE_DIR, "model_cache")

SPECIFIC_MODEL_PATH = os.path.join(
    MODEL_DIR,
    "models--sentence-transformers--all-MiniLM-L6-v2"
)

TAXONOMY_PATH = os.path.join(
    BASE_DIR,
    "analytics",
    "drive-download-20260206T091016Z-1-001",
    "keyword_dictionary_10000.csv"
)

MODEL_NAME = "all-MiniLM-L6-v2"


# ================= UTILS =================
def normalize_text(text):
    return str(text).lower().strip()


def resolve_taxonomy_path() -> str:
    """
    Find taxonomy CSV from common locations.
    Priority:
    1) env TAXONOMY_PATH
    2) configured TAXONOMY_PATH
    3) recursive search under BACK and project root
    """
    env_path = os.getenv("TAXONOMY_PATH")
    if env_path and os.path.exists(env_path):
        return env_path

    if os.path.exists(TAXONOMY_PATH):
        return TAXONOMY_PATH

    project_root = os.path.dirname(BASE_DIR)
    search_roots = [BASE_DIR, project_root]

    for root in search_roots:
        for dirpath, _, filenames in os.walk(root):
            if "keyword_dictionary_10000.csv" in filenames:
                return os.path.join(dirpath, "keyword_dictionary_10000.csv")

    raise RuntimeError(
        "Taxonomy file NOT FOUND. Checked TAXONOMY_PATH env, configured TAXONOMY_PATH, "
        "and recursive search for 'keyword_dictionary_10000.csv' under BACK/project root."
    )


# ================= LIFESPAN =================
@asynccontextmanager
async def lifespan(app: FastAPI):

    print("\n" + "="*60)
    print("🚀 STARTING FASTAPI SYSTEM")

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"🖥 Device: {device}")

    # init state
    app.state.model = None
    app.state.tax_embeddings = None
    app.state.df_tax = None
    app.state.model_load_seconds = None
    app.state.taxonomy_load_seconds = None
    app.state.startup_total_seconds = None
    startup_t0 = time.time()

    # ---------- STEP 1: LOAD MODEL ----------
    print("\n🚀 STEP 1: Load Model")
    step1_t0 = time.time()

    try:
        if os.path.exists(SPECIFIC_MODEL_PATH):
            print(f"✅ Model Found: {SPECIFIC_MODEL_PATH}")
        else:
            print(f"📥 Model not found → downloading to {MODEL_DIR}")

        model = SentenceTransformer(
            MODEL_NAME,
            device=device,
            cache_folder=MODEL_DIR
        )

        print("✅ Model loaded successfully")
        app.state.model_load_seconds = round(time.time() - step1_t0, 3)

    except Exception as e:
        print("❌ MODEL LOAD FAILED")
        print(e)
        raise RuntimeError("Model loading failed")

    # ---------- STEP 2: LOAD TAXONOMY ----------
    print("\n🚀 STEP 2: Load Taxonomy")
    step2_t0 = time.time()

    try:
        resolved_taxonomy_path = resolve_taxonomy_path()
        print(f"📄 Reading: {resolved_taxonomy_path}")
        df_tax = pd.read_csv(resolved_taxonomy_path)

        print(f"📊 Rows: {len(df_tax)}")

        df_tax["keyword_norm"] = (
            df_tax["keyword_norm"]
            .fillna("")
            .apply(normalize_text)
        )

        texts = df_tax["keyword_norm"].tolist()

        print(f"🔄 Encoding {len(texts)} keywords...")

        embeddings = model.encode(
            texts,
            batch_size=512,
            show_progress_bar=True,
            convert_to_tensor=True,
            normalize_embeddings=True
        )

        # ✅ SET STATE (สำคัญมาก)
        app.state.model = model
        app.state.tax_embeddings = embeddings
        app.state.df_tax = df_tax

        print("✅ Taxonomy encoded & stored in memory")
        app.state.taxonomy_load_seconds = round(time.time() - step2_t0, 3)

    except Exception as e:
        print("❌ TAXONOMY LOAD FAILED")
        print(e)
        raise RuntimeError("Taxonomy processing failed")

    # ---------- DEBUG ----------
    print("\n🔍 DEBUG STATE CHECK")
    print("model:", type(app.state.model))
    print("tax_embeddings:", type(app.state.tax_embeddings))
    print("df_tax:", type(app.state.df_tax))

    print("\n✨ API READY")
    app.state.startup_total_seconds = round(time.time() - startup_t0, 3)
    print("="*60 + "\n")

    yield

    print("🛑 Server shutting down...")


# ================= APP =================
from routers import ingest, paper, upload

app = FastAPI(
    title="SF342 API System",
    lifespan=lifespan
)

app.include_router(upload.router)
app.include_router(ingest.router)
app.include_router(paper.router)
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def root():
    return {
        "status": 200,
        "model_ready": app.state.model is not None,
        "taxonomy_ready": app.state.tax_embeddings is not None,
        "model_load_seconds": app.state.model_load_seconds,
        "taxonomy_load_seconds": app.state.taxonomy_load_seconds,
        "startup_total_seconds": app.state.startup_total_seconds,
    }


@app.get("/frontend")
async def frontend():
    return FileResponse("static/index.html")