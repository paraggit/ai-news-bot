"""
Configuration management for AI News Aggregator Bot.

This module handles loading and validating configuration from environment variables.
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv


@dataclass
class Config:
    """Configuration class for the AI News Aggregator Bot."""
    
    # Telegram Configuration
    telegram_bot_token: str
    telegram_channel_id: str
    
    # Summarizer Configuration
    summarizer_type: str  # 'openai', 'deepseek', or 'local'
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-3.5-turbo"
    deepseek_api_key: Optional[str] = None
    deepseek_base_url: str = "https://api.deepseek.com/v1"
    
    # News Fetching Configuration (increased for expanded sources)
    fetch_interval_minutes: int = 30
    max_articles_per_run: int = 15
    
    # Database Configuration
    database_path: str = "data/news_aggregator.db"
    
    # Logging Configuration
    log_level: str = "INFO"
    log_file: str = "logs/app.log"
    
    # ArXiv Configuration (increased for expanded research coverage)
    arxiv_max_results: int = 10
    arxiv_categories: List[str] = None
    
    # Perplexity Search API Configuration
    perplexity_api_key: Optional[str] = None
    perplexity_model: str = "llama-3.1-sonar-small-128k-online"
    perplexity_max_results: int = 5
    perplexity_search_queries: List[str] = None
    
    # RSS Feed Configuration
    rss_feed_interval: int = 15
    
    # Local Model Configuration
    local_model_name: str = "facebook/bart-large-cnn"
    local_model_device: str = "auto"
    local_model_precision: str = "float16"
    local_model_max_length: int = 1024
    local_model_batch_size: int = 1
    local_model_cache_dir: str = "./models"
    local_model_use_quantization: bool = False
    local_model_load_in_8bit: bool = False
    local_model_load_in_4bit: bool = False
    
    # Anthropic/Claude Configuration
    anthropic_api_key: Optional[str] = None
    anthropic_model: str = "claude-sonnet-4-20250514"

    # Digest Configuration
    digest_enabled: bool = False
    digest_schedule_hour: int = 8
    digest_period_hours: int = 24
    digest_max_articles: int = 15

    # Concurrency Configuration
    max_concurrent_sources: int = 4

    # Network Configuration
    ssl_verify: bool = True
    http_timeout: int = 30
    max_retries: int = 3
    user_agent: str = "AI-News-Aggregator-Bot/1.0"
    
    def __post_init__(self):
        """Post-initialization validation and setup."""
        if self.arxiv_categories is None:
            self.arxiv_categories = [
                "cs.AI",    # Artificial Intelligence
                "cs.LG",    # Machine Learning
                "cs.CL",    # Computation and Language (NLP)
                "cs.CV",    # Computer Vision
                "cs.NE",    # Neural and Evolutionary Computing
                "cs.RO",    # Robotics
                "cs.IR",    # Information Retrieval
                "cs.MA",    # Multiagent Systems
                "cs.HC",    # Human-Computer Interaction (AI interfaces)
                "cs.CR",    # Cryptography & Security (AI safety)
                "cs.SD",    # Sound (speech/audio AI)
                "eess.AS",  # Audio and Speech Processing
                "stat.ML",  # Machine Learning (Statistics)
            ]
        
        if self.perplexity_search_queries is None:
            # Default search queries for latest AI research
            self.perplexity_search_queries = [
                "latest AI research papers and breakthroughs",
                "agentic AI and autonomous agents recent developments",
                "LangChain LangGraph updates and new features",
                "Model Context Protocol MCP AI integration",
                "large language models LLM research advances",
                "AI agents tool use and function calling",
                "retrieval augmented generation RAG systems",
                "multimodal AI vision language models",
            ]
        
        # Validate required fields
        if not self.telegram_bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN is required")
        
        if not self.telegram_channel_id:
            raise ValueError("TELEGRAM_CHANNEL_ID is required")
        
        # Validate summarizer configuration
        if self.summarizer_type == "openai" and not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required when using OpenAI summarizer")

        if self.summarizer_type == "deepseek" and not self.deepseek_api_key:
            raise ValueError("DEEPSEEK_API_KEY is required when using DeepSeek summarizer")

        if self.summarizer_type == "anthropic" and not self.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY is required when using Anthropic summarizer")

        if self.summarizer_type not in ["openai", "deepseek", "local", "anthropic"]:
            raise ValueError("SUMMARIZER_TYPE must be 'openai', 'deepseek', 'local', or 'anthropic'")


def load_config() -> Config:
    """Load configuration from environment variables."""
    
    # Load environment variables from .env file if it exists
    env_path = Path(".env")
    if env_path.exists():
        load_dotenv(env_path)
    
    # Parse ArXiv categories (expanded for better research coverage)
    default_categories = "cs.AI,cs.LG,cs.CL,cs.CV,cs.NE,cs.RO,cs.IR,cs.MA,stat.ML"
    arxiv_categories_str = os.getenv("ARXIV_CATEGORIES", default_categories)
    arxiv_categories = [cat.strip() for cat in arxiv_categories_str.split(",")]
    
    # Parse Perplexity search queries
    perplexity_queries_str = os.getenv("PERPLEXITY_SEARCH_QUERIES", "")
    perplexity_queries = None
    if perplexity_queries_str:
        perplexity_queries = [q.strip() for q in perplexity_queries_str.split("|")]
    
    config = Config(
        # Telegram Configuration
        telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
        telegram_channel_id=os.getenv("TELEGRAM_CHANNEL_ID", ""),
        
        # Summarizer Configuration
        summarizer_type=os.getenv("SUMMARIZER_TYPE", "openai"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
        deepseek_api_key=os.getenv("DEEPSEEK_API_KEY"),
        deepseek_base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
        
        # News Fetching Configuration (increased for expanded sources)
        fetch_interval_minutes=int(os.getenv("FETCH_INTERVAL_MINUTES", "30")),
        max_articles_per_run=int(os.getenv("MAX_ARTICLES_PER_RUN", "15")),
        
        # Database Configuration
        database_path=os.getenv("DATABASE_PATH", "data/news_aggregator.db"),
        
        # Logging Configuration
        log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
        log_file=os.getenv("LOG_FILE", "logs/app.log"),
        
        # ArXiv Configuration (increased for better research coverage)
        arxiv_max_results=int(os.getenv("ARXIV_MAX_RESULTS", "10")),
        arxiv_categories=arxiv_categories,
        
        # Perplexity Search API Configuration
        perplexity_api_key=os.getenv("PERPLEXITY_API_KEY"),
        perplexity_model=os.getenv("PERPLEXITY_MODEL", "llama-3.1-sonar-small-128k-online"),
        perplexity_max_results=int(os.getenv("PERPLEXITY_MAX_RESULTS", "5")),
        perplexity_search_queries=perplexity_queries,
        
        # RSS Feed Configuration
        rss_feed_interval=int(os.getenv("RSS_FEED_INTERVAL", "15")),
        
        # Local Model Configuration
        local_model_name=os.getenv("LOCAL_MODEL_NAME", "facebook/bart-large-cnn"),
        local_model_device=os.getenv("LOCAL_MODEL_DEVICE", "auto"),
        local_model_precision=os.getenv("LOCAL_MODEL_PRECISION", "float16"),
        local_model_max_length=int(os.getenv("LOCAL_MODEL_MAX_LENGTH", "1024")),
        local_model_batch_size=int(os.getenv("LOCAL_MODEL_BATCH_SIZE", "1")),
        local_model_cache_dir=os.getenv("LOCAL_MODEL_CACHE_DIR", "./models"),
        local_model_use_quantization=os.getenv("LOCAL_MODEL_USE_QUANTIZATION", "false").lower() == "true",
        local_model_load_in_8bit=os.getenv("LOCAL_MODEL_LOAD_IN_8BIT", "false").lower() == "true",
        local_model_load_in_4bit=os.getenv("LOCAL_MODEL_LOAD_IN_4BIT", "false").lower() == "true",
        
        # Anthropic/Claude Configuration
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        anthropic_model=os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514"),

        # Digest Configuration
        digest_enabled=os.getenv("DIGEST_ENABLED", "false").lower() == "true",
        digest_schedule_hour=int(os.getenv("DIGEST_SCHEDULE_HOUR", "8")),
        digest_period_hours=int(os.getenv("DIGEST_PERIOD_HOURS", "24")),
        digest_max_articles=int(os.getenv("DIGEST_MAX_ARTICLES", "15")),

        # Concurrency Configuration
        max_concurrent_sources=int(os.getenv("MAX_CONCURRENT_SOURCES", "4")),

        # Network Configuration
        ssl_verify=os.getenv("SSL_VERIFY", "true").lower() == "true",
        http_timeout=int(os.getenv("HTTP_TIMEOUT", "30")),
        max_retries=int(os.getenv("MAX_RETRIES", "3")),
        user_agent=os.getenv("USER_AGENT", "AI-News-Aggregator-Bot/1.0")
    )
    
    return config


# RSS Feed URLs for AI news sources - FOCUSED ON RESEARCH BREAKTHROUGHS
# NOTE: Prioritizing research-focused sources over business/investment news
RSS_FEEDS = {
    # ── Journals & Academic Publishers (HIGHEST PRIORITY) ─────────────
    "Nature Machine Intelligence": "https://www.nature.com/natmachintell.rss",
    "Nature Computational Science": "https://www.nature.com/natcomputsci.rss",
    "Science AI": "https://www.science.org/rss/news_current.xml",
    "IEEE Spectrum AI": "https://spectrum.ieee.org/feeds/feed.rss",
    "ACM TechNews": "https://technews.acm.org/news.rss",
    "JMLR Papers": "https://jmlr.org/jmlr.xml",
    "Distill.pub": "https://distill.pub/rss.xml",
    "Transactions on ML Research": "https://jmlr.org/tmlr/tmlr.xml",

    # ── University & Research Lab Blogs (HIGH PRIORITY) ───────────────
    "Google AI Blog": "https://ai.googleblog.com/feeds/posts/default",
    "Berkeley AI Research": "https://bair.berkeley.edu/blog/feed.xml",
    "CMU ML Blog": "https://blog.ml.cmu.edu/feed/",
    "Stanford AI Lab": "https://ai.stanford.edu/blog/feed/",
    "MIT CSAIL News": "https://www.csail.mit.edu/news/rss",
    "Stanford HAI": "https://hai.stanford.edu/news/rss.xml",
    "Princeton NLP": "https://princeton-nlp.github.io/feed.xml",
    "ETH Zurich AI Center": "https://ai.ethz.ch/news/feed.xml",
    "Mila Quebec AI": "https://mila.quebec/en/blog/feed/",
    "Max Planck IS": "https://is.mpg.de/news_feed",
    "Toronto ML Group": "https://www.cs.toronto.edu/~hinton/nntut/feed.xml",

    # ── AI Research Aggregators & Trackers (HIGH PRIORITY) ────────────
    "Papers with Code": "https://paperswithcode.com/latest",
    "Synced AI": "https://syncedreview.com/feed/",
    "The Batch (deeplearning.ai)": "https://www.deeplearning.ai/the-batch/feed/",
    "Ahead of AI (Sebastian Raschka)": "https://magazine.sebastianraschka.com/feed",
    "Import AI Newsletter": "https://importai.substack.com/feed",
    "The Gradient": "https://thegradient.pub/rss/",
    "AI Alignment Forum": "https://www.alignmentforum.org/feed.xml?view=community-rss",
    "ML Safety Newsletter": "https://newsletter.mlsafety.org/feed",
    "Interconnects (Nathan Lambert)": "https://www.interconnects.ai/feed",

    # ── AI Safety & Alignment Research (HIGH PRIORITY) ────────────────
    "Anthropic Research": "https://www.anthropic.com/research/rss",
    "DeepMind Safety Research": "https://deepmindsafetyresearch.medium.com/feed",
    "Center for AI Safety": "https://www.safe.ai/blog/rss.xml",
    "ARC Evals": "https://evals.alignment.org/blog/rss.xml",
    "MIRI Research": "https://intelligence.org/feed/",

    # ── AI Company Research Blogs (HIGH PRIORITY) ─────────────────────
    "OpenAI Research": "https://openai.com/blog/rss/",
    "Hugging Face Blog": "https://huggingface.co/blog/feed.xml",
    "Meta AI Research": "https://ai.meta.com/blog/rss/",
    "Microsoft Research AI": "https://www.microsoft.com/en-us/research/feed/",
    "NVIDIA AI Research": "https://blogs.nvidia.com/feed/",
    "Apple ML Research": "https://machinelearning.apple.com/rss.xml",
    "Amazon Science": "https://www.amazon.science/index.rss",
    "Salesforce AI Research": "https://blog.salesforceairesearch.com/rss/",
    "EleutherAI Blog": "https://blog.eleuther.ai/rss/",
    "Stability AI Blog": "https://stability.ai/blog/rss.xml",
    "Mistral AI Blog": "https://mistral.ai/feed.xml",
    "Together AI Blog": "https://www.together.ai/blog/rss.xml",

    # ── AI Agents, Frameworks & Tools (HIGH PRIORITY) ─────────────────
    "LangChain Blog": "https://blog.langchain.dev/rss/",
    "LlamaIndex Blog": "https://www.llamaindex.ai/blog/rss.xml",
    "Perplexity AI Blog": "https://www.perplexity.ai/hub/blog/rss",
    "AI21 Labs Blog": "https://www.ai21.com/blog/rss.xml",
    "Cohere AI Blog": "https://txt.cohere.com/rss/",
    "Weights & Biases Blog": "https://wandb.ai/site/rss.xml",
    "Gradient Flow": "https://gradientflow.com/feed/",

    # ── Tech News with Research Focus (MEDIUM PRIORITY) ───────────────
    "MIT Technology Review AI": "https://www.technologyreview.com/topic/artificial-intelligence/feed/",
    "Wired AI": "https://www.wired.com/tag/artificial-intelligence/feed/",
    "The New Stack AI": "https://thenewstack.io/tag/artificial-intelligence/feed/",
    "InfoQ AI": "https://www.infoq.com/ai-ml-data-eng/rss/",
    "Ars Technica AI": "https://arstechnica.com/tag/artificial-intelligence/feed/",
    "Quanta Magazine CS": "https://www.quantamagazine.org/computer-science/feed/",
}

# Web scraping targets for official blogs and research institutions
WEB_SCRAPING_TARGETS = {
    # ── Major AI Research Labs ────────────────────────────────────────
    "OpenAI": {
        "url": "https://openai.com/blog/",
        "title_selector": "h3 a",
        "link_selector": "h3 a",
        "content_selector": ".post-content",
    },
    "Google AI": {
        "url": "https://ai.googleblog.com/",
        "title_selector": ".post-title a",
        "link_selector": ".post-title a",
        "content_selector": ".post-content",
    },
    "DeepMind": {
        "url": "https://deepmind.google/discover/blog/",
        "title_selector": "h3 a",
        "link_selector": "h3 a",
        "content_selector": ".article-content",
    },
    "Meta AI": {
        "url": "https://ai.meta.com/blog/",
        "title_selector": "h3 a",
        "link_selector": "h3 a",
        "content_selector": ".article-content",
    },
    "Microsoft Research AI": {
        "url": "https://www.microsoft.com/en-us/research/research-area/artificial-intelligence/",
        "title_selector": "h3 a",
        "link_selector": "h3 a",
        "content_selector": ".entry-content",
    },
    "Anthropic": {
        "url": "https://www.anthropic.com/news",
        "title_selector": "h3 a",
        "link_selector": "h3 a",
        "content_selector": ".article-content",
    },
    "Apple ML Research": {
        "url": "https://machinelearning.apple.com/",
        "title_selector": "h2 a, h3 a",
        "link_selector": "h2 a, h3 a",
        "content_selector": "article, .post-content",
    },
    "Amazon Science": {
        "url": "https://www.amazon.science/",
        "title_selector": "h2 a, h3 a",
        "link_selector": "h2 a, h3 a",
        "content_selector": "article, .article-content",
    },
    "NVIDIA Research": {
        "url": "https://research.nvidia.com/news",
        "title_selector": "h2 a, h3 a",
        "link_selector": "h2 a, h3 a",
        "content_selector": "article, .content",
    },

    # ── Academic Institutions ─────────────────────────────────────────
    "MIT CSAIL": {
        "url": "https://www.csail.mit.edu/news",
        "title_selector": ".news-title a",
        "link_selector": ".news-title a",
        "content_selector": ".news-content",
    },
    "Stanford HAI": {
        "url": "https://hai.stanford.edu/news",
        "title_selector": "h3 a",
        "link_selector": "h3 a",
        "content_selector": ".article-content",
    },
    "Berkeley AI Research": {
        "url": "https://bair.berkeley.edu/blog/",
        "title_selector": ".post-title a",
        "link_selector": ".post-title a",
        "content_selector": ".post-content",
    },
    "Carnegie Mellon AI": {
        "url": "https://www.cs.cmu.edu/news",
        "title_selector": "h3 a",
        "link_selector": "h3 a",
        "content_selector": ".news-content",
    },
    "Oxford AI": {
        "url": "https://www.ox.ac.uk/news-and-events/find-an-event/?type=all&topic=artificial-intelligence",
        "title_selector": "h3 a, h2 a",
        "link_selector": "h3 a, h2 a",
        "content_selector": "article, .content",
    },
    "Cambridge ML Group": {
        "url": "https://mlg.eng.cam.ac.uk/blog/",
        "title_selector": "h2 a, h3 a",
        "link_selector": "h2 a, h3 a",
        "content_selector": "article, .post-content",
    },

    # ── Independent Research Labs ─────────────────────────────────────
    "Allen Institute for AI": {
        "url": "https://allenai.org/news",
        "title_selector": "h3 a",
        "link_selector": "h3 a",
        "content_selector": ".article-content",
    },
    "EleutherAI": {
        "url": "https://blog.eleuther.ai/",
        "title_selector": "h2 a, h3 a",
        "link_selector": "h2 a, h3 a",
        "content_selector": "article, .post-content",
    },
    "Cohere For AI": {
        "url": "https://cohere.com/research",
        "title_selector": "h2 a, h3 a",
        "link_selector": "h2 a, h3 a",
        "content_selector": "article, .article-content",
    },

    # ── AI Agent Frameworks & Tools ───────────────────────────────────
    "LangChain": {
        "url": "https://blog.langchain.dev/",
        "title_selector": "h2 a, h3 a",
        "link_selector": "h2 a, h3 a",
        "content_selector": ".post-content, article",
    },
    "LlamaIndex": {
        "url": "https://www.llamaindex.ai/blog",
        "title_selector": "h2 a, h3 a",
        "link_selector": "h2 a, h3 a",
        "content_selector": ".article-content, article",
    },
    "Hugging Face": {
        "url": "https://huggingface.co/blog",
        "title_selector": "h2 a, h3 a",
        "link_selector": "h2 a, h3 a",
        "content_selector": "article, .prose",
    },
    "Weights & Biases": {
        "url": "https://wandb.ai/site/articles",
        "title_selector": "h2 a, h3 a",
        "link_selector": "h2 a, h3 a",
        "content_selector": "article, .article-content",
    },
    "Perplexity AI": {
        "url": "https://www.perplexity.ai/hub/blog",
        "title_selector": "h2 a, h3 a, .post-title a",
        "link_selector": "h2 a, h3 a, .post-title a",
        "content_selector": "article, .post-content, .article-content",
    },
}