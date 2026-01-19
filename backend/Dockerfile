# Use Python 3.10 Slim image (Lightweight Linux)
FROM python:3.10-slim

# 1. Install System Dependencies (Linux)
# - poppler-utils: Required for pdf2image processing
# - libgl1-mesa-glx: Required for opencv-python-headless (sometimes needed depending on base image)
RUN apt-get update && apt-get install -y \
    poppler-utils \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

# 2. Setup Work Directory
WORKDIR /app

# 3. Install Python Dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copy Application Code
COPY . .

# 5. Expose Port (Standard for Render/Railway)
EXPOSE 8000

# 6. Run the Application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
