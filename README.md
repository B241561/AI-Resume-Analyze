# AI Resume Analyzer

> **AI-assisted desktop application for resume analysis, ATS-oriented readiness scoring, job-description matching, skill extraction, improvement suggestions, analysis history, and PDF report generation.**

**Application:** Desktop GUI · **Platform:** Windows-first · **Language:** Python

---

## 📸 Application Preview

<!-- Add your application screenshots to `docs/images/` -->
<img width="1917" height="1030" alt="image" src="https://github.com/user-attachments/assets/4c1d9980-6d8e-4766-9502-00340b1304f0" />



> **Tip:** Replace the image paths above with your actual screenshots. Keeping screenshots inside `docs/images/` makes the README portable across GitHub and local clones.

---

## ✨ Overview

**AI Resume Analyzer** is a Python-based desktop application designed to help students and job seekers understand how well their resume is prepared for a target role.

The application combines:

* Deterministic local resume analysis
* ATS-oriented readiness scoring
* Job-description matching
* Technical and soft-skill extraction
* Optional Gemini-powered contextual analysis
* OCR fallback for scanned PDFs
* Local analysis history
* PDF report generation

The system is designed around a simple principle:

> **Make resume analysis understandable, reproducible, and actionable rather than presenting an unexplained score.**

---

## 🚀 Key Features

### 📄 Resume Processing

* PDF resume support
* DOCX resume support
* Automatic text extraction
* OCR fallback for image/scanned PDFs
* File-size validation
* Configurable OCR support through Tesseract

### 📊 ATS Readiness Analysis

The application calculates an application-specific **ATS Readiness** score using observable resume evidence.

It evaluates:

* Contact information
* Professional links
* Standard resume sections
* Technical skills
* Measurable achievements
* Action-oriented language
* Text parseability
* Job relevance when a JD is provided

The score is **deterministic and calculated locally**, so enabling or disabling Gemini does not change the underlying ATS Readiness rubric.

> **Important:** ATS Readiness is an application-specific assessment. It does **not** claim to reproduce the proprietary scoring system of any particular employer or ATS vendor.

### 🎯 Job Description Matching

The analyzer supports two approaches.

#### Gemini contextual matching

When Gemini is enabled, the application can evaluate:

* Responsibilities
* Required skills
* Tools and technologies
* Relevant experience
* Seniority
* Job-specific relevance

The model is instructed to avoid inventing qualifications, experience, or achievements.

#### Local matching

When Gemini is disabled, matching remains completely local using:

* TF-IDF similarity
* Unigram features
* Bigram features
* Technical-skill coverage
* Canonical skill names
* Skill aliases

This provides a transparent local alternative without requiring an external AI API.

### 🧠 Skill Extraction

The analyzer identifies relevant:

* Programming languages
* Frameworks
* Libraries
* Databases
* Developer tools
* Cloud technologies
* Technical concepts
* Soft skills

It can also identify skills appearing in a job description but missing from the resume.

### 💡 Improvement Suggestions

The analysis can highlight:

* Resume strengths
* Potential weaknesses
* Missing keywords
* Missing job skills
* Grammar issues
* Action-language improvements
* General recommendations

### 🗃️ Local Analysis History

Analysis history is stored using SQLite.

The database stores analysis results and metadata rather than raw resume/JD content.

Stored information can include:

* Filename
* Timestamp
* Analysis results
* Scores
* Extracted metadata

Raw resume text and job-description text are **not intended to be persisted**.

Legacy raw-text fields from older database records are cleared during startup.

### 📑 PDF Reports

Generate an A4 PDF report containing the analysis results for easier:

* Sharing
* Review
* Printing
* Portfolio documentation
* Personal tracking

### 🔒 Privacy Controls

Gemini is optional.

When Gemini is disabled:

```text
Resume → Local Processing → Local Analysis
```

No Gemini API request is made.

When Gemini is enabled:

```text
Resume/JD → Local Extraction → Gemini API → Contextual Analysis
```

The UI explicitly informs the user that enabling Gemini sends extracted resume/JD text to the configured Google Gemini API.

---

## 🖼️ System Architecture

![AI Resume Analyzer Architecture](docs/images/architecture.png)

### Architecture Flow

```text
                    ┌─────────────────────┐
                    │    PDF / DOCX       │
                    │      Resume         │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   File Validation   │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   Text Extraction   │
                    │                     │
                    │ PDF → PyMuPDF       │
                    │ DOCX → python-docx │
                    └──────────┬──────────┘
                               │
                     Insufficient text?
                          ┌────┴────┐
                         Yes       No
                          │         │
                          ▼         │
                    ┌───────────┐   │
                    │   OCR     │   │
                    │Tesseract  │   │
                    └─────┬─────┘   │
                          │         │
                          └────┬────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   Resume Text + JD  │
                    └──────────┬──────────┘
                               │
                    ┌──────────┴──────────┐
                    │                     │
                    ▼                     ▼
             Gemini Enabled?         Local Mode
                    │                     │
                    ▼                     ▼
             Gemini Contextual      TF-IDF + Skill
                Analysis             Coverage
                    │                     │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ ATS Readiness Engine│
                    │   Deterministic     │
                    └──────────┬──────────┘
                               │
                 ┌─────────────┴─────────────┐
                 │                           │
                 ▼                           ▼
          ┌──────────────┐            ┌──────────────┐
          │ GUI Dashboard│            │ SQLite History│
          └──────┬───────┘            └──────────────┘
                 │
                 ▼
          ┌──────────────┐
          │  PDF Report  │
          └──────────────┘
```

---

## 🧮 ATS Readiness

The application deliberately separates **ATS Readiness** from AI-generated qualitative feedback.

The score is calculated from observable resume evidence.

### Example scoring dimensions

| Dimension           | What is evaluated                               |
| ------------------- | ----------------------------------------------- |
| Contact Information | Email, phone and professional identity          |
| Professional Links  | LinkedIn, GitHub, portfolio, etc.               |
| Resume Sections     | Education, experience, projects, skills, etc.   |
| Technical Skills    | Relevant technical skill presence               |
| Measurable Impact   | Numbers, percentages, scale, measurable results |
| Action Language     | Use of meaningful action-oriented wording       |
| Parseability        | Extractable and machine-readable text           |
| Job Relevance       | Alignment with a supplied JD                    |

The resulting score should be interpreted as:

> **"How ready does this resume appear according to this application's transparent rubric?"**

It should not be interpreted as an actual employer ATS score.

---

## 🎯 Job Matching Pipeline

### Gemini Mode

```text
Resume
   │
   ├── Skills
   ├── Experience
   ├── Projects
   └── Keywords
          │
          ▼
    Gemini Contextual
       Assessment
          │
          ▼
      Job Fit Analysis
```

### Local Mode

```text
Resume ──────────────┐
                     │
                     ▼
               TF-IDF Vectorizer
                     │
                     ▼
               Cosine Similarity
                     │
                     ├──────────────┐
                     │              │
                     ▼              ▼
             Skill Extraction   Skill Aliases
                     │              │
                     └──────┬───────┘
                            ▼
                    Technical Coverage
                            │
                            ▼
                     Local Job Match
```

---

## 🔍 OCR Pipeline

Text-based PDFs are processed directly through **PyMuPDF**.

If the extracted text is below the configured threshold, the application can attempt OCR.

```text
PDF
 │
 ▼
PyMuPDF Extraction
 │
 ├── Enough text ───────► Continue
 │
 └── Too little text
             │
             ▼
        Tesseract OCR
             │
             ▼
        OCR Text
             │
             ▼
        Continue Analysis
```

OCR requires a locally installed **Tesseract executable**.

Example Windows configuration:

```env
TESSERACT_CMD=C:\\Program Files\\Tesseract-OCR\\tesseract.exe
```

OCR can be disabled:

```env
OCR_ENABLED=false
```

---

## 🔐 Privacy

The application follows a privacy-by-default approach for local analysis history.

### Local processing

When Gemini is disabled:

* Resume extraction happens locally.
* Local matching happens locally.
* ATS Readiness is calculated locally.
* SQLite history is stored locally.
* No Gemini request is made.

### SQLite history

Raw resume text is not stored in the intended database schema.

Job descriptions are not stored as raw text.

Stored information is primarily:

* Analysis results
* Scores
* Filename/metadata
* Timestamp
* Other derived analysis information

Legacy raw-text data from previous database versions is cleared during application startup.

### Gemini mode

Gemini is an optional external processing component.

When enabled, extracted resume/JD text is sent to the configured Google Gemini API.

Users should review applicable Google service terms and privacy requirements before processing confidential resumes.

---

## 🛠️ Technology Stack

| Component       | Technology                       |
| --------------- | -------------------------------- |
| Language        | Python                           |
| GUI             | CustomTkinter                    |
| PDF Extraction  | PyMuPDF                          |
| DOCX Extraction | python-docx                      |
| OCR             | Tesseract + pytesseract + Pillow |
| Local Matching  | scikit-learn TF-IDF              |
| AI Analysis     | Google Gemini API                |
| Database        | SQLite                           |
| PDF Reports     | ReportLab                        |
| Packaging       | PyInstaller                      |
| Configuration   | python-dotenv                    |

---

## 📁 Project Structure

```text
Project/
│
├── README.md
├── LICENSE
├── .gitignore
│
├── docs/
│   └── images/
│       ├── dashboard.png
│       ├── analysis.png
│       ├── job-matching.png
│       ├── history.png
│       ├── architecture.png
│       └── pdf-report.png
│
└── ResumeAnalyzer/
    ├── app.py
    ├── ui.py
    ├── analyzer.py
    ├── pdf_reader.py
    ├── report_generator.py
    ├── database.py
    ├── config.py
    ├── requirements.txt
    ├── .env.example
    ├── build.py
    ├── build.bat
    ├── ResumeAnalyzer.spec
    ├── README.txt
    │
    └── assets/
```

---

## ⚙️ Development Setup

### Requirements

Recommended:

* Python **3.11+**
* Windows for the primary desktop workflow
* Tesseract OCR if OCR functionality is required
* Gemini API key if Gemini functionality is required

### 1. Clone the repository

```bash
git clone <your-repository-url>
cd Project/ResumeAnalyzer
```

### 2. Create a virtual environment

#### Windows PowerShell

```powershell
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Configure environment variables

Copy the example configuration:

```powershell
Copy-Item .env.example .env
```

Example:

```env
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-1.5-flash

MAX_PDF_MB=5

OCR_ENABLED=true
TESSERACT_CMD=
```

### 5. Run the application

```powershell
python app.py
```

---

## 🤖 Gemini Configuration

Gemini functionality is optional.

Configure the API key through `.env`:

```env
GEMINI_API_KEY=your_api_key
```

Never hard-code or commit an API key.

The application should continue operating in local mode when Gemini is unavailable or disabled.

---

## 📦 Build

The project uses a Python-based PyInstaller build workflow.

From the `ResumeAnalyzer` directory:

```bash
python build.py
```

The resulting application is generated under:

```text
ResumeAnalyzer/dist/ResumeAnalyzer_Portable/
```

A Windows build contains:

```text
ResumeAnalyzer.exe
```

`build.bat` is retained as a Windows convenience wrapper.

### Native builds

PyInstaller produces an executable for the operating system on which the build is performed.

```text
Windows → Windows executable
macOS   → macOS application
Linux   → Linux executable
```

Cross-compiling a Windows executable from another operating system is not provided by this project.

---

## 🧪 Testing & Quality

The project should be tested across the major processing paths:

```text
PDF
 ├── Text-based PDF
 └── Scanned PDF → OCR

DOCX
 └── Text extraction

Gemini
 ├── Enabled
 └── Disabled / unavailable

Database
 ├── New database
 └── Legacy database cleanup

Reports
 └── A4 PDF generation

Packaging
 └── PyInstaller build
```

### Recommended test categories

* File validation
* PDF extraction
* DOCX extraction
* OCR fallback
* Skill extraction
* ATS scoring
* Local job matching
* Gemini integration
* SQLite initialization
* Legacy-data cleanup
* PDF report generation
* GUI startup
* PyInstaller packaging

---

## 🛡️ Security & Configuration

The following files and directories should **never** be committed:

```text
.env
.venv/
dist/
build/
*.db
*.sqlite
*.sqlite3
*.log
generated reports
```

Example `.gitignore` entries:

```gitignore
.env
.venv/
__pycache__/
*.pyc

build/
dist/

*.db
*.sqlite
*.sqlite3

*.log

reports/
```

### API key security

Never place API keys directly inside:

* Python source files
* README files
* Git commits
* Screenshots
* Configuration examples

Use environment variables instead.

---

## 📊 Example Analysis Flow

![Analysis Flow](docs/images/analysis-flow.png)

A typical analysis follows:

```text
1. User selects resume
          ↓
2. File validation
          ↓
3. PDF/DOCX extraction
          ↓
4. OCR fallback if required
          ↓
5. Resume structure analysis
          ↓
6. Skill extraction
          ↓
7. ATS Readiness calculation
          ↓
8. Optional Job Description matching
          ↓
9. Gemini contextual analysis (optional)
          ↓
10. Recommendations
          ↓
11. Save derived results to SQLite
          ↓
12. Generate PDF report
```

---

## 📄 Generated Report

![PDF Report](docs/images/pdf-report.png)

The report is designed for A4 paper and can contain:

* Resume overview
* ATS Readiness
* Job-match information
* Extracted skills
* Missing skills
* Strengths
* Weaknesses
* Recommendations
* Additional analysis information

---

## 🧩 Design Principles

### 1. Local-first

Core resume processing should remain functional without external AI services.

### 2. Explainability

The application should provide evidence and reasons behind analysis rather than presenting unexplained numbers.

### 3. Deterministic scoring

The ATS Readiness calculation uses a reproducible local rubric.

### 4. Optional AI

Gemini enhances contextual analysis but is not required for the core application.

### 5. Privacy awareness

Raw resume/JD content is not intentionally persisted in local history.

### 6. Graceful fallback

When optional services such as Gemini or OCR are unavailable, the application should provide an appropriate local/fallback workflow whenever possible.

---

## ⚠️ Current Limitations

* Local job matching remains primarily text-based.
* Gemini provides contextual matching only when enabled and configured.
* OCR quality depends on document quality and the installed Tesseract engine.
* ATS Readiness is an application-specific rubric and is not an employer ATS score.
* Semantic matching is not currently performed entirely locally through embeddings.
* Industry-specific skill taxonomies are not yet fully configurable.
* Resume visual-format analysis remains limited.
* PyInstaller builds are native to the current operating system.

---

## 🔮 Future Improvements

Potential future development includes:

* [ ] Automated unit and integration test suite
* [ ] Embedding-based local semantic matching
* [ ] Industry-specific skill taxonomies
* [ ] Advanced resume formatting analysis
* [ ] Section-level resume diagnostics
* [ ] Configurable data-retention controls
* [ ] Analysis export/import
* [ ] CI-based linting and testing
* [ ] Automated packaging validation
* [ ] More detailed job-fit explanations
* [ ] Additional document formats
* [ ] Improved OCR preprocessing
* [ ] Resume version comparison
* [ ] Interactive analytics dashboard

---

## 📌 Project Status

**Status:** Active Development

The project currently focuses on building a transparent desktop resume-analysis workflow combining deterministic local analysis with optional AI-powered contextual assessment.

---

## 📜 License

See [`LICENSE`](LICENSE) for licensing information.

---

## ⭐ Contributing

Contributions, bug reports, and feature suggestions are welcome.

Before submitting a change:

1. Keep API keys and private documents out of commits.
2. Test both local and optional-AI workflows where applicable.
3. Preserve the deterministic nature of the ATS Readiness calculation.
4. Update documentation when adding user-facing functionality.
5. Keep generated build artifacts out of source control.

---

## 👨‍💻 Project

**AI Resume Analyzer**

Built with Python, CustomTkinter, SQLite, scikit-learn, PyMuPDF, ReportLab, Tesseract OCR, and optional Google Gemini integration.

> **Analyze. Understand. Improve.**
