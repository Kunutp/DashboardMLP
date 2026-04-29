@echo off
echo ====================================
echo Starting Water Quality Dashboard...
echo ====================================
echo.

cd /d "%~dp0"

REM Activate virtual environment and run Streamlit
call .venv\Scripts\activate.bat
streamlit run app.py

pause
