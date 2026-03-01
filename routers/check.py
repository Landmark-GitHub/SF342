# from fastapi import APIRouter, HTTPException
# import pandas as pd
# import os
# from .state import LATEST_FILE   # ⭐ ต้อง import

# router = APIRouter(prefix="/check", tags=["File Inspection"])


# @router.get("/")
# async def check_file():

#     file_path = LATEST_FILE.get("path")

#     if not file_path:
#         raise HTTPException(400, "No file uploaded yet")

#     if not os.path.exists(file_path):
#         raise HTTPException(404, "File not found")

#     delimiter = "\t" if file_path.endswith(".tsv") else ","

#     try:
#         df_head = pd.read_csv(file_path, sep=delimiter, nrows=5)

#         # นับ row แบบไม่กิน RAM
#         with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
#             row_count = sum(1 for _ in f) - 1

#     except Exception:
#         raise HTTPException(400, "Invalid CSV/TSV format")

#     return {
#         "filename": os.path.basename(file_path),
#         "rows": row_count,
#         "columns": len(df_head.columns),
#         "column_names": df_head.columns.tolist()
#     }

from fastapi import APIRouter, HTTPException
import json
from .state import LATEST_FILE

router = APIRouter(prefix="/check", tags=["Check"])


@router.get("/")
async def check_file():

    meta_path = LATEST_FILE.get("meta")
    if not meta_path:
        raise HTTPException(400, "Run /ingest first")

    with open(meta_path) as f:
        meta = json.load(f)

    return meta