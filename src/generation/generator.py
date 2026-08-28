"""
src/generation/generator.py

LLM generation with Groq as the primary provider and Gemini as fallback.

Primary  : Groq — model openai/gpt-oss-120b, streaming.
Fallback : Gemini — model gemini-1.5-flash, non-streaming (yields single chunk).

The function is a generator so the caller (pipeline.py / app.py) can stream
tokens directly to the Gradio ChatInterface without buffering.
"""

import logging
from typing import Generator, Any

import warnings

import groq

# google.generativeai emits a FutureWarning about migrating to google-genai.
# The package still works correctly; suppress the warning to keep logs clean.
with warnings.catch_warnings():
    warnings.simplefilter("ignore", FutureWarning)
    import google.generativeai as genai


from src.config import settings
from src.generation.prompt import SYSTEM_PROMPT

logger = logging.getLogger(__name__)

GROQ_MODEL = "openai/gpt-oss-120b"
GEMINI_MODEL = "gemini-1.5-flash"


def generate(
    prompt: str,
    context_chunks: list[dict[str, Any]],
) -> Generator[str, None, None]:
    """Stream an answer grounded in *context_chunks*.

    Parameters
    ----------
    prompt:
        The raw user question.
    context_chunks:
        Ordered list of retrieval dicts, each containing at minimum a ``text``
        key.  Produced by ``retriever.retrieve()``.

    Yields
    ------
    str
        Incremental text tokens (Groq) or the full response (Gemini fallback).
    """
    def _chunk_header(chunk: dict[str, Any]) -> str:
        name = chunk.get("project_name", chunk.get("source", "Unknown"))
        url = chunk.get("project_url", "")
        return f"[Source: {name} | {url}]" if url else f"[Source: {name}]"

    context = "\n---\n".join(
        f"{_chunk_header(chunk)}\n{chunk['text']}"
        for chunk in context_chunks
    )

    system_content = SYSTEM_PROMPT.format(context=context)

    # ── Primary: Groq streaming ──────────────────────────────────────────────
    try:
        client = groq.Groq(api_key=settings.GROQ_API_KEY)
        stream = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_content},
                {"role": "user", "content": prompt},
            ],
            stream=True,
        )
        logger.info("Provider: Groq (%s)", GROQ_MODEL)
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta
        return

    except Exception as exc:
        logger.warning("Groq failed — %s. Falling back to Gemini.", exc)

    # ── Fallback: Gemini non-streaming ───────────────────────────────────────
    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel(GEMINI_MODEL)
    full_prompt = f"{system_content}\n\nUser: {prompt}"
    response = model.generate_content(full_prompt)
    logger.info("Provider: Gemini fallback (%s)", GEMINI_MODEL)
    yield response.text
