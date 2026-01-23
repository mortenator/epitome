"""
Chat service for processing user messages with LLM integration.
Handles both Q&A and edit command execution.
"""
import os
import json
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from api.database import Project, CallSheet, ProjectCrew
from api.services.project_service import (
    update_call_sheet,
    update_crew_rsvp,
    update_project,
    update_location,
    get_project_for_frontend
)
from agents.prompts import EPITOME_CHAT_SYSTEM_PROMPT

# Check if Gemini is available
try:
    import google.genai as genai
    from google.genai import types
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None
    types = None


async def process_chat_message(
    db: AsyncSession,
    project_id: str,
    message: str
) -> Dict[str, Any]:
    """
    Process a chat message using Gemini API.
    
    Returns:
        Dict with 'type' ('answer' or 'edit'), 'response', and optionally 'action' and 'parameters'
    """
    # Fetch project data for context
    project_data = await get_project_for_frontend(db, project_id)
    if not project_data:
        return {
            "type": "answer",
            "response": "Sorry, I couldn't find the project. Please check the project ID."
        }
    
    # Build context string from project data
    context = _build_project_context(project_data)
    
    # Build user prompt with context
    user_prompt = f"""Project Context:
{context}

User Message: {message}

Please respond with valid JSON only, no markdown formatting."""
    
    # Call Gemini API
    if not GEMINI_AVAILABLE:
        return {
            "type": "answer",
            "response": "Sorry, the AI chat feature is not available. Please install google-genai package."
        }
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {
            "type": "answer",
            "response": "Sorry, the AI chat feature is not configured. Please set GEMINI_API_KEY."
        }
    
    try:
        client = genai.Client(api_key=api_key)
        
        config = types.GenerateContentConfig(
            temperature=0.3,
            maxOutputTokens=2048,
            systemInstruction=EPITOME_CHAT_SYSTEM_PROMPT,
        )
        
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=user_prompt,
            config=config
        )
        
        # Extract text from response
        response_text = response.text if hasattr(response, 'text') else str(response)
        
        # Parse JSON from response (handle markdown code blocks)
        json_str = _extract_json_from_response(response_text)
        result = json.loads(json_str)
        
        # If it's an edit command, execute it
        if result.get("type") == "edit":
            edit_result = await _execute_edit_command(
                db,
                project_id,
                result.get("action"),
                result.get("parameters", {}),
                project_data
            )
            
            if edit_result.get("success"):
                return {
                    "type": "edit",
                    "action": result.get("action"),
                    "response": result.get("response", "Edit completed successfully."),
                    "success": True
                }
            else:
                return {
                    "type": "answer",
                    "response": edit_result.get("error", "Sorry, I couldn't execute that edit. Please try again.")
                }
        
        # Return answer
        return {
            "type": "answer",
            "response": result.get("response", "I'm not sure how to help with that.")
        }
        
    except json.JSONDecodeError as e:
        return {
            "type": "answer",
            "response": f"Sorry, I had trouble understanding that. Could you rephrase? (Error: {str(e)})"
        }
    except Exception as e:
        return {
            "type": "answer",
            "response": f"Sorry, an error occurred: {str(e)}"
        }


def _build_project_context(project_data: Dict[str, Any]) -> str:
    """Build a context string from project data for the LLM."""
    lines = []
    
    # Project info
    proj = project_data.get("project", {})
    lines.append(f"Project: {proj.get('jobName', 'N/A')} ({proj.get('jobNumber', 'N/A')})")
    lines.append(f"Client: {proj.get('client', 'N/A')}")
    if proj.get("agency"):
        lines.append(f"Agency: {proj.get('agency')}")
    lines.append("")
    
    # Call sheets
    call_sheets = project_data.get("callSheets", [])
    if call_sheets:
        lines.append("Call Sheets:")
        for cs in call_sheets:
            lines.append(f"  Day {cs.get('dayNumber')}: {cs.get('shootDate', 'N/A')}")
            lines.append(f"    Production Call: {cs.get('productionCall', 'TBD')}")
            lines.append(f"    Crew Call: {cs.get('generalCrewCall', 'TBD')}")
            lines.append(f"    Talent Call: {cs.get('talentCall', 'TBD')}")
            if cs.get("hospital", {}).get("name"):
                lines.append(f"    Hospital: {cs.get('hospital', {}).get('name')} - {cs.get('hospital', {}).get('address', '')}")
            lines.append(f"    ID: {cs.get('id')}")
        lines.append("")
    
    # Locations
    locations = project_data.get("locations", [])
    if locations:
        lines.append("Locations:")
        for loc in locations:
            lines.append(f"  {loc.get('name', 'N/A')}: {loc.get('address', 'N/A')}")
            lines.append(f"    ID: {loc.get('id')}")
        lines.append("")
    
    # Crew by department
    departments = project_data.get("departments", [])
    if departments:
        lines.append("Crew:")
        for dept in departments:
            lines.append(f"  {dept.get('name')}:")
            for crew in dept.get("crew", []):
                crew_info = f"    {crew.get('role', 'N/A')}"
                if crew.get("name"):
                    crew_info += f" - {crew.get('name')}"
                if crew.get("callTime") and crew.get("callTime") != "TBD":
                    crew_info += f" (Call: {crew.get('callTime')})"
                lines.append(crew_info)
                lines.append(f"      ID: {crew.get('id')}")
        lines.append("")
    
    return "\n".join(lines)


def _extract_json_from_response(response_text: str) -> str:
    """Extract JSON from LLM response, handling markdown code blocks."""
    # Try to find JSON in markdown code blocks
    if "```json" in response_text:
        json_start = response_text.find("```json") + 7
        json_end = response_text.find("```", json_start)
        return response_text[json_start:json_end].strip()
    elif "```" in response_text:
        json_start = response_text.find("```") + 3
        json_end = response_text.find("```", json_start)
        return response_text[json_start:json_end].strip()
    else:
        # Try to find JSON object
        json_start = response_text.find("{")
        json_end = response_text.rfind("}") + 1
        if json_start >= 0 and json_end > json_start:
            return response_text[json_start:json_end]
        else:
            raise ValueError("No JSON found in response")


async def _execute_edit_command(
    db: AsyncSession,
    project_id: str,
    action: str,
    parameters: Dict[str, Any],
    project_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Execute an edit command based on action type."""
    try:
        if action == "update_call_sheet":
            call_sheet_id = parameters.get("call_sheet_id")
            if not call_sheet_id:
                # Try to find call sheet by day number from parameters
                day_number = parameters.get("dayNumber")
                if day_number:
                    call_sheets = project_data.get("callSheets", [])
                    matching_sheet = next(
                        (cs for cs in call_sheets if cs.get("dayNumber") == day_number),
                        None
                    )
                    if matching_sheet:
                        call_sheet_id = matching_sheet.get("id")
                
                # Fallback to first call sheet if still not found
                if not call_sheet_id:
                    call_sheets = project_data.get("callSheets", [])
                    if call_sheets:
                        call_sheet_id = call_sheets[0].get("id")
                    else:
                        return {"success": False, "error": "No call sheet found"}
            
            success = await update_call_sheet(
                db,
                call_sheet_id,
                day_name=parameters.get("dayName"),
                shoot_date=parameters.get("shootDate"),
                general_crew_call=parameters.get("generalCrewCall"),
                production_call=parameters.get("productionCall"),
                talent_call=parameters.get("talentCall"),
                hospital_name=parameters.get("hospitalName"),
                hospital_address=parameters.get("hospitalAddress")
            )
            return {"success": success}
        
        elif action == "update_crew_rsvp":
            crew_id = parameters.get("crew_id")
            if not crew_id:
                return {"success": False, "error": "Crew ID is required"}
            
            success = await update_crew_rsvp(
                db,
                crew_id,
                call_time=parameters.get("callTime"),
                location=parameters.get("location"),
                call_sheet_id=parameters.get("callSheetId")
            )
            return {"success": success}
        
        elif action == "update_project":
            success = await update_project(
                db,
                project_id,
                job_name=parameters.get("jobName"),
                client=parameters.get("client"),
                agency=parameters.get("agency")
            )
            return {"success": success}
        
        elif action == "update_location":
            location_id = parameters.get("location_id")
            if not location_id:
                return {"success": False, "error": "Location ID is required"}
            
            success = await update_location(
                db,
                location_id,
                address=parameters.get("address"),
                name=parameters.get("name")
            )
            return {"success": success}
        
        else:
            return {"success": False, "error": f"Unknown action: {action}"}
    
    except Exception as e:
        return {"success": False, "error": str(e)}
