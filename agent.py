"""
Slack Daily Digest Agent
Analyzes Slack channels daily and sends important updates via DM
"""

import os
from datetime import datetime, timedelta
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import json
import requests
import subprocess

class SlackDigestAgent:
    def __init__(self):
        self.slack_token = os.getenv('SLACK_BOT_TOKEN')
        self.slack_cookie = os.getenv('SLACK_COOKIE')  # For user tokens (xoxc-)
        self.ollama_model = os.getenv('OLLAMA_MODEL', 'llama3.2')  # Default to llama3.2
        self.ollama_url = os.getenv('OLLAMA_URL', 'http://localhost:11434')  # Default Ollama endpoint
        self.user_id = os.getenv('SLACK_USER_ID')  # Your Slack user ID to send DM
        
        if not self.slack_token:
            raise ValueError("SLACK_BOT_TOKEN environment variable not set")
        if not self.user_id:
            raise ValueError("SLACK_USER_ID environment variable not set")
        
        # Initialize Slack client with cookie support for user tokens
        if self.slack_cookie:
            # User token (xoxc-) requires cookie in headers
            self.slack_client = WebClient(
                token=self.slack_token,
                headers={"Cookie": f"d={self.slack_cookie}"}
            )
            print("🔐 Using user token with cookie authentication")
        else:
            # Bot token (xoxb-) doesn't need cookies
            self.slack_client = WebClient(token=self.slack_token)
            print("🤖 Using bot token authentication")
        
        print(f"🧠 Using Ollama with model: {self.ollama_model}")
        
    def get_channel_messages(self, channel_id, hours_back=24):
        """Fetch messages from a channel for the last N hours"""
        try:
            # Calculate timestamp for N hours ago
            oldest_timestamp = (datetime.now() - timedelta(hours=hours_back)).timestamp()
            
            # Fetch messages
            result = self.slack_client.conversations_history(
                channel=channel_id,
                oldest=str(oldest_timestamp),
                limit=1000
            )
            
            messages = result['messages']
            
            # Get channel name and workspace info
            channel_info = self.slack_client.conversations_info(channel=channel_id)
            channel_name = channel_info['channel']['name']
            
            # Get workspace domain for links
            team_info = self.slack_client.team_info()
            workspace_domain = team_info['team']['domain']
            
            # Format messages with user info
            formatted_messages = []
            for msg in messages:
                if msg.get('type') == 'message' and 'subtype' not in msg:
                    user_id = msg.get('user', 'Unknown')
                    text = msg.get('text', '')
                    msg_ts = msg.get('ts', '')
                    timestamp = datetime.fromtimestamp(float(msg_ts)).strftime('%Y-%m-%d %H:%M')
                    
                    # Create Slack permalink
                    # Format: https://workspace.slack.com/archives/CHANNEL_ID/pTIMESTAMP
                    ts_link = msg_ts.replace('.', '')  # Remove dot from timestamp
                    slack_link = f"https://{workspace_domain}.slack.com/archives/{channel_id}/p{ts_link}"
                    
                    # Get username
                    try:
                        user_info = self.slack_client.users_info(user=user_id)
                        username = user_info['user']['real_name'] or user_info['user']['name']
                    except:
                        username = 'Unknown User'
                    
                    # Check if message has thread replies
                    thread_text = ""
                    if msg.get('reply_count', 0) > 0:
                        try:
                            # Fetch thread replies
                            thread_result = self.slack_client.conversations_replies(
                                channel=channel_id,
                                ts=msg_ts
                            )
                            
                            # Get all replies (excluding the parent message which is first)
                            thread_messages = thread_result['messages'][1:]  # Skip parent message
                            
                            if thread_messages:
                                thread_text = "\n  Thread replies:"
                                for reply in thread_messages:
                                    reply_user_id = reply.get('user', 'Unknown')
                                    reply_text = reply.get('text', '')
                                    
                                    # Get reply username
                                    try:
                                        reply_user_info = self.slack_client.users_info(user=reply_user_id)
                                        reply_username = reply_user_info['user']['real_name'] or reply_user_info['user']['name']
                                    except:
                                        reply_username = 'Unknown User'
                                    
                                    thread_text += f"\n    - {reply_username}: {reply_text}"
                        except SlackApiError as e:
                            print(f"  Warning: Could not fetch thread replies for message {msg_ts}: {e.response['error']}")
                    
                    formatted_messages.append({
                        'channel': channel_name,
                        'user': username,
                        'text': text + thread_text,
                        'timestamp': timestamp,
                        'link': slack_link
                    })
            
            return formatted_messages
            
        except SlackApiError as e:
            print(f"Error fetching messages from {channel_id}: {e.response['error']}")
            return []
    
    def analyze_messages_with_ai(self, all_messages):
        """Use Ollama to analyze messages and extract important information"""
        
        if not all_messages:
            return "No messages found in the specified channels."
        
        # Format messages for AI analysis (including links in Slack format)
        messages_text = "\n\n".join([
            f"Channel: #{msg['channel']}\n"
            f"From: {msg['user']}\n"
            f"Time: {msg['timestamp']}\n"
            f"Message: {msg['text']}\n"
            f"Link: <{msg['link']}|link>"
            for msg in all_messages
        ])
        
        prompt = f"""You are analyzing Slack messages from the last 24 hours. Your job is to identify and summarize the most important, high-quality information.

Focus on:
- Important announcements or decisions
- Critical updates or blockers
- Valuable insights or discussions
- Action items that need attention
- News or information that would be valuable to know
- UI bugs or any quality issues that have been reported
- Any direct mentions of me that i need to give attention to
- **THREAD REPLIES**: Pay special attention to thread replies as they often contain resolutions, solutions, or important follow-up information to issues

Ignore:
- Casual conversations
- Simple acknowledgments ("thanks", "ok", etc.)
- Routine status updates with no significant information
- Off-topic chatter

Here are the messages (including thread replies):

{messages_text}

Please provide a concise daily digest organized by importance. Use this format:

🔴 CRITICAL / URGENT
[List any urgent items that need immediate attention. If a thread has replies with a resolution, mention the resolution.]

🟡 IMPORTANT UPDATES
[List significant updates, decisions, or announcements. Include resolutions from thread replies if applicable.]

🟢 NOTABLE DISCUSSIONS
[List interesting discussions or insights worth knowing. Note any conclusions reached in thread replies.]

IMPORTANT: Add a clickable link INLINE at the end of EACH bullet point (not on a separate line).
Use this EXACT format at the END of the sentence: (<URL|link>)
For example: "Database migration delayed until Friday (<https://redhat.slack.com/archives/C123/p456789|link>)"
The link should be in parentheses and appear right after the text, not on a new line with "Link:".

If there's nothing important, just say "No significant updates today."

Keep it concise and actionable."""

        try:
            # Call Ollama API
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.ollama_model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=120  # 2 minute timeout for local AI
            )
            response.raise_for_status()
            
            result = response.json()
            ai_summary = result.get('response', 'No response from AI')
            
            return ai_summary
            
        except requests.exceptions.RequestException as e:
            print(f"Error connecting to Ollama: {e}")
            return f"Error: Could not connect to Ollama. Make sure Ollama is running (brew services start ollama)"
        except Exception as e:
            print(f"Error analyzing messages with AI: {e}")
            return f"Error analyzing messages: {str(e)}"
    
    def send_dm(self, message):
        """Send a direct message to the specified user"""
        try:
            # Open a DM channel with the user
            response = self.slack_client.conversations_open(users=[self.user_id])
            dm_channel = response['channel']['id']
            
            # Send the message (with link unfurling disabled)
            self.slack_client.chat_postMessage(
                channel=dm_channel,
                text=message,
                mrkdwn=True,
                unfurl_links=False,  # Don't show link previews
                unfurl_media=False   # Don't show media previews
            )
            
            print(f"✅ Daily digest sent successfully to user {self.user_id}")
            
        except SlackApiError as e:
            print(f"❌ Error sending DM: {e.response['error']}")
    
    def send_macos_notification(self, title, message):
        """Send a macOS notification banner"""
        try:
            # Use display dialog notification
            script = f'''
            display dialog "{message}" with title "{title}" buttons {{"Open Slack", "OK"}} default button "Open Slack" giving up after 30
            '''
            result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True, timeout=35)
            
            # If user clicked "Open Slack", open Slack app
            if "Open Slack" in result.stdout:
                subprocess.run(['open', '-a', 'Slack'], check=False)
            
            print(f"🔔 macOS notification sent")
        except subprocess.TimeoutExpired:
            # Dialog timed out after 30 seconds - that's fine
            print(f"🔔 macOS notification displayed (timed out)")
        except Exception as e:
            print(f"⚠️  Could not send macOS notification: {e}")
    
    def run_daily_digest(self, channel_ids, hours_back=24):
        """Main function to run the daily digest"""
        print(f"🤖 Starting Slack Daily Digest Agent...")
        print(f"📅 Analyzing messages from the last {hours_back} hours")
        print(f"📺 Monitoring {len(channel_ids)} channel(s)")
        
        # Collect messages from all channels
        all_messages = []
        for channel_id in channel_ids:
            print(f"📥 Fetching messages from channel: {channel_id}")
            messages = self.get_channel_messages(channel_id, hours_back)
            all_messages.extend(messages)
            print(f"   Found {len(messages)} messages")
        
        print(f"\n📊 Total messages collected: {len(all_messages)}")
        
        # Analyze with AI
        print("🧠 Analyzing messages with AI...")
        digest = self.analyze_messages_with_ai(all_messages)
        
        # Create final message
        header = f"*📬 Daily Slack Digest* - {datetime.now().strftime('%B %d, %Y')}\n"
        header += f"_Analyzed {len(all_messages)} messages from {len(channel_ids)} channel(s)_\n\n"
        header += "─" * 50 + "\n\n"
        
        final_message = header + digest
        
        # Send DM
        print("📤 Sending digest...")
        self.send_dm(final_message)
        
        # Send macOS notification
        self.send_macos_notification(
            "Slack Daily Digest Ready! 📬",
            f"Analyzed {len(all_messages)} messages from {len(channel_ids)} channel(s). Check your Slack DMs!"
        )
        
        print("\n✨ Daily digest complete!")
        
        return final_message


def main():
    """Main entry point"""
    # Initialize agent
    agent = SlackDigestAgent()
    
    # Define channels to monitor (comma-separated in env var)
    channels_env = os.getenv('SLACK_CHANNELS', '')
    if not channels_env:
        print("❌ Error: SLACK_CHANNELS environment variable not set")
        print("   Example: SLACK_CHANNELS=C1234567890,C0987654321")
        return
    
    channel_ids = [ch.strip() for ch in channels_env.split(',')]
    
    # Run the digest
    agent.run_daily_digest(channel_ids, hours_back=24)


if __name__ == "__main__":
    main()

