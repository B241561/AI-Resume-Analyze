# AI Resume Analyzer Desktop

AI Resume Analyzer is a standalone Windows desktop application built with Python and CustomTkinter. It does not use React, FastAPI, Flask, Electron, Node.js, a browser, or a local server.

## Features

- Choose a PDF or DOCX resume with a file picker
- Extract resume text with PyMuPDF
- Extract Word resume text with python-docx
- Analyze with Gemini when `GEMINI_API_KEY` is configured
- Fall back to a keyword-based analyzer when Gemini is unavailable
- Display summary, ATS score, skills, strengths, weaknesses, grammar suggestions, recommendations, and job match data
- Paste an optional job description
- Save analyses in SQLite
- Export the current analysis as a PDF report
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

Edit `.env` and add your Gemini API key:

```env
GEMINI_API_KEY=your_gemini_api_key_here
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

## Optional Gemini API Key

The portable folder includes `.env.example`. To use Gemini:

```text
1. Copy .env.example to .env.
2. Put your key in .env:
   GEMINI_API_KEY=your_gemini_api_key_here
```

Without a Gemini key, the application still works with the fallback keyword-based analyzer.

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

- If Gemini is unavailable or the API key is missing, the app still works using the fallback analyzer.
- Reports are saved to the `reports` folder.
- Runtime logs are saved to `app.log`.
- For a custom executable icon, place a valid `app_icon.ico` file inside `assets/` before running `build.bat`.
