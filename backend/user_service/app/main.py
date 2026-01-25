from fastapi import FastAPI
from app.router.user_router import router as user_router
from app.router.favorite_router import router as favorite_router
from app.router import auth_router

pagepuff = FastAPI()

@pagepuff.get("/")
async def root():
    return {"message": "User Service - PagePuff"}

@pagepuff.get("/health")
async def health_check():
    return {"status": "healthy", "service": "user"}

pagepuff.include_router(user_router, tags=["Users"])
pagepuff.include_router(favorite_router, tags=["Favorites"])  # Sem prefixo, gateway já roteia /user/favorites
pagepuff.include_router(auth_router.router, prefix="")  # login sem prefixo