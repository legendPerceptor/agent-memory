# Memory Optimization Plan

**English** | [🌐 中文](../../zh/IMPROVEMENT_PLAN.md)

## Current State Analysis

**Statistics Date:** 2026-03-24

| File | Lines | Characters | Token Estimate | Percentage |
|------|-------|------------|---------------|------------|
| AGENTS.md | 212 | 7,874 | ~1,968 | 76.7% |
| MEMORY.md | 54 | 1,951 | ~487 | 19.0% |
| USER.md | 15 | 445 | ~111 | 4.3% |
| **Total** | **281** | **10,270** | **~2,566** | **100%** |

### Findings

1. **AGENTS.md is the largest** - accounts for 77% of tokens
   - Contains behavior rules, heartbeat strategy, group chat etiquette
   - Loaded every session, but much content is rarely used

2. **MEMORY.md is well-streamlined** - only 19%
   - Mainly user information and environment configuration
   - Clear structure, easy to maintain

3. **memory/*.md not counted in startup** - daily notes loaded only when needed
   - 4 files, 302 lines, 8,973 characters
   - But each read loads everything

---

## Optimization Plans

### Plan A: Split AGENTS.md (Immediate Benefit)

**Goal:** Reduce 60-70% of startup tokens

**Implementation:**
```
AGENTS.md (Startup load - streamlined version)
├── Core rules
├── Memory usage
└── Red line rules

rules/ (On-demand loading)
├── group-chat.md    # Group chat etiquette
├── heartbeat.md     # Heartbeat strategy
└── tools.md         # Tool usage
```

**Benefits:**
- Startup tokens: 2,566 → ~1,000
- 60% reduction

---

### Plan B: Vectorize Memory (Long-term Benefit)

**Goal:** Support 100x memory scale, 50x lookup efficiency improvement

**Implementation:**
```javascript
// Reuse aicreatorvault's Qdrant
const memoryCollection = "agent-memories";

// Write memory
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

// Retrieve memory
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

**Benefits:**
- Support million-level memories
- Millisecond lookup
- Smart relevance ranking

---

### Plan C: Auto Summarization (Mid-term Benefit)

**Goal:** Compress historical logs by 90%

**Implementation:**
```bash
# Run automatically weekly
0 0 * * 0 /path/to/weekly-summary.py
```

**Flow:**
```
Day 1-7: memory/2026-03-XX.md (7 files, ~2,000 lines)
  ↓ Sunday auto-compress
Week Summary: memory/2026-W12.md (1 file, ~50 lines)
  ↓ Month-end compress again
Month Summary: memory/2026-03.md (1 file, ~10 lines)
```

**Benefits:**
- 7 days of logs → 1 day summary
- 90% token reduction
- Key information preserved

---

## Recommended Implementation Order

### Week 1: Immediate Actions (Zero Code)

- [ ] **Streamline MEMORY.md**
  - Remove completed TODOs
  - Archive outdated project information
  
- [ ] **Create memory/archive/**
  - Move logs older than 7 days
  
- [ ] **Manually write weekly summary**
  - Summarize this week's work
  - Save as `memory/2026-W12.md`

### Week 2: Automation (Simple Scripts)

- [ ] **Implement weekly-summary.py**
  - Auto-generate weekly summaries
  - Auto-archive old files
  
- [ ] **Configure cron job**
  - Run every Sunday at 00:00
  
- [ ] **Create memory-stats.sh**
  - Monitor token consumption

### Week 3-4: Vectorization (Integrate Qdrant)

- [ ] **Reuse aicreatorvault's Qdrant**
  - Create `agent-memories` collection
  
- [ ] **Implement remember/recall API**
  - Auto-vectorize when writing memories
  - Retrieve top-k related memories at startup
  
- [ ] **Optimize startup flow**
  - Only load related memories
  - Dynamically adjust context

---

## Success Metrics

| Metric | Current | Target | Improvement |
|--------|---------|--------|-------------|
| Startup Tokens | ~2,566 | ~1,000 | -61% |
| Memory Capacity | ~100 entries | ~10,000 entries | 100x |
| Lookup Speed | O(n) file scan | O(log n) vector search | 50x |
| History Compression | 0% | 90% | 90% |

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Qdrant downtime | Cannot retrieve memories | Fallback to file search |
| Vectorization latency | Slower writes | Async processing |
| Summary loses details | Incomplete information | Keep original files for 30 days |
| AGENTS.md split | Complex loading logic | Use include mechanism |

---

**Next Step:** Choose a plan to start implementing?
