"""
Content Analyzer for AI News Aggregator.

This module provides advanced content analysis including:
- AI relevance scoring
- Topic categorization
- Keyword extraction
- Content similarity detection
"""

import re
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


# AI topic categories with weighted keywords
AI_TOPIC_KEYWORDS = {
    "Large Language Models": {
        "keywords": [
            "llm", "large language model", "gpt", "bert", "transformer",
            "chatgpt", "claude", "gemini", "palm", "bard", "llama",
            "language model", "generative ai", "prompt engineering",
            "fine-tuning", "rlhf", "instruction tuning", "context window",
            "token", "embedding", "attention mechanism", "foundation model"
        ],
        "weight": 1.5
    },
    "Computer Vision": {
        "keywords": [
            "computer vision", "image recognition", "object detection",
            "image segmentation", "cv", "visual", "cnn", "convolutional",
            "yolo", "rcnn", "vit", "vision transformer", "image generation",
            "stable diffusion", "dall-e", "midjourney", "imagen",
            "visual understanding", "image classification", "face recognition",
            "scene understanding", "video analysis"
        ],
        "weight": 1.3
    },
    "Natural Language Processing": {
        "keywords": [
            "nlp", "natural language processing", "text analysis",
            "sentiment analysis", "named entity", "ner", "tokenization",
            "language understanding", "text generation", "machine translation",
            "question answering", "text classification", "semantic",
            "syntactic", "parsing", "pos tagging", "word embeddings"
        ],
        "weight": 1.2
    },
    "Machine Learning": {
        "keywords": [
            "machine learning", "ml", "neural network", "deep learning",
            "supervised learning", "unsupervised learning", "reinforcement learning",
            "training", "inference", "model", "algorithm", "gradient descent",
            "backpropagation", "optimization", "regularization", "overfitting",
            "cross-validation", "hyperparameter", "feature engineering"
        ],
        "weight": 1.0
    },
    "AI Ethics & Safety": {
        "keywords": [
            "ai ethics", "ai safety", "alignment", "bias", "fairness",
            "explainable ai", "interpretability", "transparency",
            "responsible ai", "ai governance", "ai regulation",
            "privacy", "security", "adversarial", "robustness",
            "hallucination", "ai risks", "ai benefits"
        ],
        "weight": 1.4
    },
    "Robotics & Autonomous Systems": {
        "keywords": [
            "robotics", "autonomous", "self-driving", "robot",
            "automation", "embodied ai", "control systems",
            "sensor fusion", "slam", "path planning", "manipulation",
            "humanoid", "drone", "autonomous vehicle"
        ],
        "weight": 1.3
    },
    "AI Research": {
        "keywords": [
            "arxiv", "research paper", "study", "experiment",
            "benchmark", "dataset", "sota", "state-of-the-art",
            "evaluation", "ablation", "methodology", "architecture",
            "novel approach", "breakthrough", "innovation"
        ],
        "weight": 1.1
    },
    "AI Applications": {
        "keywords": [
            "ai application", "use case", "deployment", "production",
            "enterprise ai", "ai integration", "ai adoption",
            "real-world", "practical", "implementation", "solution"
        ],
        "weight": 0.9
    },
    "AI Companies & Business": {
        "keywords": [
            "openai", "google ai", "deepmind", "anthropic", "meta ai",
            "microsoft ai", "amazon ai", "nvidia", "hugging face",
            "startup", "funding", "investment", "acquisition",
            "partnership", "product launch", "announcement"
        ],
        "weight": 1.0
    },
    "Multimodal AI": {
        "keywords": [
            "multimodal", "vision-language", "text-to-image",
            "image-to-text", "video understanding", "audio-visual",
            "cross-modal", "unified model", "multi-task"
        ],
        "weight": 1.4
    }
}


# High-value AI keywords for relevance scoring
HIGH_VALUE_KEYWORDS = {
    "breakthrough", "revolutionary", "novel", "state-of-the-art", "sota",
    "benchmark", "outperform", "significant", "advancement", "innovation",
    "introduces", "proposes", "demonstrates", "achieves", "improves"
}

# Research-specific keywords for boosting academic content
RESEARCH_KEYWORDS = {
    "research", "study", "paper", "arxiv", "published", "journal",
    "conference", "proceedings", "experiment", "findings", "results",
    "methodology", "dataset", "evaluation", "analysis", "empirical",
    "theoretical", "algorithm", "framework", "approach", "method",
    "peer-reviewed", "citation", "authors", "abstract", "conclusion",
    "hypothesis", "validate", "reproduce", "ablation", "baseline",
    "neurips", "icml", "iclr", "cvpr", "acl", "emnlp", "aaai", "ijcai"
}


class ContentAnalyzer:
    """Analyzes article content for AI relevance, topics, and keywords."""
    
    def __init__(self):
        """Initialize the content analyzer."""
        self.logger = logger.getChild(self.__class__.__name__)
        
        # Build comprehensive keyword set for AI detection
        self.ai_keywords = set()
        for topic_data in AI_TOPIC_KEYWORDS.values():
            self.ai_keywords.update(topic_data["keywords"])
        
        # Include research keywords for comprehensive coverage
        self.research_keywords = RESEARCH_KEYWORDS
    
    def analyze_article(self, title: str, content: str) -> Dict:
        """
        Perform comprehensive analysis on article content.
        
        Returns a dict with:
        - relevance_score: float (0-100)
        - topics: list of identified topics
        - keywords: list of extracted keywords
        - is_ai_related: bool
        """
        text_lower = f"{title} {content}".lower()
        
        # Calculate relevance score
        relevance_score = self._calculate_relevance_score(title, content, text_lower)
        
        # Identify topics
        topics = self._identify_topics(text_lower)
        
        # Extract keywords
        keywords = self._extract_keywords(title, content, text_lower)
        
        # Determine if content is AI-related
        is_ai_related = relevance_score >= 30 or len(topics) > 0
        
        return {
            "relevance_score": round(relevance_score, 2),
            "topics": topics,
            "keywords": keywords,
            "is_ai_related": is_ai_related
        }
    
    def _calculate_relevance_score(self, title: str, content: str, text_lower: str) -> float:
        """
        Calculate AI relevance score (0-100).
        
        Scoring factors:
        - Keyword matches in title (higher weight)
        - Keyword matches in content
        - Topic category matches
        - High-value keyword presence
        - Density of AI terms
        """
        score = 0.0
        title_lower = title.lower()
        
        # Score 1: Title keyword matches (up to 30 points)
        title_matches = 0
        for keyword in self.ai_keywords:
            if keyword in title_lower:
                title_matches += 1
                # Longer keywords are more specific and valuable
                score += min(len(keyword) / 2, 5)
        
        score = min(score, 30)  # Cap title contribution
        
        # Score 2: Content keyword matches (up to 30 points)
        content_matches = 0
        for keyword in self.ai_keywords:
            if keyword in text_lower:
                content_matches += 1
        
        # Calculate density (keywords per 100 words)
        word_count = len(text_lower.split())
        if word_count > 0:
            density = (content_matches / word_count) * 100
            score += min(density * 3, 30)  # Up to 30 points
        
        # Score 3: Topic category matches (up to 20 points)
        topic_score = 0
        for topic, topic_data in AI_TOPIC_KEYWORDS.items():
            matches = sum(1 for kw in topic_data["keywords"] if kw in text_lower)
            if matches > 0:
                topic_score += matches * topic_data["weight"]
        
        score += min(topic_score, 20)
        
        # Score 4: High-value keywords (up to 15 points)
        high_value_matches = sum(1 for kw in HIGH_VALUE_KEYWORDS if kw in text_lower)
        score += min(high_value_matches * 3, 15)
        
        # Score 5: Title prominence bonus (up to 5 points)
        if any(kw in title_lower for kw in ["ai", "artificial intelligence", "machine learning", "llm"]):
            score += 5
        
        # Score 6: Research content boost (up to 10 points)
        research_matches = sum(1 for kw in self.research_keywords if kw in text_lower)
        if research_matches > 0:
            # Strong boost for research content
            research_boost = min(research_matches * 2, 10)
            score += research_boost
            
            # Extra bonus for ArXiv or published papers
            if "arxiv" in text_lower or "published" in text_lower:
                score += 5
        
        return min(score, 100.0)
    
    def _identify_topics(self, text_lower: str) -> List[str]:
        """Identify relevant AI topic categories."""
        identified_topics = []
        
        for topic, topic_data in AI_TOPIC_KEYWORDS.items():
            matches = sum(1 for kw in topic_data["keywords"] if kw in text_lower)
            
            # Threshold: at least 2 keyword matches to identify a topic
            if matches >= 2:
                identified_topics.append(topic)
        
        return identified_topics
    
    def _extract_keywords(self, title: str, content: str, text_lower: str) -> List[str]:
        """Extract most relevant keywords from the content."""
        # Find all matching AI keywords
        found_keywords = set()
        
        for keyword in self.ai_keywords:
            if keyword in text_lower:
                found_keywords.add(keyword)
        
        # Also look for high-value keywords
        for keyword in HIGH_VALUE_KEYWORDS:
            if keyword in text_lower:
                found_keywords.add(keyword)
        
        # Add research keywords (prioritize research content)
        for keyword in self.research_keywords:
            if keyword in text_lower:
                found_keywords.add(keyword)
        
        # Prioritize keywords that appear in the title
        title_lower = title.lower()
        prioritized = []
        regular = []
        
        for kw in found_keywords:
            if kw in title_lower:
                prioritized.append(kw)
            else:
                regular.append(kw)
        
        # Return up to 20 most relevant keywords (increased for research)
        return (prioritized + regular)[:20]
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate similarity between two texts using Jaccard similarity.
        
        Returns a score between 0 and 1.
        """
        # Tokenize and create sets of words
        words1 = set(re.findall(r'\w+', text1.lower()))
        words2 = set(re.findall(r'\w+', text2.lower()))
        
        # Remove very common words
        stop_words = {'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                      'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
                      'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
                      'would', 'should', 'could', 'may', 'might', 'must', 'can'}
        
        words1 = words1 - stop_words
        words2 = words2 - stop_words
        
        if not words1 or not words2:
            return 0.0
        
        # Calculate Jaccard similarity
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        similarity = len(intersection) / len(union) if union else 0.0
        
        return similarity
    
    def is_duplicate(self, title1: str, title2: str, threshold: float = 0.7) -> bool:
        """
        Check if two articles are likely duplicates based on title similarity.
        """
        similarity = self.calculate_similarity(title1, title2)
        return similarity >= threshold
    
    def get_ai_keyword_stats(self) -> Dict[str, int]:
        """Get statistics about AI keywords."""
        return {
            "total_keywords": len(self.ai_keywords),
            "topics": len(AI_TOPIC_KEYWORDS),
            "high_value_keywords": len(HIGH_VALUE_KEYWORDS)
        }

