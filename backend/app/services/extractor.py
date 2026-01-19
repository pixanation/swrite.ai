import io
import uuid
import json
import os
from sqlalchemy.orm import Session
from app.models.job import Job
from app.models.page import Page
from pypdf import PdfReader
from google.cloud import vision

# Real Google OCR Service
class GoogleOCR:
    @staticmethod
    def process_file(file_bytes: bytes, is_pdf: bool = False):
        """
        Calls Google Cloud Vision API.
        Returns: list of dicts { "content": str, "source": str }
        """
        client = vision.ImageAnnotatorClient()
        
        # 1. Image Processing
        if not is_pdf:
            image = vision.Image(content=file_bytes)
            # Use DOCUMENT_TEXT_DETECTION for dense text/handwriting
            response = client.document_text_detection(image=image)
            
            if response.error.message:
                raise Exception(f"Google Vision Error: {response.error.message}")
                
            # SIMPLIFICATION: Extract Plain Text Only
            full_text = response.full_text_annotation.text
            
            return [{
                "content": full_text,
                "source": "google_ocr_image"
            }]
            
        # 2. PDF Processing
        else:
            from pdf2image import convert_from_bytes
            from app.core.config import POPPLER_PATH
            
            try:
                images = convert_from_bytes(file_bytes, poppler_path=POPPLER_PATH)
            except Exception as e:
                raise Exception(f"Failed to rasterize PDF for OCR: {e}. Is Poppler installed?")

            results = []
            for img in images:
                # Convert PIL image to bytes
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format='JPEG')
                content = img_byte_arr.getvalue()
                
                # Recursive call treating it as an image
                page_result = GoogleOCR.process_file(content, is_pdf=False)
                # Override source to reflect it came from a PDF
                page_result[0]["source"] = "google_ocr_pdf_page"
                results.extend(page_result)
                
            return results


class Extractor:
    @staticmethod
    def extract_job(job: Job, db: Session, file_bytes: bytes):
        """
        Route the job to the correct pipeline based on input_type.
        """
        print(f"Extractor: Starting extraction for Job {job.id} ({job.input_type})")
        
        pages_data = []

        try:
            if job.input_type == "text_pdf":
                pages_data = Extractor._pipeline_text_pdf(file_bytes)
            elif job.input_type == "scanned_pdf":
                pages_data = Extractor._pipeline_scanned_pdf(file_bytes)
            elif job.input_type == "image_handwritten":
                pages_data = Extractor._pipeline_image_handwritten(file_bytes)
            else:
                raise ValueError(f"Unknown input_type: {job.input_type}")
                
            # Save Pages to DB
            for i, p_data in enumerate(pages_data):
                page = Page(
                    id=str(uuid.uuid4()),
                    job_id=job.id,
                    user_id=job.user_id,
                    page_number=i+1,
                    status="completed",
                    content=p_data["content"],
                    source=p_data["source"],
                    structure_map={} # Deprecated / Empty
                )
                db.add(page)
            
            job.status = "extracted" 
            db.commit()
            print(f"Extractor: Saved {len(pages_data)} pages.")
            return len(pages_data)

        except Exception as e:
            print(f"Extraction Failed: {e}")
            job.status = "failed"
            db.commit()
            raise e

    @staticmethod
    def _pipeline_text_pdf(file_bytes: bytes) -> list:
        """
        Pipeline A: pypdf Extraction.
        """
        pages_output = []
        reader = PdfReader(io.BytesIO(file_bytes))
        
        for page in reader.pages:
            text = page.extract_text()
            pages_output.append({
                "content": text,
                "source": "pypdf"
            })
            
        return pages_output

    @staticmethod
    def _pipeline_scanned_pdf(file_bytes: bytes) -> list:
        return GoogleOCR.process_file(file_bytes, is_pdf=True)

    @staticmethod
    def _pipeline_image_handwritten(file_bytes: bytes) -> list:
        return GoogleOCR.process_file(file_bytes, is_pdf=False)
