#!/usr/bin/env python3
"""
Epitome API Server
Run this script to start the frontend demo server.

Usage:
    python run.py

Then open http://127.0.0.1:8000 in your browser.
"""

import uvicorn

if __name__ == "__main__":
    print("\n🎬 Starting Epitome Production Workbook Generator...")
    print("📍 Open http://127.0.0.1:8000 in your browser\n")

    uvicorn.run(
        "api.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )
