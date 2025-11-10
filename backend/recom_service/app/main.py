from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.router import router as recommendation_router

app = FastAPI(title="PagePuff Recommendation Service", version="1.0.0")

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
    return {
        "message": "Recommendation Service - PagePuff",
        "version": "1.0.0",
        "endpoints": [
            "/train - Treinar modelo de recomendação",
            "/recommendations - Gerar recomendações",
            "/clusters - Informações dos clusters",
            "/status - Status do serviço",
            "/refresh-cache - Atualizar cache"
        ]
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "recommendation"}

# Incluir router de recomendações
app.include_router(recommendation_router, tags=["Recommendations"])
