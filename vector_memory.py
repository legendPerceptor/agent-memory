"""
Agent Memory 向量化服务

功能：
1. 记忆写入时自动生成 embedding 并存储到 Qdrant
2. 记忆检索时根据查询向量搜索相关记忆
3. 自动压缩历史日志（weekly summary）

依赖：
- Qdrant (localhost:6333)
- OpenAI Embedding API (text-embedding-3-small)
"""

import os
import json
import requests
from datetime import datetime
from typing import List, Dict, Optional

class VectorMemory:
    def __init__(self, qdrant_url: str = "http://host.docker.internal:6333", openai_api_key: str = None):
        self.qdrant_url = qdrant_url
        self.collection_name = "agent_memories"
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        
        # 初始化 Qdrant collection
        self._init_collection()
    
    def _init_collection(self):
        """Create collection if not exists"""
        url = f"{self.qdrant_url}/collections/{self.collection_name}"
        
        payload = {
            "vectors": {
                "size": 384,
                "distance": "Cosine"
            }
        }
        
        try:
            response = requests.put(url, json=payload)
            if response.status_code == 200:
                print(f"Collection created: {self.collection_name}")
            else:
                print(f"Collection exists: {self.collection_name}")
        except Exception as e:
            print(f"Error creating collection: {e}")
    
    def get_embedding(self, text: str) -> List[float]:
        """Get text embedding using OpenAI API"""
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY not set")
        
        url = "https://api.openai.com/v1/embeddings"
        headers = {
            "Authorization": f"Bearer {self.openai_api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "input": text,
            "model": "text-embedding-3-small"
        }
        
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        
        return response.json()["data"][0]["embedding"]
    
    def remember(self, content: str, metadata: Optional[Dict] = None) -> str:
        """
        Store a memory in Qdrant with automatic embedding
        
        Args:
            content: The memory content to remember
            metadata: Optional metadata (type, importance, tags, date)
        
        Returns:
            Memory ID
        """
        # Generate embedding
        embedding = self.get_embedding(content)
        
        # Generate unique ID
        memory_id = f"mem-{datetime.now().strftime('%Y%m%d%H%M%S')[-6:]}"
        
        # Prepare payload
        payload = {
            "content": content,
            "date": metadata.get("date", datetime.now().isoformat()) if metadata else datetime.now().isoformat(),
            "type": metadata.get("type", "general") if metadata else "general",
            "importance": metadata.get("importance", 0.5) if metadata else 0.5,
            "tags": metadata.get("tags", []) if metadata else []
        }
        
        # Store in Qdrant
        url = f"{self.qdrant_url}/collections/{self.collection_name}/points"
        point_data = {
            "id": memory_id,
            "vector": embedding,
            "payload": payload
        }
        
        response = requests.put(url, json=point_data)
        response.raise_for_status()
        
        return memory_id
    
    def recall(self, query: str, limit: int = 10, min_importance: float = 0.0) -> List[Dict]:
        """
        Retrieve relevant memories based on query
        
        Args:
            query: Search query
            limit: Maximum number of results
            min_importance: Minimum importance filter
        
        Returns:
            List of relevant memories
        """
        # Generate query embedding
        query_embedding = self.get_embedding(query)
        
        # Search in Qdrant
        url = f"{self.qdrant_url}/collections/{self.collection_name}/search"
        search_data = {
            "vector": query_embedding,
            "limit": limit,
            "filter": {
                "must": [
                    {"key": "importance", "range": {"gte": min_importance}}
                ]
            }
        }
        
        response = requests.post(url, json=search_data)
        response.raise_for_status()
        
        results = response.json()
        
        # Format results
        memories = []
        for result in results.get("result", []):
            memories.append({
                "id": result["id"],
                "content": result["payload"]["content"],
                "date": result["payload"]["date"],
                "type": result["payload"]["type"],
                "importance": result["payload"]["importance"],
                "tags": result["payload"]["tags"],
                "score": result["score"]
            })
        
        return memories
    
    def compress_memories(self, memories: List[Dict]) -> str:
        """
        Compress multiple memories into a summary
        
        Args:
            memories: List of memory dicts to compress
        
        Returns:
            Summary text
        """
        if not memories:
            return "No memories to compress"
        
        # Extract key points
        events = []
        decisions = []
        todos = []
        
        for mem in memories:
            content = mem["content"]
            if any(word in content.lower() for word in ['完成', '✅', '集成', 'finish', 'done']):
                events.append(content)
            if any(word in content.lower() for word in ['决定', '选择', '配置', 'choose', 'decide', 'decided']):
                decisions.append(content)
            if '[ ]' in content or 'todo' in content.lower():
                todos.append(content)
        
        # Generate summary
        summary = f"""本周摘要：
        
## 重要事件
{chr(10).join(f'- {e}' for e in events[:10])}

## 关键决策
{chr(10).join(f'- {d}' for d in decisions[:5])}

## 待办事项
{chr(10).join(f'- {t}' for t in todos[:10])}

---
*生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}*
"""
        
        return summary


# Example usage
if __name__ == "__main__":
    # Initialize
    memory = VectorMemory(
        qdrant_url="http://localhost:6333",
        openai_api_key="your-api-key"
    )
    
    # Remember something
    memory_id = memory.remember(
        "远见购买了 MiniMax Token Plan",
        metadata={
            "type": "fact",
            "importance": 0.8,
            "tags": ["minimax", "api", "token-plan"]
        }
    )
    print(f"Remembered: {memory_id}")
    
    # Recall memories
    memories = memory.recall(
        "MiniMax 配置",
        limit=5,
        min_importance=0.7
    )
    
    print("\n相关 memories:")
    for mem in memories:
        print(f"- [{mem['date']}] {mem['content'][:100]}... (score: {mem['score']:.2f})")