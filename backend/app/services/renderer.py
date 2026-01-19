import os
import hashlib
import httpx
import replicate
from sqlalchemy.orm import Session
from app.models.job import Job
from app.models.page import Page
from app.core.config import settings

# Supabase Storage Config
SUPABASE_URL = settings.SUPABASE_URL
SUPABASE_KEY = settings.SUPABASE_KEY
STORAGE_BUCKET = "rendered-pages"  # Create this bucket in Supabase

class HandwritingRenderer:
    """
    Phase 6: Dumb, deterministic factory.
    Systems retry failures. Humans retry preferences.
    """
    
    @staticmethod
    def render_job(job_id: str, db: Session) -> int:
        """
        Render all unrendered handwritten pages for a job.
        Sequential. No parallelism.
        """
        print(f"Renderer: Starting job {job_id}")
        
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise Exception("Job not found.")
            
        pages = db.query(Page).filter(
            Page.job_id == job_id,
            Page.page_type == "handwritten"
        ).order_by(Page.page_number).all()
        
        rendered_count = 0
        
        for page in pages:
            if page.status in ["rendered", "approved"]:
                print(f"  Page {page.page_number}: Already done. Skipping.")
                continue
                
            try:
                HandwritingRenderer.render_page(page, db)
                rendered_count += 1
            except Exception as e:
                print(f"  Page {page.page_number}: FAILED - {e}")
                # Status already set to failed_system in render_page
        
        # Update Job
        all_pages = db.query(Page).filter(
            Page.job_id == job_id,
            Page.page_type == "handwritten"
        ).all()
        
        all_done = all(p.status in ["rendered", "approved"] for p in all_pages)
        job.status = "rendered" if all_done else "partial"
        db.commit()
        
        print(f"Renderer: Finished. Rendered {rendered_count} pages.")
        return rendered_count
    
    @staticmethod
    def render_page(page: Page, db: Session, is_user_retry: bool = False):
        """
        Render a single page. System auto-retries for failures only.
        """
        print(f"  Rendering Page {page.page_number}...")
        page.status = "rendering"
        db.commit()
        
        # Step 1: Lock Seed
        seed = HandwritingRenderer._generate_seed(page, is_user_retry)
        page.render_seed = seed
        page.render_attempts += 1
        
        # Step 2: Build Prompt
        prompt = HandwritingRenderer._build_prompt(page.content)
        
        # Step 3: Build Payload
        payload = {
            "prompt": prompt,
            "width": 1024,
            "height": 1408,
            "seed": seed,
            "num_inference_steps": 28,
            "guidance_scale": 7.5,
            "negative_prompt": (
                "printed font, typeset text, decorations, "
                "calligraphy, artistic style, blur, skewed lines"
            )
        }
        
        # Step 4: Call Replicate (with system retry for hard failures)
        max_system_retries = 2
        last_error = None
        
        for attempt in range(max_system_retries):
            try:
                print(f"    System Attempt {attempt + 1}...")
                
                output = replicate.run(
                    "stability-ai/stable-diffusion-3.5-medium",
                    input=payload
                )
                
                # Validate: Image exists
                if not output or (isinstance(output, list) and len(output) == 0):
                    raise SystemError("Empty output from Replicate.")
                
                image_url = output[0] if isinstance(output, list) else output
                
                if not image_url or not isinstance(image_url, str):
                    raise SystemError("Invalid image URL from Replicate.")
                
                # Step 5: Upload to Supabase Storage
                stored_url = HandwritingRenderer._upload_to_supabase(
                    image_url, 
                    page.job_id, 
                    page.page_number
                )
                
                # Step 6: Persist
                page.image_url = stored_url
                page.status = "rendered"  # Awaits user approval
                db.commit()
                print(f"    Success: {stored_url[:60]}...")
                return
                
            except SystemError as e:
                # System failure - auto retry allowed
                print(f"    System Failure: {e}")
                last_error = e
                # Continue to next attempt
                
            except Exception as e:
                # Unexpected error - still a system failure
                print(f"    Unexpected Error: {e}")
                last_error = e
        
        # All system attempts failed
        page.status = "failed_system"
        db.commit()
        raise Exception(f"Page {page.page_number} failed (system): {last_error}")
    
    @staticmethod
    def user_retry_page(page: Page, db: Session):
        """
        User-initiated retry. Different seed for variation.
        """
        print(f"  User Retry: Page {page.page_number}...")
        HandwritingRenderer.render_page(page, db, is_user_retry=True)
    
    @staticmethod
    def _generate_seed(page: Page, include_attempt: bool = False) -> int:
        """
        Deterministic seed.
        System retry: Same seed (reproducible).
        User retry: Include attempt count (variation).
        """
        if include_attempt:
            seed_input = f"{page.id}:{page.page_number}:{page.render_attempts}"
        else:
            seed_input = f"{page.id}:{page.page_number}"
            
        hash_val = hashlib.sha256(seed_input.encode()).hexdigest()
        return int(hash_val, 16) % (2**32)
    
    @staticmethod
    def _build_prompt(page_text: str) -> str:
        """
        Boring, deterministic prompt. No creativity bait.
        """
        return f"""Render the following text as neat, legible human handwriting.

Rules:
- Write the provided text faithfully.
- Preserve line breaks.
- Do not add or remove content.
- Follow the handwriting reference for stroke and spacing.
- Keep margins fixed.

Text:
\"\"\"
{page_text}
\"\"\""""

    @staticmethod
    def _upload_to_supabase(image_url: str, job_id: str, page_number: int) -> str:
        """
        Download image from Replicate and upload to Supabase Storage.
        Returns the public URL.
        """
        # Download image from Replicate
        response = httpx.get(image_url)
        if response.status_code != 200:
            raise SystemError(f"Failed to download image: {response.status_code}")
        
        image_bytes = response.content
        
        if len(image_bytes) == 0:
            raise SystemError("Downloaded image is empty (0 bytes).")
        
        # Upload to Supabase
        file_path = f"{job_id}/page_{page_number}.png"
        upload_url = f"{SUPABASE_URL}/storage/v1/object/{STORAGE_BUCKET}/{file_path}"
        
        headers = {
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "image/png",
            "x-upsert": "true"  # Overwrite if exists
        }
        
        upload_response = httpx.post(upload_url, content=image_bytes, headers=headers)
        
        if upload_response.status_code not in [200, 201]:
            raise SystemError(f"Supabase upload failed: {upload_response.text}")
        
        # Return public URL
        public_url = f"{SUPABASE_URL}/storage/v1/object/public/{STORAGE_BUCKET}/{file_path}"
        return public_url
