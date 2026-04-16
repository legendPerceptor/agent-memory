#!/usr/bin/env python3
"""
将 OpenClaw Memory 同步到 Qdrant

用法：
    python -m agent_memory.sync
    # 或
    uv run python -m agent_memory.sync
"""

import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict

from .memory_service import MemoryService

# 配置
WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory"

# 初始化向量记忆
memory = MemoryService()


def extract_memories_from_file(filepath: Path) -> List[Dict]:
    """从 markdown 文件提取记忆条目"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    memories = []
    lines = content.split('\n')

    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue

        # 跳过标题和空行
        if line.startswith('##') or line.startswith('###'):
            continue

        # 提取日期（格式：2026-03-24）
        date_match = re.search(r'\d{4}-\d{2}-\d{2}', line)
        date_str = date_match.group(0) if date_match else datetime.now().strftime('%Y-%m-%d')

        # 提取待办事项
        if line.startswith('- [ ]') or line.startswith('- [x]'):
            memory_type = 'todo'
            importance = 0.7
            memory_text = line.replace('- [ ]', '').replace('- [x]', '').strip()
        # 提取普通条目
        elif line.startswith('- '):
            memory_type = 'general'
            importance = 0.5
            memory_text = line.replace('- ', '', 1).strip()
        else:
            continue

        # 提取标签
        tags = []
        if 'todo' in memory_text.lower() or '待办' in memory_text.lower():
            tags.append('todo')
        if 'project' in memory_text.lower() or '项目' in memory_text.lower():
            tags.append('project')
        if 'config' in memory_text.lower() or '配置' in memory_text.lower():
            tags.append('config')

        memories.append({
            'content': memory_text,
            'date': date_str,
            'type': memory_type,
            'importance': importance,
            'tags': tags,
            'source': filepath.name
        })

    return memories


def main():
    """同步所有 memory 文件到 Qdrant"""
    print("🔄 开始同步记忆到 Qdrant...")

    total_memories = 0

    # 同步 MEMORY.md
    memory_file = WORKSPACE / "MEMORY.md"
    if memory_file.exists():
        print(f"\n📄 处理 {memory_file.name}...")
        memories = extract_memories_from_file(memory_file)
        total_memories += len(memories)

        for mem in memories:
            memory_id = memory.remember(
                mem['content'],
                memory_type=mem['type'],
                importance=mem['importance'],
                tags=mem['tags']
            )
            print(f"  ✅ {mem['content'][:60]}...")

    # 同步 memory/*.md
    for md_file in sorted(MEMORY_DIR.glob("*.md")):
        print(f"\n📄 处理 {md_file.name}...")
        memories = extract_memories_from_file(md_file)
        total_memories += len(memories)

        for mem in memories:
            memory_id = memory.remember(
                mem['content'],
                memory_type=mem['type'],
                importance=mem['importance'],
                tags=mem['tags']
            )
            print(f"  ✅ {mem['content'][:60]}...")

    print(f"\n✅ 同步完成！")
    print(f"📊 总计: {total_memories} 条记忆")

    # 测试检索
    print("\n🔍 测试记忆检索...")
    test_queries = [
        "MiniMax 配置",
        "Qdrant 集成",
        "项目进度"
    ]

    for query in test_queries:
        print(f"\n查询: {query}")
        results = memory.recall(query, limit=3, min_importance=0.5)
        print(f"找到 {len(results)} 条相关记忆:")
        for result in results:
            content = result['content']
            score = result['score']
            print(f"  - {content[:80]}... (score: {score:.2f})")


if __name__ == "__main__":
    main()
