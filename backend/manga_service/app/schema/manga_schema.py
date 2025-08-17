from pydantic import BaseModel
from typing import Optional, List

class MangaResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    rating: Optional[float] = None
    year: Optional[int] = None
    tags: Optional[List[str]] = None
    cover: Optional[str] = None

    class Config:
        orm_mode = True