from pydantic import BaseModel, Field, field_validator
from typing import List
from datetime import datetime, timezone


# Message and Conversation Models
class Message(BaseModel):
    """Single message in conversation history."""
    role: str = Field(..., description="Role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")
    timestamp: datetime | None = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator('role')
    @classmethod
    def validate_role(cls, v: str) -> str:
        """Ensure role is either 'user' or 'assistant'."""
        if v not in ('user', 'assistant'):
            raise ValueError("Role must be 'user' or 'assistant'")
        return v

class ConversationHistory(BaseModel):
    """Conversation history for context."""
    messages: List[Message] = Field(default_factory=list, max_length=10)

    def get_recent_messages(self, max_turns: int = 5) -> List[Message]:
        """
        Get the most recent conversation turns.
        
        Args:
            max_turns: Maximum number of turns (user + assistant pairs)
            
        Returns:
            Recent messages (up to max_turns * 2 messages)
        """
        return self.messages[-(max_turns * 2):]

# Request Models
class QueryRequest(BaseModel):
    """Request model for chat queries."""
    query: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="User's natural language question or statement"
    )

    conversation_history: ConversationHistory | None = Field(
        default=None,
        description="Previous conversation context"
    )

    force_new_search: bool = Field(
        default=False,
        description="Force new PubMed search even for follow-ups"
    )

    @field_validator('query')
    @classmethod
    def validate_query(cls, v: str) -> str:
        """Ensure query is not just whitespace."""
        if not v.strip():
            raise ValueError("Query cannot be empty or whitespace only")
        return v.strip()

class PaperSection(BaseModel):
    """Structured section of a paper."""
    title: str = Field(..., description="Section title (e.g. 'Methods')")
    content: str = Field(..., description="Section content")

# Paper and Citation Models
class Paper(BaseModel):
    """Structured paper metadata and content."""

    pmid: str = Field(..., description="PubMed ID")
    pmc_id: str | None = Field(None, description="PubMed Central ID")
    title: str = Field(..., description="Paper title")
    authors: List[str] = Field(default_factory=list, description="List of authors")
    journal: str | None = Field(None, description="Journal name")
    year: int | None = Field(None, description="Publication year")
    abstract: str | None = Field(None, description="Paper abstract")
    sections: List[PaperSection] = Field(default_factory=list, description="Structured sections from paper body with 'title' and 'content' keys")
    full_text: str | None = Field(None, description="Full text if available")
    doi: str | None = Field(None, description="DOI identifier")
    url: str | None = Field(None, description="URL to full paper")

    # Abbreviations map: short form -> expanded form
    # e.g. {"GLP-1": "Glucagon-like peptide-1", "T2D": "Type 2 diabetes"}
    # Populated by PubMedService._extract_abbreviations(); empty dict when none found.
    abbreviations: dict[str, str] = Field(
        default_factory=dict,
        description=(
            "Abbreviations defined in the paper, as a mapping of "
            "short form to expanded form (e.g. {'GLP-1': 'Glucagon-like peptide-1'})."
        )
    )

    def get_citation_text(self, index: int) -> str:
        """
        Generate formatted citation text for reference list.
        
        Args:
            index: Citation number (e.g., 1 for [1])
            
        Returns:
            Formatted citation string
        """
        # Format authors
        authors_str = ", ".join(self.authors[:3])
        if len(self.authors) > 3:
            authors_str += " et al."

        # Build citation
        parts = [f"[{index}]", authors_str]

        if self.year:
            parts.append(f"{self.year}")

        parts.append(f"{self.title}.")

        if self.journal:
            parts.append(f"{self.journal}.")

        return " ".join(parts)
    
class Citation(BaseModel):
    """Citation reference in the response."""

    index: int = Field(..., description="Citation number [1], [2], etc.")
    pmid: str = Field(..., description="PubMed ID being cited")


# Response Models
class QueryResponse(BaseModel):
    """Complete response model for chat queries."""
    query: str = Field(..., description="Original user query")
    answer: str = Field(..., description="Generated answer with inline citations")
    papers: List[Paper] = Field(
        default_factory=list, 
        description="Papers used for this response (5-10 most relevant)")
    citations: List[Citation] = Field(
        default_factory=list,
        description="List of citations used in the answer"
    )
    is_follow_up: bool = Field(
        False,
        description="Whether this was treated as a follow-up question"
    )
    papers_reused: bool = Field(
        False,
        description="Whether papers were reused from previous query"
    )
    processing_time_ms: int | None = Field(
        None,
        description="Total processing time in milliseconds"
    )


class HealthCheckResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API Version")
    timestamp: datetime | None = Field(default_factory=lambda: datetime.now(timezone.utc)) # timezone-aware timestamp

class ErrorResponse(BaseModel):
    """Error response model."""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    detail: dict | None = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc)) # timezone-aware timestamp