@echo off
REM ===================================================================
REM  AI Knowledge Transfer & SOP Builder - one-click launcher (Windows)
REM  Double-click this file to start the app in your browser.
REM ===================================================================

REM Always run from the folder this script lives in.
cd /d "%~dp0"

REM If a local virtual environment exists, use it automatically.
if exist ".venv\Scripts\activate.bat" (
    call ".venv\Scripts\activate.bat"
)

echo Starting AI Knowledge Transfer ^& SOP Builder...
echo (A browser tab should open at http://localhost:8501)
echo Close this window or press Ctrl+C to stop the app.
echo.

REM Launch Streamlit via the Python module runner (does not depend on PATH).
python -m streamlit run app.py

REM Keep the window open if something goes wrong so you can read the error.
if errorlevel 1 (
    echo.
    echo The app stopped or failed to start. Review the message above.
    pause
)
