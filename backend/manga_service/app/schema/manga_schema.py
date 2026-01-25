from pydantic import BaseModel, validator
from typing import Optional, List
import json

class MangaResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    rating: Optional[float] = None
    year: Optional[int] = None
    tags: Optional[List[str]] = None
    cover: Optional[str] = None

    @validator('tags', pre=True)
    def parse_tags(cls, v):
        """Converte tags de string para lista"""
        if v is None:
            return []
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            try:
                tags_str = v.replace("'", '"')
                return json.loads(tags_str)
            except:
                return []
        return []

    class Config:
        orm_mode = True