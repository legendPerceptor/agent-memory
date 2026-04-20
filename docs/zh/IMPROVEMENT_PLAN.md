# Memory 优化计划

[🌐 English](../../en/IMPROVEMENT_PLAN.md) | **中文**

## 当前状态分析

**统计日期：** 2026-03-24

| 文件 | 行数 | 字符数 | Token 估算 | 占比 |
|------|------|--------|-----------|------|
| AGENTS.md | 212 | 7,874 | ~1,968 | 76.7% |
| MEMORY.md | 54 | 1,951 | ~487 | 19.0% |
| USER.md | 15 | 445 | ~111 | 4.3% |
| **总计** | **281** | **10,270** | **~2,566** | **100%** |

### 发现

1. **AGENTS.md 是大头** - 占了 77% 的 token
   - 包含行为规则、心跳策略、群聊礼仪
   - 每次会话都加载，但很多内容很少用到

2. **MEMORY.md 精简良好** - 只占 19%
   - 主要是用户信息和环境配置
   - 结构清晰，易于维护

3. **memory/*.md 未计入启动** - 每日笔记只在需要时加载
   - 4 个文件，302 行，8,973 字符
   - 但每次读取都全量加载

---

## 优化方案

### 方案 A: 拆分 AGENTS.md（立即收益）

**目标：** 减少 60-70% 启动 token

**实施：**
```
AGENTS.md (启动加载 - 精简版)
├── 核心规则
├── Memory 使用
└── 红线规则

rules/ (按需加载)
├── group-chat.md    # 群聊礼仪
├── heartbeat.md     # 心跳策略
└── tools.md         # 工具使用
```

**收益：**
- 启动 token: 2,566 → ~1,000
- 减少 60%

---

### 方案 B: 向量化 Memory（长期收益）

**目标：** 支持 100x 记忆量级，查找效率 50x 提升

**实施：**
```javascript
// 复用 aicreatorvault 的 Qdrant
const memoryCollection = "agent-memories";

// 写入记忆
async function remember(content, metadata) {
  const embedding = await getEmbedding(content);
  await qdrant.upsert(memoryCollection, {
    id: generateId(),
    vector: embedding,
    payload: {
      content,
      date: new Date().toISOString(),
      type: metadata.type, // fact | event | preference | decision
      importance: metadata.importance,
      tags: metadata.tags
    }
  });
}

// 检索记忆
async function recall(query, options = {}) {
  const embedding = await getEmbedding(query);
  const results = await qdrant.search(memoryCollection, {
    vector: embedding,
    limit: options.limit || 10,
    filter: {
      must: [
        { key: "importance", range: { gte: options.minImportance || 0.5 } }
      ]
    }
  });
  return results;
}
```

**收益：**
- 支持百万级记忆
- 毫秒级查找
- 智能相关性排序

---

### 方案 C: 自动摘要（中期收益）

**目标：** 历史日志压缩 90%

**实施：**
```bash
# 每周自动运行
0 0 * * 0 /path/to/weekly-summary.py
```

**流程：**
```
Day 1-7: memory/2026-03-XX.md (7 个文件, ~2,000 行)
  ↓ 周日自动压缩
Week Summary: memory/2026-W12.md (1 个文件, ~50 行)
  ↓ 月末再压缩
Month Summary: memory/2026-03.md (1 个文件, ~10 行)
```

**收益：**
- 7 天日志 → 1 天摘要
- Token 减少 90%
- 关键信息保留

---

## 推荐实施顺序

### 第 1 周：立即可做（零代码）

- [ ] **精简 MEMORY.md**
  - 移除已完成的待办
  - 归档过时的项目信息
  
- [ ] **创建 memory/archive/**
  - 移动 7 天前的日志
  
- [ ] **手动写周摘要**
  - 总结本周工作
  - 保存为 `memory/2026-W12.md`

### 第 2 周：自动化（简单脚本）

- [ ] **实施 weekly-summary.py**
  - 自动生成周摘要
  - 自动归档旧文件
  
- [ ] **配置 cron job**
  - 每周日 00:00 运行
  
- [ ] **创建 memory-stats.sh**
  - 监控 token 消耗

### 第 3-4 周：向量化（集成 Qdrant）

- [ ] **复用 aicreatorvault 的 Qdrant**
  - 创建 `agent-memories` collection
  
- [ ] **实现 remember/recall API**
  - 写入记忆时自动向量化
  - 启动时检索 top-k 相关记忆
  
- [ ] **优化启动流程**
  - 只加载相关记忆
  - 动态调整上下文

---

## 成功指标

| 指标 | 当前 | 目标 | 改进 |
|------|------|------|------|
| 启动 Token | ~2,566 | ~1,000 | -61% |
| 记忆容量 | ~100 条 | ~10,000 条 | 100x |
| 查找速度 | O(n) 文件扫描 | O(log n) 向量搜索 | 50x |
| 历史压缩率 | 0% | 90% | 90% |

---

## 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| Qdrant 宕机 | 无法检索记忆 | 回退到文件搜索 |
| 向量化延迟 | 写入变慢 | 异步处理 |
| 摘要丢失细节 | 信息不完整 | 保留原始文件 30 天 |
| AGENTS.md 拆分 | 加载逻辑复杂 | 使用 include 机制 |

---

**下一步：** 选择一个方案开始实施？
