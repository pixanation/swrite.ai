import os
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.api.dependencies import get_current_user_id
from app.models.job import Job
from app.models.page import Page
from app.models.user import User
from app.services.segregator import segregate_input
from app.services.planner import PlannerService
from app.services.renderer import HandwritingRenderer

router = APIRouter()

class PageStatusResponse(BaseModel):
    page_number: int
    status: str

class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    input_type: str
    pipeline: Optional[str] = None
    requires_review: bool
    total_pages: int
    created_at: str
    pages: List[PageStatusResponse]

@router.post("/create")
async def create_job(
    content: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    page_count_estimate: int = Form(1),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    # 1. Segregate
    try:
        segregation = await segregate_input(content=content, file=file)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 2. Sync User
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        user = User(id=user_id, email=f"{user_id}@placeholder.com")
        db.add(user)
        db.commit()

    # 3. Create Job (and save file)
    job_id = str(uuid.uuid4())
    original_path = None
    file_bytes = None
    
    if file:
        file_bytes = await file.read()
        await file.seek(0)
        
        # Save to backend/uploads
        upload_dir = os.path.join(os.getcwd(), "uploads")
        os.makedirs(upload_dir, exist_ok=True)
        
        clean_name = os.path.basename(file.filename)
        save_path = os.path.join(upload_dir, f"{job_id}_{clean_name}")
        
        with open(save_path, "wb") as f:
            f.write(file_bytes)
        
        original_path = save_path
        
    job = Job(
        id=job_id,
        user_id=user_id,
        status="processing",
        total_pages=0,
        original_file_path=original_path,
        input_type=segregation.input_type,
        pipeline=segregation.pipeline,
        requires_review=segregation.requires_review
    )
    db.add(job)
    db.flush()

    # 4. Extract (OCR)
    if file:
        await file.seek(0) # Reset before extraction
        
    from app.services.extractor import Extractor
    try:
        pages_count = Extractor.extract_job(job, db, file_bytes)
        job.total_pages = pages_count
    except Exception as e:
        print(f"Extraction Failed: {e}")
        job.status = "failed"
    
    db.commit()
    
    return {
        "job_id": job.id, 
        "status": job.status,
        "segregation": {
            "input_type": segregation.input_type,
            "pipeline": segregation.pipeline,
            "requires_review": segregation.requires_review
        },
        "pages_created": job.total_pages
    }

@router.get("/{job_id}/status", response_model=JobStatusResponse)
def get_job_status(
    job_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    job = db.query(Job).filter(Job.id == job_id, Job.user_id == user_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return JobStatusResponse(
        job_id=job.id,
        status=job.status,
        total_pages=job.total_pages,
        created_at=str(job.created_at),
        pages=[PageStatusResponse(page_number=p.page_number, status=p.status) for p in job.pages]
    )

class LayoutConfig(BaseModel):
    page_size: str = "A4" # A4, A5, Letter
    margin_left: int = 48
    margin_top: int = 64
    margin_bottom: int = 64
    header_space: int = 40
    footer_space: int = 30
    line_spacing: str = "normal"

def requires_replan(old_config: dict, new_config: LayoutConfig) -> bool:
    if not old_config:
        return True
    
    # Critical fields that change handwriting capacity
    critical_fields = ["page_size", "margin_left", "margin_top", "margin_bottom", "header_space", "footer_space", "line_spacing"]
    
    for field in critical_fields:
        if old_config.get(field) != getattr(new_config, field):
            return True
            
    return False

@router.post("/{job_id}/plan")
def plan_job(
    job_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """
    Phase 4: Initial Planning (Default Layout).
    """
    default_config = LayoutConfig() # Use defaults
    return replan_job_endpoint(job_id, default_config, db, user_id)

@router.post("/{job_id}/replan")
def replan_job_endpoint(
    job_id: str,
    config: LayoutConfig,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """
    Phase 5: Updates layout and re-triggers Planner if needed.
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    if job.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    # Check if we need to re-run ChatGPT
    if requires_replan(job.layout_config, config):
        try:
            pages_count = PlannerService.replan_job(job_id, db, config.model_dump())
            return {"status": "replanned", "total_pages": pages_count}
        except Exception as e:
            print(f"Replan Error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    else:
        # Just update config, no API call
        job.layout_config = config.model_dump()
        db.commit()
        return {"status": "updated_config_only"}

@router.post("/{job_id}/render")
def render_job_endpoint(
    job_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """
    Phase 6: Render handwritten pages.
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    if job.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    try:
        rendered_count = HandwritingRenderer.render_job(job_id, db)
        return {"status": "rendered", "pages_rendered": rendered_count}
    except Exception as e:
        print(f"Render Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{job_id}/pages/{page_number}/approve")
def approve_page(
    job_id: str,
    page_number: int,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """
    User approves a rendered page.
    """
    page = db.query(Page).filter(
        Page.job_id == job_id,
        Page.page_number == page_number
    ).first()
    
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    
    if page.status != "rendered":
        raise HTTPException(status_code=400, detail="Page not in rendered state")
        
    page.status = "approved"
    db.commit()
    return {"status": "approved", "page_number": page_number}

@router.post("/{job_id}/pages/{page_number}/retry")
def user_retry_page(
    job_id: str,
    page_number: int,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """
    User requests regeneration. Different seed for variation.
    """
    page = db.query(Page).filter(
        Page.job_id == job_id,
        Page.page_number == page_number
    ).first()
    
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    
    if page.status not in ["rendered", "failed_system"]:
        raise HTTPException(status_code=400, detail="Page cannot be retried")
        
    try:
        HandwritingRenderer.user_retry_page(page, db)
        return {"status": "retried", "page_number": page_number}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
