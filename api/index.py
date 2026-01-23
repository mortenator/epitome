"""
Vercel serverless function entry point for FastAPI.
This wraps the FastAPI app for Vercel's serverless Python runtime.
"""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.main import app

# Vercel expects a handler function
handler = app
