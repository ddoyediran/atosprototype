import logging
from typing import List
import re

log = logging.getLogger(__name__)

class KeyWordExtractor:
    """Service for extracting search keywords from natural language queries."""

    # Common stop words to filter out
    STOP_WORDS = frozenset({
        "what", "is", "are", "the", "a", "an", "how", "does", "do", "can", "could",
        "would", "should", "will", "about", "tell", "me", "explain", "describe",
        "definition", "of", "for", "in", "on", "at", "to", "from", "with", "by",
        "this", "that", "these", "those", "it", "its", "be", "been", "being",
        "have", "has", "had", "was", "were", "and", "or", "but", "if", "then",
        "than", "such", "so", "as", "too", "very", "just", "there"
    })

    # Medical/ scientific terms - keep even of they look like stop words
    MEDICAL_TERMS = frozenset({
        "receptor", "protein", "peptide", "hormone", "cell", "gene", "therapy",
        "treatment", "drug", "disease", "syndrome", "disorder", "condition",
        "mechanism", "pathway", "signaling", "enzyme", "molecule", "acid",
        "function", "effect", "response", "level", "expression", "activation",
        "inhibition", "regulation", "metabolism", "synthesis"
    })

    def extract_keywords(self, query: str) -> List[str]:
        """
        Extract relevant search keywords from a natural language query.
        
        Args:
            query: Natural language question from user
            
        Returns:
            List of extracted keywords (max 10)
        """
        if not query or not query.strip():
            return []
        
        # Clean and normalize
        cleaned = self._clean_query(query)

        # Extract different types of keywords
        keywords = set()

        # 1. Extract acronyms (e.g., GLP-1, TNF, IL-6)
        keywords.update(self._extract_acronyms(query))

        # 2. Extract hyphenated terms (e.g., T-cell, beta-blocker)
        keywords.update(self._hyphenated_terms(query))

        # 3. Extract regular words (filtered)
        keywords.update(self._extract_words(cleaned))

        # Maintain order while removing duplicates
        unique_keywords = []
        seen = set()

        for kw in keywords:
            kw_lower = kw.lower()
            if kw_lower not in seen:
                seen.add(kw_lower)

        # Limit to 10 keywords for optimal PubMed results
        final_keywords = unique_keywords[:10]

        log.info(f"Extracted keywords: {final_keywords}")
        return final_keywords
    
    def _clean_query(self, query: str) -> str:
        """
        Clean and normalize query text.

        Args:
            query (str): Raw user query.

        Returns:
            Cleaned/ normalized query of type string.
        """
        # Remove special characters but keep hyphens amd spaces
        cleaned = re.sub(r'[^\w\s\-]', ' ', query)
        # Normalize whitespace
        return ' '.join(cleaned.split())

    def _extract_acronyms(self, query: str) -> set[str]:
        """
        Extract acronyms (e.g., GLP-1, TNF-α, IL-6).
        
        Args:
            query (str): Raw user query.

        Returns:
            Set of acronyms found in the query.
        """
        # Match: 2+ uppercase letters, optionally with numbers/ hyphens
        pattern = r'\b[A-Z]{2,}(?:-\d+)?(?:-[a-zα-ω])?\b'
        return set(re.findall(pattern, query))
    
    def _extract_hyphenated_terms(self, query: str) -> set[str]:
        """
        Extract hyphenated medical terms (e.g., T-cell, beta-blocker).
        
        Args:
            query (str): Raw user query.

        Returns:
            Set of hyphenated terms found in the query.
        """
        # Match: word-word pattern
        pattern = r'\b\w+(?:-\w+)+\b'
        return set(re.findall(pattern, query))
    
    def _extract_words(self, cleaned_query: str) -> set[str]:
        """
        Extract filtered words from cleaned query.
        
        Args:
            cleaned_query (str): Cleaned user query.

        Returns:
            Set of filtered words found in the query.
        """
        words = cleaned_query.split()
        keywords = set()

        for word in words:
            word_lower = word.lower()

            # Keep if: medical term OR (not stop word AND length > 2)
            if (word_lower in self.MEDICAL_TERMS or 
                (word_lower not in self.STOP_WORDS and len(word) > 2)):
                keywords.add(word)

        return keywords
    
    def should_search_new_papers(
            self,
            current_query: str,
            previous_query: str,
            threshold: float = 0.3
    ) -> bool: 
        """
        Determine if new PubMed search is needed based on keyword overlap.
        
        Args:
            current_query: Current user query
            previous_query: Previous user query
            threshold: Minimum keyword overlap to reuse papers (0.3 = 30%)
            
        Returns:
            True if new search needed, False if papers can be reused
        """
        current_keyword = set(kw.lower() for kw in self.extract_keywords(current_query))
        previous_keyword = set(kw.lower() for kw in self.extract_keywords(previous_query))

        if not current_keyword or not previous_keyword:
            return True
        
        # Jaccard similarity: intersection / union
        intersection = len(current_keyword & previous_keyword)
        union = len(current_keyword | previous_keyword)
        similarity = intersection / union if union > 0 else 0

        log.info(
            f"Keyword similarity: {similarity:.2f} "
            f"(current: {current_keyword}, previous: {previous_keyword})"
        )
        
        # If similarity is below threshold, we need to search for new papers
        return similarity < threshold