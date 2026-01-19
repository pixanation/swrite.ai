from sqlalchemy import create_engine, text
from app.core.config import settings

def migrate():
    print(f"Connecting to DB...")
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        print("Running Page.user_id Migration...")
        try:
            # Add column (nullable first to avoid errors on existing rows, though we can make it false if we update data)
            # For simplicity in dev, we'll make it nullable=True initially or just not enforce constraint instantly on old data
            # But here I'll try to add it.
            conn.execute(text("ALTER TABLE pages ADD COLUMN IF NOT EXISTS user_id TEXT;"))
            print("Added 'user_id' column.")
            
            # Optionally we could backfill if needed, but for now just schema.
        except Exception as e:
            print(f"Error: {e}")
        
        conn.commit()
        print("Migration Complete.")

if __name__ == "__main__":
    migrate()
