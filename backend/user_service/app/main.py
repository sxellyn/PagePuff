from fastapi import FastAPI
from app.router.user_router import router as user_router
from app.router.favorite_router import router as favorite_router
from app.router import auth_router

pagepuff = FastAPI()

pagepuff.include_router(user_router, prefix="/user", tags=["Users"])
pagepuff.include_router(favorite_router, prefix="/favorite", tags=["Favorites"])
pagepuff.include_router(auth_router.router)