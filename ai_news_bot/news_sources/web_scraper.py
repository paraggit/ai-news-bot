"""
Web scraper news source implementation.

This module scrapes official blog pages from AI companies like OpenAI, Google AI, etc.
"""

from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

from .base import NewsSource, Article
from ..config import WEB_SCRAPING_TARGETS


class WebScraperSource(NewsSource):
    """News source that scrapes official company blogs and websites."""
    
    def __init__(self, config) -> None:
        """Initialize web scraper source."""
        super().__init__(config, "Web Scraper")
        self.scraping_targets = WEB_SCRAPING_TARGETS
    
    async def fetch_articles(self) -> List[Article]:
        """Fetch articles from all configured web scraping targets."""
        all_articles = []
        
        for site_name, site_config in self.scraping_targets.items():
            try:
                articles = await self._scrape_site(site_name, site_config)
                self.logger.info(f"Scraped {len(articles)} articles from {site_name}")
                all_articles.extend(articles)
            except Exception as e:
                self.logger.error(f"Error scraping {site_name}: {e}")
        
        # Sort by publication date (newest first)
        # Ensure all datetimes are timezone-aware for comparison
        def get_sort_key(article):
            if article.published_date is None:
                return datetime.min.replace(tzinfo=timezone.utc)
            # If the datetime is naive, assume UTC
            if article.published_date.tzinfo is None:
                return article.published_date.replace(tzinfo=timezone.utc)
            return article.published_date
        
        all_articles.sort(key=get_sort_key, reverse=True)
        
        return all_articles[:self.config.max_articles_per_run]
    
    async def _scrape_site(self, site_name: str, site_config: Dict[str, Any]) -> List[Article]:
        """Scrape articles from a specific website."""
        try:
            base_url = site_config['url']
            
            # Fetch the main page
            html_content = await self._fetch_url(base_url)
            if not html_content:
                return []
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Find article links
            articles = []
            link_elements = soup.select(site_config['link_selector'])
            
            for link_elem in link_elements[:10]:  # Limit to first 10 articles
                try:
                    article = await self._extract_article_from_link(
                        link_elem, base_url, site_name, site_config
                    )
                    if article and article.is_valid:
                        # Enrich article with metadata
                        article = self._enrich_article_metadata(article)
                        articles.append(article)
                except Exception as e:
                    self.logger.error(f"Error extracting article from {site_name}: {e}")
            
            return articles
            
        except Exception as e:
            self.logger.error(f"Error scraping site {site_name}: {e}")
            return []
    
    async def _extract_article_from_link(
        self, 
        link_elem, 
        base_url: str, 
        site_name: str, 
        site_config: Dict[str, Any]
    ) -> Optional[Article]:
        """Extract article information from a link element."""
        try:
            # Extract URL
            href = link_elem.get('href')
            if not href:
                return None
            
            # Convert relative URLs to absolute
            article_url = urljoin(base_url, href)
            
            # Extract title from link text or title attribute
            title = link_elem.get_text(strip=True) or link_elem.get('title', '')
            title = self._clean_text(title)
            
            if not title or len(title) < 10:
                return None
            
            # Fetch full article content
            content = await self._fetch_article_content(article_url, site_config)
            if not content:
                return None
            
            # Try to extract publication date from the article page
            published_date = await self._extract_publication_date(article_url)
            
            return Article(
                title=title,
                url=article_url,
                content=content,
                source=site_name,
                published_date=published_date,
                tags=['AI', 'Official Blog']
            )
            
        except Exception as e:
            self.logger.error(f"Error extracting article from link: {e}")
            return None
    
    async def _fetch_article_content(self, url: str, site_config: Dict[str, Any]) -> Optional[str]:
        """Fetch the full content of an article."""
        try:
            html_content = await self._fetch_url(url)
            if not html_content:
                return None
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove unwanted elements
            for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'iframe']):
                element.decompose()
            
            # Try the configured content selector first
            content = ""
            if 'content_selector' in site_config:
                content_elements = soup.select(site_config['content_selector'])
                if content_elements:
                    content = content_elements[0].get_text()
            
            # Fallback selectors if configured selector doesn't work
            if not content or len(content) < 100:
                fallback_selectors = [
                    'article',
                    '.article-content',
                    '.post-content',
                    '.entry-content',
                    '.content',
                    'main',
                    '[role="main"]'
                ]
                
                for selector in fallback_selectors:
                    elements = soup.select(selector)
                    if elements:
                        content = elements[0].get_text()
                        if len(content) > 100:
                            break
            
            # Final fallback to body content
            if not content or len(content) < 100:
                body = soup.find('body')
                if body:
                    content = body.get_text()
            
            # Clean and validate content
            content = self._clean_text(content)
            
            if len(content) > 200:  # Minimum content length
                return content
            
        except Exception as e:
            self.logger.debug(f"Error fetching article content from {url}: {e}")
        
        return None
    
    async def _extract_publication_date(self, url: str) -> Optional[datetime]:
        """Try to extract publication date from article page."""
        try:
            html_content = await self._fetch_url(url)
            if not html_content:
                return None
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Common date selectors
            date_selectors = [
                'time[datetime]',
                '.published',
                '.post-date',
                '.article-date',
                '.date',
                '[class*="date"]',
                '[class*="time"]'
            ]
            
            for selector in date_selectors:
                elements = soup.select(selector)
                for elem in elements:
                    # Try datetime attribute first
                    datetime_attr = elem.get('datetime')
                    if datetime_attr:
                        try:
                            return datetime.fromisoformat(datetime_attr.replace('Z', '+00:00'))
                        except (ValueError, TypeError):
                            pass
                    
                    # Try text content
                    date_text = elem.get_text(strip=True)
                    if date_text:
                        parsed_date = self._parse_date_string(date_text)
                        if parsed_date:
                            return parsed_date
            
        except Exception as e:
            self.logger.debug(f"Error extracting publication date from {url}: {e}")
        
        return None
    
    def _parse_date_string(self, date_string: str) -> Optional[datetime]:
        """Parse various date string formats."""
        import re
        from dateutil import parser
        
        try:
            # Clean the date string
            date_string = re.sub(r'[^\w\s\-\/:,]', '', date_string)
            
            # Try parsing with dateutil
            parsed_date = parser.parse(date_string, fuzzy=True)
            
            # Ensure timezone info
            if parsed_date.tzinfo is None:
                parsed_date = parsed_date.replace(tzinfo=timezone.utc)
            
            return parsed_date
            
        except (ValueError, TypeError):
            return None