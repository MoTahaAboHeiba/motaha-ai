"""
src/pipeline.py

End-to-end RAG pipeline: retrieval → scope guard → generation → sources footer.
This is the single entry point called by app.py.

Sources footer strategy
-----------------------
Rather than asking the LLM to format citations (which causes it to cite
section headings like "[Architecture]" instead of project links), the
pipeline appends a programmatic, deduplicated sources footer AFTER the LLM
finishes streaming.  The footer is built directly from the retrieval result
so it is always correct, always clickable.
"""

import logging
from typing import Generator

from src.retrieval.retriever import retrieve
from src.generation.scope_guard import is_sufficient, REFUSAL
from src.generation.generator import generate

logger = logging.getLogger(__name__)


def _build_sources_footer(chunks: list[dict]) -> str:
    """Build a deduplicated markdown sources footer from retrieved chunks.

    Deduplicates by URL so multiple chunks from the same repo produce one link.
    Falls back to plain project name if no URL is available.

    Returns an empty string if no chunks have a project name.
    """
    seen: set[str] = set()
    links: list[str] = []

    for chunk in chunks:
        name = chunk.get("project_name") or chunk.get("source", "")
        url = chunk.get("project_url", "")
        if not name:
            continue
        dedup_key = url if url else name
        if dedup_key in seen:
            continue
        seen.add(dedup_key)
        links.append(f"[{name}]({url})" if url else name)

    if not links:
        return ""
    return "\n\n---\n📎 **Sources:** " + " · ".join(links)


def answer(query: str) -> Generator[str, None, None]:
    """Produce a streamed answer for *query*.

    Yields
    ------
    str
        Incremental text tokens.  The full answer is the concatenation of all
        yielded strings.

    Flow
    ----
    1. Retrieve top-5 chunks via hybrid search (dense + sparse + RRF).
    2. Check scope guard against the top Qdrant cosine score (threshold 0.35).
       Below threshold → yield refusal, return.
    3. Stream LLM response token by token.
    4. Append a programmatic sources footer with clickable GitHub links.
    """
    logger.info("Pipeline invoked — query: %.80s", query)

    result = retrieve(query)
    chunks: list[dict] = result["chunks"]
    top_dense_score: float = result["top_dense_score"]

    if not is_sufficient(top_dense_score):
        logger.info(
            "Scope guard fired (top_dense_score=%.3f < 0.35) — returning refusal",
            top_dense_score,
        )
        yield REFUSAL
        return

    yield from generate(query, chunks)

    # Append guaranteed-correct clickable source links after LLM finishes.
    footer = _build_sources_footer(chunks)
    if footer:
        yield footer
