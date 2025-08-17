from sqlalchemy import Column, Integer, ForeignKey, DateTime, func
from app.config.database import AlchemyBaseModel

class Favorite(AlchemyBaseModel):
    __tablename__ = "favorites"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    manga_id = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
