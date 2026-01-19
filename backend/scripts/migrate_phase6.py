from sqlalchemy import create_engine, text
from app.core.config import settings

def migrate():
    print("Connecting to DB...")
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        print("Running Phase 6 Migration...")
        try:
            conn.execute(text("ALTER TABLE pages ADD COLUMN IF NOT EXISTS image_url TEXT;"))
            print("Added 'image_url' to Pages.")
            
            conn.execute(text("ALTER TABLE pages ADD COLUMN IF NOT EXISTS render_seed BIGINT;"))
            print("Added 'render_seed' to Pages.")
            
            conn.execute(text("ALTER TABLE pages ADD COLUMN IF NOT EXISTS render_attempts INTEGER DEFAULT 0;"))
            print("Added 'render_attempts' to Pages.")
            
        except Exception as e:
            print(f"Error: {e}")
        
        conn.commit()
        print("Migration Complete.")

if __name__ == "__main__":
    migrate()
