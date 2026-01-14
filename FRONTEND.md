# Epitome Frontend Documentation

## 1. Project Overview

**Stack:** React, Vite, TypeScript, Tailwind CSS

**Purpose:** Automated Call Sheet builder for film production.

**Current State:** UI is fully mocked with hardcoded data. Needs backend integration.

## 2. Core User Flow & Components

### A. Dashboard (`/`)

**Component:** `InputCard.tsx`

**Functionality:**
- Drag-and-drop zone for files (Crew Lists).
- Textarea for natural language prompts (e.g., "3 day shoot for Nike").

**Integration Goal:** On submit, this must POST FormData (file + prompt) to the backend.

### B. Loading Screen (`/loading`)

**Component:** `LoadingContent.tsx`

**Functionality:**
- Visual progress steps (`LoadingStepList.tsx`).
- Currently uses a timeout to redirect.

**Integration Goal:** Should poll the backend status or wait for the generic API response before redirecting to `/callsheet`.

### C. Call Sheet Builder (`/callsheet`)

**Component:** `CallSheetPreview.tsx` (Main Container)

**Data Display:**
- `ProductionInfoCards.tsx`: Displays Logistics (Parking, Weather).
- `CrewDepartment.tsx`: Renders lists of crew (Camera, Grip, etc.).

**Interactions:**
- Inline Editing: Users can click Call Time/Location to edit.
- Add Crew: `AddCrewDropdown.tsx` allows adding people to departments.

**Integration Goal:** Replace `const [departments]` state with data fetched from the DB. Sync edits (PATCH requests) to the DB.

### D. Export/Download

**Component:** `TopBar.tsx`

**Functionality:** "Download" button.

**Integration Goal:** Trigger a GET request that runs the Python Excel generator and returns the .xlsx file blob.

## 3. Data Structures (Current Mocks)

### CrewMember
```typescript
{
  role: string;
  name: string;
  phone: string;
  email: string;
  callTime: string;
  location: string;
}
```

### Department
```typescript
{
  name: string;
  crew: CrewMember[];
}
```

## 4. Required Backend Mappings

### Frontend → Database Mappings

- **Frontend `CrewMember`** → **Database `ProjectCrew` + `CallSheetRSVP`**
  - Crew member data is stored in `ProjectCrew` table
  - Per-day RSVP status tracked in `CallSheetRSVP` table

- **Frontend `ProductionInfoCards`** → **Database `Location`**
  - Parking/Basecamp information stored in `Location` table
  - Linked to call sheets via `CallSheetLocation` junction table

- **Frontend Prompt Input** → **Database `Project` (Creation)**
  - Natural language prompt should create/update `Project` record
  - Extracted data populates project fields (jobName, client, dates, etc.)

## 5. API Integration Points

### POST `/api/generate`
- **Purpose:** Submit prompt + file to start workbook generation
- **Payload:** `FormData` with `prompt` (string) and `file` (File)
- **Response:** `{ job_id: string, status: "started" }`
- **Used by:** `InputCard.tsx` on form submit

### GET `/api/progress/{job_id}`
- **Purpose:** Poll for generation progress (SSE stream)
- **Response:** Server-Sent Events stream with progress updates
- **Used by:** `LoadingContent.tsx` to show progress and redirect when complete

### GET `/api/download/{filename}`
- **Purpose:** Download generated Excel workbook
- **Response:** `.xlsx` file blob
- **Used by:** `TopBar.tsx` Download button

### GET `/api/result/{job_id}`
- **Purpose:** Get final result data after generation
- **Response:** `{ status: "complete", data: {...}, download_filename: string }`
- **Used by:** After generation completes, to get workbook details

## 6. Component Structure

```
src/
├── pages/
│   ├── Index.tsx              # Dashboard with InputCard
│   ├── Loading.tsx             # Loading screen with progress
│   └── CallSheet.tsx          # Call sheet builder
├── components/
│   ├── dashboard/
│   │   ├── InputCard.tsx      # File upload + prompt input
│   │   └── LoadingContent.tsx # Progress display
│   ├── callsheet/
│   │   ├── CallSheetPreview.tsx    # Main container
│   │   ├── ProductionInfoCards.tsx  # Logistics cards
│   │   ├── CrewDepartment.tsx       # Department crew lists
│   │   └── AddCrewDropdown.tsx      # Add crew member UI
│   └── shared/
│       └── TopBar.tsx         # Download button
```

## 7. State Management

**Current:** Local component state with hardcoded data

**Future:** 
- Replace with API calls to fetch from database
- Use React Query or similar for data fetching/caching
- Sync edits back to database via PATCH requests

## 8. Integration Checklist

- [ ] Connect `InputCard.tsx` to POST `/api/generate`
- [ ] Update `LoadingContent.tsx` to poll `/api/progress/{job_id}`
- [ ] Replace hardcoded departments in `CallSheetPreview.tsx` with API data
- [ ] Implement PATCH requests for inline edits (call time, location)
- [ ] Connect `AddCrewDropdown.tsx` to create new `ProjectCrew` records
- [ ] Connect `TopBar.tsx` Download button to GET `/api/download/{filename}`
- [ ] Map frontend data structures to Prisma models
- [ ] Handle loading/error states throughout

## 9. Notes

- The frontend is currently in the `frontend_source/` directory
- Built files are synced to `static/` directory for FastAPI to serve
- Use `./sync_frontend.sh` to rebuild and sync frontend changes
- FastAPI serves the frontend from `static/` and handles API routes at `/api/*`
