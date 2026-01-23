#!/usr/bin/env python3
"""
Epitome API Server
Run this script to start the frontend demo server.

Usage:
    python run.py

Then open http://127.0.0.1:8000 in your browser.
"""

import os
import uvicorn

if __name__ == "__main__":
    # Use PORT from environment (Railway/production) or default to 8000
    port = int(os.environ.get("PORT", 8000))
    # Use 0.0.0.0 in production (PORT set), 127.0.0.1 locally
    host = "0.0.0.0" if os.environ.get("PORT") else "127.0.0.1"
    # Disable reload in production
    reload = not os.environ.get("PORT")

    print(f"\n🎬 Starting Epitome Production Workbook Generator...")
    print(f"📍 Server running on http://{host}:{port}\n")

    uvicorn.run(
        "api.main:app",
        host=host,
        port=port,
        reload=reload
    )
