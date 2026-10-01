AI Resume Analyzer

This is a portable desktop application. Double-click ResumeAnalyzer.exe on Windows.

Features:
- PDF and DOCX resume extraction
- OCR fallback for scanned PDFs (Tesseract required)
- Transparent ATS Readiness scoring
- Local TF-IDF + skill-coverage job matching
- Job Match is calculated only when a target job description is provided; otherwise the app displays an unavailable state, not a zero score
- Gemini is enabled by default when GEMINI_API_KEY is configured; it can be turned off
- Resume/JD text is sent to Gemini only while Gemini is enabled; local analysis remains available
- Resume-specific recommendations shown in the application
- Local SQLite history without storing raw resume/JD text
- PDF report and formatted JSON downloads with a Save As dialog
- Recommendations included in PDF reports

Gemini privacy:
When Gemini is enabled, extracted resume/JD text is sent to the configured Google Gemini API.
When Gemini is disabled, analysis stays local.

Without GEMINI_API_KEY, Gemini is unavailable and local analysis remains enabled.
