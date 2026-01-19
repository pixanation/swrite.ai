import requests
import os

BASE_URL = "http://localhost:8000"
# Get a token manually or just hack the dependency for testing?
# Since auth is required, we need a valid token. 
# We can't generate one easily without logging in via frontend.
# HACK: For this test script, we can disable auth on the endpoint temporarily or ask the user to paste a token?
# Better: Make the script print "Please provide a Bearer Token" or try to login if possible.
# Actually, since we have the `SUPABASE_JWT_SECRET`, we can MOCK a token!

from jose import jwt
import datetime
# Mock Token Generation
# Use Env Var or Default helper
from app.core.config import settings

SECRET = settings.SUPABASE_JWT_SECRET
if not SECRET:
    raise ValueError("SUPABASE_JWT_SECRET not set in env")

ALGORITHM = "HS256"

def create_test_token():
    payload = {
        "sub": "test_user_id_123",
        "aud": "authenticated",
        "role": "authenticated",
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    }
    return jwt.encode(payload, SECRET, algorithm=ALGORITHM)

TOKEN = create_test_token()

HEADERS = {"Authorization": f"Bearer {TOKEN}"}

def test_pasted_text():
    print("Testing Pasted Text...")
    res = requests.post(
        f"{BASE_URL}/jobs/create",
        headers=HEADERS,
        data={"content": "Hello world", "page_count_estimate": 1}
    )
    print(res.json())

def test_fake_pdf():
    print("\nTesting PDF (Simulated Upload)...")
    # multiple files not supported in requests simplistic way easily mixed with data
    # We need to construct multipart
    
    # Mock PDF content
    files = {'file': ('test.pdf', b'%PDF-1.4 ... fake content', 'application/pdf')}
    res = requests.post(f"{BASE_URL}/jobs/create", headers=HEADERS, files=files, data={"page_count_estimate": 1})
    print(res.json())

if __name__ == "__main__":
    try:
        test_pasted_text()
        test_fake_pdf()
        print("\nNote: Real PDF/Image testing requires actual files. This verifies routing basics.")
    except Exception as e:
        print(f"Error: {e}")
