# Knowledge Graph Update and Integration Mechanism

**English** | [🌐 中文](../../zh/KNOWLEDGE_GRAPH_UPDATE.md)

## 🔄 Update Mechanism

### 1. Auto-Extraction (Rule Engine)

Currently uses a **rule engine** to automatically extract entities and relations from text:

#### Extraction Rules

```python
# Rule 1: "X likes Y" -> PERSON RELATED_TO CONCEPT
Text: "Yuanjian likes League of Legends"
Extraction: 
  - Entity: Yuanjian (PERSON)
  - Entity: League of Legends (CONCEPT)
  - Relation: Yuanjian -related_to-> League of Legends

# Rule 2: "X created Y" -> PERSON CREATED_BY CONCEPT
Text: "Yuanjian created the agent-memory project"
Extraction:
  - Entity: Yuanjian (PERSON)
  - Entity: agent-memory (CONCEPT)
  - Relation: Yuanjian -created_by-> agent-memory

# Rule 3: "X is at Y" -> PERSON LOCATED_AT LOCATION
Text: "Yuanjian is in Shanghai"
Extraction:
  - Entity: Yuanjian (PERSON)
  - Entity: Shanghai (LOCATION)
  - Relation: Yuanjian -located_at-> Shanghai
```

#### Code Implementation

```python
# knowledge_graph.py - extract_from_text() method
def extract_from_text(self, text: str) -> Tuple[List[Entity], List[Relation]]:
    entities = []
    relations = []
    
    # Rule 1: "X likes Y"
    match = re.search(r"(\w+)\s*likes\s*(\w+)", text)
    if match:
        person_name, target_name = match.groups()
        entities.append(self.add_entity(person_name, EntityType.PERSON))
        target = self.add_entity(target_name, EntityType.CONCEPT)
        entities.append(target)
        relations.append(self.add_relation(person_name, target_name, RelationType.RELATED_TO))
    
    # ... other rules
    
    return entities, relations
```

---

### 2. Manual Addition

You can also manually add entities and relations:

```python
from knowledge_graph import KnowledgeGraph, EntityType, RelationType

graph = KnowledgeGraph()

# Manually add entities
person = graph.add_entity("Yuanjian", EntityType.PERSON, role="user")
game = graph.add_entity("League of Legends", EntityType.CONCEPT, type="game")

# Manually add relations
graph.add_relation("Yuanjian", "League of Legends", RelationType.RELATED_TO)
```

---

## 🔗 Integration with Memory System

### Integration Method: Dual-Write + Dual-Query

```
User Input
    ↓
┌─────────────────────────────────┐
│  EnhancedMemoryWithGraph       │
│  (Enhanced Memory Service)     │
└───────────┬─────────────────────┘
            │
            ├─────────────────┐
            │                 │
            ▼                 ▼
    ┌──────────────┐  ┌──────────────┐
    │ MemoryService│  │KnowledgeGraph│
    │ (Vector Store)│  │(Structured) │
    └──────────────┘  └──────────────┘
            │                 │
            │                 │
            ▼                 ▼
    ┌──────────────────────────────────┐
    │  Auto-extract entities & relations│
    └──────────────────────────────────┘
```

### 1. When Storing Memory (Dual-Write)

```python
# enhanced_memory_graph.py

def remember(self, content: str, memory_type: str = "fact", **kwargs) -> str:
    # 1. Store to vector memory
    memory_id = self.memory_service.remember(content, memory_type, **kwargs)
    
    # 2. Auto-extract entities and relations
    entities, relations = self.graph.extract_from_text(content)
    
    # Example result:
    # entities = [
    #     Entity("Yuanjian", PERSON),
    #     Entity("League of Legends", CONCEPT)
    # ]
    # relations = [
    #     Relation("Yuanjian", "League of Legends", RELATED_TO)
    # ]
    
    return memory_id
```

**Example:**
```python
# User stores memory
enhanced.remember("Yuanjian likes League of Legends", "fact")

# What happens automatically:
# 1. Store to vector memory (with embedding)
# 2. Extract entities: Yuanjian (PERSON), League of Legends (CONCEPT)
# 3. Create relation: Yuanjian -related_to-> League of Legends
# 4. Persist to knowledge_graph/graph.json
```

---

### 2. When Retrieving Memory (Dual-Query + Enhancement)

```python
# enhanced_memory_graph.py

def recall(self, query: str, limit: int = 10, include_graph_context: bool = True, **kwargs) -> List[dict]:
    # 1. Vector retrieval of related memories
    memories = self.memory_service.recall(query, limit=limit, **kwargs)
    
    # 2. Graph context enhancement (optional)
    if include_graph_context:
        for memory in memories:
            # Extract entity names from memory
            entities_in_memory = self._extract_entities_from_memory(memory)
            
            for entity_name in entities_in_memory:
                # Get entity's graph (neighbors + relations)
                entity_graph = self.get_entity_graph(entity_name, depth=2)
                
                # Add to memory results
                memory["graph_context"] = entity_graph
    
    return memories
```

**Example:**
```python
# User query
results = enhanced.recall("What does Yuanjian like", include_graph_context=True)

# Returned results:
[
    {
        "content": "Yuanjian likes League of Legends",
        "score": 0.85,
        "graph_context": {
            "entity": {"name": "Yuanjian", "type": "person"},
            "neighbors": [
                {"name": "League of Legends", "type": "concept"},
                {"name": "Akali", "type": "person"}
            ],
            "relations": [
                {"source": "Yuanjian", "target": "League of Legends", "type": "related_to"},
                {"source": "Yuanjian", "target": "Akali", "type": "knows"}
            ]
        }
    }
]
```

---

## 📊 Complete Flow Example

### Scenario: User says "Yuanjian likes League of Legends, Akali is his assistant"

```python
# Step 1: Store memory
enhanced.remember("Yuanjian likes League of Legends, Akali is his assistant", "fact")

# Auto-executed:
# ┌─────────────────────────────────────┐
# │ 1. Vector storage                    │
# │    - Content: "Yuanjian likes..."    │
# │    - Embedding: [0.024, -0.064, ...] │
# │    - Storage: Qdrant / File          │
# └─────────────────────────────────────┘
#            ↓
# ┌─────────────────────────────────────┐
# │ 2. Entity extraction (rule engine)   │
# │    - "Yuanjian" → PERSON             │
# │    - "League of Legends" → CONCEPT   │
# │    - "Akali" → PERSON                │
# └─────────────────────────────────────┘
#            ↓
# ┌─────────────────────────────────────┐
# │ 3. Relation extraction               │
# │    - Yuanjian -related_to-> LoL      │
# │    - Yuanjian -knows-> Akali         │
# └─────────────────────────────────────┘
#            ↓
# ┌─────────────────────────────────────┐
# │ 4. Graph storage                     │
# │    - Entities: 3                     │
# │    - Relations: 2                    │
# │    - File: knowledge_graph/graph.json│
# └─────────────────────────────────────┘
```

### Scenario: Query "What does Yuanjian like"

```python
# Step 2: Retrieve memory
results = enhanced.recall("What does Yuanjian like", include_graph_context=True)

# Auto-executed:
# ┌─────────────────────────────────────┐
# │ 1. Vector retrieval                  │
# │    - Query: "What does Yuanjian like"│
# │    - Similarity: 0.85                │
# │    - Result: "Yuanjian likes LoL..." │
# └─────────────────────────────────────┘
#            ↓
# ┌─────────────────────────────────────┐
# │ 2. Entity identification             │
# │    - Extract from result: "Yuanjian" │
# └─────────────────────────────────────┘
#            ↓
# ┌─────────────────────────────────────┐
# │ 3. Graph query                       │
# │    - Query "Yuanjian" neighbors (2)  │
# │    - Neighbors: LoL, Akali           │
# │    - Relations: related_to, knows    │
# └─────────────────────────────────────┘
#            ↓
# ┌─────────────────────────────────────┐
# │ 4. Return enhanced results           │
# │    - Memory content + vector score   │
# │    - Graph context (neighbors+rels)  │
# └─────────────────────────────────────┘
```

---

## 🎯 Advantages

### 1. Automation
- ✅ Auto-extract entities and relations when storing
- ✅ No manual graph maintenance needed
- ✅ Zero extra operations

### 2. Dual Enhancement
- ✅ Vector retrieval: Semantic similarity
- ✅ Graph query: Structural relationships
- ✅ Combined results are more accurate

### 3. Traceability
- ✅ Every memory has graph context
- ✅ Can trace knowledge sources
- ✅ Supports reasoning and association

---

## 🔧 Configuration Options

### Enable/Disable Graph

```python
# Enable graph enhancement
enhanced = EnhancedMemoryWithGraph()

# Include graph context in retrieval
results = enhanced.recall("query", include_graph_context=True)

# Exclude graph context (pure vector retrieval)
results = enhanced.recall("query", include_graph_context=False)
```

### Adjust Search Depth

```python
# Get entity's 1-level neighbors
graph = enhanced.get_entity_graph("Yuanjian", depth=1)

# Get entity's 2-level neighbors (recommended)
graph = enhanced.get_entity_graph("Yuanjian", depth=2)

# Get entity's 3-level neighbors (may be too many)
graph = enhanced.get_entity_graph("Yuanjian", depth=3)
```

---

## 📈 Performance Impact

| Operation | Extra Time | Description |
|-----------|-----------|-------------|
| Store memory | +2ms | Entity extraction |
| Retrieve memory (no graph) | 0ms | Pure vector retrieval |
| Retrieve memory (with graph) | +5ms | Graph query |
| Visualization | +10ms | Mermaid generation |

**Recommendations:**
- When storing: Always enable (auto-extraction)
- When retrieving: Enable for important queries, disable for regular queries

---

## 🚀 Future Improvements

### Short-term
- [ ] Smarter entity extraction (using NER models)
- [ ] Support more relation types
- [ ] Entity disambiguation ("Yuanjian" vs "User")

### Mid-term
- [ ] LLM-enhanced extraction (more accurate)
- [ ] Graph reasoning (path reasoning)
- [ ] Subgraph matching queries

### Long-term
- [ ] Graph Neural Networks (GNN)
- [ ] Knowledge representation learning
- [ ] Multi-hop reasoning

---

**Updated:** 2026-03-25 02:40 UTC
**Version:** v3.0-alpha
**Branch:** knowledge-graph
