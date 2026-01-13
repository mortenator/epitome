"""
Test workbook generation with extracted PDF data
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

from debug_extraction import extract_pdf_text, extract_with_gemini
from agents.production_workbook_generator import EpitomeWorkbookGenerator

if __name__ == "__main__":
    pdf_path = os.path.expanduser("~/Downloads/Epitome Sample_2026-01-09T093845 (1).pdf")
    pdf_text = extract_pdf_text(pdf_path)
    
    prompt = "Create call sheets based on the information in this PDF"
    
    print("🤖 Extracting data from PDF...")
    extracted_data = extract_with_gemini(prompt, pdf_text)
    
    print("\n📊 Extracted Data Summary:")
    print(f"   Job Name: {extracted_data['production_info'].get('job_name')}")
    print(f"   Job Number: {extracted_data['production_info'].get('job_number')}")
    print(f"   Client: {extracted_data['production_info'].get('client')}")
    print(f"   Schedule Days: {len(extracted_data.get('schedule_days', []))}")
    print(f"   Crew Members: {len(extracted_data.get('crew_list', []))}")
    print(f"   Crew with rates: {sum(1 for c in extracted_data.get('crew_list', []) if c.get('rate') and c.get('rate') != 'TBD')}")
    
    print("\n📝 Generating workbook...")
    output_file = "test_workbook.xlsx"
    generator = EpitomeWorkbookGenerator(data=extracted_data, output_filename=output_file)
    final_path = generator.generate()
    
    print(f"✅ Workbook generated: {final_path}")
    print("\n📋 Check the workbook to see if the extracted data appears correctly!")
