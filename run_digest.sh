#!/bin/bash
# Simple script to run the Slack Daily Digest Agent

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

source venv/bin/activate
export $(cat .env | grep -v '^#' | xargs)
python agent.py

