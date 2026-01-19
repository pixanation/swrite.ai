import os
from pydantic_settings import BaseSettings

# Auto-set Google Credentials and Poppler Path for Phase 3
# This must run BEFORE the Settings class is instantiated or fields are validated
if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "service_account.json"

base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
poppler_dir = os.path.join(base_dir, "poppler_bin", "poppler-24.08.0", "Library", "bin")

POPPLER_PATH = None
if os.path.exists(poppler_dir):
    # Prepend to PATH so it's found first
    os.environ["PATH"] = poppler_dir + os.pathsep + os.environ["PATH"]
    POPPLER_PATH = poppler_dir

class Settings(BaseSettings):
    PROJECT_NAME: str = "swrite.ai"
    
    # Supabase - Set via environment variables
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    DATABASE_URL: str = ""
    SUPABASE_JWT_SECRET: str = ""

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
