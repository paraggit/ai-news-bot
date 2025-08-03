#!/usr/bin/env python3
"""
Telegram Setup Helper for AI News Aggregator Bot.

This script helps you properly configure your Telegram bot and find the correct channel ID.
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent))

from ai_news_bot.telegram.bot import TelegramBot
from ai_news_bot.config import load_config


async def test_bot_token():
    """Test if the bot token is valid."""
    print("🤖 Testing bot token...")
    
    try:
        config = load_config()
        bot = TelegramBot(config.telegram_bot_token)
        
        bot_info = await bot.get_bot_info()
        if bot_info:
            print("✅ Bot token is valid!")
            print(f"   Bot name: {bot_info.get('first_name', 'Unknown')}")
            print(f"   Bot username: @{bot_info.get('username', 'Unknown')}")
            print(f"   Bot ID: {bot_info.get('id', 'Unknown')}")
            return True
        else:
            print("❌ Invalid bot token or connection failed")
            return False
            
    except Exception as e:
        print(f"❌ Error testing bot token: {e}")
        return False


async def test_channel_access(channel_id: str):
    """Test if the bot can access a specific channel."""
    print(f"\n📢 Testing channel access: {channel_id}")
    
    try:
        config = load_config()
        bot = TelegramBot(config.telegram_bot_token)
        
        # Check if bot has permissions
        permissions = await bot.check_chat_permissions(channel_id)
        if permissions:
            print("✅ Bot has access to the channel")
            return True
        else:
            print("❌ Bot doesn't have access to the channel")
            return False
            
    except Exception as e:
        print(f"❌ Error accessing channel: {e}")
        return False


async def send_test_message(channel_id: str):
    """Send a test message to verify everything works."""
    print(f"\n📨 Sending test message to: {channel_id}")
    
    try:
        config = load_config()
        bot = TelegramBot(config.telegram_bot_token)
        
        success = await bot.send_test_message(channel_id)
        if success:
            print("✅ Test message sent successfully!")
            return True
        else:
            print("❌ Failed to send test message")
            return False
            
    except Exception as e:
        print(f"❌ Error sending test message: {e}")
        return False


async def get_chat_info(channel_id: str):
    """Get detailed information about a chat/channel."""
    print(f"\n🔍 Getting chat information for: {channel_id}")
    
    try:
        config = load_config()
        bot = TelegramBot(config.telegram_bot_token)
        
        # Use aiogram's get_chat method directly
        chat = await bot.bot.get_chat(channel_id)
        
        print("✅ Chat found!")
        print(f"   Chat ID: {chat.id}")
        print(f"   Chat type: {chat.type}")
        print(f"   Chat title: {getattr(chat, 'title', 'N/A')}")
        print(f"   Chat username: @{getattr(chat, 'username', 'N/A')}")
        print(f"   Chat description: {getattr(chat, 'description', 'N/A')[:100]}...")
        
        return chat.id
        
    except Exception as e:
        print(f"❌ Error getting chat info: {e}")
        return None


def get_channel_id_from_user():
    """Get channel ID from user input."""
    print("\n📝 Enter your channel information:")
    print("You can use:")
    print("1. Channel username (e.g., @mychannel)")
    print("2. Numeric channel ID (e.g., -1001234567890)")
    print("3. Channel invite link (e.g., https://t.me/mychannel)")
    
    channel_input = input("\nEnter channel ID/username/link: ").strip()
    
    # Clean up the input
    if channel_input.startswith("https://t.me/"):
        # Extract username from link
        channel_input = "@" + channel_input.split("/")[-1]
    elif not channel_input.startswith("@") and not channel_input.startswith("-"):
        # Add @ if it's just the username
        channel_input = "@" + channel_input
    
    return channel_input


async def interactive_setup():
    """Interactive setup process."""
    print("🚀 Telegram Bot Setup Helper")
    print("=" * 40)
    
    # Step 1: Test bot token
    if not await test_bot_token():
        print("\n❌ Bot token is invalid. Please check your TELEGRAM_BOT_TOKEN in .env")
        return False
    
    # Step 2: Get channel ID from user
    channel_id = get_channel_id_from_user()
    
    # Step 3: Get chat info
    actual_channel_id = await get_chat_info(channel_id)
    if not actual_channel_id:
        print("\n❌ Could not find the channel. Make sure:")
        print("1. The channel exists")
        print("2. The bot is added to the channel")
        print("3. The bot is an administrator")
        return False
    
    # Step 4: Test channel access
    if not await test_channel_access(str(actual_channel_id)):
        print("\n❌ Bot doesn't have proper permissions. Make sure:")
        print("1. Bot is added as an administrator")
        print("2. Bot has 'Post Messages' permission")
        return False
    
    # Step 5: Send test message
    if await send_test_message(str(actual_channel_id)):
        print(f"\n🎉 Setup successful!")
        print(f"✅ Use this in your .env file:")
        print(f"TELEGRAM_CHANNEL_ID={actual_channel_id}")
        
        # Update .env file
        update_env_file(actual_channel_id)
        return True
    else:
        print("\n❌ Test message failed. Check bot permissions.")
        return False


def update_env_file(channel_id):
    """Update the .env file with the correct channel ID."""
    env_file = Path(".env")
    
    if not env_file.exists():
        print("⚠️  .env file not found")
        return
    
    # Read current content
    with open(env_file, 'r') as f:
        lines = f.readlines()
    
    # Update or add TELEGRAM_CHANNEL_ID
    updated = False
    for i, line in enumerate(lines):
        if line.startswith('TELEGRAM_CHANNEL_ID='):
            lines[i] = f'TELEGRAM_CHANNEL_ID={channel_id}\n'
            updated = True
            break
    
    if not updated:
        lines.append(f'TELEGRAM_CHANNEL_ID={channel_id}\n')
    
    # Write back
    with open(env_file, 'w') as f:
        f.writelines(lines)
    
    print(f"✅ Updated .env file with TELEGRAM_CHANNEL_ID={channel_id}")


async def quick_test():
    """Quick test with current configuration."""
    print("⚡ Quick test with current .env configuration...")
    
    try:
        config = load_config()
        print(f"Current channel ID: {config.telegram_channel_id}")
        
        # Test current setup
        await test_bot_token()
        await test_channel_access(config.telegram_channel_id)
        await send_test_message(config.telegram_channel_id)
        
    except Exception as e:
        print(f"❌ Error in quick test: {e}")


def print_setup_instructions():
    """Print detailed setup instructions."""
    print("\n📋 Manual Setup Instructions:")
    print("=" * 40)
    print("1. Create a new Telegram channel:")
    print("   - Open Telegram")
    print("   - Create new channel (not group)")
    print("   - Give it a name and username")
    print("")
    print("2. Add your bot as administrator:")
    print("   - Go to your channel")
    print("   - Click on channel name → Administrators")
    print("   - Add your bot (@yourbotname)")
    print("   - Give it 'Post Messages' permission")
    print("")
    print("3. Get the channel ID:")
    print("   - Use @username format: @yourchannel")
    print("   - Or numeric ID from this tool")
    print("")
    print("4. Test the setup:")
    print("   - Run this script again")
    print("   - Or run: poetry run ai-news-bot")


async def main():
    """Main function."""
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "test":
            await quick_test()
        elif command == "setup":
            await interactive_setup()
        elif command == "help":
            print_setup_instructions()
        else:
            print(f"Unknown command: {command}")
            print("Available commands: test, setup, help")
    else:
        print("🤖 Telegram Setup Helper")
        print("Choose an option:")
        print("1. Interactive setup (recommended)")
        print("2. Quick test current config")
        print("3. Show setup instructions")
        
        choice = input("\nEnter choice (1-3): ").strip()
        
        if choice == "1":
            await interactive_setup()
        elif choice == "2":
            await quick_test()
        elif choice == "3":
            print_setup_instructions()
        else:
            print("Invalid choice")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nSetup cancelled by user")
    except Exception as e:
        print(f"Error: {e}")