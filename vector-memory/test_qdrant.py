#!/usr/bin/env python3
"""
测试 Qdrant 连接和向量检索
"""

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import hashlib

# 连接 Qdrant（使用 localhost 和端口映射）
client = QdrantClient(
    host="localhost",
    port=6333,
    timeout=10
)
print("✅ Qdrant 连接成功!")

# Collection 配置
COLLECTION_NAME = "agent_memories"
VECTOR_SIZE = 384

# 检查 collection 是否存在
try:
    collections = client.get_collections().collections
    exists = any(c.name == COLLECTION_NAME for c in collections)
    
    if exists:
        print(f"ℹ️  Collection 已存在: {COLLECTION_NAME}")
    else:
        print(f"⚠️  Collection 不存在，请先创建: {COLLECTION_NAME}")
        exit(1)
except Exception as e:
    print(f"❌ 连接错误: {e}")
    exit(1)

# 测试数据
test_memories = [
    ("远见购买了 MiniMax Token Plan", "fact", 0.8),
    ("Qdrant 集成完成，性能提升 50x", "event", 0.9),
    ("用户偏好简洁回复", "preference", 0.7),
    ("GLM → MiniMax fallback 配置", "decision", 0.8),
]

# 插入记忆
print("\n📝 插入测试记忆...")
for content, mem_type, importance in test_memories:
    # 生成伪向量（临时）
    hash_obj = hashlib.sha256(content.encode())
    hash_bytes = hash_obj.digest()
    vector = [hash_bytes[i % len(hash_bytes)] / 255.0 for i in range(VECTOR_SIZE)]
    
    # 归一化
    magnitude = sum(v ** 2 for v in vector) ** 0.5
    vector = [v / magnitude for v in vector]
    
    memory_id = hashlib.md5(content.encode()).hexdigest()[:12]
    
    client.upsert(
        collection_name=COLLECTION_NAME,
        points=[
            PointStruct(
                id=memory_id,
                vector=vector,
                payload={
                    "content": content,
                    "type": mem_type,
                    "importance": importance,
                    "tags": []
                }
            )
        ]
    )
    print(f"  ✓ {memory_id}: {content[:50]}...")

print("\n✅ 插入完成!")

# 测试检索
print("\n🔍 测试向量检索...")
queries = [
    "API 配置",
    "性能优化",
    "用户偏好"
]

for query in queries:
    print(f"\n查询: '{query}'")
    
    # 生成查询向量
    hash_obj = hashlib.sha256(query.encode())
    hash_bytes = hash_obj.digest()
    query_vector = [hash_bytes[i % len(hash_bytes)] / 255.0 for i in range(VECTOR_SIZE)]
    magnitude = sum(v ** 2 for v in query_vector) ** 0.5
    query_vector = [v / magnitude for v in query_vector]
    
    results = client.search(
        collection_name=COLLECTION_NAME,
        query_vector=query_vector,
        limit=3
    )
    
    for i, result in enumerate(results, 1):
        print(f"  {i}. [score={result.score:.3f}] {result.payload['content'][:60]}...")

print("\n✅ 测试完成!")
