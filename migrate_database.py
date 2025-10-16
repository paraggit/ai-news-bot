#!/usr/bin/env python3
"""
Database Migration Script

Safely migrates existing database to new schema with topics, keywords, and relevance_score.
Run this before starting the updated application.
"""

import asyncio
import sqlite3
import sys
from pathlib import Path

# Default database path
DEFAULT_DB_PATH = "data/news_aggregator.db"


def check_column_exists(db_path: str, table: str, column: str) -> bool:
    """Check if a column exists in a table."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [row[1] for row in cursor.fetchall()]
        return column in columns
    finally:
        conn.close()


def migrate_database(db_path: str):
    """Migrate database to new schema."""
    print(f"🔄 Migrating database: {db_path}")
    
    if not Path(db_path).exists():
        print(f"✅ Database doesn't exist yet - will be created with new schema")
        return True
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check and add missing columns
        columns_to_add = [
            ("topics", "TEXT"),
            ("keywords", "TEXT"),
            ("relevance_score", "REAL DEFAULT 0.0")
        ]
        
        added_columns = []
        for column_name, column_type in columns_to_add:
            if not check_column_exists(db_path, "articles", column_name):
                print(f"  Adding column: {column_name}")
                cursor.execute(f"ALTER TABLE articles ADD COLUMN {column_name} {column_type}")
                added_columns.append(column_name)
            else:
                print(f"  ✓ Column exists: {column_name}")
        
        if added_columns:
            conn.commit()
            print(f"✅ Added {len(added_columns)} new column(s)")
        else:
            print("✅ All columns already exist")
        
        # Create FTS5 table if it doesn't exist
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='articles_fts'
        """)
        
        if not cursor.fetchone():
            print("  Creating full-text search table...")
            cursor.execute("""
                CREATE VIRTUAL TABLE articles_fts USING fts5(
                    title, summary, original_content, keywords,
                    content='articles',
                    content_rowid='id'
                )
            """)
            
            # Populate FTS table from existing articles
            print("  Populating full-text search index...")
            cursor.execute("""
                INSERT INTO articles_fts(rowid, title, summary, original_content, keywords)
                SELECT id, title, summary, original_content, keywords FROM articles
            """)
            
            conn.commit()
            print("✅ Full-text search table created and populated")
        else:
            print("✅ Full-text search table already exists")
        
        # Create or replace triggers
        print("  Setting up triggers...")
        
        # Drop existing triggers if they exist
        cursor.execute("DROP TRIGGER IF EXISTS articles_ai")
        cursor.execute("DROP TRIGGER IF EXISTS articles_ad")
        cursor.execute("DROP TRIGGER IF EXISTS articles_au")
        
        # Create new triggers
        cursor.execute("""
            CREATE TRIGGER articles_ai AFTER INSERT ON articles BEGIN
                INSERT INTO articles_fts(rowid, title, summary, original_content, keywords)
                VALUES (new.id, new.title, new.summary, new.original_content, new.keywords);
            END
        """)
        
        cursor.execute("""
            CREATE TRIGGER articles_ad AFTER DELETE ON articles BEGIN
                DELETE FROM articles_fts WHERE rowid = old.id;
            END
        """)
        
        cursor.execute("""
            CREATE TRIGGER articles_au AFTER UPDATE ON articles BEGIN
                UPDATE articles_fts SET 
                    title = new.title,
                    summary = new.summary,
                    original_content = new.original_content,
                    keywords = new.keywords
                WHERE rowid = new.id;
            END
        """)
        
        conn.commit()
        print("✅ Triggers created")
        
        # Create indexes if they don't exist
        print("  Creating indexes...")
        
        indexes = [
            ("idx_articles_topics", "CREATE INDEX IF NOT EXISTS idx_articles_topics ON articles(topics)"),
            ("idx_articles_relevance", "CREATE INDEX IF NOT EXISTS idx_articles_relevance ON articles(relevance_score DESC)")
        ]
        
        for idx_name, idx_sql in indexes:
            cursor.execute(idx_sql)
            print(f"  ✓ Index: {idx_name}")
        
        conn.commit()
        print("✅ Indexes created")
        
        # Get statistics
        cursor.execute("SELECT COUNT(*) FROM articles")
        article_count = cursor.fetchone()[0]
        
        print(f"\n📊 Database Statistics:")
        print(f"   Total articles: {article_count}")
        
        if article_count > 0:
            cursor.execute("SELECT COUNT(*) FROM articles WHERE topics IS NOT NULL")
            with_topics = cursor.fetchone()[0]
            print(f"   With topics: {with_topics}")
            print(f"   Without topics: {article_count - with_topics}")
            print(f"\n💡 Tip: Existing articles will be enriched with metadata on next fetch")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()


def main():
    """Main migration function."""
    print("=" * 60)
    print("🔄 AI News Aggregator - Database Migration")
    print("=" * 60)
    print()
    
    # Get database path from command line or use default
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    else:
        db_path = DEFAULT_DB_PATH
    
    print(f"Database: {db_path}")
    print()
    
    # Run migration
    success = migrate_database(db_path)
    
    print()
    print("=" * 60)
    if success:
        print("✅ Migration completed successfully!")
        print()
        print("You can now start the application:")
        print("  python -m ai_news_bot.main")
    else:
        print("❌ Migration failed!")
        print()
        print("Please check the error messages above and try again.")
        sys.exit(1)
    print("=" * 60)


if __name__ == "__main__":
    main()

