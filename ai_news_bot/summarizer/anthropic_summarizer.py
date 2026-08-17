"""
Anthropic Claude-based summarizer implementation.

Uses Anthropic's Claude models to generate article summaries.
Lightweight API client — no local model overhead, ideal for Raspberry Pi.
"""

from typing import Optional

import anthropic

from .base import BaseSummarizer


class AnthropicSummarizer(BaseSummarizer):
    """Summarizer that uses Anthropic's Claude models."""

    def __init__(self, config) -> None:
        super().__init__(config, "Anthropic")

        if not config.anthropic_api_key:
            raise ValueError("Anthropic API key is required for Anthropic summarizer")

        self.client = anthropic.AsyncAnthropic(api_key=config.anthropic_api_key)
        self.model = config.anthropic_model

        self.logger.info(f"Initialized Anthropic summarizer with model {self.model}")

    async def summarize(
        self,
        title: str,
        content: str,
        source_url: Optional[str] = None,
    ) -> str:
        try:
            cleaned_content = self._prepare_content(title, content)
            system_prompt = self._build_system_prompt()
            user_prompt = self._build_user_prompt(title, cleaned_content)

            self.logger.debug(f"Generating summary for: {title}")

            message = await self.client.messages.create(
                model=self.model,
                max_tokens=400,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
                temperature=0.3,
            )

            summary = message.content[0].text.strip()

            if not self._validate_summary(summary):
                self.logger.warning(f"Generated summary failed validation for: {title}")
                return f"Unable to generate quality summary for this article. Title: {title}"

            processed_summary = self._post_process_summary(summary)
            self.logger.info(f"Successfully generated summary for: {title}")
            return processed_summary

        except anthropic.RateLimitError as e:
            self.logger.error(f"Anthropic rate limit exceeded: {e}")
            return f"Summary temporarily unavailable due to rate limits. Title: {title}"

        except anthropic.APIError as e:
            self.logger.error(f"Anthropic API error: {e}")
            return f"Summary generation failed due to API error. Title: {title}"

        except Exception as e:
            self.logger.error(f"Unexpected error in Anthropic summarization: {e}")
            return f"Summary generation failed. Title: {title}"

    def _build_system_prompt(self) -> str:
        base_prompt = super()._build_system_prompt()
        claude_specific = """
Additional instructions:
- Be precise and factual — avoid speculation
- Include specific metrics, numbers, or dates when mentioned
- Balance technical accuracy with accessibility
- Respond with just the summary, no meta-commentary
"""
        return base_prompt + claude_specific
