import logging
import re

from openai import AsyncOpenAI
from typing import List, AsyncGenerator
from app.core.config import settings
from app.models.schemas import Paper

log = logging.getLogger(__name__)

class OpenAIService:
    """Service for generating responses using OpenAI GPT-4o."""

    # Token estimation constant (approximate)
    CHARS_PER_TOKEN = 4

    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL
        self.max_tokens = settings.OPENAI_MAX_TOKENS
        self.temperature = settings.OPENAI_TEMPERATURE

    def build_context(self, papers: List[Paper], max_tokens: int = 1000) -> str:
        """
        Build optimized context string from papers.
        
        Strategy:
        - All papers: metadata + abstract
        - Top X (default 10) papers: full text (truncated to 10K chars each)
        - Stops at max_tokens limit
        
        Args:
            papers: List of Paper objects
            max_tokens: Maximum tokens for context
            
        Returns:
            Formatted context string
        """
        context_parts = []
        estimated_tokens = 0

        for idx, paper in enumerate(papers, 1):
            # Build paper context
            paper_context = self._format_paper_context(idx, paper, include_full_text=(idx <= 10)) # I need to move the 10 to config

            # Check token limit
            paper_tokens = len(paper_context) // self.CHARS_PER_TOKEN

            if estimated_tokens + paper_tokens > max_tokens:
                log.warning(f"Context limit reached at paper {idx}/{len(papers)}")
                break

            context_parts.append(paper_context)
            estimated_tokens += paper_tokens

        log.info(f"Built context from {len(context_parts)} papers (~{estimated_tokens} tokens)")
        return "\n".join(context_parts)
