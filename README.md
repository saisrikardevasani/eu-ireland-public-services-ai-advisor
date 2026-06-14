# EU & Ireland Public Services AI Advisor

A production-grade RAG (Retrieval-Augmented Generation) chatbot that answers questions about Irish public services — immigration, tax, health, housing, and employment — with **cited, grounded answers** linked to official Citizens Information sources.

> Built as a 4-week learning project: build a real product, learn the engineering behind it.

---

## What It Does

Ask a question like *"When can I switch from Stamp 2 to Stamp 1G?"* and the system:

1. Embeds your question into a 384-dimensional vector
2. Runs **hybrid retrieval** — BM25 full-text search + dense cosine similarity — in parallel
3. Fuses results with **Reciprocal Rank Fusion (RRF)** to get the top 5 passages
4. Streams a grounded answer from **Llama 3.1** (via NVIDIA free API) token-by-token
5. Returns clickable citation chips linking every claim to its source

Every factual claim is cited. The model is instructed never to answer outside the retrieved context.

---

## Architecture

```
User question
     │
     ▼
[Query Embedder]  ←── BAAI/bge-small-en-v1.5 (384-dim, runs locally)
     │
     ├──────────────────────────────────────┐
     ▼                                      ▼
[BM25 Search]                        [Dense Search]
Postgres tsvector + ts_rank_cd       pgvector cosine similarity
top 20 candidates                    top 20 candidates
     │                                      │
     └──────────────┬───────────────────────┘
                    ▼
            [RRF Fusion]
            score = Σ 1/(60 + rank)
            top 5 chunks
                    │
                    ▼
         [Llama 3.1 via NVIDIA API]
         Streams tokens with [n] citations
                    │
                    ▼
         [SSE stream → Next.js UI]
```

### Tech Stack

| Layer | Technology |
|---|---|
| **API** | FastAPI + Server-Sent Events (SSE) |
| **Database** | PostgreSQL 16 + pgvector extension |
| **Full-text search** | Postgres `tsvector` / `ts_rank_cd` |
| **Vector search** | pgvector cosine similarity (`<=>`) |
| **Embeddings** | `BAAI/bge-small-en-v1.5` via sentence-transformers |
| **LLM** | `meta/llama-3.1-8b-instruct` via NVIDIA NIM (free tier) |
| **Frontend** | Next.js 14 + Tailwind CSS |
| **Cache** | Redis 7 |
| **Containers** | Docker Compose |
| **Migrations** | Alembic |

---

## Project Structure

```
.
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── chat.py          # POST /v1/chat/messages — SSE streaming endpoint
│   │   │   └── health.py        # GET /health
│   │   ├── ingestion/
│   │   │   ├── chunker.py       # Fixed-size chunking (512 words, 50 overlap)
│   │   │   ├── crawler.py       # Citizens Information web crawler
│   │   │   ├── embedder.py      # Sentence-transformer embedding
│   │   │   └── pipeline.py      # Ingest orchestrator (idempotent)
│   │   ├── models/
│   │   │   └── schema.py        # SQLAlchemy ORM: Document + Chunk
│   │   ├── pipeline/
│   │   │   ├── generator.py     # LLM answer generation (NVIDIA / Anthropic)
│   │   │   └── retrieval.py     # Hybrid BM25 + dense + RRF fusion
│   │   ├── config.py            # pydantic-settings config from .env
│   │   ├── database.py          # Async SQLAlchemy engine + session
│   │   └── main.py              # FastAPI app factory
│   ├── fixtures/
│   │   └── citizens_information.json   # 15 seed documents for local dev
│   ├── migrations/              # Alembic migrations
│   ├── scripts/
│   │   ├── seed.py              # Load fixtures (fast, no crawling)
│   │   └── ingest.py            # Live crawler (requires site access)
│   ├── tests/
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── app/
│       │   └── chat/page.tsx    # Chat UI (streaming tokens + citations)
│       ├── components/
│       │   ├── ChatMessage.tsx  # Message bubbles + citation chips
│       │   └── ChatInput.tsx    # Input box
│       └── lib/api.ts           # SSE client
├── docker-compose.yml
├── Makefile
└── .env.example
```

---

## Quick Start

### Prerequisites

- Docker Desktop
- Python 3.11+
- Node.js 18+
- A free NVIDIA API key from [build.nvidia.com](https://build.nvidia.com)

### 1. Clone and configure

```bash
git clone https://github.com/saisrikardevasani/eu-ireland-public-services-ai-advisor.git
cd eu-ireland-public-services-ai-advisor

# Create your local environment file
cp .env.example backend/.env
# Edit backend/.env and add your NVIDIA_API_KEY
```

### 2. Start the database

```bash
make db-up
```

This starts Postgres 16 (with pgvector) and Redis 7 in Docker.

### 3. Run migrations

```bash
make migrate
```

Creates the `documents` and `chunks` tables, GIN index for full-text search, and vector column.

### 4. Seed the database

```bash
make seed
```

Loads 15 pre-written Citizens Information documents. Takes ~30 seconds on first run (downloads the 134MB embedding model).

### 5. Start the backend

```bash
make backend
# API available at http://localhost:8000
# Docs at http://localhost:8000/docs
```

### 6. Start the frontend

```bash
make frontend
# UI available at http://localhost:3000
```

---

## Available Commands

```bash
make db-up      # Start Postgres + Redis in Docker
make db-down    # Stop and remove containers
make migrate    # Apply database migrations
make seed       # Load fixture documents (fast, no crawling)
make ingest     # Crawl Citizens Information live (slow)
make backend    # Start FastAPI backend (hot reload)
make frontend   # Start Next.js frontend (hot reload)
```

---

## API Reference

### `POST /v1/chat/messages`

Streams an answer to a public services question via Server-Sent Events.

**Request:**
```json
{ "message": "How do I apply for a medical card?" }
```

**Response stream (SSE):**
```
event: meta
data: {"retrieved_count": 5}

event: token
data: {"text": "To apply for a medical card..."}

event: citations
data: {"citations": [{"n": 1, "title": "Medical Card", "url": "...", "snippet": "..."}]}

event: done
data: {"message": "Stream complete"}
```

### `GET /health`

Returns `{"status": "ok"}`.

---

## How Hybrid Retrieval Works

**Why hybrid?** Pure keyword search misses synonyms; pure vector search misses exact terms. Combining both captures more relevant documents.

**BM25** (via Postgres `tsvector`): tokenises and stems the query, ranks documents by term frequency. Great for specific terms like "Stamp 1G" or "USC rate".

**Dense** (via pgvector): embeds query and chunks into 384-dim vectors, ranks by cosine similarity. Great for semantic matches — "switching visa" finds "changing immigration permission".

**RRF Fusion**: merges the two ranked lists with `score = Σ 1/(60 + rank)`. Documents appearing in both lists get boosted. Parameter-free and consistently outperforms linear score combination.

---

## Topics Covered (Seed Data)

- Stamp 1G — Third Level Graduate Programme
- Critical Skills Employment Permit
- Irish Residence Permit (IRP) registration
- PPSN (Personal Public Service Number)
- Medical Card and GP Visit Card
- USC (Universal Social Charge)
- Income Tax calculation
- PAYE Tax Credit
- Minimum Wage
- Jobseeker's Benefit and Allowance
- Child Benefit
- Tenants' Rights (Residential Tenancies Acts)
- Opening a Bank Account in Ireland
- Employment Permits overview

---

## Configuration

All configuration is via environment variables in `backend/.env`. See `.env.example` for the full reference.

Key settings:

| Variable | Default | Description |
|---|---|---|
| `LLM_PROVIDER` | `nvidia` | `nvidia` or `anthropic` |
| `NVIDIA_MODEL` | `meta/llama-3.1-8b-instruct` | Any model from NVIDIA NIM |
| `EMBEDDING_MODEL` | `BAAI/bge-small-en-v1.5` | Sentence-transformers model |
| `BM25_TOP_K` | `20` | BM25 candidates before fusion |
| `DENSE_TOP_K` | `20` | Dense candidates before fusion |
| `FINAL_TOP_K` | `5` | Chunks passed to LLM |

---

## Roadmap

- **v0.1 (complete)** — Hybrid RAG pipeline, streaming UI, seed data, NVIDIA LLM
- **v0.2** — Eval harness: 30 gold Q&A pairs, RAGAS faithfulness + recall metrics, CI gates
- **v0.3** — Hierarchical chunking, cross-encoder reranking, Revenue.ie as second source
- **v0.4** — AWS deployment, Langfuse observability, public Grafana dashboard

---

## Disclaimer

This tool provides **informational guidance only**. It is not a substitute for professional legal, tax, or immigration advice. Always verify information with official sources:

- [citizensinformation.ie](https://www.citizensinformation.ie)
- [revenue.ie](https://www.revenue.ie)
- [irishimmigration.ie](https://www.irishimmigration.ie)

---

## License

[Apache 2.0](LICENSE) — see licence terms for permitted use, modification, and distribution.

---

## Contributing

Pull requests are welcome. Please open an issue first to discuss significant changes.

This project is a learning exercise. If you use it as a foundation for a production service, please ensure you comply with the terms of service of any data sources you crawl.
