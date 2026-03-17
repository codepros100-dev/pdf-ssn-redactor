@echo off
REM Build SSN Redactor as a standalone Windows app.
REM Run from the project root: build.bat

echo Building SSN Redactor...

pyinstaller ^
    --noconfirm ^
    --windowed ^
    --name "SSN Redactor" ^
    --collect-all customtkinter ^
    ssn_redactor\gui.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo Build successful!
    echo.
    echo App folder: dist\SSN Redactor\
    echo Run it:     dist\SSN Redactor\SSN Redactor.exe
) else (
    echo.
    echo Build failed. Check the output above for errors.
    exit /b 1
)
