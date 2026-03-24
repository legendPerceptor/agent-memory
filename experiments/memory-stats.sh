#!/bin/bash
# Memory Token 统计工具

WORKSPACE="$HOME/.openclaw/workspace"
MEMORY_DIR="$WORKSPACE/memory"

echo "📊 Memory 系统统计"
echo "===================="
echo ""

# 统计文件大小
echo "📁 文件统计："
echo ""

# 主要文件
for file in MEMORY.md AGENTS.md USER.md TOOLS.md HEARTBEAT.md; do
    if [ -f "$WORKSPACE/$file" ]; then
        lines=$(wc -l < "$WORKSPACE/$file")
        chars=$(wc -c < "$WORKSPACE/$file")
        echo "  $file: $lines 行, $chars 字符"
    fi
done

echo ""

# 每日笔记
echo "📝 每日笔记 (memory/*.md)："
daily_files=$(ls -1 "$MEMORY_DIR"/*.md 2>/dev/null | wc -l)
total_lines=0
total_chars=0

for file in "$MEMORY_DIR"/*.md; do
    if [ -f "$file" ]; then
        lines=$(wc -l < "$file")
        chars=$(wc -c < "$file")
        total_lines=$((total_lines + lines))
        total_chars=$((total_chars + chars))
    fi
done

echo "  文件数: $daily_files"
echo "  总行数: $total_lines"
echo "  总字符: $total_chars"
echo ""

# 估算 token（粗略：1 token ≈ 4 字符）
echo "🔥 Token 估算："
startup_tokens=0
for file in MEMORY.md AGENTS.md USER.md; do
    if [ -f "$WORKSPACE/$file" ]; then
        chars=$(wc -c < "$WORKSPACE/$file")
        tokens=$((chars / 4))
        startup_tokens=$((startup_tokens + tokens))
        echo "  $file: ~$tokens tokens"
    fi
done

# 今天和昨天的 memory
today=$(date +%Y-%m-%d)
yesterday=$(date -d "yesterday" +%Y-%m-%d 2>/dev/null || date -v-1d +%Y-%m-%d)

for date in $today $yesterday; do
    file="$MEMORY_DIR/$date.md"
    if [ -f "$file" ]; then
        chars=$(wc -c < "$file")
        tokens=$((chars / 4))
        startup_tokens=$((startup_tokens + tokens))
        echo "  $date.md: ~$tokens tokens"
    fi
done

echo ""
echo "  ⚡ 启动消耗: ~$startup_tokens tokens"
echo ""

# 建议
echo "💡 优化建议："
if [ $startup_tokens -gt 10000 ]; then
    echo "  ⚠️  Token 消耗较高，建议："
    echo "     1. 精简 MEMORY.md，移除过时信息"
    echo "     2. 归档旧日志到 memory/archive/"
    echo "     3. 实施周摘要压缩"
elif [ $startup_tokens -gt 5000 ]; then
    echo "  K Token 消耗中等，可以："
    echo "     1. 定期清理 memory/*.md"
    echo "     2. 实施分层存储"
else
    echo "  ✅ Token 消耗良好，继续保持！"
fi
