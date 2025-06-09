@echo off
echo SFTP GUI Manager - Create Sample Release
echo =====================================

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python not found in PATH
    echo Please install Python and add it to your PATH
    pause
    exit /b 1
)

REM Parse arguments
set VERSION=
set NO_DRY_RUN=

:parse_args
if "%~1"=="" goto :end_parse_args
if /i "%~1"=="--version" (
    set VERSION=%~2
    shift
    shift
    goto :parse_args
)
if /i "%~1"=="--no-dry-run" (
    set NO_DRY_RUN=--no-dry-run
    shift
    goto :parse_args
)
shift
goto :parse_args

:end_parse_args

REM Build command
set CMD=python scripts/create_sample_release.py
if defined VERSION set CMD=%CMD% --version %VERSION%
if defined NO_DRY_RUN set CMD=%CMD% %NO_DRY_RUN%

echo Running: %CMD%
%CMD%

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✅ Sample release created successfully!
) else (
    echo.
    echo ❌ Failed to create sample release!
    pause
    exit /b 1
)

pause
