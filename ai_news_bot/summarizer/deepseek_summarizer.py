"""
DeepSeek-based summarizer implementation.

This module uses DeepSeek's API to generate article summaries.
"""

from typing import Optional
import httpx

from .base import BaseSummarizer


class DeepSeekSummarizer(BaseSummarizer):
    """Summarizer that uses DeepSeek's API."""
    
    def __init__(self, config) -> None:
        """Initialize DeepSeek summarizer."""
        super().__init__(config, "DeepSeek")
        
        if not config.deepseek_api_key:
            raise ValueError("DeepSeek API key is required for DeepSeek summarizer")
        
        self.api_key = config.deepseek_api_key
        self.base_url = config.deepseek_base_url
        self.model = "deepseek-chat"  # Default DeepSeek model
        
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
        )
        
        self.logger.info(f"Initialized DeepSeek summarizer")
    
    async def summarize(
        self, 
        title: str, 
        content: str, 
        source_url: Optional[str] = None
    ) -> str:
        """Summarize content using DeepSeek's API."""
        try:
            # Prepare content
            cleaned_content = self._prepare_content(title, content)
            
            # Build prompts
            system_prompt = self._build_system_prompt()
            user_prompt = self._build_user_prompt(title, cleaned_content)
            
            self.logger.debug(f"Generating summary for: {title}")
            
            # Prepare API request
            request_data = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "max_tokens": 300,
                "temperature": 0.3,
                "top_p": 0.9,
                "stream": False
            }
            
            # Call DeepSeek API
            response = await self.client.post(
                f"{self.base_url}/chat/completions",
                json=request_data
            )
            
            response.raise_for_status()
            result = response.json()
            
            # Extract summary
            if "choices" not in result or not result["choices"]:
                raise ValueError("Invalid response format from DeepSeek API")
            
            summary = result["choices"][0]["message"]["content"].strip()
            
            # Validate and post-process
            if not self._validate_summary(summary):
                self.logger.warning(f"Generated summary failed validation for: {title}")
                return f"Unable to generate quality summary for this article. Title: {title}"
            
            processed_summary = self._post_process_summary(summary)
            
            self.logger.info(f"Successfully generated summary for: {title}")
            return processed_summary
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                self.logger.error("DeepSeek rate limit exceeded")
                return f"Summary temporarily unavailable due to rate limits. Title: {title}"
            else:
                self.logger.error(f"DeepSeek HTTP error {e.response.status_code}: {e}")
                return f"Summary generation failed due to API error. Title: {title}"
        
        except httpx.RequestError as e:
            self.logger.error(f"DeepSeek request error: {e}")
            return f"Summary generation failed due to network error. Title: {title}"
        
        except Exception as e:
            self.logger.error(f"Unexpected error in DeepSeek summarization: {e}")
            return f"Summary generation failed. Title: {title}"
    
    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()
    
    def _build_system_prompt(self) -> str:
        """Build DeepSeek-specific system prompt."""
        base_prompt = super()._build_system_prompt()
        
        deepseek_specific = """
Additional instructions for DeepSeek:
- Focus on factual accuracy and clear reasoning
- Include specific technical details when relevant
- Maintain a balance between comprehensiveness and conciseness
- Avoid repetition and redundant information
- Structure the summary logically with smooth transitions between ideas
"""
        
        return base_prompt + deepseek_specific