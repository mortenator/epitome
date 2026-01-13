"""
Epitome Production Workbook Generator
Generates multi-tab Excel workbooks for production management using xlsxwriter.
"""

import xlsxwriter
import json
from datetime import datetime, timedelta


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
        """Orchestrates the generation of all sheets."""
        self._write_crew_list()
        self._write_schedule()

        # Dynamic Call Sheets (One per scheduled day)
        days = self.data.get('schedule_days', [{'day_number': 1, 'date': 'TBD'}])
        for day in days:
            self._write_call_sheet(day)

        self._write_locations()
        self._write_po_log()

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
# TOOL ENTRY POINT
# ==========================================

def run_tool(prompt: str, attached_file_content: str = None):
    """
    Simulates the Tool execution pipeline.
    1. In a real scenario, an Agent would use the 'EPITOME_EXTRACTION_SYSTEM_PROMPT'
       to parse the 'prompt' and 'attached_file_content' into the 'json_data' dict below.
    2. We then pass that JSON to the Generator.
    """

    # --- MOCK DATA EXTRACTION (Simulating LLM Output) ---
    # This dictionary mimics what the LLM would return based on a prompt like:
    # "Create a call sheet for a 3 day shoot for Nike starting Jan 20th"

    mock_llm_output = {
        "production_info": {
            "job_name": "Nike Campaign - Summer 26",
            "client": "Nike",
            "job_number": "EP-NIKE-001",
            "production_company": "Epitome"
        },
        "logistics": {
            "locations": [
                {"name": "SoFi Stadium", "address": "1001 Stadium Dr, Inglewood, CA", "parking": "Lot C"},
                {"name": "Venice Beach", "address": "Ocean Front Walk", "parking": "Public Lot 4"}
            ],
            "weather": {"high": "75F", "low": "60F", "sunrise": "6:45 AM", "sunset": "5:30 PM"},
            "hospital": {"name": "Centinela Hospital", "address": "555 E Hardy St, Inglewood"}
        },
        "schedule_days": [
            {"day_number": 1, "date": "2026-01-20", "crew_call": "07:00 AM", "talent_call": "09:00 AM"},
            {"day_number": 2, "date": "2026-01-21", "crew_call": "06:30 AM", "talent_call": "08:00 AM"},
            {"day_number": 3, "date": "2026-01-22", "crew_call": "08:00 AM", "talent_call": "10:00 AM"}
        ],
        "crew_list": [] # Empty, forcing the generator to use default template roles
    }

    # If the user uploaded a file (e.g., Crew List csv), we would parse it here
    # and populate 'mock_llm_output["crew_list"]' with the actual data.
    if attached_file_content:
        # Simple Logic: parsing a CSV string into the dict
        # In production this would be handled by pandas.read_csv
        pass

    # --- GENERATION ---
    output_file = "Epitome_Production_Workbook.xlsx"
    generator = EpitomeWorkbookGenerator(data=mock_llm_output, output_filename=output_file)
    final_path = generator.generate()

    return f"Successfully generated production workbook at: {final_path}"


if __name__ == "__main__":
    # Test Run
    print(run_tool("Create call sheets for our 3 day shoot on monday"))
