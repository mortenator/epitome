# Epitome

**Automated Production Workbook Generator**

Epitome is a vertical SaaS platform designed to automate physical production workflows (film, TV, advertising). Currently in Phase 1 ("The Utility"), focusing on automating the creation of production call sheets.

## 🎯 Problem

Producers spend approximately **3.5 hours per day** manually formatting Excel files and PDFs for production workflows. This time-consuming process involves:
- Manually entering crew information
- Formatting call sheets for multiple shoot days
- Ensuring consistent branding and layout
- Managing logistics data (locations, weather, schedules)

## ✨ Solution

Epitome acts as an **"Automated Executive Producer"** that:
- Ingests natural language prompts (e.g., "3 day shoot for Nike")
- Accepts raw files (Crew Lists in CSV/Excel format)
- Instantly generates production-ready Excel workbooks with proper formatting and branding

## 🏗️ Architecture

The system follows a linear **Extraction → Transformation → Generation** pipeline:

```
User Input (Prompt + CSV) 
  → Extraction Agent (LLM Parsing)
  → Structured JSON
  → Generator Engine (xlsxwriter)
  → Final Workbook.xlsx
```

### Components

1. **Input Layer**: Natural language prompts and optional file attachments (Crew Lists, Schedules)
2. **Extraction Agent** (`prompts.py`): LLM-powered parser that normalizes inputs into structured JSON
3. **Generator Engine** (`production_workbook_generator.py`): Python script using xlsxwriter to create formatted workbooks

## 📊 Workbook Structure

The generated `Epitome_Production_Workbook.xlsx` includes:

- **Crew List**: Master contact database grouped by department
- **Call Sheet - Day [X]**: Dynamic daily logistics sheets (1-10 days based on schedule)
- **Schedule**: Timeline of events and activities
- **Locations**: Detailed logistics information with parking and hospital details
- **PO Log**: Financial tracking for vendors and purchases

## 🎨 Features

- **Dynamic Tab Generation**: Automatically creates call sheet tabs based on shoot schedule
- **Fallback Templates**: Pre-populates with "Skeleton Crew" roles if no crew data provided
- **TBD Safety Net**: Gracefully handles incomplete data with "TBD" defaults
- **Role Normalization**: Groups crew by industry-standard departments
- **Branded Formatting**: Consistent Epitome styling (Dark Mode headers, grid layouts)

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- Required packages: `xlsxwriter`, `anthropic` (or your LLM provider)

### Installation

```bash
# Clone the repository
git clone https://github.com/mortenator/epitome.git
cd epitome

# Install dependencies
pip install -r requirements.txt
```

### Usage

```python
from production_workbook_generator import generate_workbook

# Example: Generate workbook from structured JSON
data = {
    "production_info": {
        "job_name": "Nike Commercial",
        "client": "Nike",
        "job_number": "NK-2024-001"
    },
    "schedule_days": [
        {
            "day_number": 1,
            "date": "2024-01-15",
            "crew_call": "07:00 AM",
            "talent_call": "09:00 AM"
        }
    ],
    "crew_list": [...]
}

generate_workbook(data, "Epitome_Production_Workbook.xlsx")
```

## 📁 Project Structure

```
epitome/
├── production_workbook_generator.py  # Main generator engine
├── prompts.py                        # LLM extraction agent
├── claude.md                         # Best practices for working with Claude
└── README.md                         # This file
```

## 📋 Data Schema

The system expects JSON data following this structure:

```json
{
  "production_info": {
    "job_name": "String",
    "client": "String",
    "job_number": "String"
  },
  "logistics": {
    "locations": [{"name": "String", "address": "String", "parking": "String"}],
    "hospital": {"name": "String", "address": "String"},
    "weather": {"high": "String", "low": "String", "sunrise": "String", "sunset": "String"}
  },
  "schedule_days": [
    {
      "day_number": 1,
      "date": "YYYY-MM-DD",
      "crew_call": "07:00 AM",
      "talent_call": "09:00 AM"
    }
  ],
  "crew_list": [
    {
      "department": "Camera",
      "role": "Director of Photography",
      "name": "String",
      "email": "String",
      "rate": "String"
    }
  ]
}
```

## 🔄 Development Status

**Current**: `production_workbook_generator.py` is fully functional with mock data.

**Roadmap**:
- [ ] Connect `prompts.py` to live LLM endpoint
- [ ] Implement CSV parsing for crew list population
- [ ] Add distribution layer (Email/SMS functionality)
- [ ] Web interface for user interactions
- [ ] Integration with production management tools

## 📚 Documentation

- See [`claude.md`](./claude.md) for best practices when working with Claude on this codebase
- Project-specific context and architecture details are documented in `claude.md`

## 🤝 Contributing

This is currently a private project. For questions or collaboration, please contact the repository owner.

## 📄 License

[Add license information here]

---

**Built for producers, by producers.** Save time, reduce errors, focus on creativity.
