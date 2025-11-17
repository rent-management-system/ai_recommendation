import uuid # For UUID type, even if not default
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, ARRAY, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID # For user_id if it's UUID
from sqlalchemy.orm import relationship
from .tenant_profile import Base # Assuming Base is still imported from here

class SavedSearch(Base):
    __tablename__ = "SavedSearches"

    id = Column(Integer, primary_key=True) # serial not null
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id")) # Assuming UUID and FK to users.id
    location = Column(String(255))
    min_price = Column(Float) # double precision
    max_price = Column(Float) # double precision
    house_type = Column(String(50))
    amenities = Column(ARRAY(String)) # character varying[]
    bedrooms = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow) # timestamp without time zone
    max_distance_km = Column(Float) # double precision

    # Relationships
    user = relationship("User", backref="saved_searches")
