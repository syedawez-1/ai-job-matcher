from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth_utils import get_current_user
from app.database import get_db
from app.models.models import Application
from app.schemas import ApplicationCreate, ApplicationUpdate, ApplicationOut

router = APIRouter()


@router.post("/", response_model=ApplicationOut)
async def create_application(
    payload: ApplicationCreate,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    application = Application(user_id=user["sub"], **payload.model_dump())
    db.add(application)
    db.commit()
    db.refresh(application)
    return application


@router.get("/", response_model=list[ApplicationOut])
async def list_applications(user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return (
        db.query(Application)
        .filter(Application.user_id == user["sub"])
        .order_by(Application.applied_at.desc())
        .all()
    )


@router.patch("/{application_id}", response_model=ApplicationOut)
async def update_application(
    application_id: str,
    payload: ApplicationUpdate,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    application = (
        db.query(Application)
        .filter(Application.id == application_id, Application.user_id == user["sub"])
        .first()
    )
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(application, field, value)

    db.commit()
    db.refresh(application)
    return application


@router.delete("/{application_id}")
async def delete_application(application_id: str, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    application = (
        db.query(Application)
        .filter(Application.id == application_id, Application.user_id == user["sub"])
        .first()
    )
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    db.delete(application)
    db.commit()
    return {"status": "deleted"}
