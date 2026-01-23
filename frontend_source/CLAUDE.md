# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is the **React frontend** for Epitome, a vertical SaaS platform for automating film/TV production workflows. This frontend connects to a FastAPI backend (in the parent `../` directory).

## Commands

```bash
# Development
npm run dev          # Start Vite dev server on port 8080

# Build
npm run build        # Production build
npm run build:dev    # Development build (with sourcemaps)
npm run preview      # Preview production build

# Quality
npm run lint         # ESLint
npm run test         # Run tests once
npm run test:watch   # Run tests in watch mode
```

**Important**: The dev server runs on port 8080, but proxies `/api` requests to the FastAPI backend on port 8000. Always test on port 8080, not 8000.

## Architecture

### Tech Stack
- **Vite** + **React 18** + **TypeScript**
- **Tailwind CSS** with custom CSS variables (defined in `src/index.css`)
- **shadcn/ui** components (Radix UI primitives in `src/components/ui/`)
- **React Query** for data fetching and caching
- **React Router** for navigation
- **lucide-react** for icons

### Directory Structure

```
src/
├── components/
│   ├── ui/              # shadcn/ui primitives (button, table, dropdown, etc.)
│   ├── callsheet/       # Call sheet view components
│   ├── dashboard/       # Dashboard/home page components
│   ├── loading/         # Generation progress components
│   └── shared/          # Shared components (TopBar, etc.)
├── hooks/               # Custom React hooks
├── lib/                 # Utilities and API client
├── pages/               # Route pages (Index, Loading, CallSheet)
└── test/                # Test setup and test files
```

### Key Files

| File | Purpose |
|------|---------|
| `src/lib/api.ts` | API client - all backend communication |
| `src/hooks/useProject.ts` | React Query hooks for project data |
| `src/hooks/useGeneration.ts` | SSE-based generation progress tracking |
| `src/hooks/useWorkbookRegeneration.ts` | Workbook regeneration after data changes |
| `src/components/callsheet/CallSheetPreview.tsx` | Main call sheet view |
| `src/components/callsheet/ChatPanel.tsx` | AI chat panel for Q&A and edits |
| `src/index.css` | CSS variables and Tailwind base styles |

### Data Flow

1. **Generation flow**: `InputCard` → `/api/generate` → SSE progress → Navigate to `/callsheet?project=ID`
2. **Project fetch**: `useProject` hook → `/api/project/{id}` → React Query cache
3. **Chat flow**: `ChatPanel` → `/api/chat` → LLM response → Refresh data if edit
4. **Inline edits**: `CrewDepartment` → `updateCrewMember` → Regenerate workbook

### API Proxy

Vite proxies `/api/*` requests to `http://localhost:8000` (configured in `vite.config.ts`). This means:
- Frontend calls `/api/project/123`
- Vite proxies to `http://localhost:8000/api/project/123`

### CSS Variables

Custom colors defined in `src/index.css`:
- `--primary`, `--secondary`, `--muted`, `--accent` - standard shadcn colors
- `--epitome-blue` - brand blue
- `--sidebar-*` - sidebar-specific colors
- `--nav-active/--nav-inactive` - navigation states

### Component Patterns

**shadcn/ui components** are in `src/components/ui/` and should not be modified directly. To customize, either:
1. Use Tailwind classes in the consuming component
2. Create a wrapper component in `src/components/`

**Overflow handling**: Use `min-w-0 overflow-hidden` on flex containers to prevent content from pushing parents wider than their flex allocation.

### Testing

Tests use Vitest with jsdom. Test files should be named `*.test.ts` or `*.spec.ts` and placed in `src/test/` or next to the component.

```bash
npm run test              # Run all tests
npm run test:watch        # Watch mode
```

## Backend Reference

See `../CLAUDE.md` for backend architecture, database schema, and API endpoints.

## Ports

| Port | Service |
|------|---------|
| 8080 | Vite dev server (frontend) |
| 8000 | FastAPI (backend) |
