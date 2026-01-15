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
| **Database** | PostgreSQL (Supabase) |
| **ORM** | Prisma |
| **Backend** | Python (FastAPI) |
| **AI/LLM** | Google Gemini |
| **Excel Generation** | xlsxwriter |

### System Architecture

The system follows a **Database-First** architecture:

```
┌─────────────────────────────────────────────────────────────────┐
│                    SUPABASE (PostgreSQL)                        │
│                      21 Tables, 17 Enums                        │
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

### Key Files

| File | Purpose |
|------|---------|
| `prisma/schema.prisma` | Database schema (21 tables) |
| `agents/production_workbook_generator.py` | Excel workbook generator |
| `api/main.py` | FastAPI REST endpoints |
| `.env` | Environment variables (DATABASE_URL, API keys) |

## Database Schema

### Entity Relationship Overview

```
Organization (Tenant)
  ├── users (team members)
  ├── crew_members (rolodex)
  ├── vendors
  └── projects
        ├── budgets → budget_sections → budget_lines ← purchase_orders
        │                                     ↑
        ├── project_crew ─────────────────────┴──→ timecards
        │       │
        │       └──→ call_sheet_rsvps
        │                   │
        ├── locations ──────┼──→ call_sheet_locations
        │                   │
        └── call_sheets ────┘
              └── schedule_events
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
id, jobNumber, jobName, client, agency, brand, status,
bidDate, awardDate, prepStartDate, shootStartDate, shootEndDate, wrapDate,
insuranceRate, payrollTaxRate, workersCompRate, agencyFeeRate,
organizationId
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
| `project_crew.budgetLineId` → `budget_lines` | Labor variance tracking |
| `purchase_orders.budgetLineId` → `budget_lines` | Expense variance tracking |
| `call_sheet_rsvps.projectCrewId` → `project_crew` | Per-day crew confirmations |
| `call_sheet_locations` junction | Link locations to specific shoot days |

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
- The Prisma schema and table relationships
- The multi-tenant organization structure
- The Budget Line as the "pivot point" for cost tracking
- The CallSheet → RSVP → ProjectCrew relationship for logistics
- The Supabase/PostgreSQL database connection

### Common Tasks

**Adding a new field:**
1. Update `prisma/schema.prisma`
2. Run `npx prisma migrate dev --name add_field_name`
3. Update related TypeScript types and API endpoints

**Creating a new API endpoint:**
1. Use Prisma client for database access
2. Follow REST conventions
3. Include proper error handling
4. Add input validation

**Generating Excel from database:**
1. Query Prisma for project data with relations
2. Transform to the generator's expected JSON schema
3. Call `production_workbook_generator.py`

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

### Prisma Client Usage
```typescript
import { PrismaClient } from '@prisma/client'

const prisma = new PrismaClient()

// Create with relations
const project = await prisma.projects.create({
  data: {
    id: generateCuid(),
    jobNumber: '2024-NIKE-001',
    jobName: 'Nike Campaign',
    client: 'Nike',
    organizationId: orgId,
    updatedAt: new Date(),
    call_sheets: {
      create: [
        { id: generateCuid(), dayNumber: 1, shootDate: new Date(), updatedAt: new Date() }
      ]
    }
  },
  include: { call_sheets: true }
})

// Query with nested relations
const fullProject = await prisma.projects.findUnique({
  where: { id: projectId },
  include: {
    call_sheets: {
      include: {
        schedule_events: { orderBy: { sortOrder: 'asc' } },
        call_sheet_rsvps: { include: { project_crew: true } },
        call_sheet_locations: { include: { locations: true } }
      }
    },
    project_crew: { include: { crew_members: true } },
    budgets: { where: { isActive: true } }
  }
})
```

## Security Considerations

When working with Claude on code, always:
- **Review generated code**: Don't blindly trust AI-generated code
- **Validate inputs**: Ensure proper input validation is in place
- **Secure credentials**: Never commit API keys or secrets (use `.env`)
- **Use prepared statements**: Prisma handles this automatically
- **Implement authorization**: Check user permissions before operations

---

*This document is a living guide and should be updated as best practices evolve.*
