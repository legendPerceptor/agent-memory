# Agent Memory - AI Agent 记忆向量系统

**一个为 AI Agent 设计的分层记忆系统，支持向量检索、自动演化、知识图谱**

**中文** | [🌐 English](README.md)

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
- **Human-in-the-Loop 反馈系统** - 人类反馈驱动的记忆质量提升
- **文件存储回退** - 当 Qdrant 不可用时自动回退到文件存储
- **多类型支持** - fact / event / preference / decision
- **独立 Qdrant 容器** - agent-memory-qdrant（独立于 aicreatorvault）

### 🚧 开发中

- 时间感知记忆（Bi-temporal）
- 异步优化
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

## 👤 Human-in-the-Loop 反馈系统

通过人类反馈提升记忆质量，支持飞书、CLI、API 等多种反馈渠道。

### 三层反馈架构

```
Layer 1: 写入时反馈
├── 记忆候选项审核（propose → review → confirm/modify/reject）
├── 高置信度自动审批，低置信度等待人工审核
└── 核心记忆变更提案（diff 预览）

Layer 2: 检索时反馈
├── 记忆评价（+1 有用 / -1 无用）
├── 检索相关性反馈
└── 反馈驱动检索参数自适应

Layer 3: 周期性审核
├── 低置信度/矛盾/长期未访问记忆审核
├── 矛盾记忆检测与合并建议
└── 受保护记忆（不可压缩/删除）
```

### 使用示例

```python
from agent_memory import HumanFeedbackManager

manager = HumanFeedbackManager()

# 写入时反馈 - 创建候选项等待审核
candidate = manager.propose_memory(
    content="用户偏好简洁回复",
    memory_type="preference",
    importance=0.8,
    confidence=0.85,
    source="feishu"
)

# 确认候选项
manager.confirm_candidate(candidate.candidate_id, source="feishu")

# 修改候选项后写入
manager.modify_candidate(
    candidate.candidate_id,
    content="用户偏好简洁回复，不喜欢长篇大论",
    importance=0.9,
    reason="用户补充了细节",
    source="feishu"
)

# 拒绝候选项
manager.reject_candidate(candidate.candidate_id, reason="信息不准确", source="feishu")

# 检索时反馈 - 评价记忆
manager.rate_memory(memory_id, rating=1, source="feishu")   # 有用
manager.rate_memory(memory_id, rating=-1, source="feishu")  # 无用

# 检索相关性反馈
manager.submit_relevance_feedback("API 配置", memory_id, relevant=False, source="feishu")

# 自动审批高置信度候选项
manager.auto_approve(confidence_threshold=0.9)

# 周期性审核
queue = manager.generate_review_queue()        # 生成待审核队列
contradictions = manager.detect_contradictions() # 检测矛盾记忆
merges = manager.suggest_merges()               # 建议合并相似记忆
manager.apply_review_decision(memory_id, "protect")  # 保护重要记忆
```

### OpenClaw 集成（飞书反馈）

```python
from agent_memory.integrate import get_memory_service

service = get_memory_service()

# 记录记忆时要求审核
candidate = service.remember("用户使用 MiniMax 模型", require_approval=True)

# 用户在飞书确认/修改/拒绝
service.confirm_candidate(candidate.candidate_id, source="feishu")
service.modify_candidate(candidate.candidate_id, content="修正内容", source="feishu")
service.reject_candidate(candidate.candidate_id, reason="不需要", source="feishu")

# 用户在飞书评价检索结果
service.rate_memory(memory_id, rating=-1, source="feishu")
service.submit_relevance_feedback(query, memory_id, relevant=False, source="feishu")
```

### 反馈数据模型

```python
@dataclass
class MemoryFeedback:
    feedback_id: str           # 反馈 ID
    memory_id: str             # 关联的记忆 ID
    feedback_type: str         # confirm | modify | reject | relevance_up | relevance_down
    original_content: str      # 原始内容
    modified_content: str      # 修改后内容
    original_importance: float # 原始重要性
    modified_importance: float # 修改后重要性
    source: str                # feishu | cli | api
    reason: str                # 反馈原因
    created_at: str            # 反馈时间

@dataclass
class MemoryCandidate:
    candidate_id: str          # 候选项 ID
    content: str               # 记忆内容
    memory_type: str           # 建议分类
    importance: float          # 建议重要性
    confidence: float          # 抽取置信度
    operation: str             # ADD | UPDATE | DELETE
    status: str                # pending | confirmed | modified | rejected
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
agent-memory/
├── agent_memory/
│   ├── __init__.py              # 模块入口
│   ├── config.py                # 配置管理
│   ├── memory_service.py        # 底层向量存储原语（Qdrant + 文件回退）
│   ├── tiered_memory.py         # 分层存储（内部使用 MemoryService）
│   ├── memory_evolver.py        # 记忆演化
│   ├── human_feedback.py        # Human-in-the-Loop 反馈系统
│   ├── hybrid_rag.py            # 混合检索（内部使用 MemoryService）
│   ├── atomic_notes.py          # Zettelkasten 原子笔记
│   ├── knowledge_graph.py       # 知识图谱
│   ├── enhanced_memory_graph.py # 图谱增强记忆
│   ├── memory_compressor.py     # 记忆压缩
│   ├── memory_optimizer.py      # 性能优化
│   ├── batch_embedding.py       # 批量 Embedding
│   └── integrate.py             # OpenClaw 集成入口
│
├── scripts/
│   ├── init_memory.py           # OpenClaw 启动初始化
│   └── benchmark_improvements.py # 性能基准测试
│
├── .env.example                 # 配置模板
├── docker-compose.yml           # Docker 配置
└── README.md                    # 本文件
```

## 🔗 架构关系

```
OpenClawMemoryService (integrate.py)
    │
    ├── MemoryService (memory_service.py)  ← 底层向量存储原语
    │       └── Qdrant / 文件回退
    │
    ├── TieredMemory (tiered_memory.py)
    │       ├── CoreMemory (JSON)
    │       ├── WorkingMemory (内存)
    │       ├── RecallMemory → 内部使用 MemoryService
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

**关键设计**：`MemoryService` 是唯一的底层向量存储原语，`RecallMemory`、`HybridRAG` 等组件内部都委托给它，避免重复的 Qdrant 连接和 embedding 逻辑。

---

## 📚 文档

| 文档 | English | 中文 |
|------|---------|------|
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

## 🚧 开发路线图

### Phase 2: 核心功能完善
- [x] Qdrant 连接修复
- [x] 真实 OpenAI Embedding
- [x] 记忆压缩功能
- [x] 性能优化

### Phase 3: 高级功能
- [x] 知识图谱记忆（`knowledge-graph` 分支）
- [x] Human-in-the-Loop 反馈系统
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

### v2.1 (2026-04-23)
- ✅ 新增 Human-in-the-Loop 反馈系统（写入时反馈、检索时反馈、周期性审核）
- ✅ 记忆候选项审核机制（propose → confirm/modify/reject）
- ✅ 记忆评价与检索相关性反馈
- ✅ 反馈驱动检索参数自适应
- ✅ 核心记忆变更提案（diff 预览）
- ✅ 受保护记忆（不可压缩/删除）
- ✅ 周期性审核队列与矛盾检测

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
