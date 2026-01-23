# Claude Code Best Practices

This document outlines best-in-class practices for working with Claude on code projects.

## Table of Contents
- [Project Context: Epitome](#project-context-epitome)
- [Database Schema](#database-schema)
- [Prompt Engineering](#prompt-engineering)
- [Code Generation Guidelines](#code-generation-guidelines)
- [Code Review Practices](#code-review-practices)
- [API Usage Patterns](#api-usage-patterns)

## Project Context: Epitome

### Overview
**Epitome** is a vertical SaaS platform designed to automate physical production workflows (film, TV, advertising).

**Current Phase**: Phase 1 ("The Utility") — Automating the creation of the Call Sheet.

**Core Problem**: Producers spend ~3.5 hours/day manually formatting Excel files and PDFs.

**Solution**: An "Automated Executive Producer" that ingests natural language prompts (e.g., "3 day shoot for Nike") and raw files (Crew Lists) to instantly generate a production-ready Excel workbook.

### Tech Stack

| Layer | Technology |
|-------|------------|
| **Database** | PostgreSQL (Supabase) with Row Level Security |
| **ORM** | Prisma (migrations) + SQLAlchemy (runtime) |
| **Backend** | Python (FastAPI) |
| **Frontend** | React + TypeScript + Vite + Tailwind CSS |
| **AI/LLM** | Google Gemini (extraction + chat) |
| **Excel Generation** | xlsxwriter |
| **Data Enrichment** | Google Maps API, Google Weather API, Google Places API, logo.dev API |

### System Architecture

The system follows a **Database-First** architecture:

```
┌─────────────────────────────────────────────────────────────────┐
│                    SUPABASE (PostgreSQL)                        │
│                      22 Tables, 17 Enums                        │
│                    Row Level Security (RLS)                     │
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
│   FastAPI        │ │  LLM Services     │ │  Excel Generator │
│   REST API       │ │  - Extraction    │ │  (xlsxwriter)    │
│   - Chat API     │ │  - Chat/Q&A      │ │                  │
│   - Project API  │ │  - Edit Commands │ │                  │
└──────────────────┘ └──────────────────┘ └──────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  Data Enrichment │
                    │  - Geocoding     │
                    │  - Weather API   │
                    │  - Client Research│
                    └──────────────────┘
```

### Key Files

| File | Purpose |
|------|---------|
| `prisma/schema.prisma` | Database schema (22 tables) |
| `agents/production_workbook_generator.py` | Excel workbook generator |
| `agents/enrichment.py` | Data enrichment (geocoding, weather, logos) |
| `agents/prompts.py` | LLM system prompts for extraction and chat |
| `api/main.py` | FastAPI REST endpoints |
| `api/services/chat_service.py` | Chat functionality with LLM integration |
| `api/services/project_service.py` | Project CRUD operations |
| `api/database.py` | SQLAlchemy models |
| `.env` | Environment variables (DATABASE_URL, API keys) |

## Database Schema

### Entity Relationship Overview

```
Organization (Tenant)
  ├── users (team members)
  ├── crew_members (rolodex) [auto-deduplicated by email/phone]
  ├── vendors
  ├── clients [dedicated client table]
  └── projects
        ├── budgets → budget_sections → budget_lines ← purchase_orders
        │                                     ↑
        ├── project_crew ─────────────────────┴──→ timecards
        │       │
        │       └──→ call_sheet_rsvps
        │                   │
        ├── locations ──────┼──→ call_sheet_locations
        │                   │
        ├── clients (relation) ────┐
        │                          │
        └── call_sheets ────┘      │
              └── schedule_events  │
                                   │
                            (projects.clientId → clients.id)
```

### Tables by Section

#### 1. Core Hierarchy (Auth & Org)

**organizations** - Multi-tenant root
```
id, name, slug, defaultInsuranceRate, defaultPayrollTaxRate,
defaultWorkersCompRate, defaultAgencyFeeRate
```

**users** - Team members
```
id, email, name, hashedPassword, role (ADMIN|PRODUCER|COORDINATOR|CREW),
organizationId
```

**projects** - Central hub
```
id, jobNumber, jobName, client (legacy string), clientId (FK to clients),
agency, brand, status,
bidDate, awardDate, prepStartDate, shootStartDate, shootEndDate, wrapDate,
insuranceRate, payrollTaxRate, workersCompRate, agencyFeeRate,
organizationId
```

**clients** - Dedicated client table for reporting and management
```
id, name, contactName, email, phone, address, city, state, zip,
notes, isActive, createdAt, updatedAt, organizationId
```

#### 2. Budgeting Engine (AICP/Hot Budget)

**budgets** - Version-controlled budget documents
```
id, version, name, status (DRAFT|PENDING_REVIEW|CLIENT_REVIEW|APPROVED|REVISED),
isActive, lockedAt, projectId, createdById
```

**budget_sections** - Categories (A, B, C...)
```
id, code, name, sortOrder, sectionType (LABOR|EXPENSES|TALENT|PRODUCTION|INSURANCE),
budgetId
```

**budget_lines** - Individual line items
```
id, lineNumber, description, sortOrder,
quantity, rate, days, ot15Hours, ot20Hours, estimatedTotal,
notes, isContracted, sectionId
```

**budget_fringes** - Percentage markups
```
id, name, fringeType (PAYROLL_TAX|WORKERS_COMP|INSURANCE|AGENCY_FEE|CUSTOM),
rate, isActive, sectionId
```

#### 3. Crew Management

**crew_members** - Organization's "Rolodex"
```
id, firstName, lastName, email, phone, address, city, state, zip,
department, primaryRole, defaultRate, unionStatus, unionLocal,
loanOutCompany, w9OnFile, skills[], notes, isActive, organizationId

Note: Auto-deduplication based on email/phone (unique per organization).
When creating crew members, system checks for existing records with
matching email or phone and merges data instead of creating duplicates.
```

**project_crew** - Per-project assignments
```
id, role, department, dealRate, dealType (DAY_RATE|WEEKLY_RATE|FLAT_FEE|HOURLY),
guaranteedDays, kitFee, perDiem, status (HOLD|CONFIRMED|CANCELLED|WRAPPED),
dealMemoSigned, startDate, endDate,
dietaryRestrictions, shirtSize, vehicleInfo, notes,
projectId, crewMemberId, budgetLineId
```

**vendors** - Rental houses, suppliers
```
id, name, contactName, email, phone, address, taxId, w9OnFile,
notes, isActive, organizationId
```

#### 4. Actualization (Financial Feedback Loop)

**purchase_orders** - Committed costs
```
id, poNumber, status (DRAFT|PENDING|APPROVED|ISSUED|RECEIVED|INVOICED|PAID|CANCELLED),
description, amount, taxAmount, totalAmount,
issueDate, dueDate, paidDate, invoiceNumber, paymentMethod, paymentRef, notes,
projectId, vendorId, budgetLineId, createdById, approvedById, approvedAt
```

**timecards** - Actual labor hours
```
id, workDate, callTime, wrapTime,
regularHours, ot15Hours, ot20Hours, mealPenalty,
regularAmount, ot15Amount, ot20Amount, totalAmount,
status (DRAFT|SUBMITTED|APPROVED|REJECTED|PROCESSED|PAID), notes,
projectCrewId, submittedById, submittedAt
```

#### 5. Call Sheets & Logistics

**call_sheets** - Daily shoot containers
```
id, dayNumber, shootDate, status (DRAFT|REVIEW|APPROVED|DISTRIBUTED),
generalCrewCall, firstShot, estimatedWrap,
weatherHigh, weatherLow, weatherSummary, sunrise, sunset,
nearestHospital, hospitalAddress, emergencyContact, emergencyPhone, notes,
projectId
```

**locations** - Places
```
id, name, address, city, state, zip,
latitude, longitude, mapLink,
contactName, contactPhone, contactEmail,
parkingNotes, parkingAddress, loadingNotes, accessNotes, arrivalInstructions, notes,
projectId
```

**call_sheet_locations** - Junction (many-to-many)
```
id, locationType (SHOOT|BASECAMP|CREW_PARKING|TRUCK_PARKING|CATERING|HOLDING|HOSPITAL|HOTEL|OTHER),
callTime, notes, callSheetId, locationId
```

#### 6. Schedule & RSVP

**schedule_events** - Daily timeline
```
id, sortOrder, time, endTime, description, scene, location, notes,
eventType (CREW_CALL|TALENT_CALL|MEAL|SHOOT|COMPANY_MOVE|WRAP|GENERAL),
callSheetId
```

**call_sheet_rsvps** - Per-day crew confirmations
```
id, status (PENDING|SENT|VIEWED|CONFIRMED|DECLINED),
sentAt, viewedAt, confirmedAt,
personalizedCallTime, personalizedNotes,
callSheetId, projectCrewId
```

### Department Enum
```
PRODUCTION, CAMERA, GRIP_ELECTRIC, ART, WARDROBE,
HAIR_MAKEUP, SOUND, LOCATIONS, TRANSPORTATION, CATERING,
POST_PRODUCTION, OTHER
```

### Union Status Enum
```
NON_UNION, IATSE, TEAMSTERS, SAG_AFTRA, DGA, WGA, OTHER_UNION
```

### Critical Relationships

| Link | Purpose |
|------|---------|
| `projects.clientId` → `clients.id` | Client relationship (new) |
| `projects.client` | Legacy string field (kept for migration compatibility) |
| `project_crew.budgetLineId` → `budget_lines` | Labor variance tracking |
| `purchase_orders.budgetLineId` → `budget_lines` | Expense variance tracking |
| `call_sheet_rsvps.projectCrewId` → `project_crew` | Per-day crew confirmations |
| `call_sheet_locations` junction | Link locations to specific shoot days |
| `crew_members.email` + `organizationId` | Unique constraint (deduplication) |
| `crew_members.phone` + `organizationId` | Unique constraint (deduplication) |

### Estimated vs. Actual Query Pattern

```typescript
// Get budget variance for a department
const variance = await prisma.budget_lines.findMany({
  where: {
    budget_sections: {
      budgets: { projectId, isActive: true }
    }
  },
  include: {
    project_crew: {
      where: { department: 'CAMERA' },
      include: {
        timecards: { where: { status: { in: ['APPROVED', 'PAID'] } } }
      }
    },
    purchase_orders: { where: { status: { not: 'CANCELLED' } } }
  }
})

// Calculate: estimatedTotal vs SUM(timecards.totalAmount) + SUM(purchase_orders.totalAmount)
```

## Working with Claude on Epitome

When asking Claude to work on Epitome code, provide context about:
- The Prisma schema and table relationships (22 tables)
- The multi-tenant organization structure with RLS policies
- The Budget Line as the "pivot point" for cost tracking
- The CallSheet → RSVP → ProjectCrew relationship for logistics
- The Supabase/PostgreSQL database connection
- The clients table for client-based reporting
- Crew member auto-deduplication (email/phone uniqueness)
- Chat functionality with LLM integration for Q&A and edit commands
- Data enrichment pipeline (geocoding, weather, client research)

### Common Tasks

**Adding a new field:**
1. Update `prisma/schema.prisma`
2. Run `npx prisma migrate dev --name add_field_name`
3. Update related SQLAlchemy models in `api/database.py`
4. Update API endpoints in `api/main.py` and `api/services/`
5. Add RLS policies if needed (for Supabase security)

**Creating a new API endpoint:**
1. Add route to `api/main.py`
2. Create service function in `api/services/` if needed
3. Use SQLAlchemy (AsyncSession) for database access
4. Follow REST conventions
5. Include proper error handling and input validation
6. Add to `api/services/__init__.py` exports

**Generating Excel from database:**
1. Query SQLAlchemy for project data with relations
2. Transform to the generator's expected JSON schema
3. Call `production_workbook_generator.py`

**Adding chat functionality:**
1. Chat commands are processed via `api/services/chat_service.py`
2. LLM prompts are defined in `agents/prompts.py`
3. Edit commands execute via `project_service` functions
4. Frontend sends messages to `/api/chat` endpoint
5. Chat supports both Q&A and edit commands (e.g., "Change crew call to 8am")

**Data enrichment:**
1. Enrichment happens in `agents/enrichment.py`
2. Supports geocoding (Google Maps), weather (Google Weather API), hospital lookup (Google Places), logos (logo.dev)
3. Runs in parallel for performance
4. Caches results to avoid duplicate API calls
5. Weather data requires valid YYYY-MM-DD dates (validated before API calls)
6. Forecasts limited to 10 days ahead (Google Weather API limitation)
7. Sunrise/sunset times are converted to local timezone using the location's timezone ID
8. Nearest hospital is automatically found based on filming location coordinates

**Frontend Integration:**
1. Frontend is in separate repository (`frontend_source/`)
2. Uses React Query for data fetching (`useProject`, `useGeneration` hooks)
3. Chat panel component handles form submission and Enter key
4. Production info cards support inline editing with overflow protection
5. API client in `frontend_source/src/lib/api.ts` handles all backend communication

## Prompt Engineering

### Clear, Specific Requests
- **Be explicit**: State exactly what you want Claude to do
- **Provide context**: Include relevant code snippets, file paths, and project structure
- **Specify constraints**: Mention language versions, frameworks, style guides, and requirements
- **Break down complex tasks**: Decompose large requests into smaller, manageable steps

### Effective Prompt Structure
```
Context: [Brief description of what you're working on]
Goal: [What you want to achieve]
Constraints: [Any limitations or requirements]
Example: [Reference code or pattern if applicable]
```

## Code Generation Guidelines

### Request High-Quality Code
- Ask for **production-ready code** with proper error handling
- Request **comments and documentation** for complex logic
- Specify **code style** preferences (ESLint, Prettier, Black, etc.)
- Ask for **type safety** when using TypeScript/Python type hints

### Language-Specific Best Practices

#### TypeScript (Prisma)
- Use Prisma's generated types
- Handle async/await properly
- Use transactions for multi-table operations
- Implement proper error handling

#### Python
- Follow PEP 8 style guide
- Use type hints (Python 3.5+)
- Implement proper exception handling
- Document with docstrings

## Code Review Practices

### Review Checklist
When asking Claude to review code, request checks for:
- **Logic errors** and potential bugs
- **Performance issues** (N+1 queries, unnecessary re-renders, etc.)
- **Security vulnerabilities** (SQL injection, XSS, etc.)
- **Code quality** (readability, maintainability, complexity)
- **Best practices** adherence

## API Usage Patterns

### SQLAlchemy Usage (Backend)
```python
from api.database import get_db, Project, Client, CrewMember
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

# Create with relations
async def create_project(db: AsyncSession, org_id: str):
    project = Project(
        id=str(uuid.uuid4()),
        jobNumber='2024-NIKE-001',
        jobName='Nike Campaign',
        client='Nike',  # Legacy field
        organizationId=org_id,
        updatedAt=datetime.utcnow()
    )
    db.add(project)
    await db.commit()
    return project

# Query with relations
async def get_project(db: AsyncSession, project_id: str):
    result = await db.execute(
        select(Project)
        .where(Project.id == project_id)
        .options(
            selectinload(Project.call_sheets),
            selectinload(Project.client_relation),  # New clients relation
            selectinload(Project.project_crew)
        )
    )
    return result.scalar_one_or_none()

# Get or create client (with deduplication)
async def get_or_create_client(db: AsyncSession, client_name: str, org_id: str):
    result = await db.execute(
        select(Client)
        .where(Client.name == client_name, Client.organizationId == org_id)
    )
    client = result.scalar_one_or_none()
    if not client:
        client = Client(
            id=str(uuid.uuid4()),
            name=client_name,
            organizationId=org_id,
            updatedAt=datetime.utcnow()
        )
        db.add(client)
        await db.commit()
    return client.id
```

### API Endpoints

**Project Management:**
- `GET /api/project/{project_id}` - Get project data for frontend
- `PATCH /api/project/{project_id}?jobName=...&client=...&agency=...` - Update project

**Chat Functionality:**
- `POST /api/chat` - Send chat message (FormData: project_id, message)
  - Returns: `{ type: "answer"|"edit", response: string, action?: string, success?: boolean }`

**Crew Management:**
- `PATCH /api/crew/{crew_id}?callTime=...&location=...` - Update crew member
- `GET /api/crew/search?q=...&department=...` - Search crew members

**Generation:**
- `POST /api/generate` - Start workbook generation (FormData: prompt, file)
- `GET /api/progress/{job_id}` - SSE stream for progress updates
- `GET /api/download/{filename}` - Download generated workbook

## Security Considerations

When working with Claude on code, always:
- **Review generated code**: Don't blindly trust AI-generated code
- **Validate inputs**: Ensure proper input validation is in place
- **Secure credentials**: Never commit API keys or secrets (use `.env`)
- **Use prepared statements**: SQLAlchemy handles this automatically
- **Implement authorization**: Check user permissions before operations
- **Row Level Security (RLS)**: All tables should have RLS policies in Supabase
  - Policies restrict access based on `organizationId`
  - Service role (used by Prisma/SQLAlchemy) bypasses RLS
  - Authenticated users can only access their organization's data
- **Data deduplication**: Crew members are auto-deduplicated to prevent duplicates
- **Client data**: Use the `clients` table for client management, not the legacy `projects.client` string

## Recent Features (January 2025/2026)

### Chat Functionality
- **LLM-Powered Chat**: Interactive chat panel for Q&A and edit commands
- **Edit Commands**: Natural language commands like "Change crew call time to 8am"
- **Context-Aware**: Chat has access to full project context (crew, locations, call sheets)
- **Real-time Updates**: Frontend automatically refreshes after successful edits

### Clients Table
- **Dedicated Client Management**: New `clients` table for better client reporting
- **Migration**: Existing `projects.client` data automatically migrated
- **RLS Policies**: Full Row Level Security with organization-based access control
- **Backward Compatible**: Legacy `projects.client` string field retained

### Crew Member Deduplication
- **Auto-Deduplication**: Automatic merging of duplicate crew members
- **Unique Constraints**: Email and phone are unique per organization (partial indexes)
- **Merge Strategy**: When duplicates found, existing record is updated with new data
- **Data Cleanup**: Migration handles existing duplicates before applying constraints

### Data Enrichment
- **Geocoding**: Automatic coordinate lookup for locations (Google Maps API)
- **Weather Data**: Forecast weather with proper timezone conversion (Google Weather API)
- **Hospital Lookup**: Nearest hospital found via Google Places API based on filming location
- **Date Validation**: Prevents malformed dates from breaking weather API calls
- **Parallel Processing**: Multiple API calls run concurrently for performance
- **Caching**: Results cached to minimize API calls
- **Timezone Support**: Sunrise/sunset times converted to local timezone using location's timezone ID

### Call Sheet Generation
- **Balanced Crew Grid**: Greedy bin-packing algorithm distributes departments between left/right columns for visual balance
- **Anchor Departments**: Production and Camera always stay on the left column (traditional call sheet order)
- **Talent Call Times**: Cast and Talent departments use `talent_call` time; other departments use `crew_call`
- **Dynamic Layout**: Grid height adjusts based on crew count, footer sections move up accordingly
- **Department Grouping**: Crew automatically grouped by department with headers

### UI Improvements
- **Chat Panel**: Fixed form submission and Enter key handling
- **Input Overflow**: Fixed input boxes extending beyond card boundaries
- **Layout Stability**: Prevented text jumping on hover (edit icon space reservation)
- **Height Management**: Proper flexbox layout for full-height panels

### Call Sheet Layout (January 2026)
- **Balanced Crew Grid**: Replaced hardcoded department list with greedy bin-packing algorithm
  - Departments distributed between left/right columns for visual balance (e.g., 20 vs 18 rows instead of 44 vs 0)
  - Production and Camera anchored to left column (traditional call sheet order)
  - Remaining departments sorted by size and assigned to column with fewer rows
- **Talent Call Times**: Cast members now correctly receive talent call time instead of crew call time
- **Hospital Enrichment**: Nearest hospital automatically populated using Google Places API
- **Weather Timezone Fix**: Sunrise/sunset times now display in local timezone (not UTC)

---

*This document is a living guide and should be updated as best practices evolve.*
