# Quick Start Guide 🚀

Get your Slack Daily Digest Agent running in 5 minutes!

## Step 1: Create Slack App (5 min)

1. Go to https://api.slack.com/apps
2. Click **"Create New App"** → **"From scratch"**
3. Name: `Daily Digest Bot`, select your workspace
4. Go to **"OAuth & Permissions"** in sidebar
5. Scroll to **"Scopes"** → **"Bot Token Scopes"**, add:
   - `channels:history`
   - `channels:read`
   - `chat:write`
   - `im:write`
   - `users:read`
6. Scroll up, click **"Install to Workspace"**
7. Copy your **"Bot User OAuth Token"** (starts with `xoxb-`)

## Step 2: Invite Bot to Channels

In each Slack channel you want to monitor:
```
/invite @Daily Digest Bot
```

## Step 3: Get Your User ID

1. Click your profile picture in Slack
2. Click **"View profile"**
3. Click **"More"** (three dots) → **"Copy member ID"**

## Step 4: Get Channel IDs

Right-click each channel → **"View channel details"** → scroll to bottom → **Copy ID**

## Step 5: Setup Project

```bash
cd /path/to/slack-daily-digest

# Run setup script
./setup.sh

# Edit .env file with your credentials
nano .env
```

Fill in:
```bash
SLACK_BOT_TOKEN=xoxb-your-token-from-step-1
SLACK_USER_ID=U1234567890  # Your user ID from step 3
SLACK_CHANNELS=C111,C222,C333  # Channel IDs from step 4 (comma-separated)
ANTHROPIC_API_KEY=sk-ant-your-key  # From console.anthropic.com
```

## Step 6: Test It!

```bash
# Activate environment
source venv/bin/activate

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

# Optional: List channels to verify
python list_channels.py

# Run the agent!
python agent.py
```

You should get a Slack DM with your digest! 🎉

## Step 7: Schedule Daily (Optional)

### macOS - Using launchd

```bash
# Edit the plist file to set your preferred time
nano ~/Library/LaunchAgents/com.slackdigest.daily.plist
```

Paste this (adjust the Hour to your preference):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.slackdigest.daily</string>
    <key>ProgramArguments</key>
    <array>
        <string>/path/to/slack-daily-digest/run_daily.sh</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>9</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>/path/to/slack-daily-digest/daily_digest.log</string>
    <key>StandardErrorPath</key>
    <string>/path/to/slack-daily-digest/daily_digest.log</string>
</dict>
</plist>
```

Then load it:

```bash
launchctl load ~/Library/LaunchAgents/com.slackdigest.daily.plist
launchctl list | grep slackdigest
```

### Linux - Using cron

```bash
crontab -e

# Add this line (runs at 9 AM daily):
0 9 * * * /path/to/slack-daily-digest/run_daily.sh
```

## Troubleshooting

### "missing_scope" error
→ Go back to Step 1, make sure you added ALL the scopes

### "channel_not_found" error
→ Did you invite the bot? Go back to Step 2

### No messages found
→ Check if there are messages in the last 24 hours
→ Verify bot is in the channels: `python list_channels.py`

### Check logs
```bash
tail -f daily_digest.log
```

## Done! 🎉

Your agent will now:
- ✅ Monitor your Slack channels daily
- ✅ Use AI to find important messages
- ✅ Send you a curated digest via DM
- ✅ Run automatically on schedule

Need help? Check the full README.md

