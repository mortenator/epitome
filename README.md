# Epitome

**Automated Production Workbook Generator**

Epitome is a vertical SaaS platform designed to automate physical production workflows (film, TV, advertising). Currently in Phase 1 ("The Utility"), focusing on automating the creation of production call sheets.

## Problem

Producers spend approximately **3.5 hours per day** manually formatting Excel files and PDFs for production workflows. This time-consuming process involves:
- Manually entering crew information
- Formatting call sheets for multiple shoot days
- Ensuring consistent branding and layout
- Managing logistics data (locations, weather, schedules)
- Tracking RSVPs and crew confirmations

## Solution

Epitome acts as an **"Automated Executive Producer"** that:
- Ingests natural language prompts (e.g., "3 day shoot for Nike")
- Accepts raw files (Crew Lists in CSV/Excel format)
- Instantly generates production-ready Excel workbooks with proper formatting and branding
- Manages crew, locations, schedules, and budgets in a unified database

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Database** | PostgreSQL (Supabase) |
| **ORM** | Prisma |
| **Backend** | Python (FastAPI) |
| **AI/LLM** | Google Gemini |
| **Excel Generation** | xlsxwriter |
| **Frontend** | React + Vite (TypeScript) |
| **Deployment** | Vercel (uv package manager) |

## Architecture

The system follows a **Database-First** architecture with an **Extraction → Transformation → Generation** pipeline:

```
┌─────────────────────────────────────────────────────────────────┐
│                         SUPABASE                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Organizations│  │   Projects   │  │  Call Sheets │          │
│  │    Users     │  │   Budgets    │  │  Schedules   │          │
│  │    Crew      │  │   Vendors    │  │   RSVPs      │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      PRISMA ORM                                 │
│              Type-safe database access layer                    │
└─────────────────────────────────────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│   FastAPI        │ │  LLM Extraction  │ │  Excel Generator │
│   REST API       │ │  (Gemini)        │ │  (xlsxwriter)    │
└──────────────────┘ └──────────────────┘ └──────────────────┘
```

## Database Schema

The database is organized into 7 sections with 21 tables:

### Core Hierarchy
- `organizations` - Multi-tenant root (production companies)
- `users` - Team members with roles (Admin, Producer, Coordinator, Crew)
- `projects` - Central hub for productions

### Budgeting Engine (AICP/Hot Budget)
- `budgets` - Version-controlled budget documents
- `budget_sections` - Categories (A. Pre-Pro Labor, B. Shoot Labor, etc.)
- `budget_lines` - Individual line items with OT calculations
- `budget_fringes` - Percentage markups (P&W, Insurance, etc.)

### Crew Management
- `crew_members` - Organization's "Rolodex" of contacts
- `project_crew` - Per-project assignments with deal rates
- `vendors` - Rental houses, suppliers, etc.

### Actualization
- `purchase_orders` - Committed costs linked to budget lines
- `timecards` - Actual labor hours with OT breakdown

### Call Sheets & Logistics
- `call_sheets` - Daily shoot containers (Day 1, Day 2, etc.)
- `locations` - Shoot, basecamp, parking, hospital locations
- `call_sheet_locations` - Junction table for daily location assignments
- `schedule_events` - Daily timeline (Crew Call → Lunch → Wrap)
- `call_sheet_rsvps` - Per-day crew confirmation tracking

## Project Structure

```
epitome/
├── prisma/
│   ├── schema.prisma           # Database schema
│   └── migrations/             # Database migrations
├── agents/
│   └── production_workbook_generator.py  # Excel generator (dynamic crew grid)
├── api/
│   └── main.py                 # FastAPI endpoints + SPA routing
├── static/
│   ├── index.html              # Vite-built React app
│   └── assets/                 # JS/CSS bundles
├── pyproject.toml              # Python project config (uv compatible)
├── requirements.txt            # Python dependencies
├── package.json                # Node dependencies (Prisma, tooling)
├── .env                        # Environment variables (git-ignored)
├── .env.example                # Template for environment setup
├── sync_frontend.sh            # Script to sync Vite build
├── setup_supabase.sh           # Database setup script
├── CLAUDE.md                   # AI assistant context
└── README.md                   # This file
```

## Getting Started

### Prerequisites

- Node.js 18+ (for Prisma)
- Python 3.8+
- Supabase account (or local PostgreSQL)

### Installation

```bash
# Clone the repository
git clone https://github.com/mortenator/epitome.git
cd epitome

# Install Node dependencies (for Prisma)
npm install

# Install Python dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
# Edit .env with your Supabase credentials
```

### Database Setup

```bash
# Generate Prisma client
npx prisma generate

# Run migrations (creates all tables)
npx prisma migrate dev --name init

# View database in Prisma Studio
npx prisma studio
```

### Environment Variables

```bash
# .env
DATABASE_URL="postgresql://postgres:[PASSWORD]@db.[PROJECT].supabase.co:6543/postgres?pgbouncer=true"
DIRECT_URL="postgresql://postgres:[PASSWORD]@db.[PROJECT].supabase.co:5432/postgres"
GEMINI_API_KEY="your_gemini_api_key"
GOOGLE_MAPS_API_KEY="your_google_maps_api_key"
```

## Usage

### Using Prisma Client (TypeScript/JavaScript)

```typescript
import { PrismaClient } from '@prisma/client'

const prisma = new PrismaClient()

// Create a project with call sheets
const project = await prisma.projects.create({
  data: {
    id: 'cuid-here',
    jobNumber: '2024-NIKE-001',
    jobName: 'Nike Air Max Campaign',
    client: 'Nike',
    organizationId: 'org-id',
    updatedAt: new Date(),
    call_sheets: {
      create: [
        {
          id: 'cs1',
          dayNumber: 1,
          shootDate: new Date('2024-03-01'),
          updatedAt: new Date()
        },
        {
          id: 'cs2',
          dayNumber: 2,
          shootDate: new Date('2024-03-02'),
          updatedAt: new Date()
        }
      ]
    }
  }
})

// Query with relations
const projectWithCrew = await prisma.projects.findUnique({
  where: { id: project.id },
  include: {
    call_sheets: {
      include: {
        schedule_events: true,
        call_sheet_rsvps: true
      }
    },
    project_crew: true
  }
})
```

### Using Python Generator

```python
from production_workbook_generator import generate_workbook

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

## Key Features

### Phase 1: Call Sheet Automation
- **Multi-day shoot support**: Each day has its own call sheet with unique weather, locations, schedule
- **Dynamic crew grid**: Compact layout when crew data provided, full template when empty
  - Left side: PRODUCTION, CAMERA, STILLS, GRIP departments
  - Right side: TALENT, MGMT, VANITY, PRODUCTION SUPPORT departments
- **Location management**: Shoot, basecamp, crew parking, truck parking, hospital
- **Schedule timeline**: Crew call → First shot → Lunch → Wrap
- **RSVP tracking**: PENDING → SENT → VIEWED → CONFIRMED per crew member per day
- **Personalized call times**: Override general crew call for specific people
- **Thick perimeter borders**: Professional Excel styling matching industry templates

### Phase 2: Budgeting Engine (Ready)
- **AICP-compliant structure**: Sections A-Z with standard line numbers
- **Overtime calculations**: 1.5x and 2.0x multipliers
- **Fringes/markups**: P&W, Workers Comp, Insurance, Agency Fee
- **Estimated vs. Actual**: Budget lines link to POs and timecards for variance tracking

## Data Flow

```
Organization (Tenant)
  └── Projects
        ├── Budgets → Sections → Lines ← PurchaseOrders
        │                          ↑
        ├── ProjectCrew ───────────┴──→ Timecards
        │       │
        │       └──→ CallSheetRSVPs
        │                   │
        └── CallSheets ─────┘
              ├── ScheduleEvents
              └── CallSheetLocations → Locations
```

## Development Status

**Current**: Full-stack application with dynamic Excel generation, Vite React frontend, FastAPI backend

**Roadmap**:
- [x] Database schema design (Prisma/Supabase)
- [x] Logistics layer (Call Sheets, Schedules, RSVPs)
- [x] Budgeting engine schema
- [x] Excel generator with dynamic crew grid
- [x] FastAPI endpoints with SPA routing
- [x] LLM integration (Gemini) for natural language input
- [x] React + Vite frontend
- [x] Vercel deployment with uv package manager
- [ ] Distribution layer (Email/SMS)
- [ ] Real-time collaboration
- [ ] PDF extraction from Hot Budget files

## Documentation

- See [`CLAUDE.md`](./CLAUDE.md) for AI assistant context and database schema details
- Prisma schema: [`prisma/schema.prisma`](./prisma/schema.prisma)

## Contributing

This is currently a private project. For questions or collaboration, please contact the repository owner.

## License

[Add license information here]

---

**Built for producers, by producers.** Save time, reduce errors, focus on creativity.
