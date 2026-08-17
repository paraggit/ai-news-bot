"""
Digest generator for AI News Aggregator.

Collects top articles over a configurable period, groups by topic,
and produces a single formatted digest message for Telegram.
Memory-efficient: processes articles in batches for Raspberry Pi.
"""

import logging
from typing import Dict, List, Any, Optional

from .config import Config
from .database import DatabaseManager
from .summarizer import get_summarizer

logger = logging.getLogger(__name__)


class DigestGenerator:
    """Generates periodic digest summaries of top AI news."""

    def __init__(self, config: Config, db_manager: DatabaseManager) -> None:
        self.config = config
        self.db = db_manager
        self.summarizer = get_summarizer(config)
        self.logger = logger.getChild(self.__class__.__name__)

    async def generate_digest(
        self,
        hours: Optional[int] = None,
        max_articles: Optional[int] = None,
    ) -> Optional[str]:
        """
        Generate a digest message covering articles from the last N hours.
        Returns formatted Telegram message or None if no articles found.
        """
        hours = hours or self.config.digest_period_hours
        max_articles = max_articles or self.config.digest_max_articles

        self.logger.info(f"Generating digest for last {hours}h (max {max_articles} articles)")

        grouped = await self.db.get_digest_articles(hours=hours, limit=max_articles)
        if not grouped:
            self.logger.info("No articles found for digest")
            return None

        total = sum(len(articles) for articles in grouped.values())
        self.logger.info(f"Digest covers {total} articles across {len(grouped)} topics")

        sections: List[str] = []
        for topic, articles in grouped.items():
            section = self._format_topic_section(topic, articles)
            sections.append(section)

        header = self._build_header(total, hours, len(grouped))
        footer = self._build_footer()
        message = f"{header}\n\n" + "\n\n".join(sections) + f"\n\n{footer}"

        return message

    def _format_topic_section(
        self, topic: str, articles: List[Dict[str, Any]]
    ) -> str:
        topic_emoji = {
            "Large Language Models": "LLM",
            "Computer Vision": "CV",
            "Natural Language Processing": "NLP",
            "Machine Learning": "ML",
            "AI Ethics & Safety": "Ethics",
            "Robotics & Autonomous Systems": "Robotics",
            "AI Research": "Research",
            "AI Applications": "Apps",
            "Multimodal AI": "Multimodal",
            "AI Agents & Agentic AI": "Agents",
            "AI Frameworks & Tools": "Tools",
            "Model Context Protocol & Integration": "MCP",
            "AI Bots & Chatbots": "Bots",
            "AI Development & MLOps": "MLOps",
        }

        short_label = topic_emoji.get(topic, topic[:12])
        lines = [f"**[{short_label}] {topic}**"]

        for article in articles[:5]:
            score = article.get("relevance_score", 0)
            badge = " *" if score >= 80 else ""
            summary_text = ""
            if article.get("summary"):
                summary_text = article["summary"][:120]
                if len(article["summary"]) > 120:
                    summary_text += "..."
            title_line = f"  - [{article['title'][:80]}]({article['url']}){badge}"
            lines.append(title_line)
            if summary_text:
                lines.append(f"    _{summary_text}_")

        return "\n".join(lines)

    def _build_header(self, total: int, hours: int, topic_count: int) -> str:
        period = f"{hours}h" if hours < 48 else f"{hours // 24}d"
        return (
            f"**AI News Digest** ({period})\n"
            f"_{total} articles across {topic_count} topics_"
        )

    def _build_footer(self) -> str:
        return (
            "---\n"
            "_Use /search <query> to explore | /trending for hot topics_\n"
            "#AIDigest #AIResearch"
        )
