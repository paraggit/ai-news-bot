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
    
    # News Fetching Configuration
    fetch_interval_minutes: int = 30
    max_articles_per_run: int = 10
    
    # Database Configuration
    database_path: str = "data/news_aggregator.db"
    
    # Logging Configuration
    log_level: str = "INFO"
    log_file: str = "logs/app.log"
    
    # ArXiv Configuration
    arxiv_max_results: int = 5
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
            self.arxiv_categories = ["cs.AI", "cs.LG", "cs.CL", "cs.CV"]
        
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
    
    # Parse ArXiv categories
    arxiv_categories_str = os.getenv("ARXIV_CATEGORIES", "cs.AI,cs.LG,cs.CL,cs.CV")
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
        
        # News Fetching Configuration
        fetch_interval_minutes=int(os.getenv("FETCH_INTERVAL_MINUTES", "30")),
        max_articles_per_run=int(os.getenv("MAX_ARTICLES_PER_RUN", "10")),
        
        # Database Configuration
        database_path=os.getenv("DATABASE_PATH", "data/news_aggregator.db"),
        
        # Logging Configuration
        log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
        log_file=os.getenv("LOG_FILE", "logs/app.log"),
        
        # ArXiv Configuration
        arxiv_max_results=int(os.getenv("ARXIV_MAX_RESULTS", "5")),
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


# RSS Feed URLs for major AI news sources
RSS_FEEDS = {
    "TechCrunch AI": "https://techcrunch.com/category/artificial-intelligence/feed/",
    "VentureBeat AI": "https://venturebeat.com/ai/feed/",
    "MIT Technology Review AI": "https://www.technologyreview.com/topic/artificial-intelligence/feed/",
    "Wired AI": "https://www.wired.com/tag/artificial-intelligence/feed/",
    "The Verge AI": "https://www.theverge.com/ai-artificial-intelligence/rss/index.xml",
}

# Web scraping targets for official blogs
WEB_SCRAPING_TARGETS = {
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
    }
}