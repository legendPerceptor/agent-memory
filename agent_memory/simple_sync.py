#!/usr/bin/env python3
"""
简化版记忆同步脚本

直接读取 MEMORY.md 并向量化，支持智能 section 识别
"""

from pathlib import Path

from .memory_service import MemoryService

WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_FILE = WORKSPACE / "MEMORY.md"

SECTION_KEYWORDS = {
    "user_profile": ["用户", "档案", "个人", "关于", "profile", "about", "简介"],
    "preferences": ["偏好", "习惯", "喜好", "preference", "环境", "配置", "设置"],
    "current_task": ["项目", "任务", "当前", "project", "task", "工作", "计划"],
}


def _match_section(title: str) -> str | None:
    title_lower = title.lower()
    for block_name, keywords in SECTION_KEYWORDS.items():
        for kw in keywords:
            if kw in title_lower:
                return block_name
    return None


def main():
    """同步 MEMORY.md 的核心内容"""
    memory = MemoryService()

    print("🔄 开始同步记忆到 Qdrant...")

    if not MEMORY_FILE.exists():
        print("❌ MEMORY.md 不存在")
        return

    content = MEMORY_FILE.read_text()
    lines = content.strip().split('\n')

    current_section = ""
    count = 0

    for line in lines:
        line = line.strip()

        if line.startswith("## "):
            current_section = line[3:].strip()
            continue

        if not line or line.startswith('#') or line.startswith('```'):
            continue

        if line.startswith('- ') or line.startswith('* '):
            text = line.lstrip('-* ').strip()

            if len(text) < 10:
                continue

            importance = 0.5
            if any(keyword in text.lower() for keyword in ['api', 'token', 'key', 'github', '项目', 'config']):
                importance = 0.8
            elif any(keyword in text.lower() for keyword in ['邮箱', 'email', '时区', '偏好']):
                importance = 0.9

            tags = []
            if 'api' in text.lower():
                tags.append('api')
            if 'project' in text.lower() or '项目' in text:
                tags.append('project')
            if 'config' in text.lower() or '配置' in text:
                tags.append('config')

            if current_section:
                matched = _match_section(current_section)
                if matched:
                    tags.append(matched)
                text = f"[{current_section}] {text}"

            memory_id = memory.remember(
                text,
                memory_type="fact",
                importance=importance,
                tags=tags
            )

            count += 1
            print(f"  ✅ {text[:60]}...")

    print(f"\n✅ 同步完成！共 {count} 条记忆")

    print("\n🔍 测试记忆检索...")
    test_queries = ["配置", "项目", "偏好"]

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
