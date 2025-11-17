# Cron Job Setup Guide

This guide explains how to set up a cron job to run the job scraping script every 3 hours.

## Prerequisites

1. Ensure the script is executable:
   ```bash
   chmod +x /home/shadeform/ai-job-bot/backend/scrape_jobs.sh
   ```

2. Verify the script works manually:
   ```bash
   /home/shadeform/ai-job-bot/backend/scrape_jobs.sh
   ```

## Setting Up the Cron Job

### Step 1: Open Crontab Editor

```bash
crontab -e
```

If this is your first time, you'll be asked to choose an editor. Choose your preferred editor (nano is recommended for beginners).

### Step 2: Add the Cron Job

Add the following line to your crontab file:

```bash
0 */3 * * * /home/shadeform/ai-job-bot/backend/scrape_jobs.sh >> /home/shadeform/ai-job-bot/backend/logs/cron.log 2>&1
```

**Cron Schedule Explanation:**
- `0 */3 * * *` means: run at minute 0 of every 3rd hour (00:00, 03:00, 06:00, 09:00, 12:00, 15:00, 18:00, 21:00)

### Step 3: Save and Exit

- If using **nano**: Press `Ctrl+X`, then `Y`, then `Enter`
- If using **vim**: Press `Esc`, type `:wq`, then `Enter`

## Important: Environment Variables

Cron jobs run with a minimal environment. If your script needs environment variables (like `PROXYCURL_API_KEY`, database credentials, etc.), you have two options:

### Option 1: Source Environment File in Cron (Recommended)

Modify the cron job to source your environment file:

```bash
0 */3 * * * cd /home/shadeform/ai-job-bot/backend && . .env 2>/dev/null; /home/shadeform/ai-job-bot/backend/scrape_jobs.sh >> /home/shadeform/ai-job-bot/backend/logs/cron.log 2>&1
```

**Note:** This assumes your `.env` file is in the backend directory. Adjust the path if needed.

### Option 2: Set Environment Variables in Crontab

Add environment variable definitions at the top of your crontab file (before the cron job line):

```bash
PROXYCURL_API_KEY=your_api_key_here
PATH=/usr/local/bin:/usr/bin:/bin
# Add other required environment variables here

0 */3 * * * /home/shadeform/ai-job-bot/backend/scrape_jobs.sh >> /home/shadeform/ai-job-bot/backend/logs/cron.log 2>&1
```

### Option 3: Source Shell Profile

If your environment variables are in your shell profile (`.bashrc`, `.bash_profile`, etc.):

```bash
0 */3 * * * source ~/.bashrc && /home/shadeform/ai-job-bot/backend/scrape_jobs.sh >> /home/shadeform/ai-job-bot/backend/logs/cron.log 2>&1
```

## Verify the Cron Job

### Check if Cron Job is Added

```bash
crontab -l
```

This will display all your cron jobs.

### Check Cron Service Status

```bash
sudo systemctl status cron
```

Or on some systems:
```bash
sudo systemctl status crond
```

### View Cron Logs

Check system cron logs to see if the job is running:

```bash
# On Ubuntu/Debian
grep CRON /var/log/syslog

# On CentOS/RHEL
grep CRON /var/log/cron
```

### Check Your Script Logs

The script creates timestamped log files in:
```bash
ls -lh /home/shadeform/ai-job-bot/backend/logs/
```

Also check the cron.log file:
```bash
tail -f /home/shadeform/ai-job-bot/backend/logs/cron.log
```

## Testing the Cron Job

### Test Immediately

To test without waiting 3 hours, you can temporarily set it to run every minute:

```bash
* * * * * /home/shadeform/ai-job-bot/backend/scrape_jobs.sh >> /home/shadeform/ai-job-bot/backend/logs/cron.log 2>&1
```

**Remember to change it back to `0 */3 * * *` after testing!**

### Verify Next Run Time

You can use online cron expression validators or calculate manually:
- The job runs at: 00:00, 03:00, 06:00, 09:00, 12:00, 15:00, 18:00, 21:00

## Troubleshooting

### Script Not Running

1. **Check file permissions:**
   ```bash
   ls -l /home/shadeform/ai-job-bot/backend/scrape_jobs.sh
   ```
   Should show `-rwxr-xr-x` or similar (executable)

2. **Check if PDM is in PATH:**
   Cron may not have the same PATH as your user. You might need to add:
   ```bash
   PATH=/home/shadeform/.local/bin:/usr/local/bin:/usr/bin:/bin
   ```
   at the top of your crontab.

3. **Check script shebang:**
   Ensure the first line of the script is:
   ```bash
   #!/bin/bash
   ```

### Environment Variables Not Working

- Verify your `.env` file exists and has the correct variables
- Test sourcing the environment manually:
  ```bash
  source /home/shadeform/ai-job-bot/backend/.env
  echo $PROXYCURL_API_KEY
  ```

### Database Connection Issues

If the database connection fails, ensure:
- Database is accessible from the cron environment
- Database credentials are in your environment variables
- Network/firewall rules allow the connection

## Example Complete Crontab Entry

Here's a complete example with environment setup:

```bash
# Environment variables
PATH=/home/shadeform/.local/bin:/usr/local/bin:/usr/bin:/bin
SHELL=/bin/bash

# Change to backend directory and source .env, then run script
0 */3 * * * cd /home/shadeform/ai-job-bot/backend && [ -f .env ] && . .env; /home/shadeform/ai-job-bot/backend/scrape_jobs.sh >> /home/shadeform/ai-job-bot/backend/logs/cron.log 2>&1
```

## Additional Notes

- The script creates individual timestamped log files for each run in `backend/logs/`
- The cron.log file captures any output that goes to stdout/stderr
- Logs are never automatically deleted - you may want to set up log rotation
- Consider adding email notifications for failures (cron can email you if configured)

