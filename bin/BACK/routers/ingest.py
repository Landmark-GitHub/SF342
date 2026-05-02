from fastapi import APIRouter, HTTPException, Request
import pandas as pd
import os
from .state import LATEST_FILE
import analytics.encode as encode

router = APIRouter(prefix="/ingest", tags=["Ingest"])

PROC_DIR = "storage/processed"
os.makedirs(PROC_DIR, exist_ok=True)
TOP3_PATH = os.path.join(PROC_DIR, "df_top3.csv")


@router.post("/")
async def ingest_file(request: Request):

    print("\n🚀 INGEST START")

    raw_path = LATEST_FILE.get("raw_path")

    if not raw_path:
        raise HTTPException(400, "File not found. Please upload at /upload first.")

    print(f"📄 Input file: {raw_path}")

    delimiter = "\t" if raw_path.endswith(".tsv") else ","
    df = pd.read_csv(raw_path, sep=delimiter)

    print(f"📊 Input rows: {len(df)}")

    # ---------- LOAD STATE ----------
    model = getattr(request.app.state, "model", None)
    tax_embeddings = getattr(request.app.state, "tax_embeddings", None)
    df_tax = getattr(request.app.state, "df_tax", None)

    print("\n🔍 STATE CHECK")
    print("model:", model is not None)
    print("tax_embeddings:", tax_embeddings is not None)
    print("df_tax:", df_tax is not None)

    if model is None or tax_embeddings is None or df_tax is None:
        raise HTTPException(
            500,
            "Model/taxonomy cache is not ready. Restart server and check logs."
        )

    # ---------- PROCESS ----------
    print("\n⚙️ Running mapping_hybrid...")

    try:
        df_final, metrics = encode.mapping_hybrid(
            df,
            df_tax,
            model,
            tax_embeddings
        )
    except Exception as e:
        print("❌ MAPPING FAILED")
        print(e)
        raise HTTPException(500, "Mapping process failed")

    out_path = os.path.join(PROC_DIR, "expertise_result.csv")
    
    t = df_final.copy()

    # key
    t['evidence_paper_ids_key'] = t['evidence_paper_ids'].apply(tuple)

    # -----------------------
    # 🔥 กันซ้ำก่อน
    # -----------------------
    t = t.drop_duplicates(
        subset=['author_id', 'taxonomy_id', 'evidence_paper_ids_key']
    )

    # -----------------------
    # 🔥 top3 ต่อ author ต่อ paper
    # -----------------------
    df_top3 = (
        t.sort_values('expertise_score', ascending=False)
        .groupby(['author_id', 'evidence_paper_ids_key'])
        .head(3)
        .reset_index(drop=True)
    )

    df_final.to_csv(out_path, index=False)
    df_top3.to_csv(TOP3_PATH, index=False)

    print("✅ DONE")
    print("\n📦 DF_TOP3 INFO")
    print(df_top3.info())

    print("\n📌 SAMPLE ROW")
    print(df_top3.iloc[0].to_dict())

    print("✅ DONE")
    
    # 1. แปลง DataFrame เป็น List of Dictionaries
    # orient="records" จะได้รูปแบบ [ {"col1": val1}, {"col2": val2} ]
    result_data = df_top3.to_dict(orient="records")

    # 2. (Optional แต่แนะนำ) ล้างค่า NaN หรือ NumPy types ที่อาจหลงเหลือ
    # FastAPI มี jsonable_encoder ช่วยจัดการระดับหนึ่ง แต่การแปลงเป็น standard list มักจะจบปัญหาได้ดีกว่า
    
    return {
        "status": "success",
        "total_rows": len(df_top3),
        "data": result_data
    }


@router.get("/top3")
async def get_top3(search: str = "", l1_field: str = "", limit: int = 200):
    if not os.path.exists(TOP3_PATH):
        raise HTTPException(404, "df_top3 not found. Please run /ingest first.")

    df = pd.read_csv(TOP3_PATH).fillna("")

    if search:
        q = search.lower().strip()
        df = df[
            df["author_name"].astype(str).str.lower().str.contains(q)
            | df["subfield_name"].astype(str).str.lower().str.contains(q)
            | df["l1_field"].astype(str).str.lower().str.contains(q)
            | df["l2_domain"].astype(str).str.lower().str.contains(q)
        ]

    if l1_field:
        df = df[df["l1_field"].astype(str) == l1_field]

    if limit > 0:
        df = df.head(limit)

    return {
        "total": int(len(df)),
        "filters": {"search": search, "l1_field": l1_field, "limit": limit},
        "data": df.to_dict(orient="records"),
    }