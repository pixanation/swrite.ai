import io
import numpy as np
import cv2
from fastapi import UploadFile
from PIL import Image
from pypdf import PdfReader
from dataclasses import dataclass

@dataclass
class SegregationResult:
    input_type: str
    pipeline: str
    requires_review: bool

async def segregate_input(content: str = None, file: UploadFile = None) -> SegregationResult:
    # Strict Rule: No Pasted Text
    if not file:
        raise ValueError("File upload required. Pasted text is not supported.")

    filename = file.filename.lower()
    
    # CASE 1 & 2: PDF
    if filename.endswith(".pdf"):
        return await _analyze_pdf(file)
    
    # CASE 3: Image (Assumed Handwritten per 'Scenario 3')
    if filename.endswith((".jpg", ".jpeg", ".png", ".bmp", ".webp", ".heic")):
        # We can still do a quick check if it's a valid image, but logic is simplified.
        # "Image File (handwritten) -> input_type = image_handwritten"
        return SegregationResult(
            input_type="image_handwritten",
            pipeline="direct_rewrite", # OCR + Render (No ChatGPT Planning)
            requires_review=True
        )
    
    raise ValueError(f"Unsupported file type: {filename}. Only PDF and Images allowed.")

async def _analyze_pdf(file: UploadFile) -> SegregationResult:
    # Read first few bytes/pages to check for text layer
    content_bytes = await file.read()
    file.file.seek(0) # Reset pointer
    
    try:
        reader = PdfReader(io.BytesIO(content_bytes))
        has_text = False
        
        # Check first 3 pages
        for i, page in enumerate(reader.pages[:3]):
            text = page.extract_text()
            if text and len(text.strip()) > 10: 
                has_text = True
                break
        
        if has_text:
            return SegregationResult(
                input_type="text_pdf",
                pipeline="pdf_flow", # Extract + ChatGPT Plan + Render
                requires_review=False
            )
        else:
            return SegregationResult(
                input_type="scanned_pdf",
                pipeline="pdf_flow", # OCR + Extract + ChatGPT Plan + Render
                requires_review=True
            )
            
    except Exception:
        # Fallback to scanned if parsing fails
        return SegregationResult(
            input_type="scanned_pdf",
            pipeline="pdf_flow",
            requires_review=True
        )


