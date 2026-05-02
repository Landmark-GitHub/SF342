from fastapi import APIRouter, UploadFile, File, HTTPException
import os
from pathlib import Path
from .state import LATEST_FILE

router = APIRouter(prefix="/upload", tags=["Upload"])

RAW_DIR = Path("storage/raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/")
async def upload_file(file: UploadFile = File(...)):

    # ✅ ตรวจสอบนามสกุลไฟล์
    if not file.filename.lower().endswith((".csv", ".tsv")):
        raise HTTPException(status_code=400, detail="Only CSV/TSV allowed")

    # ✅ ป้องกัน path traversal
    safe_name = os.path.basename(file.filename)
    file_path = RAW_DIR / safe_name

    # ✅ บันทึกไฟล์ (แก้ไข: ใช้ await file.read() แทน shutil.copyfileobj)
    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="File is empty")

    with open(file_path, "wb") as buffer:
        buffer.write(contents)

    # ✅ ดึงข้อมูลไฟล์
    file_size = file_path.stat().st_size  # bytes
    content_type = file.content_type

    # เก็บ path ล่าสุด
    LATEST_FILE["raw_path"] = str(file_path)

    return {
        "status": "uploaded",
        "file_name": safe_name,
        "content_type": content_type,
        "size_bytes": file_size,
        "size_mb": round(file_size / (1024 * 1024), 2),
        "path": str(file_path)
    }