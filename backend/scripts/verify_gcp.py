import os
import io
from google.cloud import vision
from pdf2image import convert_from_bytes, convert_from_path

# Force set creds for this script test
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "service_account.json"

def test_gcp():
    print("Testing Google Cloud Vision API...")
    try:
        client = vision.ImageAnnotatorClient()
        print("✅ Client initialized.")
        
        # Test with a dummy image (just a black pixel) to check auth
        # Construct a minimal valid PNG
        dummy_png = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
        
        image = vision.Image(content=dummy_png)
        response = client.text_detection(image=image)
        
        if response.error.message:
            print(f"❌ API Returned Error: {response.error.message}")
        else:
            print("✅ API Call Successful (Auth works).")
            
    except Exception as e:
        print(f"❌ GCP Auth Failed: {e}")

def test_poppler():
    print("\nTesting Poppler (pdf2image)...")
    try:
        # Create a tiny dummy PDF in memory is hard without a library, 
        # but we can try to subprocess 'pdftoppm -h' which pdf2image uses.
        from pdf2image.exceptions import PDFInfoNotInstalledError
        try:
            # This triggers a check
            convert_from_bytes(b'dummy')
        except PDFInfoNotInstalledError:
            print("❌ Poppler is NOT installed or not in PATH.")
            return
        except Exception:
            # It will fail on dummy bytes, but if it's NOT PDFInfoNotInstalledError, 
            # then the binary was found at least.
            print("✅ Poppler seems to be installed (binary found).")
            pass
            
    except Exception as e:
        print(f"❌ Poppler Check Error: {e}")

if __name__ == "__main__":
    test_gcp()
    test_poppler()
