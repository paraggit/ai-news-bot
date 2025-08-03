"""
Telegram bot implementation for AI News Aggregator.

This module handles posting news summaries to Telegram channels/chats.
"""

import asyncio
from typing import Optional, List
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramAPIError, TelegramRetryAfter
from aiogram.types import Message

logger = logging.getLogger(__name__)


class TelegramBot:
    """Telegram bot for posting AI news summaries."""

    def __init__(self, bot_token: str) -> None:
        """Initialize Telegram bot."""
        if not bot_token:
            raise ValueError("Telegram bot token is required")

        self.bot = Bot(
            token=bot_token,
            default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
        )
        self.dp = Dispatcher()
        self.logger = logger.getChild(self.__class__.__name__)

        self.logger.info("Initialized Telegram bot")

    async def send_message(
        self,
        chat_id: str,
        message: str,
        parse_mode: Optional[str] = ParseMode.MARKDOWN
    ) -> bool:
        """Send a message to a Telegram chat/channel."""
        max_length = 4096
        try:
            parts = self._split_message_intelligently(message, max_length)

            for i, part in enumerate(parts):
                if i > 0:
                    await asyncio.sleep(1)  # small delay to avoid rate limits
                await self._send_single_message(chat_id, part, parse_mode)

            self.logger.info(f"Successfully sent message to {chat_id}")
            return True

        except TelegramRetryAfter as e:
            self.logger.warning(f"Rate limited, waiting {e.retry_after} seconds")
            await asyncio.sleep(e.retry_after)
            return await self.send_message(chat_id, message, parse_mode)

        except TelegramAPIError as e:
            self.logger.error(f"Telegram API error: {e}")
            return False

        except Exception as e:
            self.logger.error(f"Unexpected error sending message: {e}")
            return False

    async def _send_single_message(
        self,
        chat_id: str,
        message: str,
        parse_mode: Optional[str]
    ) -> Message:
        """Send a single message (under 4096 characters)."""
        return await self.bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode=parse_mode,
            disable_web_page_preview=False,
            disable_notification=False
        )

    def _split_message_intelligently(self, message: str, max_length: int) -> List[str]:
        """Split message intelligently at paragraph and sentence boundaries."""
        if len(message) <= max_length:
            return [message]

        parts, current_part = [], ""
        paragraphs = message.split('\n\n')

        for paragraph in paragraphs:
            if len(current_part) + len(paragraph) + 2 > max_length:
                if current_part:
                    parts.append(current_part.strip())
                    current_part = ""

                sentences = paragraph.split('. ')
                for sentence in sentences:
                    if len(current_part) + len(sentence) + 2 > max_length:
                        if current_part:
                            parts.append(current_part.strip())
                            current_part = sentence
                        else:
                            # Force split for very long sentence
                            while len(sentence) > max_length:
                                parts.append(sentence[:max_length].strip())
                                sentence = sentence[max_length:]
                            current_part = sentence
                    else:
                        current_part += ('. ' if current_part else '') + sentence
            else:
                current_part += ('\n\n' if current_part else '') + paragraph

        if current_part:
            parts.append(current_part.strip())

        return parts

    async def send_test_message(self, chat_id: str) -> bool:
        """Send a test message to verify bot configuration."""
        test_message = (
            "🤖 **AI News Aggregator Test**\n\n"
            "This is a test message from your AI News Aggregator Bot!\n\n"
            "✅ Bot is configured correctly\n"
            "✅ Connection to Telegram is working\n"
            "✅ Ready to start posting AI news updates\n\n"
            "#AINews #TestMessage"
        )
        return await self.send_message(chat_id, test_message)

    async def get_bot_info(self) -> Optional[dict]:
        """Get information about the bot."""
        try:
            bot_info = await self.bot.get_me()
            info = {
                "id": bot_info.id,
                "username": bot_info.username,
                "first_name": bot_info.first_name,
                "is_bot": bot_info.is_bot,
                "can_join_groups": bot_info.can_join_groups,
                "can_read_all_group_messages": bot_info.can_read_all_group_messages,
                "supports_inline_queries": bot_info.supports_inline_queries
            }

            self.logger.info(f"Bot info: {info}")
            return info

        except Exception as e:
            self.logger.error(f"Error getting bot info: {e}")
            return None

    async def check_chat_permissions(self, chat_id: str) -> bool:
        """Check if bot has permission to send messages to the chat."""
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