# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A layered memory system for AI agents with vector search (Qdrant), knowledge graphs, and automatic memory evolution. Written in Python 3.11+, managed with [uv](https://docs.astral.sh/uv/). Designed to integrate with an agent framework called OpenClaw.

## Setup & Running

```bash
# Install dependencies (uv creates .venv automatically)
uv sync

# Start Qdrant (Docker, requires proxy-net network)
docker compose up -d agent-memory-qdrant

# Configure environment
cp .env.example .env
# Edit .env — must set QDRANT_HOST, OPENAI_API_KEY

# Run tests
uv run python -m agent_memory.test_improvements
uv run python -m agent_memory.test_openai_embedding
uv run python -m agent_memory.test_quickstart

# Run benchmarks
uv run python scripts/benchmark_improvements.py
```

## Architecture

### Core Data Flow

```
User Input → MemoryService / TieredMemory → Qdrant (vector store)
                                           → JSON file (fallback when Qdrant unavailable)
```

### Shared Configuration

All modules import from `agent_memory.config`, which loads `.env` once via `python-dotenv`. Do not add manual `.env` parsing to new modules.

### Key Modules (all in `agent_memory/`)

- **config.py** — Centralized settings loaded from `.env`. All other modules import from here.
- **memory_service.py** — Entry point. `MemoryService` class handles vector storage via Qdrant with automatic file-based fallback. Embeddings use OpenAI `text-embedding-3-small` (1536-dim).
- **batch_embedding.py** — Batch embedding with caching. All embedding calls go through here, not directly to OpenAI.
- **tiered_memory.py** — Four-layer memory hierarchy: Core (always in context) → Working (FIFO, last 50 messages) → Recall (vector-indexed history) → Archival (compressed summaries). Inspired by MemGPT/Letta.
- **memory_evolver.py** — Automatic memory evolution: ADD new, UPDATE contradictory, DELETE stale, NOOP duplicates. Inspired by Mem0.
- **knowledge_graph.py** — Entity-relation graph with types (PERSON, LOCATION, EVENT, CONCEPT, ORGANIZATION, OBJECT). In-memory dicts + JSON persistence.
- **enhanced_memory_graph.py** — Integrates knowledge graph with MemoryService for auto entity extraction on store and graph-augmented retrieval.
- **hybrid_rag.py** — Combines vector similarity, temporal filtering, and keyword boosting for retrieval.
- **atomic_notes.py** — Zettelkasten-style atomic notes. Each note = one concept, auto-linked by keywords. Inspired by A-MEM.
- **memory_compressor.py** — Time-based compression: raw → weekly summary → monthly summary → archive.
- **memory_optimizer.py** — Query caching, batch operations, async writes, connection pooling.
- **integrate.py** — OpenClaw integration bridge (`OpenClawMemoryService`).
- **sync.py** / **simple_sync.py** — Scripts to sync OpenClaw workspace memories into Qdrant.

### External Scripts

- **scripts/init_memory.py** — OpenClaw auto-start hook.
- **scripts/benchmark_improvements.py** — Benchmark comparing Basic vs Hybrid RAG vs Zettelkasten.

## Environment Variables

| Variable | Default | Required |
|----------|---------|----------|
| `QDRANT_HOST` | `agent-memory-qdrant` | Yes |
| `QDRANT_PORT` | `6333` | Yes |
| `OPENAI_API_KEY` | — | Yes |
| `OPENAI_EMBEDDING_MODEL` | `text-embedding-3-small` | No |
| `HTTP_PROXY` / `HTTPS_PROXY` | — | No |

## Important Patterns

- All imports use relative package syntax (e.g., `from .config import ...`). No `sys.path.insert` calls.
- `NO_PROXY="*"` is set in `config.py` to avoid proxy issues with Qdrant connections.
- Qdrant runs on port 6334 externally (mapped from 6333 internally) to avoid conflicts with another Qdrant instance.
- Memory IDs: UUID for Qdrant points, MD5-based short IDs for file storage fallback.
- Collection name `agent_memories` is defined in `config.py`.
