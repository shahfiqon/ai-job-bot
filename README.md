# Job Apply Assistant Bot

An automated job application system that scrapes jobs, enriches them with external data, and generates tailored application materials.

## Monorepo Layout
- `jobspy/` – core scraping library originally shipped with this repository
- `backend/` – new FastAPI service that orchestrates scraping, enrichment, and workflow automation
- `backend/cli/` – Typer + Rich command-line tools for scraping jobs and enriching company data
- `frontend/` – planned Next.js dashboard (coming soon)
- `notebooks/` – Jupyter explorations such as Proxycurl integration prototypes
- `scrape_jobs.py` – legacy helper script that exercises the jobspy library

## Quick Start
- Backend API: see `backend/README.md` for PDM setup, `.env` configuration, and local server instructions
- CLI scraping: `cd backend && pdm run jobbot scrape --search-term "software engineer" --location "San Francisco" --results-wanted 10`
- Frontend: placeholder until the Next.js app lands in later phases
- JobSpy tooling: continue using `requirements.txt` or Poetry config from the repo root

## Architecture

This system consists of three cooperating layers: job scraping (JobSpy), backend APIs (FastAPI + PostgreSQL), and a forthcoming frontend for human review. Data flows from external job boards into our database, enriched with Proxycurl where needed, before reaching the UI.

```mermaid
%%{init: {
  "theme": "base",
  "themeVariables": {
    "primaryColor": "#EEF2FF",
    "primaryTextColor": "#111827",
    "primaryBorderColor": "#6366F1",
    "lineColor": "#94A3B8",
    "fontSize": "14px",
    "fontFamily": "Inter, ui-sans-serif, system-ui"
  }
}}%%
flowchart LR
  %% LAYOUT
  %% Sources on left -> ETL/LLM center -> DB right
  %% ----------------------------------------------------------------
  subgraph S[🔎 Sources]
    direction TB
    A[LinkedIn]:::source
    B[Indeed]:::source
    C[ZipRecruiter]:::source
    D[Other Boards]:::source
  end

  subgraph P[⚙️ Pipeline]
    direction LR
    E([Step 1 · Scrape Listings]):::step
    F([Step 2 · Extract Job Info · LLM]):::llm
    G[(Step 3 · Job DB)]:::db
    H([Step 4 · Filter Jobs · LLM]):::llm
    J([Step 5 · Write Tailored Resume · LLM + JsonResume]):::llm
    K([Step 6 · Store Tailored Resume]):::step
  end

  subgraph R[🧰 Resume Inputs]
    direction TB
    I[Base Resume]:::input
  end

  %% FLOWS
  A --> E
  B --> E
  C --> E
  D --> E

  E --> F
  F -->|structured fields| G

  G --> H
  I --> H
  H --> J
  J -->|tailored resume| K
  K --> G

  %% STYLES
  classDef source fill:#F0F9FF,stroke:#38BDF8,stroke-width:1px,color:#0C4A6E;
  classDef step fill:#EEF2FF,stroke:#6366F1,stroke-width:1px,color:#111827;
  classDef llm fill:#FFF7ED,stroke:#FB923C,stroke-width:1px,color:#7C2D12;
  classDef db fill:#ECFDF5,stroke:#34D399,stroke-width:1px,color:#064E3B;
  classDef input fill:#FAF5FF,stroke:#A78BFA,stroke-width:1px,color:#3730A3;
```

## JobSpy Library & Legacy Script

The `scrape_jobs.py` script scrapes job postings from LinkedIn using the [JobSpy library](https://github.com/speedyapply/JobSpy).

**Run the scraper:**

```bash
python scrape_jobs.py
```

**Configuration:**

The script ships with these defaults:
- **Search Term:** "software engineer"
- **Location:** "San Francisco, CA"
- **Number of Results:** 50 jobs
- **Output File:** `jobs.csv`

Update the variables in `scrape_jobs.py` to customize:

```python
search_term = "your job title"
location = "your location"
results_wanted = 50
```

**Output:**

`jobs.csv` will contain job metadata such as titles, employers, locations, salary hints, descriptions, and URLs.

**Important Notes:**
- LinkedIn can rate-limit repeated scrapes. Add delays or proxies as needed.
- The script sets `linkedin_fetch_description=True`, increasing the number of LinkedIn requests.

## Resources

- [JSON Resume](https://docs.jsonresume.org/)

## Backend

### CLI Tools
The backend ships with a Typer-powered CLI (`pdm run jobbot`) that scrapes LinkedIn via JobSpy, enriches companies using Proxycurl, and writes everything to PostgreSQL with Rich-powered progress bars. See [backend/README.md](backend/README.md#cli-tools) for full usage instructions.

Key features:
- Scrapes jobs using the `python-jobspy` library
- Enriches LinkedIn companies through the Proxycurl API
- Deduplicates companies by LinkedIn URL and jobs by `job_url`
- Presents colorful status updates, progress bars, and a summary table in the terminal
