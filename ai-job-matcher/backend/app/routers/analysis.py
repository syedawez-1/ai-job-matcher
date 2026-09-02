from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth_utils import get_current_user
from app.database import get_db
from app.models.models import Resume, Job
from app.services import ai_client

router = APIRouter()


@router.get("/skill-gap/{resume_id}/{job_id}")
async def skill_gap(resume_id: str, job_id: str, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    resume = db.query(Resume).filter(Resume.id == resume_id, Resume.user_id == user["sub"]).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    resume_skills = (resume.parsed_data or {}).get("skills", [])
    result = ai_client.analyze_skill_gap(resume_skills, job.required_skills or [])
    return {"resume_id": resume_id, "job_id": job_id, **result}


@router.get("/ats-score/{resume_id}")
async def ats_score(resume_id: str, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    resume = db.query(Resume).filter(Resume.id == resume_id, Resume.user_id == user["sub"]).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    raw_text = (resume.parsed_data or {}).get("raw_text", "")
    if not raw_text:
        raise HTTPException(status_code=400, detail="No parsed text available for this resume")

    result = ai_client.score_ats(raw_text)
    return {"resume_id": resume_id, **result}
