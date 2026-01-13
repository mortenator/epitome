"""FastAPI application for Epitome frontend demo."""
import asyncio
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# Load environment variables from .env file BEFORE importing agents
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, continue without it

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.progress import ProgressEvent, progress_manager
from agents.production_workbook_generator import run_tool

# Directory setup
BASE_DIR = Path(__file__).parent.parent
OUTPUT_DIR = BASE_DIR / "output"
STATIC_DIR = BASE_DIR / "static"

OUTPUT_DIR.mkdir(exist_ok=True)

# Create FastAPI app
app = FastAPI(
    title="Epitome Production Workbook Generator",
    description="Generate production workbooks from natural language prompts",
    version="1.0.0"
)

# CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/", response_class=HTMLResponse)
async def serve_index():
    """Serve the main HTML page."""
    index_path = STATIC_DIR / "index.html"
    if not index_path.exists():
        return HTMLResponse(
            content="<h1>Epitome API</h1><p>Frontend not found. Place index.html in /static/</p>",
            status_code=200
        )
    return FileResponse(str(index_path))


@app.post("/api/generate")
async def generate_workbook(
    prompt: str = Form(...),
    file: Optional[UploadFile] = File(None)
):
    """
    Start workbook generation. Returns a job_id for progress tracking.

    - Accepts multipart form data
    - prompt: Natural language request
    - file: Optional CSV/PDF/TXT file for context
    """
    loop = asyncio.get_event_loop()
    job_id = progress_manager.create_job(loop)

    # Read uploaded file if provided
    file_content = None
    if file:
        content = await file.read()
        # Handle different file types
        if file.filename.endswith('.csv') or file.filename.endswith('.txt'):
            file_content = content.decode('utf-8', errors='ignore')
        elif file.filename.endswith('.pdf'):
            # Properly extract text from PDF
            try:
                import io
                import PyPDF2
                
                pdf_file = io.BytesIO(content)
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                
                # Extract text from all pages
                extracted_text = []
                for page_num, page in enumerate(pdf_reader.pages, 1):
                    page_text = page.extract_text()
                    if page_text.strip():
                        extracted_text.append(f"--- Page {page_num} ---\n{page_text}")
                
                if extracted_text:
                    file_content = f"[PDF file: {file.filename}]\n\n" + "\n\n".join(extracted_text)
                else:
                    file_content = f"[PDF file: {file.filename} - No extractable text found]"
                    
            except Exception as e:
                # Fallback if PDF parsing fails
                file_content = f"[PDF file: {file.filename} - Error extracting text: {str(e)}]"
        else:
            file_content = content.decode('utf-8', errors='ignore')

    # Run generation in background
    asyncio.create_task(
        run_generation_task(job_id, prompt, file_content, loop)
    )

    return {"job_id": job_id, "status": "started"}


async def run_generation_task(
    job_id: str,
    prompt: str,
    file_content: Optional[str],
    loop: asyncio.AbstractEventLoop
):
    """Background task that runs the generation pipeline."""

    def progress_callback(stage_id: str, percent: int, message: str):
        """Callback to emit progress events."""
        progress_manager.emit_progress(job_id, stage_id, percent, message)

    try:
        # Run the synchronous run_tool in a thread pool
        result = await loop.run_in_executor(
            None,
            lambda: run_tool(
                prompt=prompt,
                attached_file_content=file_content,
                enrich=True,
                progress_callback=progress_callback
            )
        )

        # Move workbook to output directory with unique name
        original_path = Path(result['workbook_path'])
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        new_filename = f"Epitome_Workbook_{job_id[:8]}_{timestamp}.xlsx"
        new_path = OUTPUT_DIR / new_filename

        if original_path.exists():
            shutil.move(str(original_path), str(new_path))

        result['workbook_path'] = str(new_path)
        result['download_filename'] = new_filename

        progress_manager.set_result(job_id, result)

        # Send download ready event
        download_event = ProgressEvent(
            "download_ready", 100,
            json.dumps({"filename": new_filename})
        )
        queue = progress_manager.get_queue(job_id)
        if queue:
            await queue.put(download_event)

    except Exception as e:
        # Emit error event
        error_event = ProgressEvent("error", -1, f"Error: {str(e)}")
        queue = progress_manager.get_queue(job_id)
        if queue:
            await queue.put(error_event)
        progress_manager.set_result(job_id, {"error": str(e)})


@app.get("/api/progress/{job_id}")
async def stream_progress(job_id: str):
    """
    SSE endpoint for real-time progress updates.

    Client connects and receives events like:
    data: {"stage_id": "extracting_data", "percent": 30, "message": "..."}
    """
    queue = progress_manager.get_queue(job_id)
    if not queue:
        raise HTTPException(status_code=404, detail="Job not found")

    async def event_generator():
        try:
            while True:
                try:
                    # Wait for next event with timeout
                    event = await asyncio.wait_for(queue.get(), timeout=120.0)
                    yield event.to_sse()

                    # Check if error or download ready (don't break on 'complete' - wait for download_ready)
                    if event.stage_id in ("error", "download_ready"):
                        break

                except asyncio.TimeoutError:
                    # Send keepalive comment
                    yield ": keepalive\n\n"

        except asyncio.CancelledError:
            pass
        finally:
            # Clean up after stream ends
            progress_manager.cleanup_job(job_id)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@app.get("/api/download/{filename}")
async def download_workbook(filename: str):
    """Download a generated workbook."""
    # Security: sanitize filename
    safe_filename = Path(filename).name
    file_path = OUTPUT_DIR / safe_filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    # Ensure file is within output directory
    try:
        file_path.resolve().relative_to(OUTPUT_DIR.resolve())
    except ValueError:
        raise HTTPException(status_code=403, detail="Access denied")

    return FileResponse(
        path=str(file_path),
        filename=safe_filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


@app.get("/api/result/{job_id}")
async def get_result(job_id: str):
    """Get the result data for a completed job."""
    result = progress_manager.get_result(job_id)
    if not result:
        raise HTTPException(status_code=404, detail="Result not found")

    return {
        "status": "error" if "error" in result else "complete",
        "data": result.get("data"),
        "download_filename": result.get("download_filename"),
        "error": result.get("error")
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "epitome-api"}
