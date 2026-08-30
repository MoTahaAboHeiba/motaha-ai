"""
app.py
Gradio entrypoint for MoTaha AI.
Terminal aesthetic — matches motahaaboheiba.github.io portfolio identity.
Run locally:
    python app.py
On Hugging Face Spaces the module-level `demo` object is detected
automatically — no launch() needed.
"""

import html
import os
import re

# Gradio 6 enables SSR on Spaces by default (Node proxy -> Python). The Node
# sidecar exits right after boot and takes the app down ("Stopping Node.js
# server..."). Force client-side rendering before Gradio reads the env var.
os.environ["GRADIO_SSR_MODE"] = "false"

import logging
from typing import Generator

import gradio as gr
import spaces

from src.config import settings
from src.pipeline import answer
from src.project_registry import get_all_projects

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

CSS = """
html, body, #root, #app {
    background: #0a0e17 !important;
    height: 100% !important;
    min-height: 0 !important;
}
body {
    margin: 0 !important;
    overflow: hidden !important;
    color: #e2e8f0 !important;
    font-family: Arial, Helvetica, sans-serif !important;
    background: #0a0e17 !important;
}
.gradio-container {
    background: #0a0e17 !important;
    height: 100% !important;
    min-height: 0 !important;
    max-width: 100% !important;
    padding: 0 !important;
    overflow: hidden !important;
}
.gradio-container .main,
.gradio-container .main > div,
.gradio-container > div,
.gradio-container .main > div > div,
.gradio-container .main > div > div > div {
    background: transparent !important;
    min-height: 0 !important;
}
.gradio-container .main,
.gradio-container .main > div,
.gradio-container > div {
    height: 100% !important;
    display: flex !important;
    flex-direction: column !important;
}
.gradio-container .main .panel,
.gradio-container .main .chatbot,
.gradio-container .main [data-testid="chatbot"],
[role="log"],
[aria-label="chatbot conversation"] {
    background: #0a0e17 !important;
    border: 0 !important;
    box-shadow: none !important;
}
.gradio-container .main [role="log"] {
    background: #0a0e17 !important;
    border-radius: 10px !important;
    overflow: hidden !important;
}
footer { display: none !important; }
#portfolio-shell {
    width: 100% !important;
    height: 100% !important;
    min-height: 0 !important;
    margin: 0 auto !important;
    border: 1px solid rgba(34,211,238,0.12) !important;
    border-radius: 12px !important;
    overflow: hidden !important;
    background: #0a0e17 !important;
    box-shadow: 0 0 0 1px rgba(15, 23, 42, 0.8), 0 18px 40px rgba(15, 23, 42, 0.6) !important;
    display: flex !important;
    flex-direction: column !important;
}
#portfolio-shell > div {
    min-height: 0 !important;
}
#portfolio-shell > div:nth-child(2) {
    flex: 1 1 auto !important;
    overflow: hidden !important;
}
#portfolio-header {
    background: #0d1117 !important;
    border-bottom: 1px solid rgba(34,211,238,0.1) !important;
    padding: 8px 20px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: space-between !important;
    flex-shrink: 0 !important;
}
#portfolio-header .brand {
    display: flex !important;
    align-items: center !important;
    gap: 12px !important;
}
.brand-mark {
    color: #22D3EE !important;
    font-size: 10px !important;
    font-weight: 600 !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    font-family: Arial, Helvetica, sans-serif !important;
}
.brand-divider {
    color: #1e3a4a !important;
    font-size: 12px !important;
}
.brand-subtitle {
    color: #64748b !important;
    font-size: 12px !important;
}
.status-pill {
    display: flex !important;
    align-items: center !important;
    gap: 8px !important;
}
.status-dot {
    width: 7px !important;
    height: 7px !important;
    border-radius: 50% !important;
    background: #22D3EE !important;
    display: inline-block !important;
}
.status-text {
    color: #64748b !important;
    font-size: 11px !important;
    font-family: 'Courier New', monospace !important;
}
#portfolio-chatbot {
    background: #0a0e17 !important;
    border: 0 !important;
    border-radius: 0 !important;
    flex: 1 1 auto !important;
    min-height: 0 !important;
    height: auto !important;
    max-height: none !important;
    padding: 16px 20px !important;
    overflow: hidden !important;
    display: flex !important;
    flex-direction: column !important;
    gap: 16px !important;
}
#portfolio-chatbot > div {
    height: 100% !important;
    min-height: 0 !important;
    overflow-y: auto !important;
    scroll-behavior: smooth !important;
}
.portfolio-message-row {
    display: flex !important;
    gap: 12px !important;
    align-items: flex-start !important;
    width: 100% !important;
}
.portfolio-message-row.user {
    justify-content: flex-end !important;
}
.portfolio-message {
    display: flex !important;
    flex-direction: column !important;
    width: 100% !important;
}
.portfolio-message.user {
    align-items: flex-end !important;
}
.portfolio-message.bot {
    align-items: flex-start !important;
}
.portfolio-avatar {
    width: 32px !important;
    height: 32px !important;
    border-radius: 50% !important;
    background: rgba(34,211,238,0.1) !important;
    border: 1px solid rgba(34,211,238,0.3) !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    font-size: 11px !important;
    font-weight: 700 !important;
    color: #22D3EE !important;
    flex-shrink: 0 !important;
    margin-top: 2px !important;
    font-family: 'Courier New', monospace !important;
}
.portfolio-bubble {
    display: inline-block !important;
    max-width: 85% !important;
    padding: 14px 16px !important;
    font-size: 13px !important;
    line-height: 1.7 !important;
    color: #e2e8f0 !important;
    font-family: Arial, Helvetica, sans-serif !important;
    box-sizing: border-box !important;
}
.portfolio-bubble.bot {
    background: #0d1117 !important;
    border: 1px solid rgba(34,211,238,0.08) !important;
    border-left: 2px solid #22D3EE !important;
    border-radius: 0 8px 8px 8px !important;
}
.portfolio-bubble.user {
    background: #0f1e2e !important;
    border: 1px solid rgba(34,211,238,0.15) !important;
    border-right: 2px solid #22D3EE !important;
    border-radius: 8px 0 8px 8px !important;
    max-width: 70% !important;
}
.portfolio-bubble p,
.portfolio-bubble strong,
.portfolio-bubble a,
.portfolio-bubble li,
.portfolio-bubble span {
    color: #e2e8f0 !important;
    font-family: Arial, Helvetica, sans-serif !important;
    line-height: 1.7 !important;
}
.portfolio-bubble strong {
    color: #22D3EE !important;
}
.portfolio-bubble a {
    color: #22D3EE !important;
    text-decoration: none !important;
}
.portfolio-source-row {
    display: flex !important;
    flex-wrap: wrap !important;
    align-items: center !important;
    gap: 6px !important;
    margin-top: 10px !important;
    border-top: 1px solid rgba(34,211,238,0.08) !important;
    padding-top: 10px !important;
}
.portfolio-source-label {
    color: #64748b !important;
    font-size: 10px !important;
    letter-spacing: 0.06em !important;
    text-transform: uppercase !important;
    margin-right: 2px !important;
}
.portfolio-source-link {
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    background: rgba(34,211,238,0.05) !important;
    border: 1px solid rgba(34,211,238,0.2) !important;
    border-radius: 4px !important;
    color: #22D3EE !important;
    text-decoration: none !important;
    font-size: 11px !important;
    padding: 4px 10px !important;
    line-height: 1.4 !important;
    transition: all 0.2s ease !important;
}
.portfolio-source-link:hover {
    border-color: rgba(34,211,238,0.4) !important;
    background: rgba(34,211,238,0.08) !important;
}
#portfolio-composer {
    border-top: 1px solid rgba(34,211,238,0.1) !important;
    background: #0d1117 !important;
    padding: 10px 20px 12px !important;
    gap: 8px !important;
    width: 100% !important;
    flex-shrink: 0 !important;
    display: flex !important;
    align-items: center !important;
}
#portfolio-composer .gr-textbox {
    flex: 1 1 auto !important;
    min-width: 0 !important;
}
#portfolio-composer textarea,
#portfolio-composer .gr-textbox textarea {
    width: 100% !important;
    min-height: 42px !important;
    height: 42px !important;
    background: #0a0e17 !important;
    border: 1px solid rgba(34,211,238,0.15) !important;
    border-radius: 6px !important;
    color: #dfe7f3 !important;
    font-size: 13px !important;
    padding: 10px 14px !important;
    resize: none !important;
    box-shadow: none !important;
}
#portfolio-composer textarea:focus,
#portfolio-composer .gr-textbox textarea:focus {
    border-color: rgba(34,211,238,0.35) !important;
    box-shadow: 0 0 0 2px rgba(34,211,238,0.12) !important;
    outline: none !important;
}
#send-button,
#portfolio-composer button,
.example-pill {
    height: 42px !important;
    min-height: 42px !important;
    line-height: 1.2 !important;
    box-sizing: border-box !important;
    white-space: nowrap !important;
    flex: 0 0 auto !important;
}
#send-button {
    background: #22D3EE !important;
    color: #0a0e17 !important;
    border: none !important;
    border-radius: 6px !important;
    font-size: 14px !important;
    font-weight: 700 !important;
    padding: 0 16px !important;
    min-width: 78px !important;
    width: auto !important;
    max-width: none !important;
    flex-shrink: 0 !important;
    box-shadow: none !important;
}
#send-button:hover {
    background: #67E8F9 !important;
}
#send-button:disabled,
.example-pill:disabled {
    opacity: 0.5 !important;
    cursor: not-allowed !important;
}
button[aria-label*="Clear"],
button[title*="Clear"],
button[aria-label*="Copy"],
button[title*="Copy"],
button[aria-label*="Share"],
button[title*="Share"],
button[aria-label*="copy"],
button[title*="copy"],
button[data-testid="copy-btn"],
button[data-testid="clear-btn"] {
    display: none !important;
}
.example-row {
    display: flex !important;
    flex-wrap: wrap !important;
    gap: 6px !important;
    margin: 6px 0 10px !important;
    flex-shrink: 0 !important;
}
.example-pill {
    background: transparent !important;
    border: 1px solid rgba(34,211,238,0.15) !important;
    border-radius: 4px !important;
    color: #64748b !important;
    font-size: 11px !important;
    line-height: 1.2 !important;
    padding: 0 12px !important;
    min-height: 32px !important;
    height: 32px !important;
    flex: 0 0 auto !important;
    box-shadow: none !important;
}
.example-pill:hover {
    border-color: rgba(34,211,238,0.35) !important;
    color: #22D3EE !important;
}
::-webkit-scrollbar { width: 8px; }
::-webkit-scrollbar-track { background: #0a0e17; }
::-webkit-scrollbar-thumb {
    background: rgba(34,211,238,0.18);
    border-radius: 4px;
}
"""

HEADER_HTML = """
<div id="portfolio-header">
  <div class="brand">
    <span class="brand-mark">// MOTAHA AI</span>
    <span class="brand-divider">|</span>
    <span class="brand-subtitle">Ask me anything about my engineering work</span>
  </div>
  <div class="status-pill">
    <span class="status-dot"></span>
    <span class="status-text">taha@portfolio ~</span>
  </div>
</div>
"""

TERMINAL_HEADER = HEADER_HTML
GITHUB_ICON = ""

# Runs after every history-changing event (submit, send click, example pill
# click) to keep the transcript pinned to the latest message. gr.HTML has no
# built-in autoscroll like gr.Chatbot, and the render function rebuilds the
# node's innerHTML on every update, so any <script> embedded in that markup
# never executes. This is chained as client-side JS via `.then(..., js=...)`
# instead, after the DOM has actually updated.
SCROLL_TO_BOTTOM_JS = """
() => {
    const container = document.querySelector('#portfolio-chatbot');
    if (!container) { return []; }
    const scrollable = container.querySelector(':scope > div') || container;
    requestAnimationFrame(() => {
        scrollable.scrollTop = scrollable.scrollHeight;
    });
    return [];
}
"""


def _build_github_buttons_html() -> str:
    return ""


def _missing_runtime_secrets() -> list[str]:
    return settings.missing_required


def _startup_message() -> str:
    missing = _missing_runtime_secrets()
    if not missing:
        return (
            "Hey, I'm Taha.\n\n"
            "Ask me anything about my engineering work — projects, technical decisions, architecture choices, or what I can bring to your team."
        )
    return (
        "This Space is not fully configured yet.\n\n"
        f"Missing required environment variables: {', '.join(missing)}.\n\n"
        "Add them in your Hugging Face Space settings and redeploy the app."
    )


INITIAL_HISTORY = [{
    "role": "assistant",
    "content": _startup_message(),
}]


def _render_message_content(content: str) -> str:
    safe_content = html.escape(content)
    safe_content = safe_content.replace("\n", "<br>")

    source_label = "You can find it here:"
    if source_label in safe_content:
        prefix, source_block = safe_content.split(source_label, 1)
        source_block = source_block.strip()
        links: list[str] = []
        for token in re.split(r"\s*·\s*", source_block):
            match = re.match(r"^\[([^\]]+)\]\((https?://[^)]+)\)$", token.strip())
            if not match:
                continue
            label, url = match.groups()
            links.append(
                f'<a class="portfolio-source-link" href="{html.escape(url)}" '
                'target="_blank" rel="noopener noreferrer">'
                f'{html.escape(label)}</a>'
            )
        if links:
            return (
                f'{prefix}'
                f'<div class="portfolio-source-row">'
                f'<span class="portfolio-source-label">{source_label}</span>'
                f'{"".join(links)}'
                '</div>'
            )

    def link_repl(match: re.Match[str]) -> str:
        label = match.group(1)
        url = match.group(2)
        return (
            f'<a class="portfolio-source-link" href="{html.escape(url)}" target="_blank" '
            'rel="noopener noreferrer">'
            f'{html.escape(label)}</a>'
        )

    return re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", link_repl, safe_content)


def _render_history(history: list | None) -> str:
    # `history or INITIAL_HISTORY` is wrong here: an empty list is falsy in
    # Python, so a genuinely empty (but valid) history would silently fall
    # back to the startup message instead of rendering nothing. Only None
    # (never initialized) should fall back.
    messages = history if history is not None else INITIAL_HISTORY
    html_parts: list[str] = ['<div class="portfolio-message-list">']

    for item in messages:
        role = str(item.get("role", "assistant")).lower()
        content = str(item.get("content", ""))
        rendered = _render_message_content(content)

        if role == "user":
            html_parts.append(
                '<div class="portfolio-message-row user">'
                '<div class="portfolio-message user">'
                f'<div class="portfolio-bubble user">{rendered}</div>'
                '</div>'
                '</div>'
            )
        else:
            html_parts.append(
                '<div class="portfolio-message-row bot">'
                '<div class="portfolio-avatar">MT</div>'
                '<div class="portfolio-message bot">'
                '<div class="portfolio-bubble bot">'
                f'{rendered}'
                '</div>'
                '</div>'
                '</div>'
            )

    html_parts.append('</div>')
    return "".join(html_parts)


@spaces.GPU(duration=120)
def _submit_prompt(message: str, history: list | None = None):
    if not message or not str(message).strip():
        current = history if history is not None else INITIAL_HISTORY
        return _render_history(current), current, ""

    user_text = str(message).strip()
    next_history = list(history if history is not None else INITIAL_HISTORY)
    next_history.append({"role": "user", "content": user_text})

    missing = _missing_runtime_secrets()
    if missing:
        reply = (
            "This Space is not fully configured yet. "
            f"Missing required environment variables: {', '.join(missing)}. "
            "Add them in the Space settings and redeploy."
        )
        next_history.append({"role": "assistant", "content": reply})
        return _render_history(next_history), next_history, ""

    try:
        reply = "".join(answer(user_text, history=history if history is not None else INITIAL_HISTORY))
    except Exception as exc:
        logger.error("Pipeline error: %s", exc, exc_info=True)
        reply = "Something went wrong on my end. Try again in a moment."

    next_history.append({"role": "assistant", "content": reply})
    return _render_history(next_history), next_history, ""


def _set_example(prompt: str):
    return prompt


with gr.Blocks(fill_height=True) as demo:
    history_state = gr.State(value=INITIAL_HISTORY)

    with gr.Column(elem_id="portfolio-shell"):
        gr.HTML(HEADER_HTML)
        chat_html = gr.HTML(
            _render_history(INITIAL_HISTORY),
            elem_id="portfolio-chatbot",
        )

        with gr.Row(elem_id="portfolio-composer"):
            textbox = gr.Textbox(
                value="",
                placeholder=(
                    "Add the required Space secrets before chatting..."
                    if _missing_runtime_secrets()
                    else "Ask me about my projects, decisions, or background..."
                ),
                show_label=False,
                lines=1,
                max_lines=4,
                interactive=not _missing_runtime_secrets(),
            )
            submit = gr.Button("Send", elem_id="send-button", interactive=not _missing_runtime_secrets())

        with gr.Row(equal_height=True, elem_classes=["example-row"]):
            example_buttons = []
            for prompt in [
                "Who are you?",
                "How does your Lakehouse work?",
                "What certifications do you hold?",
                "Explain your experience in Data Engineering",
                "Explain your experience in AI Engineering",
           
            ]:
                example_btn = gr.Button(
                    prompt,
                    elem_classes=["example-pill"],
                    interactive=not _missing_runtime_secrets(),
                )
                example_buttons.append((example_btn, prompt))

    # Enter key / Send button: fill happens client-side already via the
    # textbox binding, then submit the turn and scroll to the new answer.
    textbox.submit(
        fn=_submit_prompt,
        inputs=[textbox, history_state],
        outputs=[chat_html, history_state, textbox],
    ).then(fn=None, inputs=None, outputs=None, js=SCROLL_TO_BOTTOM_JS)

    submit.click(
        fn=_submit_prompt,
        inputs=[textbox, history_state],
        outputs=[chat_html, history_state, textbox],
    ).then(fn=None, inputs=None, outputs=None, js=SCROLL_TO_BOTTOM_JS)

    # Example pills: previously these only dropped the prompt text into the
    # textbox and stopped, so clicking one did nothing visible until the user
    # manually hit Send. Chained here to fill, submit, and scroll in one
    # click, same as typing the question yourself.
    for example_btn, prompt in example_buttons:
        example_btn.click(
            fn=lambda p=prompt: p,
            inputs=None,
            outputs=[textbox],
        ).then(
            fn=_submit_prompt,
            inputs=[textbox, history_state],
            outputs=[chat_html, history_state, textbox],
        ).then(fn=None, inputs=None, outputs=None, js=SCROLL_TO_BOTTOM_JS)


if __name__ == "__main__":
    # Hugging Face Spaces already provides the public URL.  Creating a second
    # Gradio share tunnel downloads/starts frpc and can terminate the Space
    # after the local server has started.
    is_space = bool(os.environ.get("SPACE_ID"))
    port = int(os.environ.get("PORT", "7862" if not is_space else "7860"))
    demo.launch(
        server_name="0.0.0.0",
        server_port=port,
        share=False,
        ssr_mode=False,
        debug=True,
        show_error=True,
        css=CSS,
        theme=gr.themes.Base(),
    )