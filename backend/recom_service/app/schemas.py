from pydantic import BaseModel
from typing import List, Optional

class RecommendationRequest(BaseModel):
    user_id: int
    limit: int = 10

class RecommendationResponse(BaseModel):
    user_id: int
    recommendations: List[dict]
    total_recommendations: int

class ClusterInfo(BaseModel):
    cluster_id: int
    size: int
    avg_rating: float
    common_tags: List[str]
    representative_mangas: List[str]

class UserPreferences(BaseModel):
    user_id: int
    preferred_genres: List[str]
    favorite_titles: Optional[List[str]] = []
    favorite_authors: Optional[List[str]] = []
    preferred_rating_min: Optional[float] = 0.0
    preferred_rating_max: Optional[float] = 5.0

class PreferencesResponse(BaseModel):
    message: str
    user_id: int
    preferences_saved: bool
    model_training_started: bool
