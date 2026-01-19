from sqlalchemy import create_engine, text
from app.core.config import settings

def migrate():
    print(f"Connecting to DB...")
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        print("Running Job FilePath Migration...")
        try:
            conn.execute(text("ALTER TABLE jobs ADD COLUMN IF NOT EXISTS original_file_path TEXT;"))
            print("Added 'original_file_path' column.")
        except Exception as e:
            print(f"Error: {e}")
        
        conn.commit()
        print("Migration Complete.")

if __name__ == "__main__":
    migrate()
