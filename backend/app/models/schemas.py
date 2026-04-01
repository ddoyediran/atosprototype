from pydantic import BaseModel, Field, field_validator
from typing import List
from datetime import datetime

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
    full_text: str | None = Field(None, description="Full text if available")
    doi: str | None = Field(None, description="DOI identifier")
    url: str | None = Field(None, description="URL to full paper")

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