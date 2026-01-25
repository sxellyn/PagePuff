from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func
from app.config.database import get_db
from app.model.manga_model import Manga
from app.schema.manga_schema import MangaResponse
from typing import List, Optional
from pydantic import BaseModel
import traceback

router = APIRouter()

@router.get("/mangas/categories")
def get_categories(db: Session = Depends(get_db)):
    """Returns all unique available categories"""
    try:
        import json
        mangas = db.query(Manga).all()
        all_tags = set()
        
        for manga in mangas:
            if manga.tags:
                try:
                    tags_str = manga.tags.replace("'", '"')
                    tags_list = json.loads(tags_str)
                    if isinstance(tags_list, list):
                        all_tags.update(tags_list)
                except:
                    pass
        
        return {"categories": sorted(list(all_tags))}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting categories: {str(e)}"
        )

class PaginatedMangaResponse(BaseModel):
    items: List[MangaResponse]
    total: int
    page: int
    limit: int
    total_pages: int

@router.get("/mangas", response_model=PaginatedMangaResponse)
def list_mangas(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    category: Optional[str] = Query(None, description="Filter by category/tag"),
    search: Optional[str] = Query(None, description="Search by title")
):
    try:
        import json
        
        query = db.query(Manga)
        
        if search:
            query = query.filter(
                func.lower(Manga.title).like(f"%{search.lower()}%")
            )
        
        if category:
            query = query.filter(
                Manga.tags.like(f"%'{category}'%")
            )
        
        total = query.count()
        
        if search:
            mangas = query.all()
            manga_items = [MangaResponse.from_orm(manga) for manga in mangas]
            
            return_limit = min(total, 10000) if total > 0 else 1
            
            return {
                "items": manga_items,
                "total": total,
                "page": 1,
                "limit": return_limit,
                "total_pages": 1
            }
        
        offset = (page - 1) * limit
        
        mangas = query.offset(offset).limit(limit).all()
        
        total_pages = (total + limit - 1) // limit if total > 0 else 1
        
        manga_items = [MangaResponse.from_orm(manga) for manga in mangas]
        
        return {
            "items": manga_items,
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": total_pages
        }
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

@router.get("/mangas/{manga_id}", response_model=MangaResponse)
def get_manga_by_id(manga_id: int, db: Session = Depends(get_db)):
    manga = db.query(Manga).filter(Manga.id == manga_id).first()
    if not manga:
        raise HTTPException(status_code=404, detail="Manga not found")
    return MangaResponse.from_orm(manga)
