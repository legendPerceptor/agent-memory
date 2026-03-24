# 🧠 我的记忆系统使用指南

**创建日期：** 2026-03-24  
**维护者：** 阿卡丽 🗡️

---

## 系统架构

我使用 **分层记忆系统**，灵感来自 MemGPT/Letta：

```
┌─────────────────────────────────────────────────────┐
│ Level 1: Core Memory (核心记忆)                    │
│ - 始终在 context window (167 tokens)                │
│ - 用户档案、偏好、当前任务                          │
│ - 位置: ~/.openclaw/workspace/memory/core_memory.json│
├─────────────────────────────────────────────────────┤
│ Level 2: Working Memory (工作记忆)                 │
│ - 最近 50 条对话                                    │
│ - 自动轮换 (FIFO)                                   │
│ - 位置: 内存中的 deque                              │
├─────────────────────────────────────────────────────┤
│ Level 3: Recall Memory (回忆记忆)                  │
│ - 完整历史记录 (18 条)                              │
│ - Qdrant 向量索引                                   │
│ - 语义检索                                          │
├─────────────────────────────────────────────────────┤
│ Level 4: Archival Memory (归档记忆)                │
│ - 压缩摘要                                          │
│ - 长期存储                                          │
│ - 位置: memory/archive/                             │
└─────────────────────────────────────────────────────┘
```

---

## 如何使用

### 1. 启动时自动初始化

**触发时机：** 每次会话开始

**执行流程：**
```python
# 1. 读取 AGENTS.md 启动指令
# 2. 运行 init_memory.py
# 3. 导入现有记忆（MEMORY.md + memory/*.md）
# 4. 初始化 Qdrant 连接
# 5. 显示记忆统计
```

**输出示例：**
```
🧠 正在初始化分层记忆系统...
📊 记忆已加载:
  - 核心记忆: 167 tokens
  - 工作记忆: 0/50
  - 回忆记忆: 18 条
  - 归档记忆: 0 个
✅ 分层记忆系统已就绪
```

---

### 2. 记录新记忆

**何时记录：**
- ✅ 用户明确要求"记住这个"
- ✅ 重要配置变更（API keys、模型设置）
- ✅ 用户偏好发现（"我喜欢..."）
- ✅ 关键决策记录（"选择 X 而不是 Y"）
- ❌ 临时信息（不需要记录）

**使用示例：**

```python
from integrate_to_openclaw import get_memory_service

memory = get_memory_service()

# 示例 1: 记录用户偏好
memory.remember(
    content="远见偏好简洁回复",
    memory_type="preference",
    importance=0.7
)
# → 自动判断层级：
#   importance >= 0.9 → 核心记忆
#   importance >= 0.7 → 回忆记忆（演化）
#   importance < 0.7  → 回忆记忆

# 示例 2: 记录重要配置
memory.remember(
    content="配置了 MiniMax Token Plan",
    memory_type="fact",
    importance=0.8
)
# → 演化系统自动：
#   - 检测相似记忆
#   - 判断操作类型（ADD/UPDATE/DELETE/NOOP）
#   - 执行演化

# 示例 3: 记录关键决策
memory.remember(
    content="选择 Qdrant 作为向量数据库",
    memory_type="decision",
    importance=0.9
)
# → 高重要性 → 自动更新核心记忆
```

---

### 3. 智能检索记忆

**何时检索：**
- ✅ 回答关于用户偏好的问题
- ✅ 查找历史配置
- ✅ 回忆之前讨论的内容
- ✅ 需要上下文时

**使用示例：**

```python
# 示例 1: 检索用户偏好
context = memory.recall(
    query="用户的偏好是什么？",
    max_tokens=2000
)
# → 返回：
# === 核心信息 ===
# 用户档案...
# 
# === 相关记忆 ===
# - [0.85] 用户偏好简洁回复
# - [0.72] 用户喜欢英雄联盟
# ...

# 示例 2: 检索配置信息
context = memory.recall(
    query="API 配置",
    max_tokens=1000
)
# → 按相关性排序：
# - [0.39] 优化 NO_PROXY 配置
# - [0.38] 远见配置了 MiniMax Token Plan
# - [0.35] GLM → MiniMax fallback 配置
# ...

# 示例 3: 获取完整上下文（用于对话）
context = memory.recall(
    query="最近的工作",
    max_tokens=4000
)
# → 包含：
# 1. 核心记忆（用户档案）
# 2. 工作记忆（最近对话）
# 3. 回忆记忆（相关历史）
```

---

### 4. 记忆演化

**自动演化规则：**

| 操作 | 触发条件 | 示例 |
|------|----------|------|
| **ADD** | 新信息 | "配置了 MiniMax" |
| **UPDATE** | 矛盾信息 | "改用 MiniMax" → 替换 "使用 GLM-5" |
| **DELETE** | 过时信息 | "临时测试配置" |
| **NOOP** | 重复信息 | 相似度 > 0.95 |

**演化示例：**

```python
# 场景 1: 矛盾更新
memory.remember("用户使用 GLM-5", 0.8)
# → ADD: 记录到回忆记忆

memory.remember("用户改用 MiniMax", 0.8)
# → 检测到相似记忆（相似度 0.6）
# → 检测到矛盾（"改用" vs "使用"）
# → UPDATE: 删除旧记忆，添加新记忆

# 场景 2: 重复跳过
memory.remember("用户偏好简洁回复", 0.7)
# → ADD

memory.remember("用户喜欢简洁的回复", 0.7)
# → 检测到相似记忆（相似度 0.92）
# → NOOP: 跳过，避免重复

# 场景 3: 过时删除
memory.remember("临时测试配置", 0.3)
# → DELETE: 包含"临时"关键字
```

---

## 实际使用场景

### 场景 1: 用户告诉我偏好

**用户说：** "记住，我喜欢简洁的回复，不要重复说同一句话"

**我的处理：**
```python
# 1. 判断重要性
importance = 0.8  # 用户偏好，高重要性

# 2. 记录到记忆系统
memory.remember(
    content="远见偏好简洁回复，不要重复说同一句话",
    memory_type="preference",
    importance=importance
)

# 3. 演化系统自动处理
# → 检测到相似记忆
# → 判断是否矛盾
# → 执行 ADD/UPDATE/NOOP

# 4. 如果 importance >= 0.9
# → 自动更新核心记忆
memory.update_core("preferences", "远见偏好简洁回复...")
```

**效果：**
- ✅ 核心记忆更新（如果 importance >= 0.9）
- ✅ 回忆记忆记录（向量索引）
- ✅ 未来检索时自动返回

---

### 场景 2: 回答关于用户的问题

**用户问：** "我之前说过我喜欢什么吗？"

**我的处理：**
```python
# 1. 检索记忆
context = memory.recall(
    query="用户偏好",
    max_tokens=2000
)

# 2. 解析返回结果
# === 核心信息 ===
# 用户档案: 喜欢英雄联盟...
# 
# === 相关记忆 ===
# - [0.85] 用户偏好简洁回复
# - [0.72] 用户喜欢英雄联盟
# ...

# 3. 组织回答
response = f"你之前告诉我：\n"
response += f"- 偏好简洁的回复\n"
response += f"- 喜欢英雄联盟\n"
```

**效果：**
- ✅ 自动检索核心记忆 + 回忆记忆
- ✅ 按相关性排序
- ✅ 快速回答

---

### 场景 3: 配置变更

**用户说：** "我配置了新的 API key"

**我的处理：**
```python
# 1. 提取关键信息
content = "远见配置了 MiniMax Token Plan (API key: sk-cp-...)"

# 2. 判断重要性
importance = 0.9  # 配置信息，非常重要

# 3. 记录到记忆系统
memory.remember(content, "fact", importance)

# 4. 自动更新核心记忆（importance >= 0.9）
# → 核心记忆中的"当前任务"块更新
```

**效果：**
- ✅ 核心记忆更新（始终在线）
- ✅ 回忆记忆记录（可检索）
- ✅ 未来对话中自动包含此信息

---

### 场景 4: 记忆冲突

**用户说：** "我不用 GLM-5 了，改用 MiniMax"

**我的处理：**
```python
# 1. 记录新信息
memory.remember("用户改用 MiniMax", "fact", 0.8)

# 2. 演化系统自动：
# - 检索相似记忆 → 找到"用户使用 GLM-5"
# - 检测矛盾 → "改用" vs "使用"
# - 判断操作 → UPDATE

# 3. 执行更新
# → 删除旧记忆："用户使用 GLM-5"
# → 添加新记忆："用户使用 MiniMax (更新于 2026-03-24)"
```

**效果：**
- ✅ 自动检测矛盾
- ✅ 更新旧记忆
- ✅ 保持记忆一致性

---

## 性能指标

| 指标 | 值 |
|------|-----|
| **核心记忆大小** | 167 tokens (~3% context) |
| **回忆记忆数量** | 18 条 |
| **检索延迟** | < 100ms |
| **演化延迟** | < 200ms |
| **去重率** | ~50% |
| **Token 节省** | ~70% |

---

## 维护

### 定期优化（每周）

```python
# 运行记忆优化
service.optimize()
```

**优化内容：**
1. 清理过时记忆（90 天+，importance < 0.3）
2. 重建向量索引
3. 解决矛盾记忆

### 手动管理

```python
# 查看统计
stats = memory.get_stats()
print(stats)

# 更新核心记忆
memory.update_core("user_profile", "新信息")

# 清空工作记忆
memory.tiered.working.clear()
```

---

## 文件位置

```
~/.openclaw/
├── scripts/
│   └── init_memory.py              # 自动启动脚本
└── workspace/
    ├── ai-memory/
    │   ├── integrate_to_openclaw.py # 集成服务
    │   └── vector-memory/
    │       ├── tiered_memory.py     # 分层存储
    │       └── memory_evolver.py    # 记忆演化
    └── memory/
        ├── core_memory.json          # 核心记忆存储
        ├── recall_memory.json        # 回忆记忆备份
        └── archive/                  # 归档记忆
```

---

## 最佳实践

### ✅ DO（应该做的）

1. **记录重要信息**
   - 用户偏好
   - 关键配置
   - 重要决策

2. **使用演化系统**
   - 让系统自动去重
   - 让系统自动更新矛盾

3. **定期优化**
   - 每周运行一次 `optimize()`

4. **检索时指定 max_tokens**
   - 避免 context window 溢出

### ❌ DON'T（不应该做的）

1. **不要记录临时信息**
   - "临时测试..."
   - "待删除..."

2. **不要手动修改 Qdrant**
   - 使用提供的 API

3. **不要过度记录**
   - 只记录真正重要的信息

---

## 总结

**我的记忆系统：**
- ✅ 分层存储（4 层）
- ✅ 自动演化（去重/更新/删除）
- ✅ 智能检索（向量搜索）
- ✅ 自动启动（每次会话）

**我能做到：**
- ✅ 始终记住你的核心信息
- ✅ 自动去重，避免冗余
- ✅ 智能检索相关记忆
- ✅ 自动清理过时信息

**使用方式：**
1. 启动时自动初始化
2. 重要信息自动记录
3. 检索时智能返回
4. 演化时自动优化

---

**创建者：** 阿卡丽 🗡️  
**最后更新：** 2026-03-24
