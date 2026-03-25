#!/usr/bin/env python3
"""
知识图谱与记忆服务集成

功能：
1. 自动从记忆内容中提取实体和关系
2. 查询时结合图谱上下文
3. 图谱可视化
4. 实体共指消解（同一实体的不同表述）
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Optional

# 添加路径
sys.path.insert(0, str(Path(__file__).parent))

from knowledge_graph import (
    KnowledgeGraph,
    EntityType,
    RelationType,
    get_knowledge_graph
)
from memory_service import MemoryService


class EnhancedMemoryWithGraph:
    """带知识图谱的增强记忆服务"""
    
    def __init__(self, memory_service: MemoryService = None):
        """
        初始化增强记忆服务
        
        参数：
            memory_service: 记忆服务实例（如果为 None，自动创建）
        """
        self.memory_service = memory_service or MemoryService()
        self.graph = get_knowledge_graph()
    
    def remember(self, content: str, memory_type: str = "fact", **kwargs) -> str:
        """
        记录记忆（自动提取实体和关系）
        
        参数：
            content: 记忆内容
            memory_type: 记忆类型
            **kwargs: 其他参数
        
        返回：
            记忆 ID
        """
        # 1. 存储到记忆服务
        memory_id = self.memory_service.remember(content, memory_type, **kwargs)
        
        # 2. 提取实体和关系
        entities, relations = self.graph.extract_from_text(content)
        
        # 3. 关联记忆 ID
        if entities:
            print(f"  📊 提取 {len(entities)} 个实体, {len(relations)} 条关系")
        
        return memory_id
    
    def recall(self, query: str, limit: int = 10, include_graph_context: bool = True, **kwargs) -> List[dict]:
        """
        检索记忆（结合图谱上下文）
        
        参数：
            query: 查询文本
            limit: 最大返回数量
            include_graph_context: 是否包含图谱上下文
            **kwargs: 其他参数
        
        返回：
            记忆列表
        """
        # 1. 检索相关记忆
        memories = self.memory_service.recall(query, limit=limit, **kwargs)
        
        # 2. 提取查询中的实体
        query_entities, _ = self.graph.extract_from_text(query)
        
        if include_graph_context and query_entities:
            # 3. 获取相关实体的图谱上下文
            graph_context = []
            
            for entity in query_entities[:3]:  # 最多取前 3 个实体
                # 获取邻居
                neighbors = self.graph.get_neighbors(entity.name, depth=2)
                
                for neighbor in neighbors[:5]:  # 每个实体最多 5 个邻居
                    graph_context.append({
                        "entity": neighbor.name,
                        "type": neighbor.type.value,
                        "source": entity.name,
                        "context": "graph"
                    })
            
            # 4. 添加图谱上下文到结果
            if graph_context:
                memories.append({
                    "content": f"[图谱上下文] 相关实体: {', '.join([ctx['entity'] for ctx in graph_context[:10]])}",
                    "type": "graph_context",
                    "score": 0.5,
                    "entities": graph_context
                })
        
        return memories
    
    def get_entity_memories(self, entity_name: str, limit: int = 10) -> List[dict]:
        """
        获取与实体相关的所有记忆
        
        参数：
            entity_name: 实体名称
            limit: 最大返回数量
        
        返回：
            记忆列表
        """
        # 使用实体名称作为查询
        return self.memory_service.recall(entity_name, limit=limit)
    
    def get_entity_graph(self, entity_name: str, depth: int = 2) -> dict:
        """
        获取实体的图谱子图
        
        参数：
            entity_name: 实体名称
            depth: 搜索深度
        
        返回：
            子图信息
        """
        entity = self.graph.get_entity(entity_name)
        if not entity:
            return {"error": f"实体 '{entity_name}' 不存在"}
        
        # 获取邻居
        neighbors = self.graph.get_neighbors(entity_name, depth=depth)
        
        # 获取相关关系
        relations = []
        for neighbor in neighbors:
            # 查找实体和邻居之间的关系
            for relation in self.graph.relation_index.get(entity.id, []):
                if relation.source_id == neighbor.id or relation.target_id == neighbor.id:
                    relations.append({
                        "source": self.graph.entities[relation.source_id].name,
                        "target": self.graph.entities[relation.target_id].name,
                        "type": relation.type.value
                    })
        
        return {
            "entity": {
                "name": entity.name,
                "type": entity.type.value,
                "attributes": entity.attributes
            },
            "neighbors": [
                {
                    "name": n.name,
                    "type": n.type.value
                }
                for n in neighbors
            ],
            "relations": relations
        }
    
    def stats(self) -> dict:
        """获取统计信息"""
        memory_stats = self.memory_service.stats()
        graph_stats = self.graph.stats()
        
        return {
            "memory": memory_stats,
            "graph": graph_stats,
            "enhanced": True
        }
    
    def visualize_entity_network(self, entity_name: str, output_file: str = None) -> str:
        """
        可视化实体网络
        
        参数：
            entity_name: 中心实体名称
            output_file: 输出文件路径（可选）
        
        返回：
            Mermaid 图表代码
        """
        entity = self.graph.get_entity(entity_name)
        if not entity:
            return f"错误: 实体 '{entity_name}' 不存在"
        
        # 获取 2 层邻居
        neighbors = self.graph.get_neighbors(entity_name, depth=2)
        
        # 生成 Mermaid 代码
        lines = ["graph TD"]
        
        # 中心节点
        lines.append(f'    {entity.id}["{entity.name}\\n({entity.type.value})"]')
        lines.append(f'    style {entity.id} fill:#f9f,stroke:#333,stroke-width:4px')
        
        # 添加邻居节点和边
        for neighbor in neighbors:
            label = f"{neighbor.name}\\n({neighbor.type.value})"
            lines.append(f'    {neighbor.id}["{label}"]')
        
        # 添加关系边
        for relation in self.graph.relations:
            if relation.source_id in [entity.id] + [n.id for n in neighbors]:
                if relation.target_id in [entity.id] + [n.id for n in neighbors]:
                    source = self.graph.entities[relation.source_id]
                    target = self.graph.entities[relation.target_id]
                    label = relation.type.value
                    lines.append(f'    {source.id} -->|{label}| {target.id}')
        
        mermaid_code = "\n".join(lines)
        
        if output_file:
            Path(output_file).write_text(mermaid_code)
            print(f"✅ 图表已导出到: {output_file}")
        
        return mermaid_code


# 便捷函数
_enhanced_memory = None

def get_enhanced_memory() -> EnhancedMemoryWithGraph:
    """获取全局增强记忆服务实例"""
    global _enhanced_memory
    
    if _enhanced_memory is None:
        _enhanced_memory = EnhancedMemoryWithGraph()
    
    return _enhanced_memory


if __name__ == "__main__":
    # 测试
    print("🧪 测试知识图谱增强记忆服务\n")
    print("=" * 60)
    
    # 创建增强记忆服务
    enhanced = EnhancedMemoryWithGraph()
    
    # 记录记忆（自动提取实体）
    print("\n1️⃣ 记录记忆...")
    memory_id = enhanced.remember("远见喜欢英雄联盟，阿卡丽是他的助手", "fact")
    print(f"  ✅ 记忆 ID: {memory_id}")
    
    # 检索记忆（带图谱上下文）
    print("\n2️⃣ 检索记忆...")
    results = enhanced.recall("远见", limit=5, include_graph_context=True)
    print(f"  找到 {len(results)} 条结果:")
    for i, result in enumerate(results, 1):
        content = result.get('content', '')
        print(f"    {i}. {content[:60]}...")
    
    # 获取实体的图谱
    print("\n3️⃣ 获取实体图谱...")
    graph = enhanced.get_entity_graph("远见")
    print(f"  实体: {graph.get('entity', {}).get('name')}")
    print(f"  邻居数: {len(graph.get('neighbors', []))}")
    print(f"  关系数: {len(graph.get('relations', []))}")
    
    # 统计
    print("\n4️⃣ 统计信息...")
    stats = enhanced.stats()
    print(f"  记忆数: {stats['memory'].get('count', 0)}")
    print(f"  实体数: {stats['graph']['entity_count']}")
    print(f"  关系数: {stats['graph']['relation_count']}")
    
    # 可视化
    print("\n5️⃣ 生成实体网络图...")
    mermaid = enhanced.visualize_entity_network("远见")
    print(mermaid)
    
    print("\n" + "=" * 60)
    print("✅ 测试完成！")
