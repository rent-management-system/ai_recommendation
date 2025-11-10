from pydantic import BaseModel
from typing import List, Dict

class PropertySearchRequest(BaseModel):
    query: str

class PropertySearchResponse(BaseModel):
    results: List[Dict]
