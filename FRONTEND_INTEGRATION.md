# Frontend Integration Guide

This document explains how the Lovable frontend (blueprint-dash-render) is integrated with the Epitome backend.

## Architecture

- **Lovable Repo**: https://github.com/mortenator/blueprint-dash-render.git
  - This repo stays connected to Lovable for syncing
  - Contains the React/TypeScript/Vite frontend source code
  
- **Epitome Repo**: https://github.com/mortenator/epitome.git
  - Contains the FastAPI backend
  - Serves the built frontend from `static/` directory

## How It Works

1. **Development in Lovable**: Make changes in the Lovable repo (blueprint-dash-render)
2. **Sync to Epitome**: Run the sync script to build and copy frontend to Epitome
3. **Serve via FastAPI**: Epitome's FastAPI serves the built frontend from `static/`

## Setup Instructions

### Initial Setup

1. **Sync the frontend for the first time**:
   ```bash
   ./sync_frontend.sh
   ```

2. **Start the FastAPI server**:
   ```bash
   source venv/bin/activate
   uvicorn api.main:app --reload --host 127.0.0.1 --port 8000
   ```

### Updating Frontend

When you make changes in Lovable:

1. **Push changes to blueprint-dash-render repo** (Lovable does this automatically)

2. **Sync to Epitome**:
   ```bash
   ./sync_frontend.sh
   ```

3. **Restart FastAPI server** (if needed):
   ```bash
   # The server will auto-reload if --reload flag is used
   ```

## Directory Structure

```
epitome/
├── static/              # Built frontend files (served by FastAPI)
├── frontend_source/     # Cloned Lovable repo (gitignored)
├── sync_frontend.sh     # Sync script
├── api/                 # FastAPI backend
└── agents/              # Epitome agents
```

## API Integration

The frontend should call the Epitome API endpoints:

- `POST /api/generate` - Generate workbook
- `GET /api/progress/{job_id}` - Get progress updates
- `GET /api/download/{filename}` - Download workbook
- `GET /api/result/{job_id}` - Get result data

## Environment Variables

Make sure your `.env` file has:
- `GEMINI_API_KEY` - For AI extraction
- `GOOGLE_MAPS_API_KEY` - For location services (optional)

## Notes

- The `frontend_source/` directory is gitignored (keeps repos separate)
- The `static/` directory contains the built frontend (can be committed)
- Lovable continues to sync to blueprint-dash-render.git
- Epitome serves the built frontend independently
