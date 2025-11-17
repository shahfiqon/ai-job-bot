#!/bin/bash

# Job Scraping Script for Cron
# This script runs the job scraping command with predefined parameters
# Intended to be run every 3 hours via cron

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

# Set up logging
LOG_DIR="$SCRIPT_DIR/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/scrape_$(date +%Y%m%d_%H%M%S).log"

# Function to log messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "Starting job scraping..."

# Run the scraping command using PDM and redirect all output to log file
{
    pdm run jobbot scrape \
        --search-term "python OR rust" \
        --location "usa" \
        --results-wanted 200
} >> "$LOG_FILE" 2>&1

# Capture exit code
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    log "Job scraping completed successfully"
else
    log "Job scraping failed with exit code: $EXIT_CODE"
fi

exit $EXIT_CODE

