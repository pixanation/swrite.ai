from sqlalchemy import Column, String, DateTime
from sqlalchemy.sql import func
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    # Maps to Supabase auth.users.id
    id = Column(String, primary_key=True, index=True) 
    email = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
