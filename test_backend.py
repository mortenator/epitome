#!/usr/bin/env python3
"""Test script for Epitome backend API"""
import requests
import sys
from pathlib import Path

# API endpoint
API_URL = "http://127.0.0.1:8000/api/generate"

# Prompt
PROMPT = "Use the attached budget to create a production well for an upcoming shoot in Oslo Norway scheduled for this saturday"

# File path
FILE_PATH = Path.home() / "Downloads" / "Epitome Sample_2026-01-09T093845.pdf"

def test_generate():
    """Test the generate endpoint"""
    if not FILE_PATH.exists():
        print(f"❌ Error: File not found at {FILE_PATH}")
        print(f"   Please check the file path")
        sys.exit(1)
    
    print(f"📤 Testing Epitome Backend API")
    print(f"   Prompt: {PROMPT}")
    print(f"   File: {FILE_PATH.name}")
    print(f"   URL: {API_URL}\n")
    
    # Prepare the request
    with open(FILE_PATH, 'rb') as f:
        files = {'file': (FILE_PATH.name, f, 'application/pdf')}
        data = {'prompt': PROMPT}
        
        try:
            print("🔄 Sending request...")
            response = requests.post(API_URL, files=files, data=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                job_id = result.get('job_id')
                print(f"✅ Request accepted!")
                print(f"   Job ID: {job_id}")
                print(f"\n📊 To check progress:")
                print(f"   curl http://127.0.0.1:8000/api/progress/{job_id}")
                print(f"\n📥 To download when ready:")
                print(f"   curl http://127.0.0.1:8000/api/download/{{filename}} -o workbook.xlsx")
            else:
                print(f"❌ Error: {response.status_code}")
                print(f"   {response.text}")
                sys.exit(1)
                
        except requests.exceptions.ConnectionError:
            print("❌ Error: Could not connect to API")
            print("   Make sure the server is running:")
            print("   uvicorn api.main:app --reload --host 127.0.0.1 --port 8000")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Error: {e}")
            sys.exit(1)

if __name__ == "__main__":
    test_generate()
