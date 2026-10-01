# AI Resume Analyzer 
 
An AI-assisted desktop application for resume analysis, ATS-oriented readiness scoring, job-description matching, skill extraction, improvement suggestions, analysis history, and PDF report generation. 
 
> **Application type:** Desktop GUI · **Primary platform:** Windows · **Language:** Python 
 
## Key Features 
 
- PDF and DOCX resume support 
- Automatic OCR fallback for scanned/image-based PDFs 
- Transparent, deterministic **ATS Readiness** rubric 
- Job-description matching using **Gemini contextual assessment** when enabled 
- Local fallback matching using **TF-IDF similarity + technical-skill coverage** 
- Technical and soft-skill extraction 
- Missing keywords and missing job skills 
- Strengths, weaknesses, grammar suggestions, and recommendations 
- Local SQLite history that **does not store raw resume/JD text** 
- Optional Gemini AI mode with an explicit privacy disclosure/control 
- A4 PDF report export 
- Native packaging through PyInstaller with a cross-platform Python build script## 📸 Application Preview

<!-- Add your application screenshots to `docs/images/` -->
<img width="1917" height="1030" alt="image" src="https://github.com/user-attachments/assets/4c1d9980-6d8e-4766-9502-00340b1304f0" />

## Architecture 
 
```text 
PDF / DOCX Resume 
        | 
        v 
File Validation 
        | 
        v 
Text Extraction 
  |             | 
PDF           DOCX 
 |              | 
 +---- OCR -----+ 
        | 
        v 
Resume Text + Optional Job Description 
        | 
        +----------------------+ 
        |                      | 
   Gemini enabled?          Local mode 
        |                      | 
        v                      v 
Gemini qualitative       Local analyzer 
feedback + contextual    + TF-IDF matching 
job matching            + skill coverage 
        |                      | 
        +----------+-----------+ 
                   | 
                   v 
         Deterministic ATS Rubric 
                   | 
             +-----+-----+ 
             |           | 
             v           v 
        GUI Dashboard  SQLite History 
             | 
             v 
         PDF Report 
``` 
 
## ATS Readiness 
 
The application does **not** claim to reproduce a specific employer's ATS score. 
 
Instead, it calculates a reproducible **ATS Readiness** score from observable resume evidence: 
 
- Contact and professional links 
- Common resume sections 
- Technical skills 
- Measurable impact 
- Action-oriented language 
- Text parseability 
- Job relevance when a target job description is supplied 
 
The score is calculated locally and is therefore independent of whether Gemini is enabled. 
 
## Job Matching 
 
There are two matching modes: 
 
### Gemini mode 
 
When enabled, Gemini evaluates job fit contextually across responsibilities, required skills, tools, seniority, and relevant experience. The model is instructed not to invent qualifications or achievements. 
 
### Local mode 
 
The local matcher uses: 
 
- TF-IDF document similarity 
- Unigram and bigram features 
- Technical-skill coverage using a canonical skill list and aliases 
 
This is more informative than simple word-count overlap while remaining fully local. 
 
## OCR Support 
 
Text-based PDFs are parsed directly with PyMuPDF. If too little text is extracted, the application automatically attempts OCR using Tesseract. 
 
Install the Python dependencies with: 
 
```bash 
python -m pip install -r ResumeAnalyzer/requirements.txt 
``` 
 
A **Tesseract OCR executable must also be installed on the machine**. On Windows, you can optionally configure its path in `.env`: 
 
```env 
TESSERACT_CMD=C:\\Program Files\\Tesseract-OCR\\tesseract.exe 
``` 
 
OCR can be disabled with: 
 
```env 
OCR_ENABLED=false 
``` 
 
## Privacy 
 
The application follows a privacy-by-default approach for local history: 
 
- Raw resume text is not stored in SQLite. 
- Job descriptions are not stored in SQLite. 
- Analysis results and filename/timestamp metadata are stored locally. 
- On startup, legacy raw text from older database records is cleared. 
 
### Gemini privacy control 
 
Gemini is optional. The UI explicitly tells the user that enabling Gemini sends extracted resume/JD text to the configured Google Gemini API. 
 
When Gemini is disabled, analysis remains local and no Gemini request is made. 
 
Review the applicable Google service terms and privacy requirements before processing confidential resumes. 
 
## Technology Stack 
 
| Component | Technology | 
|---|---| 
| GUI | CustomTkinter | 
| PDF extraction | PyMuPDF | 
| DOCX extraction | python-docx | 
| OCR | Tesseract + pytesseract + Pillow | 
| Job matching | scikit-learn TF-IDF | 
| AI | Google Gemini API | 
| Database | SQLite | 
| PDF reports | ReportLab | 
| Packaging | PyInstaller | 
 
## Project Structure 
 
```text 
Project/ 
├── README.md 
├── LICENSE 
├── .gitignore 
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
    └── assets/ 
``` 
 
Do not commit `.env`, `.venv`, `dist`, `build`, database files, logs, or generated reports. 
 
## Development Setup 
 
Python 3.11 or newer is recommended. 
 
### Windows PowerShell 
 
```powershell 
cd "C:\path\to\Project\ResumeAnalyzer" 
python -m venv .venv 
.venv\Scripts\activate 
python -m pip install -r requirements.txt 
Copy-Item .env.example .env 
``` 
 
Edit `.env` if you want Gemini and/or OCR configuration. 
 
Run the application: 
 
```powershell 
python app.py 
``` 
 
## Build 
 
The primary build workflow is implemented in Python, so the same command structure works on Windows, macOS, and Linux: 
 
```bash 
cd ResumeAnalyzer 
python build.py 
``` 
 
`build.bat` is retained as a Windows convenience wrapper. 
 
The build script creates a native PyInstaller one-directory application for the operating system on which it is executed: 
 
```text 
ResumeAnalyzer/dist/ResumeAnalyzer_Portable/ 
``` 
 
A Windows build contains `ResumeAnalyzer.exe`; other operating systems receive their native executable format. 
 
## Security and Configuration 
 
`.env` is intentionally ignored by Git. Use `.env.example` as a template: 
 
```env 
GEMINI_API_KEY=your_gemini_api_key_here 
GEMINI_MODEL=gemini-1.5-flash 
MAX_PDF_MB=5 
OCR_ENABLED=true 
TESSERACT_CMD= 
``` 
 
Never commit an actual API key. 
 
## Current Limitations 
 
- Local job matching is still text-based; Gemini provides contextual matching only when enabled. 
- OCR depends on a locally installed Tesseract executable and works best on clear scans. 
- ATS Readiness is an application-specific rubric, not a verified employer ATS score. 
- No automated test suite is included yet. 
- PyInstaller builds are native to the current operating system; cross-compiling a Windows executable is not provided. 
 
## Future Improvements 
 
- Add automated unit/integration tests. 
- Add configurable industry-specific skill taxonomies. 
- Add embedding-based local semantic matching. 
- Add more detailed resume-format checks. 
- Add user-selectable retention/export controls. 
- Add CI checks for linting, tests, and packaging. 
 
## License 
 
See [LICENSE](LICENSE). 
