"""
Project service for database operations.
Handles saving and retrieving project data for the frontend.
"""
import uuid
from datetime import datetime
from typing import Optional

from dateutil import parser as date_parser
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.database import (
    CallSheet,
    CallSheetRsvp,
    Client,
    CrewMember,
    Location,
    Organization,
    Project,
    ProjectCrew,
    ScheduleEvent,
)

# =============================================================================
# Department Mapping
# =============================================================================

DEPARTMENT_NORMALIZE_MAP = {
    "PRODUCTION": "PRODUCTION",
    "CAMERA": "CAMERA",
    "CAMERA DEPT": "CAMERA",
    "DIGITAL": "CAMERA",  # Digital tech grouped with camera
    "G&E": "GRIP_ELECTRIC",
    "GRIP": "GRIP_ELECTRIC",
    "ELECTRIC": "GRIP_ELECTRIC",
    "LIGHTING": "GRIP_ELECTRIC",  # Lighting grouped with G&E
    "GRIP & ELECTRIC": "GRIP_ELECTRIC",
    "GRIP_ELECTRIC": "GRIP_ELECTRIC",
    "ART": "ART",
    "ART DEPT": "ART",
    "WARDROBE": "WARDROBE",
    "HAIR": "HAIR_MAKEUP",
    "MAKEUP": "HAIR_MAKEUP",
    "HAIR & MAKEUP": "HAIR_MAKEUP",
    "HAIR_MAKEUP": "HAIR_MAKEUP",
    "HMU": "HAIR_MAKEUP",  # Common abbreviation
    "VANITIES": "HAIR_MAKEUP",
    "SOUND": "SOUND",
    "LOCATIONS": "LOCATIONS",
    "TRANSPORTATION": "TRANSPORTATION",
    "TRANSPO": "TRANSPORTATION",
    "CATERING": "CATERING",
    "CRAFT": "CATERING",
    "CRAFT SERVICES": "CATERING",  # Full name variation
    "POST": "POST_PRODUCTION",
    "POST PRODUCTION": "POST_PRODUCTION",
    "POST_PRODUCTION": "POST_PRODUCTION",
    "STILLS": "CAMERA",  # Group stills with camera
    "TALENT": "OTHER",
    "MGMT": "PRODUCTION",
    "DIRECTING": "PRODUCTION",  # Directors in production
    "MEDICAL": "OTHER",  # Medics in other
    "OTHER": "OTHER",
}

DEPARTMENT_DISPLAY_MAP = {
    "PRODUCTION": "PRODUCTION",
    "CAMERA": "CAMERA DEPT",
    "GRIP_ELECTRIC": "GRIP & ELECTRIC",
    "ART": "ART DEPT",
    "WARDROBE": "WARDROBE",
    "HAIR_MAKEUP": "HAIR & MAKEUP",
    "SOUND": "SOUND",
    "LOCATIONS": "LOCATIONS",
    "TRANSPORTATION": "TRANSPORTATION",
    "CATERING": "CATERING",
    "POST_PRODUCTION": "POST PRODUCTION",
    "OTHER": "OTHER",
}


def normalize_department(dept: str) -> str:
    """Normalize department string to enum value."""
    if not dept:
        return "OTHER"
    return DEPARTMENT_NORMALIZE_MAP.get(dept.upper().strip(), "OTHER")


def format_department_name(dept: str) -> str:
    """Format department enum to display name."""
    return DEPARTMENT_DISPLAY_MAP.get(dept, dept)


def parse_rate(rate_value) -> float:
    """Parse a rate value (int, float, or string like '2,400.00') to float."""
    if rate_value is None:
        return 0.0
    if isinstance(rate_value, (int, float)):
        return float(rate_value)
    if isinstance(rate_value, str):
        try:
            # Remove commas and parse
            cleaned = rate_value.replace(",", "").strip()
            if cleaned:
                return float(cleaned)
        except (ValueError, TypeError):
            pass
    return 0.0


# =============================================================================
# Date/Time Helpers
# =============================================================================

def parse_date(date_str: Optional[str]) -> Optional[datetime]:
    """Parse a date string to datetime."""
    if not date_str or date_str == "TBD":
        return None
    try:
        return date_parser.parse(date_str)
    except Exception:
        return None


def parse_time(time_str: Optional[str], base_date: Optional[datetime] = None) -> Optional[datetime]:
    """Parse a time string to datetime."""
    if not time_str or time_str == "TBD":
        return None
    try:
        parsed = date_parser.parse(time_str)
        if base_date:
            return base_date.replace(
                hour=parsed.hour,
                minute=parsed.minute,
                second=0,
                microsecond=0
            )
        return parsed
    except Exception:
        return None


def format_time(dt: Optional[datetime]) -> str:
    """Format datetime to time string."""
    if not dt:
        return "TBD"
    try:
        # Try macOS/Linux format first (removes leading zero from hour)
        formatted = dt.strftime("%-I:%M %p")
        return formatted
    except ValueError:
        # Windows doesn't support %-I, use alternative
        formatted = dt.strftime("%I:%M %p")
        # Remove leading zero only from hour, not from minutes
        if formatted.startswith("0"):
            formatted = formatted[1:]
        return formatted


# =============================================================================
# Main Service Functions
# =============================================================================

async def ensure_default_organization(db: AsyncSession) -> str:
    """Ensure a default organization exists and return its ID."""
    result = await db.execute(
        select(Organization).where(Organization.slug == "default")
    )
    org = result.scalar_one_or_none()

    if not org:
        org = Organization(
            id=str(uuid.uuid4()),
            name="Default Organization",
            slug="default",
            updatedAt=datetime.utcnow(),
        )
        db.add(org)
        await db.flush()

    return org.id


async def get_or_create_client(
    db: AsyncSession,
    client_name: str,
    organization_id: str
) -> Optional[str]:
    """
    Get existing client by name or create a new one.
    
    Returns:
        Client ID, or None if client_name is empty/TBD
    """
    if not client_name or client_name == "TBD":
        return None
    
    # Check for existing client
    result = await db.execute(
        select(Client).where(
            Client.name == client_name,
            Client.organizationId == organization_id
        )
    )
    existing_client = result.scalar_one_or_none()
    
    if existing_client:
        return existing_client.id
    
    # Create new client
    client_id = str(uuid.uuid4())
    client = Client(
        id=client_id,
        name=client_name,
        organizationId=organization_id,
        updatedAt=datetime.utcnow(),
    )
    db.add(client)
    await db.flush()
    
    return client_id


async def create_project_from_generation(
    db: AsyncSession,
    enriched_data: dict,
    organization_id: Optional[str] = None
) -> str:
    """
    Save generated production data to database.

    Args:
        db: Database session
        enriched_data: The enriched JSON from the LLM extraction
        organization_id: Optional org ID (uses default if not provided)

    Returns:
        The created project ID
    """
    # Ensure we have an organization
    if not organization_id:
        organization_id = await ensure_default_organization(db)

    prod_info = enriched_data.get("production_info", {})
    logistics = enriched_data.get("logistics", {})

    # Get or create client
    client_name = prod_info.get("client", "TBD")
    client_id = await get_or_create_client(db, client_name, organization_id)

    # Get or create Project (handle duplicate job numbers)
    job_number = prod_info.get("job_number") or f"EP-{datetime.now().strftime('%Y%m%d-%H%M')}"
    
    # Check if project with this job number already exists
    existing_project_result = await db.execute(
        select(Project).where(
            Project.jobNumber == job_number,
            Project.organizationId == organization_id
        )
    )
    existing_project = existing_project_result.scalar_one_or_none()
    
    if existing_project:
        # Update existing project
        project_id = existing_project.id
        existing_project.jobName = prod_info.get("job_name", existing_project.jobName)
        existing_project.client = client_name  # Keep legacy field for backward compatibility
        existing_project.clientId = client_id  # Set new clientId field
        existing_project.agency = prod_info.get("agency") or existing_project.agency
        existing_project.brand = prod_info.get("brand") or existing_project.brand
        existing_project.updatedAt = datetime.utcnow()
        project = existing_project
        print(f"[DB DEBUG] Updating existing project {project_id} with job number {job_number}")
    else:
        # Create new project
        project_id = str(uuid.uuid4())
        project = Project(
            id=project_id,
            jobNumber=job_number,
            jobName=prod_info.get("job_name", "Untitled Project"),
            client=client_name,  # Keep legacy field for backward compatibility
            clientId=client_id,  # Set new clientId field
            agency=prod_info.get("agency"),
            brand=prod_info.get("brand"),
            organizationId=organization_id,
            updatedAt=datetime.utcnow(),
        )
        db.add(project)
        print(f"[DB DEBUG] Creating new project {project_id} with job number {job_number}")

    # Create or update Locations
    # First, delete existing locations for this project (we'll recreate them)
    await db.execute(
        delete(Location).where(Location.projectId == project_id)
    )
    
    location_ids = {}
    for loc_data in logistics.get("locations", []):
        loc_id = str(uuid.uuid4())
        location = Location(
            id=loc_id,
            name=loc_data.get("name", "Location"),
            address=loc_data.get("address"),
            city=loc_data.get("city"),
            state=loc_data.get("state"),
            parkingNotes=loc_data.get("parking"),
            mapLink=loc_data.get("map_link"),
            projectId=project_id,
        )
        db.add(location)
        location_ids[loc_data.get("name", "Location")] = loc_id

    # Create or update Call Sheets for each schedule day
    schedule_days = enriched_data.get("schedule_days", [])
    if not schedule_days:
        # Create at least one call sheet
        schedule_days = [{"day_number": 1, "date": datetime.now().strftime("%Y-%m-%d")}]

    # Delete existing call sheets for this project (we'll recreate them)
    await db.execute(
        delete(CallSheet).where(CallSheet.projectId == project_id)
    )

    call_sheet_map = {}  # day_number -> call_sheet_id
    weather = logistics.get("weather", {})
    hospital = logistics.get("hospital", {})

    for day in schedule_days:
        day_num = day.get("day_number", 1)
        shoot_date = parse_date(day.get("date")) or datetime.now()
        
        # Get day-specific weather if available
        day_weather = day.get("weather", {})
        if not day_weather:
            day_weather = weather  # Fallback to logistics weather
        
        # Initialize weather variables FIRST (before any conditional checks)
        weather_high = None
        weather_low = None
        weather_summary = None
        weather_sunrise = None
        weather_sunset = None
        
        # Debug: Log weather data being saved
        if day_weather:
            print(f"[DB DEBUG] Day {day_num} weather data: {day_weather}")
        
        # Extract weather data properly
        if day_weather:
            # Handle nested temperature structure
            temp_data = day_weather.get("temperature", {})
            if isinstance(temp_data, dict):
                weather_high = temp_data.get("high", "").replace("F", "").strip() if temp_data.get("high") else None
                weather_low = temp_data.get("low", "").replace("F", "").strip() if temp_data.get("low") else None
            else:
                # Fallback for old format
                weather_high = str(day_weather.get("high", "")).replace("F", "").strip() if day_weather.get("high") else None
                weather_low = str(day_weather.get("low", "")).replace("F", "").strip() if day_weather.get("low") else None
            
            weather_summary = day_weather.get("conditions") or day_weather.get("summary")
            weather_sunrise = day_weather.get("sunrise")
            weather_sunset = day_weather.get("sunset")
        
        # Debug: Log extracted values
        print(f"[DB DEBUG] Day {day_num} extracted - high: {weather_high}, low: {weather_low}, sunrise: {weather_sunrise}, sunset: {weather_sunset}")
        
        # Parse call times with debug logging
        crew_call_time = parse_time(day.get("crew_call"), shoot_date)
        shoot_call_time = parse_time(day.get("shoot_call"), shoot_date)
        
        # Debug: Log what's being saved
        print(f"[DB DEBUG] Day {day_num} - crew_call from data: '{day.get('crew_call')}', parsed: {crew_call_time}, formatted: {format_time(crew_call_time)}")
        
        call_sheet = CallSheet(
            id=str(uuid.uuid4()),
            dayNumber=day_num,
            shootDate=shoot_date,
            generalCrewCall=crew_call_time,
            firstShot=shoot_call_time,
            weatherHigh=weather_high,
            weatherLow=weather_low,
            weatherSummary=weather_summary,
            sunrise=weather_sunrise,
            sunset=weather_sunset,
            nearestHospital=hospital.get("name"),
            hospitalAddress=hospital.get("address"),
            projectId=project_id,
            updatedAt=datetime.utcnow(),
        )
        db.add(call_sheet)
        call_sheet_map[day_num] = call_sheet.id

    # Delete existing project crew and RSVPs (we'll recreate them)
    # Note: RSVPs will be cascade deleted when ProjectCrew is deleted
    await db.execute(
        delete(ProjectCrew).where(ProjectCrew.projectId == project_id)
    )

    # Create ProjectCrew entries with linked CrewMember records
    crew_list = enriched_data.get("crew_list", [])
    for crew_data in crew_list:
        department = normalize_department(crew_data.get("department", "OTHER"))

        # Extract crew member details
        name = crew_data.get("name", "")
        first_name = ""
        last_name = ""
        if name and name != "TBD":
            name_parts = name.strip().split(" ", 1)
            first_name = name_parts[0] if name_parts else ""
            last_name = name_parts[1] if len(name_parts) > 1 else ""

        # Get or create CrewMember record (with deduplication by email/phone)
        crew_member_id = None
        if first_name:  # Only create if we have at least a first name
            email = crew_data.get("email")
            phone = crew_data.get("phone")
            
            # Check for existing crew member by email or phone
            existing_crew = None
            if email:
                result = await db.execute(
                    select(CrewMember).where(
                        CrewMember.email == email,
                        CrewMember.organizationId == organization_id
                    )
                )
                existing_crew = result.scalar_one_or_none()
            
            if not existing_crew and phone:
                result = await db.execute(
                    select(CrewMember).where(
                        CrewMember.phone == phone,
                        CrewMember.organizationId == organization_id
                    )
                )
                existing_crew = result.scalar_one_or_none()
            
            if existing_crew:
                # Merge: update existing record with new data
                existing_crew.firstName = first_name or existing_crew.firstName
                existing_crew.lastName = last_name or existing_crew.lastName
                existing_crew.email = email or existing_crew.email
                existing_crew.phone = phone or existing_crew.phone
                existing_crew.department = department or existing_crew.department
                existing_crew.primaryRole = crew_data.get("role") or existing_crew.primaryRole
                existing_crew.updatedAt = datetime.utcnow()
                crew_member_id = existing_crew.id
            else:
                # Create new crew member
                crew_member_id = str(uuid.uuid4())
                crew_member = CrewMember(
                    id=crew_member_id,
                    firstName=first_name,
                    lastName=last_name or "",
                    email=email,
                    phone=phone,
                    department=department,
                    primaryRole=crew_data.get("role"),
                    organizationId=organization_id,
                    updatedAt=datetime.utcnow(),
                )
                db.add(crew_member)

        # Create ProjectCrew entry
        project_crew_id = str(uuid.uuid4())
        project_crew = ProjectCrew(
            id=project_crew_id,
            role=crew_data.get("role", "TBD"),
            department=department,
            dealRate=parse_rate(crew_data.get("rate")),
            projectId=project_id,
            crewMemberId=crew_member_id,  # Link to CrewMember if created
            updatedAt=datetime.utcnow(),
        )
        db.add(project_crew)

        # Create RSVPs for each call sheet
        for day_num, call_sheet_id in call_sheet_map.items():
            # Get the day-specific call time or use crew's default
            day_data = next((d for d in schedule_days if d.get("day_number") == day_num), {})
            crew_call = day_data.get("crew_call")

            rsvp = CallSheetRsvp(
                id=str(uuid.uuid4()),
                callSheetId=call_sheet_id,
                projectCrewId=project_crew_id,
                personalizedCallTime=parse_time(crew_data.get("call_time") or crew_call),
                personalizedNotes=crew_data.get("location", "Set"),
                updatedAt=datetime.utcnow(),
            )
            db.add(rsvp)

    await db.commit()
    return project_id


async def get_project_for_frontend(
    db: AsyncSession,
    project_id: str
) -> Optional[dict]:
    """
    Fetch project data formatted for the frontend.

    Returns data matching the frontend's Department[] and ProductionInfo interfaces.
    """
    # Fetch project with client relation
    result = await db.execute(
        select(Project)
        .where(Project.id == project_id)
        .options(selectinload(Project.client_relation))
    )
    project = result.scalar_one_or_none()
    if not project:
        return None

    # Fetch call sheets
    sheets_result = await db.execute(
        select(CallSheet)
        .where(CallSheet.projectId == project_id)
        .order_by(CallSheet.dayNumber)
    )
    call_sheets = sheets_result.scalars().all()

    # Fetch project crew with RSVPs
    crew_result = await db.execute(
        select(ProjectCrew)
        .where(ProjectCrew.projectId == project_id)
        .options(selectinload(ProjectCrew.crew_member))
    )
    project_crew = crew_result.scalars().all()

    # Fetch locations
    locations_result = await db.execute(
        select(Location).where(Location.projectId == project_id)
    )
    locations = locations_result.scalars().all()

    # Get first call sheet for default RSVP data
    first_call_sheet = call_sheets[0] if call_sheets else None

    # Group crew by department
    departments_map: dict[str, list[dict]] = {}
    for crew in project_crew:
        dept_name = format_department_name(crew.department)
        if dept_name not in departments_map:
            departments_map[dept_name] = []

        # Get RSVP for first call sheet
        rsvp = None
        if first_call_sheet:
            rsvp_result = await db.execute(
                select(CallSheetRsvp)
                .where(CallSheetRsvp.projectCrewId == crew.id)
                .where(CallSheetRsvp.callSheetId == first_call_sheet.id)
            )
            rsvp = rsvp_result.scalar_one_or_none()

        # Get crew member details if linked
        name = None
        phone = None
        email = None
        if crew.crew_member:
            name = f"{crew.crew_member.firstName} {crew.crew_member.lastName}".strip()
            phone = crew.crew_member.phone
            email = crew.crew_member.email
            # If name is empty after stripping, set to None
            if not name:
                name = None

        # Always add crew member to departments, even if name is None (role is still available)
        departments_map[dept_name].append({
            "id": crew.id,
            "role": crew.role,
            "name": name,
            "phone": phone,
            "email": email,
            "callTime": format_time(rsvp.personalizedCallTime) if rsvp else "TBD",
            "location": rsvp.personalizedNotes if rsvp else "Set",
        })

    # Format as Department[]
    departments = []
    for dept_name, crew_list in departments_map.items():
        departments.append({
            "name": dept_name,
            "count": len(crew_list),
            "expanded": False,
            "crew": crew_list,
        })

    # Sort departments by a logical order
    dept_order = [
        "PRODUCTION", "CAMERA DEPT", "GRIP & ELECTRIC", "ART DEPT",
        "WARDROBE", "HAIR & MAKEUP", "SOUND", "LOCATIONS",
        "TRANSPORTATION", "CATERING", "POST PRODUCTION", "OTHER"
    ]
    departments.sort(key=lambda d: dept_order.index(d["name"]) if d["name"] in dept_order else 999)

    # Get client name from relation if available, otherwise fall back to legacy field
    client_name = project.client_relation.name if project.client_relation else project.client
    
    response_data = {
        "project": {
            "id": project.id,
            "jobName": project.jobName,
            "jobNumber": project.jobNumber,
            "client": client_name,
            "agency": project.agency,
        },
        "callSheets": [
            {
                "id": cs.id,
                "dayNumber": cs.dayNumber,
                "shootDate": cs.shootDate.isoformat() if cs.shootDate else None,
                "generalCrewCall": format_time(cs.generalCrewCall),
                "weather": {
                    "high": cs.weatherHigh,
                    "low": cs.weatherLow,
                    "summary": cs.weatherSummary,
                    "sunrise": cs.sunrise,
                    "sunset": cs.sunset,
                },
                "hospital": {
                    "name": cs.nearestHospital,
                    "address": cs.hospitalAddress,
                },
            }
            for cs in call_sheets
        ],
        "locations": [
            {
                "id": loc.id,
                "name": loc.name,
                "address": loc.address,
                "city": loc.city,
                "state": loc.state,
                "mapLink": loc.mapLink,
                "parkingNotes": loc.parkingNotes,
            }
            for loc in locations
        ],
        "departments": departments,
    }
    
    return response_data


async def update_crew_rsvp(
    db: AsyncSession,
    crew_id: str,
    call_time: Optional[str] = None,
    location: Optional[str] = None,
    call_sheet_id: Optional[str] = None
) -> bool:
    """
    Update a crew member's call time or location.

    If call_sheet_id is provided, updates the specific day's RSVP.
    Otherwise, updates the first available RSVP.
    """
    query = select(CallSheetRsvp).where(CallSheetRsvp.projectCrewId == crew_id)
    if call_sheet_id:
        query = query.where(CallSheetRsvp.callSheetId == call_sheet_id)

    result = await db.execute(query)
    rsvp = result.scalar_one_or_none()

    if not rsvp:
        return False

    if call_time is not None:
        rsvp.personalizedCallTime = parse_time(call_time)
    if location is not None:
        rsvp.personalizedNotes = location

    rsvp.updatedAt = datetime.utcnow()

    await db.commit()
    return True


async def update_call_sheet(
    db: AsyncSession,
    call_sheet_id: str,
    day_name: Optional[str] = None,
    shoot_date: Optional[str] = None,
    general_crew_call: Optional[str] = None,
    hospital_name: Optional[str] = None,
    hospital_address: Optional[str] = None
) -> bool:
    """
    Update call sheet fields.
    
    Args:
        call_sheet_id: ID of the call sheet to update
        day_name: Optional new day name (not stored directly, but can be used for notes)
        shoot_date: Optional new shoot date (YYYY-MM-DD format)
        general_crew_call: Optional new general crew call time (e.g., "7:45 AM")
        hospital_name: Optional new hospital name
        hospital_address: Optional new hospital address
    """
    result = await db.execute(
        select(CallSheet).where(CallSheet.id == call_sheet_id)
    )
    call_sheet = result.scalar_one_or_none()
    
    if not call_sheet:
        return False
    
    if shoot_date is not None:
        call_sheet.shootDate = parse_date(shoot_date) or call_sheet.shootDate
    
    if general_crew_call is not None:
        call_sheet.generalCrewCall = parse_time(general_crew_call, call_sheet.shootDate)
    
    if hospital_name is not None:
        call_sheet.nearestHospital = hospital_name
    
    if hospital_address is not None:
        call_sheet.hospitalAddress = hospital_address
    
    call_sheet.updatedAt = datetime.utcnow()
    
    await db.commit()
    return True


async def update_project(
    db: AsyncSession,
    project_id: str,
    job_name: Optional[str] = None,
    client: Optional[str] = None,
    agency: Optional[str] = None
) -> bool:
    """
    Update project fields.
    
    Args:
        project_id: ID of the project to update
        job_name: Optional new job name
        client: Optional new client name
        agency: Optional new agency name
    """
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()
    
    if not project:
        return False
    
    if job_name is not None:
        project.jobName = job_name
    
    if client is not None:
        project.client = client
    
    if agency is not None:
        project.agency = agency
    
    project.updatedAt = datetime.utcnow()
    
    await db.commit()
    return True


async def update_location(
    db: AsyncSession,
    location_id: str,
    address: Optional[str] = None,
    name: Optional[str] = None
) -> bool:
    """
    Update location fields.
    
    Args:
        location_id: ID of the location to update
        address: Optional new address
        name: Optional new location name
    """
    result = await db.execute(
        select(Location).where(Location.id == location_id)
    )
    location = result.scalar_one_or_none()
    
    if not location:
        return False
    
    if address is not None:
        location.address = address
        # Re-geocode the address if we have Google Maps API key
        from agents.enrichment import get_location_coordinates
        coords = get_location_coordinates(address)
        if coords:
            location.latitude = coords['lat']
            location.longitude = coords['lng']
            location.mapLink = f"https://www.google.com/maps/search/?api=1&query={coords['lat']},{coords['lng']}"
    
    if name is not None:
        location.name = name
    
    # Note: updatedAt is handled by SQLAlchemy's onupdate
    
    await db.commit()
    return True


async def search_crew_members(
    db: AsyncSession,
    query: str = "",
    department: Optional[str] = None,
    organization_id: Optional[str] = None,
    limit: int = 20
) -> list[dict]:
    """
    Search crew members from the master database.
    Used by the AddCrewDropdown component.
    """
    from sqlalchemy import or_

    from api.database import CrewMember

    stmt = select(CrewMember)

    if organization_id:
        stmt = stmt.where(CrewMember.organizationId == organization_id)

    if query:
        search_term = f"%{query}%"
        stmt = stmt.where(
            or_(
                CrewMember.firstName.ilike(search_term),
                CrewMember.lastName.ilike(search_term),
                CrewMember.primaryRole.ilike(search_term),
            )
        )

    if department:
        stmt = stmt.where(CrewMember.department == normalize_department(department))

    stmt = stmt.limit(limit)

    result = await db.execute(stmt)
    crew_members = result.scalars().all()

    return [
        {
            "id": cm.id,
            "name": f"{cm.firstName} {cm.lastName}",
            "role": cm.primaryRole or "Crew",
            "phone": cm.phone,
            "email": cm.email,
            "department": format_department_name(cm.department) if cm.department else None,
        }
        for cm in crew_members
    ]
