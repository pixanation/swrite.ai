from sqlalchemy import create_engine, text
from app.core.config import settings

def migrate():
    print(f"Connecting to DB...")
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        print("Running Phase 4 Migration (page_type, char_count)...")
        try:
            conn.execute(text("ALTER TABLE pages ADD COLUMN IF NOT EXISTS page_type TEXT DEFAULT 'input';"))
            conn.execute(text("ALTER TABLE pages ADD COLUMN IF NOT EXISTS char_count INTEGER DEFAULT 0;"))
            print("Added 'page_type' and 'char_count' columns.")
        except Exception as e:
            print(f"Error: {e}")
        
        conn.commit()
        print("Migration Complete.")

if __name__ == "__main__":
    migrate()
