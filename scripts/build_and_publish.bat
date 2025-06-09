@echo off
echo SFTP GUI Manager - Build and Publish
echo ===================================

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
set DRY_RUN=
set SKIP_BUILD=
set SKIP_GIT=

:parse_args
if "%~1"=="" goto :end_parse_args
if /i "%~1"=="--version" (
    set VERSION=%~2
    shift
    shift
    goto :parse_args
)
if /i "%~1"=="--dry-run" (
    set DRY_RUN=--dry-run
    shift
    goto :parse_args
)
if /i "%~1"=="--skip-build" (
    set SKIP_BUILD=--skip-build
    shift
    goto :parse_args
)
if /i "%~1"=="--skip-git" (
    set SKIP_GIT=--skip-git
    shift
    goto :parse_args
)
shift
goto :parse_args

:end_parse_args

REM Build command
set CMD=python build_and_publish.py
if defined VERSION set CMD=%CMD% --version %VERSION%
if defined DRY_RUN set CMD=%CMD% %DRY_RUN%
if defined SKIP_BUILD set CMD=%CMD% %SKIP_BUILD%
if defined SKIP_GIT set CMD=%CMD% %SKIP_GIT%

echo Running: %CMD%
%CMD%

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✅ Build and publish completed successfully!
) else (
    echo.
    echo ❌ Build and publish failed!
    pause
    exit /b 1
)

pause
