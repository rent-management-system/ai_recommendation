from sqlalchemy import Column, Integer, String, Float, ARRAY, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime

class Base(AsyncAttrs, DeclarativeBase):
    pass

class TenantProfile(Base):
    __tablename__ = "TenantProfiles"
    id = Column(Integer, primary_key=True)
    user_id = Column(UUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    job_school_location = Column(String(255))
    salary = Column(Float)
    house_type = Column(String(50))
    family_size = Column(Integer)
    preferred_amenities = Column(ARRAY(String))
    created_at = Column(DateTime, default=datetime.utcnow)

class RecommendationLog(Base):
    __tablename__ = "RecommendationLogs"
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("TenantProfiles.id", ondelete="CASCADE"), nullable=False)
    recommendation = Column(JSONB)
    feedback = Column(JSONB)
    created_at = Column(DateTime, default=datetime.utcnow)
