import asyncio
from ai_news_bot.telegram.bot import TelegramBot
from dotenv import load_dotenv
import os

async def get_bot_info():
    """Get bot information."""
    load_dotenv()  # Load environment variables from .env file
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")

    if not bot_token:
        raise ValueError("TELEGRAM_BOT_TOKEN not set in .env file")

    bot = TelegramBot(bot_token)
    info = await bot.get_bot_info()
    print(f'Bot info: {info}')
    await bot.bot.session.close()

if __name__ == "__main__":
    asyncio.run(get_bot_info())