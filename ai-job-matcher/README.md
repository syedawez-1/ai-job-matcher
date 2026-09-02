# AI Job Matcher

An AI-powered platform that parses your resume, analyzes skill gaps against real job postings, and gives personalized recommendations — plus an ATS resume analyzer and application tracker.

## 30-Day Build Plan

| Days | Milestone |
|---|---|
| 1–3 | Project setup + GitHub + Next.js + FastAPI |
| 4–7 | User authentication + resume PDF upload |
| 8–12 | Resume parser → skills, education, projects, experience |
| 13–17 | Job database + job matching algorithm |
| 18–21 | AI skill-gap analysis + personalized recommendations |
| 22–24 | AI resume/ATS analyzer |
| 25–27 | Dashboard + application tracker |
| 28–29 | Docker + testing + deployment |
| 30 | README + architecture diagram + demo video + polishing |

## Tech Stack

- **Frontend:** Next.js (App Router) + Tailwind CSS, hosted on Vercel
- **Backend:** FastAPI, hosted on Railway/Render
- **Auth:** NextAuth.js, JWT verified by FastAPI
- **Database:** PostgreSQL (Supabase)
- **File storage:** Supabase Storage (resume PDFs)
- **AI:** Claude/OpenAI API called server-side from FastAPI
- **Resume parsing:** pdfplumber/pymupdf + LLM structuring

## Project Structure

```
ai-job-matcher/
├── frontend/          # Next.js app
│   ├── app/           # App Router pages
│   ├── components/    # React components
│   └── lib/           # API client, auth helpers
├── backend/           # FastAPI app
│   ├── app/
│   │   ├── routers/   # API route handlers
│   │   ├── models/    # SQLAlchemy models
│   │   └── services/  # Resume parsing, AI calls, matching logic
│   └── alembic/       # DB migrations
└── docker-compose.yml
```

## Getting Started

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env      # fill in your DB and API keys
alembic upgrade head      # creates all tables
uvicorn app.main:app --reload
```

Backend runs at `http://localhost:8000` (docs at `/docs`). Schema is
managed by Alembic (`alembic/`, wired to the models in
`app/models/models.py` via `alembic/env.py`) — `alembic upgrade head`
applies the initial migration that creates `users`, `resumes`, `jobs`,
and `applications`.

**When you change a model later:** edit `app/models/models.py`, then run
```bash
alembic revision --autogenerate -m "describe your change"
alembic upgrade head
```
This only works from inside `backend/` (where `alembic.ini` lives) with
your `.env` pointing at a real, reachable database — `env.py` reads
`DATABASE_URL` from there.

Seed a few demo jobs so matching/skill-gap has data to work with:

```bash
python -m app.seed_jobs
```

### Frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local  # fill in your values
npm run dev
```

Frontend runs at `http://localhost:3000`.

### Try it end to end

1. Go to `http://localhost:3000/register`, create an account
2. On the dashboard, upload a PDF resume — it's parsed automatically (skills, education, experience)
3. Click "See matching jobs" to view ranked matches against the seeded jobs
4. Click "Analyze skill gap" on any job for AI-generated missing skills + recommendations
5. Click "Track application" to add it to your tracker, then manage status at `/applications`

### Environment variables you'll need

- Supabase project URL + service key (DB, storage)
- NextAuth secret + OAuth provider keys (if using Google login)
- Anthropic or OpenAI API key (server-side only, backend `.env`)

## Deployment

- Frontend → Vercel
- Backend → Railway or Render (Docker)
- Database + storage → Supabase

## Architecture Diagram

_Add on Day 30._

## Demo

_Add demo video link on Day 30._
