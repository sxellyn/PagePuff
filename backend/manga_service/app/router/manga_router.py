from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.model.manga_model import Manga
from app.schema.manga_schema import MangaResponse
from typing import List

router = APIRouter()

@router.get("/mangas", response_model=List[MangaResponse])
def list_mangas(db: Session = Depends(get_db)):
    return db.query(Manga).all()

@router.get("/mangas/{manga_id}", response_model=MangaResponse)
def get_manga_by_id(manga_id: int, db: Session = Depends(get_db)):
    manga = db.query(Manga).filter(Manga.id == manga_id).first()
    if not manga:
        raise HTTPException(status_code=404, detail="Manga not found")
    return manga
