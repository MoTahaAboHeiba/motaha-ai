---
document_type: project
topic: motaha-ai
project: MoTaha AI
portfolio_section: Projects
portfolio_url: https://my-portfolio.mohamed-aboheiba.workers.dev/#projects
source_url: https://github.com/MoTahaAboHeiba/motaha-ai
---

# MoTaha AI

Mohamed Taha built MoTaha AI to turn his engineering portfolio into a
grounded conversational experience for visitors and hiring teams.

## MoTaha AI — What it is

MoTaha AI is the assistant you are talking to right now. It is a
production-oriented RAG chatbot embedded in my portfolio that acts as
a virtual version of me. Instead of a visitor reading a static page
and guessing whether I can answer their specific question, they can
ask it directly and get a grounded, cited answer drawn from my actual
documented experience.

The chatbot speaks in first person as me. It answers questions about
my engineering background, projects, technical decisions, certifications,
skills, and professional experience. When it does not have the
information, it says so directly and points the visitor to my contact
details rather than hallucinating an answer.

## MoTaha AI — Why I built it

Two reasons.

First, a static portfolio answers the questions I anticipated. A
conversational interface answers the questions the visitor actually has.
A recruiter and a senior engineer ask completely different things about
the same candidate. A chatbot handles both without me needing to predict
every question in advance.

Second, building MoTaha AI is itself evidence of what I can do. The
system required designing an ingestion pipeline, choosing and combining
retrieval strategies, integrating LLM providers with fallback logic,
and making deployment decisions under real constraints. Any hiring
manager who wants to know whether I can build AI-powered data systems
can look at this system as the answer.

## MoTaha AI — The engineering problem

The core engineering problem is: how do you make an LLM answer
questions about a specific person accurately, without hallucinating
credentials or experience that person does not have?

The answer is retrieval-augmented generation with a scope guard. The
LLM is not the source of truth. My knowledge base is. The LLM is only
the generation layer. If the retrieval system cannot find relevant
evidence, the LLM never gets called.

## MoTaha AI — Architecture
User question (FastAPI)
│
▼
pipeline.answer()
│
├── retriever.retrieve()
│ │
│ ├── dense.search() → Qdrant Cloud (top-10 by cosine)
│ └── sparse.query() → BM25Okapi (top-10 by BM25 score)
│ │
│ └── fusion.rrf() → RRF k=60 → top-5 chunks
│
├── scope_guard.is_sufficient()
│ ├── top_dense_score < 0.35 → REFUSAL (no LLM call)
│ └── top_dense_score ≥ 0.35 → proceed
│
└── generator.generate()
├── Groq openai/gpt-oss-20b → stream tokens
└── on failure → Gemini gemini-2.5-flash

## MoTaha AI — Technology choices and why

**Gemini (`gemini-embedding-001`)**
MoTaha AI uses Gemini's `gemini-embedding-001` model for document and query
embeddings. The ingestion script configures document embeddings for retrieval
and stores 3,072-dimensional cosine vectors in Qdrant Cloud.

**Qdrant Cloud**
Managed vector database on the free tier. Persistent storage, no
infrastructure to maintain, integrates with the Gemini embedding client. I
designed ingestion to use deterministic UUIDs generated from file path
and chunk index, which makes re-running the ingestion script fully
idempotent. The same chunks always produce the same point IDs, so
upserts overwrite rather than duplicate.

**BM25 sparse retrieval (rank-bm25)**
Pure Python, no GPU, no external service. The BM25 index is built
at module load time over the full knowledge base corpus and held in
memory. All subsequent queries hit a pre-built index with zero I/O
overhead. BM25 handles lexical matching: when a visitor asks about
a specific tool or project name, BM25 surfaces chunks that contain
those exact terms even when the semantic similarity score is moderate.

**Reciprocal Rank Fusion (k=60)**
RRF merges the dense and sparse result sets into a single ranked list
without requiring score normalization. The formula is the sum of
1/(k + rank) across both lists. With k=60 the constant dampens the
advantage of top-ranked results so neither retrieval method dominates
purely by position. I deduplicate by chunk text before returning the
final top-5.

**Scope guard on dense cosine score**
The scope guard checks the top cosine similarity score from Qdrant,
not the RRF score. This is a deliberate decision. RRF scores are sums
of 1/(k + rank). With k=60 and two lists of 10 results, the maximum
possible RRF score is 1/61 + 1/61 = 0.033. A threshold of 0.35 on an
RRF score would be permanently unreachable. Every query would be
refused. Cosine similarity lives in the range 0 to 1 and directly
represents semantic overlap. 0.35 cosine similarity is a defensible
floor for "this query is at least moderately related to something in
the knowledge base."

**Groq `openai/gpt-oss-20b` with Gemini `gemini-2.5-flash` fallback**
Groq is the primary generation provider and uses the configured
`openai/gpt-oss-20b` model. If Groq generation fails, MoTaha AI falls back to
Gemini `gemini-2.5-flash`.

**FastAPI and Uvicorn**
The current application exposes a FastAPI service from `main.py` and runs
with Uvicorn. The `/chat` endpoint streams responses over Server-Sent Events,
and the Render deployment uses `uvicorn main:app --host 0.0.0.0 --port $PORT`.

## MoTaha AI — Engineering challenges I solved

**Keeping deployment files available**
The BM25 index is built when the sparse retrieval module is imported. The
deployed service therefore needs the Markdown and PDF files under
`knowledge_base/` in the repository, not only on the development machine.

**The RRF threshold bug**
After the rebuild, the scope guard was written with a threshold of 0.35
applied to the RRF score. This would have caused every query to be
refused because RRF scores can never reach 0.35 with k=60. I caught
this during review before deployment. The fix was to pass the top
dense cosine score separately through the retrieval pipeline alongside
the fused results and check that instead.

**Idempotent ingestion**
Running the ingestion script twice with the same knowledge base would
create duplicate points in Qdrant if IDs were random. I generate
UUIDs deterministically from file path and chunk index using
uuid5(NAMESPACE_URL, f"{file_path}:{chunk_index}"). The same chunk
always maps to the same ID. Qdrant upsert overwrites the existing
point. Ingestion is safe to re-run at any time.

**Provider fallback**
The generation layer keeps provider-specific model configuration in one place
and falls back from Groq to Gemini when the primary provider fails.

## MoTaha AI — Knowledge base design

The knowledge base is a categorized set of markdown documents covering:

- My identity, professional profile, and career focus
- My certifications, skills, and education
- Each project I have built with architecture, decisions, and
  engineering challenges
- My engineering philosophy

Every document is authored by me and reviewed before ingestion. The
chatbot answers only from this content. It does not infer, speculate,
or draw from LLM training data about me. This is a deliberate
engineering and integrity decision: a portfolio chatbot that invents
credentials is worse than having no chatbot.

## MoTaha AI — What you can ask

Recruiter-level questions:
- Who are you and what do you specialize in?
- What evidence do you have that you can deliver?
- Can you work in a team?
- What roles are you targeting?

Technical questions:
- Why did you use hybrid retrieval instead of pure vector search?
- How does the scope guard prevent hallucination?
- How does RRF merge dense and sparse results?
- Why use Gemini embeddings with BM25?
- How does the Groq fallback work?
- Walk me through the ingestion pipeline.

Project questions:
- How does MoTaha AI work end to end?
- What was the hardest engineering problem you solved in this project?
- Why use FastAPI for deployment?

## MoTaha AI — What I would do differently with more time

Reranking: I dropped the BGE reranker to eliminate the GPU dependency.
A Cohere Rerank API call would restore reranking without any local
model. That is the next retrieval improvement.

Evaluation: I do not have a formal evaluation dataset yet. The correct
approach is a benchmark of recruiter questions, technical questions, and
adversarial questions with expected behavior labels, run against every
KB change. Without it I am validating by manual spot-check.

Streaming citations: citations currently appear as a block at the end
of the response. Inline citations linked to source documents during
streaming would be a better user experience.

## MoTaha AI — Repository

GitHub: https://github.com/MoTahaAboHeiba/motaha-ai
Render: https://motaha-ai.onrender.com
HF Space: huggingface.co/spaces/Mo-Taha-AboHeiba/motaha-ai