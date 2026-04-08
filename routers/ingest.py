from fastapi import APIRouter, HTTPException
import pandas as pd
import os
import json
from .state import LATEST_FILE
from analytics.Test import test_ingest
from analytics.expertise import format_author_name

router = APIRouter(prefix="/ingest", tags=["Ingest"])

PROC_DIR = "storage/processed"
os.makedirs(PROC_DIR, exist_ok=True)


@router.post("/")
async def ingest_file():

    raw_path = LATEST_FILE.get("raw_path")
    if not raw_path:
        raise HTTPException(400, "File not found. Please upload at /upload first.")

    delimiter = "\t" if raw_path.endswith(".tsv") else ","

    df = pd.read_csv(raw_path, sep=delimiter)

    dataAuthorAll = format_author_name(df)
    
    dataAuthorAll.to_csv("storage/processed/author_all.csv", index=False)

    return {
        "status": "Success Result dataAuthorAll",
        "rows": len(dataAuthorAll)
    }

# #STEP 2 — Clean Column ที่ใช้
#     df = dataTeamp[['EID', 'Author(s) ID', 'Author Keywords', 'Index Keywords', 'Cited by', 'Year']]

#     df['Author Keywords'] = df['Author Keywords'].fillna('')
#     df['Index Keywords'] = df['Index Keywords'].fillna('')

#     # รวม keyword ทั้งหมด
#     df['all_keywords'] = df['Author Keywords'] + ';' + df['Index Keywords']

    
#     #STEP 3 — Explode Authors
#     df['Author(s) ID'] = df['Author(s) ID'].astype(str).str.split(';')

#     author_paper = df[['EID', 'Author(s) ID']].explode('Author(s) ID')
#     author_paper['Author(s) ID'] = author_paper['Author(s) ID'].str.strip()


#     #STEP 4 — Explode Keywords   
#     df['all_keywords'] = df['all_keywords'].str.split(';')

#     paper_keyword = df[['EID', 'all_keywords']].explode('all_keywords')
#     paper_keyword['all_keywords'] = paper_keyword['all_keywords'].str.strip()

#     paper_keyword = paper_keyword[
#         paper_keyword['all_keywords'] != ''
#     ]

#     #STEP 5 — Merge Author + Keyword
#     author_keyword = author_paper.merge(
#         paper_keyword,
#         on='EID',
#         how='left'
#     )

#     author_keyword = author_keyword.rename(columns={
#         'Author(s) ID': 'author_id',
#         'all_keywords': 'keyword'
#     })

#     #STEP 6 — (OPTIONAL) ส่ง LLM รวมคำ
#     unique_keywords = author_keyword['keyword'].unique().tolist()
