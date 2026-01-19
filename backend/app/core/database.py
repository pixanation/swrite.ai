from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Use DB URL from settings, fallback to SQLite if not provided or testing
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

# Basic check to avoid crashing if URL is placeholder
if "postgresql" not in SQLALCHEMY_DATABASE_URL and "sqlite" not in SQLALCHEMY_DATABASE_URL:
    # Fallback to local sqlite for now to prevent startup crash until configured
    SQLALCHEMY_DATABASE_URL = "sqlite:///./swrite.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False} if "sqlite" in SQLALCHEMY_DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
