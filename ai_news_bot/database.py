"""
Database management for AI News Aggregator Bot.

This module handles SQLite database operations for storing processed articles
and maintaining state across application restarts.
"""

import aiosqlite
import asyncio
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
                processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Index on URL for fast lookups
        await self.db.execute("""
            CREATE INDEX IF NOT EXISTS idx_articles_url ON articles(url)
        """)
        
        # Index on source and processed_at for analytics
        await self.db.execute("""
            CREATE INDEX IF NOT EXISTS idx_articles_source_date 
            ON articles(source, processed_at)
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
        original_content: Optional[str] = None
    ) -> None:
        """Save a processed article to the database."""
        if not self.db:
            raise RuntimeError("Database not initialized")
        
        try:
            await self.db.execute("""
                INSERT OR REPLACE INTO articles 
                (url, title, source, summary, original_content, processed_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (url, title, source, summary, original_content))
            
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
    
    async def close(self) -> None:
        """Close the database connection."""
        if self.db:
            await self.db.close()
            self.db = None
            logger.info("Database connection closed")