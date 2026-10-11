"""Unit tests for summarizer loading and dependency handling."""

import unittest
from unittest.mock import MagicMock
import sys

from ai_news_bot.summarizer import (
    BaseSummarizer,
    get_summarizer,
    AnthropicSummarizer,
)


class TestSummarizerImports(unittest.TestCase):
    """Test summarizer loading and error handling."""

    def test_get_summarizer_unknown_type(self):
        """Unknown summarizer types should raise ValueError."""
        config = MagicMock()
        config.summarizer_type = "invalid_type"
        with self.assertRaises(ValueError):
            get_summarizer(config)

    def test_anthropic_summarizer_missing_dependency(self):
        """AnthropicSummarizer should raise ImportError if anthropic is not installed."""
        # Check if anthropic is installed in this test environment
        if "anthropic" not in sys.modules:
            try:
                import anthropic
            except ImportError:
                config = MagicMock()
                config.anthropic_api_key = "test-key"
                config.anthropic_model = "claude-3-haiku-20240307"
                with self.assertRaises(ImportError) as ctx:
                    AnthropicSummarizer(config)
                self.assertIn("anthropic", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
