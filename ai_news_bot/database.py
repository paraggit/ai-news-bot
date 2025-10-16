"""
Database management for AI News Aggregator Bot.

This module handles SQLite database operations for storing processed articles
and maintaining state across application restarts.
"""

import aiosqlite
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages SQLite database operations for the news aggregator."""
    
    def __init__(self, database_path: str) -> None:
        """Initialize database manager with given database path."""
        self.database_path = database_path
        self.db: Optional[aiosqlite.Connection] = None
        
    async def initialize(self) -> None:
        """Initialize the database and create tables if they don't exist."""
        # Ensure directory exists
        Path(self.database_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Connect to database
        self.db = await aiosqlite.connect(self.database_path)
        
        # Enable WAL mode for better concurrency
        await self.db.execute("PRAGMA journal_mode=WAL")
        
        # Create tables
        await self._create_tables()
        
        logger.info(f"Database initialized at {self.database_path}")
    
    async def _create_tables(self) -> None:
        """Create necessary database tables."""
        
        # Articles table to track processed articles
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                source TEXT NOT NULL,
                summary TEXT,
                original_content TEXT,
                topics TEXT,
                keywords TEXT,
                relevance_score REAL DEFAULT 0.0,
                processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Migrate existing database - add new columns if they don't exist
        await self._migrate_schema()
        
        # Index on URL for fast lookups
        await self.db.execute("""
            CREATE INDEX IF NOT EXISTS idx_articles_url ON articles(url)
        """)
        
        # Index on source and processed_at for analytics
        await self.db.execute("""
            CREATE INDEX IF NOT EXISTS idx_articles_source_date 
            ON articles(source, processed_at)
        """)
        
        # Index on topics for filtering
        await self.db.execute("""
            CREATE INDEX IF NOT EXISTS idx_articles_topics ON articles(topics)
        """)
        
        # Index on relevance score
        await self.db.execute("""
            CREATE INDEX IF NOT EXISTS idx_articles_relevance ON articles(relevance_score DESC)
        """)
        
        # Create full-text search virtual table
        await self.db.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS articles_fts USING fts5(
                title, summary, original_content, keywords,
                content='articles',
                content_rowid='id'
            )
        """)
        
        # Create triggers to keep FTS table in sync
        await self.db.execute("""
            CREATE TRIGGER IF NOT EXISTS articles_ai AFTER INSERT ON articles BEGIN
                INSERT INTO articles_fts(rowid, title, summary, original_content, keywords)
                VALUES (new.id, new.title, new.summary, new.original_content, new.keywords);
            END
        """)
        
        await self.db.execute("""
            CREATE TRIGGER IF NOT EXISTS articles_ad AFTER DELETE ON articles BEGIN
                DELETE FROM articles_fts WHERE rowid = old.id;
            END
        """)
        
        await self.db.execute("""
            CREATE TRIGGER IF NOT EXISTS articles_au AFTER UPDATE ON articles BEGIN
                UPDATE articles_fts SET 
                    title = new.title,
                    summary = new.summary,
                    original_content = new.original_content,
                    keywords = new.keywords
                WHERE rowid = new.id;
            END
        """)
        
        # Failed articles table to track processing failures
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS failed_articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                title TEXT,
                source TEXT NOT NULL,
                error_message TEXT,
                retry_count INTEGER DEFAULT 0,
                last_attempt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Application state table for storing configuration and state
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS app_state (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await self.db.commit()
    
    async def _migrate_schema(self) -> None:
        """Migrate existing database schema to add new columns if needed."""
        try:
            # Check if topics column exists
            cursor = await self.db.execute("PRAGMA table_info(articles)")
            columns = await cursor.fetchall()
            await cursor.close()
            
            column_names = [col[1] for col in columns]
            
            # Add missing columns
            if 'topics' not in column_names:
                logger.info("Migrating database: adding 'topics' column")
                await self.db.execute("ALTER TABLE articles ADD COLUMN topics TEXT")
            
            if 'keywords' not in column_names:
                logger.info("Migrating database: adding 'keywords' column")
                await self.db.execute("ALTER TABLE articles ADD COLUMN keywords TEXT")
            
            if 'relevance_score' not in column_names:
                logger.info("Migrating database: adding 'relevance_score' column")
                await self.db.execute(
                    "ALTER TABLE articles ADD COLUMN relevance_score REAL DEFAULT 0.0"
                )
            
            await self.db.commit()
            logger.info("Database schema migration completed")
            
        except Exception as e:
            logger.error(f"Error during schema migration: {e}")
            # Don't fail if migration has issues - columns might already exist
    
    async def article_exists(self, url: str) -> bool:
        """Check if an article URL has already been processed."""
        if not self.db:
            raise RuntimeError("Database not initialized")
        
        cursor = await self.db.execute(
            "SELECT 1 FROM articles WHERE url = ? LIMIT 1",
            (url,)
        )
        result = await cursor.fetchone()
        await cursor.close()
        
        return result is not None
    
    async def save_article(
        self, 
        url: str, 
        title: str, 
        source: str, 
        summary: str,
        original_content: Optional[str] = None,
        topics: Optional[str] = None,
        keywords: Optional[str] = None,
        relevance_score: float = 0.0
    ) -> None:
        """Save a processed article to the database."""
        if not self.db:
            raise RuntimeError("Database not initialized")
        
        try:
            await self.db.execute("""
                INSERT OR REPLACE INTO articles 
                (url, title, source, summary, original_content, topics, keywords, 
                 relevance_score, processed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (url, title, source, summary, original_content, topics, keywords, relevance_score))
            
            await self.db.commit()
            logger.debug(f"Saved article: {title}")
            
        except Exception as e:
            logger.error(f"Error saving article {url}: {e}")
            raise
    
    async def save_failed_article(
        self, 
        url: str, 
        title: Optional[str], 
        source: str, 
        error_message: str
    ) -> None:
        """Save information about a failed article processing attempt."""
        if not self.db:
            raise RuntimeError("Database not initialized")
        
        try:
            # Check if this URL already exists in failed articles
            cursor = await self.db.execute(
                "SELECT retry_count FROM failed_articles WHERE url = ?",
                (url,)
            )
            result = await cursor.fetchone()
            await cursor.close()
            
            if result:
                # Update existing record
                retry_count = result[0] + 1
                await self.db.execute("""
                    UPDATE failed_articles 
                    SET error_message = ?, retry_count = ?, last_attempt = CURRENT_TIMESTAMP
                    WHERE url = ?
                """, (error_message, retry_count, url))
            else:
                # Insert new record
                await self.db.execute("""
                    INSERT INTO failed_articles 
                    (url, title, source, error_message, retry_count, last_attempt)
                    VALUES (?, ?, ?, ?, 1, CURRENT_TIMESTAMP)
                """, (url, title, source, error_message))
            
            await self.db.commit()
            logger.debug(f"Saved failed article: {url}")
            
        except Exception as e:
            logger.error(f"Error saving failed article {url}: {e}")
            raise
    
    async def get_recent_articles(self, hours: int = 24, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recently processed articles."""
        if not self.db:
            raise RuntimeError("Database not initialized")
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        cursor = await self.db.execute("""
            SELECT url, title, source, summary, processed_at
            FROM articles
            WHERE processed_at > ?
            ORDER BY processed_at DESC
            LIMIT ?
        """, (cutoff_time, limit))
        
        results = await cursor.fetchall()
        await cursor.close()
        
        return [
            {
                "url": row[0],
                "title": row[1], 
                "source": row[2],
                "summary": row[3],
                "processed_at": row[4]
            }
            for row in results
        ]
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics."""
        if not self.db:
            raise RuntimeError("Database not initialized")
        
        stats = {}
        
        # Total articles processed
        cursor = await self.db.execute("SELECT COUNT(*) FROM articles")
        result = await cursor.fetchone()
        stats["total_articles"] = result[0] if result else 0
        await cursor.close()
        
        # Articles by source
        cursor = await self.db.execute("""
            SELECT source, COUNT(*) as count
            FROM articles
            GROUP BY source
            ORDER BY count DESC
        """)
        results = await cursor.fetchall()
        stats["articles_by_source"] = {row[0]: row[1] for row in results}
        await cursor.close()
        
        # Articles processed today
        today = datetime.now().strftime("%Y-%m-%d")
        cursor = await self.db.execute("""
            SELECT COUNT(*) FROM articles
            WHERE DATE(processed_at) = ?
        """, (today,))
        result = await cursor.fetchone()
        stats["articles_today"] = result[0] if result else 0
        await cursor.close()
        
        # Failed articles count
        cursor = await self.db.execute("SELECT COUNT(*) FROM failed_articles")
        result = await cursor.fetchone()
        stats["failed_articles"] = result[0] if result else 0
        await cursor.close()
        
        return stats
    
    async def cleanup_old_data(self, days: int = 30) -> None:
        """Clean up old data from the database."""
        if not self.db:
            raise RuntimeError("Database not initialized")
        
        cutoff_time = datetime.now() - timedelta(days=days)
        
        # Delete old articles
        cursor = await self.db.execute("""
            DELETE FROM articles
            WHERE processed_at < ?
        """, (cutoff_time,))
        
        deleted_articles = cursor.rowcount
        await cursor.close()
        
        # Delete old failed articles
        cursor = await self.db.execute("""
            DELETE FROM failed_articles
            WHERE created_at < ?
        """, (cutoff_time,))
        
        deleted_failed = cursor.rowcount
        await cursor.close()
        
        await self.db.commit()
        
        logger.info(f"Cleaned up {deleted_articles} old articles and {deleted_failed} failed articles")
    
    async def set_app_state(self, key: str, value: str) -> None:
        """Set application state value."""
        if not self.db:
            raise RuntimeError("Database not initialized")
        
        await self.db.execute("""
            INSERT OR REPLACE INTO app_state (key, value, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        """, (key, value))
        
        await self.db.commit()
    
    async def get_app_state(self, key: str) -> Optional[str]:
        """Get application state value."""
        if not self.db:
            raise RuntimeError("Database not initialized")
        
        cursor = await self.db.execute(
            "SELECT value FROM app_state WHERE key = ?",
            (key,)
        )
        result = await cursor.fetchone()
        await cursor.close()
        
        return result[0] if result else None
    
    async def search_articles(
        self,
        query: Optional[str] = None,
        sources: Optional[List[str]] = None,
        topics: Optional[List[str]] = None,
        min_relevance: Optional[float] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Search articles with advanced filtering.
        
        Args:
            query: Full-text search query
            sources: Filter by source names
            topics: Filter by topics
            min_relevance: Minimum relevance score
            start_date: Filter articles after this date
            end_date: Filter articles before this date
            limit: Maximum number of results
            offset: Offset for pagination
        
        Returns:
            List of articles matching the search criteria
        """
        if not self.db:
            raise RuntimeError("Database not initialized")
        
        # Build the query dynamically
        if query:
            # Use full-text search
            sql = """
                SELECT a.id, a.url, a.title, a.source, a.summary, a.topics, 
                       a.keywords, a.relevance_score, a.processed_at,
                       articles_fts.rank as search_rank
                FROM articles a
                INNER JOIN articles_fts ON articles_fts.rowid = a.id
                WHERE articles_fts MATCH ?
            """
            params = [query]
        else:
            # Regular search without full-text
            sql = """
                SELECT id, url, title, source, summary, topics, keywords,
                       relevance_score, processed_at, 0 as search_rank
                FROM articles
                WHERE 1=1
            """
            params = []
        
        # Add filters
        if sources:
            placeholders = ','.join('?' * len(sources))
            sql += f" AND source IN ({placeholders})"
            params.extend(sources)
        
        if topics:
            # Search for any of the topics in the topics field
            topic_conditions = " OR ".join(["topics LIKE ?" for _ in topics])
            sql += f" AND ({topic_conditions})"
            params.extend([f"%{topic}%" for topic in topics])
        
        if min_relevance is not None:
            sql += " AND relevance_score >= ?"
            params.append(min_relevance)
        
        if start_date:
            sql += " AND processed_at >= ?"
            params.append(start_date)
        
        if end_date:
            sql += " AND processed_at <= ?"
            params.append(end_date)
        
        # Order by relevance and search rank
        if query:
            sql += " ORDER BY search_rank, relevance_score DESC, processed_at DESC"
        else:
            sql += " ORDER BY relevance_score DESC, processed_at DESC"
        
        # Add pagination
        sql += " LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor = await self.db.execute(sql, params)
        results = await cursor.fetchall()
        await cursor.close()
        
        articles = []
        for row in results:
            articles.append({
                "id": row[0],
                "url": row[1],
                "title": row[2],
                "source": row[3],
                "summary": row[4],
                "topics": row[5].split(',') if row[5] else [],
                "keywords": row[6].split(',') if row[6] else [],
                "relevance_score": row[7],
                "processed_at": row[8],
                "search_rank": row[9] if query else None
            })
        
        return articles
    
    async def get_articles_by_topic(self, topic: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get articles filtered by a specific topic."""
        return await self.search_articles(topics=[topic], limit=limit)
    
    async def get_top_articles(self, hours: int = 24, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top articles by relevance score in the last N hours."""
        start_date = datetime.now() - timedelta(hours=hours)
        return await self.search_articles(
            start_date=start_date,
            limit=limit
        )
    
    async def find_similar_articles(self, title: str, threshold: float = 0.7) -> List[Dict[str, Any]]:
        """
        Find articles with similar titles using simple string matching.
        For better similarity, consider using sentence transformers.
        """
        if not self.db:
            raise RuntimeError("Database not initialized")
        
        # Simple approach: search for articles with similar keywords
        # Extract significant words from title
        import re
        words = re.findall(r'\w+', title.lower())
        significant_words = [w for w in words if len(w) > 4][:5]  # Use longest words
        
        if not significant_words:
            return []
        
        # Use full-text search to find similar articles
        query = " OR ".join(significant_words)
        return await self.search_articles(query=query, limit=10)
    
    async def get_trending_topics(self, days: int = 7) -> Dict[str, int]:
        """Get trending topics in the last N days."""
        if not self.db:
            raise RuntimeError("Database not initialized")
        
        start_date = datetime.now() - timedelta(days=days)
        
        cursor = await self.db.execute("""
            SELECT topics FROM articles
            WHERE processed_at >= ? AND topics IS NOT NULL
        """, (start_date,))
        
        results = await cursor.fetchall()
        await cursor.close()
        
        # Count topic occurrences
        topic_counts = {}
        for row in results:
            if row[0]:
                topics = row[0].split(',')
                for topic in topics:
                    topic = topic.strip()
                    if topic:
                        topic_counts[topic] = topic_counts.get(topic, 0) + 1
        
        # Sort by count
        sorted_topics = dict(sorted(topic_counts.items(), key=lambda x: x[1], reverse=True))
        return sorted_topics
    
    async def close(self) -> None:
        """Close the database connection."""
        if self.db:
            await self.db.close()
            self.db = None
            logger.info("Database connection closed")