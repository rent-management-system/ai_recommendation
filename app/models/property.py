import uuid
from datetime import datetime
from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey, Text, JSON, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB, TSVECTOR # TSVECTOR for fts
from sqlalchemy.orm import relationship
from .tenant_profile import Base # Assuming Base is still imported from here

class Property(Base):
    __tablename__ = "properties"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4) # Assuming uuid_generate_v4 is handled by default=uuid.uuid4
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    location = Column(String(255), nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    amenities = Column(JSONB, default=[]) # Use JSONB for json null default '[]'::jsonb
    photos = Column(JSONB, default=[]) # Use JSONB for json null default '[]'::jsonb
    status = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    # fts = Column(TSVECTOR) # Omit for now, requires specific handling
    lat = Column(Float)
    lon = Column(Float)
    house_type = Column(String(50), nullable=False)
    payment_id = Column(UUID(as_uuid=True), ForeignKey("payments.id"), unique=True) # Foreign key to payments.id
    payment_status = Column(String, nullable=False)
    approval_timestamp = Column(DateTime)

    # Relationships
    user = relationship("User", backref="properties")
    payment = relationship("Payment", backref="property", uselist=False) # One-to-one or one-to-many? Assuming one-to-one for payment_id unique constraint
