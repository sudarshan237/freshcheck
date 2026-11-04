from datetime import datetime, timezone
import os
from typing import Any

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from freshness import assess_answer

load_dotenv()

TAVILY_SEARCH_URL = "https://api.tavily.com/search"
MAX_RESULTS = 5

app = FastAPI(
    title="FreshCheck API",
    description="Check a pasted answer against current web evidence using Tavily.",
    version="0.1.0",
)

app.mount("/static", StaticFiles(directory="static"), name="static")


class CheckRequest(BaseModel):
    answer: str = Field(min_length=20, max_length=8000)
    query: str | None = Field(default=None, max_length=300)


@app.get("/", include_in_schema=False)
async def home() -> FileResponse:
    return FileResponse("static/index.html")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "freshcheck"}


def _clean_sources(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    sources: list[dict[str, Any]] = []
    for item in results[:MAX_RESULTS]:
        url = item.get("url")
        if not isinstance(url, str) or not url.startswith(("https://", "http://")):
            continue
        sources.append(
            {
                "title": str(item.get("title") or "Untitled source")[:300],
                "url": url,
                "snippet": str(item.get("content") or "")[:1200],
                "score": item.get("score"),
                "published_date": item.get("published_date") or item.get("publishedDate"),
            }
        )
    return sources


@app.post("/api/check")
async def check_answer(payload: CheckRequest) -> dict[str, Any]:
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="TAVILY_API_KEY is missing. Add it to your .env file and restart FreshCheck.",
        )

    answer = payload.answer.strip()
    query = (payload.query or "").strip() or answer[:250]
    if len(answer) < 20:
        raise HTTPException(status_code=422, detail="Please enter an answer with at least 20 characters.")
    if not query:
        raise HTTPException(status_code=422, detail="Please enter a search query.")

    request_body = {
        "query": query,
        "search_depth": "basic",
        "max_results": MAX_RESULTS,
        "include_answer": "basic",
        "include_raw_content": False,
    }

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(25.0, connect=8.0)) as client:
            response = await client.post(
                TAVILY_SEARCH_URL,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json=request_body,
            )
            response.raise_for_status()
            data = response.json()
    except httpx.TimeoutException as exc:
        raise HTTPException(status_code=504, detail="Tavily search timed out. Please try again.") from exc
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code in (401, 403):
            detail = "Tavily rejected the API key. Check that TAVILY_API_KEY is valid."
        elif exc.response.status_code == 429:
            detail = "Tavily rate limit or credit limit reached. Try again later or check your Tavily account."
        else:
            detail = f"Tavily returned an error (HTTP {exc.response.status_code})."
        raise HTTPException(status_code=502, detail=detail) from exc
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail="Could not connect to Tavily. Check your internet connection.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=502, detail="Tavily returned an unreadable response.") from exc

    results = data.get("results") or []
    current_summary = str(data.get("answer") or "").strip()
    if not current_summary:
        current_summary = "Tavily did not return a generated summary. Review the source snippets below."

    verdict = assess_answer(answer, current_summary, results)
    return {
        **verdict,
        "current_summary": current_summary,
        "sources": _clean_sources(results),
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "search_query": query,
        "disclaimer": (
            "This prototype uses keyword overlap as a screening heuristic, not semantic fact verification. "
            "A high score does not prove correctness. Read the linked sources before relying on the result."
        ),
    }
