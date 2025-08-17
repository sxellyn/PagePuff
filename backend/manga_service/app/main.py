from fastapi import FastAPI
from router.manga_router import router as manga_router

app = FastAPI()
app.include_router(manga_router, prefix="", tags=["Mangas"])
