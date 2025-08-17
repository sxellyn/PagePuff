from fastapi import FastAPI
from app.router.manga_router import router as manga_router

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Manga Service - PagePuff"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "manga"}

app.include_router(manga_router, prefix="", tags=["Mangas"])
