"""Progress Manager for SSE streaming."""
import asyncio
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional


@dataclass
class ProgressEvent:
    """A single progress event."""
    stage_id: str
    percent: int
    message: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_sse(self) -> str:
        """Convert to SSE format."""
        data = {
            "stage_id": self.stage_id,
            "percent": self.percent,
            "message": self.message,
            "timestamp": self.timestamp
        }
        return f"data: {json.dumps(data)}\n\n"


class ProgressManager:
    """Manages progress queues for multiple jobs."""

    def __init__(self):
        self._queues: Dict[str, asyncio.Queue] = {}
        self._results: Dict[str, dict] = {}
        self._loops: Dict[str, asyncio.AbstractEventLoop] = {}

    def create_job(self, loop: asyncio.AbstractEventLoop = None) -> str:
        """Create a new job and return its ID."""
        job_id = str(uuid.uuid4())
        self._queues[job_id] = asyncio.Queue()
        if loop:
            self._loops[job_id] = loop
        return job_id

    def get_queue(self, job_id: str) -> Optional[asyncio.Queue]:
        """Get the progress queue for a job."""
        return self._queues.get(job_id)

    def emit_progress(self, job_id: str, stage_id: str, percent: int, message: str):
        """
        Emit a progress event (thread-safe, called from sync code).

        This method is designed to be called from synchronous code running in
        a thread pool executor, and safely puts events into the async queue.
        """
        if job_id not in self._queues:
            return

        event = ProgressEvent(stage_id, percent, message)
        queue = self._queues[job_id]
        loop = self._loops.get(job_id)

        if loop and loop.is_running():
            # Thread-safe way to put into async queue from sync code
            asyncio.run_coroutine_threadsafe(queue.put(event), loop)
        else:
            # Fallback: try to put directly (may not work in all contexts)
            try:
                queue.put_nowait(event)
            except Exception:
                pass

    def set_result(self, job_id: str, result: dict):
        """Store the final result for a job."""
        self._results[job_id] = result

    def get_result(self, job_id: str) -> Optional[dict]:
        """Get the result for a job."""
        return self._results.get(job_id)

    def cleanup_job(self, job_id: str):
        """Clean up resources for a completed job."""
        self._queues.pop(job_id, None)
        self._loops.pop(job_id, None)
        # Keep result for download - will be cleaned up separately


# Global instance
progress_manager = ProgressManager()
