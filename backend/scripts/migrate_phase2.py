from sqlalchemy import create_engine, text
from app.core.config import settings

def migrate():
    print(f"Connecting to DB: {settings.DATABASE_URL.split('@')[1]}") # Print host only for safety
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        print("Running Phase 2 Migration...")
        # Add new columns if they don't exist
        # We use raw SQL for safety and simplicity on the live DB without full alembic setup
        statements = [
            "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS input_type_new VARCHAR;",
            "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS pipeline VARCHAR;",
            "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS requires_review BOOLEAN DEFAULT FALSE;",
            # Fix: We already had input_type but strict migration might need to handle it.
            # Ideally we keep input_type but maybe broaden it. 
            # The previous input_type was String, so it should be fine.
        ]
        
        for stmt in statements:
            try:
                conn.execute(text(stmt))
                print(f"Executed: {stmt}")
            except Exception as e:
                print(f"Skipped/Error: {stmt} -> {e}")
        
        conn.commit()
        print("Migration Complete.")

if __name__ == "__main__":
    migrate()
