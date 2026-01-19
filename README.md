# swrite.ai

swrite.ai converts clean text into print-ready handwritten documents using AI, with page-level transparency and user-controlled regeneration.

## Project Structure

- `backend/`: Python FastAPI backend
- `frontend/`: Web application (Vite + React)
- `docs/`: Documentation
- `scripts/`: Helper scripts

## specific Rules from System Contract

- Handwriting is never edited, only re-rendered
- Page = atomic unit
- If source text changes → page regenerates
- Errors are shown to the user, not auto-hidden
