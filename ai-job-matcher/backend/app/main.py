from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import auth, resumes, jobs, analysis, applications

app = FastAPI(title="AI Job Matcher API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin, "http://localhost:3000"],
    allow_origin_regex=r"https://ai-job-matcher-o9hz.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(resumes.router, prefix="/resumes", tags=["resumes"])
app.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
app.include_router(analysis.router, prefix="/analysis", tags=["analysis"])
app.include_router(applications.router, prefix="/applications", tags=["applications"])

# Schema is managed by Alembic migrations now (see alembic/), not
# auto-created on startup. Run `alembic upgrade head` before starting
# the server for the first time, and after pulling any new migration.


@app.get("/health")
def health_check():
    return {"status": "ok"}
