"""
Epitome Main Entry Point
Runs the full Extraction -> Transformation -> Generation pipeline
"""

import os
import json
import sys
from datetime import datetime, timedelta
from agents.prompts import EPITOME_EXTRACTION_SYSTEM_PROMPT
from agents.production_workbook_generator import EpitomeWorkbookGenerator

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, continue without it

try:
    from google import genai
    GEMINI_AVAILABLE = True
except ImportError:
    genai = None
    GEMINI_AVAILABLE = False


def calculate_relative_date(date_str: str) -> str:
    """
    Helper to calculate relative dates like "next Monday"
    This is a simplified version - in production, use a proper date parser
    """
    today = datetime.now()
    
    if "next monday" in date_str.lower():
        days_ahead = 0 - today.weekday()  # Monday is 0
        if days_ahead <= 0:  # Target day already happened this week
            days_ahead += 7
        return (today + timedelta(days=days_ahead)).strftime("%Y-%m-%d")
    elif "monday" in date_str.lower():
        days_ahead = 0 - today.weekday()
        if days_ahead < 0:
            days_ahead += 7
        return (today + timedelta(days=days_ahead)).strftime("%Y-%m-%d")
    
    # Default: return today's date
    return today.strftime("%Y-%m-%d")


def extract_with_gemini(prompt: str, attached_file_content: str = None) -> dict:
    """
    Uses Google Gemini API to extract structured production data from natural language prompt.
    """
    if not GEMINI_AVAILABLE:
        print("Warning: google-genai package not installed. Run: pip install google-genai")
        print("Falling back to mock data extraction.")
        return extract_mock_data(prompt)
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Warning: GEMINI_API_KEY not set. Using mock data extraction.")
        return extract_mock_data(prompt)
    
    try:
        client = genai.Client(api_key=api_key)
        
        # Build the user prompt
        user_prompt = f"User Prompt: {prompt}\n\n"
        if attached_file_content:
            user_prompt += f"Attached File Content:\n{attached_file_content}\n\n"
        
        user_prompt += "Please extract the production information and return ONLY valid JSON following the schema above. Do not include any markdown formatting or explanations, just the JSON object."
        
        # Generate response using Gemini
        from google.genai import types
        config = types.GenerateContentConfig(
            temperature=0.2,  # Lower temperature for structured extraction
            maxOutputTokens=4096,
            systemInstruction=EPITOME_EXTRACTION_SYSTEM_PROMPT,
        )
        
        response = client.models.generate_content(
            model="gemini-1.5-pro",
            contents=user_prompt,
            config=config
        )
        # Extract text from response
        response_text = response.text if hasattr(response, 'text') else str(response)
        
        # Try to parse JSON from the response
        # Gemini might wrap it in markdown code blocks
        if "```json" in response_text:
            json_start = response_text.find("```json") + 7
            json_end = response_text.find("```", json_start)
            json_str = response_text[json_start:json_end].strip()
        elif "```" in response_text:
            json_start = response_text.find("```") + 3
            json_end = response_text.find("```", json_start)
            json_str = response_text[json_start:json_end].strip()
        else:
            # Try to find JSON object in the response
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
            else:
                raise ValueError("No JSON found in response")
        
        extracted_data = json.loads(json_str)
        return extracted_data
        
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        print("Falling back to mock data extraction...")
        return extract_mock_data(prompt)


def extract_mock_data(prompt: str) -> dict:
    """
    Fallback mock extraction when Claude API is not available.
    Parses basic information from the prompt.
    """
    prompt_lower = prompt.lower()
    
    # Extract number of days
    days_count = 1
    for i in range(1, 11):
        if f"{i} day" in prompt_lower or f"{i}-day" in prompt_lower:
            days_count = i
            break
    
    # Extract client/job name
    job_name = "TBD"
    client = "TBD"
    
    # Look for common client names
    if "nike" in prompt_lower:
        client = "Nike"
        job_name = "Nike Campaign"
    elif "adidas" in prompt_lower:
        client = "Adidas"
        job_name = "Adidas Campaign"
    
    # Calculate start date
    start_date = calculate_relative_date(prompt)
    base_date = datetime.strptime(start_date, "%Y-%m-%d")
    
    # Generate schedule days
    schedule_days = []
    for i in range(days_count):
        day_date = base_date + timedelta(days=i)
        schedule_days.append({
            "day_number": i + 1,
            "date": day_date.strftime("%Y-%m-%d"),
            "crew_call": "07:00 AM",
            "talent_call": "09:00 AM",
            "shoot_call": "08:00 AM"
        })
    
    return {
        "production_info": {
            "job_name": job_name,
            "client": client,
            "production_company": "Epitome",
            "job_number": f"EP-{datetime.now().strftime('%Y%m%d')}-001"
        },
        "logistics": {
            "locations": [
                {"name": "TBD", "address": "TBD", "parking": "TBD"}
            ],
            "hospital": {"name": "TBD", "address": "TBD"},
            "weather": {"high": "TBD", "low": "TBD", "sunrise": "TBD", "sunset": "TBD"}
        },
        "schedule_days": schedule_days,
        "crew_list": []  # Empty - will use default template
    }


def run_epitome_flow(prompt: str, attached_file: str = None):
    """
    Main pipeline: Extraction -> Transformation -> Generation
    """
    print(f"🎬 Epitome Production Workbook Generator")
    print(f"📝 Processing prompt: '{prompt}'")
    print()
    
    # Step 1: Extraction
    print("🔍 Step 1: Extracting structured data from prompt...")
    attached_content = None
    if attached_file and os.path.exists(attached_file):
        with open(attached_file, 'r') as f:
            attached_content = f.read()
    
    extracted_data = extract_with_gemini(prompt, attached_content)
    print(f"✅ Extracted data for {len(extracted_data.get('schedule_days', []))} day(s)")
    print()
    
    # Step 2: Generation
    print("📊 Step 2: Generating production workbook...")
    output_filename = f"Epitome_Production_Workbook_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    
    generator = EpitomeWorkbookGenerator(
        data=extracted_data,
        output_filename=output_filename
    )
    
    final_path = generator.generate()
    print(f"✅ Workbook generated: {final_path}")
    print()
    
    # Summary
    print("📋 Summary:")
    print(f"   Job: {extracted_data['production_info'].get('job_name', 'TBD')}")
    print(f"   Client: {extracted_data['production_info'].get('client', 'TBD')}")
    print(f"   Days: {len(extracted_data.get('schedule_days', []))}")
    print(f"   Crew Members: {len(extracted_data.get('crew_list', []))}")
    print()
    
    return final_path


if __name__ == "__main__":
    # Example usage
    if len(sys.argv) > 1:
        prompt = " ".join(sys.argv[1:])
        attached_file = None
        if len(sys.argv) > 2 and os.path.exists(sys.argv[-1]):
            attached_file = sys.argv[-1]
    else:
        # Default test prompt
        prompt = "Create call sheets for a 3 day shoot for Nike starting next Monday"
    
    run_epitome_flow(prompt, attached_file)
