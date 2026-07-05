from sqlalchemy import Column, Integer, String, Float, Text
from app.config.database import AlchemyBaseModel
import json

class Manga(AlchemyBaseModel):
    __tablename__ = "mangas"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    rating = Column(Float, nullable=True)
    year = Column(Integer, nullable=True)
    tags = Column(Text, nullable=True)
    cover = Column(String(512), nullable=True)
    
    def get_tags(self):
        if not self.tags:
            return []
        try:
            if isinstance(self.tags, str):
                tags_str = self.tags.replace("'", '"')
                return json.loads(tags_str)
            return self.tags
        except:
            return []