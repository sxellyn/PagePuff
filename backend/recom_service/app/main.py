from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.router import recommendation_router

app = FastAPI(
    title="PagePuff Recommendation Service",
    description="K-Means based recommendation service for manga",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(recommendation_router.router, prefix="/recommendations", tags=["Recommendations"])

@app.get("/")
async def root():
    return {"message": "Recommendation Service - PagePuff", "algorithm": "K-Means Clustering"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "recommendation"}
