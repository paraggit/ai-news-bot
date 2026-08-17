#!/usr/bin/env python3
"""
AI News Aggregator Bot - Main Entry Point

Orchestrates news fetching, summarization, Telegram posting,
interactive commands, and periodic digests.
"""

import asyncio
import signal
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from .config import Config, load_config
from .database import DatabaseManager
from .digest import DigestGenerator
from .news_sources import get_all_news_sources
from .summarizer import get_summarizer
from .telegram.bot import TelegramBot
from .utils.logger import setup_logger


class AINewsAggregator:
    """Main application class that orchestrates the news aggregation process."""

    def __init__(self, config: Config) -> None:
        self.config = config
        self.logger = setup_logger(config.log_level, config.log_file)
        self.db_manager = DatabaseManager(config.database_path)
        self.scheduler = AsyncIOScheduler()
        self.telegram_bot = TelegramBot(config.telegram_bot_token)
        self.summarizer = get_summarizer(config)
        self.news_sources = get_all_news_sources(config)
        self.digest_generator: DigestGenerator = None  # type: ignore[assignment]
        self.running = False

        # Source health tracking
        self._source_health: Dict[str, Dict[str, int]] = defaultdict(
            lambda: {"success": 0, "failure": 0}
        )

    async def initialize(self) -> None:
        self.logger.info("Initializing AI News Aggregator...")

        await self.db_manager.initialize()

        for source in self.news_sources:
            await source.initialize()

        self.digest_generator = DigestGenerator(self.config, self.db_manager)

        # Wire interactive Telegram commands
        self.telegram_bot.set_command_handlers(
            search=self._handle_search,
            trending=self._handle_trending,
            stats=self._handle_stats,
            digest=self._handle_digest,
        )

        self.logger.info("Initialization complete")

    # ------------------------------------------------------------------
    # News fetching — concurrent with semaphore
    # ------------------------------------------------------------------

    async def fetch_and_process_news(self) -> None:
        self.logger.info("Starting news fetch and processing cycle")

        try:
            all_articles = await self._fetch_all_sources_concurrent()

            # Filter already-processed articles
            new_articles = []
            for article in all_articles:
                if not await self.db_manager.article_exists(article.url):
                    new_articles.append(article)

            self.logger.info(f"Found {len(new_articles)} new articles to process")

            # Content analyzer already scored and tagged every article
            # during enrichment in each source. Filter on the result.
            new_articles = [a for a in new_articles if a.relevance_score >= 35]
            self.logger.info(f"After relevance filtering: {len(new_articles)} articles")

            # Deduplicate and rank
            from .utils import ArticleFilter

            article_filter = ArticleFilter()
            article_dicts = [
                {
                    "title": a.title,
                    "url": a.url,
                    "relevance_score": a.relevance_score,
                    "article_obj": a,
                }
                for a in new_articles
            ]
            unique = article_filter.remove_duplicates(article_dicts, similarity_threshold=0.8)
            ranked = article_filter.rank_by_quality(unique)
            new_articles = [a["article_obj"] for a in ranked]
            self.logger.info(f"After dedup/rank: {len(new_articles)} articles")

            # Cap per run
            if len(new_articles) > self.config.max_articles_per_run:
                new_articles = new_articles[: self.config.max_articles_per_run]
                self.logger.info(f"Limited to {self.config.max_articles_per_run} articles")

            for article in new_articles:
                try:
                    await self._process_single_article(article)
                except Exception as e:
                    self.logger.error(f"Error processing article {article.title}: {e}")

            self._log_source_health()
            self.logger.info("News processing cycle completed")

        except Exception as e:
            self.logger.error(f"Error in fetch and process cycle: {e}")

    async def _fetch_all_sources_concurrent(self) -> list:
        """Fetch from all sources concurrently, capped by semaphore."""
        sem = asyncio.Semaphore(self.config.max_concurrent_sources)

        async def _fetch_one(source):
            async with sem:
                name = source.__class__.__name__
                try:
                    articles = await source.fetch_articles()
                    self._source_health[name]["success"] += 1
                    self.logger.info(f"Fetched {len(articles)} articles from {name}")
                    return articles
                except Exception as e:
                    self._source_health[name]["failure"] += 1
                    self.logger.error(f"Error fetching from {name}: {e}")
                    return []

        results = await asyncio.gather(
            *[_fetch_one(s) for s in self.news_sources],
            return_exceptions=False,
        )

        all_articles = []
        for batch in results:
            all_articles.extend(batch)
        return all_articles

    def _log_source_health(self) -> None:
        for name, counts in self._source_health.items():
            total = counts["success"] + counts["failure"]
            if total > 0 and counts["failure"] / total > 0.5:
                self.logger.warning(
                    f"Source {name} has high failure rate: "
                    f"{counts['failure']}/{total} failures"
                )

    # ------------------------------------------------------------------
    # Article processing
    # ------------------------------------------------------------------

    async def _process_single_article(self, article) -> None:
        self.logger.info(f"Processing article: {article.title}")

        summary = await self.summarizer.summarize(
            title=article.title,
            content=article.content,
            source_url=article.url,
        )

        message = self._format_telegram_message(article, summary)

        success = await self.telegram_bot.send_message(
            chat_id=self.config.telegram_channel_id,
            message=message,
        )

        if success:
            await self.db_manager.save_article(
                url=article.url,
                title=article.title,
                source=article.source,
                summary=summary,
                original_content=article.content[:1000],
                topics=",".join(article.topics) if article.topics else None,
                keywords=",".join(article.keywords) if article.keywords else None,
                relevance_score=article.relevance_score,
            )
            self.logger.info(
                f"Posted: {article.title} (relevance: {article.relevance_score:.1f})"
            )
        else:
            self.logger.error(f"Failed to post article: {article.title}")

    def _format_telegram_message(self, article, summary: str) -> str:
        source_emoji = {
            "OpenAI": "🤖", "Google AI": "🧠", "DeepSeek": "🔍",
            "Perplexity": "💡", "ArXiv": "📚",
            "Nature Machine Intelligence": "🔬", "Science AI": "🔬",
            "Berkeley AI Research": "🎓", "CMU ML Blog": "🎓",
            "Stanford AI Lab": "🎓", "Papers with Code": "📊",
        }.get(article.source, "🔗")

        is_breakthrough = article.relevance_score >= 85
        header = "**AI Research Breakthrough**" if is_breakthrough else "**AI Research Update**"
        score_badge = (
            f" Score: {article.relevance_score:.0f}/100"
            if article.relevance_score >= 70
            else ""
        )

        tag = article.source.replace(" ", "").replace(".", "")
        return (
            f"{header} {source_emoji}{score_badge}\n\n"
            f"**{article.title}**\n\n"
            f"**Summary:**\n{summary}\n\n"
            f"**Source:** {article.source}\n"
            f"**Read More:** {article.url}\n\n"
            f"#{tag} #AIResearch #MachineLearning"
        )

    # ------------------------------------------------------------------
    # Interactive command callbacks
    # ------------------------------------------------------------------

    async def _handle_search(self, message, query: str) -> None:
        from .utils import NewsSearchEngine

        search_engine = NewsSearchEngine(self.db_manager)
        results = await search_engine.search(query=query, limit=5)

        if not results:
            await message.answer(f"No articles found for: *{query}*")
            return

        lines = [f"**Search results for:** _{query}_\n"]
        for i, a in enumerate(results, 1):
            score = a.get("relevance_score", 0)
            lines.append(f"{i}. [{a['title'][:70]}]({a['url']})  ({score:.0f})")
        await message.answer("\n".join(lines), disable_web_page_preview=True)

    async def _handle_trending(self, message) -> None:
        from .utils import NewsSearchEngine

        search_engine = NewsSearchEngine(self.db_manager)
        topics = await search_engine.get_trending_topics(days=7)

        if not topics:
            await message.answer("No trending data yet.")
            return

        lines = ["**Trending AI Topics (7 days)**\n"]
        for i, (topic, count) in enumerate(list(topics.items())[:10], 1):
            bar = "█" * min(count, 20)
            lines.append(f"{i}. {topic}: {bar} ({count})")
        await message.answer("\n".join(lines))

    async def _handle_stats(self, message) -> None:
        stats = await self.db_manager.get_statistics()

        health_lines = []
        for name, counts in self._source_health.items():
            total = counts["success"] + counts["failure"]
            rate = (counts["success"] / total * 100) if total else 0
            health_lines.append(f"  {name}: {rate:.0f}% ok ({total} fetches)")

        text = (
            f"**Database Statistics**\n\n"
            f"Total articles: {stats['total_articles']}\n"
            f"Articles today: {stats['articles_today']}\n"
            f"Failed articles: {stats['failed_articles']}\n"
        )
        if health_lines:
            text += "\n**Source Health**\n" + "\n".join(health_lines)
        await message.answer(text)

    async def _handle_digest(self, message) -> None:
        await message.answer("Generating digest...")
        digest_text = await self.digest_generator.generate_digest()
        if digest_text:
            await self.telegram_bot.send_message(
                chat_id=str(message.chat.id), message=digest_text
            )
        else:
            await message.answer("No articles found for digest.")

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def start(self) -> None:
        self.logger.info("Starting AI News Aggregator...")

        await self.initialize()

        # Schedule news fetching
        self.scheduler.add_job(
            self.fetch_and_process_news,
            trigger=IntervalTrigger(minutes=self.config.fetch_interval_minutes),
            id="fetch_news",
            name="Fetch and Process News",
            max_instances=1,
            replace_existing=True,
        )

        # Schedule daily digest (if enabled)
        if self.config.digest_enabled:
            self.scheduler.add_job(
                self._post_scheduled_digest,
                trigger=CronTrigger(hour=self.config.digest_schedule_hour, minute=0),
                id="daily_digest",
                name="Daily Digest",
                max_instances=1,
                replace_existing=True,
            )
            self.logger.info(
                f"Daily digest scheduled at {self.config.digest_schedule_hour}:00"
            )

        self.scheduler.start()
        self.running = True

        # Run initial fetch
        await self.fetch_and_process_news()

        self.logger.info(
            f"News aggregator started. Fetching every "
            f"{self.config.fetch_interval_minutes} minutes."
        )

        # Start polling for interactive commands in background
        polling_task = asyncio.create_task(self._safe_start_polling())

        try:
            while self.running:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("Received shutdown signal")
        finally:
            polling_task.cancel()
            await self.shutdown()

    async def _safe_start_polling(self) -> None:
        """Start Telegram polling with error recovery."""
        try:
            await self.telegram_bot.start_polling()
        except asyncio.CancelledError:
            pass
        except Exception as e:
            self.logger.error(f"Telegram polling error: {e}")

    async def _post_scheduled_digest(self) -> None:
        """Post a scheduled digest to the configured channel."""
        try:
            digest_text = await self.digest_generator.generate_digest()
            if digest_text:
                await self.telegram_bot.send_message(
                    chat_id=self.config.telegram_channel_id,
                    message=digest_text,
                )
                self.logger.info("Posted daily digest")
            else:
                self.logger.info("No articles for daily digest")
        except Exception as e:
            self.logger.error(f"Error posting digest: {e}")

    async def shutdown(self) -> None:
        self.logger.info("Shutting down AI News Aggregator...")
        self.running = False

        if self.scheduler.running:
            self.scheduler.shutdown(wait=True)

        await self.db_manager.close()

        for source in self.news_sources:
            if hasattr(source, "close"):
                await source.close()

        self.logger.info("Shutdown complete")


def setup_signal_handlers(aggregator: AINewsAggregator) -> None:
    def signal_handler(signum, frame):
        aggregator.logger.info(f"Received signal {signum}")
        aggregator.running = False

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


def main() -> None:
    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        print("\nShutdown requested by user")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


async def async_main() -> None:
    config = load_config()

    Path(config.database_path).parent.mkdir(parents=True, exist_ok=True)
    Path(config.log_file).parent.mkdir(parents=True, exist_ok=True)

    aggregator = AINewsAggregator(config)
    setup_signal_handlers(aggregator)

    try:
        await aggregator.start()
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
