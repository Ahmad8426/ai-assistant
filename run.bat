@echo off
echo Starting AI Assistant...

:: Check if virtual environment exists and activate it
if exist venv\Scripts\activate (
    call venv\Scripts\activate
    echo Virtual environment activated
) else (
    echo No virtual environment found, using system Python
)

:: Run the application
python app.py

pause
