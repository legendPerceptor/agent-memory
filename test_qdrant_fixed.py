#!/usr/bin/env python3
"""
测试修复后的 Qdrant 连接
在导入 qdrant_client 之前设置 NO_PROXY
"""

import os
import sys

# ⚠️ 关键：在导入 qdrant_client 之前设置 NO_PROXY
os.environ['NO_PROXY'] = '*'
os.environ['no_proxy'] = '*'

# 现在才导入
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

def test_connection():
    """测试 Qdrant 连接"""
    try:
        print("🔌 连接 Qdrant...")
        client = QdrantClient(
            host="aicreatorvault-qdrant-1",
            port=6333,
            timeout=10
        )
        
        print("✅ 连接成功！")
        
        # 列出 collections
        collections = client.get_collections()
        print(f"\n📋 Collections ({len(collections.collections)} 个):")
        for col in collections.collections:
            print(f"  - {col.name}")
        
        # 测试创建 collection
        test_collection = "test_connection"
        try:
            client.create_collection(
                collection_name=test_collection,
                vectors_config=VectorParams(size=4, distance=Distance.COSINE)
            )
            print(f"\n✅ 测试 collection '{test_collection}' 创建成功")
            
            # 删除测试 collection
            client.delete_collection(test_collection)
            print(f"✅ 测试 collection 已清理")
        except Exception as e:
            print(f"⚠️ 测试 collection 失败: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
