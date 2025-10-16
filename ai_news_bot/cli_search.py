#!/usr/bin/env python3
"""
Command-line interface for searching the AI News database.

This tool allows you to search through stored articles using various filters.
"""

import asyncio
import argparse
import sys
from typing import Optional, List

from .config import load_config
from .database import DatabaseManager
from .utils import NewsSearchEngine


async def search_news(
    query: Optional[str] = None,
    sources: Optional[List[str]] = None,
    topics: Optional[List[str]] = None,
    min_relevance: Optional[float] = None,
    days_back: Optional[int] = None,
    limit: int = 10
):
    """Search for news articles."""
    config = load_config()
    db = DatabaseManager(config.database_path)
    
    try:
        await db.initialize()
        search_engine = NewsSearchEngine(db)
        
        print("\n🔍 Searching AI News Database...\n")
        
        results = await search_engine.search(
            query=query,
            sources=sources,
            topics=topics,
            min_relevance=min_relevance,
            days_back=days_back,
            limit=limit
        )
        
        if not results:
            print("No results found.")
            return
        
        print(f"Found {len(results)} article(s):\n")
        print("=" * 80)
        
        for i, article in enumerate(results, 1):
            print(f"\n{i}. {article['title']}")
            print(f"   Source: {article['source']}")
            print(f"   Relevance: {article['relevance_score']:.1f}/100")
            
            if article['topics']:
                topics_str = ', '.join(article['topics'][:3])
                print(f"   Topics: {topics_str}")
            
            if article['keywords']:
                keywords_str = ', '.join(article['keywords'][:5])
                print(f"   Keywords: {keywords_str}")
            
            print(f"   Date: {article['processed_at']}")
            print(f"   URL: {article['url']}")
            
            if article.get('summary'):
                summary = article['summary'][:200] + "..." if len(article['summary']) > 200 else article['summary']
                print(f"   Summary: {summary}")
            
            print("-" * 80)
    
    finally:
        await db.close()


async def get_trending_topics(days: int = 7):
    """Show trending topics."""
    config = load_config()
    db = DatabaseManager(config.database_path)
    
    try:
        await db.initialize()
        search_engine = NewsSearchEngine(db)
        
        print(f"\n📊 Trending Topics (Last {days} days):\n")
        
        topics = await search_engine.get_trending_topics(days=days)
        
        if not topics:
            print("No topics found.")
            return
        
        for i, (topic, count) in enumerate(topics.items(), 1):
            bar = "█" * min(count, 50)
            print(f"{i:2d}. {topic:30s} {bar} ({count})")
    
    finally:
        await db.close()


async def get_top_articles(hours: int = 24, limit: int = 10):
    """Show top articles."""
    config = load_config()
    db = DatabaseManager(config.database_path)
    
    try:
        await db.initialize()
        search_engine = NewsSearchEngine(db)
        
        print(f"\n⭐ Top Articles (Last {hours} hours):\n")
        
        results = await search_engine.get_top_articles(hours=hours, limit=limit)
        
        if not results:
            print("No articles found.")
            return
        
        for i, article in enumerate(results, 1):
            print(f"{i:2d}. [{article['relevance_score']:.1f}] {article['title']}")
            print(f"    {article['source']} - {article['processed_at']}")
            print(f"    {article['url']}\n")
    
    finally:
        await db.close()


async def get_statistics():
    """Show database statistics."""
    config = load_config()
    db = DatabaseManager(config.database_path)
    
    try:
        await db.initialize()
        stats = await db.get_statistics()
        
        print("\n📈 Database Statistics:\n")
        print(f"Total Articles: {stats['total_articles']}")
        print(f"Articles Today: {stats['articles_today']}")
        print(f"Failed Articles: {stats['failed_articles']}")
        
        print("\n📊 Articles by Source:")
        for source, count in stats['articles_by_source'].items():
            bar = "█" * min(count, 50)
            print(f"  {source:20s} {bar} ({count})")
    
    finally:
        await db.close()


async def show_available_topics():
    """Show all available topics."""
    from .utils.content_analyzer import AI_TOPIC_KEYWORDS
    
    print("\n📚 Available Topics for Filtering:\n")
    for i, topic in enumerate(AI_TOPIC_KEYWORDS.keys(), 1):
        print(f"{i:2d}. {topic}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Search AI News Database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Search for articles about GPT
  %(prog)s search --query "GPT"
  
  # Get articles from specific source
  %(prog)s search --source ArXiv
  
  # Filter by topic
  %(prog)s search --topic "Large Language Models"
  
  # Get top articles from last 24 hours
  %(prog)s top
  
  # Show trending topics
  %(prog)s trending
  
  # Show database statistics
  %(prog)s stats
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Search command
    search_parser = subparsers.add_parser('search', help='Search for articles')
    search_parser.add_argument('-q', '--query', help='Search query')
    search_parser.add_argument('-s', '--source', action='append', help='Filter by source')
    search_parser.add_argument('-t', '--topic', action='append', help='Filter by topic')
    search_parser.add_argument('-r', '--min-relevance', type=float, help='Minimum relevance score')
    search_parser.add_argument('-d', '--days', type=int, help='Only show articles from last N days')
    search_parser.add_argument('-l', '--limit', type=int, default=10, help='Maximum results')
    
    # Top articles command
    top_parser = subparsers.add_parser('top', help='Show top articles')
    top_parser.add_argument('--hours', type=int, default=24, help='Time window in hours')
    top_parser.add_argument('-l', '--limit', type=int, default=10, help='Maximum results')
    
    # Trending topics command
    trending_parser = subparsers.add_parser('trending', help='Show trending topics')
    trending_parser.add_argument('-d', '--days', type=int, default=7, help='Time window in days')
    
    # Statistics command
    subparsers.add_parser('stats', help='Show database statistics')
    
    # Show topics command
    subparsers.add_parser('topics', help='Show available topics')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == 'search':
            asyncio.run(search_news(
                query=args.query,
                sources=args.source,
                topics=args.topic,
                min_relevance=args.min_relevance,
                days_back=args.days,
                limit=args.limit
            ))
        elif args.command == 'top':
            asyncio.run(get_top_articles(hours=args.hours, limit=args.limit))
        elif args.command == 'trending':
            asyncio.run(get_trending_topics(days=args.days))
        elif args.command == 'stats':
            asyncio.run(get_statistics())
        elif args.command == 'topics':
            asyncio.run(show_available_topics())
    
    except KeyboardInterrupt:
        print("\n\nSearch cancelled.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

