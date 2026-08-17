"""
Telegram bot implementation for AI News Aggregator.

Handles posting news summaries and interactive user commands.
"""

import asyncio
from typing import Optional, List, Callable, Awaitable
import logging

from aiogram import Bot, Dispatcher, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramAPIError, TelegramRetryAfter
from aiogram.filters import Command
from aiogram.types import Message

logger = logging.getLogger(__name__)

MAX_SEND_RETRIES = 3


class TelegramBot:
    """Telegram bot for posting AI news summaries and handling commands."""

    def __init__(self, bot_token: str) -> None:
        if not bot_token:
            raise ValueError("Telegram bot token is required")

        self.bot = Bot(
            token=bot_token,
            default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN),
        )
        self.dp = Dispatcher()
        self.router = Router()
        self.dp.include_router(self.router)
        self.logger = logger.getChild(self.__class__.__name__)

        self._search_handler: Optional[Callable] = None
        self._trending_handler: Optional[Callable] = None
        self._stats_handler: Optional[Callable] = None
        self._digest_handler: Optional[Callable] = None

        self._register_commands()
        self.logger.info("Initialized Telegram bot with interactive commands")

    # ------------------------------------------------------------------
    # Interactive command handlers
    # ------------------------------------------------------------------

    def _register_commands(self) -> None:
        @self.router.message(Command("start", "help"))
        async def cmd_help(message: Message) -> None:
            help_text = (
                "**AI News Bot Commands**\n\n"
                "/search <query> — Search articles\n"
                "/trending — Show trending AI topics\n"
                "/stats — Database statistics\n"
                "/digest — Get a digest of top articles\n"
                "/help — Show this help message"
            )
            await message.answer(help_text)

        @self.router.message(Command("search"))
        async def cmd_search(message: Message) -> None:
            if not self._search_handler:
                await message.answer("Search is not configured.")
                return
            query = message.text.partition(" ")[2].strip()
            if not query:
                await message.answer("Usage: /search <query>\nExample: /search transformer")
                return
            await self._search_handler(message, query)

        @self.router.message(Command("trending"))
        async def cmd_trending(message: Message) -> None:
            if not self._trending_handler:
                await message.answer("Trending is not configured.")
                return
            await self._trending_handler(message)

        @self.router.message(Command("stats"))
        async def cmd_stats(message: Message) -> None:
            if not self._stats_handler:
                await message.answer("Stats are not configured.")
                return
            await self._stats_handler(message)

        @self.router.message(Command("digest"))
        async def cmd_digest(message: Message) -> None:
            if not self._digest_handler:
                await message.answer("Digest is not configured.")
                return
            await self._digest_handler(message)

    def set_command_handlers(
        self,
        search: Optional[Callable] = None,
        trending: Optional[Callable] = None,
        stats: Optional[Callable] = None,
        digest: Optional[Callable] = None,
    ) -> None:
        """Register callback handlers for interactive commands."""
        self._search_handler = search
        self._trending_handler = trending
        self._stats_handler = stats
        self._digest_handler = digest

    async def start_polling(self) -> None:
        """Start polling for incoming messages (long-poll, Pi-friendly)."""
        self.logger.info("Starting Telegram command polling")
        await self.dp.start_polling(self.bot, polling_timeout=30)

    async def stop_polling(self) -> None:
        await self.dp.stop_polling()

    # ------------------------------------------------------------------
    # Message sending (with bounded retries)
    # ------------------------------------------------------------------

    async def send_message(
        self,
        chat_id: str,
        message: str,
        parse_mode: Optional[str] = ParseMode.MARKDOWN,
    ) -> bool:
        max_length = 4096
        try:
            parts = self._split_message_intelligently(message, max_length)

            for i, part in enumerate(parts):
                if i > 0:
                    await asyncio.sleep(1)
                await self._send_with_retry(chat_id, part, parse_mode)

            self.logger.info(f"Successfully sent message to {chat_id}")
            return True

        except TelegramAPIError as e:
            self.logger.error(f"Telegram API error: {e}")
            return False

        except Exception as e:
            self.logger.error(f"Unexpected error sending message: {e}")
            return False

    async def _send_with_retry(
        self,
        chat_id: str,
        message: str,
        parse_mode: Optional[str],
    ) -> Message:
        """Send a single message with bounded retry on rate limits."""
        for attempt in range(MAX_SEND_RETRIES):
            try:
                return await self.bot.send_message(
                    chat_id=chat_id,
                    text=message,
                    parse_mode=parse_mode,
                    disable_web_page_preview=False,
                    disable_notification=False,
                )
            except TelegramRetryAfter as e:
                if attempt == MAX_SEND_RETRIES - 1:
                    raise
                self.logger.warning(
                    f"Rate limited, waiting {e.retry_after}s "
                    f"(attempt {attempt + 1}/{MAX_SEND_RETRIES})"
                )
                await asyncio.sleep(e.retry_after)

    def _split_message_intelligently(self, message: str, max_length: int) -> List[str]:
        """Split message intelligently at paragraph and sentence boundaries."""
        if len(message) <= max_length:
            return [message]

        parts, current_part = [], ""
        paragraphs = message.split("\n\n")

        for paragraph in paragraphs:
            if len(current_part) + len(paragraph) + 2 > max_length:
                if current_part:
                    parts.append(current_part.strip())
                    current_part = ""

                sentences = paragraph.split(". ")
                for sentence in sentences:
                    if len(current_part) + len(sentence) + 2 > max_length:
                        if current_part:
                            parts.append(current_part.strip())
                            current_part = sentence
                        else:
                            while len(sentence) > max_length:
                                parts.append(sentence[:max_length].strip())
                                sentence = sentence[max_length:]
                            current_part = sentence
                    else:
                        current_part += (". " if current_part else "") + sentence
            else:
                current_part += ("\n\n" if current_part else "") + paragraph

        if current_part:
            parts.append(current_part.strip())

        return parts

    # ------------------------------------------------------------------
    # Utility methods
    # ------------------------------------------------------------------

    async def send_test_message(self, chat_id: str) -> bool:
        test_message = (
            "**AI News Aggregator Test**\n\n"
            "This is a test message from your AI News Aggregator Bot!\n\n"
            "Bot is configured correctly\n"
            "Connection to Telegram is working\n"
            "Interactive commands are available — send /help\n\n"
            "#AINews #TestMessage"
        )
        return await self.send_message(chat_id, test_message)

    async def get_bot_info(self) -> Optional[dict]:
        try:
            bot_info = await self.bot.get_me()
            info = {
                "id": bot_info.id,
                "username": bot_info.username,
                "first_name": bot_info.first_name,
                "is_bot": bot_info.is_bot,
                "can_join_groups": bot_info.can_join_groups,
                "can_read_all_group_messages": bot_info.can_read_all_group_messages,
                "supports_inline_queries": bot_info.supports_inline_queries,
            }
            self.logger.info(f"Bot info: {info}")
            return info

        except Exception as e:
            self.logger.error(f"Error getting bot info: {e}")
            return None

    async def check_chat_permissions(self, chat_id: str) -> bool:
        try:
            chat = await self.bot.get_chat(chat_id)
            self.logger.info(f"Chat info: {chat.type}, {chat.title or chat.first_name}")

            if chat.type == "channel":
                bot_member = await self.bot.get_chat_member(chat_id, self.bot.id)
                if bot_member.status not in ["administrator", "creator"]:
                    self.logger.error(f"Bot is not an admin in channel {chat_id}")
                    return False

            return True

        except Exception as e:
            self.logger.error(f"Could not check permissions: {e}")
            return False
