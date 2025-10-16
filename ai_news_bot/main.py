#!/usr/bin/env python3
"""
AI News Aggregator Bot - Main Entry Point

This is the main orchestrator that coordinates news fetching, summarization,
and Telegram posting on a scheduled basis.
"""

import asyncio
import signal
import sys
from pathlib import Path

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from .config import Config, load_config
from .database import DatabaseManager
from .news_sources import get_all_news_sources
from .summarizer import get_summarizer
from .telegram.bot import TelegramBot
from .utils.logger import setup_logger


class AINewsAggregator:
    """Main application class that orchestrates the news aggregation process."""
    
    def __init__(self, config: Config) -> None:
        """Initialize the AI News Aggregator with configuration."""
        self.config = config
        self.logger = setup_logger(config.log_level, config.log_file)
        self.db_manager = DatabaseManager(config.database_path)
        self.scheduler = AsyncIOScheduler()
        self.telegram_bot = TelegramBot(config.telegram_bot_token)
        self.summarizer = get_summarizer(config)
        self.news_sources = get_all_news_sources(config)
        self.running = False

    async def initialize(self) -> None:
        """Initialize all components."""
        self.logger.info("Initializing AI News Aggregator...")
        
        # Initialize database
        await self.db_manager.initialize()
        
        # Initialize news sources
        for source in self.news_sources:
            await source.initialize()
        
        self.logger.info("Initialization complete")

    async def fetch_and_process_news(self) -> None:
        """Main news processing workflow."""
        self.logger.info("Starting news fetch and processing cycle")
        
        try:
            # Fetch articles from all sources
            all_articles = []
            for source in self.news_sources:
                try:
                    articles = await source.fetch_articles()
                    self.logger.info(f"Fetched {len(articles)} articles from {source.__class__.__name__}")
                    all_articles.extend(articles)
                except Exception as e:
                    self.logger.error(f"Error fetching from {source.__class__.__name__}: {e}")
            
            # Filter out already processed articles
            new_articles = []
            for article in all_articles:
                if not await self.db_manager.article_exists(article.url):
                    new_articles.append(article)
            
            self.logger.info(f"Found {len(new_articles)} new articles to process")
            
            # Remove duplicates based on title similarity
            from .utils import ArticleFilter
            article_filter = ArticleFilter()
            
            # Convert Article objects to dicts for filtering
            article_dicts = [
                {
                    'title': a.title,
                    'url': a.url,
                    'relevance_score': a.relevance_score,
                    'article_obj': a
                }
                for a in new_articles
            ]
            
            # Remove duplicates
            unique_articles = article_filter.remove_duplicates(article_dicts, similarity_threshold=0.8)
            
            # Rank by quality
            ranked_articles = article_filter.rank_by_quality(unique_articles)
            
            # Extract Article objects
            new_articles = [a['article_obj'] for a in ranked_articles]
            
            self.logger.info(f"After deduplication and ranking: {len(new_articles)} articles")
            
            # Limit articles per run to avoid overwhelming
            if len(new_articles) > self.config.max_articles_per_run:
                new_articles = new_articles[:self.config.max_articles_per_run]
                self.logger.info(f"Limited to {self.config.max_articles_per_run} articles for this run")
            
            # Process each new article
            for article in new_articles:
                try:
                    await self._process_single_article(article)
                except Exception as e:
                    self.logger.error(f"Error processing article {article.title}: {e}")
            
            self.logger.info("News processing cycle completed")
            
        except Exception as e:
            self.logger.error(f"Error in fetch and process cycle: {e}")

    async def _process_single_article(self, article) -> None:
        """Process a single article: summarize and post to Telegram."""
        self.logger.info(f"Processing article: {article.title}")
        
        try:
            # Generate summary
            summary = await self.summarizer.summarize(
                title=article.title,
                content=article.content,
                source_url=article.url
            )
            
            # Create Telegram message
            message = self._format_telegram_message(article, summary)
            
            # Post to Telegram
            success = await self.telegram_bot.send_message(
                chat_id=self.config.telegram_channel_id,
                message=message
            )
            
            if success:
                # Save to database as processed with enriched metadata
                await self.db_manager.save_article(
                    url=article.url,
                    title=article.title,
                    source=article.source,
                    summary=summary,
                    original_content=article.content[:1000],  # Store first 1000 chars
                    topics=','.join(article.topics) if article.topics else None,
                    keywords=','.join(article.keywords) if article.keywords else None,
                    relevance_score=article.relevance_score
                )
                self.logger.info(
                    f"Successfully processed and posted: {article.title} "
                    f"(relevance: {article.relevance_score:.1f})"
                )
            else:
                self.logger.error(f"Failed to post article to Telegram: {article.title}")
                
        except Exception as e:
            self.logger.error(f"Error processing article {article.title}: {e}")
            raise

    def _format_telegram_message(self, article, summary: str) -> str:
        """Format article and summary into a Telegram message."""
        # Create engaging Telegram message with emojis and formatting
        source_emoji = {
            "OpenAI": "🤖",
            "Google AI": "🧠", 
            "DeepSeek": "🔍",
            "Perplexity": "💡",
            "ArXiv": "📚",
            "TechCrunch": "📰",
            "VentureBeat": "💼",
            "AI News": "🤖"
        }.get(article.source, "🔗")
        
        message = f"""🚀 **AI News Alert** {source_emoji}

**{article.title}**

📝 **Summary:**
{summary}

🔗 **Source:** {article.source}
📰 **Read More:** {article.url}

#{article.source.replace(' ', '').replace('.', '')} #AI #MachineLearning #Tech"""
        
        return message

    async def start(self) -> None:
        """Start the news aggregator with scheduled jobs."""
        self.logger.info("Starting AI News Aggregator...")
        
        await self.initialize()
        
        # Schedule the main job
        self.scheduler.add_job(
            self.fetch_and_process_news,
            trigger=IntervalTrigger(minutes=self.config.fetch_interval_minutes),
            id='fetch_news',
            name='Fetch and Process News',
            max_instances=1,  # Prevent overlapping jobs
            replace_existing=True
        )
        
        # Start scheduler
        self.scheduler.start()
        self.running = True
        
        # Run initial fetch
        await self.fetch_and_process_news()
        
        self.logger.info(f"News aggregator started. Fetching news every {self.config.fetch_interval_minutes} minutes.")
        
        # Keep running
        try:
            while self.running:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("Received shutdown signal")
        finally:
            await self.shutdown()

    async def shutdown(self) -> None:
        """Gracefully shutdown the application."""
        self.logger.info("Shutting down AI News Aggregator...")
        self.running = False
        
        if self.scheduler.running:
            self.scheduler.shutdown(wait=True)
        
        await self.db_manager.close()
        
        # Close news sources
        for source in self.news_sources:
            if hasattr(source, 'close'):
                await source.close()
        
        self.logger.info("Shutdown complete")


def setup_signal_handlers(aggregator: AINewsAggregator) -> None:
    """Setup signal handlers for graceful shutdown."""
    def signal_handler(signum, frame):
        aggregator.logger.info(f"Received signal {signum}")
        aggregator.running = False
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


def main() -> None:
    """Main entry point that runs the async main function."""
    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        print("\nShutdown requested by user")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


async def async_main() -> None:
    """Async main function."""
    # Load configuration
    config = load_config()
    
    # Create directories if they don't exist
    Path(config.database_path).parent.mkdir(parents=True, exist_ok=True)
    Path(config.log_file).parent.mkdir(parents=True, exist_ok=True)
    
    # Create and start aggregator
    aggregator = AINewsAggregator(config)
    setup_signal_handlers(aggregator)
    
    try:
        await aggregator.start()
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Run the main function
    main()