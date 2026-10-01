@echo off
setlocal

echo Building AI Resume Analyzer desktop app...

where python >nul 2>nul
if errorlevel 1 (
    echo Python was not found on PATH. Install Python 3.11+ and try again.
    exit /b 1
)

if not exist .env (
    copy .env.example .env
)

if not exist reports mkdir reports
if not exist temp mkdir temp

if exist build\ResumeAnalyzer rmdir /S /Q build\ResumeAnalyzer
if exist build\ResumeAnalyzer_Portable rmdir /S /Q build\ResumeAnalyzer_Portable
if exist dist\ResumeAnalyzer rmdir /S /Q dist\ResumeAnalyzer
if exist dist\ResumeAnalyzer_Portable rmdir /S /Q dist\ResumeAnalyzer_Portable
if exist dist\ResumeAnalyzer.exe del /Q dist\ResumeAnalyzer.exe

python -m pip install --upgrade pip
if errorlevel 1 goto build_failed

python -m pip install -r requirements.txt
if errorlevel 1 goto build_failed

python -m PyInstaller --noconfirm --clean --distpath dist --workpath build ResumeAnalyzer.spec
if errorlevel 1 goto build_failed

if not exist dist\ResumeAnalyzer_Portable\ResumeAnalyzer.exe goto build_failed
if not exist dist\ResumeAnalyzer_Portable\_internal goto build_failed

if not exist dist\ResumeAnalyzer_Portable\assets mkdir dist\ResumeAnalyzer_Portable\assets
if not exist dist\ResumeAnalyzer_Portable\reports mkdir dist\ResumeAnalyzer_Portable\reports
if not exist dist\ResumeAnalyzer_Portable\temp mkdir dist\ResumeAnalyzer_Portable\temp

xcopy /E /I /Y assets dist\ResumeAnalyzer_Portable\assets >nul
xcopy /E /I /Y reports dist\ResumeAnalyzer_Portable\reports >nul
xcopy /E /I /Y temp dist\ResumeAnalyzer_Portable\temp >nul
copy /Y .env.example dist\ResumeAnalyzer_Portable\.env.example >nul
copy /Y README.txt dist\ResumeAnalyzer_Portable\README.txt >nul

if not exist dist\ResumeAnalyzer_Portable\.env.example goto build_failed
if not exist dist\ResumeAnalyzer_Portable\README.txt goto build_failed

echo.
echo Build complete.
echo Output: dist\ResumeAnalyzer_Portable\ResumeAnalyzer.exe
echo Zip and share the dist\ResumeAnalyzer_Portable folder.

endlocal
exit /b 0

:build_failed
echo.
echo Build failed. Check the messages above for the exact PyInstaller or dependency error.
endlocal
exit /b 1
