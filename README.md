# Agent Memory - AI Agent Memory Vector System

**A tiered memory system for AI Agents, supporting vector retrieval, auto-evolution, and knowledge graph**

[🌐 中文](README.zh.md) | **English**

[![GitHub](https://img.shields.io/badge/GitHub-legendPerceptor/agent--memory-blue)](https://github.com/legendPerceptor/agent-memory)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11+-blue)](https://www.python.org/)

---

## 🌟 Features

### ✅ Implemented

- **Vector Memory Storage** - Efficient semantic retrieval using Qdrant
- **Real OpenAI Embedding** - text-embedding-3-small (1536 dimensions)
- **Tiered Storage Architecture** - Core / Working / Recall / Archival four-layer memory
- **Memory Evolution System** - Auto-deduplication, smart updates, obsolete deletion
- **Human-in-the-Loop Feedback System** - Human feedback driven memory quality improvement
- **File Storage Fallback** - Automatically falls back to file storage when Qdrant is unavailable
- **Multi-type Support** - fact / event / preference / decision
- **Standalone Qdrant Container** - agent-memory-qdrant (independent from aicreatorvault)

### 🚧 In Development

- Time-aware memory (Bi-temporal)
- Async optimization
- Web UI management interface
- Local embedding model support

---

## 🚀 Quick Start

### 1. Start Qdrant Container

```bash
# Start the standalone agent-memory-qdrant container
docker run -d \
  --name agent-memory-qdrant \
  --network proxy-net \
  --restart unless-stopped \
  -p 6336:6333 \
  -p 6337:6334 \
  -v agent_memory_qdrant_data:/qdrant/storage \
  qdrant/qdrant:latest
```

### 2. Configure Environment Variables

```bash
# Copy the configuration template
cp .env.example .env

# Edit configuration
nano .env

# Required settings:
# - QDRANT_HOST=agent-memory-qdrant
# - OPENAI_API_KEY=sk-proj-...
# - HTTP_PROXY=http://xray:1087  # If proxy is needed
```

### 3. Install Dependencies

```bash
# Create virtual environment
python3 -m venv venv
. venv/bin/activate

# Install dependencies
pip install -r vector-memory/requirements.txt
```

### 4. Test Run

```bash
# Test Qdrant connection
python3 test_agent_memory_qdrant.py

# Test full service
python3 test_memory_service.py
```

---

## 📖 Usage Examples

### Basic Usage

```python
import sys
sys.path.insert(0, 'vector-memory')

from memory_service import MemoryService

# Initialize service
service = MemoryService()

# Store memory (automatically uses real OpenAI Embedding)
service.remember(
    content="Yuanjian likes League of Legends, assistant is Akali",
    memory_type="preference",
    importance=0.8,
    tags=["user", "game", "preference"]
)

# Semantic retrieval
results = service.recall("What games does Yuanjian like", limit=5)
for result in results:
    print(f"{result['content']} (similarity: {result.get('score', 0):.4f})")

# View statistics
stats = service.stats()
print(f"Total memories: {stats['count']}")
print(f"Storage type: {stats['storage']}")
```

### OpenClaw Integration

```python
# Auto-initialize when OpenClaw starts
from init_memory import initialize_memory, get_context_for_query

# Initialize
service = initialize_memory()

# Retrieve context
context = get_context_for_query("user programming preferences")
```

---

## 🏗️ Tiered Storage Architecture

```
Level 1: Core Memory
├── User profile
├── Current tasks
├── Key preferences
└── Always in context window

Level 2: Working Memory
├── Recent 50 conversations
├── Auto rotation (FIFO)
└── Temporary context

Level 3: Recall Memory
├── Complete history
├── Vector index
└── Semantic retrieval

Level 4: Archival Memory
├── Compressed summaries
├── Long-term storage
└── Periodic archival
```

---

## 🧠 Memory Evolution System

```python
from memory_evolver import MemoryEvolver

evolver = MemoryEvolver()

# Scenario 1: Contradictory update
evolver.evolve("User uses GLM-5")      # ADD
evolver.evolve("User switched to MiniMax")    # UPDATE (auto-replace)

# Scenario 2: Duplicate skip
evolver.evolve("User prefers concise replies")    # ADD
evolver.evolve("User likes concise responses")  # NOOP (similarity > 0.95)

# Scenario 3: Obsolete deletion
evolver.evolve("Temporary test configuration")        # DELETE
```

---

## 👤 Human-in-the-Loop Feedback System

Improve memory quality through human feedback, supporting Feishu, CLI, API and other feedback channels.

### Three-Layer Feedback Architecture

```
Layer 1: Write-time Feedback
├── Memory candidate review (propose → review → confirm/modify/reject)
├── Auto-approve high confidence, pending review for low confidence
└── Core memory change proposals (diff preview)

Layer 2: Retrieval-time Feedback
├── Memory rating (+1 useful / -1 not useful)
├── Retrieval relevance feedback
└── Feedback-driven retrieval parameter adaptation

Layer 3: Periodic Review
├── Low confidence / contradictory / long-unaccessed memory review
├── Contradiction detection and merge suggestions
└── Protected memories (no compression/deletion)
```

### Usage Examples

```python
from agent_memory import HumanFeedbackManager

manager = HumanFeedbackManager()

# Write-time feedback - create candidate for review
candidate = manager.propose_memory(
    content="User prefers concise replies",
    memory_type="preference",
    importance=0.8,
    confidence=0.85,
    source="feishu"
)

# Confirm candidate
manager.confirm_candidate(candidate.candidate_id, source="feishu")

# Modify candidate before writing
manager.modify_candidate(
    candidate.candidate_id,
    content="User prefers concise replies, dislikes lengthy responses",
    importance=0.9,
    reason="User added details",
    source="feishu"
)

# Reject candidate
manager.reject_candidate(candidate.candidate_id, reason="Inaccurate info", source="feishu")

# Retrieval-time feedback - rate memory
manager.rate_memory(memory_id, rating=1, source="feishu")   # useful
manager.rate_memory(memory_id, rating=-1, source="feishu")  # not useful

# Retrieval relevance feedback
manager.submit_relevance_feedback("API config", memory_id, relevant=False, source="feishu")

# Auto-approve high confidence candidates
manager.auto_approve(confidence_threshold=0.9)

# Periodic review
queue = manager.generate_review_queue()        # generate review queue
contradictions = manager.detect_contradictions() # detect contradictory memories
merges = manager.suggest_merges()               # suggest similar memory merges
manager.apply_review_decision(memory_id, "protect")  # protect important memory
```

### OpenClaw Integration (Feishu Feedback)

```python
from agent_memory.integrate import get_memory_service

service = get_memory_service()

# Require approval when remembering
candidate = service.remember("User uses MiniMax model", require_approval=True)

# User confirms/modifies/rejects via Feishu
service.confirm_candidate(candidate.candidate_id, source="feishu")
service.modify_candidate(candidate.candidate_id, content="Corrected content", source="feishu")
service.reject_candidate(candidate.candidate_id, reason="Not needed", source="feishu")

# User rates retrieval results via Feishu
service.rate_memory(memory_id, rating=-1, source="feishu")
service.submit_relevance_feedback(query, memory_id, relevant=False, source="feishu")
```

### Feedback Data Models

```python
@dataclass
class MemoryFeedback:
    feedback_id: str           # Feedback ID
    memory_id: str             # Associated memory ID
    feedback_type: str         # confirm | modify | reject | relevance_up | relevance_down
    original_content: str      # Original content
    modified_content: str      # Modified content
    original_importance: float # Original importance
    modified_importance: float # Modified importance
    source: str                # feishu | cli | api
    reason: str                # Feedback reason
    created_at: str            # Feedback timestamp

@dataclass
class MemoryCandidate:
    candidate_id: str          # Candidate ID
    content: str               # Memory content
    memory_type: str           # Suggested classification
    importance: float          # Suggested importance
    confidence: float          # Extraction confidence
    operation: str             # ADD | UPDATE | DELETE
    status: str                # pending | confirmed | modified | rejected
```

---

## 📊 Performance Metrics

| Metric | Current | Target | Improvement |
|--------|---------|--------|-------------|
| Startup Tokens | ~2,961 | ~1,000 | -66% |
| Memory Capacity | ~100 entries | ~10,000 entries | 100x |
| Lookup Speed | O(n) | O(log n) | 50x |
| History Compression | 0% | 90% | 90% |
| Semantic Similarity | 0.4890 | - | ✅ Real vectors |

---

## 🔧 Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `QDRANT_HOST` | `agent-memory-qdrant` | Qdrant hostname |
| `QDRANT_PORT` | `6333` | Qdrant port |
| `OPENAI_API_KEY` | - | OpenAI API Key (required) |
| `OPENAI_EMBEDDING_MODEL` | `text-embedding-3-small` | Embedding model |
| `HTTP_PROXY` | - | HTTP proxy (optional) |
| `HTTPS_PROXY` | - | HTTPS proxy (optional) |

---

## 💾 Data Backup

```bash
# Create backup
docker exec agent-memory-qdrant tar -czf /tmp/backup.tar.gz -C /qdrant/storage .

# Copy to local
docker cp agent-memory-qdrant:/tmp/backup.tar.gz ./backups/

# Scheduled backup (crontab)
# Daily at 2 AM
0 2 * * * docker exec agent-memory-qdrant tar -czf /tmp/backup.tar.gz -C /qdrant/storage . && docker cp agent-memory-qdrant:/tmp/backup.tar.gz ~/backups/qdrant_$(date +\%Y\%m\%d).tar.gz
```

---

## 🗂️ Project Structure

```
agent-memory/
├── agent_memory/
│   ├── __init__.py              # Module entry
│   ├── config.py                # Configuration
│   ├── memory_service.py        # Low-level vector storage primitive (Qdrant + file fallback)
│   ├── tiered_memory.py         # Tiered storage (uses MemoryService internally)
│   ├── memory_evolver.py        # Memory evolution
│   ├── human_feedback.py        # Human-in-the-Loop feedback system
│   ├── hybrid_rag.py            # Hybrid retrieval (uses MemoryService internally)
│   ├── atomic_notes.py          # Zettelkasten atomic notes
│   ├── knowledge_graph.py       # Knowledge graph
│   ├── enhanced_memory_graph.py # Graph-enhanced memory
│   ├── memory_compressor.py     # Memory compression
│   ├── memory_optimizer.py      # Performance optimization
│   ├── batch_embedding.py       # Batch embedding
│   └── integrate.py             # OpenClaw integration entry
│
├── scripts/
│   ├── init_memory.py           # OpenClaw startup initialization
│   └── benchmark_improvements.py # Performance benchmark
│
├── .env.example                 # Configuration template
├── docker-compose.yml           # Docker configuration
└── README.md                    # This file
```

## 🔗 Architecture

```
OpenClawMemoryService (integrate.py)
    │
    ├── MemoryService (memory_service.py)  ← Low-level vector storage primitive
    │       └── Qdrant / file fallback
    │
    ├── TieredMemory (tiered_memory.py)
    │       ├── CoreMemory (JSON)
    │       ├── WorkingMemory (in-memory)
    │       ├── RecallMemory → uses MemoryService internally
    │       └── ArchivalMemory (JSON)
    │
    ├── MemoryEvolver (memory_evolver.py)
    │       └── TieredMemory
    │
    └── HumanFeedbackManager (human_feedback.py)
            └── TieredMemory

HybridRAG (hybrid_rag.py)
    └── MemoryService

ZettelkastenMemory (atomic_notes.py)
    └── HybridRAG → MemoryService
```

**Key Design**: `MemoryService` is the single low-level vector storage primitive. `RecallMemory`, `HybridRAG`, and other components delegate to it, avoiding duplicate Qdrant connections and embedding logic.

---

## 📚 Documentation

| Document | English | 中文 |
|----------|---------|------|
| Advanced Memory 2026 | [en](docs/en/ADVANCED_MEMORY_2026.md) | [zh](docs/zh/ADVANCED_MEMORY_2026.md) |
| Knowledge Graph | [en](docs/en/KNOWLEDGE_GRAPH.md) | [zh](docs/zh/KNOWLEDGE_GRAPH.md) |
| Full Research | [en](docs/en/FULL_RESEARCH.md) | [zh](docs/zh/FULL_RESEARCH.md) |
| Summary | [en](docs/en/SUMMARY.md) | [zh](docs/zh/SUMMARY.md) |
| Integration Guide | [en](docs/en/INTEGRATION_GUIDE.md) | [zh](docs/zh/INTEGRATION_GUIDE.md) |
| Knowledge Graph Update | [en](docs/en/KNOWLEDGE_GRAPH_UPDATE.md) | [zh](docs/zh/KNOWLEDGE_GRAPH_UPDATE.md) |
| Quick Start | [en](docs/en/QUICKSTART.md) | [zh](docs/zh/QUICKSTART.md) |
| Improvements | [en](docs/en/IMPROVEMENTS.md) | [zh](docs/zh/IMPROVEMENTS.md) |
| Improvement Plan | [en](docs/en/IMPROVEMENT_PLAN.md) | [zh](docs/zh/IMPROVEMENT_PLAN.md) |
| Compression & Optimization | [en](docs/en/COMPRESSION_AND_OPTIMIZATION.md) | [zh](docs/zh/COMPRESSION_AND_OPTIMIZATION.md) |
| Pull Request Template | [en](docs/en/PULL_REQUEST_TEMPLATE.md) | [zh](docs/zh/PULL_REQUEST_TEMPLATE.md) |
| Agent Memory Qdrant | [en](docs/en/AGENT_MEMORY_QDRANT.md) | [zh](docs/zh/AGENT_MEMORY_QDRANT.md) |
| OpenAI Embedding | [en](docs/en/OPENAI_EMBEDDING_INTEGRATION.md) | [zh](docs/zh/OPENAI_EMBEDDING_INTEGRATION.md) |
| Push to GitHub | [en](docs/en/PUSH_TO_GITHUB.md) | [zh](docs/zh/PUSH_TO_GITHUB.md) |

---

## 🚧 Roadmap

### Phase 2: Core Feature Enhancement
- [x] Qdrant connection fix
- [x] Real OpenAI Embedding
- [x] Memory compression
- [x] Performance optimization

### Phase 3: Advanced Features
- [x] Knowledge graph memory (`knowledge-graph` branch)
- [x] Human-in-the-Loop feedback system
- [ ] Time-aware memory
- [ ] Async optimization
- [ ] Batch operations

### Phase 4: Production Ready
- [ ] Multi-user collaboration
- [ ] Web UI
- [ ] Performance monitoring
- [ ] API documentation

---

## 📝 Changelog

### v2.1 (2026-04-23)
- ✅ Added Human-in-the-Loop feedback system (write-time, retrieval-time, periodic review)
- ✅ Memory candidate review mechanism (propose → confirm/modify/reject)
- ✅ Memory rating and retrieval relevance feedback
- ✅ Feedback-driven retrieval parameter adaptation
- ✅ Core memory change proposals (diff preview)
- ✅ Protected memories (no compression/deletion)
- ✅ Periodic review queue and contradiction detection

### v2.0 (2026-03-25)
- ✅ Integrated real OpenAI Embedding API
- ✅ Created standalone agent-memory-qdrant container
- ✅ Fixed Qdrant Python client connection issue (NO_PROXY)
- ✅ Updated memory_service.py to use standalone container
- ✅ Full test passed (semantic similarity 0.4890)

### v1.0 (2026-03-24)
- ✅ Implemented tiered storage architecture
- ✅ Implemented memory evolution system
- ✅ Created memory_service.py
- ✅ Qdrant vector storage integration

---

## 📄 License

MIT

---

## 🙏 Acknowledgments

- [OpenClaw](https://github.com/openclaw/openclaw)
- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [OpenAI Embeddings](https://platform.openai.com/docs/guides/embeddings)
