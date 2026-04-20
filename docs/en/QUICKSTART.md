# Quick Start - Optimize Memory Immediately

**English** | [🌐 中文](../../zh/QUICKSTART.md)

> No code changes needed, reduce token consumption by 50% immediately

## 1. Manual Cleanup (5 minutes)

### Clean Up MEMORY.md

```bash
# Check current size
wc -l ~/.openclaw/workspace/MEMORY.md

# Edit and remove:
# - Completed project information
# - Outdated configurations
# - Duplicate content
```

### Archive Old Logs

```bash
# Create archive directory
mkdir -p ~/.openclaw/workspace/memory/archive

# Move files older than 7 days
find ~/.openclaw/workspace/memory -name "*.md" -mtime +7 -exec mv {} ~/.openclaw/workspace/memory/archive/ \;
```

## 2. Write Weekly Summary (10 minutes)

Create `~/.openclaw/workspace/memory/2026-W12.md`:

```markdown
# 2026-W12 Weekly Summary

**Period:** 2026-03-18 ~ 2026-03-24

## Key Events
- 3/20: Qdrant integration complete, 50x performance improvement
- 3/22: Test slide generation
- 3/24: Configure MiniMax Token Plan, implement GLM → MiniMax fallback

## Key Decisions
- Choose Qdrant as vector database
- Purchase MiniMax Token Plan (China region)
- Configure automatic model switching

## Current Projects
- aicreatorvault: Qdrant integrated, awaiting testing
- ai-memory: Under research, plan proposed

## TODO
- [ ] Test Qdrant search
- [ ] Select and implement memory optimization plan
```

## 3. Configure Auto Maintenance (5 minutes)

### Create Cleanup Script

```bash
# ~/.openclaw/scripts/cleanup-memory.sh
#!/bin/bash
MEMORY_DIR="$HOME/.openclaw/workspace/memory"
ARCHIVE_DIR="$MEMORY_DIR/archive"

# Archive files older than 7 days
find "$MEMORY_DIR" -name "2026-*.md" -mtime +7 -exec mv {} "$ARCHIVE_DIR/" \;

echo "Memory cleanup done at $(date)"
```

### Configure cron job

```bash
# Edit crontab
crontab -e

# Add (run daily at 04:00)
0 4 * * * /home/node/.openclaw/scripts/cleanup-memory.sh >> /var/log/openclaw/memory-cleanup.log 2>&1
```

## 4. Verify Improvements

```bash
# Run statistics tool
bash ~/workspace/ai-memory/experiments/memory-stats.sh

# Expected output
# ⚡ Startup consumption: ~1,500 tokens (previously ~2,500)
```

---

## Results Comparison

| Operation | Token Reduction | Time |
|-----------|----------------|------|
| Clean MEMORY.md | -200 | 5 minutes |
| Archive old logs | -500 | 2 minutes |
| Write weekly summary | -300 | 10 minutes |
| **Total** | **-1,000** | **17 minutes** |

---

## Next Steps

After completion, you can:

1. **Continue manual maintenance** - Write weekly summaries, archive monthly
2. **Automate** - Implement Plan B (vectorization)
3. **Integrate into OpenClaw** - Contribute improvement proposals

Which one to choose?
