"""
Epitome Production Workbook Generator
Generates multi-tab Excel workbooks for production management using xlsxwriter.
"""

import xlsxwriter
import json
import os
import re
from datetime import datetime
from google import genai
from .prompts import EPITOME_EXTRACTION_SYSTEM_PROMPT


class EpitomeWorkbookGenerator:
    """
    Generates a production workbook based on the Epitome template.
    Includes: Crew List, Daily Call Sheets, Schedule, Locations, and PO Log.
    """

    def __init__(self, data: dict, output_filename: str = "production_workbook.xlsx"):
        self.data = data
        self.output_filename = output_filename
        self.workbook = xlsxwriter.Workbook(self.output_filename)
        self.formats = {}

        # Define standard Layout/Styles
        self._init_formats()

    def _init_formats(self):
        """Initialize Excel formats for consistent branding."""
        # Main Headers
        self.formats['header_dark'] = self.workbook.add_format({
            'bold': True, 'font_color': 'white', 'bg_color': '#111827',
            'border': 1, 'align': 'center', 'valign': 'vcenter', 'font_size': 12
        })
        self.formats['header_light'] = self.workbook.add_format({
            'bold': True, 'font_color': 'black', 'bg_color': '#F3F4F6',
            'border': 1, 'align': 'left', 'valign': 'vcenter'
        })

        # Data Cells
        self.formats['cell_normal'] = self.workbook.add_format({'border': 1, 'valign': 'vcenter'})
        self.formats['cell_center'] = self.workbook.add_format({'border': 1, 'align': 'center', 'valign': 'vcenter'})
        self.formats['cell_bold'] = self.workbook.add_format({'border': 1, 'bold': True, 'valign': 'vcenter'})

        # Section Dividers (Department Headers)
        self.formats['dept_header'] = self.workbook.add_format({
            'bold': True, 'bg_color': '#D1D5DB', 'border': 1, 'align': 'left'
        })

        # Title
        self.formats['title_large'] = self.workbook.add_format({
            'bold': True, 'font_size': 18, 'align': 'left'
        })

    def generate(self):
        """Orchestrates the generation of all sheets matching sample workbook structure."""
        # Core sheets
        self._write_crew_list()
        self._write_schedule()

        # Dynamic Call Sheets (One per scheduled day)
        days = self.data.get('schedule_days', [{'day_number': 1, 'date': 'TBD'}])
        for day in days:
            self._write_call_sheet(day)

        # Additional production sheets
        self._write_po_log()
        self._write_credits_list()
        self._write_locations()
        self._write_key_crew()
        self._write_overages()
        self._write_transpo()
        self._write_pick_up_list()
        self._write_travel()
        self._write_travel_memo()
        self._write_wrap_notes()

        self.workbook.close()
        return self.output_filename

    # ==========================================
    # SHEET 1: CREW LIST
    # ==========================================
    def _write_crew_list(self):
        ws = self.workbook.add_worksheet('Crew List')
        ws.set_column('A:A', 25) # Dept/Role
        ws.set_column('B:B', 25) # Name
        ws.set_column('C:C', 15) # Phone
        ws.set_column('D:D', 25) # Email
        ws.set_column('E:E', 15) # Rate

        # Header Info
        prod_info = self.data.get('production_info', {})
        ws.write('A1', f"JOB: {prod_info.get('job_name', 'TBD')}", self.formats['title_large'])
        ws.write('A2', f"CLIENT: {prod_info.get('client', 'TBD')}")

        # Table Headers
        headers = ['Role', 'Name', 'Phone', 'Email', 'Rate', 'Notes']
        for col, h in enumerate(headers):
            ws.write(3, col, h, self.formats['header_dark'])

        # Write Crew Data
        row = 4
        current_dept = None

        # Sort crew by department for cleaner grouping if possible, otherwise use input order
        crew = self.data.get('crew_list', [])

        # Default buckets if empty
        if not crew:
            departments = ['Production', 'Camera', 'G&E', 'Art', 'Sound', 'H/MU', 'Wardrobe', 'PA']
            for dept in departments:
                ws.merge_range(row, 0, row, 5, dept.upper(), self.formats['dept_header'])
                row += 1
                for _ in range(3): # Add a few blank lines per dept
                    ws.write_blank(row, 0, None, self.formats['cell_normal'])
                    row += 1
            return

        # If we have data
        for person in crew:
            dept = person.get('department', 'General')
            if dept != current_dept:
                ws.merge_range(row, 0, row, 5, dept.upper(), self.formats['dept_header'])
                row += 1
                current_dept = dept

            ws.write(row, 0, person.get('role', ''), self.formats['cell_bold'])
            ws.write(row, 1, person.get('name', ''), self.formats['cell_normal'])
            ws.write(row, 2, person.get('phone', ''), self.formats['cell_normal'])
            ws.write(row, 3, person.get('email', ''), self.formats['cell_normal'])
            ws.write(row, 4, person.get('rate', ''), self.formats['cell_normal'])
            ws.write(row, 5, person.get('notes', ''), self.formats['cell_normal'])
            row += 1

    # ==========================================
    # SHEET 2: CALL SHEET (Dynamic per Day)
    # ==========================================
    def _write_call_sheet(self, day_info):
        day_num = day_info.get('day_number', 1)
        ws_name = f"Call Sheet - Day {day_num}"
        ws = self.workbook.add_worksheet(ws_name)

        # Column Setup
        ws.set_column('A:F', 20)

        # --- HEADER BLOCK (Grid Layout) ---
        prod_info = self.data.get('production_info', {})
        logistics = self.data.get('logistics', {})

        # Row 1-2: Titles
        ws.merge_range('A1:B2', "EPITOME", self.formats['title_large'])
        ws.merge_range('C1:D1', f"CALL SHEET - DAY {day_num}", self.formats['header_dark'])
        ws.merge_range('C2:D2', day_info.get('date', 'TBD'), self.formats['cell_center'])

        # Row 4-8: Logistics Grid
        # Left Block: Production
        ws.write('A4', "PRODUCTION CO:", self.formats['header_light'])
        ws.write('B4', prod_info.get('production_company', 'Epitome'), self.formats['cell_normal'])
        ws.write('A5', "JOB NAME:", self.formats['header_light'])
        ws.write('B5', prod_info.get('job_name', 'TBD'), self.formats['cell_normal'])

        # Middle Block: Location
        locs = logistics.get('locations', [])
        main_loc = locs[0] if locs else {}
        ws.write('C4', "LOCATION:", self.formats['header_light'])
        ws.write('C5', main_loc.get('name', 'TBD'), self.formats['cell_normal'])
        ws.write('C6', main_loc.get('address', ''), self.formats['cell_normal'])

        # Right Block: Times & Weather
        ws.write('E4', "CREW CALL:", self.formats['header_light'])
        ws.write('F4', day_info.get('crew_call', 'TBD'), self.formats['cell_bold'])
        ws.write('E5', "WEATHER:", self.formats['header_light'])
        weather = logistics.get('weather', {})
        ws.write('F5', f"H: {weather.get('high','-')} L: {weather.get('low','-')}", self.formats['cell_normal'])

        ws.write('A8', "NEAREST HOSPITAL:", self.formats['header_light'])
        hosp = logistics.get('hospital', {})
        ws.write('B8', f"{hosp.get('name','TBD')} - {hosp.get('address','')}", self.formats['cell_normal'])

        # --- CREW GRID ---
        start_row = 11
        headers = ['TITLE', 'NAME', 'PHONE', 'EMAIL', 'CALL TIME', 'LOCATION']
        for col, h in enumerate(headers):
            ws.write(start_row, col, h, self.formats['header_dark'])

        row = start_row + 1

        # If we have specific crew for this day, filter them. Otherwise use master list.
        crew = self.data.get('crew_list', [])

        # Pre-populate specific roles if list is empty (The "Epitome" requirement)
        if not crew:
            default_roles = [
                ('PRODUCTION', ['Executive Producer', 'Producer', 'Prod. Supervisor', 'PA - Set']),
                ('CAMERA', ['Director of Photography', '1st AC', '2nd AC', 'DIT']),
                ('AUDIO', ['Sound Mixer', 'Boom Op']),
                ('G&E', ['Gaffer', 'Key Grip', 'Best Boy']),
                ('TALENT', ['Talent 1', 'Talent 2'])
            ]

            for dept, roles in default_roles:
                ws.merge_range(row, 0, row, 5, dept, self.formats['dept_header'])
                row += 1
                for role in roles:
                    ws.write(row, 0, role, self.formats['cell_bold'])
                    ws.write_blank(row, 1, None, self.formats['cell_normal']) # Name
                    ws.write_blank(row, 2, None, self.formats['cell_normal']) # Phone
                    ws.write_blank(row, 3, None, self.formats['cell_normal']) # Email

                    # Fill Call time based on day_info
                    call_time = day_info.get('crew_call', 'TBD')
                    if dept == 'TALENT': call_time = day_info.get('talent_call', 'TBD')

                    ws.write(row, 4, call_time, self.formats['cell_center'])
                    ws.write(row, 5, "Set", self.formats['cell_center'])
                    row += 1
        else:
            # Render actual crew list
            current_dept = None
            for person in crew:
                dept = person.get('department', 'Crew')
                if dept != current_dept:
                    ws.merge_range(row, 0, row, 5, dept.upper(), self.formats['dept_header'])
                    row += 1
                    current_dept = dept

                ws.write(row, 0, person.get('role', ''), self.formats['cell_bold'])
                ws.write(row, 1, person.get('name', ''), self.formats['cell_normal'])
                ws.write(row, 2, person.get('phone', ''), self.formats['cell_normal'])
                ws.write(row, 3, person.get('email', ''), self.formats['cell_normal'])
                ws.write(row, 4, day_info.get('crew_call', '07:00 AM'), self.formats['cell_center'])
                ws.write(row, 5, "Set", self.formats['cell_center'])
                row += 1


    # ==========================================
    # SHEET 3: SCHEDULE
    # ==========================================
    def _write_schedule(self):
        ws = self.workbook.add_worksheet('Schedule')
        ws.set_column('A:A', 15)  # Time
        ws.set_column('B:B', 40)  # Activity
        ws.set_column('C:C', 30)  # Notes

        ws.write('A1', "SHOOT SCHEDULE", self.formats['title_large'])

        headers = ['TIME', 'ACTIVITY / SCENE', 'NOTES']
        for col, h in enumerate(headers):
            ws.write(3, col, h, self.formats['header_dark'])

        # Get schedule from data, or use default template
        schedule = self.data.get('schedule', [])

        if not schedule:
            # Default schedule template when none provided
            schedule = [
                {"time": "07:00 AM", "activity": "CREW CALL / BREAKFAST", "notes": "Catering Tent"},
                {"time": "08:00 AM", "activity": "Safety Meeting", "notes": "All Hands"},
                {"time": "08:15 AM", "activity": "Shoot Scene 1", "notes": "TBD"},
                {"time": "01:00 PM", "activity": "LUNCH", "notes": "30 Mins"},
                {"time": "01:30 PM", "activity": "Shoot Scene 2", "notes": "TBD"},
                {"time": "07:00 PM", "activity": "WRAP", "notes": "Estimated"}
            ]

        row = 4
        for item in schedule:
            ws.write(row, 0, item.get('time', ''), self.formats['cell_center'])
            ws.write(row, 1, item.get('activity', ''), self.formats['cell_normal'])
            ws.write(row, 2, item.get('notes', ''), self.formats['cell_normal'])
            row += 1

    # ==========================================
    # SHEET 4: LOCATIONS
    # ==========================================
    def _write_locations(self):
        ws = self.workbook.add_worksheet('Locations')
        ws.set_column('A:F', 20)

        headers = ['Location Name', 'Address', 'Contact Name', 'Phone', 'Parking Notes', 'Nearest Hospital']
        for col, h in enumerate(headers):
            ws.write(0, col, h, self.formats['header_dark'])

        locs = self.data.get('logistics', {}).get('locations', [])
        hosp = self.data.get('logistics', {}).get('hospital', {})
        hosp_info = f"{hosp.get('name', 'TBD')} - {hosp.get('address', '')}" if hosp else "TBD"

        row = 1
        for loc in locs:
            ws.write(row, 0, loc.get('name', ''), self.formats['cell_bold'])
            ws.write(row, 1, loc.get('address', ''), self.formats['cell_normal'])
            ws.write(row, 2, loc.get('contact', ''), self.formats['cell_normal'])
            ws.write(row, 3, loc.get('phone', ''), self.formats['cell_normal'])
            ws.write(row, 4, loc.get('parking', ''), self.formats['cell_normal'])
            ws.write(row, 5, hosp_info, self.formats['cell_normal'])
            row += 1

    # ==========================================
    # SHEET 5: PO LOG
    # ==========================================
    def _write_po_log(self):
        ws = self.workbook.add_worksheet('PO Log')
        ws.set_column('A:H', 15)

        title = f"PO LOG - {self.data.get('production_info', {}).get('job_name', '')}"
        ws.merge_range('A1:H1', title, self.formats['title_large'])

        headers = ['PO #', 'Vendor', 'Description', 'Amount', 'Date', 'Pay Status', 'Notes', 'Budget Code']
        for col, h in enumerate(headers):
            ws.write(3, col, h, self.formats['header_dark'])

        # Add blank rows for entry
        for r in range(4, 20):
            for c in range(8):
                ws.write_blank(r, c, None, self.formats['cell_normal'])

    # ==========================================
    # SHEET 6: CREDITS LIST
    # ==========================================
    def _write_credits_list(self):
        ws = self.workbook.add_worksheet('Credits List')
        ws.set_column('A:A', 25)
        ws.set_column('B:B', 25)
        ws.set_column('C:C', 20)

        ws.write('A1', "CREDITS LIST", self.formats['header_dark'])

        headers = ['Production', 'Name', 'Instagram (@)']
        for col, h in enumerate(headers):
            ws.write(1, col, h, self.formats['dept_header'])

        # Standard production roles for credits
        roles = [
            'Director', 'Executive Producer', 'Producer', 'Production Manager',
            'Production Coordinator', '1st AD', '2nd AD', 'Director of Photography',
            'Camera Operator', '1st AC', 'Gaffer', 'Key Grip', 'HMU', 'Wardrobe Stylist',
            'Production Designer', 'Art Director', 'Editor', 'Colorist', 'Sound Mixer'
        ]

        row = 2
        for role in roles:
            ws.write(row, 0, role, self.formats['cell_bold'])
            ws.write_blank(row, 1, None, self.formats['cell_normal'])
            ws.write_blank(row, 2, None, self.formats['cell_normal'])
            row += 1

    # ==========================================
    # SHEET 7: KEY CREW
    # ==========================================
    def _write_key_crew(self):
        ws = self.workbook.add_worksheet('Key Crew')
        ws.set_column('A:A', 5)
        ws.set_column('B:B', 25)
        ws.set_column('C:C', 20)
        ws.set_column('D:D', 15)
        ws.set_column('E:E', 25)
        ws.set_column('F:I', 15)

        ws.merge_range('A1:I1', "Key Crew Options", self.formats['header_dark'])

        headers = ['#', 'Name', 'Website', 'Phone', 'Email', 'Rate/Fees', 'Holds', 'Agency', 'Agency Email']
        for col, h in enumerate(headers):
            ws.write(1, col, h, self.formats['dept_header'])

        # Key crew categories
        categories = [
            'Director of Photography', 'Gaffer', 'Key Grip', 'Production Designer',
            'HMU', 'Wardrobe Stylist', 'Editor', 'Colorist'
        ]

        row = 2
        for category in categories:
            ws.write(row, 0, category, self.formats['cell_bold'])
            ws.merge_range(row, 1, row, 8, '', self.formats['cell_normal'])
            row += 1
            # Add 3 option rows per category
            for i in range(1, 4):
                ws.write(row, 0, f'{i}.0', self.formats['cell_center'])
                for c in range(1, 9):
                    ws.write_blank(row, c, None, self.formats['cell_normal'])
                row += 1

    # ==========================================
    # SHEET 8: OVERAGES
    # ==========================================
    def _write_overages(self):
        ws = self.workbook.add_worksheet('Overages')
        ws.set_column('A:L', 15)

        ws.merge_range('A1:L1', "OVERAGES TRACKER", self.formats['header_dark'])

        headers = ['Department', 'Description', 'Budgeted', 'Actual', 'Overage', 'Notes']
        for col, h in enumerate(headers):
            ws.write(2, col, h, self.formats['dept_header'])

        # Add blank rows for entry
        for r in range(3, 20):
            for c in range(6):
                ws.write_blank(r, c, None, self.formats['cell_normal'])

    # ==========================================
    # SHEET 9: TRANSPO
    # ==========================================
    def _write_transpo(self):
        ws = self.workbook.add_worksheet('Transpo')
        ws.set_column('A:A', 5)
        ws.set_column('B:B', 20)
        ws.set_column('C:C', 20)
        ws.set_column('D:K', 12)

        ws.merge_range('A1:K1', "Transportation & Rental Grid", self.formats['header_dark'])

        # Day headers row
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        ws.write(1, 5, 'Day of Week', self.formats['dept_header'])
        for i, day in enumerate(days):
            ws.write(1, 6 + i, day, self.formats['dept_header'])

        ws.write(2, 5, 'Date', self.formats['cell_bold'])
        ws.write(3, 5, 'Prep/Shoot/Wrap', self.formats['cell_bold'])

        # Column headers
        headers = ['#', 'Vehicle Type', 'Vendor', 'Days Used', 'Price', 'Driver']
        for col, h in enumerate(headers):
            ws.write(4, col, h, self.formats['dept_header'])

        # Add blank rows for vehicles
        for r in range(5, 15):
            ws.write(r, 0, f'{r - 4}.0', self.formats['cell_center'])
            for c in range(1, 11):
                ws.write_blank(r, c, None, self.formats['cell_normal'])

    # ==========================================
    # SHEET 10: PICK UP LIST
    # ==========================================
    def _write_pick_up_list(self):
        ws = self.workbook.add_worksheet('Pick Up List')
        ws.set_column('A:A', 5)
        ws.set_column('B:B', 25)
        ws.set_column('C:C', 30)
        ws.set_column('D:G', 15)

        ws.merge_range('A1:G1', "Pick Up List", self.formats['header_dark'])

        headers = ['#', 'Name', 'Address', 'Phone', 'Date', 'Time', 'What']
        for col, h in enumerate(headers):
            ws.write(1, col, h, self.formats['dept_header'])

        ws.write(2, 0, 'Driver:', self.formats['cell_bold'])
        ws.merge_range(2, 1, 2, 6, '', self.formats['cell_normal'])

        # Add blank rows for pickups
        for r in range(3, 15):
            ws.write(r, 0, f'{r - 2}.0', self.formats['cell_center'])
            for c in range(1, 7):
                ws.write_blank(r, c, None, self.formats['cell_normal'])

    # ==========================================
    # SHEET 11: TRAVEL
    # ==========================================
    def _write_travel(self):
        ws = self.workbook.add_worksheet('Travel')
        ws.set_column('A:A', 5)
        ws.set_column('B:B', 15)
        ws.set_column('C:C', 20)
        ws.set_column('D:N', 12)

        # Flights section
        ws.merge_range('A1:N1', "Flights", self.formats['header_dark'])

        # Sub-headers
        ws.merge_range('C2:E2', "Booking Info", self.formats['dept_header'])
        ws.merge_range('F2:I2', "Outbound", self.formats['dept_header'])
        ws.merge_range('J2:M2', "Inbound", self.formats['dept_header'])

        headers = ['#', 'Role', 'Name', 'Birthday', 'Frequent Flyer #',
                   'Date', 'Airline', 'Departure', 'Arrival',
                   'Date', 'Airline', 'Departure', 'Arrival', 'Notes']
        for col, h in enumerate(headers):
            ws.write(2, col, h, self.formats['cell_bold'])

        # Standard roles
        roles = ['EP', 'Director', 'Producer', 'DP', 'Talent 1', 'Talent 2']
        for i, role in enumerate(roles):
            row = 3 + i
            ws.write(row, 0, f'{i + 1}.0', self.formats['cell_center'])
            ws.write(row, 1, role, self.formats['cell_normal'])
            for c in range(2, 14):
                ws.write_blank(row, c, None, self.formats['cell_normal'])

        # Lodging section
        lodging_row = 10
        ws.merge_range(f'A{lodging_row}:N{lodging_row}', "Lodging", self.formats['header_dark'])

        lodging_headers = ['#', 'Role', 'Name', 'Hotel', 'Check-In', 'Check-Out', 'Confirmation #', 'Notes']
        for col, h in enumerate(lodging_headers):
            ws.write(lodging_row, col, h, self.formats['cell_bold'])

        for r in range(lodging_row + 1, lodging_row + 8):
            ws.write(r, 0, f'{r - lodging_row}.0', self.formats['cell_center'])
            for c in range(1, 8):
                ws.write_blank(r, c, None, self.formats['cell_normal'])

    # ==========================================
    # SHEET 12: TRAVEL MEMO
    # ==========================================
    def _write_travel_memo(self):
        ws = self.workbook.add_worksheet('Travel Memo')
        ws.set_column('A:Z', 12)

        prod_info = self.data.get('production_info', {})
        client = prod_info.get('client', 'CLIENT')

        ws.merge_range('A1:J1', f"{client} - WEEKLY SCHEDULE", self.formats['header_dark'])

        # Section headers
        ws.write('A3', "Shoot", self.formats['dept_header'])
        ws.write('D3', "Hotel", self.formats['dept_header'])
        ws.write('G3', "Location", self.formats['dept_header'])

        # Add placeholder content
        days = self.data.get('schedule_days', [])
        row = 4
        for day in days:
            ws.write(row, 0, f"Day {day.get('day_number', '')}", self.formats['cell_bold'])
            ws.write(row, 1, day.get('date', 'TBD'), self.formats['cell_normal'])
            row += 1

    # ==========================================
    # SHEET 13: WRAP NOTES
    # ==========================================
    def _write_wrap_notes(self):
        ws = self.workbook.add_worksheet('Wrap Notes')
        ws.set_column('A:V', 15)

        prod_info = self.data.get('production_info', {})

        ws.merge_range('A1:V1', "WRAP REPORT", self.formats['header_dark'])

        # Header info
        ws.write('A3', "Job Name:", self.formats['cell_bold'])
        ws.write('B3', prod_info.get('job_name', 'TBD'), self.formats['cell_normal'])
        ws.write('C3', "Producer:", self.formats['cell_bold'])
        ws.write('D3', '', self.formats['cell_normal'])
        ws.write('E3', "UPM:", self.formats['cell_bold'])
        ws.write('F3', '', self.formats['cell_normal'])

        ws.write('A4', "Client:", self.formats['cell_bold'])
        ws.write('B4', prod_info.get('client', 'TBD'), self.formats['cell_normal'])
        ws.write('C4', "Wrap Date:", self.formats['cell_bold'])
        ws.write('D4', '', self.formats['cell_normal'])

        # Wrap notes sections
        sections = ['Equipment Returns', 'Outstanding Payments', 'Final Deliverables', 'Notes']
        row = 6
        for section in sections:
            ws.merge_range(row, 0, row, 5, section, self.formats['dept_header'])
            row += 1
            for _ in range(4):
                for c in range(6):
                    ws.write_blank(row, c, None, self.formats['cell_normal'])
                row += 1
            row += 1


# ==========================================
# TOOL ENTRY POINT
# ==========================================

def _extract_json_from_response(text: str) -> dict:
    """Extract JSON from LLM response, handling markdown code blocks."""
    # Try to find JSON in markdown code block
    json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
    if json_match:
        json_str = json_match.group(1)
    else:
        # Assume the entire response is JSON
        json_str = text.strip()

    return json.loads(json_str)


def _get_api_key() -> str:
    """Get Gemini API key from environment variables."""
    api_key = os.environ.get('GEMINI_API_KEY') or os.environ.get('GOOGLE_API_KEY')
    if not api_key:
        raise ValueError(
            "Missing API key. Set GEMINI_API_KEY or GOOGLE_API_KEY environment variable."
        )
    return api_key


def run_tool(prompt: str, attached_file_content: str = None) -> str:
    """
    Execute the Epitome production workbook generation pipeline.

    1. Uses Gemini LLM with EPITOME_EXTRACTION_SYSTEM_PROMPT to parse
       the user prompt and optional file content into structured JSON.
    2. Passes the extracted JSON to EpitomeWorkbookGenerator.
    3. Returns the path to the generated workbook.

    Args:
        prompt: Natural language request (e.g., "Create call sheets for a 5 day shoot for Google")
        attached_file_content: Optional CSV/text content of crew list or schedule

    Returns:
        Success message with path to generated workbook

    Raises:
        ValueError: If API key is missing
        Exception: If LLM call or JSON parsing fails
    """
    # Get API key and initialize client
    api_key = _get_api_key()
    client = genai.Client(api_key=api_key)

    # Build user message
    today = datetime.now().strftime("%Y-%m-%d")
    user_message = f"Today's date is {today}.\n\nUser request: {prompt}"

    if attached_file_content:
        user_message += f"\n\nAttached file content:\n{attached_file_content}"

    # Call Gemini for extraction
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[
            {"role": "user", "parts": [{"text": EPITOME_EXTRACTION_SYSTEM_PROMPT}]},
            {"role": "model", "parts": [{"text": "I understand. I will extract production data from user requests and return structured JSON following the schema you provided. I'm ready to process requests."}]},
            {"role": "user", "parts": [{"text": user_message}]}
        ]
    )

    # Extract JSON from response
    response_text = response.text
    extracted_data = _extract_json_from_response(response_text)

    # Generate workbook
    output_file = "Epitome_Production_Workbook.xlsx"
    generator = EpitomeWorkbookGenerator(data=extracted_data, output_filename=output_file)
    final_path = generator.generate()

    return f"Successfully generated production workbook at: {final_path}"


if __name__ == "__main__":
    # Test Run
    print(run_tool("Create call sheets for a 5 day shoot for Google starting next Monday"))
