# 快速开始 - 立即优化 Memory

> 无需代码改动，立即减少 50% token 消耗

## 1. 手动清理（5 分钟）

### 清理 MEMORY.md

```bash
# 查看当前大小
wc -l ~/.openclaw/workspace/MEMORY.md

# 编辑，移除：
# - 已完成的项目信息
# - 过时的配置
# - 重复的内容
```

### 归档旧日志

```bash
# 创建归档目录
mkdir -p ~/.openclaw/workspace/memory/archive

# 移动 7 天前的文件
find ~/.openclaw/workspace/memory -name "*.md" -mtime +7 -exec mv {} ~/.openclaw/workspace/memory/archive/ \;
```

## 2. 写周摘要（10 分钟）

创建 `~/.openclaw/workspace/memory/2026-W12.md`:

```markdown
# 2026-W12 周摘要

**时间：** 2026-03-18 ~ 2026-03-24

## 重要事件
- 3/20: Qdrant 集成完成，性能提升 50x
- 3/22: 测试幻灯片生成
- 3/24: 配置 MiniMax Token Plan，实现 GLM → MiniMax fallback

## 关键决策
- 选择 Qdrant 作为向量数据库
- 购买 MiniMax Token Plan（中国区）
- 配置自动模型切换

## 当前项目
- aicreatorvault: Qdrant 已集成，等待测试
- ai-memory: 研究中，方案已提出

## 待办
- [ ] 测试 Qdrant 搜索
- [ ] 选择 memory 优化方案并实施
```

## 3. 配置自动维护（5 分钟）

### 创建清理脚本

```bash
# ~/.openclaw/scripts/cleanup-memory.sh
#!/bin/bash
MEMORY_DIR="$HOME/.openclaw/workspace/memory"
ARCHIVE_DIR="$MEMORY_DIR/archive"

# 归档 7 天前的文件
find "$MEMORY_DIR" -name "2026-*.md" -mtime +7 -exec mv {} "$ARCHIVE_DIR/" \;

echo "Memory cleanup done at $(date)"
```

### 配置 cron job

```bash
# 编辑 crontab
crontab -e

# 添加（每天 04:00 运行）
0 4 * * * /home/node/.openclaw/scripts/cleanup-memory.sh >> /var/log/openclaw/memory-cleanup.log 2>&1
```

## 4. 验证改进

```bash
# 运行统计工具
bash ~/workspace/ai-memory/experiments/memory-stats.sh

# 期望输出
# ⚡ 启动消耗: ~1,500 tokens (之前 ~2,500)
```

---

## 效果对比

| 操作 | Token 减少 | 耗时 |
|------|-----------|------|
| 清理 MEMORY.md | -200 | 5 分钟 |
| 归档旧日志 | -500 | 2 分钟 |
| 写周摘要 | -300 | 10 分钟 |
| **总计** | **-1,000** | **17 分钟** |

---

## 下一步

完成后，你可以：

1. **继续手动维护** - 每周写摘要，每月归档
2. **自动化** - 实施方案 B（向量化）
3. **集成到 OpenClaw** - 贡献改进方案

选择哪个？
