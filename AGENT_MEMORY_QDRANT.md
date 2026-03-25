# Agent Memory Qdrant 容器文档

## 🎯 容器信息

**容器名称：** `agent-memory-qdrant`
**镜像：** `qdrant/qdrant:latest`
**网络：** `proxy-net`
**重启策略：** `unless-stopped`

**端口映射：**
- HTTP API: `6336 -> 6333`
- gRPC API: `6337 -> 6334`

**数据卷：** `agent_memory_qdrant_data`

---

## 🔌 连接方式

### 从 OpenClaw 容器连接（推荐）

```python
import os
os.environ['NO_PROXY'] = '*'  # ⚠️ 必须在导入前设置

from qdrant_client import QdrantClient

client = QdrantClient(
    host="agent-memory-qdrant",
    port=6333
)
```

### 从宿主机连接

```bash
# HTTP API
curl http://localhost:6336/collections

# Python 客户端
from qdrant_client import QdrantClient
client = QdrantClient(host="localhost", port=6336)
```

---

## 💾 数据持久化

### Docker Volume

**名称：** `agent_memory_qdrant_data`
**位置：** `/qdrant/storage`（容器内）

**查看 volume：**
```bash
docker volume inspect agent_memory_qdrant_data
```

**Volume 位置（宿主机）：**
```
/var/lib/docker/volumes/agent_memory_qdrant_data/_data
```

---

## 🔄 备份策略

### 方式 1: 手动备份（推荐）

```bash
# 创建备份
docker exec agent-memory-qdrant tar -czf /tmp/backup.tar.gz -C /qdrant/storage .

# 复制到宿主机
docker cp agent-memory-qdrant:/tmp/backup.tar.gz \
  ~/.openclaw/workspace/ai-memory/backups/qdrant_backup_$(date +%Y%m%d_%H%M%S).tar.gz

# 清理容器内临时文件
docker exec agent-memory-qdrant rm /tmp/backup.tar.gz
```

### 方式 2: 快照导出（API 方式）

```bash
# 创建快照
curl -X POST http://localhost:6336/collections/agent_memories/snapshots

# 下载快照
curl http://localhost:6336/collections/agent_memories/snapshots \
  | jq -r '.result[0].name'
```

### 方式 3: 定期自动备份（crontab）

```bash
# 编辑 crontab
crontab -e

# 添加每天凌晨 2 点备份
0 2 * * * docker exec agent-memory-qdrant tar -czf /tmp/backup.tar.gz -C /qdrant/storage . && docker cp agent-memory-qdrant:/tmp/backup.tar.gz /backups/qdrant_$(date +\%Y\%m\%d).tar.gz
```

---

## 🔧 维护命令

### 查看日志

```bash
docker logs -f agent-memory-qdrant
```

### 重启容器

```bash
docker restart agent-memory-qdrant
```

### 停止容器

```bash
docker stop agent-memory-qdrant
```

### 启动容器

```bash
docker start agent-memory-qdrant
```

### 删除容器（⚠️ 数据会保留在 volume）

```bash
docker rm -f agent-memory-qdrant
```

### 删除数据（⚠️ 危险操作！）

```bash
# 停止容器
docker stop agent-memory-qdrant

# 删除 volume
docker volume rm agent_memory_qdrant_data

# 重新启动容器（会创建新的空 volume）
docker start agent-memory-qdrant
```

---

## 📊 监控

### 检查健康状态

```bash
curl http://agent-memory-qdrant:6333/health
```

### 查看 collection 统计

```bash
curl http://agent-memory-qdrant:6333/collections/agent_memories
```

### 查看磁盘使用

```bash
docker exec agent-memory-qdrant du -sh /qdrant/storage
```

---

## 🔐 安全建议

1. **不要暴露到公网** - 端口只在内部网络可用
2. **定期备份** - 每天至少备份一次
3. **监控磁盘空间** - Qdrant 数据会持续增长
4. **限制访问** - 只有 OpenClaw 容器可以访问

---

## 📝 Collection 命名规范

**推荐的 collection 名称：**
- `agent_memories` - 主记忆存储
- `agent_knowledge` - 知识图谱
- `agent_conversations` - 对话历史
- `agent_decisions` - 决策记录

**命名规范：**
- 使用 snake_case
- 前缀 `agent_` 避免与 aicreatorvault 冲突
- 语义化命名

---

## 🚀 性能优化

### 内存配置

```bash
# 查看 Qdrant 内存使用
docker stats agent-memory-qdrant
```

### 索引优化

```python
# 创建 collection 时配置 HNSW 索引
from qdrant_client.models import VectorParams, HnswConfig

client.create_collection(
    collection_name="agent_memories",
    vectors_config=VectorParams(
        size=1536,
        distance=Distance.COSINE,
        hnsw_config=HnswConfig(
            m=16,  # 每个 node 的连接数
            ef_construct=100  # 构建索引时的搜索范围
        )
    )
)
```

---

## 🆚 与 aicreatorvault-qdrant 的区别

| 特性 | agent-memory-qdrant | aicreatorvault-qdrant |
|------|---------------------|----------------------|
| **用途** | Agent 记忆向量 | 图片向量搜索 |
| **端口** | 6336/6337 | 6333/6334 |
| **数据** | 独立存储 | 独立存储 |
| **网络** | proxy-net | aicreatorvault-net |
| **重启** | 不影响对方 | 不影响对方 |

---

**创建日期：** 2026-03-24
**状态：** ✅ 运行中
**下次备份：** 手动或配置 crontab
