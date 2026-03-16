@echo off
REM Build SSN Redactor as a standalone Windows exe.
REM Run from the project root: build.bat

echo Building SSN Redactor...

pyinstaller ^
    --onefile ^
    --windowed ^
    --name "SSN Redactor" ^
    --collect-all customtkinter ^
    ssn_redactor\gui.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo Build successful!
    echo Executable: dist\SSN Redactor.exe
) else (
    echo.
    echo Build failed. Check the output above for errors.
    exit /b 1
)
