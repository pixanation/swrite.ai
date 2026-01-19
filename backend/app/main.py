from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import engine, Base
from app.api import jobs

# Create tables (For Phase 1 w/ SQLite or if we need to auto-create in Postgres)
# In production with Supabase, usage of Alembic is better, but this works for prototype.
Base.metadata.create_all(bind=engine)

app = FastAPI(title="swrite.ai Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "swrite.ai backend"}

app.include_router(jobs.router, prefix="/jobs", tags=["Jobs"])
