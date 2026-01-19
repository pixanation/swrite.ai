from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Text, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

class Page(Base):
    __tablename__ = "pages"

    id = Column(String, primary_key=True, index=True) # UUID
    job_id = Column(String, ForeignKey("jobs.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False) # Denormalized for easy access/RLS
    
    page_number = Column(Integer, nullable=False)
    status = Column(String, default="pending") # pending, processing, completed, failed
    content = Column(Text, nullable=True) # Raw extracted text
    page_type = Column(String, default="input") # input (OCR), output (Planned)
    char_count = Column(Integer, default=0)
    source = Column(String, nullable=True) # google_ocr, pypdf, planner_slice
    structure_map = Column(JSON, nullable=True) # Deprecated/Unused for now
    
    # Phase 6: Rendering
    image_url = Column(String, nullable=True) # Rendered handwriting image
    render_seed = Column(Integer, nullable=True) # Deterministic seed
    render_attempts = Column(Integer, default=0) # Retry count
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    job = relationship("Job", back_populates="pages")
