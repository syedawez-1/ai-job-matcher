from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth_utils import get_current_user
from app.database import get_db
from app.models.models import Job, Resume
from app.schemas import JobCreate, JobOut
from app.services.matcher import rank_jobs

router = APIRouter()


@router.post("/", response_model=JobOut)
async def create_job(
    payload: JobCreate,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    job = Job(**payload.model_dump())
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


@router.get("/", response_model=list[JobOut])
async def list_jobs(db: Session = Depends(get_db)):
    """
    Return only currently active jobs.
    Inactive/expired jobs remain in the database for history
    but are not shown to users.
    """
    return (
        db.query(Job)
        .filter(Job.is_active == True)
        .order_by(Job.created_at.desc())
        .all()
    )


@router.get("/matches/{resume_id}")
async def get_matches(
    resume_id: str,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    resume = (
        db.query(Resume)
        .filter(
            Resume.id == resume_id,
            Resume.user_id == user["sub"]
        )
        .first()
    )

    if not resume:
        raise HTTPException(
            status_code=404,
            detail="Resume not found"
        )

    resume_skills = (resume.parsed_data or {}).get("skills", [])

    # Only match the user's resume against active jobs.
    jobs = (
        db.query(Job)
        .filter(Job.is_active == True)
        .all()
    )

    job_dicts = [
    {
        "id": str(j.id),
        "title": j.title,
        "company": j.company,
        "required_skills": j.required_skills or [],
        "source_url": j.source_url,
    }
    for j in jobs
]

    ranked = rank_jobs(resume_skills, job_dicts)

    return {
        "resume_id": resume_id,
        "matches": ranked
    }