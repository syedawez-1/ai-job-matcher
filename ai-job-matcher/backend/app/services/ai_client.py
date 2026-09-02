"""
Central place for all LLM calls (resume structuring, skill-gap analysis,
ATS scoring). Keeping this in one module makes it easy to swap providers
or tune prompts later.
"""

import json
import re

from anthropic import Anthropic

from app.config import settings

client = Anthropic(api_key=settings.anthropic_api_key)
MODEL = "claude-sonnet-4-6"


def _extract_json(text: str) -> dict:
    """Strip markdown fences etc. and parse the first JSON object found."""
    cleaned = re.sub(r"^```(json)?|```$", "", text.strip(), flags=re.MULTILINE).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        raise


def structure_resume(raw_text: str) -> dict:
    """Turn raw resume text into structured JSON: skills, education, projects, experience."""
    prompt = f"""Extract the following from this resume as strict JSON only
(no preamble, no markdown fences): skills (list of strings), education
(list of {{"degree": str, "school": str, "year": str}}), projects
(list of {{"name": str, "description": str}}), experience (list of
{{"title": str, "company": str, "duration": str, "description": str}}).

Resume text:
{raw_text}"""
    response = client.messages.create(
        model=MODEL,
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
    )
    return _extract_json(response.content[0].text)


def analyze_skill_gap(resume_skills: list, job_requirements: list) -> dict:
    """Compare resume skills against a job's requirements."""
    prompt = f"""Given these candidate skills: {resume_skills}
And these job requirements: {job_requirements}
Return strict JSON only, no preamble, no markdown fences:
{{"missing_skills": [...], "matching_skills": [...], "recommendations": [...]}}"""
    response = client.messages.create(
        model=MODEL,
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}],
    )
    return _extract_json(response.content[0].text)


def score_ats(raw_resume_text: str) -> dict:
    """Score a resume for ATS-friendliness and give actionable feedback."""
    prompt = f"""You are an ATS (Applicant Tracking System) resume reviewer.
Review this resume text and return strict JSON only, no preamble, no
markdown fences: {{"score": <0-100 integer>, "feedback": [list of short,
actionable strings], "strengths": [list of short strings]}}.

Resume text:
{raw_resume_text}"""
    response = client.messages.create(
        model=MODEL,
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}],
    )
    return _extract_json(response.content[0].text)
