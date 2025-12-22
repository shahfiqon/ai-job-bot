# Job Scraping Script for Windows Task Scheduler
# This script runs the job scraping command with predefined parameters
# Intended to be run every 3 hours via Windows Task Scheduler

# Get the directory where this script is located
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

# Set up logging
$LogDir = Join-Path $ScriptDir "logs"
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir | Out-Null
}
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$LogFile = Join-Path $LogDir "scrape_$Timestamp.log"

# Function to log messages
function Write-Log {
    param([string]$Message)
    $LogMessage = "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $Message"
    Write-Host $LogMessage
    Add-Content -Path $LogFile -Value $LogMessage
}

Write-Log "Starting job scraping..."

# Run the scraping command using PDM and redirect all output to log file
try {
    $Output = pdm run jobbot scrape `
        --search-term "python OR rust" `
        --location "usa" `
        --results-wanted 200 2>&1
    
    # Write output to log file
    $Output | ForEach-Object { Add-Content -Path $LogFile -Value $_ }
    
    # Check if the command succeeded
    if ($LASTEXITCODE -eq 0) {
        Write-Log "Job scraping completed successfully"
        exit 0
    } else {
        Write-Log "Job scraping failed with exit code: $LASTEXITCODE"
        exit $LASTEXITCODE
    }
}
catch {
    Write-Log "Job scraping failed with error: $_"
    exit 1
}

