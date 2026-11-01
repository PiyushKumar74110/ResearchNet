"""Provide Tavily search and guarded webpage extraction tools."""

import ipaddress
import os
import socket
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from langchain.tools import tool
from tavily import TavilyClient

from app.core.config import settings


def _get_tavily_client() -> TavilyClient:
    """Create a Tavily client when a search call is made."""
    api_key = settings.tavily_api_key or os.getenv("TAVILY_API_KEY", "")
    if not api_key:
        raise RuntimeError("TAVILY_API_KEY is missing. Add it to backend/.env.")
    return TavilyClient(api_key=api_key)


@tool
def web_search(query: str) -> str:
    """Search the web for relevant information and return titles, URLs, and snippets."""
    response = _get_tavily_client().search(query=query, max_results=5)
    results = response.get("results", response.get("result", []))
    if not results:
        return "No search results were returned."
    output = []
    for result in results:
        output.append(
            f"Title: {result.get('title', 'Untitled')}\n"
            f"URL: {result.get('url', '')}\n"
            f"Snippet: {str(result.get('content', ''))[:500]}"
        )
    return "\n\n---\n\n".join(output)


def _validate_public_http_url(url: str) -> None:
    """Reject unsupported URL schemes and obvious private or local network targets."""
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("Only absolute HTTP or HTTPS URLs can be scraped.")
    hostname = parsed.hostname.lower()
    if hostname in {"localhost", "localhost.localdomain"} or hostname.endswith(".local"):
        raise ValueError("Local hostnames cannot be scraped.")
    try:
        addresses = socket.getaddrinfo(hostname, parsed.port or (443 if parsed.scheme == "https" else 80))
        for address in addresses:
            ip = ipaddress.ip_address(address[4][0])
            if not ip.is_global:
                raise ValueError("Private or non-public network addresses cannot be scraped.")
    except socket.gaierror as exc:
        raise ValueError("The source hostname could not be resolved.") from exc


@tool
def scrape_url(url: str) -> str:
    """Extract readable text from a public HTTP or HTTPS webpage."""
    try:
        _validate_public_http_url(url)
        response = requests.get(
            url,
            timeout=10,
            headers={"User-Agent": "ResearchMind/1.0 (research reader)"},
            allow_redirects=False,
        )
        response.raise_for_status()
        content_type = response.headers.get("content-type", "")
        if "text/html" not in content_type.lower():
            return f"Skipped non-HTML source (content type: {content_type or 'unknown'})."
        soup = BeautifulSoup(response.text, "html.parser")
        for tag in soup(["script", "style", "footer", "nav", "header", "noscript", "form"]):
            tag.decompose()
        text = soup.get_text(separator=" ", strip=True)
        return text[:8000] or "No readable text was found on this page."
    except Exception as exc:
        return f"Could not scrape URL: {exc}"
