"""Search-query disambiguation for genome-edited foods.

The acronym "NGT" collides heavily on the open web with unrelated meanings
(nasogastric tube, natural gas technology, next-generation telescope, …),
so any search query that mentions "NGT" alone tends to drag in irrelevant
medical or industrial results.

This module centralises query construction so that every retrieval call
uses the same disambiguation strategy: expand the acronym to its full
phrase, anchor with food-safety context, and explicitly exclude common
collision domains via Tavily-style negation operators.
"""
from __future__ import annotations


# Phrase expansion + domain anchor.
# - The double-quoted phrase forces the search engine to match it as a unit.
# - The unquoted nouns ("genome-editing", "food", "regulation"…) bias ranking
#   toward food-safety regulatory sources.
DOMAIN_ANCHOR: str = (
    '"new genomic techniques" genome-editing food safety'
)

# Common false-positive domains for the "NGT" acronym.
# Tavily, Google, and most web-search APIs treat "-term" as a negation.
NEGATIONS: str = "-nasogastric -medical -tube -telescope"


def disambiguate(topic: str, intent: str = "") -> str:
    """Build a domain-disambiguated search query.

    Args:
        topic: the user-facing research topic (kept verbatim for ranking).
        intent: optional extra keywords describing what is being looked up
                (e.g. "regulation 2025", "EFSA opinion", "verification").

    Returns:
        A single-line search query suitable for Tavily / RAG / EFSA Journal
        searches. Includes phrase expansion, domain anchor, and negations.
    """
    parts = [topic.strip(), DOMAIN_ANCHOR]
    if intent.strip():
        parts.append(intent.strip())
    parts.append(NEGATIONS)
    return " ".join(p for p in parts if p)


def rag_query(topic: str, intent: str = "") -> str:
    """Query for the RAG vector search (revision, corpus v1).

    Same topic, anchor and intent as disambiguate(), without the web-search negation operators: an
    embedding model does not read "-term" as exclusion, so the operators only add those words' meaning
    to the query vector.
    """
    parts = [topic.strip(), DOMAIN_ANCHOR]
    if intent.strip():
        parts.append(intent.strip())
    return " ".join(p for p in parts if p)
