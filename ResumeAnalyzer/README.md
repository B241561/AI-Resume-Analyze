# AI Resume Analyzer Desktop

AI Resume Analyzer is a standalone Windows desktop application built with Python and CustomTkinter. It does not use React, FastAPI, Flask, Electron, Node.js, a browser, or a local server.

## Features

- Choose a PDF or DOCX resume with a file picker
- Extract resume text with PyMuPDF
- Extract Word resume text with python-docx
- Configure Groq in-app or through `GROQ_API_KEY`; requests use the official Groq Python SDK
- Groq is enabled by default when a key is configured, with an option to turn it off
- Use local ATS, skills, and job-match analysis when Groq is disabled or unavailable
- Show resume-specific recommendations, skills, strengths, weaknesses, grammar suggestions, and job-match data
- Paste an optional job description
- Calculate Job Match only when a target job description is provided; without one, display an unavailable state rather than a zero score
- Save analysis results in SQLite without storing raw resume or job-description text
- Download the current analysis as a PDF report or formatted JSON file
- Build a portable Windows one-dir application with PyInstaller

## Project Structure

```text
ResumeAnalyzer/
  app.py
  ui.py
  analyzer.py
  pdf_reader.py
  report_generator.py
  database.py
  config.py
  requirements.txt
  .env.example
  build.bat
  README.md
  assets/
  reports/
  temp/
```

## Setup for Development

Use Python 3.11 or newer.

```bat
cd ResumeAnalyzer
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Groq can be configured in the application or through the optional `.env` fallback. When using `.env`, copy `.env.example` and set `GROQ_API_KEY` locally. Groq is enabled by default when a key is configured, and can be turned off in the application.

```env
GROQ_API_KEY=
GROQ_MODEL=openai/gpt-oss-120b
```

Run the app during development:

```bat
python app.py
```

## Build Windows Executable

```bat
cd ResumeAnalyzer
build.bat
```

The portable application folder will be created at:

```text
dist\ResumeAnalyzer_Portable\
```

## Final Portable Folder

```text
dist/
  ResumeAnalyzer_Portable/
    ResumeAnalyzer.exe
    _internal/
    assets/
    reports/
    temp/
    .env.example
    README.txt
```

## Portable Usage

For sharing:

```text
1. Zip the dist\ResumeAnalyzer_Portable folder.
2. Send or upload the ZIP.
3. The user downloads the ZIP.
4. The user extracts the ZIP.
5. The user double-clicks ResumeAnalyzer.exe.
```

No installation is required after building. The user does not need Python, Node.js, Visual Studio, a terminal, a browser, or a local server.

## Groq Configuration and Privacy

Configure Groq either in **Groq AI Settings** in the application or with the `GROQ_API_KEY` environment variable / `.env` file. In-app credentials are stored in the operating system credential store and take precedence over the environment key. The model is configurable through `GROQ_MODEL` and defaults to `openai/gpt-oss-120b`. The portable folder includes `.env.example` as an optional developer setup path.

```text
1. Open Groq AI Settings and enter a key, or configure GROQ_API_KEY in the environment/.env.
2. Use Test Connection to validate a key with a minimal request that contains no resume or job-description text.
```

Groq is contacted only when its checkbox is enabled. Extracted resume and job-description text is sent to Groq only while enabled; when disabled or unavailable, local analysis remains available.

## Required Portable Contents

```text
ResumeAnalyzer_Portable/
  ResumeAnalyzer.exe
  _internal/
  assets/
  reports/
  temp/
  .env.example
  README.txt
```

## Notes

- If Groq is unavailable or the API key is missing, the app still works using the fallback analyzer.
- PDF and JSON downloads open a Save As dialog and suggest a filename based on the resume.
- Recommendations are shown in the application and included in PDF reports.
- Runtime logs are saved to `app.log`.
- For a custom executable icon, place a valid `app_icon.ico` file inside `assets/` before running `build.bat`.
