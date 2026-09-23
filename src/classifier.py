"""
src/classifier.py

Classifies incoming queries before they reach the RAG pipeline.
Handles greetings, personal introductions, and small talk with canned
human responses so the pipeline only processes genuine career questions.

Categories
----------
GREETING      : hi, hello, hey, good morning, salaam, marhaba, etc.
INTRODUCTION  : "I'm Mostafa", "my name is X", "I'm a recruiter from Y"
SMALL_TALK    : how are you, thanks, nice to meet you, etc.
CAREER        : anything else — goes to the full RAG pipeline
"""

from __future__ import annotations

import re

# ── Constants ─────────────────────────────────────────────────────────────────

CAREER_CATEGORY = "CAREER"


class CanonicalAnswerService:
    """High-precision canonical answers for repetitive portfolio questions."""

    _CANONICAL_ANSWERS = {
        "who_are_you": (
            "I'm Taha, a Data Engineer based in Egypt.\n\n"
            "I build the systems that collect, clean, and organize data "
            "so companies can actually use it. Most businesses have data "
            "spread across multiple places in different formats — my job "
            "is making sure it ends up somewhere reliable, in a shape "
            "that's useful for analytics or AI products.\n\n"
            "I've built data pipelines for retail, e-commerce, and AI "
            "systems. I'm currently looking for full-time Data Engineering "
            "roles in Cairo."
        ),
        "contact": (
            "The best way to reach me is by email at "
            "mohamed-aboheiba@outlook.com.\n\n"
            "You can also find me on LinkedIn at "
            "linkedin.com/in/mohamed-taha-abo-heiba, or browse my "
            "projects and download my CV from my portfolio at "
            "my-portfolio.mohamed-aboheiba.workers.dev."
        ),
        "availability": (
            "I am actively looking for full-time Data Engineering roles "
            "in Cairo, and I am available to start immediately.\n\n"
            "I am open to on-site, hybrid, and remote-within-Egypt "
            "positions. If you want to talk through a role or have a "
            "quick conversation, reach me at "
            "mohamed-aboheiba@outlook.com."
        ),
        "flagship_project": (
            "My flagship project is the Retail Lakehouse Pipeline.\n\n"
            "It is a full-stack data engineering system that ingests from "
            "two disconnected source systems — a PostgreSQL sales database "
            "and Amazon S3 supply chain files — transforms the data through "
            "a dbt Medallion Architecture, and serves a Gold layer that "
            "feeds both Power BI reporting and an AI retrieval layer.\n\n"
            "The pipeline is orchestrated with Apache Airflow running in "
            "Docker, tested with dbt, and built with GitHub Actions CI. "
            "You can see the full project on GitHub or on my portfolio."
        ),
        "projects": (
            "I have worked on several data engineering projects that cover the full lifecycle from ingestion to modeling, orchestration, and analytics.\n\n"
            "**Retail Lakehouse Pipeline** is one of my main projects. It builds an end-to-end retail data platform with PostgreSQL ingestion, Databricks processing, Delta Lake storage, dbt transformations, Airflow orchestration, and a gold layer for analytics.\n\n"
            "**Databricks Lakehouse, E-Commerce** focuses on a lakehouse architecture for six CRM and ERP source files. It uses a three-task Databricks Jobs workflow, Bronze ingestion, Spark-based Silver transformations, and a governed Gold star schema.\n\n"
            "**SQL Server Data Warehouse** is a complete warehouse project that loads more than 60K records from six source systems into SQL Server using BULK INSERT and layered transformation logic. It covers ingestion, staging, warehouse modeling, and reporting readiness.\n\n"
            "I also worked on AI-oriented data work, including retrieval and evaluation pipelines, where I connect data engineering with vector search and RAG systems."
        ),
        "data_engineering_experience": (
            "My experience in Data Engineering is grounded in building practical pipelines and reliable data systems, not only writing scripts.\n\n"
            "At **DEPI**, I built 4 SSIS ETL packages that ingested 7 CSV sources into SQL Server and used 17 stored procedures to automate ingestion and transformations. That project processed 70K records and supported a customer churn model that reached 97.4% accuracy.\n\n"
            "At **NTI**, I worked on Big Data engineering with Hadoop, Spark, Kafka, and Flink. I built GB-scale Spark batch pipelines on HDFS and Hive, plus streaming pipelines for real-time log ingestion. I was also recognized as the best-performing trainee in a cohort of 30+, and I passed the **Huawei HCIA-Big Data** certification on my first attempt.\n\n"
            "I also worked on an **AWS Cloud Data Engineer** track, where I designed a multi-tier cloud architecture with S3, EC2, RDS, VPC, and IAM, applying Well-Architected principles to storage, compute, and networking.\n\n"
            "Across all of that, my focus has been on pipeline reliability, data quality, orchestration, storage design, and making systems usable for analytics and AI workloads."
        ),
        "certifications": (
            "I currently hold two active certifications that are relevant to my Data Engineering and AI Engineering work.\n\n"
            "- **AWS Certified Cloud Practitioner (CLF-C02)**, issued by Amazon Web Services. This covers core AWS services, cloud concepts, security basics, and deployment patterns.\n\n"
            "- **Huawei HCIA-Big Data**, issued by Huawei. This covers Hadoop, Spark, Kafka, Flink, Hive, and distributed big data concepts.\n\n"
            "Both are active and directly support the systems and platforms I build in data engineering and cloud-oriented projects."
        ),
    }

    _CANONICAL_SOURCES = {
        "who_are_you": [
            {
                "label": "About",
                "github_url": "",
                "portfolio_url": "https://my-portfolio.mohamed-aboheiba.workers.dev/#about",
                "portfolio_section": "About",
            }
        ],
        "contact": [
            {
                "label": "Contact",
                "github_url": "",
                "portfolio_url": "https://my-portfolio.mohamed-aboheiba.workers.dev/#contact",
                "portfolio_section": "Contact",
            }
        ],
        "availability": [
            {
                "label": "About",
                "github_url": "",
                "portfolio_url": "https://my-portfolio.mohamed-aboheiba.workers.dev/#about",
                "portfolio_section": "About",
            }
        ],
        "flagship_project": [
            {
                "label": "Retail Lakehouse Pipeline",
                "github_url": "https://github.com/MoTahaAboHeiba/retail-lakehouse-pipeline",
                "portfolio_url": "https://my-portfolio.mohamed-aboheiba.workers.dev/#projects",
                "portfolio_section": "Projects",
            }
        ],
        "projects": [
            {
                "label": "Retail Lakehouse Pipeline",
                "github_url": "https://github.com/MoTahaAboHeiba/retail-lakehouse-pipeline",
                "portfolio_url": "https://my-portfolio.mohamed-aboheiba.workers.dev/#projects",
                "portfolio_section": "Projects",
            },
            {
                "label": "Databricks Lakehouse, E-Commerce",
                "github_url": "https://github.com/MoTahaAboHeiba/E-Commerce-Lakehouse-Using-Databricks",
                "portfolio_url": "https://my-portfolio.mohamed-aboheiba.workers.dev/#projects",
                "portfolio_section": "Projects",
            },
            {
                "label": "SQL Server Data Warehouse",
                "github_url": "https://github.com/MoTahaAboHeiba/SQL-Data-Warehouse-project",
                "portfolio_url": "https://my-portfolio.mohamed-aboheiba.workers.dev/#projects",
                "portfolio_section": "Projects",
            },
        ],
        "data_engineering_experience": [
            {
                "label": "Professional Experience",
                "github_url": "",
                "portfolio_url": "https://my-portfolio.mohamed-aboheiba.workers.dev/#experience",
                "portfolio_section": "Experience",
            }
        ],
        "certifications": [
            {
                "label": "Certifications",
                "github_url": "",
                "portfolio_url": "https://my-portfolio.mohamed-aboheiba.workers.dev/#certifications",
                "portfolio_section": "Certifications",
            }
        ],
    }

    _QUESTION_PATTERNS = {
        "who_are_you": [
            re.compile(r"^(?:can\s+you\s+)?(?:tell\s+me\s+who\s+you\s+are|who\s+are\s+you)\??$"),
            re.compile(r"^(?:can\s+you\s+)?(?:introduce\s+yourself|tell\s+me\s+about\s+yourself)\??$"),
            re.compile(r"^(?:who\s+are\s+you\s+and\s+what\s+do\s+you\s+specialize\s+in|who\s+are\s+you\s+and\s+what\s+do\s+you\s+specialize\s+in\?)$"),
        ],
        "contact": [
            re.compile(r"^(?:can\s+you\s+)?(?:contact|reach|get\s+in\s+touch|how\s+to\s+find)\s+you\??$"),
            re.compile(r"^(?:what\s+is\s+)?(?:your\s+)?(?:email|phone|whatsapp)\??$"),
            re.compile(r"^(?:cv|resume)\s+(?:download|link)\??$"),
            re.compile(r"^(?:how\s+do\s+i\s+)?(?:contact|reach|get\s+in\s+touch)\s+you\??$"),
        ],
        "availability": [
            re.compile(r"^(?:are\s+you\s+)?(?:available|open\s+to|looking\s+for)\b.*$"),
            re.compile(r"^(?:when\s+can\s+you\s+start|what\s+is\s+your\s+availability|what\s+is\s+your\s+notice\s+period)\??$"),
            re.compile(r"^(?:i\s+am\s+)?(?:open\s+to|looking\s+for)\b.*$"),
        ],
        "flagship_project": [
            re.compile(r"^(?:what\s+is\s+your\s+)?(?:flagship|main|top|best)\s+project\b.*$"),
            re.compile(r"^(?:which|what)\s+project\s+are\s+you\s+most\s+proud\s+of\??$"),
            re.compile(r"^(?:what\s+is\s+the\s+)?most\s+important\s+project\s+you\s+worked\s+on\??$"),
        ],
        "projects": [
            re.compile(r"^(?:can\s+you\s+)?(?:tell\s+me\s+about|walk\s+me\s+through|show\s+me|give\s+me\s+an\s+overview\s+of)\s+(?:your\s+)?projects?\b"),
            re.compile(r"^what\s+(?:projects|projects\s+have\s+you\s+worked\s+on|projects\s+are\s+you\s+proud\s+of)\b"),
            re.compile(r"^what\s+have\s+you\s+built\??$"),
        ],
        "data_engineering_experience": [
            re.compile(r"^(?:can\s+you\s+)?(?:explain|describe|walk\s+me\s+through)\s+(?:your\s+)?(?:experience\s+in\s+)?data\s+engineering\b"),
            re.compile(r"^what\s+(?:is|was)\s+(?:your\s+)?experience\s+in\s+data\s+engineering\b"),
            re.compile(r"^what\s+is\s+your\s+data\s+engineering\s+experience\b"),
        ],
        "certifications": [
            re.compile(r"^(?:can\s+you\s+)?(?:tell\s+me\s+about|list|share)\s+(?:your\s+)?certifications?\b"),
            re.compile(r"^what\s+(?:certifications?|certs?)\s+(?:do\s+you\s+)?(?:have|hold)\??$"),
            re.compile(r"^what\s+(?:certifications?|certs?)\s+(?:are\s+you\s+)?(?:holding|keeping)\??$"),
        ],
    }

    @staticmethod
    def _normalize(text: str) -> str:
        text = (text or "").strip()
        if not text:
            return ""
        text = text.lower()
        text = re.sub(r"[^a-z0-9\s]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def match(self, question: str) -> str | None:
        normalized = self._normalize(question)
        if not normalized:
            return None

        for intent, patterns in self._QUESTION_PATTERNS.items():
            for pattern in patterns:
                if pattern.fullmatch(normalized):
                    return intent
        return None

    def get_answer(self, intent: str) -> str | None:
        return self._CANONICAL_ANSWERS.get(intent)

    def get_sources(self, intent: str) -> list[dict[str, str]]:
        return list(self._CANONICAL_SOURCES.get(intent, []))

    def resolve(self, question: str) -> tuple[str | None, str | None, list[dict[str, str]]]:
        intent = self.match(question)
        if intent is None:
            return None, None, []
        return intent, self.get_answer(intent), self.get_sources(intent)


_CANONICAL_ANSWER_SERVICE = CanonicalAnswerService()


def get_reliable_answer(text: str) -> str | None:
    """Return a vetted answer for the approved, repetitive portfolio prompts."""
    _, answer, _ = _CANONICAL_ANSWER_SERVICE.resolve(text)
    return answer


def get_canonical_sources(text: str) -> list[dict[str, str]]:
    """Return canonical metadata for the approved, repetitive portfolio prompts."""
    intent, _, sources = _CANONICAL_ANSWER_SERVICE.resolve(text)
    if intent is None:
        return []
    return sources


def get_canonical_intent(text: str) -> str | None:
    """Return the canonical intent for a known repeated question, else None."""
    intent, _, _ = _CANONICAL_ANSWER_SERVICE.resolve(text)
    return intent

# ── Patterns ──────────────────────────────────────────────────────────────────

_GREETING = re.compile(
    r"^(hi|hey|hello|good\s+(morning|afternoon|evening|day)|howdy|"
    r"greetings|salaam|marhaba|ahlan|سلام|مرحبا|أهلاً|هاي|هلو|صباح|مساء)"
    r"[\s!,،.]*$",
    re.IGNORECASE,
)

_GREETING_WITH_NAME = re.compile(
    r"^(hi|hey|hello|good\s+(morning|afternoon|evening|day)|salaam|مرحبا|هاي)"
    r"[\s,،!]*\w+[\s!,،.]*$",
    re.IGNORECASE,
)

_INTRODUCTION = re.compile(
    r"(i[''`]?m\s+[a-zA-Z\u0600-\u06FF]+|"
    r"my name is\s+[a-zA-Z\u0600-\u06FF]+|"
    r"i am\s+a?\s*(recruiter|hiring manager|engineer|developer|student|"
    r"hr|talent|founder|cto|tech lead)|"
    r"nice to meet you|"
    r"pleased to meet|"
    r"introducing myself)",
    re.IGNORECASE,
)

_SMALL_TALK = re.compile(
    r"^(how are you|how('?re| are) (you|things|it going)|"
    r"what('?s| is) up|wassup|sup|"
    r"thank(s| you)|thx|ty|"
    r"great|awesome|cool|nice|got it|"
    r"ok|okay|alright|sounds good|"
    r"see you|bye|goodbye|take care)[\s!.،]*$",
    re.IGNORECASE,
)


# ── Canned responses ──────────────────────────────────────────────────────────

_GREETING_RESPONSE = (
    "Hey! I'm Mohamed Taha — a Data Engineer and AI Engineer based in Egypt.\n\n"
    "Feel free to ask me about my projects, skills, certifications, or anything "
    "about my engineering background. What would you like to know?"
)

_SMALL_TALK_RESPONSE = (
    "Doing well, appreciate you asking!\n\n"
    "Is there something specific about my work or engineering background "
    "I can help you with?"
)

_THANKS_RESPONSE = (
    "Happy to help.\n\n"
    "If there is anything else you want to know about my projects or "
    "background, just ask."
)

_GOODBYE_RESPONSE = (
    "Good talking to you. If you want to reach out directly:\n"
    "Email: mohamed-aboheiba@outlook.com\n"
    "LinkedIn: linkedin.com/in/mohamed-taha-abo-heiba"
)

_THANKS_RE = re.compile(
    r"^(thank(s| you)|thx|ty)[\s!.،]*$", re.IGNORECASE
)
_GOODBYE_RE = re.compile(
    r"^(bye|goodbye|see you|take care|cya)[\s!.،]*$", re.IGNORECASE
)

_FOLLOWUP = re.compile(
    r"^(tell me more|what about (that|this)|"
    r"can you (explain|elaborate|expand)|"
    r"go on|continue|and\?|more details?|"
    r"what do you mean|clarify that)[\s?.,]*$",
    re.IGNORECASE,
)

_FOLLOW_UP_START = re.compile(
    r"^(and|what about|how about|why|how did|how do|how|tell me more|"
    r"can you elaborate|also|more on|go on|continue|elaborate|explain more)\b",
    re.IGNORECASE,
)

_PRONOUN_FOLLOW_UP = re.compile(
    r"^(it|that|this|they|them|those|there)\??$",
    re.IGNORECASE,
)


def _extract_name(text: str) -> str | None:
    """Try to extract a first name from an introduction message."""
    patterns = [
        re.compile(r"i[''`]?m\s+([a-zA-Z\u0600-\u06FF]+)", re.IGNORECASE),
        re.compile(r"my name is\s+([a-zA-Z\u0600-\u06FF]+)", re.IGNORECASE),
        re.compile(
            r"(?:hi|hey|hello)[,\s]+i[''`]?m\s+([a-zA-Z\u0600-\u06FF]+)",
            re.IGNORECASE,
        ),
    ]
    for pattern in patterns:
        match = pattern.search(text)
        if match:
            return match.group(1).capitalize()
    return None


def _is_follow_up(text: str) -> bool:
    """Detect short follow-up questions that need prior conversation context."""
    stripped = text.strip()
    words = stripped.split()

    if _FOLLOW_UP_START.search(stripped) or _PRONOUN_FOLLOW_UP.match(stripped):
        return True
    if len(words) <= 8 and "?" in stripped and len(words) <= 5:
        return True
    return len(words) <= 3


def classify(text: str, history: list | None = None) -> str:
    """Return the query category: GREETING, INTRODUCTION, SMALL_TALK, or CAREER."""
    stripped = text.strip()

    if history and _FOLLOWUP.match(stripped):
        return CAREER_CATEGORY

    if (
        history
        and _is_follow_up(stripped)
        and not _SMALL_TALK.match(stripped)
        and not _THANKS_RE.match(stripped)
        and not _GOODBYE_RE.match(stripped)
    ):
        return CAREER_CATEGORY

    if _GREETING.match(stripped) or _GREETING_WITH_NAME.match(stripped):
        # A greeting with a name might also be an introduction — check both.
        if _INTRODUCTION.search(stripped):
            return "INTRODUCTION"
        return "GREETING"

    if _INTRODUCTION.search(stripped):
        return "INTRODUCTION"

    if _SMALL_TALK.match(stripped):
        return "SMALL_TALK"

    return CAREER_CATEGORY


def get_canned_response(category: str, text: str) -> str:
    """Return the appropriate canned response for a non-career query."""
    if category == "GREETING":
        return _GREETING_RESPONSE

    if category == "INTRODUCTION":
        name = _extract_name(text)
        if name:
            return (
                f"Hey {name}! Nice to connect.\n\n"
                "I'm Mohamed Taha — a Data Engineer and AI Engineer. "
                "Ask me anything about my work, projects, or technical "
                "background. I'm happy to answer."
            )
        return (
            "Nice to meet you!\n\n"
            "I'm Mohamed Taha — a Data Engineer and AI Engineer. "
            "Feel free to ask about my projects, skills, or engineering "
            "background."
        )

    if category == "SMALL_TALK":
        if _THANKS_RE.match(text.strip()):
            return _THANKS_RESPONSE
        if _GOODBYE_RE.match(text.strip()):
            return _GOODBYE_RESPONSE
        return _SMALL_TALK_RESPONSE

    # Should not reach here — CAREER is handled by the pipeline.
    return _GREETING_RESPONSE
