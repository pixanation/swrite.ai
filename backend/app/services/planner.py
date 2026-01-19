import os
import json
import base64
import io
import uuid
from typing import List
from app.core.config import settings, POPPLER_PATH
from sqlalchemy.orm import Session
from app.models.job import Job
from app.models.page import Page
from openai import OpenAI
from pdf2image import convert_from_path
from PIL import Image

# Default Handwriting Reference (Generic Cursive)
# Ideally this comes from User Profile or Upload
DEFAULT_REF_IMAGE = "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6e/Handwriting_sample.svg/1200px-Handwriting_sample.svg.png"

class PlannerService:
    @staticmethod
    def plan_job(job_id: str, db: Session):
        """
        Phase 4 (Vision-First):
        1. Load original document images.
        2. Send to GPT-4o as a "Document Layout Engine".
        3. Receive page-wise content list.
        4. Save as 'output' pages.
        """
        print(f"Planner: Starting Vision Plan for Job {job_id}")
        
        # 1. Get Job & File
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job or not job.original_file_path:
            raise Exception("Job has no original file path. Cannot perform Vision Planning.")
            
        file_path = job.original_file_path
        if not os.path.exists(file_path):
            raise Exception(f"File not found on disk: {file_path}")
            
        # 2. Convert Source to Images (Base64)
        print(f"Planner: Loading file {file_path}...")
        source_images_b64 = PlannerService._file_to_base64_images(file_path)
        print(f"Planner: Converted to {len(source_images_b64)} images.")
        
        # 3. Call OpenAI (Vision Compiler)
        plan_json = PlannerService._call_gpt4o_vision(source_images_b64, DEFAULT_REF_IMAGE)
        print("Planner: Received Vision Response.")
        
        # 4. Save Output Pages
        # Strict Compiler Mode: We replace any existing output pages
        db.query(Page).filter(
            Page.job_id == job_id, 
            Page.page_type == "output"
        ).delete()
        
        created_pages = []
        user_id = job.user_id
        
        pages_data = plan_json.get("pages", [])
        if not pages_data:
            print("Planner Warning: OpenAI returned no pages.")
            
        for p_data in pages_data:
            page_num = p_data.get("page", 1)
            content = p_data.get("content", "")
            
            new_page = Page(
                id=str(uuid.uuid4()),
                job_id=job_id,
                user_id=user_id,
                page_number=page_num,
                page_type="output",
                content=content,
                char_count=len(content),
                source="gpt4o_vision_compiler",
                status="planned"
            )
            db.add(new_page)
            created_pages.append(new_page)
            
        job.status = "planned"
        db.commit()
        print(f"Planner: Saved {len(created_pages)} output pages.")
        return len(created_pages)

    @staticmethod
    def _file_to_base64_images(file_path: str) -> List[str]:
        """
        Converts PDF or Image file to a list of Base64 strings.
        """
        b64_list = []
        
        # Determine type
        lower_path = file_path.lower()
        if lower_path.endswith(".pdf"):
            images = convert_from_path(file_path)
            # Limit pages for V1 to prevent token overflow (e.g., max 5)
            # User constraint: "Compiler". But 20 page PDF might fail API limits.
            # Let's verify with 10 for now.
            for img in images[:10]: 
                buf = io.BytesIO()
                img.save(buf, format="JPEG")
                b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
                b64_list.append(b64)
        else:
            # Assume Image
            with Image.open(file_path) as img:
                # Convert to RGB if needed (e.g. PNG with alpha)
                if img.mode in ("RGBA", "P"): 
                    img = img.convert("RGB")
                buf = io.BytesIO()
                img.save(buf, format="JPEG")
                b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
                b64_list.append(b64)
                
        return b64_list

    @staticmethod
    def replan_job(job_id: str, db: Session, layout_config: dict):
        """
        Phase 5: Re-Plan based on Layout Constraints.
        """
        print(f"Planner: Re-planning Job {job_id} with layout: {layout_config}")
        
        # 1. Get Job & File
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job or not job.original_file_path:
            raise Exception("Job has no original file path.")
            
        file_path = job.original_file_path
        if not os.path.exists(file_path):
            raise Exception(f"File not found on disk: {file_path}")
            
        # 2. Convert Source
        source_images_b64 = PlannerService._file_to_base64_images(file_path)
        
        # 3. Call OpenAI (Layout Engine)
        plan_json = PlannerService._call_gpt4o_vision(source_images_b64, DEFAULT_REF_IMAGE, layout_config)
        
        # 4. Replace Pages
        # Type: "handwritten" (Phase 5 requirement)
        db.query(Page).filter(
            Page.job_id == job_id, 
            Page.page_type.in_(["output", "handwritten"])
        ).delete()
        
        created_pages = []
        pages_data = plan_json.get("pages", [])
        
        for p_data in pages_data:
            new_page = Page(
                id=str(uuid.uuid4()),
                job_id=job_id,
                user_id=job.user_id,
                page_number=p_data.get("page", 1),
                page_type="handwritten", # Phase 5 specific
                content=p_data.get("content", ""),
                char_count=len(p_data.get("content", "")),
                source="gpt4o_vision_layout_engine",
                status="planned"
            )
            db.add(new_page)
            created_pages.append(new_page)
            
        # Update Job Config
        job.layout_config = layout_config
        job.status = "planned"
        db.commit()
        return len(created_pages)

    @staticmethod
    def _call_gpt4o_vision(source_b64s: List[str], ref_image_url: str, layout_config: dict = None) -> dict:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise Exception("OPENAI_API_KEY not set.")
            
        client = OpenAI(api_key=api_key)
        
        # 1. System Prompt (Phase 5)
        system_prompt = """
You are a document layout and pagination engine.

Your role:
- Read documents visually.
- Decide page boundaries based on handwriting capacity.
- Output page-separated content.

STRICT RULES:
- Do NOT rewrite, paraphrase, summarize, or correct text.
- Do NOT add or remove any words.
- Preserve wording and order EXACTLY as seen.
- Preserve line breaks where possible.
- You may ONLY decide where page breaks occur.

OUTPUT RULES:
- Output ONLY valid JSON.
- No markdown.
- No explanations.
- No extra keys.
"""

        # 2. User Prompt (Phase 5 Customisation Aware)
        layout_str = json.dumps(layout_config, indent=2) if layout_config else "{}"
        
        user_prompt_text = f"""
You are given:

1) The original input document (PDF or image).
2) A reference handwriting image showing writing density and style.
3) Layout constraints that affect how much content fits on a page.

Your task:
- Visually read the input document.
- Estimate handwritten page capacity based on the reference handwriting.
- Consider the layout constraints carefully.
- Split the document into handwritten-sized pages.
- Return page-separated content.

IMPORTANT:
- Preserve wording EXACTLY.
- Preserve order EXACTLY.
- Do NOT rewrite or clean text.
- Only split content.

Layout constraints (must be respected):
{layout_str}

Output format (STRICT):

{{
  "pages": [
    {{ "page": 1, "content": "EXACT text for page 1" }},
    {{ "page": 2, "content": "EXACT text for page 2" }}
  ]
}}

If layout constraints reduce page capacity, create more pages.
If constraints are generous, reduce page count.

Return ONLY JSON.
"""
        
        user_content = [{"type": "text", "text": user_prompt_text}]
        
        # Images
        for b64 in source_b64s:
            user_content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{b64}",
                    "detail": "high"
                }
            })
            
        # Reference (Last)
        user_content.append({
            "type": "image_url",
            "image_url": {
                "url": ref_image_url,
                "detail": "low"
            }
        })
        
        last_error = None
        for attempt in range(2):
            try:
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_content}
                    ],
                    response_format={"type": "json_object"},
                    max_tokens=4000,
                    temperature=0
                )
                
                content_str = response.choices[0].message.content
                data = json.loads(content_str)
                
                if "pages" not in data or not data["pages"]:
                    raise ValueError("Invalid/Empty pages list.")
                    
                return data
                
            except Exception as e:
                print(f"Planner visual attempt {attempt+1} failed: {e}")
                last_error = e
        
        raise Exception(f"Planner failed: {last_error}")
