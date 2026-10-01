from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from config import REPORTS_DIR


def export_analysis_pdf(file_name: str, analysis: dict[str, Any]) -> Path:
    REPORTS_DIR.mkdir(exist_ok=True)
    generated_at = datetime.now()
    timestamp = generated_at.strftime("%Y%m%d_%H%M%S")
    output_path = REPORTS_DIR / f"analysis_{timestamp}.pdf"

    document = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=0.6 * inch,
        leftMargin=0.6 * inch,
        topMargin=0.6 * inch,
        bottomMargin=0.6 * inch,
    )
    styles = getSampleStyleSheet()
    story: list[Any] = [
        Paragraph("AI Resume Analysis Report", styles["Title"]),
        Paragraph("Project Name: AI Resume Analyzer", styles["Normal"]),
        Paragraph(f"Resume: {file_name}", styles["Normal"]),
        Paragraph(f"Date: {generated_at.strftime('%d %B %Y, %I:%M %p')}", styles["Normal"]),
        Spacer(1, 12),
        _score_table(analysis),
        Spacer(1, 8),
        Paragraph("Scoring Method", styles["Heading2"]),
        Paragraph(
            "ATS Readiness is a transparent application-specific rubric based on contact/link completeness, resume sections, "
            "technical skills, measurable impact, action language, parseability, and—when a job description is supplied—job relevance. "
            "It is not an employer ATS score.",
            styles["BodyText"],
        ),
        Spacer(1, 12),
        Paragraph("Candidate Summary", styles["Heading2"]),
        Paragraph(_safe_text(analysis.get("summary", "")), styles["BodyText"]),
    ]

    breakdown = analysis.get("ats_breakdown", {})
    if breakdown:
        story.extend(
            [
                Spacer(1, 10),
                Paragraph("ATS Readiness Breakdown", styles["Heading2"]),
                _breakdown_table(breakdown),
            ]
        )

    if analysis.get("match_explanation"):
        story.extend(
            [
                Spacer(1, 10),
                Paragraph("Job Match Method", styles["Heading2"]),
                Paragraph(_safe_text(analysis.get("match_explanation", "")), styles["BodyText"]),
            ]
        )

    for title, key in [
        ("Technical Skills", "technical_skills"),
        ("Soft Skills", "soft_skills"),
        ("Missing Skills", "missing_skills"),
        ("Strengths", "strengths"),
        ("Weaknesses", "weaknesses"),
        ("Grammar Suggestions", "grammar_suggestions"),
        ("Improvement Recommendations", "recommendations"),
        ("Missing Keywords", "missing_keywords"),
        ("Missing Job Skills", "missing_job_skills"),
    ]:
        story.extend([Spacer(1, 10), Paragraph(title, styles["Heading2"])])
        story.extend(_bullets(analysis.get(key, []), styles["BodyText"]))

    document.build(story)
    return output_path


def _score_table(analysis: dict[str, Any]) -> Table:
    table = Table(
        [
            ["Metric", "Score"],
            ["ATS Readiness", f"{analysis.get('ats_score', 0)} / 100"],
            ["Job Match", f"{analysis.get('match_percentage', 0)}%"],
        ],
        colWidths=[3 * inch, 2.5 * inch],
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#111827")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ("PADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    return table


def _breakdown_table(breakdown: dict[str, Any]) -> Table:
    rows = [["Component", "Points"]]
    labels = {
        "contact_and_links": "Contact & links",
        "resume_sections": "Resume sections",
        "technical_skills": "Technical skills",
        "measurable_impact": "Measurable impact",
        "action_language": "Action language",
        "parseability": "Parseability",
        "job_relevance": "Job relevance",
    }
    rows.extend([[labels.get(key, key), str(value)] for key, value in breakdown.items()])
    table = Table(rows, colWidths=[3 * inch, 2.5 * inch])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E2E8F0")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ("PADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return table


def _bullets(items: list[str], style: Any) -> list[Paragraph]:
    if not items:
        return [Paragraph("No items available.", style)]
    return [Paragraph(f"- {_safe_text(item)}", style) for item in items]


def _safe_text(value: Any) -> str:
    return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
