@echo off
setlocal

python build.py
if errorlevel 1 (
    echo.
    echo Build failed. Check the messages above.
    exit /b 1
)

endlocal
