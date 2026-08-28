"""
src/config.py

Central configuration loaded from environment variables via pydantic-settings.
All four keys are required. If any is missing at import time, pydantic raises a
clear ValidationError before any query can be served.
"""

from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    GROQ_API_KEY: str
    GEMINI_API_KEY: str
    QDRANT_API_KEY: str
    QDRANT_URL: str

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


# Singleton — imported by every module that needs config or the KB path.
settings = Settings()

# Canonical path to the knowledge base directory.
# Path(__file__) is src/config.py → .parent is src/ → .parent is project root.
KB_PATH: Path = Path(__file__).parent.parent / "knowledge_base"
