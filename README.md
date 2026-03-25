<<<<<<< HEAD
# AI Memory 项目

## 项目结构

```
ai-memory/
├── README.md                    # 猱究报告（4,495 字符)
├── IMPROVEMENT_PLAN.md            # 优化计划（3,158 字符)
├── QUICKSTART.md                  # 快速开始指南
├── vector_memory.py               # 向量记忆服务
├── simple_sync.py                  # 缀化同步脚本
└── experiments/
    ├── memory-stats.sh            # Token 统计工具
    └── weekly-summary.py             # 自动摘要生成器
=======
# AI Memory - Agent 记忆向量系统

**一个为 AI Agent 设计的分层记忆系统，支持向量检索、自动演化、知识图谱**

## 🌟 特性

### ✅ 已实现

- **向量记忆存储** - 使用 Qdrant 进行高效的语义检索
- **分层存储架构** - Core / Working / Recall / Archival 四层记忆
- **记忆演化系统** - 自动去重、智能更新、过时删除
- **文件存储回退** - 当 Qdrant 不可用时自动回退到文件存储
- **多类型支持** - fact / event / preference / decision

### 🚧 开发中

- 真实 OpenAI Embedding 集成（目前使用伪向量）
- 知识图谱记忆
- 时间感知记忆（Bi-temporal）
- 记忆自动压缩
- Web UI 管理界面

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

# 记录记忆
service.remember(
    content="用户偏好使用深色主题",
    memory_type="preference",
    importance=0.7,
    tags=["ui", "theme"]
)

# 检索记忆
results = service.recall("用户界面偏好", limit=5)
for result in results:
    print(result['content'])

# 查看统计
stats = service.stats()
print(f"总记忆数: {stats['count']}")
```

### 在 OpenClaw 中使用

```python
# 在 OpenClaw 启动时自动初始化
from init_memory import initialize_memory, get_context_for_query

# 初始化
service = initialize_memory()

# 检索上下文
context = get_context_for_query("用户的编程偏好")
```

---

## 🏗️ 架构设计

### 分层存储架构

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

### 记忆演化系统

```python
from memory_evolver import MemoryEvolver

evolver = MemoryEvolver()

# 场景 1: 矛盾更新
evolver.evolve("用户使用 GLM-5")      # ADD
evolver.evolve("用户改用 MiniMax")    # UPDATE

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

---

## 📂 项目结构

```
ai-memory/
├── vector-memory/
│   ├── memory_service.py      # 核心记忆服务
│   ├── tiered_memory.py       # 分层存储
│   ├── memory_evolver.py      # 记忆演化
│   └── requirements.txt       # 依赖
│
├── test_agent_memory_qdrant.py    # Qdrant 连接测试
├── test_memory_service.py         # 服务测试
│
├── .env.example               # 配置模板
├── docker-compose.yml         # Docker 配置
├── AGENT_MEMORY_QDRANT.md     # 容器文档
└── README.md                  # 本文件
>>>>>>> 4cfd366 (Initial commit: Agent Memory vector system)
```

---

<<<<<<< HEAD
## ✅ 已完成的工作

### 1. 手动优化（立即生效)
- ✅ 归档旧日志（3 个文件)
- ✅ 创建本周摘要 `2026-W12.md`
- ✅ 磾简 MEMORY.md
- ✅ **Token 优化： 3,163 → 2,961 (-6%)

### 2. 向量化准备（已完成)
- ✅ `vector_memory.py` - 向量记忆服务类
- ✅ `simple_sync.py` - 同步脚本
- ✅ Qdrant collection `agent_memories` 已创建

### 3. 网络问题（待解决)
- ⚠️ OpenClaw 容器与 Qdrant 容器网络隔离
- ✅ 需要将两个容器连接到同一网络

---

## 下一步行动

### 立即可做（在 NAS 宿主机执行)

```bash
# 让 OpenClaw 和 Qdrant 在同一网络
docker network connect aicreatorvault_aicreatorvault-net 1panel_openclaw-1
docker network connect aicreatorvault_aicreatorvault-net aicreatorvault-qdrant-1

# 重启 OpenClaw
docker restart 1panel_openclaw-1
```

执行后，向量化 memory 就准备好了。你可以：
- 运行 `simple_sync.py` 同步记忆
- 通过 `memory.recall("关键词")` 检索相关记忆
=======
## 🔧 配置说明

### Qdrant 配置

| 环境变量 | 默认值 | 说明 |
|---------|--------|------|
| QDRANT_HOST | agent-memory-qdrant | Qdrant 主机名 |
| QDRANT_PORT | 6333 | Qdrant 端口 |

### OpenAI 配置

| 环境变量 | 默认值 | 说明 |
|---------|--------|------|
| OPENAI_API_KEY | - | OpenAI API Key（必填） |
| OPENAI_EMBEDDING_MODEL | text-embedding-3-small | Embedding 模型 |

---

## 🔄 数据备份

### 手动备份

```bash
# 创建备份
docker exec agent-memory-qdrant tar -czf /tmp/backup.tar.gz -C /qdrant/storage .

# 复制到本地
docker cp agent-memory-qdrant:/tmp/backup.tar.gz ./backups/
```

### 自动备份（crontab）

```bash
# 每天凌晨 2 点备份
0 2 * * * docker exec agent-memory-qdrant tar -czf /tmp/backup.tar.gz -C /qdrant/storage . && docker cp agent-memory-qdrant:/tmp/backup.tar.gz ~/backups/qdrant_$(date +\%Y\%m\%d).tar.gz
```

---

## 🛠️ 开发计划

### Phase 2: 核心功能完善（1-2 周）
- [x] Qdrant 连接修复
- [ ] 真实 OpenAI Embedding
- [ ] 记忆压缩功能
- [ ] 性能优化

### Phase 3: 高级功能（1-2 月）
- [ ] 知识图谱记忆
- [ ] 时间感知记忆
- [ ] 异步优化
- [ ] 批量操作

### Phase 4: 生产就绪（2-3 月）
- [ ] 多用户协作
- [ ] Web UI
- [ ] 性能监控
- [ ] API 文档

---

## 📝 更新日志

### 2026-03-25
- ✅ 创建独立的 agent-memory-qdrant 容器
- ✅ 修复 Qdrant Python 客户端连接问题（NO_PROXY）
- ✅ 更新 memory_service.py 使用独立容器
- ✅ 完整测试通过

### 2026-03-24
- ✅ 实现分层存储架构
- ✅ 实现记忆演化系统
- ✅ 创建 memory_service.py

---

## 📄 License

MIT

---

## 👤 作者

OpenClaw Agent Memory Team

---

## 🔗 相关链接

- [OpenClaw](https://github.com/openclaw/openclaw)
- [Qdrant 文档](https://qdrant.tech/documentation/)
- [OpenAI Embeddings](https://platform.openai.com/docs/guides/embeddings)
>>>>>>> 4cfd366 (Initial commit: Agent Memory vector system)
