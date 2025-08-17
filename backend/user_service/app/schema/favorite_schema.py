from pydantic import BaseModel
from datetime import datetime

class FavoriteRequest(BaseModel):
    manga_id: int

class FavoriteResponse(FavoriteRequest):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        orm_mode = True
