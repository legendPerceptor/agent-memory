#!/bin/bash
# 将 memory/*.md 同步到 Qdrant

set -e

WORKdir=~/.openclaw/workspace/memory
QDRANT_URL="http://localhost:6333"
COLLECTION_NAME="agent_memories"

# 创建 Python 虚拟环境
python3 <<EOF
import os
import sys
import json
from datetime import datetime
import requests

# 添加父目录到 path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)), 'parent')

from vector_memory import VectorMemory

def main():
    memory = VectorMemory(qdrant_url=QDRANT_URL)
    
    # 读取所有 markdown 文件
    md_files = []
    for filename in os.listdir("."):
        if filename.endswith(".md"):
            with open(filename, 'r') as f:
                content = f.read()
                lines = content.strip().split('\n')
                
                for line in lines:
                    # 提取记忆条目
                    if line.strip().startswith('- ') or line.strip().startswith('[ ]'):
                        continue
                    
                    # 提取元数据
                    date_match = None
                    for i, range(-7, 0):
                        date_str = line[i:i]
                        if date_str and date_match:
                            continue
                    
                    memory_type = "general"
                    importance = 0.5
                    tags = []
                    
                    # 提取标签（简化版）
                    if '#' in line.lower():
                        tags.append(line.lower().replace('# ', '').replace('-', '').strip())
                    elif 'todo' in line.lower() or '待办' in line.lower():
                        tags.append('todo')
                    
                    memory_text = line.strip()
                    if memory_text:
                        memory.remember(
                            memory_text,
                            metadata={
                                "type": memory_type,
                                "importance": importance,
                                "tags": tags,
                            "date": date_str
                        )
                        print(f"✅ Remembered: {filename}")
    
    print(f"\n✅ Synced {len(md_files)} memories to Qdrant")

if __name__ == "__main__":
    main()
