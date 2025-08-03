"""
Base summarizer class for AI News Aggregator Bot.

This module defines the abstract base class for all summarizer implementations.
"""

from abc import ABC, abstractmethod
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class BaseSummarizer(ABC):
    """Abstract base class for all summarization implementations."""
    
    def __init__(self, config, summarizer_name: str) -> None:
        """Initialize the summarizer."""
        self.config = config
        self.summarizer_name = summarizer_name
        self.logger = logger.getChild(self.__class__.__name__)
    
    @abstractmethod
    async def summarize(
        self, 
        title: str, 
        content: str, 
        source_url: Optional[str] = None
    ) -> str:
        """
        Summarize the given content.
        
        Args:
            title: The article title
            content: The full article content
            source_url: Optional URL of the source article
        
        Returns:
            A concise summary of the content
        """
        pass
    
    def _prepare_content(self, title: str, content: str) -> str:
        """Prepare content for summarization by cleaning and truncating if needed."""
        # Clean the content
        cleaned_content = self._clean_text(content)
        
        # Truncate if too long (most models have token limits)
        max_chars = 8000  # Conservative limit for most models
        if len(cleaned_content) > max_chars:
            cleaned_content = cleaned_content[:max_chars] + "..."
            self.logger.info(f"Truncated content to {max_chars} characters")
        
        return cleaned_content
    
    def _clean_text(self, text: str) -> str:
        """Clean text content for better summarization."""
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = " ".join(text.split())
        
        # Remove common artifacts that might interfere with summarization
        artifacts = [
            "Advertisement", "ADVERTISEMENT", "Sponsored Content",
            "Click here", "Read more", "Subscribe", "Newsletter",
            "Cookie Policy", "Terms of Service", "Privacy Policy"
        ]
        
        for artifact in artifacts:
            text = text.replace(artifact, "")
        
        return text.strip()
    
    def _build_system_prompt(self) -> str:
        """Build the system prompt for summarization."""
        return """You are an AI news summarization expert. Your task is to create concise, informative summaries of AI-related news articles and research papers.

Guidelines:
- Keep summaries between 100-200 words
- Focus on the most important developments, findings, or announcements
- Use clear, accessible language that both technical and non-technical readers can understand
- Highlight key implications or potential impact
- Maintain objectivity and accuracy
- Include specific details like company names, product names, or research findings when relevant
- For research papers, focus on the main contribution and potential applications

Format the summary as a single, well-structured paragraph."""
    
    def _build_user_prompt(self, title: str, content: str) -> str:
        """Build the user prompt with the article content."""
        return f"""Please summarize this AI-related article:

Title: {title}

Content: {content}

Provide a concise summary that captures the key points and significance of this development."""
    
    def _validate_summary(self, summary: str) -> bool:
        """Validate that the generated summary meets quality criteria."""
        if not summary:
            return False
        
        # Check length
        word_count = len(summary.split())
        if word_count < 20 or word_count > 300:
            self.logger.warning(f"Summary word count ({word_count}) outside expected range")
            return False
        
        # Check for obvious errors or incomplete responses
        error_indicators = [
            "I cannot", "I'm unable", "I don't have", "Sorry, I",
            "As an AI", "I apologize", "Error:", "Failed to"
        ]
        
        summary_lower = summary.lower()
        for indicator in error_indicators:
            if indicator.lower() in summary_lower:
                self.logger.warning(f"Summary contains error indicator: {indicator}")
                return False
        
        return True
    
    def _post_process_summary(self, summary: str) -> str:
        """Post-process the summary to ensure quality and consistency."""
        if not summary:
            return "Summary generation failed."
        
        # Clean up the summary
        summary = summary.strip()
        
        # Remove any leading/trailing quotes that might have been added
        if (summary.startswith('"') and summary.endswith('"')) or \
           (summary.startswith("'") and summary.endswith("'")):
            summary = summary[1:-1].strip()
        
        # Ensure the summary ends with proper punctuation
        if not summary.endswith(('.', '!', '?')):
            summary += '.'
        
        # Limit length if still too long
        max_chars = 800
        if len(summary) > max_chars:
            # Try to cut at a sentence boundary
            sentences = summary.split('.')
            truncated = ""
            for sentence in sentences:
                if len(truncated + sentence + '.') <= max_chars:
                    truncated += sentence + '.'
                else:
                    break
            
            if truncated:
                summary = truncated
            else:
                summary = summary[:max_chars] + '...'
        
        return summary