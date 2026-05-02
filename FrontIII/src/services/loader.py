import os
import time
import torch
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer

# ================= CONFIG =================
BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../")
)

MODEL_DIR = os.path.join(BASE_DIR, "model_cache")

RAW_DATA_DIR = os.path.join(
    BASE_DIR,
    "storage",
    "raw_data"
)

TAXONOMY_PATH = os.path.join(
    BASE_DIR,
    "analytics",
    "drive-download-20260206T091016Z-1-001",
    "keyword_dictionary_10000.csv"
)

# ✅ use npy instead of pt
TAXONOMY_EMBED_PATH = os.path.join(
    RAW_DATA_DIR,
    "taxonomy_embeddings.npy"
)

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

os.makedirs(RAW_DATA_DIR, exist_ok=True)


# ================= UTILS =================
def normalize_text(text):
    return str(text).lower().strip()


def resolve_taxonomy_path():

    if os.path.exists(TAXONOMY_PATH):
        return TAXONOMY_PATH

    for root, _, files in os.walk(BASE_DIR):
        if "keyword_dictionary_10000.csv" in files:
            return os.path.join(root, "keyword_dictionary_10000.csv")

    raise RuntimeError("Taxonomy file NOT FOUND")


# ================= MODEL =================
def get_local_model_path():

    base = os.path.join(
        MODEL_DIR,
        "models--sentence-transformers--all-MiniLM-L6-v2",
        "snapshots"
    )

    if not os.path.exists(base):
        return None

    snapshots = os.listdir(base)

    if not snapshots:
        return None

    latest = os.path.join(base, snapshots[0])

    required = [
        "model.safetensors",
        "config.json",
        "modules.json"
    ]

    if all(os.path.exists(os.path.join(latest, f)) for f in required):
        return latest

    return None


def load_model():

    device = "cuda" if torch.cuda.is_available() else "cpu"

    local_path = get_local_model_path()

    if local_path:
        print(f"✅ Load model from LOCAL cache: {local_path}")

        model = SentenceTransformer(
            local_path,
            device=device
        )

    else:
        print("⬇️ Download model from HuggingFace...")

        model = SentenceTransformer(
            MODEL_NAME,
            device=device,
            cache_folder=MODEL_DIR
        )

    return model, device


# ================= TAXONOMY =================
def load_taxonomy_dataframe():

    path = resolve_taxonomy_path()

    df = pd.read_csv(path)

    df["keyword_norm"] = (
        df["keyword_norm"]
        .fillna("")
        .apply(normalize_text)
    )

    return df


# ================= SAVE EMBEDDINGS =================
def encode_and_save_taxonomy(model, df_tax):

    print("⚡ Encoding taxonomy...")

    embeddings = model.encode(
        df_tax["keyword_norm"].tolist(),
        batch_size=512,
        convert_to_tensor=False,      # IMPORTANT
        normalize_embeddings=True,
        show_progress_bar=True
    )

    embeddings = np.asarray(
        embeddings,
        dtype=np.float32
    )

    temp_path = TAXONOMY_EMBED_PATH + ".tmp.npy"

    # cleanup old temp file
    if os.path.exists(temp_path):
        try:
            os.remove(temp_path)
        except:
            pass

    # atomic save
    with open(temp_path, "wb") as f:

        np.save(f, embeddings)

        f.flush()

        os.fsync(f.fileno())

    os.replace(
        temp_path,
        TAXONOMY_EMBED_PATH
    )

    print(
        f"✅ Saved taxonomy embeddings → "
        f"{TAXONOMY_EMBED_PATH}"
    )

    return torch.from_numpy(embeddings)


# ================= LOAD EMBEDDINGS =================
def try_load_taxonomy_embeddings(
    device,
    expected_rows
):

    if not os.path.exists(TAXONOMY_EMBED_PATH):
        print("⚠️ No saved taxonomy embeddings found")
        return None

    try:

        embeddings = np.load(
            TAXONOMY_EMBED_PATH
        )

        # validate
        if embeddings.ndim != 2:
            raise RuntimeError(
                "Invalid embedding ndim"
            )

        if embeddings.shape[0] != expected_rows:
            raise RuntimeError(
                f"Row mismatch: "
                f"{embeddings.shape[0]} "
                f"vs {expected_rows}"
            )

        if embeddings.shape[1] != 384:
            raise RuntimeError(
                f"Embedding dim mismatch: "
                f"{embeddings.shape[1]}"
            )

        embeddings = embeddings.astype(
            np.float32,
            copy=False
        )

        print(
            f"✅ Loaded taxonomy embeddings "
            f"{embeddings.shape}"
        )

        return torch.from_numpy(
            embeddings
        ).to(device)

    except Exception as e:

        print(
            f"❌ Corrupted embedding file: {e}"
        )

        try:
            os.remove(TAXONOMY_EMBED_PATH)
            print("🗑️ Deleted corrupted embedding file")
        except:
            pass

        return None


# ================= MAIN =================
def load_resources():

    result = {
        "model": None,
        "df_tax": None,
        "tax_embeddings": None,
        "device": None,
        "model_load_seconds": None,
        "taxonomy_load_seconds": None,
        "total_seconds": None,
        "errors": []
    }

    t0 = time.time()

    # =========================================================
    # STEP 1: LOAD MODEL
    # =========================================================
    try:

        t1 = time.time()

        model, device = load_model()

        result["model"] = model
        result["device"] = device

        result["model_load_seconds"] = round(
            time.time() - t1,
            2
        )

        print(
            f"✅ Model ready "
            f"({result['model_load_seconds']}s)"
        )

    except Exception as e:

        result["errors"].append(
            f"Model load failed: {e}"
        )

        return result

    # =========================================================
    # STEP 2: LOAD TAXONOMY CSV
    # =========================================================
    try:

        t2 = time.time()

        df_tax = load_taxonomy_dataframe()

        print(
            f"✅ Taxonomy CSV loaded "
            f"({len(df_tax):,} rows)"
        )

    except Exception as e:

        result["errors"].append(
            f"Taxonomy CSV load failed: {e}"
        )

        return result

    # =========================================================
    # STEP 3: LOAD / ENCODE EMBEDDINGS
    # =========================================================
    try:

        tax_embeddings = (
            try_load_taxonomy_embeddings(
                device=device,
                expected_rows=len(df_tax)
            )
        )

        # encode if missing/corrupted
        if tax_embeddings is None:

            tax_embeddings = (
                encode_and_save_taxonomy(
                    model,
                    df_tax
                )
            )

            tax_embeddings = tax_embeddings.to(device)

        result["df_tax"] = df_tax
        result["tax_embeddings"] = tax_embeddings

        result["taxonomy_load_seconds"] = round(
            time.time() - t2,
            2
        )

        print(
            f"✅ Taxonomy embeddings ready "
            f"({result['taxonomy_load_seconds']}s)"
        )

    except Exception as e:

        result["errors"].append(
            f"Taxonomy embedding failed: {e}"
        )

    # =========================================================
    # DONE
    # =========================================================
    result["total_seconds"] = round(
        time.time() - t0,
        2
    )

    print(
        f"🏁 load_resources total: "
        f"{result['total_seconds']}s"
    )

    return result

