#!/usr/bin/env python3
"""
Example script demonstrating the enhanced search capabilities.

Run this after collecting some articles to see the search features in action.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ai_news_bot.config import load_config
from ai_news_bot.database import DatabaseManager
from ai_news_bot.utils import NewsSearchEngine, ContentAnalyzer


async def example_1_basic_search():
    """Example 1: Basic keyword search."""
    print("\n" + "="*80)
    print("EXAMPLE 1: Basic Keyword Search")
    print("="*80)
    
    config = load_config()
    db = DatabaseManager(config.database_path)
    await db.initialize()
    
    try:
        search_engine = NewsSearchEngine(db)
        
        # Search for articles about GPT
        results = await search_engine.search_by_keyword("GPT", limit=5)
        
        print(f"\nFound {len(results)} articles about 'GPT':\n")
        for i, article in enumerate(results, 1):
            print(f"{i}. {article['title']}")
            print(f"   Relevance: {article['relevance_score']:.1f}/100")
            print(f"   Source: {article['source']}")
            print()
    
    finally:
        await db.close()


async def example_2_topic_filtering():
    """Example 2: Filter by AI topic."""
    print("\n" + "="*80)
    print("EXAMPLE 2: Filter by Topic")
    print("="*80)
    
    config = load_config()
    db = DatabaseManager(config.database_path)
    await db.initialize()
    
    try:
        search_engine = NewsSearchEngine(db)
        
        # Get articles about Computer Vision
        results = await search_engine.get_latest_by_topic(
            "Computer Vision",
            limit=5
        )
        
        print(f"\nLatest Computer Vision articles:\n")
        for i, article in enumerate(results, 1):
            print(f"{i}. {article['title']}")
            print(f"   Topics: {', '.join(article['topics'][:3])}")
            print(f"   Relevance: {article['relevance_score']:.1f}/100")
            print()
    
    finally:
        await db.close()


async def example_3_advanced_search():
    """Example 3: Advanced search with multiple filters."""
    print("\n" + "="*80)
    print("EXAMPLE 3: Advanced Search")
    print("="*80)
    
    config = load_config()
    db = DatabaseManager(config.database_path)
    await db.initialize()
    
    try:
        search_engine = NewsSearchEngine(db)
        
        # Complex search: LLM research papers with high relevance
        results = await search_engine.advanced_search(
            keywords=["language model", "transformer"],
            sources=["ArXiv"],
            topics=["Large Language Models"],
            min_relevance=70.0,
            sort_by="relevance",
            limit=5
        )
        
        print(f"\nHigh-quality LLM research papers:\n")
        for i, article in enumerate(results, 1):
            print(f"{i}. {article['title']}")
            print(f"   Relevance: {article['relevance_score']:.1f}/100")
            keywords = ', '.join(article['keywords'][:5])
            print(f"   Keywords: {keywords}")
            print(f"   URL: {article['url']}")
            print()
    
    finally:
        await db.close()


async def example_4_trending_topics():
    """Example 4: Show trending topics."""
    print("\n" + "="*80)
    print("EXAMPLE 4: Trending Topics")
    print("="*80)
    
    config = load_config()
    db = DatabaseManager(config.database_path)
    await db.initialize()
    
    try:
        search_engine = NewsSearchEngine(db)
        
        # Get trending topics from last 7 days
        topics = await search_engine.get_trending_topics(days=7)
        
        print(f"\nTrending AI topics (last 7 days):\n")
        for i, (topic, count) in enumerate(list(topics.items())[:10], 1):
            bar = "█" * min(count, 40)
            print(f"{i:2d}. {topic:30s} {bar} ({count})")
    
    finally:
        await db.close()


async def example_5_top_articles():
    """Example 5: Get top-rated articles."""
    print("\n" + "="*80)
    print("EXAMPLE 5: Top Articles")
    print("="*80)
    
    config = load_config()
    db = DatabaseManager(config.database_path)
    await db.initialize()
    
    try:
        search_engine = NewsSearchEngine(db)
        
        # Get top articles from last 24 hours
        results = await search_engine.get_top_articles(hours=24, limit=5)
        
        print(f"\nTop articles (last 24 hours):\n")
        for i, article in enumerate(results, 1):
            print(f"{i}. {article['title']}")
            print(f"   Relevance: {article['relevance_score']:.1f}/100")
            print(f"   Source: {article['source']}")
            print(f"   Topics: {', '.join(article['topics'][:3])}")
            print()
    
    finally:
        await db.close()


async def example_6_content_analysis():
    """Example 6: Analyze article content."""
    print("\n" + "="*80)
    print("EXAMPLE 6: Content Analysis")
    print("="*80)
    
    analyzer = ContentAnalyzer()
    
    # Sample article
    title = "GPT-4 Achieves Breakthrough Performance in Language Understanding"
    content = """
    OpenAI has announced GPT-4, their latest large language model that demonstrates
    remarkable capabilities in natural language understanding and generation. The model
    shows significant improvements over previous versions in reasoning, coding, and
    multi-modal tasks. Researchers used reinforcement learning from human feedback (RLHF)
    to fine-tune the model's behavior. The new architecture incorporates advanced
    attention mechanisms and achieves state-of-the-art results on multiple benchmarks.
    """
    
    # Analyze the article
    result = analyzer.analyze_article(title, content)
    
    print("\nAnalyzing sample article:")
    print(f"Title: {title}\n")
    print(f"Relevance Score: {result['relevance_score']:.1f}/100")
    print(f"Is AI Related: {result['is_ai_related']}")
    print(f"Topics: {', '.join(result['topics'])}")
    print(f"Keywords: {', '.join(result['keywords'][:10])}")


async def example_7_statistics():
    """Example 7: Database statistics."""
    print("\n" + "="*80)
    print("EXAMPLE 7: Database Statistics")
    print("="*80)
    
    config = load_config()
    db = DatabaseManager(config.database_path)
    await db.initialize()
    
    try:
        stats = await db.get_statistics()
        
        print(f"\nDatabase Statistics:\n")
        print(f"Total Articles: {stats['total_articles']}")
        print(f"Articles Today: {stats['articles_today']}")
        print(f"Failed Articles: {stats['failed_articles']}")
        
        print(f"\nArticles by Source:")
        for source, count in stats['articles_by_source'].items():
            print(f"  {source:30s}: {count}")
    
    finally:
        await db.close()


async def main():
    """Run all examples."""
    print("\n" + "="*80)
    print("NEWS SEARCH IMPROVEMENTS - EXAMPLES")
    print("="*80)
    print("\nThese examples demonstrate the new search capabilities.")
    print("Make sure you have some articles in the database first!")
    
    examples = [
        ("Basic Search", example_1_basic_search),
        ("Topic Filtering", example_2_topic_filtering),
        ("Advanced Search", example_3_advanced_search),
        ("Trending Topics", example_4_trending_topics),
        ("Top Articles", example_5_top_articles),
        ("Content Analysis", example_6_content_analysis),
        ("Statistics", example_7_statistics),
    ]
    
    for i, (name, example_func) in enumerate(examples, 1):
        try:
            await example_func()
            
            if i < len(examples):
                input("\nPress Enter to continue to next example...")
        
        except Exception as e:
            print(f"\n❌ Error in {name}: {e}")
            print("This might be because you don't have articles in the database yet.")
            print("Run the main application first to collect some articles.\n")
    
    print("\n" + "="*80)
    print("Examples completed!")
    print("="*80)
    print("\nTo use these features in your own code:")
    print("1. Import: from ai_news_bot.utils import NewsSearchEngine")
    print("2. Initialize: search_engine = NewsSearchEngine(db_manager)")
    print("3. Search: results = await search_engine.search(...)")
    print("\nFor CLI usage: python -m ai_news_bot.cli_search --help")
    print()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nExamples cancelled.")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)

