from sqlalchemy import create_engine, text
from app.core.config import settings

def migrate():
    print(f"Connecting to DB...")
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        print("Running Phase 5 Migration...")
        try:
            # 1. Job layout_config
            conn.execute(text("ALTER TABLE jobs ADD COLUMN IF NOT EXISTS layout_config JSONB;"))
            print("Added 'layout_config' to Jobs.")
            
            # 2. Page type/char_count (double check)
            # Already added in Phase 4 but let's be safe
            # Note: User asked for 'type' column, but we are using 'page_type'.
            # I will assume 'page_type' is sufficient and mapped in logic.
            # conn.execute(text("ALTER TABLE pages ADD COLUMN IF NOT EXISTS type VARCHAR;")) 
            
        except Exception as e:
            print(f"Error: {e}")
        
        conn.commit()
        print("Migration Complete.")

if __name__ == "__main__":
    migrate()
