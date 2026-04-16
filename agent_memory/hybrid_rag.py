#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hybrid RAG 检索系统

结合：
1. 向量相似度搜索（Semantic Search）
2. 时间有效性过滤（Temporal Filtering）
3. 关键词匹配增强（Keyword Boosting）

灵感来源：Tiger Data (2026-01) - "Building AI Agents with Persistent Memory"
"""

import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Set
import math
import string

from .memory_service import MemoryService


class HybridRAG:
    """
    混合检索系统
    
    核心思想：
    - 向量搜索找语义相关的记忆
    - 时间过滤排除过时信息
    - 关键词 boost 提升精确度
    """
    
    def __init__(self, memory_service: MemoryService = None):
        self.memory = memory_service or MemoryService()
        
        # 时间衰减参数
        self.decay_rate = 0.1  # 衰减速度
        self.half_life_days = 30  # 半衰期：30 天
        
        # 关键词权重
        self.keyword_boost_factor = 1.5  # 每个匹配关键词的 boost
        
        # 停用词（简单版）
        self.stopwords = {
            "的", "是", "在", "有", "和", "了", "我", "你", "他", "她",
            "这", "那", "就", "也", "都", "会", "能", "要", "对", "与",
            "the", "a", "an", "is", "are", "was", "were", "be", "been",
            "being", "have", "has", "had", "do", "does", "did", "will",
            "would", "could", "should", "may", "might", "must", "shall",
            "can", "need", "dare", "ought", "used", "to", "of", "in",
            "for", "on", "with", "at", "by", "from", "as", "into", "through"
        }
    
    def extract_keywords(self, text: str) -> Set[str]:
        """
        提取关键词
        
        简单实现：移除停用词 + 标点符号
        可替换为更复杂的 NLP 方法
        """
        # 转小写
        text = text.lower()
        
        # 移除标点符号
        text = text.translate(str.maketrans('', '', string.punctuation))
        
        # 分词（简单空格分词）
        words = text.split()
        
        # 过滤停用词和短词
        keywords = {
            word for word in words
            if word not in self.stopwords and len(word) > 2
        }
        
        return keywords
    
    def temporal_decay(self, created_at: str, current_time: datetime = None) -> float:
        """
        计算时间衰减因子
        
        使用指数衰减模型：
        decay = exp(-decay_rate * age_in_days)
        
        Args:
            created_at: ISO 8601 时间字符串
            current_time: 当前时间（默认为 now）
        
        Returns:
            衰减因子（0.0-1.0）
        """
        if current_time is None:
            current_time = datetime.now()
        
        try:
            memory_time = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            if memory_time.tzinfo is None:
                memory_time = memory_time.replace(tzinfo=None)
            
            age = current_time - memory_time
            age_days = age.total_seconds() / 86400  # 转换为天数
            
            # 指数衰减
            decay = math.exp(-self.decay_rate * age_days)
            
            return decay
        except:
            return 1.0  # 解析失败，不衰减
    
    def is_temporally_valid(
        self,
        memory: Dict,
        current_time: datetime = None,
        validity_threshold: float = 0.3
    ) -> bool:
        """
        检查记忆是否在时间上有效
        
        Args:
            memory: 记忆对象
            current_time: 当前时间
            validity_threshold: 有效性阈值（0.0-1.0）
        
        Returns:
            是否有效
        """
        created_at = memory.get("created_at")
        if not created_at:
            return True  # 没有时间戳，默认有效
        
        decay = self.temporal_decay(created_at, current_time)
        return decay >= validity_threshold
    
    def keyword_boost(self, memory: Dict, query_keywords: Set[str]) -> float:
        """
        计算关键词 boost
        
        Args:
            memory: 记忆对象
            query_keywords: 查询关键词集合
        
        Returns:
            boost 因子（>= 1.0）
        """
        # 提取记忆关键词
        memory_keywords = self.extract_keywords(memory.get("content", ""))
        
        # 计算交集
        common_keywords = query_keywords & memory_keywords
        
        # 每个匹配关键词增加 boost
        boost = 1.0 + len(common_keywords) * (self.keyword_boost_factor - 1.0)
        
        return boost
    
    def hybrid_recall(
        self,
        query: str,
        limit: int = 10,
        min_importance: float = 0.0,
        temporal_filter: bool = True,
        validity_threshold: float = 0.3,
        current_time: datetime = None
    ) -> List[Dict]:
        """
        混合检索
        
        步骤：
        1. 向量相似度搜索（获取 2x 候选）
        2. 时间有效性过滤
        3. 关键词 boost 重新排序
        4. 返回 Top-K
        
        Args:
            query: 查询文本
            limit: 返回数量
            min_importance: 最小重要性
            temporal_filter: 是否启用时间过滤
            validity_threshold: 时间有效性阈值
            current_time: 当前时间（用于测试）
        
        Returns:
            记忆列表（带混合分数）
        """
        if current_time is None:
            current_time = datetime.now()
        
        # 提取查询关键词
        query_keywords = self.extract_keywords(query)
        
        # 1. 向量相似度搜索（获取 2x 候选）
        candidate_limit = limit * 2
        vector_results = self.memory.recall(
            query,
            limit=candidate_limit,
            min_importance=min_importance
        )
        
        if not vector_results:
            return []
        
        # 2. 时间有效性过滤
        if temporal_filter:
            valid_results = [
                mem for mem in vector_results
                if self.is_temporally_valid(mem, current_time, validity_threshold)
            ]
        else:
            valid_results = vector_results
        
        # 3. 关键词 boost 重新计算分数
        scored_results = []
        for mem in valid_results:
            # 原始向量分数
            vector_score = mem.get("score", 0.0)
            
            # 时间衰减
            temporal_decay = self.temporal_decay(
                mem.get("created_at"),
                current_time
            )
            
            # 关键词 boost
            keyword_boost = self.keyword_boost(mem, query_keywords)
            
            # 重要性权重
            importance = mem.get("importance", 0.5)
            
            # 混合分数 = 向量分数 * 时间衰减 * 关键词 boost * 重要性
            hybrid_score = vector_score * temporal_decay * keyword_boost * importance
            
            # 添加分数详情
            mem_copy = mem.copy()
            mem_copy["hybrid_score"] = hybrid_score
            mem_copy["score_breakdown"] = {
                "vector": vector_score,
                "temporal_decay": temporal_decay,
                "keyword_boost": keyword_boost,
                "importance": importance
            }
            
            scored_results.append(mem_copy)
        
        # 4. 按混合分数排序
        scored_results.sort(key=lambda x: x["hybrid_score"], reverse=True)
        
        # 5. 返回 Top-K
        final_results = scored_results[:limit]
        
        print(f"✅ Hybrid RAG 检索完成:")
        print(f"  - 向量候选: {len(vector_results)}")
        print(f"  - 时间过滤后: {len(valid_results)}")
        print(f"  - 最终返回: {len(final_results)}")
        
        return final_results
    
    def stats(self) -> Dict:
        """统计信息"""
        base_stats = self.memory.stats()
        return {
            **base_stats,
            "hybrid_rag": {
                "decay_rate": self.decay_rate,
                "half_life_days": self.half_life_days,
                "keyword_boost_factor": self.keyword_boost_factor
            }
        }


def main():
    """测试 Hybrid RAG"""
    print("=" * 60)
    print("Hybrid RAG 检索系统 - 测试")
    print("=" * 60)
    print()
    
    # 初始化
    rag = HybridRAG()
    print()
    
    # 统计
    stats = rag.stats()
    print(f"📊 系统状态:")
    print(f"  - 存储类型: {stats.get('storage')}")
    print(f"  - 记忆数量: {stats.get('count')}")
    print(f"  - 时间衰减率: {stats['hybrid_rag']['decay_rate']}")
    print(f"  - 半衰期: {stats['hybrid_rag']['half_life_days']} 天")
    print(f"  - 关键词 boost: {stats['hybrid_rag']['keyword_boost_factor']}x")
    print()
    
    # 测试检索
    print("🔍 测试混合检索...")
    queries = [
        "API 配置和模型",
        "性能优化",
        "用户偏好"
    ]
    
    for query in queries:
        print(f"\n查询: '{query}'")
        results = rag.hybrid_recall(query, limit=3)
        
        for i, mem in enumerate(results, 1):
            print(f"  {i}. Hybrid Score: {mem.get('hybrid_score', 0):.3f}")
            print(f"     内容: {mem['content'][:50]}...")
            breakdown = mem.get("score_breakdown", {})
            print(f"     分数分解: vector={breakdown.get('vector', 0):.2f}, "
                  f"temporal={breakdown.get('temporal_decay', 0):.2f}, "
                  f"keyword={breakdown.get('keyword_boost', 0):.2f}")
    
    print()
    print("✅ 测试完成")


if __name__ == "__main__":
    main()
