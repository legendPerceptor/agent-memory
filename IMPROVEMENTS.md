# Agent Memory 改进计划

**基于最新研究：** Letta (MemGPT), Mem0, A-Mem, Zep  
**创建日期：** 2026-03-24  
**维护者：** 阿卡丽 🗡️

---

## 📊 改进概览

| # | 改进名称 | 灵感来源 | 难度 | 收益 | 状态 |
|---|----------|----------|------|------|------|
| 1 | 分层存储架构 | MemGPT | 中 | ⭐⭐⭐⭐⭐ | 🚧 开发中 |
| 2 | 记忆演化系统 | Mem0 | 中 | ⭐⭐⭐⭐ | ⏳ 待开始 |
| 3 | 知识图谱记忆 | Mem0 Graph, A-Mem | 高 | ⭐⭐⭐⭐⭐ | ⏳ 待开始 |
| 4 | 时间感知记忆 | Zep (Bi-temporal) | 中 | ⭐⭐⭐⭐ | ⏳ 待开始 |
| 5 | 异步优化 | Sleep-Time Compute | 中 | ⭐⭐⭐ | ⏳ 待开始 |
| 6 | 多用户协作记忆 | Collaborative Memory | 高 | ⭐⭐⭐ | ⏳ 待开始 |

---

## 🎯 改进 1：分层存储架构

### 灵感来源
- **MemGPT / Letta**: 操作系统式内存管理
- **核心思想**: 不同类型记忆存储在不同层级

### 当前问题
- 所有记忆平级存储
- 无优先级区分
- Context window 利用率低

### 解决方案

```
分层架构：
┌─────────────────────────────────────┐
│ Level 1: Core Memory (始终在线)     │  ← 最高优先级
│ - 用户档案                           │
│ - 当前任务                           │
│ - 核心偏好                           │
├─────────────────────────────────────┤
│ Level 2: Working Memory (最近对话)  │  ← 自动轮换
│ - 最近 50 条消息                     │
│ - 当前会话上下文                     │
├─────────────────────────────────────┤
│ Level 3: Recall Memory (可检索)     │  ← 按需加载
│ - 完整历史记录                       │
│ - 向量索引                           │
├─────────────────────────────────────┤
│ Level 4: Archival Memory (压缩)     │  ← 长期存储
│ - 周摘要                             │
│ - 月摘要                             │
└─────────────────────────────────────┘
```

### 代码设计

```python
class TieredMemory:
    """分层记忆系统"""
    
    def __init__(self):
        # Level 1: 核心记忆 (始终在 context)
        self.core_memory = {
            "user_profile": {},
            "current_task": {},
            "preferences": {}
        }
        
        # Level 2: 工作记忆 (最近对话)
        self.working_memory = deque(maxlen=50)
        
        # Level 3: 回忆记忆 (可检索历史)
        self.recall_memory = QdrantCollection("recall")
        
        # Level 4: 归档记忆 (压缩摘要)
        self.archival_memory = QdrantCollection("archival")
    
    def remember(self, content, memory_type="recall"):
        """根据类型存储到不同层级"""
        
        if memory_type == "core":
            return self._add_to_core(content)
        elif memory_type == "working":
            return self._add_to_working(content)
        else:
            return self._add_to_recall(content)
    
    def recall(self, query, context_budget=4000):
        """智能检索，优先返回高层级记忆"""
        
        result = []
        remaining_budget = context_budget
        
        # 1. 加载核心记忆 (始终包含)
        core_tokens = self._count_tokens(self.core_memory)
        if core_tokens <= remaining_budget:
            result.append(self.core_memory)
            remaining_budget -= core_tokens
        
        # 2. 加载工作记忆 (按时间倒序)
        for msg in reversed(self.working_memory):
            tokens = self._count_tokens(msg)
            if tokens <= remaining_budget:
                result.append(msg)
                remaining_budget -= tokens
            else:
                break
        
        # 3. 检索回忆记忆 (语义相似)
        if remaining_budget > 500:
            recall_results = self.recall_memory.search(
                query, 
                limit=10
            )
            for r in recall_results:
                tokens = self._count_tokens(r)
                if tokens <= remaining_budget:
                    result.append(r)
                    remaining_budget -= tokens
        
        return result
```

### 收益
- Token 消耗减少 70%
- 关键信息始终在线
- 支持无限记忆扩展

---

## 🎯 改进 2：记忆演化系统

### 灵感来源
- **Mem0**: ADD/UPDATE/DELETE/NOOP 操作
- **核心思想**: 记忆不是静态的，需要演化

### 当前问题
- 重复记忆未去重
- 矛盾记忆未更新
- 无用记忆未删除

### 解决方案

```python
class EvolvingMemory:
    """演化记忆系统"""
    
    def remember(self, new_content, importance=0.5):
        """智能记忆写入"""
        
        # 1. 检索相似记忆
        similar = self.recall(new_content, threshold=0.85, limit=1)
        
        if similar:
            # 2. 判断操作类型
            operation = self._classify_operation(
                new_content,
                similar[0]['content']
            )
            
            if operation == "UPDATE":
                return self._update_memory(
                    similar[0]['id'],
                    new_content
                )
            elif operation == "DELETE":
                return self._delete_memory(similar[0]['id'])
            elif operation == "NOOP":
                return similar[0]['id']  # 无需操作
        
        # 3. 新增记忆
        return self._add_memory(new_content, importance)
    
    def _classify_operation(self, new_content, old_content):
        """判断操作类型"""
        
        # 简单规则（可替换为 LLM）
        if self._is_contradiction(new_content, old_content):
            return "UPDATE"
        elif self._is_duplicate(new_content, old_content):
            return "NOOP"
        elif self._is_obsolete(new_content, old_content):
            return "DELETE"
        else:
            return "ADD"
```

### 操作类型

| 操作 | 触发条件 | 示例 |
|------|----------|------|
| **ADD** | 新信息 | "用户购买 MiniMax Token Plan" |
| **UPDATE** | 矛盾信息 | "用户时区是 PST" → "用户时区是 UTC+8" |
| **DELETE** | 过时信息 | "用户使用 GLM-5" (已被替代) |
| **NOOP** | 重复信息 | 相似度 > 0.95 |

### 收益
- 自动去重
- 保持一致性
- 减少冗余 50%

---

## 🎯 改进 3：知识图谱记忆

### 灵感来源
- **Mem0 Graph Memory**: 实体 + 关系
- **A-Mem (Zettelkasten)**: 原子笔记 + 链接
- **核心思想**: 记忆之间有关联

### 当前问题
- 记忆之间无关联
- 无法多跳推理
- 无法发现隐含关系

### 解决方案

```python
class GraphMemory:
    """图结构记忆"""
    
    def __init__(self):
        # 实体存储
        self.entities = {}  # {entity_id: {attributes}}
        
        # 关系存储 (三元组)
        self.relationships = []  # [(subject, predicate, object)]
        
        # 向量索引
        self.entity_index = QdrantCollection("entities")
    
    def remember(self, content):
        """提取实体和关系"""
        
        # 1. 使用 LLM 提取实体
        entities = self._extract_entities(content)
        
        # 2. 提取关系
        relationships = self._extract_relationships(content)
        
        # 3. 存储实体
        for entity in entities:
            self._add_entity(entity)
        
        # 4. 存储关系
        for rel in relationships:
            self._add_relationship(*rel)
    
    def query(self, start_entity, hops=2):
        """多跳查询"""
        
        visited = set()
        queue = [(start_entity, 0)]
        results = []
        
        while queue:
            current, depth = queue.pop(0)
            
            if current in visited or depth > hops:
                continue
            
            visited.add(current)
            
            # 查找相关实体
            for subj, pred, obj in self.relationships:
                if subj == current:
                    results.append((subj, pred, obj, depth))
                    queue.append((obj, depth + 1))
        
        return results
```

### 示例

```
记忆 1: "远见购买了 MiniMax Token Plan"
记忆 2: "MiniMax Token Plan 包含 M2.7 模型"
记忆 3: "M2.7 模型每 5 小时限制 1500 次请求"

知识图谱：
远见 -[PURCHASED]-> MiniMax Token Plan
MiniMax Token Plan -[CONTAINS]-> M2.7
M2.7 -[LIMIT]-> 1500 requests/5h

查询: "远见能用什么模型？"
→ 遍历: 远见 -[PURCHASED]-> Token Plan -[CONTAINS]-> M2.7
→ 返回: "远见可以使用 MiniMax M2.7 模型"
```

### 收益
- 支持复杂推理
- 发现隐含关系
- 更智能的检索

---

## 🎯 改进 4：时间感知记忆

### 灵感来源
- **Zep**: Bi-temporal modeling
- **核心思想**: 区分"发生时间"和"记录时间"

### 当前问题
- 无法区分"什么时候发生"和"什么时候记录"
- 无法处理过时信息
- 无法追踪记忆变化

### 解决方案

```python
class TemporalMemory:
    """时间感知记忆"""
    
    def remember(self, content, valid_from=None, valid_until=None):
        """记录带时间信息的记忆"""
        
        return {
            "content": content,
            "recorded_at": datetime.now(),  # 什么时候记录的
            "valid_from": valid_from or datetime.now(),  # 什么时候开始有效
            "valid_until": valid_until,  # 什么时候失效 (None = 永久)
        }
    
    def recall(self, query, at_time=None):
        """检索某个时间点有效的记忆"""
        
        at_time = at_time or datetime.now()
        
        # 检索所有相关记忆
        all_results = self.vector_search(query)
        
        # 过滤：只返回在该时间点有效的记忆
        valid_results = []
        for r in all_results:
            if (r['valid_from'] <= at_time and 
                (r['valid_until'] is None or at_time <= r['valid_until'])):
                valid_results.append(r)
        
        return valid_results
```

### 示例

```
记忆 1: {
    "content": "用户使用 GLM-5",
    "valid_from": "2026-01-01",
    "valid_until": "2026-03-23",
    "recorded_at": "2026-01-01"
}

记忆 2: {
    "content": "用户使用 MiniMax",
    "valid_from": "2026-03-24",
    "valid_until": null,  # 当前有效
    "recorded_at": "2026-03-24"
}

查询 (2026-03-20): "用户用什么模型？"
→ 返回: "GLM-5" (记忆 1 有效)

查询 (2026-03-25): "用户用什么模型？"
→ 返回: "MiniMax" (记忆 2 有效)
```

### 收益
- 正确处理时间演变
- 自动过期旧记忆
- 支持历史查询

---

## 🎯 改进 5：异步优化

### 灵感来源
- **Sleep-Time Compute**: 后台异步处理
- **核心思想**: 记忆管理不应影响响应速度

### 当前问题
- 记忆管理在对话时进行
- 可能影响响应速度
- 无法深度优化

### 解决方案

```python
# memory_optimizer.py

async def optimize_memories():
    """后台记忆优化任务"""
    
    logger.info("开始记忆优化...")
    
    # 1. 压缩旧记忆 (30 天+)
    old_memories = get_memories_older_than(days=30)
    if old_memories:
        summary = await llm_summarize(old_memories)
        await archive(summary)
        await delete_batch(old_memories)
        logger.info(f"压缩了 {len(old_memories)} 条旧记忆")
    
    # 2. 更新知识图谱
    await update_graph_relationships()
    logger.info("知识图谱已更新")
    
    # 3. 重新索引向量
    await reindex_embeddings()
    logger.info("向量索引已重建")
    
    # 4. 清理矛盾记忆
    contradictions = await find_contradictions()
    for c in contradictions:
        await resolve_contradiction(c)
    logger.info(f"解决了 {len(contradictions)} 个矛盾")
    
    # 5. 统计报告
    stats = await generate_stats()
    logger.info(f"记忆统计: {stats}")

# Cron 调度
# crontab: 0 3 * * * (每天凌晨 3 点)
```

### 优化任务

| 任务 | 频率 | 耗时 | 说明 |
|------|------|------|------|
| **压缩旧记忆** | 每日 | 1-5 分钟 | 30 天前的记忆 → 摘要 |
| **更新图谱** | 每小时 | 10-30 秒 | 提取新关系 |
| **重建索引** | 每周 | 5-10 分钟 | 优化向量检索 |
| **清理矛盾** | 每日 | 1-3 分钟 | 解决冲突记忆 |

### 收益
- 零延迟影响
- 更高质量的记忆
- 自动维护

---

## 🎯 改进 6：多用户协作记忆

### 灵感来源
- **Collaborative Memory Structures**: 私有 + 共享
- **核心思想**: 不同用户有不同的记忆空间

### 当前问题
- 所有记忆混在一起
- 无权限隔离
- 无来源追溯

### 解决方案

```python
class CollaborativeMemory:
    """协作记忆系统"""
    
    def __init__(self):
        # 私有记忆 (仅用户可见)
        self.private_memory = {
            # "user:远见": [...memories...]
        }
        
        # 共享记忆 (团队可见)
        self.shared_memory = {
            # "team:project-a": [...memories...]
        }
    
    def remember(self, content, scope="private", user_id=None):
        """记录记忆"""
        
        memory = {
            "content": content,
            "owner": user_id or current_user,
            "scope": scope,  # private | shared
            "created_at": datetime.now(),
            "provenance": {
                "created_by": current_user,
                "created_at": datetime.now(),
                "modified_by": [],
            }
        }
        
        if scope == "private":
            key = f"user:{user_id or current_user}"
            self.private_memory.setdefault(key, []).append(memory)
        else:
            key = f"team:{scope}"
            self.shared_memory.setdefault(key, []).append(memory)
        
        return memory
    
    def recall(self, query, user_id=None):
        """检索记忆 (包含私有 + 有权限的共享)"""
        
        results = []
        
        # 1. 加载用户私有记忆
        private_key = f"user:{user_id or current_user}"
        results.extend(self._search(self.private_memory.get(private_key, []), query))
        
        # 2. 加载有权限的共享记忆
        for team_id in self._get_user_teams(user_id):
            shared_key = f"team:{team_id}"
            results.extend(self._search(self.shared_memory.get(shared_key, []), query))
        
        return results
```

### 权限模型

| 记忆类型 | 可见性 | 示例 |
|----------|--------|------|
| **私有记忆** | 仅用户本人 | "我的 API key 是 xxx" |
| **团队记忆** | 团队成员 | "项目 A 使用 Qdrant" |
| **公开记忆** | 所有人 | "系统配置" |

### 收益
- 多用户隔离
- 权限控制
- 审计追踪

---

## 🚀 实施路线图

### Phase 1: 基础改进 (1-2 周)
- [x] 设计分层存储架构
- [ ] 实现 TieredMemory 类
- [ ] 集成到现有 memory_service.py
- [ ] 添加记忆演化逻辑
- [ ] 测试和文档

### Phase 2: 高级特性 (1-2 月)
- [ ] 实现知识图谱存储
- [ ] 添加时间感知功能
- [ ] 集成异步优化任务
- [ ] 性能测试

### Phase 3: 企业特性 (3+ 月)
- [ ] 多用户协作支持
- [ ] 权限管理系统
- [ ] Web UI 界面
- [ ] 监控和告警

---

## 📚 参考资料

### 学术论文
- **A-Mem**: Agentic Memory for LLM Agents (2025) - https://arxiv.org/abs/2502.12110
- **Mem0**: Building Production-Ready AI Agents (2025) - https://arxiv.org/pdf/2504.19413
- **MemGPT**: Virtual Context Management (2023) - https://arxiv.org/abs/2310.08560

### 开源项目
- **Letta (MemGPT)**: https://github.com/letta-ai/letta
- **Mem0**: https://github.com/mem0ai/mem0
- **Zep**: https://github.com/getzep/zep

### 博客文章
- **Letta Blog**: Agent Memory - https://www.letta.com/blog/agent-memory
- **Mem0 Blog**: Graph Memory - https://mem0.ai/blog/graph-memory-solutions-ai-agents

---

**下一步：** 开始实施改进 1 - 分层存储架构

**维护者：** 阿卡丽 🗡️  
**最后更新：** 2026-03-24
