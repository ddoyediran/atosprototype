import logging
import time
import json
import re
from typing import AsyncGenerator

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from app.models.schemas import (QueryRequest, QueryResponse, HealthCheckResponse, Paper, Citation, AbbreviationMeaning, AbbreviationPaperRef)

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

        abbreviation_bank = _build_abbreviation_bank(cited_papers)
        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)

        return QueryResponse(
            query=request.query,
            answer=answer,
            papers=cited_papers,
            citations=citations,
            abbreviation_bank=abbreviation_bank,
            is_follow_up=is_follow_up,
            papers_reused=papers_reused,
            processing_time_ms=processing_time_ms,
            
        )

    except HTTPException:
        raise
    except Exception as err:
        log.error(f"Query processing failed: {str(err)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process query: {str(err)}"
        )

@router.post("/chat/stream")
async def chat_query_stream(request: QueryRequest):
    """
    Process a chat query and stream the response in real-time using SSE.
    
    Server-Sent Events (SSE) are used for streaming with the following event types:
    - keywords: Extracted search keywords
    - papers: Brief info about retrieved papers
    - answer: Streaming answer chunks
    - complete: Final paper details and citations
    - error: Error information
    - done: Stream completion signal
    
    Args:
        request: Query request with question and optional conversation history
        
    Returns:
        StreamingResponse with text/event-stream content type
    """
    return StreamingResponse(
        _stream_response(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no", # Disable nginx buffering if used behind nginx
        }
    )

@router.get("/test/pubmed")
async def test_pubmed_search(query: str = "What is GLP-1?"):
    """
    Test endpoint to verify PubMed integration.
    
    Useful for debugging and validating the PubMed service.
    
    Args:
        query: Search term to test (default: "GLP-1")
        
    Returns:
        Summary of papers found with basic metadata
        
    Raises:
        HTTPException: 500 if PubMed service fails
    """
    try:
        keywords = keyword_extractor.extract_keywords(query)
        papers = await pubmed_service.search_papers(keywords)

        return {
            "query": query,
            "keywords": keywords,
            "papers_found": len(papers),
            "papers": [
                {
                    "pmid": p.pmid,
                    "title": p.title,
                    "authors": p.authors[:3],
                    "year": p.year,
                    "has_abstract": bool(p.abstract),
                    "has_full_text": bool(p.full_text),
                    "url": p.url
                }
                for p in papers[:5] # Show first 5 papers
            ]
        }
    except Exception as err:
        log.error(f"Pubmed test failed: {str(err)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PubMed test failed: {str(err)}"
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


def _normalize_meaning_key(text: str) -> str:
    """
    Normalize text for consistent meaning comparison in abbreviation bank.
    
    Args:
        text (str): The text to normalize.

    Returns:
        str: The normalized text.
    """
    # Treat minor punctuation/hyphen/case differences as same meaning
    t = text.lower().strip()
    t = re.sub(r"[-–—]", " ", t)
    t = re.sub(r"[^a-z0-9\s]", "", t)
    t = re.sub(r"\s+", " ", t)
    return t

def _build_abbreviation_bank(papers: list[Paper]) -> dict[str, list[AbbreviationMeaning]]:
    """
    Consolidate per-paper abbreviation maps into a single cross-paper bank.

    Args:
        papers (list): All papers returned for the current query. Each paper's
                `abbreviations` field is a raw dict of short form -> full form.

    Returns:
        A dict mapping each uppercased abbreviation to a list of one or more
        AbbreviationMeaning objects, each carrying the full form and the
        paper references that use it.
    """
    bank: dict[str, list[AbbreviationMeaning]] = {}

    for idx, paper in enumerate(papers, 1):
        if not paper.abbreviations:
            continue

        for raw_abbr, raw_full in paper.abbreviations.items():
            abbr = raw_abbr.strip().upper()
            full = raw_full.strip()
            if not abbr or not full:
                continue

            if abbr not in bank:
                bank[abbr] = []

            meaning_key = _normalize_meaning_key(full)

            existing = None
            for m in bank[abbr]:
                if _normalize_meaning_key(m.full_form) == meaning_key:
                    existing = m
                    break

            paper_ref = AbbreviationPaperRef(
                paper_index=idx,
                pmid=paper.pmid,
                paper_title=paper.title
            )

            if existing is None:
                bank[abbr].append(
                    AbbreviationMeaning(
                        full_form=full,
                        papers=[paper_ref]
                    )
                )
            else:
                if not any(
                    p.paper_index == paper_ref.paper_index and p.pmid == paper_ref.pmid
                    for p in existing.papers
                ):
                    existing.papers.append(paper_ref)

    return bank

async def _stream_response(request: QueryRequest) -> AsyncGenerator[str, None]:
    """
    Generator function for streaming chat responses via SSE.

    Args:
        request (QueryRequest): Query request with question and optional conversation history

    Returns:
        AsyncGenerator[str, None]: Streaming response chunks.
    
    Yields Server-Sent Events formatted chunks.
    """
    try:
        log.info(f"Starting stream for query: {request.query}")

        # Extract keywords
        keywords = keyword_extractor.extract_keywords(request.query)

        yield _sse_event("keywords", {"keywords": keywords})

        # Search papers
        papers = await pubmed_service.search_papers(keywords)

        if not papers:
            yield _sse_event("error", {"error": "No papers found for this query"})
            return
        
        # Send paper preview
        papers_preview = {
            "count": len(papers),
            "papers": [
                {
                    "pmid": p.pmid,
                    "title": p.title,
                    "authors": p.authors[:3],
                    "year": p.year
                }
                for p in papers[:settings.FULL_TEXT_PAPER_LIMIT]
            ]
        }
        yield _sse_event("papers", papers_preview)

        # Build conversation history
        conversation_history = _build_conversation_history(request)

        # Stream answer
        full_answer = ""
        async for chunk in openai_service.generate_response_stream(
            query=request.query,
            papers=papers,
            conversation_history=conversation_history
        ):
            full_answer += chunk
            yield _sse_event("answer", {"chunk": chunk})

        # Extract citations and prepare complete paper data
        cited_papers, citations = _extract_citations_and_papers(full_answer, papers)
        
        abbreviation_bank = _build_abbreviation_bank(cited_papers)
        
        complete_papers = [
            {
                "pmid": p.pmid,
                "pmc_id": p.pmc_id,
                "title": p.title,
                "authors": p.authors,
                "journal": p.journal,
                "year": p.year,
                "abstract": p.abstract,
                "doi": p.doi,
                "url": p.url,
                "index": citations[i].index,
                "citation": p.get_citation_text(citations[i].index)
            }
            for i, p in enumerate(cited_papers)
        ]

        yield _sse_event(
            "complete",
            {
                "papers": complete_papers,
                "abbreviation_bank": {
                    abbr: [entry.model_dump() for entry in entries]
                    for abbr, entries in abbreviation_bank.items()
                },
            },
        )
        yield _sse_event("done", {})

    except Exception as err:
        log.error(f"Stream error: {str(err)}", exc_info=True)
        yield _sse_event("error", {"error": str(err)})


def _sse_event(event_type: str, data: dict) -> str:
    """
    Format data as Server-Sent Event.

    Args:
        event_type (str): Type of SSE event (e.g., 'papers', 'chunk', 'answer', 'error')
        data (dict): Event data (will be JSON encoded)

    Returns:
        Formatted SSE string
    """
    return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"

