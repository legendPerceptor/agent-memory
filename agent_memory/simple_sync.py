#!/usr/bin/env python3
"""
简化版记忆同步脚本

直接读取 MEMORY.md 并向量化
"""

from pathlib import Path

from .memory_service import MemoryService

# 配置
WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_FILE = WORKSPACE / "MEMORY.md"


def main():
    """同步 MEMORY.md 的核心内容"""
    memory = MemoryService()

    print("🔄 开始同步记忆到 Qdrant...")

    # 读取 MEMORY.md
    if not MEMORY_FILE.exists():
        print("❌ MEMORY.md 不存在")
        return

    content = MEMORY_FILE.read_text()
    lines = content.strip().split('\n')

    count = 0
    for line in lines:
        line = line.strip()

        # 跳过空行、标题、注释
        if not line or line.startswith('#') or line.startswith('```'):
            continue

        # 提取有价值的行
        if line.startswith('- ') or line.startswith('* '):
            text = line.lstrip('-* ').strip()

            # 跳过过短的行
            if len(text) < 10:
                continue

            # 判断重要性
            importance = 0.5
            if any(keyword in text.lower() for keyword in ['api', 'token', 'key', 'github', '项目', 'config']):
                importance = 0.8
            elif any(keyword in text.lower() for keyword in ['邮箱', 'email', '时区', '偏好']):
                importance = 0.9

            # 提取标签
            tags = []
            if 'api' in text.lower():
                tags.append('api')
            if 'project' in text.lower() or '项目' in text:
                tags.append('project')
            if 'config' in text.lower() or '配置' in text:
                tags.append('config')

            # 写入记忆
            memory_id = memory.remember(
                text,
                memory_type="fact",
                importance=importance,
                tags=tags
            )

            count += 1
            print(f"  ✅ {text[:60]}...")

    print(f"\n✅ 同步完成！共 {count} 条记忆")

    # 测试检索
    print("\n🔍 测试记忆检索...")
    test_queries = ["MiniMax", "项目", "配置"]

    for query in test_queries:
        print(f"\n查询: {query}")
        results = memory.recall(query, limit=3, min_importance=0.5)
        print(f"找到 {len(results)} 条相关记忆:")
        for result in results[:2]:
            content = result['content']
            score = result['score']
            print(f"  - {content[:60]}... (score: {score:.2f})")


if __name__ == "__main__":
    main()
