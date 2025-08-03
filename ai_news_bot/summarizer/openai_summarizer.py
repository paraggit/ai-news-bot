"""
OpenAI-based summarizer implementation.

This module uses OpenAI's GPT models to generate article summaries.
"""

from typing import Optional
import openai
from openai import AsyncOpenAI

from .base import BaseSummarizer


class OpenAISummarizer(BaseSummarizer):
    """Summarizer that uses OpenAI's GPT models."""
    
    def __init__(self, config) -> None:
        """Initialize OpenAI summarizer."""
        super().__init__(config, "OpenAI")
        
        if not config.openai_api_key:
            raise ValueError("OpenAI API key is required for OpenAI summarizer")
        
        self.client = AsyncOpenAI(api_key=config.openai_api_key)
        self.model = config.openai_model
        
        self.logger.info(f"Initialized OpenAI summarizer with model {self.model}")
    
    async def summarize(
        self, 
        title: str, 
        content: str, 
        source_url: Optional[str] = None
    ) -> str:
        """Summarize content using OpenAI's GPT model."""
        try:
            # Prepare content
            cleaned_content = self._prepare_content(title, content)
            
            # Build prompts
            system_prompt = self._build_system_prompt()
            user_prompt = self._build_user_prompt(title, cleaned_content)
            
            self.logger.debug(f"Generating summary for: {title}")
            
            # Call OpenAI API
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=300,
                temperature=0.3,  # Lower temperature for more consistent summaries
                top_p=0.9,
                frequency_penalty=0.0,
                presence_penalty=0.0
            )
            
            # Extract summary
            summary = response.choices[0].message.content.strip()
            
            # Validate and post-process
            if not self._validate_summary(summary):
                self.logger.warning(f"Generated summary failed validation for: {title}")
                return f"Unable to generate quality summary for this article. Title: {title}"
            
            processed_summary = self._post_process_summary(summary)
            
            self.logger.info(f"Successfully generated summary for: {title}")
            return processed_summary
            
        except openai.RateLimitError as e:
            self.logger.error(f"OpenAI rate limit exceeded: {e}")
            return f"Summary temporarily unavailable due to rate limits. Title: {title}"
        
        except openai.APIError as e:
            self.logger.error(f"OpenAI API error: {e}")
            return f"Summary generation failed due to API error. Title: {title}"
        
        except Exception as e:
            self.logger.error(f"Unexpected error in OpenAI summarization: {e}")
            return f"Summary generation failed. Title: {title}"
    
    def _build_system_prompt(self) -> str:
        """Build OpenAI-specific system prompt."""
        base_prompt = super()._build_system_prompt()
        
        openai_specific = """
Additional instructions for OpenAI models:
- Be precise and factual
- Avoid speculation or editorial commentary
- If the article mentions specific metrics, numbers, or dates, include them
- For technical content, balance technical accuracy with accessibility
- Always respond with just the summary, no additional commentary or meta-text
"""
        
        return base_prompt + openai_specific