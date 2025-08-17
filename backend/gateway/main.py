from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx
import os
from dotenv import load_dotenv
import time
from typing import List
import json

# Carrega variáveis de ambiente
load_dotenv()

app = FastAPI(
    title="PagePuff Gateway",
    description="API Gateway para o sistema PagePuff",
    version="1.0.0"
)

# Configuração CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=json.loads(os.getenv("ALLOWED_ORIGINS", '["http://localhost:3000"]')),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# URLs dos serviços
SERVICES = {
    "user": os.getenv("USER_SERVICE_URL", "http://user_service:8000"),
    "manga": os.getenv("MANGA_SERVICE_URL", "http://manga_service:8000"),
    "rating": os.getenv("RATING_SERVICE_URL", "http://rating_service:8000"),
    "recom": os.getenv("RECOM_SERVICE_URL", "http://recom_service:8000")
}

# Cliente HTTP para fazer requisições aos serviços
http_client = httpx.AsyncClient(timeout=30.0)

@app.on_event("shutdown")
async def shutdown_event():
    await http_client.aclose()

@app.get("/")
async def root():
    return {
        "message": "🌸 PagePuff Gateway",
        "status": "online",
        "services": list(SERVICES.keys()),
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    """Verifica a saúde de todos os serviços"""
    health_status = {}
    
    for service_name, service_url in SERVICES.items():
        try:
            response = await http_client.get(f"{service_url}/health")
            health_status[service_name] = {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "response_time": response.elapsed.total_seconds()
            }
        except Exception as e:
            health_status[service_name] = {
                "status": "unhealthy",
                "error": str(e)
            }
    
    return {
        "gateway": "healthy",
        "services": health_status,
        "timestamp": time.time()
    }

# Roteamento para User Service
@app.api_route("/user/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def user_service_router(request: Request, path: str):
    """Roteia todas as requisições para o user service"""
    return await route_request(request, "user", path)

# Roteamento para Manga Service
@app.api_route("/manga/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def manga_service_router(request: Request, path: str):
    """Roteia todas as requisições para o manga service"""
    return await route_request(request, "manga", path)

# Roteamento para Rating Service
@app.api_route("/rating/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def rating_service_router(request: Request, path: str):
    """Roteia todas as requisições para o rating service"""
    return await route_request(request, "rating", path)

# Roteamento para Recom Service
@app.api_route("/recom/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def recom_service_router(request: Request, path: str):
    """Roteia todas as requisições para o recom service"""
    return await route_request(request, "recom", path)

async def route_request(request: Request, service_name: str, path: str):
    """Função auxiliar para rotear requisições aos serviços"""
    if service_name not in SERVICES:
        raise HTTPException(status_code=404, detail=f"Serviço {service_name} não encontrado")
    
    service_url = SERVICES[service_name]
    target_url = f"{service_url}/{path}"
    
    # Obtém o corpo da requisição
    body = None
    if request.method in ["POST", "PUT", "PATCH"]:
        try:
            body = await request.body()
        except:
            pass
    
    # Obtém os headers
    headers = dict(request.headers)
    # Remove headers que podem causar problemas
    headers.pop("host", None)
    headers.pop("content-length", None)
    
    # Obtém os query parameters
    query_params = dict(request.query_params)
    
    try:
        # Faz a requisição para o serviço
        response = await http_client.request(
            method=request.method,
            url=target_url,
            params=query_params,
            headers=headers,
            content=body
        )
        
        # Retorna a resposta do serviço
        return JSONResponse(
            content=response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text,
            status_code=response.status_code,
            headers=dict(response.headers)
        )
        
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Erro ao conectar com o serviço {service_name}: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno do gateway: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=os.getenv("GATEWAY_HOST", "0.0.0.0"),
        port=int(os.getenv("GATEWAY_PORT", 8000)),
        reload=True
    )
