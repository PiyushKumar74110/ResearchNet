"""FastAPI application for the ResearchMind research pipeline."""

import asyncio
import json
from typing import AsyncIterator

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.core.config import settings
from app.services.pipeline import JOBS, create_research_job, run_research_job

app = FastAPI(title="ResearchMind API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ResearchRequest(BaseModel):
    """Validate a research topic submitted by the frontend."""

    topic: str = Field(min_length=3, max_length=500)


@app.get("/health")
async def health() -> dict[str, str]:
    """Return a simple API health response."""
    return {"status": "ok", "service": "researchmind-api"}


@app.post("/api/research", status_code=202)
async def start_research(request: ResearchRequest) -> dict[str, str]:
    """Create a research job and schedule it in the background."""
    topic = request.topic.strip()
    if len(topic) < 3:
        raise HTTPException(status_code=422, detail="Please enter a longer research topic.")
    job_id = create_research_job(topic)
    asyncio.create_task(run_research_job(job_id, topic))
    return {"job_id": job_id, "status": "queued"}


@app.get("/api/research/{job_id}")
async def get_research(job_id: str) -> dict:
    """Return the current status and results for one research job."""
    job = JOBS.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Research job not found.")
    return job.public_dict()


@app.get("/api/research/{job_id}/events")
async def research_events(job_id: str) -> StreamingResponse:
    """Stream progress and completion events to the frontend using SSE."""
    job = JOBS.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Research job not found.")

    async def event_stream() -> AsyncIterator[str]:
        """Yield queued job events until the job reaches a terminal state."""
        queue = job.events
        yield f"data: {json.dumps({'type': 'snapshot', 'job': job.public_dict()})}\n\n"
        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=15)
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
                if event.get("type") in {"completed", "failed"}:
                    break
            except asyncio.TimeoutError:
                yield ": keep-alive\n\n"
                if job.status in {"completed", "failed"}:
                    yield f"data: {json.dumps({'type': job.status, 'job': job.public_dict()}, ensure_ascii=False)}\n\n"
                    break

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
