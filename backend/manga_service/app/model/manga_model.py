from sqlalchemy import Column, Integer, String, Float, Text, JSON
from app.config.database import AlchemyBaseModel

class Manga(AlchemyBaseModel):
    __tablename__ = "mangas"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    rating = Column(Float, nullable=True)
    year = Column(Integer, nullable=True)
    tags = Column(JSON, nullable=True)
    cover = Column(String(512), nullable=True)