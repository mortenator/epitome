"""
Test script to extract PDF content and test Gemini extraction
"""
import os
import sys
from pathlib import Path

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from main import extract_with_gemini
import io
import PyPDF2

def extract_pdf_text(pdf_path: str) -> str:
    """Extract text from PDF file."""
    try:
        with open(pdf_path, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            
            # Extract text from all pages
            extracted_text = []
            for page_num, page in enumerate(pdf_reader.pages, 1):
                page_text = page.extract_text()
                if page_text.strip():
                    extracted_text.append(f"--- Page {page_num} ---\n{page_text}")
            
            if extracted_text:
                return f"[PDF file: {Path(pdf_path).name}]\n\n" + "\n\n".join(extracted_text)
            else:
                return f"[PDF file: {Path(pdf_path).name} - No extractable text found]"
    except Exception as e:
        return f"[PDF file: {Path(pdf_path).name} - Error extracting text: {str(e)}]"

if __name__ == "__main__":
    pdf_path = os.path.expanduser("~/Downloads/Epitome Sample_2026-01-09T093845 (1).pdf")
    
    if not os.path.exists(pdf_path):
        print(f"❌ PDF file not found: {pdf_path}")
        sys.exit(1)
    
    print(f"📄 Extracting text from PDF: {pdf_path}")
    print("=" * 60)
    
    # Extract PDF text
    pdf_text = extract_pdf_text(pdf_path)
    
    print(f"✅ Extracted {len(pdf_text)} characters from PDF")
    print(f"\n📝 First 500 characters of extracted text:")
    print("-" * 60)
    print(pdf_text[:500])
    print("-" * 60)
    print()
    
    # Test with Gemini
    prompt = "Create call sheets based on the information in this PDF"
    
    print("🤖 Testing Gemini extraction...")
    print("=" * 60)
    
    try:
        extracted_data = extract_with_gemini(prompt, pdf_text)
        
        print("\n✅ Extraction successful!")
        print(f"📊 Extracted data:")
        print(f"   Job: {extracted_data.get('production_info', {}).get('job_name', 'N/A')}")
        print(f"   Client: {extracted_data.get('production_info', {}).get('client', 'N/A')}")
        print(f"   Schedule Days: {len(extracted_data.get('schedule_days', []))}")
        print(f"   Crew Members: {len(extracted_data.get('crew_list', []))}")
        
        # Show a sample of the extracted data
        if extracted_data.get('schedule_days'):
            print(f"\n📅 Sample schedule day:")
            print(f"   {extracted_data['schedule_days'][0]}")
        
        if extracted_data.get('crew_list'):
            print(f"\n👥 Sample crew member:")
            print(f"   {extracted_data['crew_list'][0]}")
            
    except Exception as e:
        print(f"❌ Error during extraction: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
