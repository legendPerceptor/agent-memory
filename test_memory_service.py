#!/usr/bin/env python3
"""
测试更新后的 Memory Service
使用独立的 agent-memory-qdrant 容器
"""

import sys
sys.path.insert(0, '/home/node/.openclaw/workspace/ai-memory/vector-memory')

from memory_service import MemoryService

def test_memory_service():
    """测试 Memory Service"""
    print("🧪 测试 Agent Memory Service...\n")

    # 初始化服务
    print("1️⃣ 初始化服务...")
    service = MemoryService()

    # 检查状态
    print("\n2️⃣ 服务状态:")
    stats = service.stats()
    print(f"  - 总记忆数: {stats['total_memories']}")
    print(f"  - 存储方式: {'Qdrant' if service.use_qdrant else '文件'}")

    # 添加测试记忆
    print("\n3️⃣ 添加测试记忆...")
    memory_id = service.remember(
        text="远见创建了独立的 agent-memory-qdrant 容器，避免与 aicreatorvault 冲突",
        memory_type="event",
        importance=0.8,
        tags=["architecture", "qdrant", "agent-memory"]
    )
    print(f"  ✅ 记忆 ID: {memory_id}")

    # 添加更多测试记忆
    service.remember(
        text="OpenAI API key: sk-proj-XuVwumUzWt6DPkFKwko0",
        memory_type="config",
        importance=0.9,
        tags=["api", "openai"]
    )

    service.remember(
        text="远见喜欢英雄联盟，给助手起名阿卡丽",
        memory_type="preference",
        importance=0.7,
        tags=["user", "game", "preference"]
    )

    # 检索记忆
    print("\n4️⃣ 语义检索:")
    results = service.recall("远见的偏好", max_tokens=500)
    print(f"  查询: '远见的偏好'")
    print(f"  结果数: {len(results)}")
    if results:
        print(f"  第一个结果: {results[0]['text'][:50]}...")

    # 再次查看统计
    print("\n5️⃣ 最终统计:")
    stats = service.stats()
    print(f"  - 总记忆数: {stats['total_memories']}")
    print(f"  - 存储方式: {'Qdrant' if service.use_qdrant else '文件'}")

    print("\n✅ 测试完成！")
    return service.use_qdrant

if __name__ == "__main__":
    use_qdrant = test_memory_service()
    sys.exit(0 if use_qdrant else 1)
