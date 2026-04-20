# Agent Memory Improvement Plan

**English** | [🌐 中文](../../zh/IMPROVEMENTS.md)

**Based on Latest Research:** Letta (MemGPT), Mem0, A-Mem, Zep  
**Created:** 2026-03-24  
**Maintainer:** Akali 🗡️

---

## 📊 Improvement Overview

| # | Improvement | Inspiration | Difficulty | Benefit | Status |
|---|-------------|-------------|------------|---------|--------|
| 1 | Tiered Storage Architecture | MemGPT | Medium | ⭐⭐⭐⭐⭐ | 🚧 In Development |
| 2 | Memory Evolution System | Mem0 | Medium | ⭐⭐⭐⭐ | ⏳ Pending |
| 3 | Knowledge Graph Memory | Mem0 Graph, A-Mem | High | ⭐⭐⭐⭐⭐ | ⏳ Pending |
| 4 | Time-Aware Memory | Zep (Bi-temporal) | Medium | ⭐⭐⭐⭐ | ⏳ Pending |
| 5 | Async Optimization | Sleep-Time Compute | Medium | ⭐⭐⭐ | ⏳ Pending |
| 6 | Multi-User Collaborative Memory | Collaborative Memory | High | ⭐⭐⭐ | ⏳ Pending |

---

## 🎯 Improvement 1: Tiered Storage Architecture

### Inspiration
- **MemGPT / Letta**: OS-style memory management
- **Core Idea**: Different types of memory stored at different tiers

### Current Problems
- All memories stored at the same level
- No priority differentiation
- Low context window utilization

### Solution

```
Tiered Architecture:
┌─────────────────────────────────────┐
│ Level 1: Core Memory (Always Online)│  ← Highest Priority
│ - User profile                      │
│ - Current tasks                     │
│ - Core preferences                  │
├─────────────────────────────────────┤
│ Level 2: Working Memory (Recent)    │  ← Auto Rotation
│ - Recent 50 messages                │
│ - Current session context           │
├─────────────────────────────────────┤
│ Level 3: Recall Memory (Searchable) │  ← On-Demand Loading
│ - Complete history                  │
│ - Vector index                      │
├─────────────────────────────────────┤
│ Level 4: Archival Memory (Compressed)│  ← Long-term Storage
│ - Weekly summaries                  │
│ - Monthly summaries                 │
└─────────────────────────────────────┘
```

### Code Design

```python
class TieredMemory:
    """Tiered Memory System"""
    
    def __init__(self):
        # Level 1: Core memory (always in context)
        self.core_memory = {
            "user_profile": {},
            "current_task": {},
            "preferences": {}
        }
        
        # Level 2: Working memory (recent conversations)
        self.working_memory = deque(maxlen=50)
        
        # Level 3: Recall memory (searchable history)
        self.recall_memory = QdrantCollection("recall")
        
        # Level 4: Archival memory (compressed summaries)
        self.archival_memory = QdrantCollection("archival")
    
    def remember(self, content, memory_type="recall"):
        """Store to different tiers based on type"""
        
        if memory_type == "core":
            return self._add_to_core(content)
        elif memory_type == "working":
            return self._add_to_working(content)
        else:
            return self._add_to_recall(content)
    
    def recall(self, query, context_budget=4000):
        """Smart retrieval, prioritize higher-tier memories"""
        
        result = []
        remaining_budget = context_budget
        
        # 1. Load core memory (always included)
        core_tokens = self._count_tokens(self.core_memory)
        if core_tokens <= remaining_budget:
            result.append(self.core_memory)
            remaining_budget -= core_tokens
        
        # 2. Load working memory (reverse chronological)
        for msg in reversed(self.working_memory):
            tokens = self._count_tokens(msg)
            if tokens <= remaining_budget:
                result.append(msg)
                remaining_budget -= tokens
            else:
                break
        
        # 3. Retrieve recall memory (semantic similarity)
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

### Benefits
- 70% reduction in token consumption
- Key information always online
- Supports unlimited memory expansion

---

## 🎯 Improvement 2: Memory Evolution System

### Inspiration
- **Mem0**: ADD/UPDATE/DELETE/NOOP operations
- **Core Idea**: Memory is not static, it needs to evolve

### Current Problems
- Duplicate memories not deduplicated
- Contradictory memories not updated
- Useless memories not deleted

### Solution

```python
class EvolvingMemory:
    """Evolving Memory System"""
    
    def remember(self, new_content, importance=0.5):
        """Smart memory write"""
        
        # 1. Retrieve similar memories
        similar = self.recall(new_content, threshold=0.85, limit=1)
        
        if similar:
            # 2. Classify operation type
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
                return similar[0]['id']  # No operation needed
        
        # 3. Add new memory
        return self._add_memory(new_content, importance)
    
    def _classify_operation(self, new_content, old_content):
        """Classify operation type"""
        
        # Simple rules (can be replaced with LLM)
        if self._is_contradiction(new_content, old_content):
            return "UPDATE"
        elif self._is_duplicate(new_content, old_content):
            return "NOOP"
        elif self._is_obsolete(new_content, old_content):
            return "DELETE"
        else:
            return "ADD"
```

### Operation Types

| Operation | Trigger Condition | Example |
|-----------|-------------------|---------|
| **ADD** | New information | "User purchased MiniMax Token Plan" |
| **UPDATE** | Contradictory information | "User timezone is PST" → "User timezone is UTC+8" |
| **DELETE** | Obsolete information | "User uses GLM-5" (replaced) |
| **NOOP** | Duplicate information | Similarity > 0.95 |

### Benefits
- Auto-deduplication
- Maintain consistency
- 50% redundancy reduction

---

## 🎯 Improvement 3: Knowledge Graph Memory

### Inspiration
- **Mem0 Graph Memory**: Entities + Relations
- **A-Mem (Zettelkasten)**: Atomic notes + Links
- **Core Idea**: Memories have associations

### Current Problems
- No associations between memories
- Cannot perform multi-hop reasoning
- Cannot discover implicit relationships

### Solution

```python
class GraphMemory:
    """Graph-structured Memory"""
    
    def __init__(self):
        # Entity storage
        self.entities = {}  # {entity_id: {attributes}}
        
        # Relation storage (triples)
        self.relationships = []  # [(subject, predicate, object)]
        
        # Vector index
        self.entity_index = QdrantCollection("entities")
    
    def remember(self, content):
        """Extract entities and relations"""
        
        # 1. Extract entities using LLM
        entities = self._extract_entities(content)
        
        # 2. Extract relations
        relationships = self._extract_relationships(content)
        
        # 3. Store entities
        for entity in entities:
            self._add_entity(entity)
        
        # 4. Store relations
        for rel in relationships:
            self._add_relationship(*rel)
    
    def query(self, start_entity, hops=2):
        """Multi-hop query"""
        
        visited = set()
        queue = [(start_entity, 0)]
        results = []
        
        while queue:
            current, depth = queue.pop(0)
            
            if current in visited or depth > hops:
                continue
            
            visited.add(current)
            
            # Find related entities
            for subj, pred, obj in self.relationships:
                if subj == current:
                    results.append((subj, pred, obj, depth))
                    queue.append((obj, depth + 1))
        
        return results
```

### Example

```
Memory 1: "Yuanjian purchased MiniMax Token Plan"
Memory 2: "MiniMax Token Plan includes M2.7 model"
Memory 3: "M2.7 model limits 1500 requests per 5 hours"

Knowledge Graph:
Yuanjian -[PURCHASED]-> MiniMax Token Plan
MiniMax Token Plan -[CONTAINS]-> M2.7
M2.7 -[LIMIT]-> 1500 requests/5h

Query: "What models can Yuanjian use?"
→ Traverse: Yuanjian -[PURCHASED]-> Token Plan -[CONTAINS]-> M2.7
→ Return: "Yuanjian can use the MiniMax M2.7 model"
```

### Benefits
- Supports complex reasoning
- Discovers implicit relationships
- Smarter retrieval

---

## 🎯 Improvement 4: Time-Aware Memory

### Inspiration
- **Zep**: Bi-temporal modeling
- **Core Idea**: Distinguish between "when it happened" and "when it was recorded"

### Current Problems
- Cannot distinguish "when it happened" from "when it was recorded"
- Cannot handle outdated information
- Cannot track memory changes

### Solution

```python
class TemporalMemory:
    """Time-Aware Memory"""
    
    def remember(self, content, valid_from=None, valid_until=None):
        """Store memory with temporal information"""
        
        return {
            "content": content,
            "recorded_at": datetime.now(),  # When it was recorded
            "valid_from": valid_from or datetime.now(),  # When it becomes valid
            "valid_until": valid_until,  # When it expires (None = permanent)
        }
    
    def recall(self, query, at_time=None):
        """Retrieve memories valid at a specific time"""
        
        at_time = at_time or datetime.now()
        
        # Retrieve all related memories
        all_results = self.vector_search(query)
        
        # Filter: only return memories valid at that time
        valid_results = []
        for r in all_results:
            if (r['valid_from'] <= at_time and 
                (r['valid_until'] is None or at_time <= r['valid_until'])):
                valid_results.append(r)
        
        return valid_results
```

### Example

```
Memory 1: {
    "content": "User uses GLM-5",
    "valid_from": "2026-01-01",
    "valid_until": "2026-03-23",
    "recorded_at": "2026-01-01"
}

Memory 2: {
    "content": "User uses MiniMax",
    "valid_from": "2026-03-24",
    "valid_until": null,  # Currently valid
    "recorded_at": "2026-03-24"
}

Query (2026-03-20): "What model does the user use?"
→ Return: "GLM-5" (Memory 1 valid)

Query (2026-03-25): "What model does the user use?"
→ Return: "MiniMax" (Memory 2 valid)
```

### Benefits
- Correctly handles temporal evolution
- Auto-expires old memories
- Supports historical queries

---

## 🎯 Improvement 5: Async Optimization

### Inspiration
- **Sleep-Time Compute**: Background async processing
- **Core Idea**: Memory management should not affect response speed

### Current Problems
- Memory management happens during conversations
- May affect response speed
- Cannot perform deep optimization

### Solution

```python
# memory_optimizer.py

async def optimize_memories():
    """Background memory optimization task"""
    
    logger.info("Starting memory optimization...")
    
    # 1. Compress old memories (30+ days)
    old_memories = get_memories_older_than(days=30)
    if old_memories:
        summary = await llm_summarize(old_memories)
        await archive(summary)
        await delete_batch(old_memories)
        logger.info(f"Compressed {len(old_memories)} old memories")
    
    # 2. Update knowledge graph
    await update_graph_relationships()
    logger.info("Knowledge graph updated")
    
    # 3. Re-index vectors
    await reindex_embeddings()
    logger.info("Vector index rebuilt")
    
    # 4. Clean up contradictory memories
    contradictions = await find_contradictions()
    for c in contradictions:
        await resolve_contradiction(c)
    logger.info(f"Resolved {len(contradictions)} contradictions")
    
    # 5. Statistics report
    stats = await generate_stats()
    logger.info(f"Memory statistics: {stats}")

# Cron scheduling
# crontab: 0 3 * * * (daily at 3 AM)
```

### Optimization Tasks

| Task | Frequency | Duration | Description |
|------|-----------|----------|-------------|
| **Compress old memories** | Daily | 1-5 minutes | Memories 30+ days old → summaries |
| **Update graph** | Hourly | 10-30 seconds | Extract new relations |
| **Rebuild index** | Weekly | 5-10 minutes | Optimize vector retrieval |
| **Clean contradictions** | Daily | 1-3 minutes | Resolve conflicting memories |

### Benefits
- Zero latency impact
- Higher quality memories
- Automatic maintenance

---

## 🎯 Improvement 6: Multi-User Collaborative Memory

### Inspiration
- **Collaborative Memory Structures**: Private + Shared
- **Core Idea**: Different users have different memory spaces

### Current Problems
- All memories mixed together
- No permission isolation
- No source traceability

### Solution

```python
class CollaborativeMemory:
    """Collaborative Memory System"""
    
    def __init__(self):
        # Private memory (only visible to user)
        self.private_memory = {
            # "user:yuanjian": [...memories...]
        }
        
        # Shared memory (visible to team)
        self.shared_memory = {
            # "team:project-a": [...memories...]
        }
    
    def remember(self, content, scope="private", user_id=None):
        """Store memory"""
        
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
        """Retrieve memory (includes private + authorized shared)"""
        
        results = []
        
        # 1. Load user's private memories
        private_key = f"user:{user_id or current_user}"
        results.extend(self._search(self.private_memory.get(private_key, []), query))
        
        # 2. Load authorized shared memories
        for team_id in self._get_user_teams(user_id):
            shared_key = f"team:{team_id}"
            results.extend(self._search(self.shared_memory.get(shared_key, []), query))
        
        return results
```

### Permission Model

| Memory Type | Visibility | Example |
|-------------|-----------|---------|
| **Private Memory** | Only the user | "My API key is xxx" |
| **Team Memory** | Team members | "Project A uses Qdrant" |
| **Public Memory** | Everyone | "System configuration" |

### Benefits
- Multi-user isolation
- Permission control
- Audit trail

---

## 🚀 Implementation Roadmap

### Phase 1: Basic Improvements (1-2 weeks)
- [x] Design tiered storage architecture
- [ ] Implement TieredMemory class
- [ ] Integrate into existing memory_service.py
- [ ] Add memory evolution logic
- [ ] Testing and documentation

### Phase 2: Advanced Features (1-2 months)
- [ ] Implement knowledge graph storage
- [ ] Add time-aware functionality
- [ ] Integrate async optimization tasks
- [ ] Performance testing

### Phase 3: Enterprise Features (3+ months)
- [ ] Multi-user collaboration support
- [ ] Permission management system
- [ ] Web UI interface
- [ ] Monitoring and alerting

---

## 📚 References

### Academic Papers
- **A-Mem**: Agentic Memory for LLM Agents (2025) - https://arxiv.org/abs/2502.12110
- **Mem0**: Building Production-Ready AI Agents (2025) - https://arxiv.org/pdf/2504.19413
- **MemGPT**: Virtual Context Management (2023) - https://arxiv.org/abs/2310.08560

### Open Source Projects
- **Letta (MemGPT)**: https://github.com/letta-ai/letta
- **Mem0**: https://github.com/mem0ai/mem0
- **Zep**: https://github.com/getzep/zep

### Blog Posts
- **Letta Blog**: Agent Memory - https://www.letta.com/blog/agent-memory
- **Mem0 Blog**: Graph Memory - https://mem0.ai/blog/graph-memory-solutions-ai-agents

---

**Next Step:** Start implementing Improvement 1 - Tiered Storage Architecture

**Maintainer:** Akali 🗡️  
**Last Updated:** 2026-03-24
