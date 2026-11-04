# FreshCheck — AI-powered stale-answer detection

FreshCheck is a hackathon MVP that checks a pasted AI answer against current web evidence retrieved through the Tavily Search API.

## What it does

1. The user pastes an answer they want to verify.
2. The user supplies a focused search query describing the topic or claim.
3. FreshCheck sends that query to Tavily Search.
4. Tavily returns a current search summary and ranked web sources.
5. FreshCheck compares important words in the pasted answer with the retrieved evidence.
6. The UI displays a review signal, source links, publication dates when available, and the retrieval time.

## Important limitation

The current prototype uses a **lexical-overlap heuristic**, not a reasoning model or a formal fact-checking system. A low overlap can indicate a possible mismatch; a high overlap does not prove that a claim is true. Search results can be incomplete, wrong, or out of date. Users must inspect the linked sources before relying on the result.

The project intentionally displays this limitation rather than pretending that a simple prototype can establish truth.

## Tech stack

- Python 3.11+
- FastAPI
- HTTPX
- Tavily Search API
- HTML, CSS and vanilla JavaScript

## Run locally

### 1. Clone the repository

    git clone https://github.com/sudarshan237/freshcheck.git
    cd freshcheck

### 2. Create and activate a virtual environment

Windows PowerShell:

    py -m venv .venv
    .venv\Scripts\Activate.ps1

macOS / Linux:

    python3 -m venv .venv
    source .venv/bin/activate

### 3. Install dependencies

    pip install -r requirements.txt

### 4. Configure Tavily

Create a file named .env in the project root and add:

    TAVILY_API_KEY=your_tavily_api_key

Get an API key from the Tavily developer dashboard. Never commit your real API key. The .env file is ignored by Git.

### 5. Start the app

    uvicorn app:app --reload

Open http://127.0.0.1:8000 in your browser.

## Run tests

    pip install -r requirements-dev.txt
    pytest

## Example

- Answer to check: Python 3.10 is the latest stable Python release.
- Search query: latest stable Python release

FreshCheck retrieves current search evidence and shows the search summary alongside sources. The comparison signal is a heuristic; inspect the sources to decide whether the pasted answer needs updating.

## API

### POST /api/check

Request JSON:

    {
      "answer": "The answer to check goes here.",
      "query": "A focused web search query"
    }

Response fields include:

- verdict: comparison signal
- reason: explanation of the heuristic result
- overlap_score: lexical overlap score from 0 to 1
- current_summary: Tavily's generated search summary, when available
- sources: ranked source title, URL, snippet, score and publication date
- checked_at: UTC timestamp for this search
- disclaimer: important interpretation guidance

### GET /health

Returns a simple health status.

## Project structure

    .
    ├── app.py
    ├── freshness.py
    ├── static/
    │   └── index.html
    ├── tests/
    │   └── test_freshness.py
    ├── .env.example
    ├── .gitignore
    ├── requirements.txt
    └── requirements-dev.txt

## Current scope and next steps

Current MVP:
- Answer and query input
- Tavily-powered web retrieval
- Heuristic comparison signal
- Source links, snippets and dates when available
- Explicit uncertainty and limitations
- Basic unit tests

Possible next iterations:
- Extract multiple atomic claims from a long answer
- Verify claims individually instead of comparing one whole answer
- Add an LLM-based semantic verifier with evidence-grounded explanations
- Prefer authoritative sources for domains such as official documentation
- Add an evaluation dataset with labelled stale, current and conflicting examples

## Security and privacy

- The Tavily API key is read from an environment variable.
- The app does not persist submitted answers or search results.
- Do not paste private, confidential or personally identifying information into the demo.

## Hackathon

Primary problem statement: **Stale-Answer Detector**  
Project: **FreshCheck — AI-powered stale-answer detection**  
Tavily is used as the live web retrieval layer.
