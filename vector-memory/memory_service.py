#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agent Memory Vector Service

功能：
1. 将记忆条目向量化并存储到 Qdrant
2. 语义检索相关记忆
3. 自动压缩旧记忆

依赖：
- qdrant-client
- openai (用于 embedding)
- sentence-transformers (可选，本地模型)
"""

import os
import json
import hashlib
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path

# 解决代理问题：在导入之前设置
os.environ["NO_PROXY"] = "*"
os.environ["no_proxy"] = "*"

# 加载 .env 文件
env_file = Path(__file__).parent.parent / ".env"
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            if "=" in line and not line.startswith("#"):
                key, value = line.strip().split("=", 1)
                os.environ[key] = value

# 配置
MEMORY_DIR = Path.home() / ".openclaw" / "workspace" / "memory"
COLLECTION_NAME = "agent_memories"
VECTOR_SIZE = 1536  # text-embedding-3-small
QDRANT_HOST = os.getenv("QDRANT_HOST", "aicreatorvault-qdrant-1")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

# Qdrant 客户端
try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False
    print("⚠️  qdrant-client 未安装，使用文件存储回退")

# OpenAI 客户端
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("⚠️  openai 未安装，使用伪向量回退")


class MemoryService:
    """Agent Memory 向量化服务"""
    
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
                print(f"✅ Qdrant 连接成功: {QDRANT_HOST}:{QDRANT_PORT}")
            except Exception as e:
                print(f"⚠️  Qdrant 连接失败: {e}")
                print("使用文件存储回退")
        
        # 回退：文件存储
        self.memory_file = MEMORY_DIR / "vector_memories.json"
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
        """从文件加载记忆（回退方案）"""
        if self.memory_file.exists():
            return json.loads(self.memory_file.read_text())
        return []
    
    def _save_memories(self):
        """保存记忆到文件（回退方案）"""
        self.memory_file.write_text(json.dumps(self.memories, indent=2, ensure_ascii=False))
    
    def _get_embedding(self, text: str) -> List[float]:
        """获取文本的向量表示 - 优先使用 OpenAI API"""
        
        # 优先使用 OpenAI API
        if OPENAI_AVAILABLE and OPENAI_API_KEY:
            try:
                import httpx
                # 使用代理访问 OpenAI
                proxies = {
                    "http://": os.getenv("HTTP_PROXY", ""),
                    "https://": os.getenv("HTTPS_PROXY", "")
                }
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
                print("使用伪向量回退")
        
        # 回退：使用简单的哈希作为伪向量（仅用于演示）
        hash_obj = hashlib.sha256(text.encode())
        hash_bytes = hash_obj.digest()
        
        # 生成 1536 维向量（text-embedding-3-small）
        vector = []
        for i in range(VECTOR_SIZE):
            byte_idx = i % len(hash_bytes)
            next_byte_idx = (byte_idx + 1) % len(hash_bytes)
            vector.append((hash_bytes[byte_idx] + hash_bytes[next_byte_idx]) / 510.0)
        
        # 归一化
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
        """
        记录一条新记忆
        """
        import uuid
        # 使用 UUID 作为 Qdrant point ID
        memory_id = str(uuid.uuid4())
        # 同时生成短 ID 用于文件存储
        short_id = hashlib.md5(f"{content}{datetime.now().isoformat()}".encode()).hexdigest()[:12]
        
        memory = {
            "id": short_id,  # 用于文件存储
            "qdrant_id": memory_id,  # 用于 Qdrant
            "content": content,
            "type": memory_type,
            "importance": importance,
            "tags": tags or [],
            "created_at": datetime.now().isoformat(),
            "access_count": 0
        }
        
        if self.use_qdrant:
            try:
                vector = self._get_embedding(content)
                
                self.client.upsert(
                    collection_name=COLLECTION_NAME,
                    points=[
                        PointStruct(
                            id=memory_id,  # 使用 UUID
                            vector=vector,
                            payload=memory
                        )
                    ]
                )
                print(f"✅ 记忆已存储到 Qdrant: {short_id}")
            except Exception as e:
                print(f"⚠️  Qdrant 存储失败，使用文件: {e}")
                self.memories.append(memory)
                self._save_memories()
        else:
            self.memories.append(memory)
            self._save_memories()
            print(f"✅ 记忆已存储到文件: {short_id}")
        
        return short_id
    
    def recall(
        self,
        query: str,
        limit: int = 10,
        min_importance: float = 0.0,
        memory_type: Optional[str] = None
    ) -> List[Dict]:
        """
        检索相关记忆
        """
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
                
                print(f"✅ 从 Qdrant 检索到 {len(memories)} 条记忆")
                return memories
                
            except Exception as e:
                print(f"⚠️  Qdrant 检索失败，使用文件搜索: {e}")
        
        # 回退：简单关键词匹配
        scored_memories = []
        query_words = set(query.lower().split())
        
        for memory in self.memories:
            # 简单相关性分数
            content_lower = memory["content"].lower()
            score = 0.0
            
            # 词匹配
            for word in query_words:
                if word in content_lower:
                    score += 1.0
            
            # 重要性加权
            score *= memory.get("importance", 0.5)
            
            # 类型过滤
            if memory_type and memory.get("type") != memory_type:
                continue
            
            if score > 0 and memory.get("importance", 0) >= min_importance:
                memory_copy = memory.copy()
                memory_copy["score"] = score
                scored_memories.append(memory_copy)
        
        scored_memories.sort(key=lambda x: x["score"], reverse=True)
        print(f"✅ 从文件检索到 {len(scored_memories[:limit])} 条记忆")
        return scored_memories[:limit]
    
    def compress(self, days_old: int = 30) -> int:
        """压缩旧记忆"""
        print(f"压缩功能待实现（{days_old} 天前的记忆）")
        return 0
    
    def stats(self) -> Dict:
        """获取统计信息"""
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


def main():
    """测试记忆服务"""
    print("=" * 60)
    print("Agent Memory Vector Service - 测试")
    print("=" * 60)
    print()
    
    service = MemoryService()
    print()
    
    stats = service.stats()
    print(f"📊 当前状态: {stats}")
    print()
    
    test_memories = [
        ("远见购买了 MiniMax Token Plan", "fact", 0.8, ["api", "minimax"]),
        ("Qdrant 集成完成，性能提升 50x", "event", 0.9, ["qdrant", "performance"]),
        ("用户偏好简洁回复", "preference", 0.7, ["communication"]),
        ("GLM → MiniMax fallback 配置", "decision", 0.8, ["config", "fallback"]),
    ]
    
    print("📝 写入测试记忆...")
    for content, mem_type, importance, tags in test_memories:
        memory_id = service.remember(content, mem_type, importance, tags)
        print(f"  - {memory_id}: {content[:50]}...")
    print()
    
    print("🔍 测试检索...")
    queries = ["API 配置", "性能优化", "用户偏好"]
    
    for query in queries:
        print(f"\n查询: '{query}'")
        results = service.recall(query, limit=3)
        for i, mem in enumerate(results, 1):
            print(f"  {i}. [{mem.get('score', 0):.2f}] {mem['content'][:60]}...")
    
    print()
    print("✅ 测试完成")


if __name__ == "__main__":
    main()
