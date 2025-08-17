from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx
import os
from dotenv import load_dotenv
import time
import json

load_dotenv()

app = FastAPI(
    title="PagePuff Gateway",
    description="API Gateway for PagePuff system",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=json.loads(os.getenv("ALLOWED_ORIGINS", '["http://localhost:3000"]')),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SERVICES = {
    "user": os.getenv("USER_SERVICE_URL", "http://user_service:8000"),
    "manga": os.getenv("MANGA_SERVICE_URL", "http://manga_service:8000"),
    "rating": os.getenv("RATING_SERVICE_URL", "http://rating_service:8000"),
    "recom": os.getenv("RECOM_SERVICE_URL", "http://recom_service:8000")
}

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

@app.get("/debug")
async def debug_env():
    return {
        "env_vars": {
            "USER_SERVICE_URL": os.getenv("USER_SERVICE_URL"),
            "MANGA_SERVICE_URL": os.getenv("MANGA_SERVICE_URL"),
            "RATING_SERVICE_URL": os.getenv("RATING_SERVICE_URL"),
            "RECOM_SERVICE_URL": os.getenv("RECOM_SERVICE_URL")
        },
        "services": SERVICES,
        "dotenv_loaded": True
    }

@app.api_route("/user/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def user_service_router(request: Request, path: str):
    return await route_request(request, "user", path)

@app.api_route("/manga/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def manga_service_router(request: Request, path: str):
    return await route_request(request, "manga", path)

@app.api_route("/rating/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def rating_service_router(request: Request, path: str):
    return await route_request(request, "rating", path)

@app.api_route("/recom/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def recom_service_router(request: Request, path: str):
    return await route_request(request, "recom", path)

async def route_request(request: Request, service_name: str, path: str):
    if service_name not in SERVICES:
        raise HTTPException(status_code=404, detail=f"Service {service_name} not found")
    
    service_url = SERVICES[service_name]
    target_url = f"{service_url}/{path}"
    
    body = None
    if request.method in ["POST", "PUT", "PATCH"]:
        try:
            body = await request.body()
        except:
            pass
    
    headers = dict(request.headers)
    headers.pop("host", None)
    headers.pop("content-length", None)
    
    query_params = dict(request.query_params)
    
    try:
        response = await http_client.request(
            method=request.method,
            url=target_url,
            params=query_params,
            headers=headers,
            content=body
        )
        
        return JSONResponse(
            content=response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text,
            status_code=response.status_code,
            headers=dict(response.headers)
        )
        
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Error connecting to service {service_name}: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal gateway error: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=os.getenv("GATEWAY_HOST", "0.0.0.0"),
        port=int(os.getenv("GATEWAY_PORT", 8000)),
        reload=True
    )
