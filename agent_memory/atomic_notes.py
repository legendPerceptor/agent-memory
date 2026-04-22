#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Zettelkasten 原子笔记系统

核心概念：
1. 原子性（Atomicity）- 每条笔记只包含一个概念
2. 自包含（Self-contained）- 独立可理解
3. 灵活链接（Flexible Linking）- 通过关键词自动关联

灵感来源：A-MEM (arXiv:2502.12110) - Zettelkasten method
"""

import re
import uuid
import hashlib
from datetime import datetime
from typing import List, Dict, Optional, Set
from dataclasses import dataclass, asdict
import json

from .memory_service import MemoryService
from .hybrid_rag import HybridRAG


@dataclass
class AtomicNote:
    """
    原子笔记
    
    遵循 Zettelkasten 原则：
    - 原子性：一个笔记 = 一个概念
    - 自包含：独立可理解
    - 可链接：通过关键词关联
    """
    
    id: str  # 唯一 ID
    content: str  # 笔记内容（< 200 字符）
    links: List[str]  # 关联的其他笔记 ID
    tags: List[str]  # 标签
    confidence: float  # 置信度（0.0-1.0）
    source: str  # 来源（对话 ID / 文档 ID）
    created_at: str  # 创建时间
    last_accessed: str  # 最后访问时间
    access_count: int  # 访问次数
    
    # 额外字段
    keywords: List[str]  # 关键词（用于自动链接）
    note_type: str  # fact | event | preference | decision | procedure
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'AtomicNote':
        """从字典创建"""
        return cls(**data)


class ZettelkastenMemory:
    """
    Zettelkasten 记忆系统
    
    核心功能：
    1. 将长内容分解为原子笔记
    2. 自动提取关键词并建立链接
    3. 动态演化知识结构
    """
    
    def __init__(self, memory_service: MemoryService = None):
        self.memory = memory_service or MemoryService()
        self.rag = HybridRAG(self.memory)
        
        # 原子笔记最大长度（字符）
        self.max_note_length = 200
        
        # 最小链接关键词数
        self.min_link_keywords = 2
        
        # 置信度阈值
        self.confidence_threshold = 0.6
    
    def create_atomic_note(
        self,
        content: str,
        note_type: str = "fact",
        source: str = "",
        confidence: float = 0.7,
        tags: List[str] = None
    ) -> AtomicNote:
        """
        创建原子笔记
        
        Args:
            content: 笔记内容
            note_type: 笔记类型
            source: 来源
            confidence: 置信度
            tags: 标签
        
        Returns:
            原子笔记对象
        """
        # 生成 ID
        note_id = str(uuid.uuid4())[:12]
        
        # 提取关键词
        keywords = list(self.rag.extract_keywords(content))
        
        # 时间戳
        now = datetime.now().isoformat()
        
        # 创建笔记
        note = AtomicNote(
            id=note_id,
            content=content[:self.max_note_length],  # 截断
            links=[],  # 稍后填充
            tags=tags or [],
            confidence=confidence,
            source=source,
            created_at=now,
            last_accessed=now,
            access_count=0,
            keywords=keywords,
            note_type=note_type
        )
        
        return note
    
    def auto_link(self, note: AtomicNote, existing_notes: List[AtomicNote]) -> AtomicNote:
        """
        自动链接笔记
        
        基于关键词匹配建立关联
        
        Args:
            note: 新笔记
            existing_notes: 现有笔记列表
        
        Returns:
            更新后的笔记（包含链接）
        """
        note_keywords = set(note.keywords)
        
        # 计算与现有笔记的相似度
        similar_notes = []
        
        for existing in existing_notes:
            existing_keywords = set(existing.keywords)
            
            # 关键词交集
            common = note_keywords & existing_keywords
            
            if len(common) >= self.min_link_keywords:
                # 计算相似度
                similarity = len(common) / max(len(note_keywords | existing_keywords), 1)
                similar_notes.append((existing.id, similarity, len(common)))
        
        # 排序并选择 Top-5
        similar_notes.sort(key=lambda x: x[1], reverse=True)
        note.links = [nid for nid, _, _ in similar_notes[:5]]
        
        return note
    
    def decompose_content(
        self,
        long_content: str,
        note_type: str = "fact",
        source: str = "",
        confidence: float = 0.7,
        tags: List[str] = None
    ) -> List[AtomicNote]:
        """
        将长内容分解为多个原子笔记
        
        Args:
            long_content: 长文本
            note_type: 笔记类型
            source: 来源
            confidence: 置信度
            tags: 标签
        
        Returns:
            原子笔记列表
        """
        # 简单分割策略：按句子分割
        # 可替换为更复杂的 NLP 方法
        
        # 按句号、问号、感叹号分割
        sentences = re.split(r'[。！？.!?]', long_content)
        
        # 过滤空句子
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # 合并短句（< 20 字符）
        merged_sentences = []
        current = ""
        
        for sentence in sentences:
            if len(current) + len(sentence) < self.max_note_length:
                current += sentence + "。"
            else:
                if current:
                    merged_sentences.append(current.strip())
                current = sentence + "。"
        
        if current:
            merged_sentences.append(current.strip())
        
        # 创建原子笔记
        notes = []
        for sentence in merged_sentences:
            if len(sentence) >= 10:  # 忽略太短的句子
                note = self.create_atomic_note(
                    content=sentence,
                    note_type=note_type,
                    source=source,
                    confidence=confidence,
                    tags=tags
                )
                notes.append(note)
        
        print(f"📝 分解为 {len(notes)} 个原子笔记")
        return notes
    
    def remember_atomic(
        self,
        content: str,
        note_type: str = "fact",
        source: str = "",
        confidence: float = 0.7,
        tags: List[str] = None,
        auto_decompose: bool = True
    ) -> List[str]:
        """
        存储原子笔记
        
        Args:
            content: 内容
            note_type: 笔记类型
            source: 来源
            confidence: 置信度
            tags: 标签
            auto_decompose: 是否自动分解长内容
        
        Returns:
            笔记 ID 列表
        """
        # 决定是否分解
        if auto_decompose and len(content) > self.max_note_length:
            notes = self.decompose_content(
                content, note_type, source, confidence, tags
            )
        else:
            notes = [
                self.create_atomic_note(
                    content, note_type, source, confidence, tags
                )
            ]
        
        # 获取现有笔记（用于自动链接）
        # 这里简化处理：从 Qdrant 获取最近 100 条笔记
        # 实际应用中可以使用更高效的索引
        existing_notes = []
        # TODO: 从 Qdrant 加载现有笔记
        
        # 自动链接
        for note in notes:
            note = self.auto_link(note, existing_notes)
        
        # 存储到 Qdrant
        note_ids = []
        for note in notes:
            # 存储为记忆
            memory_id = self.memory.remember(
                content=json.dumps(note.to_dict(), ensure_ascii=False),
                memory_type=f"atomic_{note.note_type}",
                importance=note.confidence,
                tags=note.tags + note.keywords
            )
            note_ids.append(memory_id)
        
        print(f"✅ 存储了 {len(note_ids)} 个原子笔记")
        return note_ids
    
    def recall_atomic(
        self,
        query: str,
        limit: int = 10,
        min_confidence: float = 0.6
    ) -> List[AtomicNote]:
        """
        检索原子笔记
        
        Args:
            query: 查询文本
            limit: 返回数量
            min_confidence: 最小置信度
        
        Returns:
            原子笔记列表
        """
        # 使用 Hybrid RAG 检索
        results = self.rag.hybrid_recall(query, limit=limit * 2)
        
        # 解析为原子笔记
        notes = []
        for result in results:
            try:
                note_data = json.loads(result["content"])
                note = AtomicNote.from_dict(note_data)
                
                # 置信度过滤
                if note.confidence >= min_confidence:
                    # 更新访问统计
                    note.last_accessed = datetime.now().isoformat()
                    note.access_count += 1
                    
                    # 添加分数
                    note_copy = note.to_dict()
                    note_copy["hybrid_score"] = result.get("hybrid_score", 0)
                    note_copy["score_breakdown"] = result.get("score_breakdown", {})
                    
                    notes.append(note)
            except:
                # 可能是非原子笔记格式的记忆
                continue
        
        # 返回 Top-K
        return notes[:limit]
    
    def get_linked_notes(self, note_id: str, depth: int = 1) -> List[AtomicNote]:
        """
        获取链接的笔记（multi-hop 检索）
        
        Args:
            note_id: 起始笔记 ID
            depth: 深度（1 = 直接链接，2 = 间接链接）
        
        Returns:
            链接的笔记列表
        """
        # TODO: 实现图遍历
        # 当前简化实现：只返回直接链接
        pass
    
    def stats(self) -> Dict:
        """统计信息"""
        base_stats = self.memory.stats()
        return {
            **base_stats,
            "zettelkasten": {
                "max_note_length": self.max_note_length,
                "min_link_keywords": self.min_link_keywords,
                "confidence_threshold": self.confidence_threshold
            }
        }


def main():
    """测试 Zettelkasten 系统"""
    print("=" * 60)
    print("Zettelkasten 原子笔记系统 - 测试")
    print("=" * 60)
    print()
    
    # 初始化
    zk = ZettelkastenMemory()
    print()
    
    # 统计
    stats = zk.stats()
    print(f"📊 系统状态:")
    print(f"  - 存储类型: {stats.get('storage')}")
    print(f"  - 最大笔记长度: {stats['zettelkasten']['max_note_length']}")
    print(f"  - 最小链接关键词: {stats['zettelkasten']['min_link_keywords']}")
    print()
    
    # 测试原子笔记创建
    print("📝 测试原子笔记创建...")
    
    # 短内容
    note_ids = zk.remember_atomic(
        content="用户偏好简洁回复",
        note_type="preference",
        confidence=0.8,
        auto_decompose=False
    )
    print(f"  短笔记 ID: {note_ids}")
    
    # 长内容（自动分解）
    long_content = """
    用户购买了一个新的 MiniMax Token Plan。这个计划包含 1000 万 tokens，
    年费 490 元。计划在 2026-04-01 激活，有效期 12 个月。
    MiniMax 的 API 支持多种模型，包括 Minimax-M2.7 和 Minimax-M2.5。
    """
    
    note_ids = zk.remember_atomic(
        content=long_content,
        note_type="event",
        confidence=0.9,
        auto_decompose=True
    )
    print(f"  长笔记分解为 {len(note_ids)} 个原子笔记: {note_ids}")
    print()
    
    # 测试检索
    print("🔍 测试原子笔记检索...")
    query = "MiniMax API 配置"
    notes = zk.recall_atomic(query, limit=3)
    
    for i, note in enumerate(notes, 1):
        print(f"\n  {i}. ID: {note.id}")
        print(f"     类型: {note.note_type}")
        print(f"     内容: {note.content[:60]}...")
        print(f"     关键词: {note.keywords}")
        print(f"     链接: {len(note.links)} 个")
        print(f"     置信度: {note.confidence}")
    
    print()
    print("✅ 测试完成")


if __name__ == "__main__":
    main()
