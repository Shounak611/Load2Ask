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
        Example:
          User: "What is TCP?"
          Assistant: "TCP is Transmission Control Protocol..."
          User: "What are its advantages?"
          Resolved: "What are the advantages of TCP?"
        """
        if not conversation_history:
            return current_query

        # Check for pronouns indicating follow-up: "it", "its", "they", "their", "this", "that", "these", "those"
        pronoun_pattern = re.compile(r'\b(it|its|they|their|them|this|that|these|those)\b', re.IGNORECASE)

        if not pronoun_pattern.search(current_query):
            return current_query

        # Extract last user query and assistant response topic
        last_user_msg = ""
        last_assistant_msg = ""
        for msg in reversed(conversation_history):
            role = msg.get("role", "")
            content = msg.get("content", "").strip()
            if role == "user" and not last_user_msg:
                last_user_msg = content
            elif role in ("assistant", "system") and not last_assistant_msg:
                last_assistant_msg = content
            if last_user_msg and last_assistant_msg:
                break

        if not last_user_msg:
            return current_query

        # Identify key subject/entity from previous user query
        subject_match = re.sub(r'^(what|how|why|where|when|who|is|are|tell me about|explain)\s+(is|are|the|a|an)?\s*', '', last_user_msg, flags=re.IGNORECASE)
        subject = subject_match.rstrip('?').strip()

        if subject:
            # Replace pronouns with explicit subject
            resolved = pronoun_pattern.sub(f"the {subject}", current_query)
            return resolved

        return current_query

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
