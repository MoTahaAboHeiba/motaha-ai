"""
app.py

Gradio entrypoint for MoTaha AI.

Layout (gr.Blocks):
  ┌─ Header ───────────────────────────────────────────┐
  │  Title + description                               │
  ├─ Projects ─────────────────────────────────────────┤
  │  [View on GitHub] buttons — one per unique project │
  │  Auto-generated from project_registry at startup   │
  ├─ Chat ─────────────────────────────────────────────┤
  │  gr.ChatInterface (streaming)                      │
  └────────────────────────────────────────────────────┘

Run locally:
    python app.py

On Hugging Face Spaces the `demo` object at module level is detected
automatically — no manual launch() needed for HF.
"""

import logging
from typing import Generator

import gradio as gr

from src.pipeline import answer
from src.project_registry import get_all_projects

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


# ── Predict function ─────────────────────────────────────────────────────────

def predict(message: str, history: list) -> Generator[str, None, None]:
    """Stream a response for the Gradio ChatInterface.

    Accumulates partial tokens so Gradio receives a growing string on each
    yield (standard streaming pattern for gr.ChatInterface).
    """
    partial = ""
    try:
        for chunk in answer(message):
            partial += chunk
            yield partial
    except Exception as exc:
        logger.error("Pipeline error: %s", exc, exc_info=True)
        yield "An error occurred while processing your request. Please try again."


# ── GitHub buttons HTML ──────────────────────────────────────────────────────

def _build_github_buttons_html() -> str:
    """Build an HTML row of 'View on GitHub' buttons from the project registry."""
    projects = get_all_projects()
    if not projects:
        return ""

    button_style = (
        "display:inline-flex; align-items:center; gap:6px; "
        "padding:8px 16px; margin:4px 6px; border-radius:8px; "
        "background:#1a1a2e; color:#e0e0ff; font-size:13px; font-weight:500; "
        "text-decoration:none; border:1px solid #3a3a5c; "
        "transition:background 0.2s, border-color 0.2s;"
    )
    hover_js = (
        "onmouseover=\"this.style.background='#2d2d4e';this.style.borderColor='#6c6cad'\" "
        "onmouseout=\"this.style.background='#1a1a2e';this.style.borderColor='#3a3a5c'\""
    )

    github_icon = (
        '<svg height="16" width="16" viewBox="0 0 16 16" fill="currentColor" '
        'xmlns="http://www.w3.org/2000/svg">'
        '<path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17'
        ".55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94"
        "-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87"
        " 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59"
        ".82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27"
        ".68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51"
        ".56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07"
        "-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z\"/>"
        "</svg>"
    )

    buttons_html = "".join(
        f'<a href="{p["url"]}" target="_blank" rel="noopener noreferrer" '
        f'style="{button_style}" {hover_js}>'
        f'{github_icon} {p["display_name"]}'
        f"</a>"
        for p in projects
    )

    return (
        '<div style="padding:8px 0 4px 0; display:flex; flex-wrap:wrap; '
        'align-items:center; gap:2px;">'
        '<span style="font-size:12px; color:#888; margin-right:6px; '
        'white-space:nowrap;">View on GitHub →</span>'
        f"{buttons_html}"
        "</div>"
    )


# ── Gradio layout ─────────────────────────────────────────────────────────────

with gr.Blocks(
    title="MoTaha AI",
    theme=gr.themes.Soft(
        primary_hue="indigo",
        secondary_hue="purple",
    ),
) as demo:

    gr.Markdown(
        "# 🤖 MoTaha AI\n"
        "Ask me about Mohamed Taha's engineering background, "
        "projects, technical decisions, and professional experience."
    )

    # GitHub project buttons — auto-generated from the project registry
    gr.HTML(_build_github_buttons_html())

    gr.ChatInterface(
        fn=predict,
        examples=[
            "Who is Mohamed Taha and what does he specialize in?",
            "How does the E-Commerce Lakehouse handle incremental loads?",
            "What is the architecture of EduMate-RAG?",
            "Why did Mohamed use Medallion Architecture in his Lakehouse projects?",
            "What certifications does Mohamed hold?",
        ],
        cache_examples=False,
    )


if __name__ == "__main__":
    demo.launch(server_port=7860)

