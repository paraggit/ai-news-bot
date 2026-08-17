"""
Summarizer package for AI News Aggregator Bot.

This package provides different summarization implementations including
OpenAI, DeepSeek, and local model options.
"""

from ..config import Config
from .base import BaseSummarizer
from .openai_summarizer import OpenAISummarizer
from .deepseek_summarizer import DeepSeekSummarizer
from .local_summarizer import LocalSummarizer
from .anthropic_summarizer import AnthropicSummarizer


def get_summarizer(config: Config) -> BaseSummarizer:
    """Get the appropriate summarizer based on configuration."""

    if config.summarizer_type == "openai":
        return OpenAISummarizer(config)
    elif config.summarizer_type == "deepseek":
        return DeepSeekSummarizer(config)
    elif config.summarizer_type == "local":
        return LocalSummarizer(config)
    elif config.summarizer_type == "anthropic":
        return AnthropicSummarizer(config)
    else:
        raise ValueError(f"Unknown summarizer type: {config.summarizer_type}")


__all__ = [
    "BaseSummarizer",
    "OpenAISummarizer",
    "DeepSeekSummarizer",
    "LocalSummarizer",
    "AnthropicSummarizer",
    "get_summarizer",
]