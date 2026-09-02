"""
Seed a handful of demo jobs so job matching/skill-gap features have
something to work against without needing a real job-board integration.

Run with: python -m app.seed_jobs
"""

from app.database import SessionLocal, Base, engine
from app.models.models import Job

DEMO_JOBS = [
    {
        "title": "Frontend Engineer",
        "company": "Acme Corp",
        "description": "Build and maintain our Next.js-based web app.",
        "required_skills": ["javascript", "react", "next.js", "css", "typescript"],
    },
    {
        "title": "Backend Engineer",
        "company": "DataFlow Inc",
        "description": "Design and scale our FastAPI + Postgres backend.",
        "required_skills": ["python", "fastapi", "postgresql", "docker", "sql"],
    },
    {
        "title": "Full Stack Developer",
        "company": "Startly",
        "description": "Own features end to end across our Next.js/FastAPI stack.",
        "required_skills": ["react", "python", "fastapi", "javascript", "postgresql"],
    },
    {
        "title": "Machine Learning Engineer",
        "company": "NeuralWorks",
        "description": "Build ML pipelines and integrate LLMs into product features.",
        "required_skills": ["python", "pytorch", "llm", "machine learning", "sql"],
    },
    {
        "title": "DevOps Engineer",
        "company": "CloudBase",
        "description": "Own our CI/CD, Docker, and cloud infrastructure.",
        "required_skills": ["docker", "kubernetes", "aws", "ci/cd", "linux"],
    },
]


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        existing_titles = {j.title for j in db.query(Job).all()}
        added = 0
        for job_data in DEMO_JOBS:
            if job_data["title"] in existing_titles:
                continue
            db.add(Job(**job_data))
            added += 1
        db.commit()
        print(f"Seeded {added} new job(s).")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
