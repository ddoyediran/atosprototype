import logging
import time
import json
from typing import AsyncGenerator

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from app.models.schemas import (QueryRequest, QueryResponse, HealthCheckResponse, Paper, Citation)

from app.services.pubmed_service import PubMedService
from app.services.keyword_service import KeyWordExtractor
from app.services.openai_service import OpenAIService
from app.core.config import settings

log = logging.getLogger(__name__)

router = APIRouter()

# Initialize services (using singletons pattern)
pubmed_service = PubMedService()
keyword_extractor = KeyWordExtractor()
openai_service = OpenAIService()

@router.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        Service status and version information
    """
    return HealthCheckResponse(
        status="healthy",
        version=settings.APP_VERSION
    )

@router.post("/chat", response_model=QueryResponse)
async def chat_query(request: QueryRequest):
    """
    Process a chat query and return a structured response with citations.
    
    This is the non-streaming version suitable for simple clients and testing.
    
    Args:
        request: Query request with question and optional conversation history
        
    Returns:
        Complete query response with answer, papers, and citations
        
    Raises:
        HTTPException: 404 error_message if no papers found, 500 for processing errors
    """
    start_time = time.time()

    try:
        log.info(f"Processing query: {request.query}")

        # Determine if this is a follow-up question
        is_follow_up, papers_reused = False, False

        if request.conversation_history and request.conversation_history.messages:
            is_follow_up = True

            # For PoC, we can always search new papers
            # In production (future implementation), implement caching logic here
            need_new_search = True
        else:
            need_new_search = True

        # Extract keywords and search papers
        keywords = keyword_extractor.extract_keywords(request.query)

        if not keywords:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not extract meaningful keywords from query"
            )
        
        papers = await pubmed_service.search_papers(keywords)

        if not papers:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No papers found for keywords: {', '.join(keywords)}"
            )

        # Build conversation history for context
        conversation_history = _build_conversation_history(request)

        # Generate response
        answer = await openai_service.generate_response(
            query=request.query,
            papers=papers,
            conversation_history=conversation_history
        )

        # Extract citations and select cited papers
        cited_papers, citations = _extract_citations_and_papers(answer, papers)

        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)

        return QueryResponse(
            query=request.query,
            answer=answer,
            papers=cited_papers,
            citations=citations,
            is_follow_up=is_follow_up,
            papers_reused=papers_reused,
            processing_time_ms=processing_time_ms
        )

    except HTTPException:
        raise
    except Exception as err:
        log.error(f"Query processing failed: {str(err)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process query: {str(err)}"
        )



# Helper functions
def _build_conversation_history(request: QueryRequest) -> list[dict] | None:
    """
    Build conversation history for OpenAI context.

    Args:
        request: Original query request with conversation history.

    Returns:
        List of messages formatted for OpenAI API or None if no history.
    """
    if not request.conversation_history:
        return None
    
    return [
        {"role": msg.role, "content": msg.content}
        for msg in request.conversation_history.get_recent_messages(
            settings.MAX_CONVERSATION_TURNS
        )
    ]

def _extract_citations_and_papers(answer: str, papers: list[Paper]) -> tuple[list[Paper], list[Citation]]:
    """
    Extract citations from answer and return cited papers.
    
    Args:
        answer: Generated answer with inline citations
        papers: All available papers
        
    Returns:
        Tuple of (cited_papers, citations)
    """
    citation_numbers = openai_service.extract_citations(answer)

    cited_papers = []
    citations = []

    for idx in citation_numbers:
        if 0 < idx <= len(papers):
            paper = papers[idx - 1]
            cited_papers.append(paper)
            citations.append(Citation(index=idx, pmid=paper.pmid))

    # If no citations found, include top 5 anyway
    if not cited_papers:
        cited_papers = papers[:5]
        citations = [
            Citation(index=i+1, pmid=p.pmid)
            for i, p in enumerate(cited_papers)
        ]
    
    return cited_papers, citations