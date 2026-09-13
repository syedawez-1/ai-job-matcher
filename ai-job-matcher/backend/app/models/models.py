import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    String,
    DateTime,
    ForeignKey,
    Text,
    JSON,
    Boolean,
)
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    email = Column(
        String,
        unique=True,
        nullable=False,
    )

    name = Column(String)

    password_hash = Column(
        String,
        nullable=False,
    )

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )


class Resume(Base):
    __tablename__ = "resumes"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )

    storage_path = Column(
        String,
        nullable=False,
    )

    parsed_data = Column(
        JSON
    )  # skills, education, projects, experience

    uploaded_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )


class Job(Base):
    __tablename__ = "jobs"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    title = Column(
        String,
        nullable=False,
    )

    company = Column(String)

    description = Column(Text)

    required_skills = Column(JSON)

    source_url = Column(
        String,
        unique=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    # Job synchronization fields
    last_seen_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
    )

    expires_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )


class Application(Base):
    __tablename__ = "applications"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )

    job_id = Column(
        UUID(as_uuid=True),
        ForeignKey("jobs.id"),
        nullable=False,
    )

    status = Column(
        String,
        default="applied",
    )  # applied, interviewing, offer, rejected

    applied_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    notes = Column(Text)