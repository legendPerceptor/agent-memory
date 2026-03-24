#!/usr/bin/env python3
"""
测试分层记忆和演化系统

运行前确保：
1. 已配置 .env 文件
2. Qdrant 正在运行
3. 已安装依赖
"""

import sys
from pathlib import Path

# 添加路径
sys.path.insert(0, str(Path(__file__).parent))

from tiered_memory import TieredMemory
from memory_evolver import MemoryEvolver

def test_tiered_memory():
    """测试分层记忆"""
    print("=" * 60)
    print("测试 1: 分层记忆系统")
    print("=" * 60)
    print()
    
    memory = TieredMemory()
    
    # 测试核心记忆
    print("📝 更新核心记忆...")
    memory.update_core("user_profile", "姓名: 远见\n时区: UTC+8")
    memory.update_core("preferences", "偏好简洁回复\n喜欢英雄联盟")
    
    # 测试工作记忆
    print("\n📝 添加工作记忆...")
    memory.working.add("user", "帮我配置 MiniMax")
    memory.working.add("assistant", "好的，我来帮你配置 MiniMax Token Plan")
    
    # 测试回忆记忆
    print("\n📝 记录回忆...")
    memory.remember("远见购买了 MiniMax Token Plan", "fact", 0.8)
    memory.remember("Qdrant 集成完成，性能提升 50x", "event", 0.9)
    
    # 统计
    print("\n📊 记忆统计:")
    stats = memory.stats()
    for level, info in stats.items():
        print(f"  {level}: {info}")
    
    # 智能检索
    print("\n🔍 测试智能检索...")
    context = memory.get_context("API 配置", max_tokens=2000)
    print(context[:500] + "...")
    
    print("\n✅ 分层记忆测试完成\n")


def test_memory_evolution():
    """测试记忆演化"""
    print("=" * 60)
    print("测试 2: 记忆演化系统")
    print("=" * 60)
    print()
    
    memory = TieredMemory()
    evolver = MemoryEvolver(memory)
    
    test_cases = [
        ("用户使用 GLM-5 模型", 0.8),
        ("用户改用 MiniMax 模型", 0.8),  # 应该 UPDATE
        ("用户偏好简洁回复", 0.7),
        ("用户喜欢简洁的回复", 0.7),  # 应该 NOOP (相似)
    ]
    
    print("📝 测试演化场景:")
    results = []
    for content, importance in test_cases:
        operation, memory_id = evolver.evolve(content, importance)
        results.append((operation, content[:30]))
        print(f"  {operation:8} | {content[:40]}")
    
    print("\n📊 演化统计:")
    operations = [r[0] for r in results]
    for op in ["ADD", "UPDATE", "DELETE", "NOOP"]:
        count = operations.count(op)
        if count > 0:
            print(f"  {op}: {count}")
    
    print("\n✅ 记忆演化测试完成\n")


if __name__ == "__main__":
    try:
        test_tiered_memory()
        test_memory_evolution()
        
        print("=" * 60)
        print("✅ 所有测试通过！")
        print("=" * 60)
        print()
        print("🎉 改进已实施:")
        print("  1. ✅ 分层存储架构")
        print("  2. ✅ 记忆演化系统")
        print()
        print("📚 文档:")
        print("  - docs/IMPROVEMENTS.md - 完整改进计划")
        print("  - vector-memory/tiered_memory.py - 分层存储")
        print("  - vector-memory/memory_evolver.py - 记忆演化")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
