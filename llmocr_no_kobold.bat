@echo off
setlocal enabledelayedexpansion



:setup
:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed. Please install Python 3.8 or higher.
    exit /b 1
)

:: Create and activate virtual environment
echo Creating virtual environment...
if not exist "venv" (
    python -m venv venv
)

:: Activate virtual environment and install packages
echo Activating virtual environment and installing packages...
call venv\Scripts\activate.bat

:: Install required packages
echo Installing Python packages...
python -m pip install --upgrade pip
pip install -r requirements.txt
cls
@echo off
setlocal enabledelayedexpansion
echo ---------------------------
echo Results will appear here...
echo ---------------------------

python ./src/llmocr-gui.py

pause
REM Deactivate the virtual environment
deactivate
