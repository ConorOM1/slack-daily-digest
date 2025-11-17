# Slack Daily Digest Agent 🤖

An AI-powered agent that monitors your Slack channels and sends you a curated daily digest via DM

## Features

- 📊 Analyzes messages from multiple Slack channels
- 🧠 Uses **Ollama (local AI)** - completely free, runs on your Machine
- 📬 Sends daily digest via Slack DM with clickable links
- 🔔 **macOS notification** pops up when digest is ready
- 🎯 Filters out noise and focuses on important content
- 🔒 **Private** - no external API calls, all AI processing happens locally

## Quick Start

### 1. Get Your Slack Credentials

**Get your User Token and Cookie (from Slack Desktop App):**

**Step 1: Get your Token (xoxc-...)**

1. Open Slack Desktop App
2. Press **Cmd + Option + I** (opens DevTools)
3. Go to **Console** tab
4. Paste this command and hit Enter:
   ```javascript
   JSON.parse(localStorage.localConfig_v2)["teams"]
   ```
5. Look through the output and find your token starting with **`xoxc-`**
6. Copy the entire token value

**Step 2: Get your Cookie (xoxd-...)**

1. Still in DevTools, go to **Application** tab (at the top)
2. On the left sidebar, expand **Cookies** (click the arrow)
3. Click on your workspace URL (e.g., `https://yourworkspace.slack.com`)
4. In the cookie table on the right, scroll and find the cookie named **`d`**
5. Click on it and copy its **Value** column (starts with **`xoxd-`**)

**Tip:** The `d` cookie is usually near the top of the cookie list

**Get Your User ID:**

1. In Slack, click your profile picture
2. Click **"View profile"**
3. Click **"⋯ More"** → **"Copy member ID"**

**Get Channel IDs:**

For each channel you want to monitor:
1. Right-click the channel name
2. Click **"View channel details"**
3. Scroll down and copy the **Channel ID**

### 2. Install Dependencies

```bash
cd <path-to>/QE/slack-daily-digest

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install packages
pip install -r requirements.txt

# Install Ollama (local AI)
brew install ollama

# Start Ollama service
brew services start ollama

# Download AI model (llama3.2 - 2GB)
ollama pull llama3.2
```

### 3. Configure Settings

Create your `.env` file:

```bash
nano .env
```

Add your credentials (no spaces around commas!):

```bash
# Slack Authentication
SLACK_BOT_TOKEN=xoxc-YOUR-TOKEN-HERE
SLACK_COOKIE=xoxd-YOUR-COOKIE-HERE

# Your Slack User ID
SLACK_USER_ID=U12345678

# Channels to monitor (comma-separated, NO SPACES)
SLACK_CHANNELS=C05ABC123,C07DEF456,C03GHI789

# Ollama Configuration (local AI)
OLLAMA_MODEL=llama3.2
OLLAMA_URL=http://localhost:11434
```

### 4. Test It!

```bash
./run_digest.sh
```

You should:
- ✅ Get a macOS notification popup
- ✅ Receive a DM in Slack with your digest
- ✅ See clickable "link" references for each message

## Automatic Daily Runs

The agent runs **weekdays at 8:30 AM** automatically via cron

**Important:** Grant Full Disk Access to `cron` or `Terminal`:
1. System Settings → Privacy & Security → Full Disk Access
2. Add `/usr/sbin/cron` or Terminal.app

## Customization

### Change Which Channels to Monitor

Edit `.env`:
```bash
SLACK_CHANNELS=C05ABC123,C07NEW456,C03ANOTHER
```

### Change When It Runs

```bash
crontab -e

# Change to 5 PM weekdays:
0 17 * * 1-5 <path-to>/slack-daily-digest/run_digest.sh >> digest.log 2>&1

# Run every day (including weekends):
30 8 * * * <path-to>/slack-daily-digest/run_digest.sh >> digest.log 2>&1
```

### Change Time Range

Edit `agent.py` line 289:
```python
agent.run_daily_digest(channel_ids, hours_back=48)  # Last 48 hours instead of 24
```

### Customize AI Focus

Edit `agent.py` lines 117-124 to change what the AI looks for:
```python
Focus on:
- Security vulnerabilities
- Customer complaints
- Your custom priorities...
```

### Change AI Model

Edit `.env`:
```bash
# Faster, smaller (default):
OLLAMA_MODEL=llama3.2

# Larger, smarter:
OLLAMA_MODEL=llama3.1:8b

# Code-focused:
OLLAMA_MODEL=codellama
```

Then download it:
```bash
ollama pull llama3.1:8b
```

## Troubleshooting

### Token Expired

User tokens can expire when you log out or change passwords. Get new ones:

1. Open Slack Desktop App → **Cmd + Option + I**
2. **Console** tab → Run:
   ```javascript
   JSON.parse(localStorage.localConfig_v2)["teams"]
   ```
3. Copy the new **`xoxc-`** token
4. **Application** tab → **Cookies** → find `d` cookie
5. Copy the new **`xoxd-`** value
6. Update both in your `.env` file

### "channel_not_found" Error

- Verify channel IDs are correct
- Make sure there are **no spaces** in `.env` around commas
- Channel IDs should look like: `C05ABC123`

### "enterprise_is_restricted" Error

Your workspace blocks certain API calls - this is normal. The agent should still work.

### No Notification Popup

Make sure Ollama is running:
```bash
brew services list | grep ollama
# Should show "started"

# If not:
brew services start ollama
```

### View Logs

```bash
# Check what happened during last run
tail -f <path-to>/slack-daily-digest/digest.log

# View recent runs
tail -n 50 digest.log
```

## How It Works

```
Every weekday at 8:30 AM:

┌─────────────────┐
│  Cron Job       │ ← Wakes up and starts agent
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Slack Channels │ ← Fetch last 24h messages (4 channels)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  agent.py       │ ← Collect & format messages
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Ollama AI      │ ← Analyze & summarize (runs locally on Mac)
│  (llama3.2)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Slack DM       │ ← Send digest with clickable links
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  macOS Alert    │ ← Notification: "Digest Ready! Check Slack"
└─────────────────┘
```

## Files

- **`agent.py`** - Main agent code
- **`.env`** - Your configuration (tokens, channels, etc.)
- **`run_digest.sh`** - Simple run script
- **`requirements.txt`** - Python dependencies
- **`digest.log`** - History of runs
- **`list_channels.py`** - Helper to list available channels

## Why This Approach?

✅ **No Slack App Needed** - Uses your personal token  
✅ **100% Free** - Ollama runs locally, no API costs  
✅ **Private** - AI processing stays on your Mac  
✅ **Fast** - No network delays for AI  
✅ **Works at Work** - Doesn't require admin permissions  

## Security Notes

⚠️ **Keep `.env` secure** - It contains your Slack credentials  
⚠️ **Tokens can expire** - You may need to refresh occasionally  
⚠️ **User tokens are personal** - Messages appear as coming from you  

## License

MIT

---

**Need help?** Run `./run_digest.sh` manually to see what happens and check the output!
