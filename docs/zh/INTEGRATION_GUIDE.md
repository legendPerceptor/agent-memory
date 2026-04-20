# 为其他 Agent 安装 Memory 系统

[🌐 English](../../en/INTEGRATION_GUIDE.md) | **中文**

本指南帮助您为其他 AI Agent（如 Mia）安装 Agent Memory 系统。

---

## 🎯 前提条件

1. **Agent Memory 已部署**
   - agent-memory-qdrant 容器运行中
   - OpenAI API Key 已配置
   - 测试通过

2. **目标 Agent 要求**
   - Python 3.11+
   - 能访问 Docker 网络
   - 有持久化存储

---

## 🚀 快速安装

### Step 1: 连接到 Qdrant 网络

```bash
# 检查 agent-memory-qdrant 网络
docker network inspect proxy-net | grep agent-memory-qdrant

# 如果目标 agent 在容器中，连接到同一网络
docker network connect proxy-net <your-agent-container>
```

### Step 2: 复制 Memory 系统文件

```bash
# 创建目标目录
mkdir -p /path/to/your-agent/memory

# 复制核心文件
cp -r ~/.openclaw/workspace/ai-memory/vector-memory /path/to/your-agent/memory/
cp ~/.openclaw/workspace/ai-memory/.env.example /path/to/your-agent/.env
cp ~/.openclaw/scripts/init_memory.py /path/to/your-agent/scripts/
```

### Step 3: 配置环境变量

```bash
# 编辑 .env
nano /path/to/your-agent/.env

# 必填项
QDRANT_HOST=agent-memory-qdrant
QDRANT_PORT=6333
OPENAI_API_KEY=sk-proj-...

# 代理（如果需要）
HTTP_PROXY=http://xray:1087
HTTPS_PROXY=http://xray:1087
```

### Step 4: 安装依赖

```bash
cd /path/to/your-agent
python3 -m venv venv
. venv/bin/activate
pip install -r memory/vector-memory/requirements.txt
```

### Step 5: 集成到启动流程

在您的 agent 启动脚本中添加：

```python
# 在导入任何模块之前
import os
os.environ['NO_PROXY'] = '*'
os.environ['no_proxy'] = '*'

# 导入 memory 系统
from init_memory import initialize_memory, get_context_for_query, remember_fact

# 初始化
memory = initialize_memory()

# 使用示例
# 检索上下文
context = get_context_for_query("用户偏好")

# 记录重要信息
remember_fact("用户喜欢简洁的回复", importance=0.8, tags=["user", "preference"])
```

---

## 📖 API 参考

### `initialize_memory()`

初始化记忆服务。

```python
from init_memory import initialize_memory

memory = initialize_memory()
```

**返回：** MemoryService 实例或 None

---

### `get_context_for_query(query, limit=10)`

检索相关记忆。

```python
from init_memory import get_context_for_query

# 检索
results = get_context_for_query("用户的编程偏好", limit=5)

for result in results:
    print(f"内容: {result['content']}")
    print(f"相似度: {result.get('score', 0):.4f}")
```

**参数：**
- `query` (str): 查询文本
- `limit` (int): 最大返回数量

**返回：** list[dict]

---

### `remember_fact(content, importance=0.7, tags=None)`

记录重要事实。

```python
from init_memory import remember_fact

memory_id = remember_fact(
    content="用户喜欢使用 Python",
    importance=0.8,
    tags=["user", "preference", "programming"]
)
```

**参数：**
- `content` (str): 记忆内容
- `importance` (float): 重要性 (0.0-1.0)
- `tags` (list): 标签列表

**返回：** memory_id 或 None

---

### `remember_event(content, importance=0.6, tags=None)`

记录重要事件。

```python
from init_memory import remember_event

memory_id = remember_event(
    content="用户部署了新版本到生产环境",
    importance=0.7,
    tags=["deployment", "production"]
)
```

---

## 🏗️ 高级用法

### 直接使用 MemoryService

```python
import sys
sys.path.insert(0, '/path/to/ai-memory/vector-memory')

from memory_service import MemoryService

service = MemoryService()

# 批量记录
memories = [
    ("用户使用 GLM-5", "fact", 0.7, ["user", "model"]),
    ("用户偏好简洁回复", "preference", 0.8, ["user", "preference"]),
]

for content, mtype, importance, tags in memories:
    service.remember(content, mtype, importance, tags)

# 高级检索
results = service.recall(
    query="用户的偏好设置",
    limit=10,
    min_importance=0.5,
    memory_type="preference"
)
```

### 使用批量 Embedding

```python
from batch_embedding import get_embeddings

# 批量获取 embedding（自动缓存）
texts = ["文本1", "文本2", "文本3"]
embeddings = get_embeddings(texts)

print(f"获取了 {len(embeddings)} 个 embedding")
```

---

## 🔧 配置选项

### 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `QDRANT_HOST` | `agent-memory-qdrant` | Qdrant 主机 |
| `QDRANT_PORT` | `6333` | Qdrant 端口 |
| `OPENAI_API_KEY` | - | OpenAI API Key |
| `OPENAI_EMBEDDING_MODEL` | `text-embedding-3-small` | Embedding 模型 |
| `HTTP_PROXY` | - | HTTP 代理 |
| `HTTPS_PROXY` | - | HTTPS 代理 |

---

## 🐛 故障排查

### 问题 1: 无法连接 Qdrant

```bash
# 检查 Qdrant 状态
docker ps | grep agent-memory-qdrant

# 测试连接
curl http://agent-memory-qdrant:6333/collections

# 如果失败，检查网络
docker network connect proxy-net <your-agent-container>
```

### 问题 2: OpenAI API 超时

```bash
# 检查代理
curl -x http://xray:1087 https://api.openai.com/v1/models

# 如果失败，检查 xray 容器
docker ps | grep xray
```

### 问题 3: ImportError

```bash
# 确保依赖已安装
pip install qdrant-client openai httpx

# 检查 Python 路径
python3 -c "import sys; print('\n'.join(sys.path))"
```

---

## 📊 性能优化

### 批量 Embedding

```python
from batch_embedding import BatchEmbeddingService

service = BatchEmbeddingService(use_cache=True)

# 批量处理（减少 API 调用）
texts = ["文本1", "文本2", ..., "文本100"]
embeddings = service.get_embeddings(texts)  # 1 次 API 调用

# 缓存统计
stats = service.get_cache_stats()
print(f"缓存: {stats['size']} 条")
```

### 缓存管理

```python
# 清空缓存
service.clear_cache()

# 查看缓存位置
print(service.cache.cache_file)
```

---

## 🔐 安全建议

1. **API Key 保护**
   ```bash
   # 不要提交 .env 到 git
   echo ".env" >> .gitignore
   
   # 使用环境变量
   export OPENAI_API_KEY="sk-proj-..."
   ```

2. **网络隔离**
   ```bash
   # 只允许内部网络访问
   docker network create --internal agent-internal
   ```

3. **数据备份**
   ```bash
   # 定期备份
   docker exec agent-memory-qdrant tar -czf /tmp/backup.tar.gz -C /qdrant/storage .
   docker cp agent-memory-qdrant:/tmp/backup.tar.gz ./backups/
   ```

---

## 📝 示例：Mia Agent 集成

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
        # 初始化 memory
        self.memory = initialize_memory()
        
        # 加载用户上下文
        self.user_context = get_context_for_query("用户偏好", limit=10)
    
    def process_message(self, message: str) -> str:
        # 检索相关记忆
        context = get_context_for_query(message, limit=5)
        
        # 使用上下文生成回复
        response = self._generate_response(message, context)
        
        # 记录重要信息
        if self._is_important(message):
            remember_fact(
                content=message,
                importance=0.7,
                tags=["user", "conversation"]
            )
        
        return response
    
    def _generate_response(self, message: str, context: list) -> str:
        # 使用记忆上下文生成回复
        # ...
        pass
    
    def _is_important(self, message: str) -> bool:
        # 判断是否重要
        keywords = ["喜欢", "偏好", "选择", "决定"]
        return any(kw in message for kw in keywords)

# 启动 Mia
if __name__ == "__main__":
    mia = MiaAgent()
    print("✅ Mia 已启动，Memory 系统已就绪")
```

---

## ✅ 验证清单

安装完成后，检查以下项目：

- [ ] `agent-memory-qdrant` 容器运行中
- [ ] 可以访问 `http://agent-memory-qdrant:6333`
- [ ] `.env` 文件配置正确
- [ ] 依赖已安装（qdrant-client, openai, httpx）
- [ ] `init_memory.py` 测试通过
- [ ] 可以检索和记录记忆

---

**更新日期：** 2026-03-25
**版本：** v2.1
**状态：** ✅ 生产就绪
