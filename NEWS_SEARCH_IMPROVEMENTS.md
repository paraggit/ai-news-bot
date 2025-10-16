# News Search Improvements Documentation

## Overview

This document describes the comprehensive improvements made to the news search functionality in the AI News Aggregator. The enhancements provide powerful search capabilities, better content filtering, intelligent deduplication, and advanced topic categorization.

## Key Improvements

### 1. Full-Text Search with SQLite FTS5

**File:** `ai_news_bot/database.py`

#### What Changed:
- Added full-text search capabilities using SQLite's FTS5 (Full-Text Search) extension
- New database fields: `topics`, `keywords`, `relevance_score`
- FTS virtual table synchronized with the main articles table using triggers

#### Benefits:
- **Fast Text Search**: Search across titles, summaries, and content efficiently
- **Ranked Results**: Search results are ranked by relevance
- **Flexible Queries**: Support for complex search queries with AND/OR operators
- **Better Performance**: Indexed search is much faster than LIKE queries

#### New Database Methods:
```python
# Search with multiple filters
await db.search_articles(
    query="GPT language models",
    sources=["ArXiv", "OpenAI"],
    topics=["Large Language Models"],
    min_relevance=60.0,
    start_date=datetime.now() - timedelta(days=7),
    limit=20
)

# Get trending topics
await db.get_trending_topics(days=7)

# Find similar articles
await db.find_similar_articles(title="GPT-4 Breakthrough")

# Get top articles by relevance
await db.get_top_articles(hours=24, limit=10)
```

---

### 2. Content Analyzer with AI Relevance Scoring

**File:** `ai_news_bot/utils/content_analyzer.py`

#### What Changed:
- Created a comprehensive content analysis system
- Intelligent AI relevance scoring (0-100 scale)
- Automatic topic categorization across 10 AI categories
- Smart keyword extraction

#### AI Topic Categories:
1. **Large Language Models** - GPT, BERT, LLMs, transformers
2. **Computer Vision** - Image recognition, object detection, CNNs
3. **Natural Language Processing** - NLP, sentiment analysis, text generation
4. **Machine Learning** - Neural networks, deep learning, training
5. **AI Ethics & Safety** - Bias, fairness, alignment, responsible AI
6. **Robotics & Autonomous Systems** - Self-driving, robots, automation
7. **AI Research** - Papers, benchmarks, SOTA results
8. **AI Applications** - Real-world use cases, deployments
9. **AI Companies & Business** - Startups, funding, product launches
10. **Multimodal AI** - Vision-language, text-to-image, cross-modal

#### Relevance Scoring Algorithm:
The analyzer calculates a relevance score based on:
- **Title keywords** (30 points max): Weighted by keyword specificity
- **Content keywords** (30 points max): Based on keyword density
- **Topic matches** (20 points max): Multiple topics increase score
- **High-value keywords** (15 points): "breakthrough", "novel", "SOTA", etc.
- **Prominence bonus** (5 points): AI keywords in title

#### Example Usage:
```python
from ai_news_bot.utils import ContentAnalyzer

analyzer = ContentAnalyzer()
result = analyzer.analyze_article(
    title="GPT-4 Achieves State-of-the-Art Results",
    content="OpenAI's latest large language model..."
)

print(result)
# {
#     'relevance_score': 85.3,
#     'topics': ['Large Language Models', 'AI Research'],
#     'keywords': ['gpt', 'language model', 'breakthrough', 'openai'],
#     'is_ai_related': True
# }
```

---

### 3. Advanced Search Engine

**File:** `ai_news_bot/utils/search.py`

#### What Changed:
- High-level search interface (`NewsSearchEngine`)
- Article filtering utilities (`ArticleFilter`)
- Support for complex queries with multiple criteria

#### Features:

**NewsSearchEngine Methods:**
```python
search_engine = NewsSearchEngine(db_manager)

# Simple keyword search
results = await search_engine.search_by_keyword("transformer", limit=20)

# Latest by topic
results = await search_engine.get_latest_by_topic("Computer Vision", limit=10)

# Top articles
results = await search_engine.get_top_articles(hours=24, limit=10)

# Trending topics
topics = await search_engine.get_trending_topics(days=7)

# Advanced search
results = await search_engine.advanced_search(
    keywords=["GPT", "language model"],
    exclude_keywords=["tutorial", "beginner"],
    sources=["ArXiv"],
    topics=["Large Language Models"],
    min_relevance=70.0,
    start_date=datetime.now() - timedelta(days=7),
    sort_by="relevance",
    limit=50
)
```

**ArticleFilter Features:**
- Remove duplicates based on title similarity
- Filter by relevance threshold
- Filter by topics and keywords
- Quality-based ranking (combines relevance, recency, source reputation)

---

### 4. Intelligent Deduplication

**Improvements in:** `ai_news_bot/main.py` and `ai_news_bot/utils/content_analyzer.py`

#### What Changed:
- Jaccard similarity calculation for comparing articles
- Automatic duplicate detection before processing
- Configurable similarity threshold (default: 0.8)

#### How It Works:
1. Extract significant words from titles
2. Remove common stop words
3. Calculate Jaccard similarity coefficient
4. Flag articles exceeding similarity threshold as duplicates

#### Benefits:
- Prevents posting the same news multiple times
- Catches similar stories from different sources
- Reduces noise in the news feed

---

### 5. Enhanced News Sources

**Files:** `ai_news_bot/news_sources/base.py`, `rss_feeds.py`, `arxiv.py`, `web_scraper.py`

#### What Changed:
- All news sources now automatically enrich articles with metadata
- Integration with ContentAnalyzer for relevance scoring
- Better AI-related content filtering
- Article objects include topics, keywords, and relevance scores

#### Article Data Structure:
```python
@dataclass
class Article:
    title: str
    url: str
    content: str
    source: str
    published_date: Optional[datetime] = None
    author: Optional[str] = None
    summary: Optional[str] = None
    tags: Optional[List[str]] = None
    # New enhanced fields
    topics: Optional[List[str]] = None  # AI topic categories
    keywords: Optional[List[str]] = None  # Extracted keywords
    relevance_score: float = 0.0  # 0-100 relevance score
```

---

### 6. Command-Line Search Tool

**File:** `ai_news_bot/cli_search.py`

#### What Changed:
- New CLI tool for searching the news database
- Multiple search commands
- Beautiful formatted output

#### Available Commands:

**Search Articles:**
```bash
# Search by keyword
python -m ai_news_bot.cli_search search --query "GPT-4"

# Filter by source
python -m ai_news_bot.cli_search search --source ArXiv

# Filter by topic
python -m ai_news_bot.cli_search search --topic "Large Language Models"

# Combined filters
python -m ai_news_bot.cli_search search \
  --query "transformer" \
  --source ArXiv \
  --min-relevance 70 \
  --days 7 \
  --limit 10
```

**Show Top Articles:**
```bash
# Top articles from last 24 hours
python -m ai_news_bot.cli_search top

# Top articles from last week
python -m ai_news_bot.cli_search top --hours 168 --limit 20
```

**Trending Topics:**
```bash
# Show trending topics from last 7 days
python -m ai_news_bot.cli_search trending

# Custom time window
python -m ai_news_bot.cli_search trending --days 30
```

**Database Statistics:**
```bash
# Show database statistics
python -m ai_news_bot.cli_search stats
```

**Available Topics:**
```bash
# List all available topics for filtering
python -m ai_news_bot.cli_search topics
```

---

## Performance Improvements

### Database Indexing
- Index on `topics` for fast topic filtering
- Index on `relevance_score` for quick ranking
- Full-text index for fast content search
- Compound index on `(source, processed_at)` for analytics

### Query Optimization
- Pagination support to handle large result sets
- Efficient duplicate detection algorithm
- Lazy loading of article content
- Prepared statements for repeated queries

---

## Migration Guide

### Database Migration

The new database schema is backward compatible. When you restart the application, it will automatically:

1. Add new columns: `topics`, `keywords`, `relevance_score`
2. Create the FTS5 virtual table
3. Set up triggers for automatic synchronization
4. Create new indexes

**No manual migration needed!** Existing articles will have NULL values for new fields until they're reprocessed.

### Code Migration

If you have custom code using the old database methods:

**Old:**
```python
# Simple article retrieval
articles = await db.get_recent_articles(hours=24)
```

**New (Backward Compatible):**
```python
# Still works!
articles = await db.get_recent_articles(hours=24)

# But you can now use enhanced search:
articles = await db.search_articles(
    min_relevance=60.0,
    start_date=datetime.now() - timedelta(hours=24),
    limit=50
)
```

---

## Usage Examples

### Example 1: Find Latest LLM Papers

```python
from ai_news_bot.database import DatabaseManager
from ai_news_bot.utils import NewsSearchEngine

# Initialize
db = DatabaseManager("data/news_aggregator.db")
await db.initialize()
search_engine = NewsSearchEngine(db)

# Search for LLM papers from ArXiv
results = await search_engine.search(
    query="large language model",
    sources=["ArXiv"],
    topics=["Large Language Models"],
    min_relevance=70.0,
    days_back=7,
    limit=10
)

# Display results
for article in results:
    print(f"{article['title']} ({article['relevance_score']:.1f})")
    print(f"Topics: {', '.join(article['topics'])}")
    print(f"URL: {article['url']}\n")
```

### Example 2: Monitor Trending Topics

```python
# Get trending topics
trending = await search_engine.get_trending_topics(days=7)

# Display top 10 topics
for topic, count in list(trending.items())[:10]:
    print(f"{topic}: {count} articles")
```

### Example 3: Find Similar Articles

```python
# Check if an article is duplicate
similar = await db.find_similar_articles(
    title="GPT-4 Released by OpenAI"
)

for article in similar:
    print(f"Similar: {article['title']}")
    print(f"Similarity score: {article.get('search_rank', 'N/A')}")
```

---

## Configuration

### Environment Variables

No new environment variables required! The improvements work with your existing configuration.

### Optional Tuning

You can adjust these parameters in your code:

```python
# Adjust similarity threshold for deduplication
article_filter = ArticleFilter()
unique = article_filter.remove_duplicates(
    articles,
    similarity_threshold=0.7  # Default: 0.7
)

# Adjust minimum relevance score
MIN_RELEVANCE_SCORE = 60.0  # Only process highly relevant articles
```

---

## Benefits Summary

✅ **Faster Search**: Full-text search is 10-100x faster than LIKE queries
✅ **Better Quality**: Relevance scoring ensures high-quality content
✅ **Smart Filtering**: 10 AI topic categories for precise filtering
✅ **No Duplicates**: Intelligent deduplication prevents redundant posts
✅ **Easy Access**: CLI tool for quick database searches
✅ **Trending Analysis**: Identify hot topics in AI research
✅ **Backward Compatible**: Works with existing code and database
✅ **Well Documented**: Clear examples and usage patterns

---

## Testing the Improvements

### 1. Test Full-Text Search

```bash
# Start the application (it will auto-migrate the database)
python -m ai_news_bot.main

# In another terminal, search the database
python -m ai_news_bot.cli_search search --query "GPT" --limit 5
```

### 2. Test Topic Filtering

```bash
# Show available topics
python -m ai_news_bot.cli_search topics

# Search by topic
python -m ai_news_bot.cli_search search --topic "Computer Vision"
```

### 3. Test Trending Analysis

```bash
# Show trending topics
python -m ai_news_bot.cli_search trending --days 7

# Show top articles
python -m ai_news_bot.cli_search top --hours 24
```

### 4. Test in Python

```python
import asyncio
from ai_news_bot.utils import ContentAnalyzer

async def test():
    analyzer = ContentAnalyzer()
    
    result = analyzer.analyze_article(
        title="GPT-4 Breakthrough in Natural Language Understanding",
        content="OpenAI's latest model demonstrates remarkable capabilities..."
    )
    
    print(f"Relevance Score: {result['relevance_score']}")
    print(f"Topics: {result['topics']}")
    print(f"Keywords: {result['keywords']}")
    print(f"Is AI Related: {result['is_ai_related']}")

asyncio.run(test())
```

---

## Troubleshooting

### Issue: "FTS5 not available"

**Solution:** Ensure you have SQLite 3.9.0+ with FTS5 support:
```bash
python -c "import sqlite3; print(sqlite3.sqlite_version)"
```

If version is too old, upgrade SQLite or rebuild Python with newer SQLite.

### Issue: No results from search

**Solution:** 
1. Ensure articles have been processed first
2. Check if articles have relevance scores (reprocess if needed)
3. Lower the `min_relevance` threshold

### Issue: Slow search performance

**Solution:**
1. Check database size: `ls -lh data/news_aggregator.db`
2. Vacuum the database: Run `VACUUM` to optimize
3. Reduce search limit
4. Use specific filters (source, topic) to narrow results

---

## Future Enhancements

Potential improvements for the future:

1. **Semantic Search**: Use sentence transformers for better similarity
2. **Search History**: Track popular searches and suggestions
3. **Export Features**: Export search results to CSV/JSON
4. **Web Interface**: Build a web UI for searching
5. **Email Digests**: Send digest of top articles by email
6. **RSS Feed**: Provide RSS feed of filtered results
7. **Article Recommendations**: Suggest related articles
8. **Custom Topics**: Allow users to define custom topics

---

## Contributing

If you want to contribute to the search functionality:

1. Test new features thoroughly
2. Add unit tests for new methods
3. Update this documentation
4. Follow the existing code style
5. Ensure backward compatibility

---

## License

Same as the main project.

---

## Support

For issues or questions:
1. Check this documentation
2. Review the code comments
3. Test with the CLI tool
4. Check the logs for errors

Happy searching! 🔍

