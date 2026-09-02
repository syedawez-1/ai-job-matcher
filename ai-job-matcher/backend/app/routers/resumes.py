"""
Resume upload + parsing.

Files are saved to local disk under storage/resumes/ by default, which
is enough to build and demo the whole flow. Swap save_upload() for a
Supabase Storage call when you're ready to deploy (see README).
"""

import os
import uuid

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session

from app.auth_utils import get_current_user
from app.database import get_db
from app.models.models import Resume
from app.schemas import ResumeOut
from app.services.resume_parser import parse_resume

router = APIRouter()

STORAGE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "storage", "resumes")
os.makedirs(STORAGE_DIR, exist_ok=True)


def save_upload(file: UploadFile) -> str:
    ext = os.path.splitext(file.filename)[1] or ".pdf"
    filename = f"{uuid.uuid4()}{ext}"
    path = os.path.join(STORAGE_DIR, filename)
    with open(path, "wb") as f:
        f.write(file.file.read())
    return path


@router.post("/upload", response_model=ResumeOut)
async def upload_resume(
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    path = save_upload(file)

    try:
        parsed = parse_resume(path)
    except Exception as e:
        parsed = {"error": f"Parsing failed: {str(e)}"}

    resume = Resume(
        user_id=user["sub"],
        storage_path=path,
        parsed_data=parsed,
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)
    return resume


@router.get("/", response_model=list[ResumeOut])
async def list_resumes(user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Resume).filter(Resume.user_id == user["sub"]).order_by(Resume.uploaded_at.desc()).all()


@router.get("/{resume_id}", response_model=ResumeOut)
async def get_resume(resume_id: str, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    resume = db.query(Resume).filter(Resume.id == resume_id, Resume.user_id == user["sub"]).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    return resume
