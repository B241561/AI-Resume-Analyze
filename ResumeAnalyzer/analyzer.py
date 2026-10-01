from __future__ import annotations

import json
import re
from typing import Any

from config import GEMINI_API_KEY, GEMINI_MODEL


TECH_SKILLS = {
    "python",
    "java",
    "javascript",
    "typescript",
    "react",
    "sql",
    "mysql",
    "postgresql",
    "mongodb",
    "fastapi",
    "django",
    "flask",
    "html",
    "css",
    "git",
    "docker",
    "aws",
    "azure",
    "pandas",
    "numpy",
    "machine learning",
    "data analysis",
}

SOFT_SKILLS = {
    "communication",
    "teamwork",
    "leadership",
    "problem solving",
    "adaptability",
    "collaboration",
    "time management",
    "presentation",
}


def analyze_resume(resume_text: str, job_description: str = "") -> dict[str, Any]:
    if GEMINI_API_KEY:
        try:
            return _analyze_with_gemini(resume_text, job_description)
        except Exception:
            # Phase 1 keeps the app usable for demos even if Gemini is unavailable.
            return _fallback_analysis(resume_text, job_description)
    return _fallback_analysis(resume_text, job_description)


def _analyze_with_gemini(resume_text: str, job_description: str) -> dict[str, Any]:
    import google.generativeai as genai

    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(GEMINI_MODEL)
    prompt = f"""
Analyze this resume and return only valid JSON with these keys:
summary, ats_score, technical_skills, soft_skills, missing_skills,
strengths, weaknesses, grammar_suggestions, recommendations,
match_percentage, missing_keywords, missing_job_skills.

Use integer scores from 0 to 100. If no job description is supplied,
set match_percentage to 0 and job-specific lists to empty arrays.

Resume:
{resume_text[:18000]}

Job description:
{job_description[:12000]}
"""
    response = model.generate_content(prompt)
    return _normalize_result(_extract_json(getattr(response, "text", "")), job_description)


def _extract_json(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    fenced = re.search(r"```(?:json)?\s*(.*?)```", cleaned, re.DOTALL | re.IGNORECASE)
    if fenced:
        cleaned = fenced.group(1).strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start >= 0 and end >= 0:
        cleaned = cleaned[start : end + 1]
    return json.loads(cleaned)


def _fallback_analysis(resume_text: str, job_description: str) -> dict[str, Any]:
    lower_resume = resume_text.lower()
    technical = sorted(_title(skill) for skill in TECH_SKILLS if skill in lower_resume)
    soft = sorted(_title(skill) for skill in SOFT_SKILLS if skill in lower_resume)

    has_metrics = bool(re.search(r"\b\d+%|\b\d+\+|\b\d{2,}\b", resume_text))
    section_count = sum(section in lower_resume for section in ["skills", "projects", "experience", "education"])
    ats_score = min(95, 45 + len(technical) * 4 + len(soft) * 2 + section_count * 6 + (10 if has_metrics else 0))

    match_percentage, missing_keywords, missing_job_skills = _compare_to_job(resume_text, job_description)

    return {
        "summary": "This resume has a clear base profile. Add role-specific keywords, measurable results, and stronger project impact to improve ATS performance.",
        "ats_score": ats_score,
        "technical_skills": technical,
        "soft_skills": soft,
        "missing_skills": [skill for skill in ["Testing", "Cloud", "Deployment"] if skill.lower() not in lower_resume],
        "strengths": [
            "Includes readable sections that are useful for ATS parsing.",
            "Shows relevant skills and project or experience details.",
        ],
        "weaknesses": [
            "Some bullets may need measurable outcomes.",
            "The resume may need more keywords from the target job description.",
        ],
        "grammar_suggestions": [
            "Use consistent tense and punctuation in all bullets.",
            "Keep formatting simple and avoid complex tables.",
        ],
        "recommendations": [
            "Start bullets with action verbs.",
            "Add numbers such as percentages, counts, or time saved.",
            "Move the strongest technical skills near the top.",
        ],
        "match_percentage": match_percentage,
        "missing_keywords": missing_keywords,
        "missing_job_skills": missing_job_skills,
    }


def _compare_to_job(resume_text: str, job_description: str) -> tuple[int, list[str], list[str]]:
    if not job_description.strip():
        return 0, [], []

    resume_words = _important_words(resume_text)
    job_words = _important_words(job_description)
    matched = resume_words & job_words
    missing_keywords = sorted(job_words - resume_words)[:20]
    match_percentage = int((len(matched) / max(len(job_words), 1)) * 100)

    job_lower = job_description.lower()
    resume_lower = resume_text.lower()
    required_skills = sorted(_title(skill) for skill in TECH_SKILLS if skill in job_lower)
    missing_skills = [skill for skill in required_skills if skill.lower() not in resume_lower]
    return min(match_percentage, 100), missing_keywords, missing_skills


def _important_words(text: str) -> set[str]:
    stop_words = {"and", "the", "with", "for", "you", "your", "our", "are", "will", "from", "that", "this"}
    words = re.findall(r"[a-zA-Z][a-zA-Z+#.]{2,}", text.lower())
    return {word for word in words if word not in stop_words}


def _normalize_result(result: dict[str, Any], job_description: str) -> dict[str, Any]:
    defaults = _fallback_analysis("", job_description)
    defaults.update(result)
    defaults["ats_score"] = _score(defaults.get("ats_score", 0))
    defaults["match_percentage"] = _score(defaults.get("match_percentage", 0))
    for key in [
        "technical_skills",
        "soft_skills",
        "missing_skills",
        "strengths",
        "weaknesses",
        "grammar_suggestions",
        "recommendations",
        "missing_keywords",
        "missing_job_skills",
    ]:
        defaults[key] = _as_list(defaults.get(key, []))
    return defaults


def _score(value: Any) -> int:
    try:
        return max(0, min(100, int(value)))
    except (TypeError, ValueError):
        return 0


def _title(skill: str) -> str:
    if skill in {"sql", "html", "css", "aws"}:
        return skill.upper()
    return skill.title()


def _as_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    if not value:
        return []
    return [str(value)]
