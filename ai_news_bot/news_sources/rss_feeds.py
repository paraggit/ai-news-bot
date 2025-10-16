"""
RSS Feed news source implementation.

This module fetches AI news from various RSS feeds of tech news websites.
"""

import feedparser
from datetime import datetime, timezone
from typing import List, Optional
from bs4 import BeautifulSoup

from .base import NewsSource, Article
from ..config import RSS_FEEDS


class RSSFeedSource(NewsSource):
    """News source that fetches from RSS feeds."""
    
    def __init__(self, config) -> None:
        """Initialize RSS feed source."""
        super().__init__(config, "RSS Feeds")
        self.feed_urls = RSS_FEEDS
    
    async def fetch_articles(self) -> List[Article]:
        """Fetch articles from all configured RSS feeds."""
        all_articles = []
        
        for feed_name, feed_url in self.feed_urls.items():
            try:
                articles = await self._fetch_from_feed(feed_name, feed_url)
                self.logger.info(f"Fetched {len(articles)} articles from {feed_name}")
                all_articles.extend(articles)
            except Exception as e:
                self.logger.error(f"Error fetching from {feed_name}: {e}")
        
        # Sort by publication date (newest first)
        all_articles.sort(key=lambda x: x.published_date or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
        
        # Filter for AI-related content and return top articles
        ai_articles = [article for article in all_articles if self._is_ai_related(article.title, article.content)]
        
        return ai_articles[:self.config.max_articles_per_run]
    
    async def _fetch_from_feed(self, feed_name: str, feed_url: str) -> List[Article]:
        """Fetch articles from a single RSS feed."""
        try:
            # Fetch RSS content
            rss_content = await self._fetch_url(feed_url)
            if not rss_content:
                return []
            
            # Parse RSS feed
            feed = feedparser.parse(rss_content)
            if not feed.entries:
                self.logger.warning(f"No entries found in feed {feed_name}")
                return []
            
            articles = []
            for entry in feed.entries:
                try:
                    article = await self._parse_rss_entry(entry, feed_name)
                    if article and article.is_valid:
                        # Enrich article with metadata
                        article = self._enrich_article_metadata(article)
                        articles.append(article)
                except Exception as e:
                    self.logger.error(f"Error parsing entry from {feed_name}: {e}")
            
            return articles
            
        except Exception as e:
            self.logger.error(f"Error fetching RSS feed {feed_name}: {e}")
            return []
    
    async def _parse_rss_entry(self, entry, feed_name: str) -> Optional[Article]:
        """Parse a single RSS entry into an Article object."""
        try:
            # Extract basic information
            title = self._clean_text(entry.get('title', ''))
            url = entry.get('link', '')
            
            if not title or not url:
                return None
            
            # Extract content
            content = ""
            if hasattr(entry, 'content') and entry.content:
                content = entry.content[0].value if isinstance(entry.content, list) else entry.content
            elif hasattr(entry, 'summary'):
                content = entry.summary
            elif hasattr(entry, 'description'):
                content = entry.description
            
            # Clean HTML from content
            if content:
                soup = BeautifulSoup(content, 'html.parser')
                content = soup.get_text()
                content = self._clean_text(content)
            
            # If content is too short, try to fetch full article
            if len(content) < 200:
                full_content = await self._fetch_full_article_content(url)
                if full_content:
                    content = full_content
            
            # Extract publication date
            published_date = None
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                try:
                    published_date = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                except (ValueError, TypeError):
                    pass
            
            # Extract author
            author = None
            if hasattr(entry, 'author'):
                author = self._clean_text(entry.author)
            
            # Extract tags
            tags = []
            if hasattr(entry, 'tags'):
                tags = [tag.term for tag in entry.tags if hasattr(tag, 'term')]
            
            return Article(
                title=title,
                url=url,
                content=content,
                source=feed_name,
                published_date=published_date,
                author=author,
                tags=tags
            )
            
        except Exception as e:
            self.logger.error(f"Error parsing RSS entry: {e}")
            return None
    
    async def _fetch_full_article_content(self, url: str) -> Optional[str]:
        """Attempt to fetch full article content from the article URL."""
        try:
            html_content = await self._fetch_url(url)
            if not html_content:
                return None
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "header", "footer", "aside"]):
                script.decompose()
            
            # Try common content selectors
            content_selectors = [
                'article',
                '.article-content',
                '.post-content', 
                '.entry-content',
                '.content',
                'main',
                '[role="main"]'
            ]
            
            content = ""
            for selector in content_selectors:
                elements = soup.select(selector)
                if elements:
                    content = elements[0].get_text()
                    break
            
            # Fallback to body if no specific content found
            if not content:
                body = soup.find('body')
                if body:
                    content = body.get_text()
            
            # Clean and return content
            content = self._clean_text(content)
            
            # Only return if we got substantial content
            if len(content) > 200:
                return content
            
        except Exception as e:
            self.logger.debug(f"Could not fetch full content for {url}: {e}")
        
        return None