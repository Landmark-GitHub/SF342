from fastapi import APIRouter, HTTPException
import pandas as pd
import os
import json
from .state import LATEST_FILE
from analytics.Test import test_ingest, format_author_name

router = APIRouter(prefix="/ingest", tags=["Ingest"])

PROC_DIR = "storage/processed"
os.makedirs(PROC_DIR, exist_ok=True)


@router.post("/")
async def ingest_file():

    raw_path = LATEST_FILE.get("raw_path")
    if not raw_path:
        raise HTTPException(400, "File not found. Please upload at /upload first.")

    delimiter = "\t" if raw_path.endswith(".tsv") else ","

    # อ่าน CSV ครั้งเดียว
    df = pd.read_csv(raw_path, sep=delimiter)
    df = df.where(pd.notnull(df), None)

    dataTest = test_ingest(df)

    data_Journal = os.path.join(PROC_DIR,"data_Journal.csv")
    LATEST_FILE["data_Journal"] = dataTest.to_csv(data_Journal, index=False)

    return {"papers": len(dataTest)}

