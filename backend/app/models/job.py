from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, JSON, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

class Job(Base):
    __tablename__ = "jobs"

    id = Column(String, primary_key=True, index=True) # UUID
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    status = Column(String, default="created") # created, processing, completed, failed
    input_type = Column(String, nullable=False) # text_pdf, scanned_pdf, image_handwritten
    pipeline = Column(String, nullable=True) # pdf_flow, direct_rewrite
    requires_review = Column(Boolean, default=False)
    
    total_pages = Column(Integer, default=0)
    original_file_path = Column(String, nullable=True) # Path to stored file for Vision
    layout_config = Column(JSON, nullable=True) # Phase 5: Margins, Spacing
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User")
    pages = relationship("Page", back_populates="job", cascade="all, delete-orphan")
