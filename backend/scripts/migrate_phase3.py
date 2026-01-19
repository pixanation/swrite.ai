from sqlalchemy import create_engine, text
from app.core.config import settings

def migrate():
    print(f"Connecting to DB...")
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        print("Running Phase 3 Migration (Pages)...")
        try:
            conn.execute(text("ALTER TABLE pages ADD COLUMN IF NOT EXISTS content TEXT;"))
            print("Added 'content' column.")
            conn.execute(text("ALTER TABLE pages ADD COLUMN IF NOT EXISTS structure_map JSONB;")) # Use JSONB for Postgres if possible, else JSON
            print("Added 'structure_map' column.")
        except Exception as e:
            print(f"Error: {e}")
        
        conn.commit()
        print("Migration Complete.")

if __name__ == "__main__":
    migrate()
