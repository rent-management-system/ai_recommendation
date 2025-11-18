import uuid
from datetime import datetime
import enum
from sqlalchemy import Column, String, Boolean, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID, BYTEA
from .tenant_profile import Base # Assuming Base is still imported from here

# Define Enums
class UserRole(enum.Enum):
    admin = "admin"
    owner = "owner"
    tenant = "tenant"
    broker = "broker"

class Language(enum.Enum):
    en = "en"
    am = "am"
    om = "om"

class Currency(enum.Enum):
    ETB = "ETB"
    USD = "USD"

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False)
    password = Column(String)
    full_name = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.tenant, nullable=False)
    phone_number = Column(BYTEA)
    preferred_language = Column(Enum(Language), default=Language.en)
    preferred_currency = Column(Enum(Currency), default=Currency.ETB)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    password_changed = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)