from pydantic import BaseModel
from typing import List, Optional

class RecommendationRequest(BaseModel):
    job_school_location: str
    salary: float
    house_type: str
    family_size: int
    preferred_amenities: Optional[List[str]] = None
    language: str = "en"  # 'en', 'am', 'or'

    class Config:
        schema_extra = {
            "example": {
                "job_school_location": "Bole",
                "salary": 5000.0,
                "house_type": "apartment",
                "family_size": 2,
                "preferred_amenities": ["wifi", "parking"],
                "language": "am"
            }
        }

class RecommendationResponse(BaseModel):
    property_id: int
    title: str
    location: str
    price: float
    transport_cost: float
    affordability_score: float
    reason: str
    map_url: str
