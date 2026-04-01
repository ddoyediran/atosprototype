import logging
import asyncio
from functools import partial

from Bio import Entrez
import xml.etree.ElementTree as ET
from typing import List
from app.core.config import settings
from app.models.schemas import Paper

log = logging.getLogger(__name__)


class PubMedService:
    """Service for interacting with PubMed Central API using BioPython."""
    
    def __init__(self):
        """Initialize PubMedService with Entrez configuration.
        
        Configures BioPython's Entrez module with email and tool identification
        from application settings, and sets the maximum number of results to fetch.
        """
        Entrez.email = settings.PUBMED_EMAIL
        Entrez.tool = settings.PUBMED_TOOL
        self.max_results = settings.PUBMED_MAX_RESULTS
    
    async def search_papers(self, keywords: List[str]) -> List[Paper]:
        """
        Search PubMed Central for open-access papers matching keywords.
        
        Args:
            keywords: List of search keywords
            
        Returns:
            List of Paper objects with metadata and full-text content
            
        Raises:
            RuntimeError: If PubMed API fails or returns invalid data
        """
        if not keywords:
            log.warning("No keywords provided for search")
            return []
        
        # Build query with open access filter for legal full-text access
        search_term = " AND ".join(keywords)
        full_query = f"({search_term}) AND open access[filter]"
        
        log.info(f"Searching PMC: {full_query}")
        
        try:
            # Get PMC IDs
            id_list = await self._search_pmc_ids(full_query)
            
            if not id_list:
                log.warning(f"No papers found for: {full_query}")
                return []
            
            log.info(f"Found {len(id_list)} papers, fetching full text...")
            
            # Fetch and parse papers
            papers = await self._fetch_and_parse_papers(id_list)
            
            log.info(f"Successfully retrieved {len(papers)} papers")
            return papers
            
        except Exception as e:
            log.error(f"PubMed search failed: {str(e)}", exc_info=True)
            raise RuntimeError(f"Failed to search PubMed: {str(e)}") from e
    
    async def _search_pmc_ids(self, query: str) -> List[str]:
        """Search PubMed Central for article IDs matching a query.
        
        Executes a blocking Entrez.esearch call in a thread pool to avoid
        blocking the async event loop, then parses the response for PMC IDs.
        
        Args:
            query (str): The search query string formatted for PubMed Central
            
        Returns:
            List[str]: List of PMC article IDs (e.g., ["123456", "789012"])
        """
        loop = asyncio.get_event_loop()
        
        # Run blocking Entrez call in thread pool
        search_handle = await loop.run_in_executor(
            None,
            partial(
                Entrez.esearch,
                db="pmc",
                term=query,
                retmax=self.max_results,
                sort="relevance"
            )
        )
        
        try:
            search_results = Entrez.read(search_handle)
            return search_results.get("IdList", [])
        finally:
            search_handle.close()
    
    async def _fetch_and_parse_papers(self, id_list: List[str]) -> List[Paper]:
        """
        Fetch full XML content for a list of PMC IDs and parse into Paper objects.
        
        Executes a blocking Entrez.efetch call in a thread pool to retrieve
        JATS-formatted XML for all provided IDs, then delegates parsing to
        _parse_pmc_xml.
        
        Args:
            id_list (List[str]): List of PMC article IDs to fetch
            
        Returns:
            List[Paper]: List of parsed Paper objects with extracted metadata
                        and content; excludes articles that fail to parse
        """
        loop = asyncio.get_event_loop()
        
        # Fetch full XML from PMC
        fetch_handle = await loop.run_in_executor(
            None,
            partial(
                Entrez.efetch,
                db="pmc",
                id=",".join(id_list),
                retmode="xml"
            )
        )
        
        try:
            xml_data = fetch_handle.read()
            return self._parse_pmc_xml(xml_data)
        finally:
            fetch_handle.close()
    
    def _parse_pmc_xml(self, xml_data: bytes) -> List[Paper]:
        """
        Parse PubMed Central JATS XML into Paper objects.
        
        Iterates through all <article> elements in the XML document, attempting
        to extract structured data via _extract_paper. Parsing failures for
        individual articles are logged and skipped to maximize data retrieval.
        
        Args:
            xml_data (bytes): Raw XML bytes from PubMed Central efetch response
            
        Returns:
            List[Paper]: List of successfully parsed Paper objects; empty list
                        if XML is invalid or no articles are found
        """
        papers = []
        
        try:
            root = ET.fromstring(xml_data)
            
            for article in root.findall('.//article'):
                try:
                    if paper := self._extract_paper(article):
                        papers.append(paper)
                except Exception as e:
                    log.warning(f"Failed to parse article: {str(e)}")
            
        except ET.ParseError as e:
            log.error(f"XML parsing failed: {str(e)}")
        
        return papers
    
    def _extract_paper(self, article: ET.Element) -> Paper | None:
        """
        Extract structured paper data from a single JATS article XML element.
        
        Coordinates extraction of identifiers, metadata, abstract, and full-text
        content by delegating to specialized helper methods. Returns None if
        extraction fails to ensure robustness.
        
        Args:
            article (ET.Element): XML Element representing a single PubMed Central article
            
        Returns:
            Paper | None: Paper object populated with extracted fields, or None
                         if extraction encounters an error
        """
        try:
            # Extract IDs
            pmcid, pmid, doi = self._extract_ids(article)
            
            # Extract metadata
            title = self._extract_text(article, './/front/article-meta/title-group/article-title') or "Untitled"
            journal = self._extract_text(article, './/front/journal-meta/journal-title-group/journal-title')
            authors = self._extract_authors(article)
            year = self._extract_year(article)
            
            # Extract content
            abstract = self._extract_text(article, './/front/article-meta/abstract')
            full_text = self._extract_full_text(article)
            
            # Build URL
            url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/" if pmcid else None
            
            return Paper(
                pmid=pmid or pmcid or "Unknown",
                pmc_id=pmcid,
                title=title,
                authors=authors,
                journal=journal,
                year=year,
                abstract=abstract,
                full_text=full_text,
                doi=doi,
                url=url
            )
            
        except Exception as e:
            log.error(f"Paper extraction failed: {str(e)}")
            return None
    
    def _extract_ids(self, article: ET.Element) -> tuple[str | None, str | None, str | None]:
        """
        Extract PMCID, PMID, and DOI identifiers from article metadata.
        
        Iterates through <article-id> elements in the JATS XML, matching on
        the pub-id-type attribute to classify and format each identifier.
        
        Args:
            article (ET.Element): XML Element containing article metadata
            
        Returns:
            (tuple): Tuple of (pmcid, pmid, doi)
                - pmcid: Formatted as "PMC{value}" if found
                - pmid: Raw numeric string if found
                - doi: Raw DOI string if found
        """
        pmcid = pmid = doi = None
        
        for article_id in article.findall('.//front/article-meta/article-id'):
            id_type = article_id.get('pub-id-type')
            text = article_id.text
            
            if not text:
                continue
                
            if id_type in ('pmc', 'pmcid'):
                pmcid = f"PMC{text}"
            elif id_type == 'pmid':
                pmid = text
            elif id_type == 'doi':
                doi = text
        
        return pmcid, pmid, doi
    
    def _extract_text(self, article: ET.Element, xpath: str) -> str | None:
        """
        Extract and clean text content from an XML element using XPath.
        
        Uses ElementTree.find() to locate the target element, then concatenates
        all nested text nodes while stripping whitespace. Returns None if the
        element is not found or contains only whitespace.
        
        Args:
            article (ET.Element): Root XML Element to search within
            xpath (str): XPath expression to locate the target element
            
        Returns:
            str | None: Cleaned, stripped text content, or None if not found
        """
        if element := article.find(xpath):
            return "".join(element.itertext()).strip() or None
        return None
    
    def _extract_authors(self, article: ET.Element) -> List[str]:
        """
        Extract author names from the article's contrib-group metadata.
        
        Iterates through <contrib> elements, extracting <surname> and
        <given-names> to format authors as "Given Surname". Skips entries
        missing required name components.
        
        Args:
            article (ET.Element): XML Element containing article metadata
            
        Returns:
            List[str]: List of formatted author names; empty list if none found
        """
        authors = []
        
        for contrib in article.findall('.//front/article-meta/contrib-group/contrib'):
            if name := contrib.find('name'):
                surname = name.find('surname')
                given = name.find('given-names')
                
                if surname is not None and surname.text:
                    author = surname.text
                    if given is not None and given.text:
                        author = f"{given.text} {author}"
                    authors.append(author.strip())
        
        return authors
    
    def _extract_year(self, article: ET.Element) -> int | None:
        """
        Extract publication year from the article's pub-date metadata.
        
        Locates the <year> element within <pub-date> and attempts to parse
        its text content as an integer. Handles missing or malformed values
        gracefully.
        
        Args:
            article (ET.Element): XML Element containing article metadata
            
        Returns:
            int | None: Publication year as integer, or None if not found or
                       if parsing fails
        """
        if pub_date := article.find('.//front/article-meta/pub-date'):
            if year_tag := pub_date.find('year'):
                if year_tag.text:
                    try:
                        return int(year_tag.text)
                    except ValueError:
                        pass
        return None
    
    def _extract_full_text(self, article: ET.Element) -> str | None:
        """
        Extract and structure full-text content from the article body.
        
        Iterates through <sec> elements within <body>, extracting section
        titles and text content. Removes duplicate titles from section text
        and filters out trivially short sections (<50 chars). Sections are
        joined with double newlines for readability.
        
        Args:
            article (ET.Element): XML Element containing the full article
            
        Returns:
            str | None: Formatted full-text content with section headers,
                       or None if no body or substantial sections found
        """
        body = article.find('.//body')
        if body is None:
            return None
        
        sections = []
        
        for sec in body.findall('./sec'):
            # Extract section title
            title_tag = sec.find('title')
            sec_title = "".join(title_tag.itertext()).strip() if title_tag is not None else "Section"
            
            # Extract section text
            sec_text = "".join(sec.itertext()).strip()
            
            # Remove title from beginning if present
            if sec_text.startswith(sec_title):
                sec_text = sec_text[len(sec_title):].strip()
            
            # Only include substantial sections (>50 chars)
            if len(sec_text) > 50:
                sections.append(f"{sec_title}: {sec_text}")
        
        return "\n\n".join(sections) if sections else None