"""Orchestrate research jobs and publish progress events."""

import asyncio
import re
import uuid
from dataclasses import dataclass, field
from typing import Any

from app.agents.agents import (
    build_critic_chain,
    build_reader_agent,
    build_search_agent,
    build_writer_chain,
)


@dataclass
class ResearchJob:
    """Keep in-memory status, outputs, and SSE events for one research request."""

    job_id: str
    topic: str
    status: str = "queued"
    stage: str = "queued"
    results: dict[str, str] = field(default_factory=dict)
    error: str | None = None
    events: asyncio.Queue = field(default_factory=asyncio.Queue)

    def public_dict(self) -> dict[str, Any]:
        """Serialize job state without exposing the internal event queue."""
        return {
            "job_id": self.job_id,
            "topic": self.topic,
            "status": self.status,
            "stage": self.stage,
            "results": self.results,
            "error": self.error,
        }


JOBS: dict[str, ResearchJob] = {}


def create_research_job(topic: str) -> str:
    """Register a new queued research job and return its unique identifier."""
    job_id = str(uuid.uuid4())
    JOBS[job_id] = ResearchJob(job_id=job_id, topic=topic)
    return job_id


async def _publish(job: ResearchJob, event: dict[str, Any]) -> None:
    """Publish a progress event to the job's SSE queue."""
    await job.events.put(event)


async def _stage(job: ResearchJob, name: str, label: str) -> None:
    """Set the current pipeline stage and publish its running status."""
    job.stage = name
    await _publish(job, {"type": "stage", "stage": name, "status": "running", "message": label})


def _last_message_content(result: dict[str, Any]) -> str:
    """Extract the latest assistant message content from a LangChain agent result."""
    messages = result.get("messages", [])
    for message in reversed(messages):
        if getattr(message, "type", "") == "ai":
            content = getattr(message, "content", "")
            if isinstance(content, str):
                return content
            return str(content)
    return "The agent did not return a final text message."


def _extract_urls(text: str) -> list[str]:
    """Return unique HTTP(S) URLs found in search output."""
    urls = re.findall(r"https?://[^\s)\]>\"']+", text)
    return list(dict.fromkeys(url.rstrip(".,;") for url in urls))


async def run_research_job(job_id: str, topic: str) -> None:
    """Run search, reading, writing, and critique stages in a background task."""
    job = JOBS[job_id]
    job.status = "running"
    try:
        await _stage(job, "search", "Searching for relevant web sources")
        search_agent = build_search_agent()
        search_result = await asyncio.to_thread(
            search_agent.invoke,
            {"messages": [("user", f"Find recent, reliable and detailed information about: {topic}. Return source titles, URLs, and evidence snippets.")]},
        )
        job.results["search"] = _last_message_content(search_result)
        await _publish(job, {"type": "stage", "stage": "search", "status": "completed", "result": job.results["search"]})

        await _stage(job, "reader", "Reading a relevant source in more depth")
        urls = _extract_urls(job.results["search"])
        if urls:
            reader_agent = build_reader_agent()
            reader_prompt = (
                f"Research topic: {topic}\nSearch results:\n{job.results['search'][:5000]}\n\n"
                f"Use the scrape_url tool on the most relevant URL from this list: {urls[:5]}. "
                "Summarize the useful content and identify the source URL. Do not invent evidence."
            )
            reader_result = await asyncio.to_thread(
                reader_agent.invoke, {"messages": [("user", reader_prompt)]}
            )
            job.results["reader"] = _last_message_content(reader_result)
        else:
            job.results["reader"] = "No usable URLs were found in the search agent output; the writer will use search snippets only."
        await _publish(job, {"type": "stage", "stage": "reader", "status": "completed", "result": job.results["reader"]})

        await _stage(job, "writer", "Writing the research report")
        combined = (
            f"SEARCH RESULTS:\n{job.results['search']}\n\n"
            f"DETAILED SCRAPED CONTENT:\n{job.results['reader']}"
        )
        writer_chain = build_writer_chain()
        report = await asyncio.to_thread(
            writer_chain.invoke, {"topic": topic, "research": combined}
        )
        job.results["writer"] = report
        await _publish(job, {"type": "stage", "stage": "writer", "status": "completed", "result": report})

        await _stage(job, "critic", "Reviewing evidence and report quality")
        critic_chain = build_critic_chain()
        feedback = await asyncio.to_thread(critic_chain.invoke, {"report": report})
        job.results["critic"] = feedback
        await _publish(job, {"type": "stage", "stage": "critic", "status": "completed", "result": feedback})

        job.status = "completed"
        job.stage = "completed"
        await _publish(job, {"type": "completed", "job": job.public_dict()})
    except Exception as exc:
        job.status = "failed"
        job.error = str(exc)
        await _publish(job, {"type": "failed", "job": job.public_dict(), "message": str(exc)})
