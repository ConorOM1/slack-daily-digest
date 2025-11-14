"""
Helper script to list all Slack channels the bot has access to
Run this to find channel IDs for your .env file
"""

import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

def list_channels():
    """List all channels the bot can access"""
    slack_token = os.getenv('SLACK_BOT_TOKEN')
    slack_cookie = os.getenv('SLACK_COOKIE')
    
    if not slack_token:
        print("❌ Error: SLACK_BOT_TOKEN environment variable not set")
        print("\nSet it with:")
        print("  export SLACK_BOT_TOKEN=xoxb-your-token-here")
        print("  or for user tokens:")
        print("  export SLACK_BOT_TOKEN=xoxc-your-token-here")
        print("  export SLACK_COOKIE=xoxd-your-cookie-here")
        return
    
    # Support both bot tokens and user tokens with cookies
    if slack_cookie:
        # User token requires cookie in headers
        client = WebClient(
            token=slack_token,
            headers={"Cookie": f"d={slack_cookie}"}
        )
        print("🔐 Using user token with cookie authentication\n")
    else:
        client = WebClient(token=slack_token)
        print("🤖 Using bot token authentication\n")
    
    try:
        print("📺 Fetching channels...\n")
        
        # Get all public channels
        result = client.conversations_list(
            types="public_channel,private_channel",
            exclude_archived=True,
            limit=1000
        )
        
        channels = result['channels']
        
        print(f"Found {len(channels)} channels:\n")
        print("=" * 80)
        
        # Show channels the bot is a member of
        member_channels = [ch for ch in channels if ch.get('is_member')]
        if member_channels:
            print("\n✅ CHANNELS BOT IS IN (ready to monitor):")
            print("-" * 80)
            for channel in member_channels:
                name = channel['name']
                channel_id = channel['id']
                num_members = channel.get('num_members', 0)
                print(f"  #{name:<30} | ID: {channel_id} | {num_members} members")
        
        # Show channels the bot is NOT in
        non_member_channels = [ch for ch in channels if not ch.get('is_member')]
        if non_member_channels:
            print("\n\n⚠️  CHANNELS BOT IS NOT IN (invite bot first):")
            print("-" * 80)
            for channel in non_member_channels[:20]:  # Show first 20
                name = channel['name']
                channel_id = channel['id']
                print(f"  #{name:<30} | ID: {channel_id}")
                print(f"      To add bot: Open #{name} and type: /invite @YourBotName")
        
        print("\n" + "=" * 80)
        
        # Generate example .env format
        if member_channels:
            print("\n📝 Add to your .env file:")
            print("-" * 80)
            channel_ids = ','.join([ch['id'] for ch in member_channels[:3]])
            print(f"SLACK_CHANNELS={channel_ids}")
            
            if len(member_channels) > 3:
                print(f"\n(Showing first 3 channels, add more as needed)")
        
    except SlackApiError as e:
        error = e.response['error']
        if error == 'missing_scope':
            print("❌ Error: Missing required permissions")
            print("\nYour bot needs these OAuth scopes:")
            print("  - channels:read")
            print("  - channels:history")
            print("\nAdd them at: https://api.slack.com/apps -> Your App -> OAuth & Permissions")
        else:
            print(f"❌ Error: {error}")


def get_user_id():
    """Helper to get the current user's/bot's ID"""
    slack_token = os.getenv('SLACK_BOT_TOKEN')
    slack_cookie = os.getenv('SLACK_COOKIE')
    
    if not slack_token:
        return
    
    # Support both bot tokens and user tokens with cookies
    if slack_cookie:
        # User token requires cookie in headers
        client = WebClient(
            token=slack_token,
            headers={"Cookie": f"d={slack_cookie}"}
        )
    else:
        client = WebClient(token=slack_token)
    
    try:
        result = client.auth_test()
        print(f"\n👤 Your User Info:")
        print(f"   User ID: {result['user_id']}")
        print(f"   Username: {result['user']}")
        print(f"   Team: {result['team']}")
        print(f"\n📝 Add to your .env file:")
        print(f"   SLACK_USER_ID={result['user_id']}")
    except SlackApiError as e:
        print(f"❌ Error getting user info: {e.response['error']}")


if __name__ == "__main__":
    list_channels()
    get_user_id()

