# Agent Memory Qdrant Container Documentation

**English** | [🌐 中文](../../zh/AGENT_MEMORY_QDRANT.md)

## 🎯 Container Information

**Container Name:** `agent-memory-qdrant`
**Image:** `qdrant/qdrant:latest`
**Network:** `proxy-net`
**Restart Policy:** `unless-stopped`

**Port Mapping:**
- HTTP API: `6336 -> 6333`
- gRPC API: `6337 -> 6334`

**Data Volume:** `agent_memory_qdrant_data`

---

## 🔌 Connection Methods

### From OpenClaw Container (Recommended)

```python
import os
os.environ['NO_PROXY'] = '*'  # ⚠️ Must be set before importing

from qdrant_client import QdrantClient

client = QdrantClient(
    host="agent-memory-qdrant",
    port=6333
)
```

### From Host Machine

```bash
# HTTP API
curl http://localhost:6336/collections

# Python client
from qdrant_client import QdrantClient
client = QdrantClient(host="localhost", port=6336)
```

---

## 💾 Data Persistence

### Docker Volume

**Name:** `agent_memory_qdrant_data`
**Location:** `/qdrant/storage` (inside container)

**View volume:**
```bash
docker volume inspect agent_memory_qdrant_data
```

**Volume Location (host):**
```
/var/lib/docker/volumes/agent_memory_qdrant_data/_data
```

---

## 🔄 Backup Strategy

### Method 1: Manual Backup (Recommended)

```bash
# Create backup
docker exec agent-memory-qdrant tar -czf /tmp/backup.tar.gz -C /qdrant/storage .

# Copy to host
docker cp agent-memory-qdrant:/tmp/backup.tar.gz \
  ~/.openclaw/workspace/ai-memory/backups/qdrant_backup_$(date +%Y%m%d_%H%M%S).tar.gz

# Clean up temporary file in container
docker exec agent-memory-qdrant rm /tmp/backup.tar.gz
```

### Method 2: Snapshot Export (API Method)

```bash
# Create snapshot
curl -X POST http://localhost:6336/collections/agent_memories/snapshots

# Download snapshot
curl http://localhost:6336/collections/agent_memories/snapshots \
  | jq -r '.result[0].name'
```

### Method 3: Scheduled Auto Backup (crontab)

```bash
# Edit crontab
crontab -e

# Add daily backup at 2 AM
0 2 * * * docker exec agent-memory-qdrant tar -czf /tmp/backup.tar.gz -C /qdrant/storage . && docker cp agent-memory-qdrant:/tmp/backup.tar.gz /backups/qdrant_$(date +\%Y\%m\%d).tar.gz
```

---

## 🔧 Maintenance Commands

### View Logs

```bash
docker logs -f agent-memory-qdrant
```

### Restart Container

```bash
docker restart agent-memory-qdrant
```

### Stop Container

```bash
docker stop agent-memory-qdrant
```

### Start Container

```bash
docker start agent-memory-qdrant
```

### Remove Container (⚠️ Data preserved in volume)

```bash
docker rm -f agent-memory-qdrant
```

### Delete Data (⚠️ Dangerous Operation!)

```bash
# Stop container
docker stop agent-memory-qdrant

# Delete volume
docker volume rm agent_memory_qdrant_data

# Restart container (will create new empty volume)
docker start agent-memory-qdrant
```

---

## 📊 Monitoring

### Check Health Status

```bash
curl http://agent-memory-qdrant:6333/health
```

### View Collection Statistics

```bash
curl http://agent-memory-qdrant:6333/collections/agent_memories
```

### View Disk Usage

```bash
docker exec agent-memory-qdrant du -sh /qdrant/storage
```

---

## 🔐 Security Recommendations

1. **Don't expose to public internet** - Ports only available on internal network
2. **Regular backups** - At least once daily
3. **Monitor disk space** - Qdrant data will grow continuously
4. **Restrict access** - Only OpenClaw container should have access

---

## 📝 Collection Naming Convention

**Recommended collection names:**
- `agent_memories` - Main memory storage
- `agent_knowledge` - Knowledge graph
- `agent_conversations` - Conversation history
- `agent_decisions` - Decision records

**Naming Rules:**
- Use snake_case
- Prefix with `agent_` to avoid conflicts with aicreatorvault
- Semantic naming

---

## 🚀 Performance Optimization

### Memory Configuration

```bash
# View Qdrant memory usage
docker stats agent-memory-qdrant
```

### Index Optimization

```python
# Configure HNSW index when creating collection
from qdrant_client.models import VectorParams, HnswConfig

client.create_collection(
    collection_name="agent_memories",
    vectors_config=VectorParams(
        size=1536,
        distance=Distance.COSINE,
        hnsw_config=HnswConfig(
            m=16,  # Connections per node
            ef_construct=100  # Search scope during index construction
        )
    )
)
```

---

## 🆚 Comparison with aicreatorvault-qdrant

| Feature | agent-memory-qdrant | aicreatorvault-qdrant |
|---------|---------------------|----------------------|
| **Purpose** | Agent memory vectors | Image vector search |
| **Ports** | 6336/6337 | 6333/6334 |
| **Data** | Independent storage | Independent storage |
| **Network** | proxy-net | aicreatorvault-net |
| **Restart** | No mutual impact | No mutual impact |

---

**Created:** 2026-03-24
**Status:** ✅ Running
**Next Backup:** Manual or configure crontab
