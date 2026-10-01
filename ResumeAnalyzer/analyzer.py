from __future__ import annotations

import json
import math
import re
from typing import Any

from config import GEMINI_API_KEY, GEMINI_MODEL


# Canonical skill names mapped to common resume/job-description aliases.
SKILL_ALIASES: dict[str, set[str]] = {
    "python": {"python"},
    "java": {"java"},
    "javascript": {"javascript", "js", "ecmascript"},
    "typescript": {"typescript", "ts"},
    "react": {"react", "reactjs", "react.js"},
    "sql": {"sql"},
    "mysql": {"mysql"},
    "postgresql": {"postgresql", "postgres", "postgres db"},
    "mongodb": {"mongodb", "mongo db", "mongo"},
    "node.js": {"node.js", "nodejs", "node js"},
    "fastapi": {"fastapi"},
    "django": {"django"},
    "flask": {"flask"},
    "html": {"html", "html5"},
    "css": {"css", "css3"},
    "git": {"git", "github", "gitlab"},
    "docker": {"docker", "containerization", "containers"},
    "kubernetes": {"kubernetes", "k8s"},
    "aws": {"aws", "amazon web services"},
    "azure": {"azure", "microsoft azure"},
    "gcp": {"gcp", "google cloud", "google cloud platform"},
    "pandas": {"pandas"},
    "numpy": {"numpy"},
    "scikit-learn": {"scikit-learn", "sklearn", "scikit learn"},
    "machine learning": {"machine learning", "ml"},
    "deep learning": {"deep learning", "dl"},
    "data analysis": {"data analysis", "data analytics"},
    "tensorflow": {"tensorflow"},
    "pytorch": {"pytorch", "torch"},
    "power bi": {"power bi", "powerbi"},
    "tableau": {"tableau"},
    "excel": {"excel", "microsoft excel"},
    "php": {"php"},
    "c++": {"c++", "cpp"},
    "c": {"c programming", " c ", "c language"},
}

TECH_SKILLS = set(SKILL_ALIASES)

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

ATS_SECTION_PATTERNS = {
    "summary": ("summary", "professional summary", "profile", "objective"),
    "skills": ("skills", "technical skills", "skills & technologies", "technologies"),
    "experience": ("experience", "work experience", "professional experience", "employment"),
    "projects": ("projects", "personal projects", "academic projects", "project experience"),
    "education": ("education", "academic background", "qualifications"),
    "certifications": ("certifications", "certificates", "licenses"),
}

ACTION_VERBS = {
    "built", "developed", "designed", "implemented", "created", "engineered", "automated",
    "optimized", "improved", "reduced", "increased", "delivered", "deployed", "led",
    "managed", "analyzed", "integrated", "migrated", "tested", "configured", "maintained",
}


def analyze_resume(
    resume_text: str,
    job_description: str = "",
    use_gemini: bool = True,
) -> dict[str, Any]:
    """Analyze a resume with explicit privacy control and a deterministic ATS rubric.

    ATS readiness is always calculated locally from observable resume evidence. Gemini is
    used only for richer qualitative feedback and contextual job matching when enabled.
    """
    if use_gemini and GEMINI_API_KEY:
        try:
            return _analyze_with_gemini(resume_text, job_description)
        except Exception:
            # Keep the application usable if Gemini is unavailable or returns invalid data.
            return _fallback_analysis(resume_text, job_description)
    return _fallback_analysis(resume_text, job_description)


def _analyze_with_gemini(resume_text: str, job_description: str) -> dict[str, Any]:
    import google.generativeai as genai

    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(GEMINI_MODEL)
    prompt = f"""
Analyze this resume and return only valid JSON with these keys:
summary, technical_skills, soft_skills, missing_skills,
strengths, weaknesses, grammar_suggestions, recommendations,
match_percentage, missing_keywords, missing_job_skills, match_explanation.

Important rules:
- Do NOT generate an ATS score. The application calculates ATS readiness locally from an
  auditable rubric using resume evidence.
- Use integer match_percentage from 0 to 100 only when a job description is supplied.
- Judge job fit contextually across responsibilities, required skills, tools, seniority,
  and relevant experience. Do not treat every common word as a match.
- Do not invent experience, skills, qualifications, or achievements that are not present.
- If no job description is supplied, set match_percentage to 0, match_explanation to an
  empty string, and job-specific lists to empty arrays.

Resume:
{resume_text[:18000]}

Job description:
{job_description[:12000]}
"""
    response = model.generate_content(prompt)
    result = _normalize_result(_extract_json(getattr(response, "text", "")), job_description)
    result["ats_score"], result["ats_breakdown"] = calculate_ats_readiness(resume_text, job_description)
    result["analysis_mode"] = "Gemini AI + local ATS rubric"
    result["match_method"] = "Gemini contextual job-fit assessment"
    result["match_percentage"] = _score(result.get("match_percentage", 0)) if job_description.strip() else 0
    return result


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
    technical = sorted(_title(skill) for skill in TECH_SKILLS if _contains_skill(lower_resume, skill))
    soft = sorted(_title(skill) for skill in SOFT_SKILLS if skill in lower_resume)

    match_percentage, missing_keywords, missing_job_skills, match_explanation = _compare_to_job(
        resume_text, job_description
    )
    ats_score, ats_breakdown = calculate_ats_readiness(resume_text, job_description)

    return {
        "summary": "This resume has a clear base profile. Add role-specific keywords, measurable results, and stronger project impact to improve ATS readiness.",
        "ats_score": ats_score,
        "ats_breakdown": ats_breakdown,
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
        "match_explanation": match_explanation,
        "analysis_mode": "Local analysis",
        "match_method": "Local TF-IDF + skill coverage",
    }


def calculate_ats_readiness(resume_text: str, job_description: str = "") -> tuple[int, dict[str, int]]:
    """Return a reproducible, explainable ATS-readiness score from 0-100.

    The base rubric has exactly 100 possible points. When a job description is supplied,
    the same core evidence contributes 80% of the score and contextual job relevance
    contributes the remaining 20%. This is an application-specific readiness metric,
    not an employer ATS score.
    """
    text = resume_text.strip()
    lower = text.lower()

    # Base rubric: 15 + 20 + 15 + 15 + 10 + 25 = 100 points.
    contact = 0
    if re.search(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", text, re.IGNORECASE):
        contact += 6
    if re.search(r"(?:\+?\d[\d\s().-]{8,}\d)", text):
        contact += 4
    if re.search(r"(?:linkedin\.com|github\.com|portfolio|behance|www\.)", lower):
        contact += 5

    sections = 0
    section_weights = {
        "summary": 3,
        "skills": 4,
        "experience": 4,
        "projects": 3,
        "education": 3,
        "certifications": 3,
    }
    for name, patterns in ATS_SECTION_PATTERNS.items():
        if any(_contains_heading(lower, pattern) for pattern in patterns):
            sections += section_weights[name]

    technical_count = sum(_contains_skill(lower, skill) for skill in TECH_SKILLS)
    technical = min(15, technical_count * 2)

    metric_count = len(
        re.findall(
            r"\b\d+(?:\.\d+)?\s*(?:%|x|hours?|days?|months?|years?|users?|clients?|projects?|records?|tickets?)\b|\b\d+\+",
            lower,
        )
    )
    metrics = min(15, metric_count * 3)

    action_verbs_used = sum(bool(re.search(rf"\b{re.escape(verb)}\b", lower)) for verb in ACTION_VERBS)
    action_impact = min(10, action_verbs_used)

    parseability = 0
    word_count = len(re.findall(r"\b\w+\b", text))
    if 250 <= word_count <= 1200:
        parseability += 10
    elif 120 <= word_count < 250 or 1200 < word_count <= 1800:
        parseability += 6
    elif word_count >= 80:
        parseability += 3
    if re.search(r"(?:^|\n)\s*(?:[-•*]|\d+[.)])\s+", text):
        parseability += 8
    if len(text) >= 50:
        parseability += 7

    base_breakdown = {
        "contact_and_links": contact,
        "resume_sections": min(sections, 20),
        "technical_skills": technical,
        "measurable_impact": metrics,
        "action_language": action_impact,
        "parseability": min(parseability, 25),
    }
    base_score = sum(base_breakdown.values())

    if not job_description.strip():
        return min(100, base_score), base_breakdown

    # A target job makes relevance part of the ATS-readiness calculation.
    job_match = _compare_to_job(resume_text, job_description)[0]
    weighted_breakdown = {key: round(value * 0.8) for key, value in base_breakdown.items()}
    weighted_breakdown["job_relevance"] = round(job_match * 0.2)
    total = min(100, sum(weighted_breakdown.values()))
    return total, weighted_breakdown


def _compare_to_job(resume_text: str, job_description: str) -> tuple[int, list[str], list[str], str]:
    if not job_description.strip():
        return 0, [], [], ""

    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity

        vectorizer = TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2),
            sublinear_tf=True,
            max_features=2500,
        )
        matrix = vectorizer.fit_transform([resume_text, job_description])
        similarity = float(cosine_similarity(matrix[0:1], matrix[1:2])[0][0])
        features = vectorizer.get_feature_names_out()
        resume_weights = matrix[0].toarray()[0]
        job_weights = matrix[1].toarray()[0]

        job_only_terms = [
            (features[index], job_weights[index])
            for index in range(len(features))
            if job_weights[index] > 0 and resume_weights[index] == 0
        ]
        job_only_terms.sort(key=lambda item: item[1], reverse=True)
        missing_keywords = [term for term, _weight in job_only_terms if not term.isdigit()][:20]
    except Exception:
        # A dependency failure should never break the core analyzer.
        resume_words = _important_words(resume_text)
        job_words = _important_words(job_description)
        overlap = resume_words & job_words
        similarity = len(overlap) / max(len(job_words), 1)
        missing_keywords = sorted(job_words - resume_words)[:20]

    job_lower = job_description.lower()
    resume_lower = resume_text.lower()
    required_skills = sorted(
        _title(skill) for skill in TECH_SKILLS if _contains_skill(job_lower, skill)
    )
    missing_skills = [skill for skill in required_skills if not _contains_skill(resume_lower, skill)]
    matched_skills = len(required_skills) - len(missing_skills)
    skill_coverage = matched_skills / max(len(required_skills), 1)

    # Weighted job-fit score: contextual text similarity plus explicit skill coverage.
    match_percentage = int(round((similarity * 0.6 + skill_coverage * 0.4) * 100))
    method = "TF-IDF similarity + technical-skill coverage"
    explanation = (
        f"The local matcher combines document similarity (60%) with explicit technical-skill coverage (40%). "
        f"It found {matched_skills}/{len(required_skills)} detected technical skills from the job description."
        if required_skills
        else "The local matcher uses TF-IDF similarity over the resume and job description because no known technical skills were detected."
    )
    return min(match_percentage, 100), missing_keywords, missing_skills, explanation


def _important_words(text: str) -> set[str]:
    stop_words = {
        "and", "the", "with", "for", "you", "your", "our", "are", "will", "from", "that", "this",
        "have", "has", "been", "into", "using", "role", "work", "team", "job",
    }
    words = re.findall(r"[a-zA-Z][a-zA-Z+#.]{2,}", text.lower())
    return {word for word in words if word not in stop_words}


def _normalize_result(result: dict[str, Any], job_description: str) -> dict[str, Any]:
    defaults = _fallback_analysis("", job_description)
    defaults.update(result)
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
    defaults["ats_score"] = _score(defaults.get("ats_score", 0))
    defaults["match_percentage"] = _score(defaults.get("match_percentage", 0))
    defaults["match_explanation"] = str(defaults.get("match_explanation", ""))
    return defaults


def _score(value: Any) -> int:
    try:
        return max(0, min(100, int(float(value))))
    except (TypeError, ValueError):
        return 0


def _title(skill: str) -> str:
    if skill in {"sql", "html", "css", "aws", "gcp", "php"}:
        return skill.upper()
    if skill == "c++":
        return "C++"
    if skill == "scikit-learn":
        return "Scikit-Learn"
    if skill == "node.js":
        return "Node.js"
    return skill.title()


def _as_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    if not value:
        return []
    return [str(value)]


def _contains_heading(text: str, heading: str) -> bool:
    return bool(re.search(rf"(?m)^\s*{re.escape(heading)}\s*[:\-]?\s*$", text)) or heading in text[:1500]


def _contains_skill(text: str, skill: str) -> bool:
    aliases = SKILL_ALIASES.get(skill, {skill})
    padded = f" {text.lower()} "
    for alias in aliases:
        alias = alias.lower().strip()
        if not alias:
            continue
        if re.search(rf"(?<![a-z0-9+#.]){re.escape(alias)}(?![a-z0-9+#.])", padded):
            return True
    return False
