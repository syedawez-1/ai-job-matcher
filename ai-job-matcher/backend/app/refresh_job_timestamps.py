from datetime import datetime, timezone

from app.database import SessionLocal
from app.models.models import Job


def main():
    db = SessionLocal()

    try:
        jobs = db.query(Job).all()

        now = datetime.now(timezone.utc)

        for job in jobs:
            job.last_seen_at = now
            job.is_active = True

        db.commit()

        print(f"Successfully refreshed {len(jobs)} jobs.")
        print(f"All jobs are now active.")
        print(f"last_seen_at set to: {now}")

    except Exception as e:
        db.rollback()
        print(f"Error: {e}")

    finally:
        db.close()


if __name__ == "__main__":
    main()