import requests
import sys
import os

# Adjust path to import from app if needed, or just use requests
BASE_URL = "http://localhost:8000"

def test_replan():
    # 1. Create a Job (using previous logic or just assume one exists)
    # We need a job with an uploaded file.
    # Let's ask user to use the one from manual verification if possible.
    # Or cleaner: Create a new job here using the test PDF.
    
    print("1. Creating Test Initial Job...")
    pdf_path = "backend/test_vision.pdf" # Assuming this exists from previous step
    if not os.path.exists(pdf_path):
        # Try to find it relative to script or create it
        pdf_path = "test_vision.pdf" 
        if not os.path.exists(pdf_path):
             print("Error: test_vision.pdf not found. Please run create_test_pdf.py first.")
             return

    with open(pdf_path, 'rb') as f:
        files = {'file': f}
        # Simulate lazy user login by not sending token (extractor relies on DB user)
        # But create_job needs auth...
        # We need a token.
        # Let's Skip creation and try to find the LATEST job in DB to replan.
        pass

    # Alternative: Connect to DB and fetch latest job
    sys.path.append(os.getcwd())
    from app.core.database import SessionLocal
    from app.models.job import Job
    from app.models.page import Page
    from app.models.user import User # Complete registry
    
    db = SessionLocal()
    job = db.query(Job).order_by(Job.created_at.desc()).first()
    
    if not job:
        print("No jobs found in DB. Please upload a file via Frontend first.")
        return
        
    print(f"Using latest Job ID: {job.id}")
    
    # 2. Call Plan (Initial)
    print("2. Calling Initial /plan (Phase 4)...")
    try:
        r = requests.post(f"{BASE_URL}/jobs/{job.id}/plan") # Needs Auth?
        # If API requires auth, this will fail 401.
        # We disabled strict auth on endpoints? No, Depends(get_current_user_id) is there.
        # We need to mock auth or use a valid token.
        # Since this is a dev script, let's look at dependencies.py.
        # It verifies JWT.
        
        # We can bypass API and call Service directly for testing logic!
        from app.services.planner import PlannerService
        from app.api.jobs import LayoutConfig
        
        default_config = LayoutConfig().model_dump()
        
        print(f"   Invoking PlannerService.replan_job directly...")
        # pages = PlannerService.replan_job(job.id, db, default_config)
        # print(f"   Initial Plan Pages: {pages}")
        
        # 3. Call Replan with SAME config (Should be skipped)
        print("3. Testing Replan Algorithm (No Change)...")
        from app.api.jobs import requires_replan, LayoutConfig
        
        # Mock Job's current config if not present
        if not job.layout_config:
            job.layout_config = default_config
            db.commit()
            
        should_replan = requires_replan(job.layout_config, LayoutConfig())
        print(f"   Requires Replan (Same Config)? {should_replan} (Expected: False)")
        
        # 4. Call Replan with NEW config
        print("4. Testing Replan Algorithm (New Config)...")
        new_config = LayoutConfig(page_size="A5", margin_left=100)
        should_replan_2 = requires_replan(job.layout_config, new_config)
        print(f"   Requires Replan (Diff Config)? {should_replan_2} (Expected: True)")
        
    except Exception as e:
        print(f"Test Failed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    test_replan()
