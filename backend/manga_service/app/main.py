from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.router.manga_router import router as manga_router

app = FastAPI()

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend React
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Manga Service - PagePuff"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "manga"}

app.include_router(manga_router, prefix="", tags=["Mangas"])
