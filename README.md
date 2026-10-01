# AI Resume Analyzer

A Windows desktop application that analyzes PDF and DOCX resumes using Google Gemini AI, with a built-in keyword-based fallback analyzer. It provides ATS-oriented feedback, job-description matching, skill extraction, improvement suggestions, saved analysis history, and PDF report generation.

> **Application type:** Desktop GUI  
> **Primary platform:** Windows  
> **Language:** Python 3.11+  
> **GUI:** CustomTkinter

## Features

- Select a resume in **PDF** or **DOCX** format.
- Extract text from PDF files using **PyMuPDF**.
- Extract text and table content from DOCX files using **python-docx**.
- Analyze resumes with **Google Gemini** when an API key is configured.
- Automatically fall back to a local keyword-based analyzer when Gemini is unavailable.
- Display:
  - ATS-oriented score
  - Job-match percentage
  - Technical skills
  - Soft skills
  - Missing skills
  - Strengths
  - Weaknesses
  - Grammar suggestions
  - Recommendations
  - Missing keywords
  - Missing job-specific skills
- Optionally paste a job description for role-specific matching.
- Store analysis history locally in **SQLite**.
- Export the current analysis as an **A4 PDF report**.
- Build a portable Windows application with **PyInstaller**.

## How It Works

```text
Resume PDF/DOCX
       |
       v
File Validation
       |
       v
Text Extraction
  |           |
 PDF         DOCX
(PyMuPDF)  (python-docx)
       |
       v
Resume Text
       |
       +----------------------+
       |                      |
Gemini API available?      No / API fails
       |                      |
      Yes                     v
       |               Local Fallback
       v               Keyword Analyzer
Gemini Analysis              |
       |                     |
       +----------+----------+
                  |
                  v
          Normalized Analysis
                  |
          +-------+--------+
          |                |
          v                v
     GUI Dashboard     SQLite History
          |
          v
     PDF Report Export
```

## Technology Stack

| Component | Technology |
|---|---|
| Programming Language | Python 3.11+ |
| Desktop GUI | CustomTkinter |
| PDF Text Extraction | PyMuPDF |
| DOCX Text Extraction | python-docx |
| AI Analysis | Google Gemini API |
| Environment Variables | python-dotenv |
| Local Database | SQLite |
| PDF Report Generation | ReportLab |
| Packaging | PyInstaller |

## Project Structure

```text
ResumeAnalyzer/
├── app.py
├── ui.py
├── analyzer.py
├── pdf_reader.py
├── report_generator.py
├── database.py
├── config.py
├── requirements.txt
├── .env.example
├── build.bat
├── ResumeAnalyzer.spec
├── assets/
│   ├── app_icon.svg
│   └── ...
├── reports/
├── temp/
├── resume_analyzer.db
└── app.log
```

### Module Responsibilities

**`app.py`**  
Application entry point. Creates required directories, configures logging, initializes SQLite, and starts the CustomTkinter application.

**`ui.py`**  
Contains the complete desktop interface, file picker, job-description input, analysis progress state, results cards, history panel, About dialog, and PDF export action.

**`analyzer.py`**  
Contains the Gemini integration and the deterministic fallback analyzer. It also normalizes AI output and performs basic job-description matching.

**`pdf_reader.py`**  
Validates resume files and extracts text from PDF and DOCX documents.

**`database.py`**  
Creates the SQLite database, saves completed analyses, and loads recent analysis history.

**`report_generator.py`**  
Generates a formatted A4 PDF report from the analysis result.

**`config.py`**  
Loads environment variables and defines application paths such as assets, reports, temporary files, database, and `.env`.

## Requirements

For development, use:

- Windows
- Python **3.11 or newer**
- Internet access when using Gemini
- A Gemini API key for AI-powered analysis

Install dependencies:

```bat
cd ResumeAnalyzer
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
```

## Configuration

Create a `.env` file from `.env.example`:

```bat
copy .env.example .env
```

Then configure:

```env
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-1.5-flash
MAX_PDF_MB=5
```

### Configuration Parameters

| Variable | Purpose | Default |
|---|---|---|
| `GEMINI_API_KEY` | API key used for Gemini analysis | Empty |
| `GEMINI_MODEL` | Gemini model name | `gemini-1.5-flash` |
| `MAX_PDF_MB` | Maximum accepted resume file size | `5` |

Keep `.env` private and never commit API keys to Git.

## Run in Development

```bat
cd ResumeAnalyzer
python app.py
```

The application opens as a desktop window. No browser, Node.js runtime, Flask server, FastAPI server, or local web server is required.

## Using the Application

1. Click **Choose Resume File**.
2. Select a PDF or DOCX resume.
3. Optionally paste a target job description.
4. Click **Analyze Resume**.
5. Review the ATS-oriented score, job match, extracted skills, weaknesses, missing keywords, and recommendations.
6. Click **Export PDF** to save the current report.
7. Previously analyzed resumes appear in the **Previous Analyses** panel.

Generated reports are stored in:

```text
reports/
```

Application logs are stored in:

```text
app.log
```

The local database is stored in:

```text
resume_analyzer.db
```

## AI and Fallback Modes

### Gemini Mode

When `GEMINI_API_KEY` is configured, the application sends resume text and the optional job description to the configured Gemini model and expects structured JSON containing the analysis fields used by the UI.

### Fallback Mode

When no Gemini API key is configured, or a Gemini request fails, the application uses a local keyword-based analyzer.

The fallback analyzer:

- Detects a predefined set of technical skills.
- Detects a predefined set of soft skills.
- Looks for common resume sections.
- Checks for measurable values such as percentages or counts.
- Compares important words between the resume and job description.
- Identifies missing job-related skills from the built-in skill list.

This means the fallback mode is useful for demonstrations and basic feedback, but it is not equivalent to a production ATS engine.

## ATS Score and Job Match

The displayed **ATS Score** is an application-generated score, not a score returned by a real applicant-tracking system.

In fallback mode, the score is calculated from detected skills, common resume sections, soft skills, and evidence of measurable achievements. In Gemini mode, the model is asked to produce a score between 0 and 100.

The **Job Match** value is also an application-level estimate. With a job description, the fallback mode calculates it from overlap between important words in the resume and job description.

Use these values as guidance rather than as a guarantee of how a specific employer's ATS will evaluate a resume.

## Input Validation

The application validates:

- File existence
- `.pdf` and `.docx` extensions
- Maximum file size
- Ability to open the document
- Minimum extracted text length

Scanned/image-only PDFs may not work because the current PDF reader extracts text rather than performing OCR.

## Portable Windows Build

The project includes a build script and PyInstaller specification.

Build the application with:

```bat
cd ResumeAnalyzer
build.bat
```

The build produces:

```text
dist/
└── ResumeAnalyzer_Portable/
    ├── ResumeAnalyzer.exe
    ├── _internal/
    ├── assets/
    ├── reports/
    ├── temp/
    ├── .env.example
    └── README.txt
```

### Sharing the Portable Version

1. Zip the `ResumeAnalyzer_Portable` folder.
2. Send the ZIP to the user.
3. Extract the ZIP.
4. Double-click `ResumeAnalyzer.exe`.

Python does not need to be installed on the target machine.

## Data and Privacy Notes

The application stores the following information locally in SQLite:

- Resume file name
- Extracted resume text
- Job description
- Generated analysis JSON
- Creation timestamp

When Gemini mode is used, resume text and the optional job description are sent to the configured Gemini API. Review the applicable provider terms and privacy requirements before using the application with sensitive or confidential resumes.

## Current Limitations

- PDF processing is text extraction only; there is no OCR for scanned/image-based resumes.
- The fallback analyzer uses a fixed list of skills and simple keyword matching.
- Job matching is based on lexical overlap rather than a trained semantic matching model.
- The ATS score is an application-specific heuristic/model output, not a verified score from an employer ATS.
- There is currently no automated test suite in the project.
- There is currently no Docker, Jenkins, or CI/CD configuration.
- The repository contains build artifacts and local development files that are better kept out of the source repository.
- The current source tree only includes an SVG application icon; the PyInstaller specification can use an `.ico` file when one is supplied.

## Recommended Repository Hygiene

Do not commit these files or folders:

```text
.venv/
dist/
build/
.env
resume_analyzer.db
*.pyc
__pycache__/
```

The existing `.gitignore` already covers the main generated and secret files. Keep the portable build output separate from the source repository when possible.

## Suggested Future Improvements

- Add OCR support for scanned resumes.
- Add a configurable and expandable skill taxonomy.
- Improve job matching with semantic embeddings.
- Add weighted ATS rules for formatting, sections, dates, links, and measurable achievements.
- Add unit and integration tests for the analyzer, parser, database, and report generator.
- Add resume history viewing with the ability to reopen past analyses.
- Add report customization and better PDF styling.
- Add configurable API/provider support.
- Add structured logging and user-friendly diagnostics.
- Add automated CI checks for syntax, tests, and packaging.

## Build Verification

The Python source files in the supplied project were statically compiled with Python's `compileall` check successfully. This verifies that the source files are syntactically valid; it does not replace functional or UI testing.

## License

No license file was included in the supplied project. Add an appropriate `LICENSE` file before distributing the repository publicly.
