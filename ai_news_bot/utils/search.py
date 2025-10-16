"""
Search utility module for AI News Aggregator.

Provides high-level search interface with advanced filtering and ranking.
"""

from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import logging

from ..database import DatabaseManager
from .content_analyzer import ContentAnalyzer

logger = logging.getLogger(__name__)


class NewsSearchEngine:
    """High-level search interface for news articles."""
    
    def __init__(self, db_manager: DatabaseManager):
        """Initialize search engine with database manager."""
        self.db = db_manager
        self.analyzer = ContentAnalyzer()
        self.logger = logger.getChild(self.__class__.__name__)
    
    async def search(
        self,
        query: Optional[str] = None,
        sources: Optional[List[str]] = None,
        topics: Optional[List[str]] = None,
        min_relevance: Optional[float] = None,
        days_back: Optional[int] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Search for articles with flexible filtering.
        
        Args:
            query: Search query for full-text search
            sources: Filter by source names (e.g., ["ArXiv", "TechCrunch AI"])
            topics: Filter by topics (e.g., ["Large Language Models", "Computer Vision"])
            min_relevance: Minimum relevance score (0-100)
            days_back: Only show articles from last N days
            limit: Maximum number of results
        
        Returns:
            List of matching articles
        """
        start_date = None
        if days_back:
            start_date = datetime.now() - timedelta(days=days_back)
        
        results = await self.db.search_articles(
            query=query,
            sources=sources,
            topics=topics,
            min_relevance=min_relevance,
            start_date=start_date,
            limit=limit
        )
        
        self.logger.info(f"Search returned {len(results)} results")
        return results
    
    async def search_by_keyword(self, keyword: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search articles by a specific keyword."""
        return await self.search(query=keyword, limit=limit)
    
    async def get_latest_by_topic(self, topic: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get latest articles for a specific topic."""
        return await self.db.get_articles_by_topic(topic, limit=limit)
    
    async def get_top_articles(self, hours: int = 24, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top-rated articles from the last N hours."""
        return await self.db.get_top_articles(hours=hours, limit=limit)
    
    async def get_trending_topics(self, days: int = 7) -> Dict[str, int]:
        """Get trending topics in the last N days."""
        return await self.db.get_trending_topics(days=days)
    
    async def find_related_articles(self, article_title: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Find articles related to a given article."""
        return await self.db.find_similar_articles(article_title)
    
    async def advanced_search(
        self,
        keywords: Optional[List[str]] = None,
        exclude_keywords: Optional[List[str]] = None,
        sources: Optional[List[str]] = None,
        topics: Optional[List[str]] = None,
        min_relevance: float = 0.0,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        sort_by: str = "relevance",  # "relevance", "date", "source"
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Advanced search with multiple filters and sorting options.
        
        Args:
            keywords: List of keywords (all must be present)
            exclude_keywords: List of keywords to exclude
            sources: Filter by sources
            topics: Filter by topics
            min_relevance: Minimum relevance score
            start_date: Filter articles after this date
            end_date: Filter articles before this date
            sort_by: Sort results by "relevance", "date", or "source"
            limit: Maximum results
        
        Returns:
            Filtered and sorted articles
        """
        # Build query from keywords
        query = None
        if keywords:
            query = " AND ".join(keywords)
        
        # Get initial results
        results = await self.db.search_articles(
            query=query,
            sources=sources,
            topics=topics,
            min_relevance=min_relevance,
            start_date=start_date,
            end_date=end_date,
            limit=limit * 2  # Get more to filter
        )
        
        # Apply exclusion filter
        if exclude_keywords:
            filtered_results = []
            for article in results:
                text = f"{article['title']} {article['summary']}".lower()
                if not any(kw.lower() in text for kw in exclude_keywords):
                    filtered_results.append(article)
            results = filtered_results
        
        # Apply custom sorting
        if sort_by == "date":
            results.sort(key=lambda x: x['processed_at'], reverse=True)
        elif sort_by == "source":
            results.sort(key=lambda x: x['source'])
        # Default is already sorted by relevance
        
        return results[:limit]
    
    async def get_source_statistics(self) -> Dict[str, Any]:
        """Get statistics about article sources."""
        stats = await self.db.get_statistics()
        return {
            "total_articles": stats.get("total_articles", 0),
            "articles_by_source": stats.get("articles_by_source", {}),
            "articles_today": stats.get("articles_today", 0),
            "failed_articles": stats.get("failed_articles", 0)
        }
    
    async def get_search_suggestions(self, partial_query: str) -> List[str]:
        """
        Get search suggestions based on partial query.
        Returns list of suggested keywords.
        """
        # Simple implementation: return matching topics and common keywords
        suggestions = []
        
        partial_lower = partial_query.lower()
        
        # Check topics
        from .content_analyzer import AI_TOPIC_KEYWORDS
        for topic in AI_TOPIC_KEYWORDS.keys():
            if partial_lower in topic.lower():
                suggestions.append(topic)
        
        # Check keywords
        for topic_data in AI_TOPIC_KEYWORDS.values():
            for keyword in topic_data["keywords"]:
                if partial_lower in keyword and keyword not in suggestions:
                    suggestions.append(keyword)
                    if len(suggestions) >= 10:
                        break
            if len(suggestions) >= 10:
                break
        
        return suggestions[:10]


class ArticleFilter:
    """Helper class for filtering articles based on various criteria."""
    
    def __init__(self):
        """Initialize article filter."""
        self.analyzer = ContentAnalyzer()
    
    def filter_by_relevance(
        self,
        articles: List[Dict[str, Any]],
        min_score: float
    ) -> List[Dict[str, Any]]:
        """Filter articles by minimum relevance score."""
        return [a for a in articles if a.get('relevance_score', 0) >= min_score]
    
    def filter_by_topics(
        self,
        articles: List[Dict[str, Any]],
        required_topics: List[str]
    ) -> List[Dict[str, Any]]:
        """Filter articles that have at least one of the required topics."""
        filtered = []
        for article in articles:
            article_topics = article.get('topics', [])
            if any(topic in article_topics for topic in required_topics):
                filtered.append(article)
        return filtered
    
    def filter_by_keywords(
        self,
        articles: List[Dict[str, Any]],
        required_keywords: List[str]
    ) -> List[Dict[str, Any]]:
        """Filter articles that contain at least one required keyword."""
        filtered = []
        for article in articles:
            text = f"{article['title']} {article.get('summary', '')}".lower()
            if any(kw.lower() in text for kw in required_keywords):
                filtered.append(article)
        return filtered
    
    def remove_duplicates(
        self,
        articles: List[Dict[str, Any]],
        similarity_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Remove duplicate articles based on title similarity."""
        if not articles:
            return []
        
        unique_articles = [articles[0]]
        
        for article in articles[1:]:
            is_duplicate = False
            for unique_article in unique_articles:
                if self.analyzer.is_duplicate(
                    article['title'],
                    unique_article['title'],
                    similarity_threshold
                ):
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_articles.append(article)
        
        return unique_articles
    
    def rank_by_quality(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Rank articles by quality score combining relevance, recency, and source.
        """
        import time
        
        def calculate_quality_score(article: Dict[str, Any]) -> float:
            # Base score from relevance
            score = article.get('relevance_score', 0)
            
            # Bonus for recency (up to 20 points)
            if article.get('processed_at'):
                try:
                    processed_time = datetime.fromisoformat(article['processed_at'])
                    age_hours = (datetime.now() - processed_time).total_seconds() / 3600
                    # Newer articles get higher bonus
                    recency_bonus = max(0, 20 - (age_hours / 24) * 2)
                    score += recency_bonus
                except:
                    pass
            
            # Bonus for trusted sources
            trusted_sources = ["ArXiv", "OpenAI", "Google AI", "DeepMind"]
            if article.get('source') in trusted_sources:
                score += 10
            
            return score
        
        # Sort by quality score
        ranked = sorted(articles, key=calculate_quality_score, reverse=True)
        return ranked

