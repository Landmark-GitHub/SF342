# from fastapi import APIRouter, UploadFile, File, HTTPException
# import os
# import shutil
# from .state import LATEST_FILE   # ⭐ ใช้ตัวเดียวกัน

# router = APIRouter(prefix="/upload", tags=["Upload Management"])

# UPLOAD_DIR = "storage"
# os.makedirs(UPLOAD_DIR, exist_ok=True)


# @router.post("/")
# async def upload_file(file: UploadFile = File(...)):

#     if not file.filename.endswith((".csv", ".tsv")):
#         raise HTTPException(400, "Only CSV / TSV allowed")

#     safe_name = os.path.basename(file.filename)
#     file_path = os.path.join(UPLOAD_DIR, safe_name)

#     try:
#         with open(file_path, "wb") as buffer:
#             shutil.copyfileobj(file.file, buffer)
#     except Exception as e:
#         raise HTTPException(500, f"Upload failed: {str(e)}")

#     # ⭐ บันทึกไฟล์ล่าสุด
#     LATEST_FILE["path"] = file_path

#     return {
#         "status": "uploaded",
#         "filename": safe_name,
#         "path": file_path
#     }

from fastapi import APIRouter, UploadFile, File, HTTPException
import os
import shutil
from .state import LATEST_FILE

router = APIRouter(prefix="/upload", tags=["Upload"])

RAW_DIR = "storage/raw"
os.makedirs(RAW_DIR, exist_ok=True)


@router.post("/")
async def upload_file(file: UploadFile = File(...)):

    if not file.filename.endswith((".csv", ".tsv")):
        raise HTTPException(400, "Only CSV/TSV allowed")

    file_path = os.path.join(RAW_DIR, file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    LATEST_FILE["raw_path"] = file_path

    return {"status": "uploaded", "path": file_path}