# candid.

A resume-to-job matching system. Upload CVs once, store structured data in Postgres, rank candidates against job descriptions using SQL scoring.

Built with FastAPI, PostgreSQL, and Groq (`llama-3.3-70b-versatile`). No vector DB — matching is a structured extraction problem, not a semantic similarity one.

---

## How it works

1. **Upload resumes** via drag-and-drop. Each PDF is parsed with pdfplumber, then sent to Groq to extract name, email, skills, experience, and education — stored in Postgres.
2. **Paste a job description** or natural language query. Groq extracts required and nice-to-have skills with weights.
3. **SQL scoring** via `CROSS JOIN` ranks every candidate against the job. Candidates below 25% match are filtered out.
4. **Click any result** to open a detail drawer with an AI recruiter note, matched/missing skills, experience, and education.

## Scoring

- `match_percentage` = required skills matched / total required × 100
- `skill_score` = sum of weights of all matched skills (required + nice-to-have)
- Candidates below 25% are excluded

## Stack

| Layer | Tech |
|---|---|
| Backend | FastAPI + SQLAlchemy |
| Database | PostgreSQL |
| LLM | Groq `llama-3.3-70b-versatile` |
| PDF parsing | pdfplumber |
| Frontend | Vanilla HTML/CSS/JS |
| Package manager | uv |
| Migrations | Alembic |

## Project structure

```
resume-filtering-system/
  ingestion/
    parser.py        # pdfplumber -> raw text + MD5 hash
    extractor.py     # Groq -> structured JSON from resume
    loader.py        # structured JSON -> Postgres
    jd_extractor.py  # Groq -> structured skills from JD
  matching/
    scorer.py        # SQL scoring query
    ranker.py        # filters <25%, sorts by match %
  models/
    orm.py           # SQLAlchemy table definitions
  api/
    routes.py        # FastAPI endpoints
  frontend/
    index.html / style.css / app.js
  alembic/           # migrations
  config.py          # reads .env
  ingest.py          # CLI: load a single resume
  create_job.py      # CLI: create a job manually
```

## Setup

**Prerequisites:** Python 3.11+, PostgreSQL, a [Groq API key](https://console.groq.com)

```bash
git clone https://github.com/aditsawhney/resume-filtering-system.git
cd resume-filtering-system
uv sync

cp .env.example .env
# fill in DATABASE_URL and GROQ_API_KEY

uv run alembic upgrade head
uv run uvicorn api.routes:app --reload
```

Open `http://127.0.0.1:8000`.

## Environment variables

```
DATABASE_URL=postgresql://user:password@localhost/resume_matcher
GROQ_API_KEY=your_key_here
```

## API

```
POST /candidates              # upload resume PDF
GET  /candidates              # list all candidates
GET  /candidates/{id}         # full candidate detail
POST /candidates/{id}/summary # AI recruiter note
POST /jobs/parse              # extract skills from JD text
POST /jobs                    # create job record
GET  /jobs                    # list all jobs
GET  /jobs/{id}/matches       # ranked candidates for a job
```

---

Built by [Adit Sawhney](https://github.com/aditsawhney)