"""
ArXiv news source implementation.

This module fetches the latest AI research papers from arXiv.org
using their API.
"""

import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import List, Optional
from urllib.parse import urlencode

from .base import NewsSource, Article


class ArXivSource(NewsSource):
    """News source that fetches AI research papers from arXiv."""
    
    BASE_URL = "http://export.arxiv.org/api/query"
    
    def __init__(self, config) -> None:
        """Initialize ArXiv source."""
        super().__init__(config, "ArXiv")
        self.categories = config.arxiv_categories
        self.max_results = config.arxiv_max_results
    
    async def fetch_articles(self) -> List[Article]:
        """Fetch recent AI papers from arXiv."""
        all_papers = []
        
        for category in self.categories:
            try:
                papers = await self._fetch_papers_by_category(category)
                self.logger.info(f"Fetched {len(papers)} papers from category {category}")
                all_papers.extend(papers)
            except Exception as e:
                self.logger.error(f"Error fetching from arXiv category {category}: {e}")
        
        # Sort by publication date (newest first) and limit results
        all_papers.sort(key=lambda x: x.published_date or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
        
        return all_papers[:self.max_results]
    
    async def _fetch_papers_by_category(self, category: str) -> List[Article]:
        """Fetch papers from a specific arXiv category."""
        try:
            # Build query parameters
            query_params = {
                'search_query': f'cat:{category}',
                'start': 0,
                'max_results': self.max_results,
                'sortBy': 'submittedDate',
                'sortOrder': 'descending'
            }
            
            url = f"{self.BASE_URL}?{urlencode(query_params)}"
            
            # Fetch XML response
            xml_content = await self._fetch_url(url)
            if not xml_content:
                return []
            
            # Parse XML
            root = ET.fromstring(xml_content)
            
            papers = []
            for entry in root.findall('{http://www.w3.org/2005/Atom}entry'):
                try:
                    paper = self._parse_arxiv_entry(entry)
                    if paper and paper.is_valid:
                        # Enrich paper with metadata
                        paper = self._enrich_article_metadata(paper)
                        papers.append(paper)
                except Exception as e:
                    self.logger.error(f"Error parsing arXiv entry: {e}")
            
            return papers
            
        except Exception as e:
            self.logger.error(f"Error fetching arXiv category {category}: {e}")
            return []
    
    def _parse_arxiv_entry(self, entry) -> Optional[Article]:
        """Parse an arXiv XML entry into an Article object."""
        try:
            # Define namespace
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            
            # Extract title
            title_elem = entry.find('atom:title', ns)
            title = title_elem.text.strip() if title_elem is not None else ""
            
            # Extract ID/URL
            id_elem = entry.find('atom:id', ns)
            arxiv_id = id_elem.text.strip() if id_elem is not None else ""
            
            if not title or not arxiv_id:
                return None
            
            # Convert arXiv ID to URL
            if arxiv_id.startswith('http://arxiv.org/abs/'):
                url = arxiv_id
            else:
                url = f"https://arxiv.org/abs/{arxiv_id.split('/')[-1]}"
            
            # Extract summary/abstract
            summary_elem = entry.find('atom:summary', ns)
            abstract = summary_elem.text.strip() if summary_elem is not None else ""
            abstract = self._clean_text(abstract)
            
            # Extract authors
            authors = []
            for author_elem in entry.findall('atom:author', ns):
                name_elem = author_elem.find('atom:name', ns)
                if name_elem is not None:
                    authors.append(name_elem.text.strip())
            
            author_str = ", ".join(authors) if authors else None
            
            # Extract publication date
            published_elem = entry.find('atom:published', ns)
            published_date = None
            if published_elem is not None:
                try:
                    # Parse ISO format: 2024-01-15T18:00:00Z
                    date_str = published_elem.text.strip()
                    published_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                except (ValueError, TypeError):
                    pass
            
            # Extract categories/tags
            tags = []
            for category_elem in entry.findall('atom:category', ns):
                term = category_elem.get('term')
                if term:
                    tags.append(term)
            
            # Create comprehensive content from title and abstract
            content = f"{title}\n\n{abstract}"
            
            return Article(
                title=title,
                url=url,
                content=content,
                source="ArXiv",
                published_date=published_date,
                author=author_str,
                tags=tags
            )
            
        except Exception as e:
            self.logger.error(f"Error parsing arXiv entry: {e}")
            return None
    
    def _clean_text(self, text: str) -> str:
        """Clean arXiv text content."""
        if not text:
            return ""
        
        # Remove extra whitespace and newlines
        text = " ".join(text.split())
        
        # Remove common arXiv formatting artifacts
        text = text.replace('\\n', ' ')
        text = text.replace('\\', '')
        
        return super()._clean_text(text)