@echo off
echo Starting Backend...
cd backend
call venv\Scripts\activate
start "swrite.ai Backend" uvicorn main:app --reload --port 8000
cd ..

echo Starting Frontend...
cd frontend
start "swrite.ai Frontend" npm run dev
cd ..

echo swrite.ai is running!
echo Backend: http://localhost:8000/health
echo Frontend: http://localhost:5173
pause
