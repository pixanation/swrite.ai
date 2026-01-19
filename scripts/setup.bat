@echo off
echo Setting up Backend...
cd backend
if not exist venv (
    python -m venv venv
)
call venv\Scripts\activate
pip install -r requirements.txt
cd ..

echo Setting up Frontend...
cd frontend
if not exist node_modules (
    npm install
)
cd ..

echo Setup complete. Run scripts\run_dev.bat to start.
pause
