# Epitome Production Workbook Generator

An AI-powered production management system that generates professional, multi-tab Excel workbooks for film and video production. The system uses a two-part architecture: an LLM extraction agent that converts natural language requests into structured data, and a robust Excel generation engine that renders pixel-perfect production documents.

## Overview

This solution replaces manual Excel work with an automated workflow that creates:
- **Crew Lists** with department groupings
- **Daily Call Sheets** (dynamically generated per shoot day)
- **Production Schedules**
- **Location Information Sheets**
- **Purchase Order (PO) Logs**

## Architecture

### 1. Extraction Agent (`agents/prompts.py`)
Contains the system prompt used by an LLM (like Claude) to extract structured JSON from natural language requests. The prompt handles:
- Parsing user requests (e.g., "Create call sheets for a 3-day Nike shoot starting Monday")
- Processing attached files (crew lists, schedules)
- Generating standardized JSON with sensible defaults for missing data
- Calculating dates relative to "today" (e.g., "next Monday")

### 2. Generation Engine (`agents/production_workbook_generator.py`)
A Python class that takes the extracted JSON and generates a professionally formatted Excel workbook using `xlsxwriter`. Features:
- **Dynamic day generation**: Automatically creates call sheets for each scheduled day
- **Fallback logic**: Pre-populates standard crew roles when no data is provided
- **Brand-consistent formatting**: Applies Epitome's visual style (dark headers, borders, etc.)
- **Multi-tab output**: Organizes information across logical worksheets

## Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

## Usage

### Quick Test
```bash
# Run the test script (generates a sample workbook)
python agents/production_workbook_generator.py
```

This will create `Epitome_Production_Workbook.xlsx` with sample data for a 3-day Nike campaign.

### Programmatic Usage

```python
from agents import EpitomeWorkbookGenerator, EPITOME_EXTRACTION_SYSTEM_PROMPT

# Example: Your extracted data (from LLM or manual input)
production_data = {
    "production_info": {
        "job_name": "Nike Campaign - Summer 26",
        "client": "Nike",
        "job_number": "EP-NIKE-001",
        "production_company": "Epitome"
    },
    "logistics": {
        "locations": [
            {"name": "SoFi Stadium", "address": "1001 Stadium Dr, Inglewood, CA", "parking": "Lot C"}
        ],
        "weather": {"high": "75F", "low": "60F"},
        "hospital": {"name": "Centinela Hospital", "address": "555 E Hardy St"}
    },
    "schedule_days": [
        {"day_number": 1, "date": "2026-01-20", "crew_call": "07:00 AM", "talent_call": "09:00 AM"}
    ],
    "crew_list": []  # Empty = uses default template roles
}

# Generate the workbook
generator = EpitomeWorkbookGenerator(data=production_data, output_filename="my_production.xlsx")
output_path = generator.generate()
print(f"Workbook created: {output_path}")
```

### Integration with LLM

To use the extraction prompt with an LLM:

```python
from agents import EPITOME_EXTRACTION_SYSTEM_PROMPT
import anthropic  # or your LLM library

client = anthropic.Anthropic(api_key="your-key")

user_prompt = "Create call sheets for a 3-day shoot starting next Monday for Nike at SoFi Stadium"

response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    system=EPITOME_EXTRACTION_SYSTEM_PROMPT,
    messages=[{"role": "user", "content": user_prompt}],
    max_tokens=2000
)

# Parse the JSON response
import json
extracted_data = json.loads(response.content[0].text)

# Generate workbook
generator = EpitomeWorkbookGenerator(data=extracted_data)
generator.generate()
```

## Output Structure

The generated Excel workbook contains the following sheets:

1. **Crew List**: Organized by department with contact information and rates
2. **Call Sheet - Day N**: One sheet per shoot day with logistics, crew calls, and times
3. **Schedule**: Detailed timeline of the shoot day activities
4. **Locations**: Contact information, addresses, and parking for all locations
5. **PO Log**: Purchase order tracking with vendor and budget information

## Key Features

### Dynamic Days
If your data specifies 3 days, the generator creates:
- Call Sheet - Day 1
- Call Sheet - Day 2
- Call Sheet - Day 3

### Fallback Logic
When `crew_list` is empty, the system automatically populates standard roles:
- **Production**: Executive Producer, Producer, Prod. Supervisor, PA
- **Camera**: Director of Photography, 1st AC, 2nd AC, DIT
- **Audio**: Sound Mixer, Boom Op
- **G&E**: Gaffer, Key Grip, Best Boy
- **Talent**: Talent 1, Talent 2

This ensures users never receive completely blank call sheets.

### Brand Formatting
- Dark headers (#111827) with white text
- Light section headers (#F3F4F6)
- Consistent borders and cell alignment
- Department groupings with gray dividers (#D1D5DB)

## Dependencies

- `xlsxwriter>=3.1.9` - Excel file generation
- `pandas>=2.0.0` (optional) - Enhanced CSV/data processing
- `python-dateutil>=2.8.2` (optional) - Date handling

## Project Structure

```
epitome/
├── agents/
│   ├── __init__.py                          # Package exports
│   ├── prompts.py                           # LLM extraction prompt
│   └── production_workbook_generator.py     # Excel generation engine
├── requirements.txt                          # Python dependencies
└── README.md                                 # This file
```

## Development

The code is designed to be:
- **Extensible**: Easily add new sheet types or modify formatting
- **Maintainable**: Clear separation between extraction logic and generation
- **Testable**: Run standalone tests without LLM integration

## Future Enhancements

- CSV/Excel file parsing for crew lists
- Date calculation utilities (e.g., "next Monday" → actual date)
- Custom template support
- PDF export option
- Web UI for non-technical users

## License

[Your License Here]

## Contact

For issues or questions, please open an issue on GitHub.
