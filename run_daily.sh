#!/bin/bash

# Slack Daily Digest - Cron Job Script
# Add to crontab: 0 9 * * * /path/to/run_daily.sh

# Change to script directory
cd "$(dirname "$0")"

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run the agent
python agent.py >> daily_digest.log 2>&1

# Log completion
echo "Daily digest completed at $(date)" >> daily_digest.log

