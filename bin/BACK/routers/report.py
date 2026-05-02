# routers/report.py
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import pandas as pd
import matplotlib.pyplot as plt
import os

router = APIRouter(
    prefix="/report",
    tags=["Reports & Graphs"]
)

STORAGE_DIR = "storage"

@router.get("/graph/{filename}")
async def get_graph(filename: str):
    file_path = os.path.join(STORAGE_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    # ประมวลผล 100k rows (ใช้ sampling เพื่อความเร็ว)
    df = pd.read_csv(file_path).sample(n=1000)
    plt.figure()
    df.plot()
    
    graph_name = f"graph_{filename}.png"
    plt.savefig(graph_name)
    plt.close()
    
    return FileResponse(graph_name, media_type="image/png")