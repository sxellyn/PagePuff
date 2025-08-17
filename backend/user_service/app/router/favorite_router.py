from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.config.database import connect_db
from app.model.favorite_model import Favorite
from app.schema.favorite_schema import FavoriteRequest, FavoriteResponse
from app.config.auth import get_current_user
from app.model.user_model import User
from typing import List

router = APIRouter()

@router.post("/favorites", response_model=FavoriteRequest)
def add_favorite(favorite: FavoriteRequest, db: Session = Depends(connect_db), current_user: User = Depends(get_current_user)):
    new_fav = Favorite(user_id=current_user.id, manga_id=favorite.manga_id)
    db.add(new_fav)
    db.commit()
    db.refresh(new_fav)
    return new_fav

@router.get("/favorites", response_model=List[FavoriteResponse])
def get_favorites(db: Session = Depends(connect_db)):
    return db.query(Favorite).filter(Favorite.user_id == 1).all()
