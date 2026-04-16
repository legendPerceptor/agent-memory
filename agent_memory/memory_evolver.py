#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
记忆演化系统

功能：
1. 自动去重 - 检测重复记忆
2. 智能更新 - 更新矛盾信息
3. 自动删除 - 清理过时记忆
4. LLM 驱动的演化决策

灵感来源：Mem0 (ADD/UPDATE/DELETE/NOOP)
"""

import json
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from pathlib import Path

from .tiered_memory import TieredMemory, RecallMemory

# 配置
MEMORY_DIR = Path.home() / ".openclaw" / "workspace" / "memory"


class MemoryEvolver:
    """
    记忆演化系统

    根据新信息自动演化现有记忆
    """

    def __init__(self, memory_system: TieredMemory = None):
        self.memory = memory_system or TieredMemory()
        self.recall = self.memory.recall_mem

        # 演化规则
        self.contradiction_keywords = [
            ("改用", "使用"),
            ("换成", "使用"),
            ("更新为", "是"),
            ("改为", "是"),
            ("不再", "使用"),
        ]

        self.obsolete_keywords = [
            "临时", "测试", "临时测试", "待删除"
        ]

    def evolve(self, new_content: str, importance: float = 0.5) -> Tuple[str, str]:
        """演化记忆"""
        # 1. 检索相似记忆
        similar = self.recall.recall(new_content, limit=3)

        if not similar:
            memory_id = self.recall.remember(new_content, "fact", importance)
            return ("ADD", memory_id)

        best_match = similar[0]
        similarity_score = best_match.get("score", 0)

        # 2. 判断操作类型
        if similarity_score > 0.95:
            print(f"⏭️  重复记忆，跳过: {best_match['id']}")
            return ("NOOP", best_match["id"])

        # 3. 检查是否矛盾
        operation = self._classify_operation(new_content, best_match["content"])

        if operation == "UPDATE":
            old_id = best_match["id"]
            updated_content = self._merge_content(
                best_match["content"],
                new_content
            )

            self._delete_memory(best_match.get("qdrant_id", old_id))

            new_id = self.recall.remember(
                updated_content,
                best_match.get("type", "fact"),
                max(importance, best_match.get("importance", 0.5))
            )

            print(f"🔄 记忆已更新: {old_id} → {new_id}")
            return ("UPDATE", new_id)

        elif operation == "DELETE":
            self._delete_memory(best_match.get("qdrant_id", best_match["id"]))
            print(f"🗑️  过时记忆已删除: {best_match['id']}")
            return ("DELETE", None)

        else:
            memory_id = self.recall.remember(new_content, "fact", importance)
            return ("ADD", memory_id)

    def _classify_operation(self, new_content: str, old_content: str) -> str:
        """判断操作类型"""
        new_lower = new_content.lower()
        old_lower = old_content.lower()

        # 1. 检查矛盾
        for new_kw, old_kw in self.contradiction_keywords:
            if new_kw in new_lower and old_kw in old_lower:
                return "UPDATE"

        # 2. 检查过时
        for keyword in self.obsolete_keywords:
            if keyword in new_lower or keyword in old_lower:
                return "DELETE"

        # 3. 检查重复
        overlap = len(set(new_lower.split()) & set(old_lower.split()))
        total = len(set(new_lower.split()) | set(old_lower.split()))

        if total > 0 and overlap / total > 0.8:
            return "NOOP"

        return "ADD"

    def _merge_content(self, old_content: str, new_content: str) -> str:
        """合并新旧内容"""
        timestamp = datetime.now().strftime("%Y-%m-%d")
        return f"{new_content} (更新于 {timestamp})"

    def _delete_memory(self, memory_id: str):
        """删除记忆"""
        if self.recall.use_qdrant:
            try:
                from qdrant_client.models import PointIdsList
                self.recall.client.delete(
                    collection_name="agent_memories",
                    points_selector=PointIdsList(
                        points=[memory_id]
                    )
                )
            except Exception as e:
                print(f"⚠️  Qdrant 删除失败: {e}")

        # 文件删除
        self.recall.memories = [
            m for m in self.recall.memories
            if m.get("id") != memory_id and m.get("qdrant_id") != memory_id
        ]
        self.recall._save_memories()

    def batch_evolve(self, memories: List[Tuple[str, float]]) -> Dict[str, int]:
        """批量演化记忆"""
        stats = {"ADD": 0, "UPDATE": 0, "DELETE": 0, "NOOP": 0}

        for content, importance in memories:
            operation, _ = self.evolve(content, importance)
            stats[operation] += 1

        print(f"📊 批量演化完成: {stats}")
        return stats

    def cleanup_obsolete(self, days_old: int = 90, min_importance: float = 0.7):
        """清理过时记忆"""
        cutoff_date = datetime.now() - timedelta(days=days_old)

        deleted = 0

        for memory in self.recall.memories[:]:
            created_at = datetime.fromisoformat(memory.get("created_at", datetime.now().isoformat()))
            importance = memory.get("importance", 0.5)

            if created_at < cutoff_date and importance < min_importance:
                self._delete_memory(memory.get("qdrant_id", memory["id"]))
                deleted += 1

        print(f"🗑️  已清理 {deleted} 条过时记忆")


# 测试代码
if __name__ == "__main__":
    print("=" * 60)
    print("记忆演化系统测试")
    print("=" * 60)
    print()

    evolver = MemoryEvolver()
    print()

    test_cases = [
        ("用户使用 GLM-5 模型", 0.8),
        ("用户改用 MiniMax 模型", 0.8),
        ("用户偏好简洁回复", 0.7),
        ("用户喜欢简洁的回复", 0.7),
        ("临时测试配置", 0.3),
    ]

    print("📝 测试演化场景...")
    for content, importance in test_cases:
        operation, memory_id = evolver.evolve(content, importance)
        print(f"  {operation}: {content[:30]}... → {memory_id}")

    print()
    print("✅ 测试完成！")
