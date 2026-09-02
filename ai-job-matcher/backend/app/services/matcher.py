"""
Day 13-17: job matching algorithm.

Start simple: overlap between resume skills and job.required_skills,
scored and ranked. Can evolve into embedding-based similarity later
(e.g. compare resume + job description embeddings via a vector column
in Postgres/pgvector) without changing the router contract.
"""


def score_match(resume_skills: list[str], job_required_skills: list[str]) -> float:
    if not job_required_skills:
        return 0.0
    resume_set = {s.lower() for s in resume_skills}
    job_set = {s.lower() for s in job_required_skills}
    overlap = resume_set & job_set
    return round(len(overlap) / len(job_set), 2)


def rank_jobs(resume_skills: list[str], jobs: list[dict]) -> list[dict]:
    scored = [
        {**job, "match_score": score_match(resume_skills, job.get("required_skills", []))}
        for job in jobs
    ]
    return sorted(scored, key=lambda j: j["match_score"], reverse=True)
