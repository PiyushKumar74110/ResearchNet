"""Test lightweight pipeline utilities without making external API calls."""

from app.services.pipeline import _extract_urls, create_research_job


def test_extract_urls_deduplicates_and_trims_punctuation():
    """Verify URL extraction removes duplicates and trailing punctuation."""
    assert _extract_urls("See https://example.com/a, then https://example.com/a.") == [
        "https://example.com/a",
    ]


def test_create_research_job_registers_queued_job():
    """Verify new jobs are stored with queued status."""
    from app.services.pipeline import JOBS

    job_id = create_research_job("Test research topic")
    assert JOBS[job_id].status == "queued"
    assert JOBS[job_id].topic == "Test research topic"
