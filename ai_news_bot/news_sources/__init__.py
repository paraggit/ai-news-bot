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
from .perplexity_search import PerplexitySearchSource


def get_all_news_sources(config: Config) -> List[NewsSource]:
    """Get all configured news sources."""
    sources = []
    
    # Add RSS feed sources
    sources.append(RSSFeedSource(config))
    
    # Add ArXiv source
    sources.append(ArXivSource(config))
    
    # Add web scraper sources
    sources.append(WebScraperSource(config))
    
    # Add Perplexity Search source (if API key is configured)
    if config.perplexity_api_key:
        sources.append(PerplexitySearchSource(config))
    
    return sources


__all__ = [
    "NewsSource",
    "RSSFeedSource", 
    "ArXivSource",
    "WebScraperSource",
    "PerplexitySearchSource",
    "get_all_news_sources"
]