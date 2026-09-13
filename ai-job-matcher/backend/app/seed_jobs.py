"""
One-off / rerunnable script to seed the jobs table with real listings
pulled from the free Arbeitnow Job Board API.

Run from the backend/ folder with the venv active:
    python app\seed_jobs.py
"""

import re
import sys
import time

import requests
from sqlalchemy.orm.attributes import flag_modified

sys.path.insert(0, ".")

from app.database import SessionLocal
from app.models.models import Job
from app.services.ai_client import extract_job_required_skills


ARBEITNOW_URL = "https://www.arbeitnow.com/api/job-board-api"
MAX_JOBS = 30


def strip_html(text: str) -> str:
    """Remove HTML tags and clean extra whitespace."""
    text = re.sub(r"<[^>]+>", " ", text or "")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def main():
    print("Fetching jobs from Arbeitnow...")

    resp = requests.get(ARBEITNOW_URL, timeout=15)
    resp.raise_for_status()

    jobs_data = resp.json().get("data", [])[:MAX_JOBS]

    print(f"Got {len(jobs_data)} jobs to process.")

    db = SessionLocal()

    inserted = 0
    skipped = 0
    retried = 0
    updated = 0

    try:
        for i, job in enumerate(jobs_data, start=1):

            title = job.get("title", "").strip()
            company = job.get("company_name", "").strip()
            url = job.get("url", "")
            raw_description = job.get("description", "")

            if not title or not url:
                skipped += 1
                continue

            # Check whether this job already exists
            existing = db.query(Job).filter(Job.source_url == url).first()

            # ---------------------------------------------------------
            # EXISTING JOB
            # ---------------------------------------------------------
            if existing:

                # Job already has skills -> leave it untouched
                if existing.required_skills:
                    print(
                        f"[{i}/{len(jobs_data)}] "
                        f"Skipping (skills already exist): {title}"
                    )
                    skipped += 1
                    continue

                # Job exists but has no skills -> retry AI extraction
                print(
                    f"[{i}/{len(jobs_data)}] "
                    f"Retrying skills for: {title} @ {company}"
                )

                retried += 1

                description = strip_html(raw_description)

                try:
                    required_skills = extract_job_required_skills(
                        title,
                        description
                    )

                    if required_skills:
                        existing.required_skills = required_skills

                        # Tell SQLAlchemy the JSON field changed
                        flag_modified(existing, "required_skills")

                        db.commit()

                        updated += 1

                        print(
                            f"    -> Skills updated: {required_skills}"
                        )
                    else:
                        print(
                            "    -> Gemini returned no skills."
                        )

                except Exception as e:
                    db.rollback()

                    print(
                        f"    -> Gemini extraction failed: {e}"
                    )

                # Wait between Gemini requests
                time.sleep(3)

                continue

            # ---------------------------------------------------------
            # NEW JOB
            # ---------------------------------------------------------

            description = strip_html(raw_description)

            print(
                f"[{i}/{len(jobs_data)}] "
                f"Extracting skills for: {title} @ {company}"
            )

            try:
                required_skills = extract_job_required_skills(
                    title,
                    description
                )

            except Exception as e:
                print(
                    f"    -> Gemini extraction failed, "
                    f"adding job without skills: {e}"
                )

                required_skills = []

            job_row = Job(
                title=title,
                company=company or "Unknown",
                description=description[:2000],
                required_skills=required_skills,
                source_url=url,
            )

            db.add(job_row)
            db.commit()

            inserted += 1

            print(
                f"    -> Job inserted. Skills: {required_skills}"
            )

            # Wait between Gemini requests
            time.sleep(3)

        print("\n----------------------------------------")
        print("Done.")
        print(f"New jobs inserted: {inserted}")
        print(f"Existing jobs skipped: {skipped}")
        print(f"Jobs retried for skills: {retried}")
        print(f"Jobs successfully updated: {updated}")
        print("----------------------------------------")

    finally:
        db.close()


if __name__ == "__main__":
    main()