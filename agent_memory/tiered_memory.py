#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分层记忆系统

实现分层存储架构：
- Level 1: Core Memory (核心记忆，始终在线)
- Level 2: Working Memory (工作记忆，最近对话)
- Level 3: Recall Memory (回忆记忆，可检索历史)
- Level 4: Archival Memory (归档记忆，压缩摘要)

灵感来源：MemGPT / Letta
"""

import json
import hashlib
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from pathlib import Path
from collections import deque

from .config import (
    MEMORY_DIR, COLLECTION_NAME, VECTOR_SIZE,
    QDRANT_HOST, QDRANT_PORT, OPENAI_API_KEY, OPENAI_EMBEDDING_MODEL,
)

# Qdrant 客户端
try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False
    print("⚠️  qdrant-client 未安装，使用文件存储")

# OpenAI 客户端
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("⚠️  openai 未安装，使用伪向量")


class CoreMemory:
    """
    Level 1: 核心记忆

    特点：
    - 始终在 context window 中
    - 存储关键信息（用户档案、偏好、当前任务）
    - 容量有限（~2000 tokens）
    """

    def __init__(self, memory_file: Path = None):
        self.memory_file = memory_file or MEMORY_DIR / "core_memory.json"
        self.blocks = self._load()

        # 默认块
        if "user_profile" not in self.blocks:
            self.blocks["user_profile"] = {
                "label": "用户档案",
                "value": "",
                "limit": 500
            }

        if "preferences" not in self.blocks:
            self.blocks["preferences"] = {
                "label": "用户偏好",
                "value": "",
                "limit": 500
            }

        if "current_task" not in self.blocks:
            self.blocks["current_task"] = {
                "label": "当前任务",
                "value": "",
                "limit": 1000
            }

    def _load(self) -> Dict:
        """加载核心记忆"""
        if self.memory_file.exists():
            return json.loads(self.memory_file.read_text())
        return {}

    def _save(self):
        """保存核心记忆"""
        self.memory_file.parent.mkdir(parents=True, exist_ok=True)
        self.memory_file.write_text(json.dumps(self.blocks, indent=2, ensure_ascii=False))

    def update(self, block_name: str, value: str, require_confirmation: bool = False):
        """更新记忆块"""
        if block_name in self.blocks:
            limit = self.blocks[block_name].get("limit", 1000)
            if len(value) > limit:
                print(f"⚠️  内容超过限制 ({len(value)} > {limit})，将被截断")
                value = value[:limit]

            self.blocks[block_name]["value"] = value
            self._save()
            print(f"✅ 核心记忆已更新: {block_name}")
        else:
            print(f"⚠️  未知的记忆块: {block_name}")

    def propose_update(self, block_name: str, new_value: str) -> Dict:
        """
        提出核心记忆变更提案（不直接执行）
        
        返回变更详情供人类审核
        """
        if block_name not in self.blocks:
            return {"error": f"未知的记忆块: {block_name}"}

        old_value = self.blocks[block_name].get("value", "")
        limit = self.blocks[block_name].get("limit", 1000)
        
        if len(new_value) > limit:
            new_value = new_value[:limit]

        return {
            "block_name": block_name,
            "block_label": self.blocks[block_name].get("label", block_name),
            "old_value": old_value,
            "new_value": new_value,
            "diff_lines": self._compute_diff(old_value, new_value),
            "token_change": (len(new_value) - len(old_value)) // 4
        }

    def _compute_diff(self, old_text: str, new_text: str) -> List[str]:
        """简单文本差异对比"""
        old_lines = set(old_text.split("\n")) if old_text else set()
        new_lines = set(new_text.split("\n")) if new_text else set()
        
        added = new_lines - old_lines
        removed = old_lines - new_lines
        
        diff = []
        for line in sorted(added):
            diff.append(f"+ {line}")
        for line in sorted(removed):
            diff.append(f"- {line}")
        
        return diff

    def append(self, block_name: str, content: str):
        """追加内容到记忆块"""
        if block_name in self.blocks:
            current = self.blocks[block_name]["value"]
            new_value = f"{current}\n{content}".strip()
            self.update(block_name, new_value)

    def get(self, block_name: str) -> str:
        """获取记忆块内容"""
        return self.blocks.get(block_name, {}).get("value", "")

    def get_all(self) -> str:
        """获取所有核心记忆（用于 context）"""
        lines = []
        for name, block in self.blocks.items():
            if block.get("value"):
                lines.append(f"## {block.get('label', name)}")
                lines.append(block["value"])
                lines.append("")
        return "\n".join(lines)

    def count_tokens(self) -> int:
        """估算 token 数量"""
        text = self.get_all()
        return len(text) // 4


class WorkingMemory:
    """
    Level 2: 工作记忆

    特点：
    - 存储最近对话
    - 自动轮换（FIFO）
    - 容量固定（最近 50 条）
    """

    def __init__(self, max_messages: int = 50):
        self.max_messages = max_messages
        self.messages = deque(maxlen=max_messages)

    def add(self, role: str, content: str, metadata: Dict = None):
        """添加消息"""
        message = {
            "id": str(uuid.uuid4())[:8],
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        self.messages.append(message)

    def get_recent(self, n: int = 10) -> List[Dict]:
        """获取最近 n 条消息"""
        return list(self.messages)[-n:]

    def get_all(self) -> List[Dict]:
        """获取所有消息"""
        return list(self.messages)

    def clear(self):
        """清空工作记忆"""
        self.messages.clear()

    def count_tokens(self, n: int = None) -> int:
        """估算 token 数量"""
        messages = self.get_recent(n) if n else self.get_all()
        text = " ".join([m["content"] for m in messages])
        return len(text) // 4


class RecallMemory:
    """
    Level 3: 回忆记忆

    特点：
    - 完整历史记录
    - 向量索引
    - 语义检索
    """

    def __init__(self):
        self.client = None
        self.use_qdrant = False

        if QDRANT_AVAILABLE:
            try:
                self.client = QdrantClient(
                    host=QDRANT_HOST,
                    port=QDRANT_PORT,
                    timeout=10,
                    check_compatibility=False
                )
                self._init_collection()
                self.use_qdrant = True
                print(f"✅ Recall Memory 连接成功: {QDRANT_HOST}:{QDRANT_PORT}")
            except Exception as e:
                print(f"⚠️  Recall Memory 连接失败: {e}")

        # 回退：文件存储
        self.memory_file = MEMORY_DIR / "recall_memory.json"
        self.memories = self._load_memories()

    def _init_collection(self):
        """初始化 Qdrant collection"""
        try:
            collections = self.client.get_collections().collections
            exists = any(c.name == COLLECTION_NAME for c in collections)

            if not exists:
                self.client.create_collection(
                    collection_name=COLLECTION_NAME,
                    vectors_config=VectorParams(
                        size=VECTOR_SIZE,
                        distance=Distance.COSINE
                    )
                )
                print(f"✅ 创建 collection: {COLLECTION_NAME}")
        except Exception as e:
            raise Exception(f"初始化 collection 失败: {e}")

    def _load_memories(self) -> List[Dict]:
        """从文件加载记忆"""
        if self.memory_file.exists():
            return json.loads(self.memory_file.read_text())
        return []

    def _save_memories(self):
        """保存记忆到文件"""
        self.memory_file.parent.mkdir(parents=True, exist_ok=True)
        self.memory_file.write_text(json.dumps(self.memories, indent=2, ensure_ascii=False))

    def _get_embedding(self, text: str) -> List[float]:
        """获取文本的向量表示"""
        import os
        import httpx

        if OPENAI_AVAILABLE and OPENAI_API_KEY:
            try:
                client = OpenAI(
                    api_key=OPENAI_API_KEY,
                    base_url="https://api.openai.com/v1",
                    http_client=httpx.Client(proxy=os.getenv("HTTPS_PROXY", "")),
                    timeout=30
                )

                response = client.embeddings.create(
                    model=OPENAI_EMBEDDING_MODEL,
                    input=text
                )

                return response.data[0].embedding
            except Exception as e:
                print(f"⚠️  OpenAI embedding 失败: {e}")

        # 回退：伪向量
        hash_obj = hashlib.sha256(text.encode())
        hash_bytes = hash_obj.digest()
        vector = []
        for i in range(VECTOR_SIZE):
            byte_idx = i % len(hash_bytes)
            next_byte_idx = (byte_idx + 1) % len(hash_bytes)
            vector.append((hash_bytes[byte_idx] + hash_bytes[next_byte_idx]) / 510.0)

        magnitude = sum(v ** 2 for v in vector) ** 0.5
        if magnitude > 0:
            vector = [v / magnitude for v in vector]

        return vector

    def remember(
        self,
        content: str,
        memory_type: str = "fact",
        importance: float = 0.5,
        tags: List[str] = None
    ) -> str:
        """记录回忆"""

        memory_id = str(uuid.uuid4())
        short_id = hashlib.md5(f"{content}{datetime.now().isoformat()}".encode()).hexdigest()[:12]

        memory = {
            "id": short_id,
            "qdrant_id": memory_id,
            "content": content,
            "type": memory_type,
            "importance": importance,
            "tags": tags or [],
            "created_at": datetime.now().isoformat(),
            "access_count": 0,
            "human_rating": 0,
            "feedback_count": 0,
            "reviewed": False,
            "protected": False
        }

        if self.use_qdrant:
            try:
                vector = self._get_embedding(content)

                self.client.upsert(
                    collection_name=COLLECTION_NAME,
                    points=[
                        PointStruct(
                            id=memory_id,
                            vector=vector,
                            payload=memory
                        )
                    ]
                )
                print(f"✅ 回忆已存储到 Qdrant: {short_id}")
            except Exception as e:
                print(f"⚠️  Qdrant 存储失败: {e}")
                self.memories.append(memory)
                self._save_memories()
        else:
            self.memories.append(memory)
            self._save_memories()
            print(f"✅ 回忆已存储到文件: {short_id}")

        return short_id

    def recall(
        self,
        query: str,
        limit: int = 10,
        min_importance: float = 0.0,
        memory_type: Optional[str] = None
    ) -> List[Dict]:
        """检索回忆"""

        if self.use_qdrant:
            try:
                vector = self._get_embedding(query)

                from qdrant_client.models import Filter, FieldCondition, Range

                conditions = []
                if min_importance > 0:
                    conditions.append(
                        FieldCondition(
                            key="importance",
                            range=Range(gte=min_importance)
                        )
                    )

                results = self.client.query_points(
                    collection_name=COLLECTION_NAME,
                    query=vector,
                    limit=limit,
                    query_filter=Filter(must=conditions) if conditions else None
                )

                memories = [
                    {
                        "id": str(point.id),
                        "score": point.score,
                        **point.payload
                    }
                    for point in results.points
                ]

                print(f"✅ 从 Qdrant 检索到 {len(memories)} 条回忆")
                return memories

            except Exception as e:
                print(f"⚠️  Qdrant 检索失败: {e}")

        # 回退：文件搜索
        scored_memories = []
        query_words = set(query.lower().split())

        for memory in self.memories:
            content_lower = memory["content"].lower()
            score = 0.0

            for word in query_words:
                if word in content_lower:
                    score += 1.0

            score *= memory.get("importance", 0.5)

            if memory_type and memory.get("type") != memory_type:
                continue

            if score > 0 and memory.get("importance", 0) >= min_importance:
                memory_copy = memory.copy()
                memory_copy["score"] = score
                scored_memories.append(memory_copy)

        scored_memories.sort(key=lambda x: x["score"], reverse=True)
        print(f"✅ 从文件检索到 {len(scored_memories[:limit])} 条回忆")
        return scored_memories[:limit]

    def stats(self) -> Dict:
        """统计信息"""
        if self.use_qdrant:
            try:
                info = self.client.get_collection(collection_name=COLLECTION_NAME)
                return {
                    "storage": "qdrant",
                    "count": info.points_count,
                    "status": info.status.value
                }
            except:
                pass

        return {
            "storage": "file",
            "count": len(self.memories),
            "file": str(self.memory_file)
        }

    def rate_memory(self, memory_id: str, rating: int) -> None:
        """评价记忆（+1 有用 / -1 无用）"""
        if rating not in [-1, 0, 1]:
            raise ValueError("rating 必须是 -1, 0 或 1")

        for mem in self.memories:
            if mem.get("id") == memory_id or mem.get("qdrant_id") == memory_id:
                mem["human_rating"] = mem.get("human_rating", 0) + rating
                mem["feedback_count"] = mem.get("feedback_count", 0) + 1
                self._save_memories()
                return

        if self.use_qdrant:
            try:
                self.client.set_payload(
                    collection_name=COLLECTION_NAME,
                    payload={
                        "human_rating": rating,
                        "feedback_count": 1
                    },
                    points=[memory_id]
                )
            except Exception as e:
                print(f"⚠️  Qdrant 更新评价失败: {e}")

    def update_memory(self, memory_id: str, content: str = None, importance: float = None) -> bool:
        """修改已有记忆的内容或重要性"""
        for mem in self.memories:
            if mem.get("id") == memory_id or mem.get("qdrant_id") == memory_id:
                if content is not None:
                    mem["content"] = content
                if importance is not None:
                    mem["importance"] = importance
                mem["reviewed"] = True
                self._save_memories()
                return True

        if self.use_qdrant:
            try:
                payload = {"reviewed": True}
                if content is not None:
                    payload["content"] = content
                if importance is not None:
                    payload["importance"] = importance
                self.client.set_payload(
                    collection_name=COLLECTION_NAME,
                    payload=payload,
                    points=[memory_id]
                )
                return True
            except Exception as e:
                print(f"⚠️  Qdrant 更新记忆失败: {e}")

        return False

    def set_protected(self, memory_id: str, protected: bool) -> None:
        """设置记忆保护状态（受保护的记忆不会被压缩或删除）"""
        for mem in self.memories:
            if mem.get("id") == memory_id or mem.get("qdrant_id") == memory_id:
                mem["protected"] = protected
                self._save_memories()
                return

        if self.use_qdrant:
            try:
                self.client.set_payload(
                    collection_name=COLLECTION_NAME,
                    payload={"protected": protected},
                    points=[memory_id]
                )
            except Exception as e:
                print(f"⚠️  Qdrant 设置保护失败: {e}")


class ArchivalMemory:
    """
    Level 4: 归档记忆

    特点：
    - 压缩摘要
    - 长期存储
    - 低频访问
    """

    def __init__(self):
        self.archive_dir = MEMORY_DIR / "archive"
        self.archive_dir.mkdir(parents=True, exist_ok=True)

    def archive_memories(self, memories: List[Dict], summary: str):
        """归档记忆"""

        archive_entry = {
            "id": str(uuid.uuid4())[:12],
            "summary": summary,
            "original_count": len(memories),
            "archived_at": datetime.now().isoformat(),
            "date_range": {
                "start": min(m["created_at"] for m in memories),
                "end": max(m["created_at"] for m in memories)
            }
        }

        archive_file = self.archive_dir / f"{archive_entry['id']}.json"
        archive_file.write_text(json.dumps({
            "entry": archive_entry,
            "memories": memories
        }, indent=2, ensure_ascii=False))

        print(f"✅ 已归档 {len(memories)} 条记忆: {archive_entry['id']}")
        return archive_entry["id"]

    def list_archives(self) -> List[Dict]:
        """列出所有归档"""
        archives = []
        for file in self.archive_dir.glob("*.json"):
            data = json.loads(file.read_text())
            archives.append(data["entry"])
        return sorted(archives, key=lambda x: x["archived_at"], reverse=True)


class TieredMemory:
    """
    分层记忆系统

    整合四个层级的记忆存储
    """

    def __init__(self):
        self.core = CoreMemory()
        self.working = WorkingMemory()
        self.recall_mem = RecallMemory()
        self.archival = ArchivalMemory()

        print("✅ 分层记忆系统已初始化")

    def remember(
        self,
        content: str,
        memory_type: str = "fact",
        importance: float = 0.5,
        tags: List[str] = None,
        level: str = "recall"
    ):
        """记录记忆"""
        if level == "core":
            print("⚠️  核心记忆需要指定块名，使用 update_core() 方法")
            return None
        elif level == "working":
            self.working.add("system", content, {"type": memory_type, "importance": importance})
            return "working"
        else:
            return self.recall_mem.remember(content, memory_type, importance, tags)

    def update_core(self, block_name: str, value: str):
        """更新核心记忆"""
        self.core.update(block_name, value)

    def recall(
        self,
        query: str,
        context_budget: int = 4000,
        min_importance: float = 0.0
    ) -> Dict[str, Any]:
        """智能检索记忆"""
        result = {
            "core": "",
            "working": [],
            "recall": [],
            "tokens_used": 0
        }

        remaining_budget = context_budget

        # 1. 加载核心记忆 (始终包含)
        core_text = self.core.get_all()
        core_tokens = self.core.count_tokens()

        if core_tokens <= remaining_budget:
            result["core"] = core_text
            result["tokens_used"] += core_tokens
            remaining_budget -= core_tokens

        # 2. 加载工作记忆 (最近对话)
        working_messages = self.working.get_recent(10)
        for msg in reversed(working_messages):
            msg_tokens = len(msg["content"]) // 4
            if msg_tokens <= remaining_budget:
                result["working"].insert(0, msg)
                result["tokens_used"] += msg_tokens
                remaining_budget -= msg_tokens
            else:
                break

        # 3. 检索回忆记忆 (语义搜索)
        if remaining_budget > 500:
            recall_results = self.recall_mem.recall(
                query,
                limit=10,
                min_importance=min_importance
            )

            for mem in recall_results:
                mem_tokens = len(mem["content"]) // 4
                if mem_tokens <= remaining_budget:
                    result["recall"].append(mem)
                    result["tokens_used"] += mem_tokens
                    remaining_budget -= mem_tokens
                else:
                    break

        return result

    def get_context(self, query: str = "", max_tokens: int = 4000) -> str:
        """获取完整的 context 文本"""
        result = self.recall(query, context_budget=max_tokens)

        context_parts = []

        if result["core"]:
            context_parts.append("=== 核心记忆 ===")
            context_parts.append(result["core"])

        if result["working"]:
            context_parts.append("\n=== 最近对话 ===")
            for msg in result["working"]:
                context_parts.append(f"{msg['role']}: {msg['content']}")

        if result["recall"]:
            context_parts.append("\n=== 相关记忆 ===")
            for mem in result["recall"]:
                context_parts.append(f"- [{mem.get('score', 0):.2f}] {mem['content']}")

        return "\n".join(context_parts)

    def stats(self) -> Dict:
        """统计信息"""
        return {
            "core": {
                "blocks": len(self.core.blocks),
                "tokens": self.core.count_tokens()
            },
            "working": {
                "messages": len(self.working.messages),
                "max": self.working.max_messages
            },
            "recall": self.recall_mem.stats(),
            "archival": {
                "archives": len(self.archival.list_archives())
            }
        }


# 测试代码
if __name__ == "__main__":
    print("=" * 60)
    print("分层记忆系统测试")
    print("=" * 60)

    memory = TieredMemory()
    print()

    print("📝 测试核心记忆...")
    memory.update_core("user_profile", "姓名: 远见\n时区: UTC+8\n邮箱: test@example.com")
    memory.update_core("preferences", "偏好简洁回复\n喜欢英雄联盟")
    print()

    print("📝 测试工作记忆...")
    memory.working.add("user", "你好")
    memory.working.add("assistant", "你好！有什么可以帮助你的？")
    memory.working.add("user", "帮我配置 MiniMax")
    print()

    print("📝 测试回忆记忆...")
    memory.remember("远见购买了 MiniMax Token Plan", "fact", 0.8, ["api", "minimax"])
    memory.remember("Qdrant 集成完成，性能提升 50x", "event", 0.9, ["performance"])
    print()

    print("📊 记忆统计:")
    stats = memory.stats()
    print(json.dumps(stats, indent=2, ensure_ascii=False))
    print()

    print("🔍 测试智能检索...")
    context = memory.get_context("API 配置", max_tokens=2000)
    print(context)
    print()

    print("=" * 60)
    print("✅ 测试完成！")
    print("=" * 60)
