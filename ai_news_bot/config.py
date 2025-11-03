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
    
    # Network Configuration
    ssl_verify: bool = True
    http_timeout: int = 30
    max_retries: int = 3
    user_agent: str = "AI-News-Aggregator-Bot/1.0"
    
    def __post_init__(self):
        """Post-initialization validation and setup."""
        if self.arxiv_categories is None:
            # Expanded ArXiv categories for comprehensive research coverage
            self.arxiv_categories = [
                "cs.AI",    # Artificial Intelligence
                "cs.LG",    # Machine Learning
                "cs.CL",    # Computation and Language (NLP)
                "cs.CV",    # Computer Vision
                "cs.NE",    # Neural and Evolutionary Computing
                "cs.RO",    # Robotics
                "cs.IR",    # Information Retrieval
                "cs.MA",    # Multiagent Systems
                "stat.ML",  # Machine Learning (Statistics)
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
        
        if self.summarizer_type not in ["openai", "deepseek", "local"]:
            raise ValueError("SUMMARIZER_TYPE must be 'openai', 'deepseek', or 'local'")


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
    # Research-focused sources (HIGH PRIORITY - actual research breakthroughs)
    "Nature Machine Intelligence": "https://www.nature.com/natmachintell.rss",
    "Science AI": "https://www.science.org/rss/news_current.xml",
    "IEEE Spectrum AI": "https://spectrum.ieee.org/feeds/feed.rss",
    "ACM TechNews": "https://technews.acm.org/news.rss",
    
    # Academic and research blogs (HIGH PRIORITY)
    "AI Research Blog - Google": "https://ai.googleblog.com/feeds/posts/default",
    "Berkeley AI Research": "https://bair.berkeley.edu/blog/feed.xml",
    "CMU ML Blog": "https://blog.ml.cmu.edu/feed/",
    "Stanford AI Lab": "https://ai.stanford.edu/blog/feed/",
    
    # AI-specific research news (HIGH PRIORITY)
    "Papers with Code": "https://paperswithcode.com/latest",
    "Synced AI": "https://syncedreview.com/feed/",
    
    # Tech news with research focus (MEDIUM PRIORITY - filtered for research)
    "MIT Technology Review AI": "https://www.technologyreview.com/topic/artificial-intelligence/feed/",
    "Wired AI": "https://www.wired.com/tag/artificial-intelligence/feed/",
    
    # NOTE: TechCrunch and VentureBeat removed - too much investment/funding news
    # If needed, they can be re-added but content_analyzer will heavily filter them
}

# Web scraping targets for official blogs and research institutions
WEB_SCRAPING_TARGETS = {
    # Major AI Companies
    "OpenAI": {
        "url": "https://openai.com/blog/",
        "title_selector": "h3 a",
        "link_selector": "h3 a",
        "content_selector": ".post-content"
    },
    "Google AI": {
        "url": "https://ai.googleblog.com/",
        "title_selector": ".post-title a",
        "link_selector": ".post-title a", 
        "content_selector": ".post-content"
    },
    "DeepMind": {
        "url": "https://deepmind.google/discover/blog/",
        "title_selector": "h3 a",
        "link_selector": "h3 a",
        "content_selector": ".article-content"
    },
    "Meta AI": {
        "url": "https://ai.meta.com/blog/",
        "title_selector": "h3 a",
        "link_selector": "h3 a",
        "content_selector": ".article-content"
    },
    "Microsoft Research AI": {
        "url": "https://www.microsoft.com/en-us/research/research-area/artificial-intelligence/",
        "title_selector": "h3 a",
        "link_selector": "h3 a",
        "content_selector": ".entry-content"
    },
    
    # Academic Institutions
    "MIT CSAIL": {
        "url": "https://www.csail.mit.edu/news",
        "title_selector": ".news-title a",
        "link_selector": ".news-title a",
        "content_selector": ".news-content"
    },
    "Stanford HAI": {
        "url": "https://hai.stanford.edu/news",
        "title_selector": "h3 a",
        "link_selector": "h3 a",
        "content_selector": ".article-content"
    },
    "Berkeley AI Research": {
        "url": "https://bair.berkeley.edu/blog/",
        "title_selector": ".post-title a",
        "link_selector": ".post-title a",
        "content_selector": ".post-content"
    },
    "Carnegie Mellon AI": {
        "url": "https://www.cs.cmu.edu/news",
        "title_selector": "h3 a",
        "link_selector": "h3 a",
        "content_selector": ".news-content"
    },
    
    # Research Labs
    "Allen Institute for AI": {
        "url": "https://allenai.org/news",
        "title_selector": "h3 a",
        "link_selector": "h3 a",
        "content_selector": ".article-content"
    },
    "Anthropic": {
        "url": "https://www.anthropic.com/news",
        "title_selector": "h3 a",
        "link_selector": "h3 a",
        "content_selector": ".article-content"
    },
}