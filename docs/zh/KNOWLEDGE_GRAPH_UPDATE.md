# 知识图谱更新与整合机制

[🌐 English](../../en/KNOWLEDGE_GRAPH_UPDATE.md) | **中文**

## 🔄 更新机制

### 1. 自动提取（规则引擎）

当前使用**规则引擎**自动从文本中提取实体和关系：

#### 提取规则

```python
# 规则 1: "X 喜欢 Y" -> PERSON RELATED_TO CONCEPT
文本: "远见喜欢英雄联盟"
提取: 
  - 实体: 远见 (PERSON)
  - 实体: 英雄联盟 (CONCEPT)
  - 关系: 远见 -related_to-> 英雄联盟

# 规则 2: "X 创建了 Y" -> PERSON CREATED_BY CONCEPT
文本: "远见创建了 agent-memory 项目"
提取:
  - 实体: 远见 (PERSON)
  - 实体: agent-memory (CONCEPT)
  - 关系: 远见 -created_by-> agent-memory

# 规则 3: "X 在 Y" -> PERSON LOCATED_AT LOCATION
文本: "远见在上海"
提取:
  - 实体: 远见 (PERSON)
  - 实体: 上海 (LOCATION)
  - 关系: 远见 -located_at-> 上海
```

#### 代码实现

```python
# knowledge_graph.py - extract_from_text() 方法
def extract_from_text(self, text: str) -> Tuple[List[Entity], List[Relation]]:
    entities = []
    relations = []
    
    # 规则 1: "X 喜欢 Y"
    match = re.search(r"(\w+)\s*喜欢\s*(\w+)", text)
    if match:
        person_name, target_name = match.groups()
        entities.append(self.add_entity(person_name, EntityType.PERSON))
        target = self.add_entity(target_name, EntityType.CONCEPT)
        entities.append(target)
        relations.append(self.add_relation(person_name, target_name, RelationType.RELATED_TO))
    
    # ... 其他规则
    
    return entities, relations
```

---

### 2. 手动添加

也可以手动添加实体和关系：

```python
from knowledge_graph import KnowledgeGraph, EntityType, RelationType

graph = KnowledgeGraph()

# 手动添加实体
person = graph.add_entity("远见", EntityType.PERSON, role="用户")
game = graph.add_entity("英雄联盟", EntityType.CONCEPT, type="游戏")

# 手动添加关系
graph.add_relation("远见", "英雄联盟", RelationType.RELATED_TO)
```

---

## 🔗 整合到记忆系统

### 整合方式：双写 + 双查

```
用户输入
    ↓
┌─────────────────────────────────┐
│  EnhancedMemoryWithGraph       │
│  (增强记忆服务)                 │
└───────────┬─────────────────────┘
            │
            ├─────────────────┐
            │                 │
            ▼                 ▼
    ┌──────────────┐  ┌──────────────┐
    │ MemoryService│  │KnowledgeGraph│
    │ (向量存储)    │  │(结构化知识)  │
    └──────────────┘  └──────────────┘
            │                 │
            │                 │
            ▼                 ▼
    ┌──────────────────────────────────┐
    │  自动提取实体和关系              │
    └──────────────────────────────────┘
```

### 1. 记录记忆时（双写）

```python
# enhanced_memory_graph.py

def remember(self, content: str, memory_type: str = "fact", **kwargs) -> str:
    # 1. 存储到向量记忆
    memory_id = self.memory_service.remember(content, memory_type, **kwargs)
    
    # 2. 自动提取实体和关系
    entities, relations = self.graph.extract_from_text(content)
    
    # 结果示例：
    # entities = [
    #     Entity("远见", PERSON),
    #     Entity("英雄联盟", CONCEPT)
    # ]
    # relations = [
    #     Relation("远见", "英雄联盟", RELATED_TO)
    # ]
    
    return memory_id
```

**示例：**
```python
# 用户记录记忆
enhanced.remember("远见喜欢英雄联盟", "fact")

# 自动发生的事情：
# 1. 存储到向量记忆（带 embedding）
# 2. 提取实体：远见 (PERSON), 英雄联盟 (CONCEPT)
# 3. 创建关系：远见 -related_to-> 英雄联盟
# 4. 持久化到 knowledge_graph/graph.json
```

---

### 2. 检索记忆时（双查 + 增强）

```python
# enhanced_memory_graph.py

def recall(self, query: str, limit: int = 10, include_graph_context: bool = True, **kwargs) -> List[dict]:
    # 1. 向量检索相关记忆
    memories = self.memory_service.recall(query, limit=limit, **kwargs)
    
    # 2. 图谱上下文增强（可选）
    if include_graph_context:
        for memory in memories:
            # 从记忆中提取实体名称
            entities_in_memory = self._extract_entities_from_memory(memory)
            
            for entity_name in entities_in_memory:
                # 获取实体的图谱（邻居 + 关系）
                entity_graph = self.get_entity_graph(entity_name, depth=2)
                
                # 添加到记忆结果中
                memory["graph_context"] = entity_graph
    
    return memories
```

**示例：**
```python
# 用户查询
results = enhanced.recall("远见喜欢什么", include_graph_context=True)

# 返回结果：
[
    {
        "content": "远见喜欢英雄联盟",
        "score": 0.85,
        "graph_context": {
            "entity": {"name": "远见", "type": "person"},
            "neighbors": [
                {"name": "英雄联盟", "type": "concept"},
                {"name": "阿卡丽", "type": "person"}
            ],
            "relations": [
                {"source": "远见", "target": "英雄联盟", "type": "related_to"},
                {"source": "远见", "target": "阿卡丽", "type": "knows"}
            ]
        }
    }
]
```

---

## 📊 完整流程示例

### 场景：用户说"远见喜欢英雄联盟，阿卡丽是他的助手"

```python
# 步骤 1: 记录记忆
enhanced.remember("远见喜欢英雄联盟,阿卡丽是他的助手", "fact")

# 自动执行：
# ┌─────────────────────────────────────┐
# │ 1. 向量存储                          │
# │    - 内容: "远见喜欢英雄联盟..."     │
# │    - Embedding: [0.024, -0.064, ...] │
# │    - 存储: Qdrant / 文件             │
# └─────────────────────────────────────┘
#            ↓
# ┌─────────────────────────────────────┐
# │ 2. 实体提取（规则引擎）               │
# │    - "远见" → PERSON                 │
# │    - "英雄联盟" → CONCEPT            │
# │    - "阿卡丽" → PERSON               │
# └─────────────────────────────────────┘
#            ↓
# ┌─────────────────────────────────────┐
# │ 3. 关系提取                          │
# │    - 远见 -related_to-> 英雄联盟     │
# │    - 远见 -knows-> 阿卡丽            │
# └─────────────────────────────────────┘
#            ↓
# ┌─────────────────────────────────────┐
# │ 4. 图谱存储                          │
# │    - 实体: 3 个                      │
# │    - 关系: 2 条                      │
# │    - 文件: knowledge_graph/graph.json│
# └─────────────────────────────────────┘
```

### 场景：查询"远见喜欢什么"

```python
# 步骤 2: 检索记忆
results = enhanced.recall("远见喜欢什么", include_graph_context=True)

# 自动执行：
# ┌─────────────────────────────────────┐
# │ 1. 向量检索                          │
# │    - 查询: "远见喜欢什么"            │
# │    - 相似度: 0.85                    │
# │    - 结果: "远见喜欢英雄联盟..."     │
# └─────────────────────────────────────┘
#            ↓
# ┌─────────────────────────────────────┐
# │ 2. 实体识别                          │
# │    - 从结果中提取: "远见"            │
# └─────────────────────────────────────┘
#            ↓
# ┌─────────────────────────────────────┐
# │ 3. 图谱查询                          │
# │    - 查询"远见"的邻居（深度 2）      │
# │    - 邻居: 英雄联盟, 阿卡丽          │
# │    - 关系: related_to, knows         │
# └─────────────────────────────────────┘
#            ↓
# ┌─────────────────────────────────────┐
# │ 4. 返回增强结果                      │
# │    - 记忆内容 + 向量相似度           │
# │    - 图谱上下文（邻居 + 关系）       │
# └─────────────────────────────────────┘
```

---

## 🎯 优势

### 1. 自动化
- ✅ 记录时自动提取实体和关系
- ✅ 不需要手动维护图谱
- ✅ 零额外操作

### 2. 双重增强
- ✅ 向量检索：语义相似性
- ✅ 图谱查询：结构关系
- ✅ 组合结果更准确

### 3. 可追溯
- ✅ 每个记忆都有图谱上下文
- ✅ 可以追溯知识来源
- ✅ 支持推理和关联

---

## 🔧 配置选项

### 启用/禁用图谱

```python
# 启用图谱增强
enhanced = EnhancedMemoryWithGraph()

# 检索时包含图谱上下文
results = enhanced.recall("查询", include_graph_context=True)

# 检索时不包含图谱上下文（纯向量检索）
results = enhanced.recall("查询", include_graph_context=False)
```

### 调整搜索深度

```python
# 获取实体的 1 层邻居
graph = enhanced.get_entity_graph("远见", depth=1)

# 获取实体的 2 层邻居（推荐）
graph = enhanced.get_entity_graph("远见", depth=2)

# 获取实体的 3 层邻居（可能过多）
graph = enhanced.get_entity_graph("远见", depth=3)
```

---

## 📈 性能影响

| 操作 | 额外时间 | 说明 |
|------|---------|------|
| 记录记忆 | +2ms | 实体提取 |
| 检索记忆（无图谱） | 0ms | 纯向量检索 |
| 检索记忆（带图谱） | +5ms | 图谱查询 |
| 可视化 | +10ms | Mermaid 生成 |

**建议：**
- 记录时：始终启用（自动提取）
- 检索时：重要查询启用，普通查询禁用

---

## 🚀 未来改进

### 短期
- [ ] 更智能的实体提取（使用 NER 模型）
- [ ] 支持更多关系类型
- [ ] 实体消歧（"远见" vs "用户"）

### 中期
- [ ] LLM 增强提取（更准确）
- [ ] 图谱推理（路径推理）
- [ ] 子图匹配查询

### 长期
- [ ] 图神经网络（GNN）
- [ ] 知识表示学习
- [ ] 多跳推理

---

**更新时间：** 2026-03-25 02:40 UTC
**版本：** v3.0-alpha
**分支：** knowledge-graph
