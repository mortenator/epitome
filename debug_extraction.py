"""
Debug script to see full extracted JSON from PDF
"""
import os
import sys
import json
from pathlib import Path

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

sys.path.insert(0, str(Path(__file__).parent))

from main import extract_with_gemini
import PyPDF2

def extract_pdf_text(pdf_path: str) -> str:
    """Extract text from PDF file."""
    with open(pdf_path, 'rb') as f:
        pdf_reader = PyPDF2.PdfReader(f)
        extracted_text = []
        for page_num, page in enumerate(pdf_reader.pages, 1):
            page_text = page.extract_text()
            if page_text.strip():
                extracted_text.append(f"--- Page {page_num} ---\n{page_text}")
        return f"[PDF file: {Path(pdf_path).name}]\n\n" + "\n\n".join(extracted_text)

if __name__ == "__main__":
    pdf_path = os.path.expanduser("~/Downloads/Epitome Sample_2026-01-09T093845 (1).pdf")
    pdf_text = extract_pdf_text(pdf_path)
    
    prompt = "Create call sheets based on the information in this PDF. Extract all production details, crew information, schedule, locations, and any other relevant information."
    
    print("🤖 Extracting with Gemini...")
    extracted_data = extract_with_gemini(prompt, pdf_text)
    
    print("\n" + "="*60)
    print("FULL EXTRACTED JSON:")
    print("="*60)
    print(json.dumps(extracted_data, indent=2))
    print("="*60)
