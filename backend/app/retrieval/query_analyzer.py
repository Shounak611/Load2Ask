import re
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class ParsedQueryConstraints(BaseModel):
    document_id: Optional[str] = None
    page_number: Optional[int] = None
    source_type: Optional[str] = None
    filename: Optional[str] = None
    url: Optional[str] = None
    section: Optional[str] = None


class AnalyzedQuery(BaseModel):
    original_query: str
    rewritten_query: str
    expanded_queries: List[str]
    intent: str  # factual, summary, comparison, procedural, general
    entities: List[str]
    keywords: List[str]
    constraints: ParsedQueryConstraints


class QueryAnalyzer:
    """Analyzes user queries, resolves conversational follow-ups, extracts metadata constraints, and expands search terms."""

    @staticmethod
    def extract_constraints(query: str) -> ParsedQueryConstraints:
        """Extract explicit page numbers, document names, or source filters from user prompt text."""
        constraints = ParsedQueryConstraints()

        # Page number pattern: "page 12", "p. 5", "page #10"
        page_match = re.search(r'\b(?:page|p\.?)\s*#?\s*(\d+)\b', query, re.IGNORECASE)
        if page_match:
            constraints.page_number = int(page_match.group(1))

        # Source type pattern: "pdf", "docx", "website", "image", "csv"
        for stype in ["pdf", "txt", "docx", "pptx", "csv", "xlsx", "json", "markdown", "html", "web", "image"]:
            if re.search(r'\b' + stype + r'\b', query, re.IGNORECASE):
                constraints.source_type = stype
                break

        return constraints

    @classmethod
    def resolve_conversational_query(
        cls,
        current_query: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        Resolve follow-up questions using prior conversation context.
        Example flow:
          1. "What is TCP?" -> TCP
          2. "What are its advantages?" -> "What are the TCP advantages?"
          3. "Compare that with UDP." -> "Compare TCP with UDP."
          4. "Which one is faster?" -> "Which one of TCP and UDP is faster?"
        """
        if not conversation_history:
            return current_query

        # Check for pronouns or referential expressions
        pronoun_pattern = re.compile(r'\b(it|its|they|their|them|this|that|these|those)\b', re.IGNORECASE)
        which_pattern = re.compile(r'\b(which one|which is|which|the former|the latter|both)\b', re.IGNORECASE)

        has_pronoun = pronoun_pattern.search(current_query)
        has_which = which_pattern.search(current_query)

        if not has_pronoun and not has_which:
            return current_query

        # Gather previous user queries to extract mentioned entities
        user_queries = [
            msg.get("content", "").strip()
            for msg in conversation_history
            if msg.get("role") == "user" and msg.get("content")
        ]

        if not user_queries:
            return current_query

        # Collect key entities from past user turns (capitalized terms, acronyms, or non-stop nouns)
        past_entities = []
        stopwords = {"what", "is", "are", "the", "a", "an", "of", "in", "on", "for", "to", "and", "or", "how", "why", "can", "tell", "me", "about", "compare", "with", "advantages", "disadvantages"}

        for uq in user_queries:
            # Match uppercase acronyms or words like TCP, UDP, RAG, etc.
            acronyms = re.findall(r'\b[A-Z0-9]{2,}\b', uq)
            for acr in acronyms:
                if acr not in past_entities:
                    past_entities.append(acr)
            # Clean subject phrase
            subj_clean = re.sub(r'^(what|how|why|where|when|who|is|are|tell me about|explain|compare)\s+(is|are|the|a|an)?\s*', '', uq, flags=re.IGNORECASE).strip('? .!')
            if subj_clean and len(subj_clean) > 2 and subj_clean not in past_entities:
                past_entities.append(subj_clean)
            words = [w.strip('?') for w in subj_clean.split() if w.lower() not in stopwords and len(w) > 2]
            for w in words:
                if w not in past_entities and w.upper() not in past_entities:
                    past_entities.append(w)


        if not past_entities:
            return current_query

        resolved = current_query

        if has_pronoun:
            # Replace pronouns with primary recent entity
            primary_entity = past_entities[0]
            resolved = pronoun_pattern.sub(primary_entity, resolved)

        if has_which:
            # Handle "Which one", "Which is", etc. using recent entity list (e.g. TCP and UDP)
            if len(past_entities) >= 2:
                entities_str = " and ".join(past_entities[:2])
                resolved = re.sub(r'\bwhich one\b', f"which one of {entities_str}", resolved, flags=re.IGNORECASE)
                resolved = re.sub(r'\bwhich is\b', f"which of {entities_str} is", resolved, flags=re.IGNORECASE)
            elif len(past_entities) == 1:
                resolved = re.sub(r'\bwhich one\b', f"which option for {past_entities[0]}", resolved, flags=re.IGNORECASE)

        return resolved


    @classmethod
    def analyze(
        cls,
        user_query: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> AnalyzedQuery:
        """Full query understanding, rewriting, expansion, and constraint extraction."""
        rewritten = cls.resolve_conversational_query(user_query, conversation_history)
        constraints = cls.extract_constraints(user_query)

        # Detect intent
        q_lower = rewritten.lower()
        if any(w in q_lower for w in ["summarize", "summary", "overview"]):
            intent = "summary"
        elif any(w in q_lower for w in ["compare", "difference", "vs", "versus"]):
            intent = "comparison"
        elif any(w in q_lower for w in ["how to", "steps", "procedure"]):
            intent = "procedural"
        else:
            intent = "factual"

        # Keywords extraction (non-stopwords)
        stopwords = {"what", "is", "are", "the", "a", "an", "of", "in", "on", "for", "to", "and", "or", "how", "why", "can", "tell", "me", "about", "page"}
        words = re.findall(r'\b[a-zA-Z0-9_-]{2,}\b', rewritten)
        keywords = [w for w in words if w.lower() not in stopwords]

        # Query Expansion: generate alternative phrasing
        expanded = [rewritten]
        if keywords:
            kw_string = " ".join(keywords)
            if kw_string.lower() != rewritten.lower():
                expanded.append(kw_string)

        return AnalyzedQuery(
            original_query=user_query,
            rewritten_query=rewritten,
            expanded_queries=expanded,
            intent=intent,
            entities=keywords[:5],
            keywords=keywords,
            constraints=constraints,
        )
