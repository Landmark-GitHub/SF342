from fastapi import FastAPI
from routers import paper, upload, ingest

app = FastAPI()

app.include_router(upload.router)
app.include_router(ingest.router)
app.include_router(paper.router)


@app.get("/")
async def root():
    return {"message": "Welcome to CSV Processor API"}