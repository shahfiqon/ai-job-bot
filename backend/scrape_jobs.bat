@echo off
REM Job Scraping Script for Windows Task Scheduler
REM This script runs the job scraping command with predefined parameters
REM Intended to be run every 3 hours via Windows Task Scheduler

REM Get the directory where this script is located
cd /d "%~dp0"

REM Set up logging
if not exist "logs" mkdir "logs"
set TIMESTAMP=%date:~10,4%%date:~4,2%%date:~7,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set TIMESTAMP=%TIMESTAMP: =0%
set LOG_FILE=logs\scrape_%TIMESTAMP%.log

echo [%date% %time%] Starting job scraping... >> "%LOG_FILE%" 2>&1
echo [%date% %time%] Starting job scraping...

REM Run the scraping command using PDM
pdm run jobbot scrape --search-term "python OR rust" --location "usa" --results-wanted 200 >> "%LOG_FILE%" 2>&1

REM Check exit code
if %ERRORLEVEL% EQU 0 (
    echo [%date% %time%] Job scraping completed successfully >> "%LOG_FILE%" 2>&1
    echo [%date% %time%] Job scraping completed successfully
    exit /b 0
) else (
    echo [%date% %time%] Job scraping failed with exit code: %ERRORLEVEL% >> "%LOG_FILE%" 2>&1
    echo [%date% %time%] Job scraping failed with exit code: %ERRORLEVEL%
    exit /b %ERRORLEVEL%
)

