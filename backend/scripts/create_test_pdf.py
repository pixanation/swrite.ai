import requests
import time
from reportlab.pdfgen import canvas

# 1. Create a Dummy PDF
pdf_path = "test_vision.pdf"
c = canvas.Canvas(pdf_path)
c.drawString(100, 750, "Hello World from swrite.ai Vision Test.")
c.drawString(100, 730, "This is a simple document to test the layout engine.")
c.drawString(100, 710, "Paragraph 1: The quick brown fox jumps over the lazy dog.")
c.drawString(100, 690, "Paragraph 2: Lorem ipsum dolor sit amet, consectetur adipiscing elit.")
c.save()
print(f"Created {pdf_path}")

# 2. Upload Job
url = "http://localhost:8000/jobs/create"
files = {'file': open(pdf_path, 'rb')}
# We need an Authorization header if we are enforcing User ID.
# Since we are using "Lazy User" in create_job (db.add(user) if missing), 
# we need to simulate a user. 
# But wait, create_job depends on get_current_user_id.
# If we don't send a token, it might fail if we don't have a mock.
# Let's assume we can mock it or use the mock token logic if enabled.
# Actually, let's login first or just try without token if dev mode is loose (it's not).

# Use a mock token if possible, or just hack the dependency for verification?
# The dependency logic checks for 'Authorization: Bearer <token>'.
# If validation is on, we need a valid token.
# Let's try to simulate a token or just bypass for this script?
# Actually, let's look at dependencies.py. If verifying key is hard, we might fail.
# BUT, we have "Lazy User" logic. Let's try sending a dummy token if verify_token allows it.
# Or better, just hardcode a user_id via dependency injection? No, that requires code change.

# Let's use a fake token and hope `jose` doesn't crash if we signed it ourselves?
# Or just use the frontend to upload? 
# Using the frontend is safer but harder to automate here.

# Alternative: Python script that imports app and calls function directly?
# That bypasses HTTP auth.
import sys
import os
sys.path.append(os.getcwd())
from app.core.database import SessionLocal
from app.api.jobs import create_job, plan_job
from app.models.user import User
from fastapi import UploadFile

# We can't easily call async create_job directly without an event loop.
# Let's stick to HTTP but I'll skip the Auth for now by assuming I can generate a token?
# Or I'll just ask the user to test via Frontend.

print("\n--- MANUAL TEST REQUIRED ---")
print("1. Please upload 'test_vision.pdf' using the Frontend.")
print("2. Check if file appears in 'backend/uploads/'.")
print("3. I will then trigger the Plan step manually via ID.")
