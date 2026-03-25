# Agent Memory - AI Agent 记忆向量系统

**一个为 AI Agent 设计的分层记忆系统，支持向量检索、自动演化、知识图谱**

[![GitHub](https://img.shields.io/badge/GitHub-legendPerceptor/agent--memory-blue)](https://github.com/legendPerceptor/agent-memory)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11+-blue)](https://www.python.org/)

---

## 🌟 特性

### ✅ 已实现

- **向量记忆存储** - 使用 Qdrant 进行高效的语义检索
- **真实 OpenAI Embedding** - text-embedding-3-small (1536 维)
- **分层存储架构** - Core / Working / Recall / Archival 四层记忆
- **记忆演化系统** - 自动去重、智能更新、过时删除
- **文件存储回退** - 当 Qdrant 不可用时自动回退到文件存储
- **多类型支持** - fact / event / preference / decision
- **独立 Qdrant 容器** - agent-memory-qdrant（独立于 aicreatorvault）

### 🚧 开发中

- 知识图谱记忆
- 时间感知记忆（Bi-temporal）
- 记忆自动压缩
- Web UI 管理界面
- 本地 embedding 模型支持

---

## 🚀 快速开始

### 1. 启动 Qdrant 容器

```bash
# 启动独立的 agent-memory-qdrant 容器
docker run -d \
  --name agent-memory-qdrant \
  --network proxy-net \
  --restart unless-stopped \
  -p 6336:6333 \
  -p 6337:6334 \
  -v agent_memory_qdrant_data:/qdrant/storage \
  qdrant/qdrant:latest
```

### 2. 配置环境变量

```bash
# 复制配置模板
cp .env.example .env

# 编辑配置
nano .env

# 必须设置：
# - QDRANT_HOST=agent-memory-qdrant
# - OPENAI_API_KEY=sk-proj-...
# - HTTP_PROXY=http://xray:1087  # 如果需要代理
```

### 3. 安装依赖

```bash
# 创建虚拟环境
python3 -m venv venv
. venv/bin/activate

# 安装依赖
pip install -r vector-memory/requirements.txt
```

### 4. 测试运行

```bash
# 测试 Qdrant 连接
python3 test_agent_memory_qdrant.py

# 测试完整服务
python3 test_memory_service.py
```

---

## 📖 使用示例

### 基础用法

```python
import sys
sys.path.insert(0, 'vector-memory')

from memory_service import MemoryService

# 初始化服务
service = MemoryService()

# 记录记忆（自动使用真实 OpenAI Embedding）
service.remember(
    content="远见喜欢英雄联盟，助手叫阿卡丽",
    memory_type="preference",
    importance=0.8,
    tags=["user", "game", "preference"]
)

# 语义检索
results = service.recall("远见喜欢什么游戏", limit=5)
for result in results:
    print(f"{result['content']} (相似度: {result.get('score', 0):.4f})")

# 查看统计
stats = service.stats()
print(f"总记忆数: {stats['count']}")
print(f"存储方式: {stats['storage']}")
```

### OpenClaw 集成

```python
# 在 OpenClaw 启动时自动初始化
from init_memory import initialize_memory, get_context_for_query

# 初始化
service = initialize_memory()

# 检索上下文
context = get_context_for_query("用户的编程偏好")
```

---

## 🏗️ 分层存储架构

```
Level 1: Core Memory (核心记忆)
├── 用户档案
├── 当前任务
├── 重要偏好
└── 始终在 context window

Level 2: Working Memory (工作记忆)
├── 最近 50 条对话
├── 自动轮换 (FIFO)
└── 临时上下文

Level 3: Recall Memory (回忆记忆)
├── 完整历史记录
├── 向量索引
└── 语义检索

Level 4: Archival Memory (归档记忆)
├── 压缩摘要
├── 长期存储
└── 定期归档
```

---

## 🧠 记忆演化系统

```python
from memory_evolver import MemoryEvolver

evolver = MemoryEvolver()

# 场景 1: 矛盾更新
evolver.evolve("用户使用 GLM-5")      # ADD
evolver.evolve("用户改用 MiniMax")    # UPDATE (自动替换)

# 场景 2: 重复跳过
evolver.evolve("用户偏好简洁回复")    # ADD
evolver.evolve("用户喜欢简洁的回复")  # NOOP (相似度 > 0.95)

# 场景 3: 过时删除
evolver.evolve("临时测试配置")        # DELETE
```

---

## 📊 性能指标

| 指标 | 当前 | 目标 | 改进 |
|------|------|------|------|
| 启动 Token | ~2,961 | ~1,000 | -66% |
| 记忆容量 | ~100 条 | ~10,000 条 | 100x |
| 查找速度 | O(n) | O(log n) | 50x |
| 历史压缩 | 0% | 90% | 90% |
| 语义相似度 | 0.4890 | - | ✅ 真实向量 |

---

## 🔧 配置说明

### 环境变量

| 环境变量 | 默认值 | 说明 |
|---------|--------|------|
| `QDRANT_HOST` | `agent-memory-qdrant` | Qdrant 主机名 |
| `QDRANT_PORT` | `6333` | Qdrant 端口 |
| `OPENAI_API_KEY` | - | OpenAI API Key（必填） |
| `OPENAI_EMBEDDING_MODEL` | `text-embedding-3-small` | Embedding 模型 |
| `HTTP_PROXY` | - | HTTP 代理（可选） |
| `HTTPS_PROXY` | - | HTTPS 代理（可选） |

---

## 💾 数据备份

```bash
# 创建备份
docker exec agent-memory-qdrant tar -czf /tmp/backup.tar.gz -C /qdrant/storage .

# 复制到本地
docker cp agent-memory-qdrant:/tmp/backup.tar.gz ./backups/

# 定期备份 (crontab)
# 每天凌晨 2 点备份
0 2 * * * docker exec agent-memory-qdrant tar -czf /tmp/backup.tar.gz -C /qdrant/storage . && docker cp agent-memory-qdrant:/tmp/backup.tar.gz ~/backups/qdrant_$(date +\%Y\%m\%d).tar.gz
```

---

## 🗂️ 项目结构

```
ai-memory/
├── vector-memory/
│   ├── memory_service.py      # 核心记忆服务
│   ├── tiered_memory.py       # 分层存储
│   ├── memory_evolver.py      # 记忆演化
│   └── requirements.txt       # 依赖
│
├── test_agent_memory_qdrant.py  # Qdrant 连接测试
├── test_memory_service.py       # 服务测试
│
├── .env.example                 # 配置模板
├── docker-compose.yml           # Docker 配置
├── AGENT_MEMORY_QDRANT.md       # 容器文档
└── README.md                    # 本文件
```

---

## 🚧 开发路线图

### Phase 2: 核心功能完善
- [x] Qdrant 连接修复
- [x] 真实 OpenAI Embedding
- [ ] 记忆压缩功能
- [ ] 性能优化

### Phase 3: 高级功能
- [ ] 知识图谱记忆
- [ ] 时间感知记忆
- [ ] 异步优化
- [ ] 批量操作

### Phase 4: 生产就绪
- [ ] 多用户协作
- [ ] Web UI
- [ ] 性能监控
- [ ] API 文档

---

## 📝 更新日志

### v2.0 (2026-03-25)
- ✅ 集成真实 OpenAI Embedding API
- ✅ 创建独立的 agent-memory-qdrant 容器
- ✅ 修复 Qdrant Python 客户端连接问题（NO_PROXY）
- ✅ 更新 memory_service.py 使用独立容器
- ✅ 完整测试通过（语义相似度 0.4890）

### v1.0 (2026-03-24)
- ✅ 实现分层存储架构
- ✅ 实现记忆演化系统
- ✅ 创建 memory_service.py
- ✅ Qdrant 向量存储集成

---

## 📄 License

MIT

---

## 🙏 致谢

- [OpenClaw](https://github.com/openclaw/openclaw)
- [Qdrant 文档](https://qdrant.tech/documentation/)
- [OpenAI Embeddings](https://platform.openai.com/docs/guides/embeddings)
