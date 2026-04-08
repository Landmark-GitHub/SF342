from fastapi import APIRouter, HTTPException
import pandas as pd

router = APIRouter(prefix="/papers", tags=["Papers"])

# โหลดข้อมูลไว้ล่วงหน้า (Caching)
DF_ALL = pd.read_csv("storage/processed/author_all.csv")
DF_ALL = DF_ALL.fillna("")

@router.get("/")
async def get_papers(page: int = 1, limit: int = 20):
    # ใช้ groupby รวบรวมข้อมูล authors เป็น list ภายในกลุ่ม EID
    # วิธีนี้จะเร็วกว่าการ iterrows() ซ้ำๆ ใน loop
    
    grouped = DF_ALL.groupby("EID")
    all_eids = list(grouped.groups.keys())
    
    total = len(all_eids)
    start = (page - 1) * limit
    end = start + limit
    
    paged_eids = all_eids[start:end]
    get_papers = []

    for eid in paged_eids:

        group = grouped.get_group(eid)
        row = group.iloc[0]

        # ---------- authors ----------
        authors = []
        for _, r in group.iterrows():

            aff = []
            if pd.notna(r["Affiliations"]):
                aff = [a.strip() for a in str(r["Affiliations"]).split(";")]

            authors.append({
                "author_id": r["author_list_number"],
                "full_name": r["author_list"],
                "affiliations": aff,
                "correspondence": pd.notna(r["Correspondence Address"])
            })

        # ---------- paper ----------
        paper = {
            "paper": {
                "title": row["Title"],
                "year": int(row["Year"]),
                "document_type": row["Document Type"],
                "publication_stage": row["Publication Stage"],
                "language": row["Language of Original Document"],
                "open_access": row["Open Access"],
                "source": row["Source"],
                "eid": row["EID"]
            },

            "authors": authors,

            "publication": {
                "source_title": row["Source title"],
                "abbreviated_title": row["Abbreviated Source Title"],
                "publisher": row["Publisher"],
                "editors": row["Editors"],
                "volume": row["Volume"],
                "issue": row["Issue"],
                "pages": f"{row['Page start']}-{row['Page end']}",
                "article_no": row["Art. No."],
                "issn": row["ISSN"],
                "isbn": row["ISBN"],
                "coden": row["CODEN"]
            },

            "content": {
                "abstract": row["Abstract"],
                "author_keywords": str(row["Author Keywords"]).split(";") if pd.notna(row["Author Keywords"]) else [],
                "index_keywords": str(row["Index Keywords"]).split(";") if pd.notna(row["Index Keywords"]) else [],
                "cited_by": int(row["Cited by"]),
                "pubmed_id": row["PubMed ID"]
            },

            "identifiers": {
                "doi": row["DOI"],
                "link": row["Link"]
            }
        }

        get_papers.append(paper)

    # ---------- pagination ----------
    total = len(get_papers)
    start = (page - 1) * limit
    end = start + limit

    return {
        "page": page,
        "limit": limit,
        "total": total,
        "data": get_papers[start:end]
    }

@router.get("/{eid}")
async def get_paper_by_eid(eid: str):
    # ค้นหาข้อมูลจาก DataFrame หลักที่โหลดไว้แล้ว
    group = DF_ALL[DF_ALL["EID"] == eid]

    if group.empty:
        raise HTTPException(status_code=404, detail="Paper not found")

    row = group.iloc[0]

    # ใช้ Logic การประกอบ JSON ชุดเดียวกับ Get All เพื่อความเหมือนกัน 100%
    authors = [
        {
            "author_id": r["author_list_number"],
            "full_name": r["author_list"],
            "affiliations": [a.strip() for a in str(r["Affiliations"]).split(";")] if r["Affiliations"] else [],
            "correspondence": bool(r["Correspondence Address"])
        }
        for _, r in group.iterrows()
    ]

    return {
        "paper": {
            "title": row["Title"],
            "year": int(row["Year"]) if row["Year"] else 0,
            "document_type": row["Document Type"],
            "publication_stage": row["Publication Stage"],
            "language": row["Language of Original Document"],
            "open_access": row["Open Access"],
            "source": row["Source"],
            "eid": row["EID"]
        },
        "authors": authors,
        "publication": {
            "source_title": row["Source title"],
            "abbreviated_title": row["Abbreviated Source Title"],
            "publisher": row["Publisher"],
            "editors": row["Editors"],
            "volume": row["Volume"],
            "issue": row["Issue"],
            "pages": f"{row['Page start']}-{row['Page end']}",
            "article_no": row["Art. No."],
            "issn": row["ISSN"],
            "isbn": row["ISBN"],
            "coden": row["CODEN"]
        },
        "content": {
            "abstract": row["Abstract"],
            "author_keywords": str(row["Author Keywords"]).split(";") if row["Author Keywords"] else [],
            "index_keywords": str(row["Index Keywords"]).split(";") if row["Index Keywords"] else [],
            "cited_by": int(row["Cited by"]) if row["Cited by"] else 0,
            "pubmed_id": row["PubMed ID"]
        },
        "identifiers": {
            "doi": row["DOI"],
            "link": row["Link"]
        }
    }