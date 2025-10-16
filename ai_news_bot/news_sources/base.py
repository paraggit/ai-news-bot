"""
Base classes for news sources.

This module defines the abstract base class and data structures
for all news source implementations.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
import asyncio
import ssl
import aiohttp
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)


@dataclass
class Article:
    """Represents a news article or research paper."""
    
    title: str
    url: str
    content: str
    source: str
    published_date: Optional[datetime] = None
    author: Optional[str] = None
    summary: Optional[str] = None
    tags: Optional[List[str]] = None
    # Enhanced fields for better search and filtering
    topics: Optional[List[str]] = None
    keywords: Optional[List[str]] = None
    relevance_score: float = 0.0
    
    def __post_init__(self):
        """Post-initialization validation."""
        if not self.title or not self.url:
            raise ValueError("Title and URL are required")
        
        # Ensure tags is a list
        if self.tags is None:
            self.tags = []
        if self.topics is None:
            self.topics = []
        if self.keywords is None:
            self.keywords = []
    
    @property
    def is_valid(self) -> bool:
        """Check if the article has minimum required content."""
        return (
            len(self.title.strip()) > 10 and
            len(self.content.strip()) > 50 and
            self.url.startswith(('http://', 'https://'))
        )


class NewsSource(ABC):
    """Abstract base class for all news sources."""
    
    def __init__(self, config, source_name: str) -> None:
        """Initialize the news source."""
        self.config = config
        self.source_name = source_name
        self.session: Optional[aiohttp.ClientSession] = None
        self.logger = logger.getChild(self.__class__.__name__)
        self.content_analyzer = None  # Will be initialized in initialize()
    
    async def initialize(self) -> None:
        """Initialize the news source (create HTTP session, etc.)."""
        import ssl
        import certifi
        
        # Initialize content analyzer
        from ..utils.content_analyzer import ContentAnalyzer
        self.content_analyzer = ContentAnalyzer()
        
        # Create SSL context based on configuration
        ssl_verify = getattr(self.config, 'ssl_verify', True)
        http_timeout = getattr(self.config, 'http_timeout', 30)
        user_agent = getattr(self.config, 'user_agent', 'AI-News-Aggregator-Bot/1.0')
        
        if ssl_verify:
            try:
                ssl_context = ssl.create_default_context(cafile=certifi.where())
            except Exception as e:
                self.logger.warning(f"Failed to create SSL context with certifi: {e}")
                ssl_context = ssl.create_default_context()
        else:
            # Disable SSL verification (for testing/debugging only)
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            self.logger.warning("SSL verification disabled - this reduces security!")
        
        # Create connector with SSL context
        connector = aiohttp.TCPConnector(
            ssl=ssl_context,
            limit=30,
            limit_per_host=10,
            keepalive_timeout=30,
            enable_cleanup_closed=True
        )
        
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=http_timeout, connect=10),
            headers={
                'User-Agent': user_agent,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            },
            connector=connector
        )
        self.logger.info(f"Initialized {self.source_name} news source")
    
    async def close(self) -> None:
        """Clean up resources."""
        if self.session:
            await self.session.close()
            self.session = None
        self.logger.info(f"Closed {self.source_name} news source")
    
    @abstractmethod
    async def fetch_articles(self) -> List[Article]:
        """Fetch articles from this news source."""
        pass
    
    async def _fetch_url(self, url: str) -> Optional[str]:
        """Fetch content from a URL with error handling and retries."""
        if not self.session:
            raise RuntimeError("Session not initialized. Call initialize() first.")
        
        max_retries = getattr(self.config, 'max_retries', 3)
        base_delay = 1.0
        
        for attempt in range(max_retries):
            try:
                async with self.session.get(url) as response:
                    if response.status == 200:
                        content = await response.text()
                        self.logger.debug(f"Successfully fetched {url}")
                        return content
                    elif response.status == 429:
                        # Rate limited, wait longer
                        delay = base_delay * (2 ** attempt) * 2
                        self.logger.warning(f"Rate limited for {url}, waiting {delay}s")
                        await asyncio.sleep(delay)
                        continue
                    elif response.status in [503, 502, 504]:
                        # Server error, retry
                        delay = base_delay * (2 ** attempt)
                        self.logger.warning(f"Server error {response.status} for {url}, retrying in {delay}s")
                        await asyncio.sleep(delay)
                        continue
                    else:
                        self.logger.warning(f"HTTP {response.status} for {url}")
                        return None
            
            except ssl.SSLError as e:
                self.logger.warning(f"SSL error for {url}: {e}")
                # Don't retry SSL errors multiple times, just fail
                return None
            
            except asyncio.TimeoutError:
                delay = base_delay * (2 ** attempt)
                self.logger.warning(f"Timeout fetching {url}, retry {attempt + 1}/{max_retries}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(delay)
                continue
            
            except aiohttp.ClientError as e:
                if "SSL" in str(e) or "certificate" in str(e).lower():
                    self.logger.warning(f"SSL/Certificate error for {url}: {e}")
                else:
                    self.logger.error(f"Client error fetching {url}: {e}")
                return None
            
            except Exception as e:
                self.logger.error(f"Unexpected error fetching {url}: {e}")
                return None
        
        self.logger.error(f"Failed to fetch {url} after {max_retries} attempts")
        return None
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text content."""
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = " ".join(text.split())
        
        # Remove common HTML entities that might have been missed
        replacements = {
            '&nbsp;': ' ',
            '&amp;': '&',
            '&lt;': '<',
            '&gt;': '>',
            '&quot;': '"',
            '&#39;': "'",
            '&hellip;': '...',
        }
        
        for entity, replacement in replacements.items():
            text = text.replace(entity, replacement)
        
        return text.strip()
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain name from URL."""
        try:
            parsed = urlparse(url)
            return parsed.netloc.lower().replace('www.', '')
        except Exception:
            return "unknown"
    
    def _is_ai_related(self, title: str, content: str) -> bool:
        """Check if content is AI-related using the content analyzer."""
        if not self.content_analyzer:
            # Fallback to basic keyword matching if analyzer not initialized
            basic_keywords = ['artificial intelligence', 'machine learning', 'ai', 'llm', 'gpt']
            text_lower = f"{title} {content}".lower()
            return any(kw in text_lower for kw in basic_keywords)
        
        analysis = self.content_analyzer.analyze_article(title, content)
        return analysis['is_ai_related']
    
    def _enrich_article_metadata(self, article: Article) -> Article:
        """
        Enrich article with metadata using content analyzer.
        Adds topics, keywords, and relevance score.
        """
        if not self.content_analyzer:
            return article
        
        try:
            analysis = self.content_analyzer.analyze_article(article.title, article.content)
            
            article.topics = analysis.get('topics', [])
            article.keywords = analysis.get('keywords', [])
            article.relevance_score = analysis.get('relevance_score', 0.0)
            
            self.logger.debug(
                f"Enriched article '{article.title[:50]}...' with "
                f"relevance={article.relevance_score:.1f}, "
                f"topics={len(article.topics)}, "
                f"keywords={len(article.keywords)}"
            )
        except Exception as e:
            self.logger.warning(f"Failed to enrich article metadata: {e}")
        
        return article