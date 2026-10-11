"""
Summarizer package for AI News Aggregator Bot.

This package provides different summarization implementations including
OpenAI, DeepSeek, and local model options.
"""

from typing import TYPE_CHECKING
from ..config import Config
from .base import BaseSummarizer

if TYPE_CHECKING:
    from .openai_summarizer import OpenAISummarizer
    from .deepseek_summarizer import DeepSeekSummarizer
    from .local_summarizer import LocalSummarizer
    from .anthropic_summarizer import AnthropicSummarizer


def get_summarizer(config: Config) -> BaseSummarizer:
    """Get the appropriate summarizer based on configuration."""

    if config.summarizer_type == "openai":
        from .openai_summarizer import OpenAISummarizer
        return OpenAISummarizer(config)
    elif config.summarizer_type == "deepseek":
        from .deepseek_summarizer import DeepSeekSummarizer
        return DeepSeekSummarizer(config)
    elif config.summarizer_type == "local":
        from .local_summarizer import LocalSummarizer
        return LocalSummarizer(config)
    elif config.summarizer_type == "anthropic":
        from .anthropic_summarizer import AnthropicSummarizer
        return AnthropicSummarizer(config)
    else:
        raise ValueError(f"Unknown summarizer type: {config.summarizer_type}")


def __getattr__(name: str):
    """Lazy-load summarizer classes to avoid import-time dependency failures."""
    if name == "OpenAISummarizer":
        from .openai_summarizer import OpenAISummarizer
        return OpenAISummarizer
    if name == "DeepSeekSummarizer":
        from .deepseek_summarizer import DeepSeekSummarizer
        return DeepSeekSummarizer
    if name == "LocalSummarizer":
        from .local_summarizer import LocalSummarizer
        return LocalSummarizer
    if name == "AnthropicSummarizer":
        from .anthropic_summarizer import AnthropicSummarizer
        return AnthropicSummarizer
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "BaseSummarizer",
    "OpenAISummarizer",
    "DeepSeekSummarizer",
    "LocalSummarizer",
    "AnthropicSummarizer",
    "get_summarizer",
]