"""
Perplexity Search API news source implementation.

This module uses Perplexity's Search API to actively search for
the latest AI research, news, and developments across the web.
"""

import json
from datetime import datetime, timezone
from typing import List, Optional
import aiohttp

from .base import NewsSource, Article


class PerplexitySearchSource(NewsSource):
    """News source that uses Perplexity Search API to find AI research."""
    
    BASE_URL = "https://api.perplexity.ai/chat/completions"
    
    def __init__(self, config) -> None:
        """Initialize Perplexity Search source."""
        super().__init__(config, "Perplexity Search")
        self.api_key = config.perplexity_api_key
        self.search_queries = config.perplexity_search_queries
        self.max_results_per_query = config.perplexity_max_results
        self.model = config.perplexity_model
    
    async def fetch_articles(self) -> List[Article]:
        """Fetch AI research and news using Perplexity Search API."""
        if not self.api_key:
            self.logger.warning("Perplexity API key not configured, skipping")
            return []
        
        all_articles = []
        
        for query in self.search_queries:
            try:
                articles = await self._search_for_topic(query)
                self.logger.info(f"Found {len(articles)} articles for query: '{query}'")
                all_articles.extend(articles)
            except Exception as e:
                self.logger.error(f"Error searching Perplexity for '{query}': {e}")
        
        # Remove duplicates based on URL
        seen_urls = set()
        unique_articles = []
        for article in all_articles:
            if article.url not in seen_urls:
                seen_urls.add(article.url)
                unique_articles.append(article)
        
        # Sort by published date (newest first)
        def get_sort_key(article):
            if article.published_date is None:
                return datetime.min.replace(tzinfo=timezone.utc)
            if article.published_date.tzinfo is None:
                return article.published_date.replace(tzinfo=timezone.utc)
            return article.published_date
        
        unique_articles.sort(key=get_sort_key, reverse=True)
        
        # Return top articles
        return unique_articles[:self.config.max_articles_per_run]
    
    async def _search_for_topic(self, query: str) -> List[Article]:
        """Search for a specific topic using Perplexity API."""
        try:
            # Construct the search prompt
            search_prompt = self._build_search_prompt(query)
            
            # Make API request
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a research assistant that finds and summarizes the latest AI research and news. Always include source URLs and publication dates when available."
                    },
                    {
                        "role": "user",
                        "content": search_prompt
                    }
                ],
                "max_tokens": 2000,
                "temperature": 0.2,
                "top_p": 0.9,
                "search_domain_filter": ["perplexity.ai"],
                "return_images": False,
                "return_related_questions": False,
                "search_recency_filter": "month",  # Focus on recent content
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.BASE_URL,
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        self.logger.error(f"Perplexity API error: {response.status} - {error_text}")
                        return []
                    
                    result = await response.json()
            
            # Parse the response
            articles = self._parse_search_response(result, query)
            return articles
            
        except Exception as e:
            self.logger.error(f"Error searching Perplexity for '{query}': {e}")
            return []
    
    def _build_search_prompt(self, query: str) -> str:
        """Build an effective search prompt for Perplexity."""
        return f"""Find the latest and most important news, research papers, and developments about: {query}

Please provide:
1. Recent breakthroughs or significant developments (last 30 days preferred)
2. Research papers with arXiv links if available
3. Product announcements or updates from major AI companies
4. Technical blog posts from leading researchers or companies

For each item, include:
- Title
- Brief summary (2-3 sentences)
- Source URL
- Publication date (if available)
- Why it's significant

Focus on technical and research content, not funding news or business deals.
Provide up to 5 most relevant and recent items."""
    
    def _parse_search_response(self, response: dict, query: str) -> List[Article]:
        """Parse Perplexity API response into Article objects."""
        articles = []
        
        try:
            # Extract the response content
            if "choices" not in response or not response["choices"]:
                self.logger.warning("No choices in Perplexity response")
                return articles
            
            content = response["choices"][0].get("message", {}).get("content", "")
            
            if not content:
                self.logger.warning("Empty content in Perplexity response")
                return articles
            
            # Extract citations/sources if available
            citations = response.get("citations", [])
            
            # Parse the content to extract articles
            # This is a simplified parser - you may want to make it more robust
            lines = content.split('\n')
            current_article = {}
            
            for line in lines:
                line = line.strip()
                
                # Look for titles (usually start with numbers or bullets)
                if line and (line[0].isdigit() or line.startswith('-') or line.startswith('*')):
                    # Save previous article if exists
                    if current_article.get('title') and current_article.get('content'):
                        article = self._create_article_from_parsed(current_article, query, citations)
                        if article:
                            articles.append(article)
                    
                    # Start new article
                    # Extract title (remove numbering/bullets)
                    title = line.lstrip('0123456789.-*• ').strip()
                    if title.startswith('[') or title.startswith('**'):
                        title = title.lstrip('[*').rstrip(']*').strip()
                    
                    current_article = {
                        'title': title,
                        'content': '',
                        'url': None
                    }
                elif current_article and line:
                    # Accumulate content
                    if 'content' in current_article:
                        current_article['content'] += line + ' '
                    
                    # Try to extract URL from the line
                    if 'http' in line:
                        import re
                        urls = re.findall(r'https?://[^\s<>"{}|\\^`\[\]]+', line)
                        if urls and not current_article.get('url'):
                            current_article['url'] = urls[0]
            
            # Don't forget the last article
            if current_article.get('title') and current_article.get('content'):
                article = self._create_article_from_parsed(current_article, query, citations)
                if article:
                    articles.append(article)
            
            # If we couldn't parse individual articles, create one from the whole response
            if not articles and content:
                self.logger.info(f"Creating single article from Perplexity response for: {query}")
                article = Article(
                    title=f"Latest Research on {query}",
                    url=citations[0] if citations else f"https://www.perplexity.ai/search?q={query.replace(' ', '+')}",
                    content=content,
                    source="Perplexity Search",
                    published_date=datetime.now(timezone.utc),
                    tags=[query, "perplexity-search"],
                )
                
                # Enrich with metadata
                if self.content_analyzer:
                    article = self._enrich_article_metadata(article)
                
                if article.is_valid:
                    articles.append(article)
            
        except Exception as e:
            self.logger.error(f"Error parsing Perplexity response: {e}")
        
        return articles
    
    def _create_article_from_parsed(
        self, 
        parsed_data: dict, 
        query: str,
        citations: List[str]
    ) -> Optional[Article]:
        """Create an Article object from parsed data."""
        try:
            title = parsed_data.get('title', '').strip()
            content = parsed_data.get('content', '').strip()
            url = parsed_data.get('url')
            
            # If no URL found, use first citation or generate Perplexity search URL
            if not url:
                if citations:
                    url = citations[0]
                else:
                    url = f"https://www.perplexity.ai/search?q={title.replace(' ', '+')}"
            
            # Ensure we have minimum content
            if not title or len(title) < 10:
                return None
            
            if not content or len(content) < 30:
                content = title  # Use title as content if content is too short
            
            article = Article(
                title=title,
                url=url,
                content=content,
                source="Perplexity Search",
                published_date=datetime.now(timezone.utc),  # Use current time as we don't have exact dates
                tags=[query, "perplexity-search"],
            )
            
            # Enrich article with metadata
            if self.content_analyzer:
                article = self._enrich_article_metadata(article)
            
            if article.is_valid:
                return article
            
        except Exception as e:
            self.logger.error(f"Error creating article from parsed data: {e}")
        
        return None

