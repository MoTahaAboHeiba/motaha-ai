"""Load text documents from the knowledge base."""

from __future__ import annotations

import logging
from pathlib import Path

import fitz

logger = logging.getLogger(__name__)
SUPPORTED_SUFFIXES = {".md", ".pdf"}


def iter_documents(root: Path):
    """Yield ``(path, text)`` pairs for supported knowledge-base files."""
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in SUPPORTED_SUFFIXES:
            continue

        if path.suffix.lower() == ".md":
            text = path.read_text(encoding="utf-8")
        else:
            with fitz.open(path) as document:
                text = "\n\n".join(page.get_text() for page in document)

        if not text.strip():
            logger.warning("No extractable text found in %s", path)
            continue
        yield path, text