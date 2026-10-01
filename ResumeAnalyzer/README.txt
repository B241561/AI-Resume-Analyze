AI Resume Analyzer

This is a portable desktop application. Double-click ResumeAnalyzer.exe on Windows.

Features:
- PDF and DOCX resume extraction
- OCR fallback for scanned PDFs (Tesseract required)
- Transparent ATS Readiness scoring
- Local TF-IDF + skill-coverage job matching
- Job Match is calculated only when a target job description is provided; otherwise the app displays an unavailable state, not a zero score
- Groq uses the official Groq Python SDK with openai/gpt-oss-120b by default; set GROQ_MODEL to select another model
- Groq can be configured in Groq AI Settings or with GROQ_API_KEY; it is enabled by default when configured and can be turned off
- Resume/JD text is sent to Groq only while Groq is enabled; local analysis remains available
- Resume-specific recommendations shown in the application
- Local SQLite history without storing raw resume/JD text
- PDF report and formatted JSON downloads with a Save As dialog
- Recommendations included in PDF reports

Groq configuration and privacy:
Configure a key in Groq AI Settings (stored in the operating system credential store) or use GROQ_API_KEY in the environment/.env. The in-app key takes precedence. Requests use the official Groq Python SDK and GROQ_MODEL. Test Connection sends only a minimal request, not resume or job-description content.

Extracted resume and job-description text is sent to Groq only when Groq is enabled. When disabled or unavailable, analysis stays local.

Without GROQ_API_KEY, Groq is unavailable and local analysis remains enabled.
