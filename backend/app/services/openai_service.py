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

    def build_context(self, papers: List[Paper], max_tokens: int | None = None) -> str:
        """
        Build optimized context string from papers.
        
        Strategy:
        - All papers: metadata + abstract
        - Top X (default 10) papers: full text (truncated to 10K chars each)
        - Stops at max_tokens limit
        
        Args:
            papers: List of Paper objects
            max_tokens: Maximum tokens for context. Defaults to
                        settings.MAX_CONTEXT_TOKENS so the full configured
                        budget is used when not overridden by callers.
            
        Returns:
            Formatted context string
        """
        # Default to MAX_CONTEXT_TOKENS (configured as 120 000) so that
        # callers that don't specify an override get the full budget.
        if max_tokens is None:
            max_tokens = settings.MAX_CONTEXT_TOKENS

        context_parts = []
        estimated_tokens = 0

        for idx, paper in enumerate(papers, 1):
            # Build paper context
            paper_context = self._format_paper_context(idx, paper, include_full_text=(idx <= settings.FULL_TEXT_PAPER_LIMIT)) # I moved the 10 papers max to config so that it is easier to configure

            # Check token limit
            paper_tokens = len(paper_context) // self.CHARS_PER_TOKEN

            if estimated_tokens + paper_tokens > max_tokens:
                log.warning(f"Context limit reached at paper {idx}/{len(papers)}")
                break

            context_parts.append(paper_context)
            estimated_tokens += paper_tokens

        log.info(f"Built context from {len(context_parts)} papers (~{estimated_tokens} tokens)")
        return "\n".join(context_parts)
    
    def _format_paper_context(self, index: int, paper: Paper, include_full_text: bool = True) -> str:
        """
        Format a single paper for context with section-level citation support.

        Args:
            index: Paper index for labeling (e.g., [1], [2], etc.)
            paper: Paper object containing metadata and content
            include_full_text: Whether to include full text (truncated) or just abstract
        """
        lines = [
            f"\n--- Paper [{index}] ---",
            f"Title: {paper.title}"
        ]

        if paper.authors:
            authors_str = ", ".join(paper.authors[:5])
            if len(paper.authors) > 5:
                authors_str += " et al."
            lines.append(f"Authors: {authors_str}")

        if paper.year:
            lines.append(f"Year: {paper.year}")

        if paper.abstract:
            lines.append(f"Abstract: {paper.abstract}")
        
        # Format sections with visible headers for section-level citations
        if include_full_text and paper.sections:
            # If paper has structured sections, format each with [Section: Name] header
            for section in paper.sections:
                section_title = section.get("title", "Section")
                section_content = section.get("content", "")
                # Truncate each section to 5k chars to respect token budget
                truncated_content = section_content[:5000]
                lines.append(f"\n[Section: {section_title}]\n{truncated_content}")
        elif include_full_text and paper.full_text:
            # Fallback to merged full_text if no structured sections available
            full_text = paper.full_text[:settings.FULL_TEXT_TRUNCATION_CHARS]
            lines.append(f"Full Text: {full_text}")

        return "\n".join(lines)
    
    @staticmethod
    def build_system_prompt() -> str:
        """
        Build the system prompt for LLM with section-level citation support.
        """
        return """You are a medical research assistant helping researchers understand scientific literature.

        Your task is to answer questions based ONLY on the provided research papers. Follow these rules strictly:

        1. CITATION REQUIREMENT:
        - Cite every claim using inline citations with section specification: [1: Methods], [1: Results], etc.
        - Format is now [paper_number: SectionName] to cite specific sections within papers
        - Multiple citations can be combined: [1: Methods], [5: Results]
        - When papers lack sections, use basic format: [1], [2]
        - The citation number corresponds to the paper number in the context
        - DO NOT make claims without citations

        2. ANSWER STRUCTURE:
        - Organize your answer into logical categories when appropriate
        - Categories might include: Biological Mechanism, Clinical Evidence, Therapeutic Applications, etc.
        - Provide a brief summary at the start if the answer is complex
        - Use clear, scientific language appropriate for medical researchers

        3. ACCURACY:
        - Answer ONLY based on the provided papers
        - If the papers don't contain enough information, explicitly state this
        - Do not use general medical knowledge not present in the papers
        - If papers conflict, present both views with citations

        4. FORMAT:
        - Use markdown formatting for readability
        - Use bullet points for lists
        - Use **bold** for key terms
        - Keep paragraphs concise

        Example response format:
        **Summary**: GLP-1 is a peptide hormone involved in glucose regulation [1: Introduction, 2: Results].

        **Biological Mechanism**:
        GLP-1 (glucagon-like peptide-1) is secreted by intestinal L-cells in response to food intake [1: Methods]. It enhances insulin secretion in a glucose-dependent manner [2: Results, 3: Discussion].

        **Clinical Applications**:
        GLP-1 receptor agonists are used in treating type 2 diabetes [4: Conclusions, 5: Methods].
        """

    def _build_user_message(self, query: str, context: str) -> str:
        """Build the user message with context and query."""
        return f"""Papers to reference:
        {context}

        Question: {query}

        Please answer the question based on the papers provided above. Remember to use inline citations.
        """
    
    def _build_user_prompt(self, query: str, context: str) -> str:
        """
        Build the user message with context and query.

        Args:
            query: User's natural language question
            context: Formatted context string from papers

        Returns:
            Combined user prompt string
        """
        return f"""Papers to reference:
        {context}

        Question: {query}

        Please answer the question based on the papers provided above. Remember to use inline citations.
        """
    
    async def generate_response_stream(
        self,
        query: str,
        papers: List[Paper],
        conversation_history: list[dict] | None = None
    ) -> AsyncGenerator[str, None]: 
        """
        Generate streaming response from OpenAI.
        
        Args:
            query: User's question
            papers: List of papers to use as context
            conversation_history: Previous conversation messages
            
        Yields:
            Response chunks as they are generated
        """
        try:
            # Build context and messages
            context = self.build_context(papers)
            messages = self._build_messages(query, context, conversation_history)

            # Stream response
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                stream=True
            )

            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as err:
            log.error(f"OpenAI streaming failed: {str(err)}", exc_info=True)
            raise

    async def generate_response(self, 
        query: str, 
        papers: List[Paper],
        conversation_history: list[dict] | None = None
    ) -> str:
        """
        Generate complete (non-streaming) response from OpenAI.
        
        Args:
            query: User's question
            papers: List of papers to use as context
            conversation_history: Previous conversation messages
            
        Returns:
            Complete response text
        """
        try:
            # Build context and messages
            context = self.build_context(papers)
            messages = self._build_messages(query, context, conversation_history)

            # Get response
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )

            return response.choices[0].message.content or ""
        
        except Exception as err:
            log.error(f"OpenAI generation failed: {str(err)}", exc_info=True)
            raise
        
    def _build_messages(
        self,
        query: str, 
        context: str, 
        conversation_history: list[dict] | None
    ) -> list[dict]:
        """
        Build messages list for OpenAI API.
        
        Args:
            query (str): User's question
            context (str): Formatted context from papers 
            conversation_history: Previous conversation messages
            
        Returns:
            List of messages for OpenAI API
        """
        messages = [
            {"role": "system", "content": self.build_system_prompt()}
        ]

        if conversation_history:
            messages.extend(conversation_history)
        
        messages.append({
            "role": "user",
            "content": self._build_user_message(query, context)
        })

        return messages
    
    @staticmethod
    def extract_citations(response_text: str) -> List[int]:
        """
        Extract citation numbers from response text.

        Args:
            response_text: Generated response text with citations.

        Returns:
            Sorted list of unique citation numbers
        """
        # Match patterns: [1], [2,3], [1,2,3]
        citation_pattern = r'\[(\d+(?:,\d+)*)\]'
        matches = re.findall(citation_pattern, response_text)

        # Extract and deduplicate numbers
        citations = set()
        for match in matches:
            numbers = (int(n.strip()) for n in match.split(','))
            citations.update(numbers)

        return sorted(citations)