"""
Test the full extraction pipeline with PDF to see what data is extracted
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

sys.path.insert(0, str(Path(__file__).parent))

from agents.production_workbook_generator import run_tool
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
    
    print("📄 Extracting PDF text...")
    pdf_text = extract_pdf_text(pdf_path)
    print(f"✅ Extracted {len(pdf_text)} characters")
    
    prompt = "Create call sheets based on the information in this PDF"
    
    print("\n🤖 Running full extraction pipeline...")
    print("=" * 60)
    
    result = run_tool(
        prompt=prompt,
        attached_file_content=pdf_text,
        enrich=False,  # Skip enrichment to see raw extraction
        progress_callback=None
    )
    
    print("\n" + "=" * 60)
    print("📊 EXTRACTION RESULTS:")
    print("=" * 60)
    
    data = result['data']
    prod_info = data.get('production_info', {})
    
    print(f"Job Name: {prod_info.get('job_name', 'N/A')}")
    print(f"Job Number: {prod_info.get('job_number', 'N/A')}")
    print(f"Client: {prod_info.get('client', 'N/A')}")
    print(f"Production Company: {prod_info.get('production_company', 'N/A')}")
    print(f"\nSchedule Days: {len(data.get('schedule_days', []))}")
    if data.get('schedule_days'):
        print(f"First day: {data['schedule_days'][0]}")
    
    print(f"\nCrew Members: {len(data.get('crew_list', []))}")
    crew_with_data = [c for c in data.get('crew_list', []) if c.get('rate') and c.get('rate') != 'TBD']
    print(f"Crew with rates: {len(crew_with_data)}")
    if crew_with_data:
        print("Sample crew with rates:")
        for crew in crew_with_data[:5]:
            print(f"  - {crew.get('role')}: ${crew.get('rate')}")
    
    print(f"\n✅ Workbook generated: {result['workbook_path']}")
