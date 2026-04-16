#!/usr/bin/env python3
"""
知识图谱记忆系统

功能：
1. 实体提取（人物、地点、事件、概念）
2. 关系提取（谁-做了什么-对谁）
3. 图谱存储（节点 + 边）
4. 图谱查询（路径查找、邻居查询）
5. 与向量记忆集成

架构：
- 实体类型：PERSON, LOCATION, EVENT, CONCEPT, ORGANIZATION, OBJECT
- 关系类型：KNOWS, WORKS_WITH, LOCATED_AT, PARTICIPATES_IN, RELATED_TO, CREATED_BY
- 存储：内存字典 + JSON 持久化
- 索引：实体索引、关系索引、类型索引
"""

import json
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Set, Tuple
from collections import defaultdict
from enum import Enum
import uuid

from .config import GRAPH_DIR

# 配置
GRAPH_FILE = GRAPH_DIR / "graph.json"

# 实体类型
class EntityType(Enum):
    PERSON = "person"
    LOCATION = "location"
    EVENT = "event"
    CONCEPT = "concept"
    ORGANIZATION = "organization"
    OBJECT = "object"
    
    @classmethod
    def from_string(cls, s: str) -> 'EntityType':
        """从字符串转换"""
        mapping = {
            "人物": cls.PERSON,
            "人": cls.PERSON,
            "地点": cls.LOCATION,
            "位置": cls.LOCATION,
            "事件": cls.EVENT,
            "概念": cls.CONCEPT,
            "组织": cls.ORGANIZATION,
            "公司": cls.ORGANIZATION,
            "对象": cls.OBJECT,
            "物品": cls.OBJECT,
        }
        return mapping.get(s.lower(), cls.CONCEPT)


# 关系类型
class RelationType(Enum):
    KNOWS = "knows"                    # 知道/认识
    WORKS_WITH = "works_with"          # 一起工作
    LOCATED_AT = "located_at"          # 位于
    PARTICIPATES_IN = "participates_in" # 参与
    RELATED_TO = "related_to"          # 相关
    CREATED_BY = "created_by"          # 创建者
    PARENT_OF = "parent_of"            # 父子关系
    MEMBER_OF = "member_of"            # 成员
    OWNS = "owns"                      # 拥有
    USES = "uses"                      # 使用
    
    @classmethod
    def from_string(cls, s: str) -> 'RelationType':
        """从字符串转换"""
        mapping = {
            "认识": cls.KNOWS,
            "知道": cls.KNOWS,
            "一起工作": cls.WORKS_WITH,
            "合作": cls.WORKS_WITH,
            "位于": cls.LOCATED_AT,
            "在": cls.LOCATED_AT,
            "参与": cls.PARTICIPATES_IN,
            "参加": cls.PARTICIPATES_IN,
            "相关": cls.RELATED_TO,
            "创建": cls.CREATED_BY,
            "建立": cls.CREATED_BY,
            "成员": cls.MEMBER_OF,
            "拥有": cls.OWNS,
            "使用": cls.USES,
        }
        return mapping.get(s.lower(), cls.RELATED_TO)


class Entity:
    """实体（节点）"""
    
    def __init__(self, name: str, entity_type: EntityType, **kwargs):
        """
        初始化实体
        
        参数：
            name: 实体名称
            entity_type: 实体类型
            **kwargs: 额外属性
        """
        self.id = str(uuid.uuid4())[:8]
        self.name = name
        self.type = entity_type
        self.attributes = kwargs
        self.created_at = datetime.now().isoformat()
        self.updated_at = self.created_at
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type.value,
            "attributes": self.attributes,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Entity':
        """从字典创建"""
        entity = cls(
            name=data["name"],
            entity_type=EntityType(data["type"]),
            **data.get("attributes", {})
        )
        entity.id = data["id"]
        entity.created_at = data.get("created_at", entity.created_at)
        entity.updated_at = data.get("updated_at", entity.updated_at)
        return entity
    
    def __repr__(self):
        return f"Entity({self.name}, {self.type.value})"


class Relation:
    """关系（边）"""
    
    def __init__(self, source_id: str, target_id: str, relation_type: RelationType, **kwargs):
        """
        初始化关系
        
        参数：
            source_id: 源实体 ID
            target_id: 目标实体 ID
            relation_type: 关系类型
            **kwargs: 额外属性
        """
        self.id = str(uuid.uuid4())[:8]
        self.source_id = source_id
        self.target_id = target_id
        self.type = relation_type
        self.attributes = kwargs
        self.created_at = datetime.now().isoformat()
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "type": self.type.value,
            "attributes": self.attributes,
            "created_at": self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Relation':
        """从字典创建"""
        relation = cls(
            source_id=data["source_id"],
            target_id=data["target_id"],
            relation_type=RelationType(data["type"]),
            **data.get("attributes", {})
        )
        relation.id = data["id"]
        relation.created_at = data.get("created_at", relation.created_at)
        return relation
    
    def __repr__(self):
        return f"Relation({self.source_id} -{self.type.value}-> {self.target_id})"


class KnowledgeGraph:
    """知识图谱"""
    
    def __init__(self):
        """初始化知识图谱"""
        # 存储
        self.entities: Dict[str, Entity] = {}
        self.relations: List[Relation] = []
        
        # 索引
        self.entity_name_index: Dict[str, str] = {}  # name -> entity_id
        self.entity_type_index: Dict[EntityType, Set[str]] = defaultdict(set)  # type -> entity_ids
        self.relation_index: Dict[str, List[Relation]] = defaultdict(list)  # entity_id -> relations
        
        # 加载持久化数据
        self._load()
    
    def add_entity(self, name: str, entity_type: EntityType, **kwargs) -> Entity:
        """
        添加实体
        
        参数：
            name: 实体名称
            entity_type: 实体类型
            **kwargs: 额外属性
        
        返回：
            Entity 实例
        """
        # 检查是否已存在
        if name in self.entity_name_index:
            entity_id = self.entity_name_index[name]
            entity = self.entities[entity_id]
            entity.updated_at = datetime.now().isoformat()
            entity.attributes.update(kwargs)
            return entity
        
        # 创建新实体
        entity = Entity(name, entity_type, **kwargs)
        
        # 添加到存储
        self.entities[entity.id] = entity
        
        # 更新索引
        self.entity_name_index[name] = entity.id
        self.entity_type_index[entity_type].add(entity.id)
        
        # 持久化
        self._save()
        
        return entity
    
    def add_relation(self, source_name: str, target_name: str, relation_type: RelationType, **kwargs) -> Optional[Relation]:
        """
        添加关系
        
        参数：
            source_name: 源实体名称
            target_name: 目标实体名称
            relation_type: 关系类型
            **kwargs: 额外属性
        
        返回：
            Relation 实例或 None（如果实体不存在）
        """
        # 查找实体
        source_id = self.entity_name_index.get(source_name)
        target_id = self.entity_name_index.get(target_name)
        
        if not source_id or not target_id:
            print(f"⚠️ 实体不存在: {source_name} 或 {target_name}")
            return None
        
        # 检查关系是否已存在
        for relation in self.relation_index[source_id]:
            if relation.target_id == target_id and relation.type == relation_type:
                return relation
        
        # 创建新关系
        relation = Relation(source_id, target_id, relation_type, **kwargs)
        
        # 添加到存储
        self.relations.append(relation)
        
        # 更新索引
        self.relation_index[source_id].append(relation)
        self.relation_index[target_id].append(relation)
        
        # 持久化
        self._save()
        
        return relation
    
    def get_entity(self, name: str) -> Optional[Entity]:
        """获取实体"""
        entity_id = self.entity_name_index.get(name)
        return self.entities.get(entity_id) if entity_id else None
    
    def get_neighbors(self, entity_name: str, relation_type: RelationType = None, depth: int = 1) -> List[Entity]:
        """
        获取邻居实体
        
        参数：
            entity_name: 实体名称
            relation_type: 关系类型过滤（可选）
            depth: 搜索深度（1=直接邻居）
        
        返回：
            邻居实体列表
        """
        entity = self.get_entity(entity_name)
        if not entity:
            return []
        
        neighbors = []
        visited = {entity.id}
        
        # BFS 搜索
        queue = [(entity.id, 0)]
        
        while queue:
            current_id, current_depth = queue.pop(0)
            
            if current_depth >= depth:
                continue
            
            for relation in self.relation_index[current_id]:
                # 过滤关系类型
                if relation_type and relation.type != relation_type:
                    continue
                
                # 找到邻居
                neighbor_id = relation.target_id if relation.source_id == current_id else relation.source_id
                
                if neighbor_id not in visited:
                    visited.add(neighbor_id)
                    neighbor = self.entities.get(neighbor_id)
                    if neighbor:
                        neighbors.append(neighbor)
                        queue.append((neighbor_id, current_depth + 1))
        
        return neighbors
    
    def find_path(self, source_name: str, target_name: str, max_depth: int = 5) -> List[Tuple[Entity, Relation]]:
        """
        查找路径（BFS）
        
        参数：
            source_name: 起始实体名称
            target_name: 目标实体名称
            max_depth: 最大搜索深度
        
        返回：
            路径列表 [(entity, relation), ...]
        """
        source = self.get_entity(source_name)
        target = self.get_entity(target_name)
        
        if not source or not target:
            return []
        
        # BFS
        visited = {source.id}
        queue = [(source.id, [])]
        
        while queue:
            current_id, path = queue.pop(0)
            
            if len(path) > max_depth:
                continue
            
            # 找到目标
            if current_id == target.id:
                return path
            
            # 遍历邻居
            for relation in self.relation_index[current_id]:
                neighbor_id = relation.target_id if relation.source_id == current_id else relation.source_id
                
                if neighbor_id not in visited:
                    visited.add(neighbor_id)
                    neighbor = self.entities.get(neighbor_id)
                    if neighbor:
                        new_path = path + [(neighbor, relation)]
                        queue.append((neighbor_id, new_path))
        
        return []
    
    def extract_from_text(self, text: str) -> Tuple[List[Entity], List[Relation]]:
        """
        从文本中提取实体和关系（规则引擎）
        
        参数：
            text: 文本内容
        
        返回：
            (实体列表, 关系列表)
        """
        entities = []
        relations = []
        
        # 规则 1: "X 喜欢 Y" -> PERSON RELATED_TO CONCEPT/OBJECT
        match = re.search(r"(\w+)\s*喜欢\s*(\w+)", text)
        if match:
            person_name, target_name = match.groups()
            entities.append(self.add_entity(person_name, EntityType.PERSON))
            
            # 判断目标类型
            if "游戏" in target_name or "英雄" in target_name:
                target = self.add_entity(target_name, EntityType.CONCEPT)
            else:
                target = self.add_entity(target_name, EntityType.CONCEPT)
            
            entities.append(target)
            relations.append(self.add_relation(person_name, target_name, RelationType.RELATED_TO))
        
        # 规则 2: "X 创建了 Y" -> PERSON CREATED_BY OBJECT/CONCEPT
        match = re.search(r"(\w+)\s*创建\s*[了]?\s*(\w+)", text)
        if match:
            person_name, target_name = match.groups()
            entities.append(self.add_entity(person_name, EntityType.PERSON))
            target = self.add_entity(target_name, EntityType.CONCEPT)
            entities.append(target)
            relations.append(self.add_relation(person_name, target_name, RelationType.CREATED_BY))
        
        # 规则 3: "X 在 Y" -> PERSON/ORG LOCATED_AT LOCATION
        match = re.search(r"(\w+)\s*在\s*(\w+)", text)
        if match:
            subject_name, location_name = match.groups()
            # 判断主体类型
            if any(org in subject_name for org in ["公司", "团队", "组织"]):
                subject = self.add_entity(subject_name, EntityType.ORGANIZATION)
            else:
                subject = self.add_entity(subject_name, EntityType.PERSON)
            
            location = self.add_entity(location_name, EntityType.LOCATION)
            entities.extend([subject, location])
            relations.append(self.add_relation(subject_name, location_name, RelationType.LOCATED_AT))
        
        # 规则 4: 提取人物名字（简单规则：大写字母开头或中文人名）
        # 中文名字模式（2-3个字）
        chinese_names = re.findall(r"[\u4e00-\u9fa5]{2,3}", text)
        for name in chinese_names:
            if len(name) >= 2 and name not in ["喜欢", "创建", "位于", "在", "使用", "拥有"]:
                entity = self.add_entity(name, EntityType.PERSON)
                if entity not in entities:
                    entities.append(entity)
        
        return entities, relations
    
    def stats(self) -> dict:
        """获取统计信息"""
        return {
            "entity_count": len(self.entities),
            "relation_count": len(self.relations),
            "entity_types": {t.value: len(ids) for t, ids in self.entity_type_index.items()},
            "relation_types": self._count_relation_types()
        }
    
    def _count_relation_types(self) -> dict:
        """统计关系类型"""
        counts = defaultdict(int)
        for relation in self.relations:
            counts[relation.type.value] += 1
        return dict(counts)
    
    def _save(self):
        """持久化到文件"""
        GRAPH_DIR.mkdir(parents=True, exist_ok=True)
        
        data = {
            "entities": [e.to_dict() for e in self.entities.values()],
            "relations": [r.to_dict() for r in self.relations],
            "updated_at": datetime.now().isoformat()
        }
        
        GRAPH_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    
    def _load(self):
        """从文件加载"""
        if not GRAPH_FILE.exists():
            return
        
        try:
            data = json.loads(GRAPH_FILE.read_text())
            
            # 加载实体
            for entity_data in data.get("entities", []):
                entity = Entity.from_dict(entity_data)
                self.entities[entity.id] = entity
                self.entity_name_index[entity.name] = entity.id
                self.entity_type_index[entity.type].add(entity.id)
            
            # 加载关系
            for relation_data in data.get("relations", []):
                relation = Relation.from_dict(relation_data)
                self.relations.append(relation)
                self.relation_index[relation.source_id].append(relation)
                self.relation_index[relation.target_id].append(relation)
            
            print(f"✅ 知识图谱已加载: {len(self.entities)} 个实体, {len(self.relations)} 条关系")
        
        except Exception as e:
            print(f"⚠️ 加载知识图谱失败: {e}")
    
    def clear(self):
        """清空图谱"""
        self.entities.clear()
        self.relations.clear()
        self.entity_name_index.clear()
        self.entity_type_index.clear()
        self.relation_index.clear()
        self._save()
    
    def visualize(self, output_file: str = None):
        """
        可视化图谱（生成 Mermaid 图表）
        
        参数：
            output_file: 输出文件路径（可选）
        """
        lines = ["graph TD"]
        
        # 添加实体节点
        for entity in self.entities.values():
            label = f"{entity.name}\\n({entity.type.value})"
            lines.append(f'    {entity.id}["{label}"]')
        
        # 添加关系边
        for relation in self.relations:
            source = self.entities[relation.source_id]
            target = self.entities[relation.target_id]
            label = relation.type.value
            lines.append(f'    {source.id} -->|{label}| {target.id}')
        
        mermaid_code = "\n".join(lines)
        
        if output_file:
            Path(output_file).write_text(mermaid_code)
            print(f"✅ 图谱已导出到: {output_file}")
        
        return mermaid_code


# 便捷函数
_knowledge_graph = None

def get_knowledge_graph() -> KnowledgeGraph:
    """获取全局知识图谱实例"""
    global _knowledge_graph
    
    if _knowledge_graph is None:
        _knowledge_graph = KnowledgeGraph()
    
    return _knowledge_graph


if __name__ == "__main__":
    # 测试
    print("🧪 测试知识图谱系统\n")
    print("=" * 60)
    
    # 创建图谱
    graph = KnowledgeGraph()
    
    # 添加实体
    print("\n1️⃣ 添加实体...")
    person = graph.add_entity("远见", EntityType.PERSON, role="用户")
    game = graph.add_entity("英雄联盟", EntityType.CONCEPT, type="游戏")
    assistant = graph.add_entity("阿卡丽", EntityType.PERSON, role="助手")
    
    print(f"  ✅ 实体: {person}")
    print(f"  ✅ 实体: {game}")
    print(f"  ✅ 实体: {assistant}")
    
    # 添加关系
    print("\n2️⃣ 添加关系...")
    relation1 = graph.add_relation("远见", "英雄联盟", RelationType.RELATED_TO)
    relation2 = graph.add_relation("远见", "阿卡丽", RelationType.KNOWS)
    
    print(f"  ✅ 关系: {relation1}")
    print(f"  ✅ 关系: {relation2}")
    
    # 查询邻居
    print("\n3️⃣ 查询远见的邻居...")
    neighbors = graph.get_neighbors("远见")
    for neighbor in neighbors:
        print(f"  - {neighbor.name} ({neighbor.type.value})")
    
    # 查找路径
    print("\n4️⃣ 查找路径: 英雄联盟 -> 阿卡丽...")
    path = graph.find_path("英雄联盟", "阿卡丽")
    if path:
        print("  路径:")
        for entity, relation in path:
            print(f"    - {entity.name} (via {relation.type.value})")
    else:
        print("  未找到路径")
    
    # 从文本提取
    print("\n5️⃣ 从文本提取...")
    text = "远见喜欢英雄联盟，阿卡丽是他的助手"
    entities, relations = graph.extract_from_text(text)
    print(f"  提取实体: {len(entities)} 个")
    print(f"  提取关系: {len(relations)} 条")
    
    # 统计
    print("\n6️⃣ 图谱统计...")
    stats = graph.stats()
    print(f"  实体数: {stats['entity_count']}")
    print(f"  关系数: {stats['relation_count']}")
    print(f"  实体类型: {stats['entity_types']}")
    print(f"  关系类型: {stats['relation_types']}")
    
    # 可视化
    print("\n7️⃣ 生成 Mermaid 图表...")
    mermaid = graph.visualize()
    print(mermaid)
    
    print("\n" + "=" * 60)
    print("✅ 测试完成！")
