@echo off
REM ============================================================
REM  SSN Redactor - One-Click Setup & Build
REM ============================================================
REM  This script does EVERYTHING for you:
REM    1. Checks if Python is installed (installs it if not)
REM    2. Checks if Tesseract OCR is installed (installs it if not)
REM    3. Installs all Python dependencies
REM    4. Builds the SSN Redactor.exe
REM
REM  Just double-click this file or run: setup.bat
REM ============================================================

echo.
echo ============================================================
echo   SSN Redactor - Setup ^& Build
echo ============================================================
echo.

REM --- Step 1: Check Python ---
echo [1/4] Checking Python...
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo       Python not found. Installing Python 3.12...
    winget install Python.Python.3.12 --accept-package-agreements --accept-source-agreements
    if %ERRORLEVEL% NEQ 0 (
        echo.
        echo  ERROR: Could not install Python automatically.
        echo  Please install Python 3.12 manually from:
        echo  https://www.python.org/downloads/
        echo  Make sure to check "Add Python to PATH" during install.
        pause
        exit /b 1
    )
    echo       Python installed. You may need to restart this script
    echo       if the next steps fail.
    echo.
) else (
    for /f "tokens=*" %%i in ('python --version 2^>^&1') do echo       Found %%i
)

REM --- Step 2: Check Tesseract ---
echo.
echo [2/4] Checking Tesseract OCR...
where tesseract >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo       Tesseract not found. Installing...
    winget install UB-Mannheim.TesseractOCR --accept-package-agreements --accept-source-agreements
    if %ERRORLEVEL% NEQ 0 (
        echo.
        echo  WARNING: Could not install Tesseract automatically.
        echo  JPG redaction will not work without it.
        echo  PDF redaction will still work fine.
        echo  To install manually, visit:
        echo  https://github.com/UB-Mannheim/tesseract/wiki
        echo.
    ) else (
        echo       Tesseract installed.
    )
) else (
    echo       Found Tesseract OCR
)

REM --- Step 3: Install Python packages ---
echo.
echo [3/4] Installing Python packages...
pip install -r requirements-dev.txt
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo  ERROR: Failed to install Python packages.
    echo  Make sure Python and pip are in your PATH.
    echo  Try closing and reopening this terminal, then run setup.bat again.
    pause
    exit /b 1
)
echo       Packages installed.

REM --- Step 4: Build the exe ---
echo.
echo [4/4] Building SSN Redactor...
echo       This may take a minute...
echo.
pyinstaller --noconfirm --windowed --name "SSN Redactor" --collect-all customtkinter ssn_redactor\gui.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo  ERROR: Build failed. Check the output above for errors.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo   SUCCESS!
echo ============================================================
echo.
echo   Your app is ready:
echo.
echo       dist\SSN Redactor\SSN Redactor.exe
echo.
echo   You can copy the entire "dist\SSN Redactor" folder
echo   anywhere and double-click SSN Redactor.exe to run.
echo ============================================================
echo.
pause
