from app.database import SessionLocal
from app.models.models import Job
from app.config import settings
from google import genai
from sqlalchemy.orm.attributes import flag_modified
import time
import json

MODEL = "gemini-flash-lite-latest"

# Process only 5 jobs per run to stay safely within Gemini limits
MAX_ATTEMPTS = 5

# Wait between Gemini requests
DELAY_SECONDS = 15

client = genai.Client(api_key=settings.gemini_api_key)


def extract_skills(job):
    prompt = f"""
Extract the most important technical and professional skills required
for this job.

Job title:
{job.title}

Company:
{job.company}

Job description:
{job.description}

Return ONLY a JSON array of skill names.

Example:
["Python", "FastAPI", "PostgreSQL", "Docker"]

Do not include explanations.
"""

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt
    )

    text = response.text.strip()

    if text.startswith("```"):
        text = text.replace("```json", "")
        text = text.replace("```", "")
        text = text.strip()

    skills = json.loads(text)

    if not isinstance(skills, list):
        raise ValueError("Gemini did not return a JSON array")

    return skills


db = SessionLocal()

try:
    jobs = (
        db.query(Job)
        .filter(Job.is_active == True)
        .all()
    )

    missing = [
        job for job in jobs
        if not job.required_skills
    ]

    batch = missing[:MAX_ATTEMPTS]

    print("=" * 60)
    print("AI JOB MATCHER - SKILL EXTRACTION")
    print("=" * 60)
    print(f"Active jobs: {len(jobs)}")
    print(f"Active jobs without skills: {len(missing)}")
    print(f"This run will process: {len(batch)}")
    print(f"Gemini model: {MODEL}")
    print("=" * 60)

    updated = 0
    failed = 0

    for index, job in enumerate(batch, start=1):

        print(f"\n[{index}/{len(batch)}] {job.title}")

        try:
            skills = extract_skills(job)

            job.required_skills = skills
            flag_modified(job, "required_skills")

            db.commit()

            updated += 1

            print(f"SUCCESS: {skills}")

        except Exception as e:

            db.rollback()

            failed += 1

            print(f"FAILED: {e}")

            error_text = str(e).lower()

            if (
                "429" in error_text
                or "quota" in error_text
                or "resource_exhausted" in error_text
                or "rate limit" in error_text
            ):
                print("\nGemini quota/rate limit reached.")
                print("Stopping this run.")
                break

        if index < len(batch):
            print(f"Waiting {DELAY_SECONDS} seconds...")
            time.sleep(DELAY_SECONDS)

    remaining = (
        db.query(Job)
        .filter(
            Job.is_active == True,
            Job.required_skills == None
        )
        .count()
    )

    print("\n" + "=" * 60)
    print("FINISHED")
    print(f"Updated: {updated}")
    print(f"Failed: {failed}")
    print("=" * 60)

finally:
    db.close()