"""
News sources package for AI News Aggregator Bot.

This package provides various news source implementations for gathering
AI-related content from different sources.
"""

from typing import List
from ..config import Config
from .base import NewsSource
from .rss_feeds import RSSFeedSource
from .arxiv import ArXivSource
from .web_scraper import WebScraperSource


def get_all_news_sources(config: Config) -> List[NewsSource]:
    """Get all configured news sources."""
    sources = []
    
    # Add RSS feed sources
    sources.append(RSSFeedSource(config))
    
    # Add ArXiv source
    sources.append(ArXivSource(config))
    
    # Add web scraper sources
    sources.append(WebScraperSource(config))
    
    return sources


__all__ = [
    "NewsSource",
    "RSSFeedSource", 
    "ArXivSource",
    "WebScraperSource",
    "get_all_news_sources"
]