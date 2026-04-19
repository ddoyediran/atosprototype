import logging
import asyncio
import re
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
            #title = self._extract_text(article, './/front/article-meta/title-group/article-title') or "Untitled"
            title = self._extract_title(article)
            journal = self._extract_text(article, './/front/journal-meta/journal-title-group/journal-title')
            authors = self._extract_authors(article)
            year = self._extract_year(article)
            
            # Extract content
            abstract = self._extract_text(article, './/front/article-meta/abstract')
            # Extract_full_text now returns (sections_list, merged_text) tuple
            sections, full_text = self._extract_full_text(article)

            # Extract abbreviations using already extracted full text.
            abbreviations = self._extract_abbreviations(article, full_text)
            
            # Build URL
            url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/" if pmcid else None
            
            # Pass extracted sections to Paper constructor citations
            return Paper(
                pmid=pmid or pmcid or "Unknown",
                pmc_id=pmcid,
                title=title,
                authors=authors,
                journal=journal,
                year=year,
                abstract=abstract,
                sections=sections,
                full_text=full_text,
                doi=doi,
                url=url,
                abbreviations=abbreviations,
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
                
            # if id_type in ('pmc', 'pmcid'):
            #     pmcid = f"PMC{text}"
            if id_type in ('pmc', 'pmcid'):
                # Remove any existing PMC prefix to avoid duplication
                text_clean = text.replace('PMC', '').strip()
                pmcid = f"PMC{text_clean}"
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
    
    def _extract_title(self, article: ET.Element) -> str:
        """
        Extract title with fallback strategies for different JATS formats.
        
        Newer JATS XML may wrap article-title content in inline elements like
        <italic> or <sub>, so itertext() is used throughout. Tries multiple
        common title locations in order of preference.

        Args:
            article (ET.Element): XML Element containing article metadata
        
        Returns:
            Title of the paper, or "Untitled" if none found.
        """
        # 1. Standard JATS location
        title = self._extract_text(
            article, './/front/article-meta/title-group/article-title'
        )

        # 2. Without title-group wrapper (some older JATS versions)
        if not title:
            title = self._extract_text(
                article, './/front/article-meta/article-title'
            )
        
        # 3. Alternative title
        if not title:
            title = self._extract_text(
                article, './/front/article-meta/title-group/alt-title'
            )

        # 4. Subtitle as last resort before giving up
        if not title:
            title = self._extract_text(
                article, './/front/article-meta/title-group/subtitle'
            )

        # 5. Search anywhere in <front> for article-title
        # Handles non-standard nesting
        if not title:
            el = article.find('.//front//article-title')
            if el is not None:
                title = "".join(el.itertext()).strip() or None

        return title or "Untitled"
    
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
        
        Handles both legacy JATS (pub-type attribute) and modern JATS 1.2+
        (date-type attribute) so that papers using either schema are covered.

        Tries multiple date elements in order of preference:
        1. Electronic publication date  (epub / epublish / electronic)
        2. Print publication date       (ppub / print / collection)
        3. Generic "pub" date-type      (common in modern JATS)
        4. Any pub-date element         (catch-all fallback)
        5. Copyright year               (last resort)
        
        Args:
            article (ET.Element): XML Element containing article metadata
            
        Returns:
            int | None: Publication year as integer, or None if not found or
                       if parsing fails
        """
        # Helper: safely parse year text from a pub-date element
        def _year_from(pub_date: ET.Element) -> int | None:
            year_tag = pub_date.find('year')
            if year_tag is not None and year_tag.text:
                try:
                    return int(year_tag.text.strip())
                except ValueError:
                    pass
            return None

        # Both legacy (pub-type) and modern JATS 1.2+ (date-type) are checked
        # together so we don't need separate loops for each schema version.
        EPUB_TYPES  = {'epub', 'epublish', 'electronic'}
        PPUB_TYPES  = {'ppub', 'print', 'collection'}
        PUB_TYPES   = {'pub'}  # modern JATS catch-all

        epub_year = ppub_year = pub_year = any_year = None

        #for pub_date in article.findall('..//front/article-meta/pub-date'):
        for pub_date in article.findall('.//front/article-meta/pub-date'):
            # Read whatever attribute is present (legacy vs modern JATS)
            attr_val = (
                pub_date.get('pub-type') or
                pub_date.get('date-type') or
                ''
            ).lower()

            y = _year_from(pub_date)
            if y is None:
                continue

            if attr_val in EPUB_TYPES and epub_year is None:
                epub_year = y
            elif attr_val in PPUB_TYPES and ppub_year is None:
                ppub_year = y
            elif attr_val in PUB_TYPES and pub_year is None:
                pub_year = y
            elif any_year is None:
                any_year = y # Catch-all: first pub-date with a year

        # Return in priority order
        year = epub_year or ppub_year or pub_year or any_year
        if year:
            return year

        # Last resort: copyright year in permission block
        if permissions := article.find('.//front/article-meta/permissions'):
            if copyright_year := permissions.find('copyright-right'):
                if copyright_year.text:
                    try:
                        return int(copyright_year.text.strip())
                    except ValueError:
                        pass

        return None
    
    def _extract_long_form(self,candidate: str, acronym: str) -> str | None:
            """
            Extract and validate a minimal long form using backward character
            alignment (Schwartz-Hearst style) from text before (ABBR).
            """
            text = candidate.strip().rstrip(" ,;:-")
            short = "".join(ch for ch in acronym.upper() if ch.isalnum())
            if not text or len(short) < 2:
                return None

            short_idx = len(short) - 1
            first_match_idx = -1

            for text_idx in range(len(text) - 1, -1, -1):
                ch = text[text_idx]
                if not ch.isalnum():
                    continue
                if ch.upper() == short[short_idx]:
                    # If a match is in the middle of a token, anchor it to the
                    # previous acronym letter via the token's first character.
                    token_start = text_idx
                    while token_start > 0 and text[token_start - 1].isalnum():
                        token_start -= 1
                    in_middle_of_token = token_start < text_idx
                    if in_middle_of_token and short_idx > 0:
                        if text[token_start].upper() != short[short_idx - 1]:
                            continue

                    if short_idx == 0:
                        first_match_idx = text_idx
                        break
                    short_idx -= 1

            if first_match_idx < 0:
                return None

            # Expand to full token containing the first matched character.
            start = first_match_idx
            while start > 0 and text[start - 1].isalnum():
                start -= 1

            long_form = text[start:].strip(" ,;:-")
            if not long_form:
                return None

            if "\n" in long_form:
                return None

            words = re.findall(r"[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*", long_form)
            if len(words) < 2 or len(words) > 8:
                return None

            short = "".join(ch for ch in acronym.upper() if ch.isalnum())
            first_alnum = next((ch.upper() for ch in long_form if ch.isalnum()), None)
            if not first_alnum or first_alnum != short[0]:
                return None

            if len(long_form) <= len(acronym) or len(long_form) <= 3:
                return None

            last_word = re.findall(r"[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*", long_form)
            if not last_word:
                return None

            last_word_text = last_word[-1]
            last_letter = short[-1]
            if last_letter not in last_word_text.upper():
                return None

            return long_form

    def _extract_abbreviations(self, article: ET.Element, full_text: str | None = None) -> dict[str, str]:
        """
        Extract abbreviation definitions from the article.

        JATS XML stores abbreviations in <def-list> elements whose @list-type
        attribute equals "abbrev", or inside <glossary> sections. Each entry
        is a <def-item> with a <term> (the short form) and a <def> (the
        expanded form).

        Fallback: also scans <abbrev> inline elements that carry an explicit
        <def> child, which some publishers use for in-text abbreviation markup.

        Args:
            article (ET.Element): Full article XML element.
            full_text (str | None): Pre-extracted merged body text.

        Returns:
            dict[str, str]: Mapping of abbreviation -> expansion,
                            e.g. {"GLP-1": "Glucagon-like peptide-1"}.
                            Empty dict if none found.
        """
        abbrevs: dict[str, str] = {}

        # 1. <def-list list-type="abbrev"> anywhere in article
        for def_list in article.findall('.//def-list'):
            if def_list.get('list-type', '').lower() in ('abbrev', 'abbreviations', 'abbreviation'):
                for def_item in def_list.findall('def-item'):
                    term_el = def_item.find('term')
                    def_el = def_item.find('def')
                    if term_el is not None and def_el is not None:
                        term = "".join(term_el.itertext()).strip()
                        defn = "".join(def_el.itertext()).strip()
                        if term and defn:
                            abbrevs[term] = defn

        # 2. <glossary> sections (some publishers use this)
        for glossary in article.findall('.//glossary'):
            for def_item in glossary.findall('.//def-item'):
                term_el = def_item.find('term')
                def_el = def_item.find('def')
                if term_el is not None and def_el is not None:
                    term = "".join(term_el.itertext()).strip()
                    defn = "".join(def_el.itertext()).strip()
                    if term and defn and term not in abbrevs:
                        abbrevs[term] = defn

        # 3. Inline <abbrev> elements with explicit <def> child
        for abbrev_el in article.findall('.//abbrev'):
            def_el = abbrev_el.find('def')
            if def_el is not None:
                term = "".join(abbrev_el.itertext()).strip()
                # itertext on abbrev includes the def text; get only the
                # abbrev's direct text to avoid duplication
                term = abbrev_el.text.strip() if abbrev_el.text else term
                defn = "".join(def_el.itertext()).strip()
                if term and defn and term not in abbrevs:
                    abbrevs[term] = defn

        # 4. Pattern matching in full text for phrases like "Full phrase (ABBR)" or "Full phrase(ABBR)"
        # Use abstract and full_text to find acronyms that follow common patterns.
        all_text_parts = []

        # Keep abstract text in regex input (full-text sections exclude abstract).
        if abstract_el := article.find('.//front/article-meta/abstract'):
            abstract_title_el = abstract_el.find('./title')
            abstract_title = "".join(abstract_title_el.itertext()).strip() if abstract_title_el is not None else ""

            abstract_paras = []
            for p in abstract_el.findall('.//p'):
                p_text = "".join(p.itertext()).strip()
                if p_text:
                    abstract_paras.append(p_text)

            if abstract_paras:
                abstract_body = "\n".join(abstract_paras)
                if abstract_title:
                    all_text_parts.append(f"{abstract_title}:\n{abstract_body}")
                else:
                    all_text_parts.append(abstract_body)
            elif abstract_title:
                all_text_parts.append(abstract_title)

        # Reuse already extracted full_text to avoid duplicate section traversal.
        if full_text:
            all_text_parts.append(full_text)

        all_text = "\n\n".join(all_text_parts)
        
        # Match patterns: "Full phrase (ABBR)" or "Full phrase(ABBR)"
        # Group 1: Full form (words separated by spaces, starts with capital)
        # Group 2: Abbreviation (capitals, numbers, hyphens)
        # Limited to single lines to avoid capturing across paragraphs/sections
        pattern = r'([A-Z0-9][A-Za-z0-9\s\-/,]{2,100}?)\s*\(([A-Z0-9][A-Z0-9\-]*[A-Z0-9]?)\)'
        
        # Track which abbreviations we've already found - only accept FIRST match for each abbr
        found_abbrs = set()
        
        for match in re.finditer(pattern, all_text):
            candidate_full_form = match.group(1).strip()
            abbr = match.group(2).strip().upper()

            # Skip if we've already found this abbreviation (first match wins)
            if abbr in found_abbrs or abbr in abbrevs:
                continue

            # Recover a minimal long form nearest the parentheses.
            full_form = self._extract_long_form(candidate_full_form, abbr)
            if not full_form:
                continue

            # Only add if abbreviation is 2+ characters
            if len(abbr) >= 2:
                abbrevs[abbr] = full_form
                found_abbrs.add(abbr)

        if abbrevs:
            log.debug(f"Extracted {len(abbrevs)} abbreviations")

        return abbrevs

    
    def _extract_full_text(self, article: ET.Element) -> tuple[list[dict], str | None]:
        """
        Extract and structure full-text content from the article body.
        
        Iterates through <sec> elements within <body>, extracting section
        titles and text content. Removes duplicate titles from section text
        and filters out trivially short sections (<50 chars). Sections are
        joined with double newlines for readability.
        
        Args:
            article (ET.Element): XML Element containing the full article
            
        Returns:
            tuple: (sections_list, merged_text) where:
                - sections_list: List[dict] with {"title": str, "content": str} for each section
                - merged_text: str | None: Merged full-text or or None if no body
        """
        body = article.find('.//body')
        if body is None:
            return [], None
        
        # Storing sections in structured format
        sections_list = []
        merged_sections = []
        
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
                sections_list.append({"title": sec_title, "content": sec_text})
                merged_sections.append(f"{sec_title}: {sec_text}")
        
        merged_text = "\n\n".join(merged_sections) if merged_sections else None
        return sections_list, merged_text