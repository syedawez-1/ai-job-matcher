"""
Automatic job synchronization + AI skill extraction.

Maintains a maximum of 500 ACTIVE jobs based on
the jobs currently available from Arbeitnow.

Behavior:
- New online job -> INSERT + ACTIVE
- Existing online job -> UPDATE + ACTIVE
- Job no longer available -> INACTIVE
- Only the first 500 current source listings remain ACTIVE
- Older/inactive records remain in the database
- Active jobs without skills -> Gemini extracts skills
- Jobs whose description/title changes -> skills are regenerated
- Jobs that already have valid skills -> Gemini is NOT called again
- Gemini quota/rate-limit errors stop only skill extraction
- Next refresh continues processing remaining jobs

Run from backend/:

    python -m app.sync_jobs
"""

import re
import json
import time
from datetime import datetime, timezone

import requests
from google import genai
from sqlalchemy.orm.attributes import flag_modified

from app.database import SessionLocal
from app.models.models import Job
from app.config import settings


# ============================================================
# CONFIGURATION
# ============================================================

ARBEITNOW_URL = "https://www.arbeitnow.com/api/job-board-api"

# Maximum number of ACTIVE jobs.
MAX_ACTIVE_JOBS = 500

# Maximum pages allowed when scanning Arbeitnow.
# This protects the application if pagination breaks.
MAX_PAGES = 100

# Delay between Arbeitnow API requests.
SOURCE_DELAY = 1

# Delay between Gemini requests.
#
# 15 seconds = approximately 4 requests/minute,
# which is safer for the Gemini free-tier rate limit.
GEMINI_DELAY = 15

# Gemini model used for skill extraction.
GEMINI_MODEL = "gemini-flash-lite-latest"


# ============================================================
# GEMINI CLIENT
# ============================================================

gemini_client = genai.Client(
    api_key=settings.gemini_api_key
)


# ============================================================
# HELPERS
# ============================================================

def strip_html(text: str) -> str:
    """
    Remove HTML tags and normalize whitespace.
    """

    text = re.sub(
        r"<[^>]+>",
        " ",
        text or ""
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    ).strip()

    return text


# ============================================================
# FETCH CURRENT JOBS
# ============================================================

def fetch_jobs():
    """
    Fetch all currently available jobs from Arbeitnow.

    We continue until the API naturally returns no jobs.

    This is important because we only deactivate old jobs
    after a COMPLETE source scan.

    Returns:
        all_jobs
        scan_successful
    """

    all_jobs = []
    seen_urls = set()

    print(
        "Fetching currently available jobs from Arbeitnow..."
    )

    print("-" * 60)

    for page in range(1, MAX_PAGES + 1):

        try:

            print(
                f"Fetching page {page}..."
            )

            response = requests.get(
                ARBEITNOW_URL,
                params={"page": page},
                timeout=20,
            )

            response.raise_for_status()

            payload = response.json()

            page_jobs = payload.get(
                "data",
                []
            )

            # =================================================
            # NATURAL END OF SOURCE
            # =================================================

            if not page_jobs:

                print(
                    "No more jobs returned by the API."
                )

                print(
                    f"Total unique jobs found: "
                    f"{len(all_jobs)}"
                )

                return all_jobs, True

            added_this_page = 0

            for job in page_jobs:

                url = (
                    job.get("url") or ""
                ).strip()

                if not url:
                    continue

                if url in seen_urls:
                    continue

                seen_urls.add(url)

                all_jobs.append(job)

                added_this_page += 1

            print(
                f"Page {page}: "
                f"received {len(page_jobs)} jobs, "
                f"total unique: {len(all_jobs)}"
            )

            # =================================================
            # BROKEN PAGINATION PROTECTION
            # =================================================

            if added_this_page == 0:

                print(
                    "No new unique jobs found on this page."
                )

                print(
                    "Stopping because pagination "
                    "appears complete."
                )

                return all_jobs, True

            time.sleep(
                SOURCE_DELAY
            )

        except Exception as e:

            print(
                f"ERROR fetching page {page}: {e}"
            )

            print(
                "Source scan FAILED."
            )

            print(
                "No jobs will be deactivated."
            )

            return all_jobs, False

    # ========================================================
    # MAX PAGE SAFETY LIMIT
    # ========================================================

    print(
        "\nMAX_PAGES reached before natural completion."
    )

    print(
        "Source scan FAILED."
    )

    print(
        "No jobs will be deactivated."
    )

    return all_jobs, False


# ============================================================
# GEMINI SKILL EXTRACTION
# ============================================================

def extract_skills(job):
    """
    Ask Gemini to extract the important skills
    required for a job.

    Returns:
        list[str]
    """

    prompt = f"""
Extract the most important technical and professional skills
required for this job.

Job title:
{job.title}

Company:
{job.company}

Job description:
{job.description}

Return ONLY a JSON array of skill names.

Example:
["Python", "FastAPI", "PostgreSQL", "Docker"]

Rules:
- Return only the JSON array.
- Do not include explanations.
- Do not include markdown.
- Include important technical and professional skills.
- Avoid unnecessary generic words.
"""

    response = gemini_client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
    )

    text = (
        response.text or ""
    ).strip()

    # ========================================================
    # REMOVE MARKDOWN CODE FENCES IF GEMINI ADDS THEM
    # ========================================================

    if text.startswith("```"):

        text = (
            text
            .replace("```json", "")
            .replace("```", "")
            .strip()
        )

    skills = json.loads(text)

    if not isinstance(skills, list):

        raise ValueError(
            "Gemini did not return a JSON array"
        )

    # Make sure every item is a string.
    skills = [
        str(skill).strip()
        for skill in skills
        if str(skill).strip()
    ]

    return skills


# ============================================================
# PROCESS MISSING SKILLS
# ============================================================

def process_missing_skills(db):
    """
    Process ALL active jobs that currently have no skills.

    There is NO artificial 5-job or 10-job limit.

    Gemini processing continues until:
    - all missing jobs are processed, or
    - Gemini quota/rate limit is reached.

    If quota is reached, already processed skills remain saved.
    The remaining jobs will be picked up by the next refresh.
    """

    print()
    print("=" * 60)
    print("AI SKILL EXTRACTION")
    print("=" * 60)

    # ========================================================
    # FIND ACTIVE JOBS WITHOUT SKILLS
    # ========================================================

    active_jobs = (
        db.query(Job)
        .filter(
            Job.is_active == True
        )
        .all()
    )

    missing_jobs = [
        job
        for job in active_jobs
        if not job.required_skills
    ]

    print(
        f"Active jobs: {len(active_jobs)}"
    )

    print(
        f"Active jobs without skills: "
        f"{len(missing_jobs)}"
    )

    print(
        f"Gemini model: {GEMINI_MODEL}"
    )

    print(
        f"Delay between Gemini requests: "
        f"{GEMINI_DELAY} seconds"
    )

    print(
        "No artificial job limit for this refresh."
    )

    print("=" * 60)

    if not missing_jobs:

        print(
            "All active jobs already have skills."
        )

        return 0

    updated = 0

    # ========================================================
    # PROCESS EVERY MISSING JOB
    # ========================================================

    for index, job in enumerate(
        missing_jobs,
        start=1
    ):

        print()

        print(
            f"[{index}/{len(missing_jobs)}] "
            f"{job.title} - {job.company}"
        )

        try:

            skills = extract_skills(
                job
            )

            job.required_skills = skills

            flag_modified(
                job,
                "required_skills"
            )

            db.commit()

            updated += 1

            print(
                f"SUCCESS: {skills}"
            )

        except Exception as e:

            db.rollback()

            print(
                f"FAILED: {e}"
            )

            error_text = str(e).lower()

            # =================================================
            # GEMINI QUOTA / RATE LIMIT
            # =================================================

            if (
                "429" in error_text
                or "quota" in error_text
                or "resource_exhausted" in error_text
                or "rate limit" in error_text
            ):

                print()
                print("=" * 60)
                print("GEMINI QUOTA/RATE LIMIT REACHED")
                print("=" * 60)

                print(
                    f"Skills extracted this refresh: "
                    f"{updated}"
                )

                print(
                    "Remaining jobs will be processed "
                    "during the next refresh."
                )

                return updated

            # =================================================
            # OTHER GEMINI ERROR
            # =================================================

            print(
                "Gemini error was not a quota error."
            )

            print(
                "Continuing with the next job..."
            )

        # ====================================================
        # DELAY BETWEEN GEMINI REQUESTS
        # ====================================================

        if index < len(missing_jobs):

            print(
                f"Waiting {GEMINI_DELAY} seconds..."
            )

            time.sleep(
                GEMINI_DELAY
            )

    # ========================================================
    # ALL JOBS PROCESSED
    # ========================================================

    print()

    print("=" * 60)
    print("ALL AVAILABLE SKILLS PROCESSED")
    print("=" * 60)

    print(
        f"Skills successfully extracted: "
        f"{updated}"
    )

    return updated


# ============================================================
# SYNCHRONIZATION
# ============================================================

def sync_jobs():

    # ========================================================
    # FETCH CURRENT ONLINE JOBS
    # ========================================================

    jobs_data, scan_successful = fetch_jobs()

    if not jobs_data:

        print(
            "\nNo jobs received from Arbeitnow."
        )

        print(
            "Synchronization stopped."
        )

        return

    db = SessionLocal()

    inserted = 0
    updated = 0
    unchanged = 0
    reactivated = 0
    deactivated = 0

    try:

        now = datetime.now(
            timezone.utc
        )

        # ====================================================
        # SELECT ACTIVE JOB POOL
        # ====================================================

        active_source_jobs = (
            jobs_data[:MAX_ACTIVE_JOBS]
        )

        active_urls = {
            (job.get("url") or "").strip()
            for job in active_source_jobs
            if job.get("url")
        }

        print()
        print("=" * 60)
        print("ACTIVE JOB POOL")
        print("=" * 60)

        print(
            f"Jobs available from source: "
            f"{len(jobs_data)}"
        )

        print(
            f"Maximum active jobs: "
            f"{MAX_ACTIVE_JOBS}"
        )

        print(
            f"Jobs selected as active: "
            f"{len(active_source_jobs)}"
        )

        print("=" * 60)

        # ====================================================
        # PROCESS ACTIVE JOBS
        # ====================================================

        print()
        print(
            "Processing active jobs..."
        )

        print("-" * 60)

        for index, job in enumerate(
            active_source_jobs,
            start=1
        ):

            title = (
                job.get("title") or ""
            ).strip()

            company = (
                job.get("company_name") or ""
            ).strip()

            url = (
                job.get("url") or ""
            ).strip()

            description = strip_html(
                job.get("description") or ""
            )

            if not title or not url:

                print(
                    f"[{index}/{len(active_source_jobs)}] "
                    "Skipping malformed job."
                )

                continue

            company = (
                company or "Unknown"
            )

            description = description[:2000]

            # =================================================
            # FIND EXISTING JOB
            # =================================================

            existing = (
                db.query(Job)
                .filter(
                    Job.source_url == url
                )
                .first()
            )

            # =================================================
            # EXISTING JOB
            # =================================================

            if existing:

                changed = False

                if existing.title != title:

                    existing.title = title

                    changed = True

                if existing.company != company:

                    existing.company = company

                    changed = True

                if existing.description != description:

                    existing.description = description

                    changed = True

                existing.last_seen_at = now

                # =================================================
                # IMPORTANT:
                # If job details changed, the old skills may
                # no longer be accurate.
                #
                # Clear the old skills so Gemini regenerates them.
                # =================================================

                if changed:

                    if existing.required_skills:

                        existing.required_skills = []

                        flag_modified(
                            existing,
                            "required_skills"
                        )

                        print(
                            f"[{index}/{len(active_source_jobs)}] "
                            f"JOB CHANGED: "
                            f"{title}"
                        )

                # =================================================
                # REACTIVATE IF JOB RETURNED
                # =================================================

                if not existing.is_active:

                    existing.is_active = True

                    reactivated += 1

                    changed = True

                    print(
                        f"[{index}/{len(active_source_jobs)}] "
                        f"REACTIVATED: "
                        f"{title} @ {company}"
                    )

                elif changed:

                    print(
                        f"[{index}/{len(active_source_jobs)}] "
                        f"UPDATED: "
                        f"{title} @ {company}"
                    )

                else:

                    unchanged += 1

                updated += 1

                db.commit()

            # =================================================
            # NEW JOB
            # =================================================

            else:

                print(
                    f"[{index}/{len(active_source_jobs)}] "
                    f"NEW JOB: "
                    f"{title} @ {company}"
                )

                new_job = Job(
                    title=title,
                    company=company,
                    description=description,
                    required_skills=[],
                    source_url=url,
                    last_seen_at=now,
                    is_active=True,
                )

                db.add(
                    new_job
                )

                db.commit()

                inserted += 1

        # ====================================================
        # DEACTIVATE JOBS NO LONGER AVAILABLE
        # ====================================================

        print()

        print(
            "Checking jobs that should be inactive..."
        )

        print("-" * 60)

        # ====================================================
        # NEVER DEACTIVATE IF SOURCE SCAN FAILED
        # ====================================================

        if not scan_successful:

            print(
                "Source scan was incomplete."
            )

            print(
                "DEACTIVATION SKIPPED."
            )

        else:

            active_jobs = (
                db.query(Job)
                .filter(
                    Job.is_active == True
                )
                .all()
            )

            for existing in active_jobs:

                if (
                    existing.source_url
                    not in active_urls
                ):

                    existing.is_active = False

                    deactivated += 1

                    print(
                        f"    -> Deactivated unavailable job: "
                        f"{existing.title}"
                    )

            db.commit()

            # =================================================
            # FINAL SAFETY CHECK
            # NEVER ALLOW >500 ACTIVE JOBS
            # =================================================

            active_jobs = (
                db.query(Job)
                .filter(
                    Job.is_active == True
                )
                .order_by(
                    Job.last_seen_at.desc()
                )
                .all()
            )

            if len(active_jobs) > MAX_ACTIVE_JOBS:

                extra_jobs = (
                    active_jobs[
                        MAX_ACTIVE_JOBS:
                    ]
                )

                for job in extra_jobs:

                    job.is_active = False

                    deactivated += 1

                    print(
                        f"    -> Deactivated "
                        f"over-limit job: "
                        f"{job.title}"
                    )

                db.commit()

        # ====================================================
        # AI SKILL EXTRACTION
        # ====================================================

        process_missing_skills(
            db
        )

        # ====================================================
        # FINAL ACTIVE COUNT
        # ====================================================

        final_active_count = (
            db.query(Job)
            .filter(
                Job.is_active == True
            )
            .count()
        )

        # ====================================================
        # FINAL MISSING-SKILL COUNT
        # ====================================================

        final_active_jobs = (
            db.query(Job)
            .filter(
                Job.is_active == True
            )
            .all()
        )

        final_missing_skills = sum(
            1
            for job in final_active_jobs
            if not job.required_skills
        )

        # ====================================================
        # FINAL SUMMARY
        # ====================================================

        print()

        print("=" * 60)
        print("JOB SYNCHRONIZATION COMPLETE")
        print("=" * 60)

        print(
            f"Jobs found online: "
            f"{len(jobs_data)}"
        )

        print(
            f"Active job limit: "
            f"{MAX_ACTIVE_JOBS}"
        )

        print(
            f"Active jobs now: "
            f"{final_active_count}"
        )

        print(
            f"Active jobs still without skills: "
            f"{final_missing_skills}"
        )

        print(
            f"New jobs inserted: "
            f"{inserted}"
        )

        print(
            f"Existing jobs processed: "
            f"{updated}"
        )

        print(
            f"Unchanged jobs: "
            f"{unchanged}"
        )

        print(
            f"Jobs reactivated: "
            f"{reactivated}"
        )

        print(
            f"Jobs deactivated: "
            f"{deactivated}"
        )

        print(
            f"Source scan successful: "
            f"{scan_successful}"
        )

        print(
            "Gemini skill extraction: ENABLED"
        )

        print("=" * 60)

    except Exception as e:

        db.rollback()

        print()
        print(
            "SYNC FAILED"
        )

        print(
            f"Error: {e}"
        )

        raise

    finally:

        db.close()


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    sync_jobs()
