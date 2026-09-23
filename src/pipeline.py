"""
src/pipeline.py

End-to-end RAG pipeline for MoTaha AI.

Query classification runs first. Greetings, introductions, and small
talk receive canned human responses and never touch the retrieval stack.

Genuine career questions go through:
  1. Hybrid retrieval (dense + BM25 + RRF)
  2. Scope guard (cosine threshold 0.35)
  3. LLM generation (Groq primary, Gemini fallback)
    4. Structured source metadata (appended in Python, not by the LLM)
"""

# Reindex required if the Qdrant collection was built with a different embedding
# dimension than the active Gemini embedding model. gemini-embedding-001 emits
# 3072-d vectors, so the collection must be recreated or rebuilt to match.

from __future__ import annotations

import json
import logging
import time
from typing import Generator

from src.classifier import (
    classify,
    get_canned_response,
    get_reliable_answer,
    get_canonical_sources,
    get_canonical_intent,
    CAREER_CATEGORY,
)
from src.generation.generator import generate
from src.generation.scope_guard import REFUSAL, is_sufficient
from src.project_registry import lookup
from src.retrieval.retriever import retrieve
from src.session import ConversationTurn, SessionService

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are MoTaha AI, a helpful assistant for the portfolio website.

Formatting rules:
- Use **bold** for names, technologies, tools, and key terms.
- Use bullet points for lists of skills, technologies, or features.
- Use numbered lists only for sequential steps or ordered items.
- Use short paragraphs. One idea per paragraph. Never write a wall of text.
- Put each paragraph on its own line with a blank line between paragraphs.
- Put each bullet list item on its own line, starting with "- " at the beginning of the line.
- Put a blank line before and after any bullet list.
- Never place list markers inline after a sentence on the same line.
- Never write "sentence: - item" or "sentence- **item**"; start a new line before a bullet list item.
- Never use headers (##, ###) in responses. Paragraphs and bullets only.
- Never use em dashes. Use a comma or a new sentence instead.
"""

def answer(
    query: str,
    history: list | None = None,
) -> Generator[str, None, None]:
    """Yield response tokens for a user query.

    Never yields sources on refusals or non-career queries.
    """
    turns = SessionService.from_gradio_history(history or [])

    request_started = time.perf_counter()

    # ── Step 1: classify ──────────────────────────────────────────────────────
    category = classify(query, history=history)
    logger.info("Chat timing: classify=%.0f ms", (time.perf_counter() - request_started) * 1000)
    if category != CAREER_CATEGORY:
        logger.info("Query classified as %s — returning canned response", category)
        yield get_canned_response(category, query)
        return

    reliable_answer = get_reliable_answer(query)
    canonical_intent = get_canonical_intent(query)
    if reliable_answer:
        logger.info(
            "answer_source=canonical canonical_intent=%s",
            canonical_intent,
        )
        yield reliable_answer
        sources = get_canonical_sources(query)
        if sources:
            yield f"[SOURCES]{json.dumps(sources)}"
        return

    # ── Step 2: retrieve ──────────────────────────────────────────────────────
    augmented_query = SessionService.build_augmented_query(query, turns)
    try:
        retrieval_started = time.perf_counter()
        retrieval_result = retrieve(augmented_query)
        results = retrieval_result["chunks"]
        top_dense_score = retrieval_result["top_dense_score"]
        dense_available = retrieval_result.get("dense_available", True)
        logger.info(
            "Chat timing: retrieval=%.0f ms, chunks=%d",
            (time.perf_counter() - retrieval_started) * 1000,
            len(results),
        )
    except Exception as exc:
        logger.error("Retrieval failed: %s", exc, exc_info=True)
        yield (
            "I ran into a technical issue retrieving context. "
            "Please try again in a moment."
        )
        return

    # ── Step 3: scope guard ───────────────────────────────────────────────────
    sparse_has_evidence = any(chunk.get("score", 0) > 0 for chunk in results)
    if not is_sufficient(top_dense_score) and (dense_available or not sparse_has_evidence):
        logger.info(
            "Scope guard fired — top_dense_score=%.4f below threshold",
            top_dense_score,
        )
        yield REFUSAL
        return

    # ── Step 4: generate ──────────────────────────────────────────────────────
    try:
        generation_started = time.perf_counter()
        first_token = True
        for chunk in generate(query, results, history=history):
            if first_token:
                logger.info(
                    "Chat timing: generation_first_token=%.0f ms, total_before_token=%.0f ms",
                    (time.perf_counter() - generation_started) * 1000,
                    (time.perf_counter() - request_started) * 1000,
                )
                first_token = False
            yield chunk
        logger.info(
            "Chat timing: request_complete=%.0f ms",
            (time.perf_counter() - request_started) * 1000,
        )
    except Exception as exc:
        logger.error("Generation failed: %s", exc, exc_info=True)
        yield (
            "I ran into a technical issue generating a response. "
            "Please try again in a moment."
        )
        return

    # ── Step 5: sources (only on real answers) ────────────────────────────────
    seen: set[str] = set()
    sources: list[dict[str, str]] = []
    for chunk in results:
        source = chunk.get("source")
        if not source:
            continue
        entry = lookup(source)
        dedupe_key = entry.get("url") or source
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        sources.append({
            "label": entry.get("display_name") or source,
            "github_url": entry.get("url", ""),
            "portfolio_url": entry.get("portfolio_url", ""),
            "portfolio_section": entry.get("portfolio_section", ""),
        })

    yield f"[SOURCES]{json.dumps(sources)}"
