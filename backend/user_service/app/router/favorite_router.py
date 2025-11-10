from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.config.database import connect_db
from app.model.favorite_model import Favorite
from app.schema.favorite_schema import FavoriteRequest, FavoriteResponse
from app.config.auth import get_current_user
from app.model.user_model import User
from typing import List

router = APIRouter()

@router.post("/favorites", response_model=FavoriteResponse)
def add_favorite(favorite: FavoriteRequest, db: Session = Depends(connect_db), current_user: User = Depends(get_current_user)):
    # Verificar se já existe
    existing = db.query(Favorite).filter(
        Favorite.user_id == current_user.id,
        Favorite.manga_id == favorite.manga_id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Manga já está nos favoritos")
    
    new_fav = Favorite(user_id=current_user.id, manga_id=favorite.manga_id)
    db.add(new_fav)
    db.commit()
    db.refresh(new_fav)
    return new_fav

@router.get("/favorites", response_model=List[FavoriteResponse])
def get_favorites(db: Session = Depends(connect_db), current_user: User = Depends(get_current_user)):
    return db.query(Favorite).filter(Favorite.user_id == current_user.id).all()

@router.delete("/favorites/{manga_id}")
def remove_favorite(manga_id: int, db: Session = Depends(connect_db), current_user: User = Depends(get_current_user)):
    favorite = db.query(Favorite).filter(
        Favorite.user_id == current_user.id,
        Favorite.manga_id == manga_id
    ).first()
    
    if not favorite:
        raise HTTPException(status_code=404, detail="Favorito não encontrado")
    
    db.delete(favorite)
    db.commit()
    return {"message": "Favorito removido com sucesso"}

@router.get("/favorites/{manga_id}/check")
def check_favorite(manga_id: int, db: Session = Depends(connect_db), current_user: User = Depends(get_current_user)):
    favorite = db.query(Favorite).filter(
        Favorite.user_id == current_user.id,
        Favorite.manga_id == manga_id
    ).first()
    
    return {"is_favorite": favorite is not None}
