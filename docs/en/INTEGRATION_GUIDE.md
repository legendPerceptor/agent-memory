# Installing Memory System for Other Agents

**English** | [🌐 中文](../../zh/INTEGRATION_GUIDE.md)

This guide helps you install the Agent Memory system for other AI Agents (such as Mia).

---

## 🎯 Prerequisites

1. **Agent Memory Deployed**
   - agent-memory-qdrant container running
   - OpenAI API Key configured
   - Tests passed

2. **Target Agent Requirements**
   - Python 3.11+
   - Access to Docker network
   - Persistent storage

---

## 🚀 Quick Installation

### Step 1: Connect to Qdrant Network

```bash
# Check agent-memory-qdrant network
docker network inspect proxy-net | grep agent-memory-qdrant

# If target agent is in a container, connect to the same network
docker network connect proxy-net <your-agent-container>
```

### Step 2: Copy Memory System Files

```bash
# Create target directory
mkdir -p /path/to/your-agent/memory

# Copy core files
cp -r ~/.openclaw/workspace/ai-memory/vector-memory /path/to/your-agent/memory/
cp ~/.openclaw/workspace/ai-memory/.env.example /path/to/your-agent/.env
cp ~/.openclaw/scripts/init_memory.py /path/to/your-agent/scripts/
```

### Step 3: Configure Environment Variables

```bash
# Edit .env
nano /path/to/your-agent/.env

# Required fields
QDRANT_HOST=agent-memory-qdrant
QDRANT_PORT=6333
OPENAI_API_KEY=sk-proj-...

# Proxy (if needed)
HTTP_PROXY=http://xray:1087
HTTPS_PROXY=http://xray:1087
```

### Step 4: Install Dependencies

```bash
cd /path/to/your-agent
python3 -m venv venv
. venv/bin/activate
pip install -r memory/vector-memory/requirements.txt
```

### Step 5: Integrate into Startup Flow

Add to your agent startup script:

```python
# Before importing any modules
import os
os.environ['NO_PROXY'] = '*'
os.environ['no_proxy'] = '*'

# Import memory system
from init_memory import initialize_memory, get_context_for_query, remember_fact

# Initialize
memory = initialize_memory()

# Usage examples
# Retrieve context
context = get_context_for_query("user preferences")

# Record important information
remember_fact("User prefers concise replies", importance=0.8, tags=["user", "preference"])
```

---

## 📖 API Reference

### `initialize_memory()`

Initialize memory service.

```python
from init_memory import initialize_memory

memory = initialize_memory()
```

**Returns:** MemoryService instance or None

---

### `get_context_for_query(query, limit=10)`

Retrieve related memories.

```python
from init_memory import get_context_for_query

# Retrieve
results = get_context_for_query("user programming preferences", limit=5)

for result in results:
    print(f"Content: {result['content']}")
    print(f"Similarity: {result.get('score', 0):.4f}")
```

**Parameters:**
- `query` (str): Query text
- `limit` (int): Maximum return count

**Returns:** list[dict]

---

### `remember_fact(content, importance=0.7, tags=None)`

Record important facts.

```python
from init_memory import remember_fact

memory_id = remember_fact(
    content="User prefers using Python",
    importance=0.8,
    tags=["user", "preference", "programming"]
)
```

**Parameters:**
- `content` (str): Memory content
- `importance` (float): Importance (0.0-1.0)
- `tags` (list): Tag list

**Returns:** memory_id or None

---

### `remember_event(content, importance=0.6, tags=None)`

Record important events.

```python
from init_memory import remember_event

memory_id = remember_event(
    content="User deployed new version to production",
    importance=0.7,
    tags=["deployment", "production"]
)
```

---

## 🏗️ Advanced Usage

### Using MemoryService Directly

```python
import sys
sys.path.insert(0, '/path/to/ai-memory/vector-memory')

from memory_service import MemoryService

service = MemoryService()

# Batch recording
memories = [
    ("User uses GLM-5", "fact", 0.7, ["user", "model"]),
    ("User prefers concise replies", "preference", 0.8, ["user", "preference"]),
]

for content, mtype, importance, tags in memories:
    service.remember(content, mtype, importance, tags)

# Advanced retrieval
results = service.recall(
    query="user preference settings",
    limit=10,
    min_importance=0.5,
    memory_type="preference"
)
```

### Using Batch Embedding

```python
from batch_embedding import get_embeddings

# Batch get embeddings (auto-cached)
texts = ["Text 1", "Text 2", "Text 3"]
embeddings = get_embeddings(texts)

print(f"Got {len(embeddings)} embeddings")
```

---

## 🔧 Configuration Options

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `QDRANT_HOST` | `agent-memory-qdrant` | Qdrant host |
| `QDRANT_PORT` | `6333` | Qdrant port |
| `OPENAI_API_KEY` | - | OpenAI API Key |
| `OPENAI_EMBEDDING_MODEL` | `text-embedding-3-small` | Embedding model |
| `HTTP_PROXY` | - | HTTP proxy |
| `HTTPS_PROXY` | - | HTTPS proxy |

---

## 🐛 Troubleshooting

### Issue 1: Cannot Connect to Qdrant

```bash
# Check Qdrant status
docker ps | grep agent-memory-qdrant

# Test connection
curl http://agent-memory-qdrant:6333/collections

# If failed, check network
docker network connect proxy-net <your-agent-container>
```

### Issue 2: OpenAI API Timeout

```bash
# Check proxy
curl -x http://xray:1087 https://api.openai.com/v1/models

# If failed, check xray container
docker ps | grep xray
```

### Issue 3: ImportError

```bash
# Ensure dependencies are installed
pip install qdrant-client openai httpx

# Check Python path
python3 -c "import sys; print('\n'.join(sys.path))"
```

---

## 📊 Performance Optimization

### Batch Embedding

```python
from batch_embedding import BatchEmbeddingService

service = BatchEmbeddingService(use_cache=True)

# Batch processing (reduce API calls)
texts = ["Text 1", "Text 2", ..., "Text 100"]
embeddings = service.get_embeddings(texts)  # 1 API call

# Cache statistics
stats = service.get_cache_stats()
print(f"Cache: {stats['size']} entries")
```

### Cache Management

```python
# Clear cache
service.clear_cache()

# View cache location
print(service.cache.cache_file)
```

---

## 🔐 Security Recommendations

1. **API Key Protection**
   ```bash
   # Don't commit .env to git
   echo ".env" >> .gitignore
   
   # Use environment variables
   export OPENAI_API_KEY="sk-proj-..."
   ```

2. **Network Isolation**
   ```bash
   # Only allow internal network access
   docker network create --internal agent-internal
   ```

3. **Data Backup**
   ```bash
   # Regular backups
   docker exec agent-memory-qdrant tar -czf /tmp/backup.tar.gz -C /qdrant/storage .
   docker cp agent-memory-qdrant:/tmp/backup.tar.gz ./backups/
   ```

---

## 📝 Example: Mia Agent Integration

```python
#!/usr/bin/env python3
"""
Mia Agent - with Memory Integration
"""

import os
os.environ['NO_PROXY'] = '*'
os.environ['no_proxy'] = '*'

from init_memory import (
    initialize_memory,
    get_context_for_query,
    remember_fact,
    remember_event
)

class MiaAgent:
    def __init__(self):
        # Initialize memory
        self.memory = initialize_memory()
        
        # Load user context
        self.user_context = get_context_for_query("user preferences", limit=10)
    
    def process_message(self, message: str) -> str:
        # Retrieve related memories
        context = get_context_for_query(message, limit=5)
        
        # Generate response using context
        response = self._generate_response(message, context)
        
        # Record important information
        if self._is_important(message):
            remember_fact(
                content=message,
                importance=0.7,
                tags=["user", "conversation"]
            )
        
        return response
    
    def _generate_response(self, message: str, context: list) -> str:
        # Generate response using memory context
        # ...
        pass
    
    def _is_important(self, message: str) -> bool:
        # Determine if important
        keywords = ["like", "prefer", "choose", "decide"]
        return any(kw in message for kw in keywords)

# Start Mia
if __name__ == "__main__":
    mia = MiaAgent()
    print("✅ Mia started, Memory system ready")
```

---

## ✅ Verification Checklist

After installation, check the following items:

- [ ] `agent-memory-qdrant` container running
- [ ] Can access `http://agent-memory-qdrant:6333`
- [ ] `.env` file configured correctly
- [ ] Dependencies installed (qdrant-client, openai, httpx)
- [ ] `init_memory.py` test passed
- [ ] Can retrieve and record memories

---

**Updated:** 2026-03-25
**Version:** v2.1
**Status:** ✅ Production Ready
