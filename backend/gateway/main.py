from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
import httpx
import os
from dotenv import load_dotenv

load_dotenv('config.env')

app = FastAPI(title="PagePuff API Gateway", version="1.0.0")

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configurações dos serviços
SERVICES = {
    "user": os.getenv("USER_SERVICE_URL", "http://user_service:8000"),
    "manga": os.getenv("MANGA_SERVICE_URL", "http://manga_service:8000"),
    "rating": os.getenv("RATING_SERVICE_URL", "http://rating_service:8000"),
    "recommendation": os.getenv("RECOMMENDATION_SERVICE_URL", "http://recom_service:8000"),
}

@app.get("/")
async def root():
    return {"message": "PagePuff API Gateway", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "gateway": "running"}

async def forward_request(service_url: str, request: Request, path: str):
    """Encaminha a requisição para o serviço apropriado"""
    try:
        # Construir URL completa
        target_url = f"{service_url}{path}"
        print(f"🔀 Gateway: Encaminhando requisição para {target_url}")
        
        # Preparar headers
        headers = dict(request.headers)
        # Remover headers que podem causar problemas
        headers.pop("host", None)
        headers.pop("content-length", None)
        
        # Preparar body se existir
        body = None
        if request.method in ["POST", "PUT", "PATCH"]:
            body = await request.body()
        
        print(f"🔀 Gateway: Método: {request.method}, Headers: {headers}")
        
        # Fazer requisição para o serviço
        async with httpx.AsyncClient() as client:
            print(f"🔀 Gateway: Fazendo requisição para {target_url}")
            response = await client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                content=body,
                params=request.query_params,
                timeout=30.0
            )
            
            print(f"🔀 Gateway: Resposta recebida: {response.status_code}")
            
            # Retornar resposta serializável
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers)
            )
            
    except httpx.ConnectError as e:
        print(f"❌ Gateway: Erro de conexão com {service_url}: {e}")
        raise HTTPException(status_code=503, detail=f"Serviço indisponível: {service_url}")
    except httpx.TimeoutException as e:
        print(f"⏰ Gateway: Timeout ao conectar com {service_url}: {e}")
        raise HTTPException(status_code=504, detail="Timeout ao conectar com o serviço")
    except Exception as e:
        print(f"💥 Gateway: Erro interno: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

# Rotas para User Service
@app.api_route("/user/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def user_service(request: Request, path: str):
    full_path = f"/user/{path}"
    return await forward_request(SERVICES["user"], request, full_path)

# Rotas para Manga Service
@app.api_route("/manga/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def manga_service(request: Request, path: str):
    # Remover o prefixo /manga para não duplicar
    return await forward_request(SERVICES["manga"], request, f"/{path}")

# Rotas para Rating Service
@app.api_route("/rating/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def rating_service(request: Request, path: str):
    # Remover o prefixo /rating para não duplicar
    return await forward_request(SERVICES["rating"], request, f"/{path}")

# Rotas para Recommendation Service
@app.api_route("/recommendation/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def recommendation_service(request: Request, path: str):
    # Remover o prefixo /recommendation para não duplicar
    return await forward_request(SERVICES["recommendation"], request, f"/{path}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=os.getenv("GATEWAY_HOST", "0.0.0.0"),
        port=int(os.getenv("GATEWAY_PORT", 8000)),
        reload=True
    )
