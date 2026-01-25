from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.config.database import connect_db
from app.model.favorite_model import Favorite
from app.schema.favorite_schema import FavoriteRequest, FavoriteResponse
from app.config.auth import get_current_user
from app.model.user_model import User
from typing import List

router = APIRouter()

@router.post("/favorites", response_model=FavoriteResponse)
def add_favorite(favorite: FavoriteRequest, db: Session = Depends(connect_db), current_user: User = Depends(get_current_user)):
    try:
        existing = db.query(Favorite).filter(
            Favorite.user_id == current_user.id,
            Favorite.manga_id == favorite.manga_id
        ).first()
        
        if existing:
            raise HTTPException(status_code=400, detail="Manga is already in favorites")
        
        new_fav = Favorite(user_id=current_user.id, manga_id=favorite.manga_id)
        db.add(new_fav)
        db.commit()
        db.refresh(new_fav)
        return new_fav
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        error_msg = str(e)
        if "duplicate entry" in error_msg.lower() or "unique_user_manga" in error_msg.lower() or "1062" in error_msg:
            raise HTTPException(
                status_code=400,
                detail="Manga is already in favorites"
            )
        if "foreign key constraint" in error_msg.lower() or "cannot add" in error_msg.lower():
            raise HTTPException(
                status_code=400,
                detail="Manga or user not found"
            )
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/favorites", response_model=List[FavoriteResponse])
def get_favorites(db: Session = Depends(connect_db), current_user: User = Depends(get_current_user)):
    try:
        favorites = db.query(Favorite).filter(Favorite.user_id == current_user.id).all()
        return favorites
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )
