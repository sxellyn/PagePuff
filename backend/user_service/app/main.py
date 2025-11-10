from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.router.user_router import router as user_router
from app.router.favorite_router import router as favorite_router
from app.router import auth_router

pagepuff = FastAPI()

# Configurar CORS
pagepuff.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend React
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@pagepuff.get("/")
async def root():
    return {"message": "User Service - PagePuff"}

@pagepuff.get("/health")
async def health_check():
    return {"status": "healthy", "service": "user"}

pagepuff.include_router(user_router, prefix="/user", tags=["Users"])
pagepuff.include_router(favorite_router, prefix="/favorite", tags=["Favorites"])
pagepuff.include_router(favorite_router, prefix="/user", tags=["User Favorites"])
pagepuff.include_router(auth_router.router, prefix="/user", tags=["Authentication"])