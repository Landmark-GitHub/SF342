from fastapi import FastAPI
from routers import upload, check, ingest

app = FastAPI()

app.include_router(upload.router)
app.include_router(check.router)
app.include_router(ingest.router)

@app.get("/")
async def root():
    return {"message": "Welcome to CSV Processor API"}