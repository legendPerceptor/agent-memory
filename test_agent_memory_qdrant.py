#!/usr/bin/env python3
"""
测试 Agent Memory 专用 Qdrant 连接
"""

import os
import sys

# ⚠️ 关键：在导入 qdrant_client 之前设置 NO_PROXY
os.environ['NO_PROXY'] = '*'
os.environ['no_proxy'] = '*'

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import time

def test_agent_memory_qdrant():
    """测试 Agent Memory 专用 Qdrant"""
    try:
        print("🔌 连接 Agent Memory Qdrant...")
        client = QdrantClient(
            host="agent-memory-qdrant",
            port=6333,
            timeout=10
        )

        print("✅ 连接成功！\n")

        # 列出 collections
        collections = client.get_collections()
        print(f"📋 Collections ({len(collections.collections)} 个):")
        for col in collections.collections:
            print(f"  - {col.name}")

        # 创建测试 collection
        test_collection = "agent_memory_test"
        print(f"\n🔨 创建测试 collection: {test_collection}")

        try:
            client.create_collection(
                collection_name=test_collection,
                vectors_config=VectorParams(size=4, distance=Distance.COSINE)
            )
            print("✅ Collection 创建成功")

            # 插入测试数据
            print("\n📝 插入测试数据...")
            client.upsert(
                collection_name=test_collection,
                points=[
                    PointStruct(
                        id=1,
                        vector=[0.1, 0.2, 0.3, 0.4],
                        payload={"test": "data", "timestamp": time.time()}
                    )
                ]
            )
            print("✅ 数据插入成功")

            # 检索数据
            print("\n🔍 检索测试数据...")
            result = client.retrieve(
                collection_name=test_collection,
                ids=[1]
            )
            print(f"✅ 检索成功: {result[0].payload}")

            # 删除测试 collection
            print(f"\n🗑️  清理测试 collection...")
            client.delete_collection(test_collection)
            print("✅ 测试 collection 已清理")

        except Exception as e:
            print(f"⚠️ 测试失败: {e}")
            return False

        print("\n🎉 所有测试通过！Agent Memory Qdrant 已就绪！")
        return True

    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return False

if __name__ == "__main__":
    success = test_agent_memory_qdrant()
    sys.exit(0 if success else 1)
