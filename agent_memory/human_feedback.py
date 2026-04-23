#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Human-in-the-Loop 记忆反馈系统

核心功能：
1. 写入时反馈 - 记忆候选项审核
2. 检索时反馈 - 记忆评价与相关性反馈
3. 周期性审核 - 低置信度/矛盾记忆审核
4. 参数自适应 - 基于反馈优化系统参数

设计原则：
- 非阻塞式：人类反馈可选，系统可无反馈运行
- 渠道无关：只提供反馈接口，不关心反馈来源（飞书/CLI/API）
- 反馈持久化：所有反馈记录保存，用于参数自适应和审计
"""

import json
import uuid
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, asdict, field
from pathlib import Path
from collections import defaultdict

from .config import MEMORY_DIR


@dataclass
class MemoryFeedback:
    """
    记忆反馈记录
    
    记录人类对某条记忆或候选项的反馈
    """
    feedback_id: str
    memory_id: str
    feedback_type: str  # "confirm" | "modify" | "reject" | "relevance_up" | "relevance_down" | "rate"
    original_content: str = ""
    modified_content: str = ""
    original_importance: float = 0.5
    modified_importance: float = 0.5
    original_type: str = ""
    modified_type: str = ""
    reason: str = ""
    source: str = "api"  # "feishu" | "cli" | "api"
    created_at: str = ""
    
    def __post_init__(self):
        if not self.feedback_id:
            self.feedback_id = str(uuid.uuid4())[:12]
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'MemoryFeedback':
        return cls(**data)


@dataclass
class MemoryCandidate:
    """
    记忆候选项
    
    提出待写入的记忆，等待人类审核后决定是否写入
    """
    candidate_id: str
    content: str
    memory_type: str = "fact"
    importance: float = 0.5
    confidence: float = 0.7
    source: str = ""
    operation: str = "ADD"  # "ADD" | "UPDATE" | "DELETE"
    status: str = "pending"  # "pending" | "confirmed" | "modified" | "rejected"
    target_memory_id: str = ""  # UPDATE/DELETE 时的目标记忆 ID
    feedback: Optional[MemoryFeedback] = None
    created_at: str = ""
    
    def __post_init__(self):
        if not self.candidate_id:
            self.candidate_id = str(uuid.uuid4())[:12]
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        if self.feedback:
            data["feedback"] = self.feedback.to_dict()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'MemoryCandidate':
        if data.get("feedback") and isinstance(data["feedback"], dict):
            data["feedback"] = MemoryFeedback.from_dict(data["feedback"])
        return cls(**data)


class FeedbackStore:
    """
    反馈存储
    
    持久化所有反馈记录
    """
    
    def __init__(self, store_dir: Path = None):
        self.store_dir = store_dir or MEMORY_DIR / "feedback"
        self.store_dir.mkdir(parents=True, exist_ok=True)
        self.feedback_file = self.store_dir / "feedback_history.json"
        self.feedbacks = self._load()
    
    def _load(self) -> List[Dict]:
        if self.feedback_file.exists():
            try:
                return json.loads(self.feedback_file.read_text())
            except:
                return []
        return []
    
    def _save(self):
        self.feedback_file.write_text(
            json.dumps(self.feedbacks, indent=2, ensure_ascii=False)
        )
    
    def save_feedback(self, feedback: MemoryFeedback) -> str:
        self.feedbacks.append(feedback.to_dict())
        self._save()
        return feedback.feedback_id
    
    def get_feedback(self, memory_id: str) -> List[MemoryFeedback]:
        return [
            MemoryFeedback.from_dict(f)
            for f in self.feedbacks
            if f.get("memory_id") == memory_id
        ]
    
    def get_recent_feedback(self, days: int = 30) -> List[MemoryFeedback]:
        cutoff = datetime.now() - timedelta(days=days)
        result = []
        for f in self.feedbacks:
            try:
                created = datetime.fromisoformat(f.get("created_at", ""))
                if created >= cutoff:
                    result.append(MemoryFeedback.from_dict(f))
            except:
                continue
        return result
    
    def get_feedback_stats(self) -> Dict:
        stats = {
            "total": len(self.feedbacks),
            "by_type": defaultdict(int),
            "by_source": defaultdict(int),
            "recent_7d": 0,
            "recent_30d": 0,
        }
        
        now = datetime.now()
        for f in self.feedbacks:
            stats["by_type"][f.get("feedback_type", "unknown")] += 1
            stats["by_source"][f.get("source", "unknown")] += 1
            
            try:
                created = datetime.fromisoformat(f.get("created_at", ""))
                if created >= now - timedelta(days=7):
                    stats["recent_7d"] += 1
                if created >= now - timedelta(days=30):
                    stats["recent_30d"] += 1
            except:
                continue
        
        stats["by_type"] = dict(stats["by_type"])
        stats["by_source"] = dict(stats["by_source"])
        return stats


class CandidateQueue:
    """
    记忆候选项队列
    
    管理待审核的记忆候选项
    """
    
    def __init__(self, store_dir: Path = None):
        self.store_dir = store_dir or MEMORY_DIR / "candidates"
        self.store_dir.mkdir(parents=True, exist_ok=True)
        self.queue_file = self.store_dir / "pending_candidates.json"
        self.queue = self._load()
    
    def _load(self) -> Dict[str, Dict]:
        if self.queue_file.exists():
            try:
                return json.loads(self.queue_file.read_text())
            except:
                return {}
        return {}
    
    def _save(self):
        self.queue_file.write_text(
            json.dumps(self.queue, indent=2, ensure_ascii=False)
        )
    
    def add(self, candidate: MemoryCandidate) -> str:
        self.queue[candidate.candidate_id] = candidate.to_dict()
        self._save()
        return candidate.candidate_id
    
    def get(self, candidate_id: str) -> Optional[MemoryCandidate]:
        data = self.queue.get(candidate_id)
        if data:
            return MemoryCandidate.from_dict(data)
        return None
    
    def update(self, candidate: MemoryCandidate) -> None:
        self.queue[candidate.candidate_id] = candidate.to_dict()
        self._save()
    
    def remove(self, candidate_id: str) -> None:
        if candidate_id in self.queue:
            del self.queue[candidate_id]
            self._save()
    
    def get_pending(self, limit: int = 20) -> List[MemoryCandidate]:
        pending = [
            MemoryCandidate.from_dict(c)
            for c in self.queue.values()
            if c.get("status") == "pending"
        ]
        pending.sort(key=lambda x: x.created_at, reverse=True)
        return pending[:limit]
    
    def get_all_pending(self) -> List[MemoryCandidate]:
        return [
            MemoryCandidate.from_dict(c)
            for c in self.queue.values()
            if c.get("status") == "pending"
        ]
    
    def cleanup(self, max_age_days: int = 7) -> int:
        cutoff = datetime.now() - timedelta(days=max_age_days)
        to_remove = []
        
        for cid, data in self.queue.items():
            if data.get("status") != "pending":
                try:
                    created = datetime.fromisoformat(data.get("created_at", ""))
                    if created < cutoff:
                        to_remove.append(cid)
                except:
                    to_remove.append(cid)
        
        for cid in to_remove:
            del self.queue[cid]
        
        if to_remove:
            self._save()
        
        return len(to_remove)


class FeedbackAnalyzer:
    """
    反馈分析器
    
    分析反馈数据，优化系统参数
    """
    
    def __init__(self, feedback_store: FeedbackStore):
        self.store = feedback_store
    
    def analyze_feedback_patterns(self) -> Dict:
        feedbacks = self.store.get_recent_feedback(days=30)
        
        if not feedbacks:
            return {"message": "无足够反馈数据"}
        
        patterns = {
            "rejection_rate": 0.0,
            "modification_rate": 0.0,
            "confirmation_rate": 0.0,
            "avg_importance_adjustment": 0.0,
            "type_modifications": defaultdict(int),
            "source_distribution": defaultdict(int),
            "common_rejection_reasons": defaultdict(int),
        }
        
        total = len(feedbacks)
        rejections = 0
        modifications = 0
        confirmations = 0
        importance_adjustments = []
        
        for f in feedbacks:
            patterns["source_distribution"][f.source] += 1
            
            if f.feedback_type == "reject":
                rejections += 1
                if f.reason:
                    patterns["common_rejection_reasons"][f.reason[:50]] += 1
            
            elif f.feedback_type == "modify":
                modifications += 1
                if f.original_type != f.modified_type:
                    patterns["type_modifications"][f"{f.original_type}→{f.modified_type}"] += 1
                if f.original_importance != f.modified_importance:
                    importance_adjustments.append(f.modified_importance - f.original_importance)
            
            elif f.feedback_type == "confirm":
                confirmations += 1
        
        patterns["rejection_rate"] = rejections / total if total > 0 else 0
        patterns["modification_rate"] = modifications / total if total > 0 else 0
        patterns["confirmation_rate"] = confirmations / total if total > 0 else 0
        
        if importance_adjustments:
            patterns["avg_importance_adjustment"] = sum(importance_adjustments) / len(importance_adjustments)
        
        patterns["type_modifications"] = dict(patterns["type_modifications"])
        patterns["source_distribution"] = dict(patterns["source_distribution"])
        patterns["common_rejection_reasons"] = dict(patterns["common_rejection_reasons"])
        
        return patterns
    
    def suggest_parameter_adjustments(self) -> Dict:
        patterns = self.analyze_feedback_patterns()
        suggestions = {}
        
        if patterns.get("rejection_rate", 0) > 0.3:
            suggestions["auto_approve_threshold"] = {
                "current": 0.9,
                "suggested": 0.95,
                "reason": "拒绝率过高，建议提高自动审批阈值"
            }
        
        if patterns.get("modification_rate", 0) > 0.2:
            suggestions["importance_calibration"] = {
                "reason": "修改率较高，建议校准重要性评估",
                "avg_adjustment": patterns.get("avg_importance_adjustment", 0)
            }
        
        type_mods = patterns.get("type_modifications", {})
        if type_mods:
            suggestions["type_classification"] = {
                "reason": "存在分类修改，建议优化分类规则",
                "modifications": type_mods
            }
        
        return suggestions


class HumanFeedbackManager:
    """
    人类反馈管理器
    
    核心协调器，管理候选项生命周期、接收与存储反馈、驱动参数自适应
    """
    
    def __init__(self, memory_system=None, store_dir: Path = None):
        from .tiered_memory import TieredMemory
        self.memory = memory_system or TieredMemory()
        self.feedback_store = FeedbackStore(store_dir / "feedback" if store_dir else None)
        self.candidate_queue = CandidateQueue(store_dir / "candidates" if store_dir else None)
        self.analyzer = FeedbackAnalyzer(self.feedback_store)
        
        self.auto_approve_threshold = 0.9
    
    def propose_memory(
        self,
        content: str,
        memory_type: str = "fact",
        importance: float = 0.5,
        confidence: float = 0.7,
        source: str = "",
        operation: str = "ADD",
        target_memory_id: str = ""
    ) -> MemoryCandidate:
        candidate = MemoryCandidate(
            candidate_id="",
            content=content,
            memory_type=memory_type,
            importance=importance,
            confidence=confidence,
            source=source,
            operation=operation,
            target_memory_id=target_memory_id
        )
        
        self.candidate_queue.add(candidate)
        print(f"📋 记忆候选项已创建: {candidate.candidate_id}")
        print(f"   内容: {content[:50]}...")
        print(f"   置信度: {confidence:.2f} | 状态: pending")
        
        return candidate
    
    def confirm_candidate(self, candidate_id: str, source: str = "api") -> str:
        candidate = self.candidate_queue.get(candidate_id)
        if not candidate:
            # NOOP 候选不会被加入队列，直接返回已有记忆 ID
            raise ValueError(f"候选项不存在: {candidate_id}")
        
        if candidate.status != "pending":
            raise ValueError(f"候选项已处理: {candidate.status}")
        
        memory_id = self._write_candidate(candidate)
        
        feedback = MemoryFeedback(
            feedback_id="",
            memory_id=memory_id,
            feedback_type="confirm",
            original_content=candidate.content,
            modified_content=candidate.content,
            original_importance=candidate.importance,
            modified_importance=candidate.importance,
            original_type=candidate.memory_type,
            modified_type=candidate.memory_type,
            source=source
        )
        self.feedback_store.save_feedback(feedback)
        
        candidate.status = "confirmed"
        candidate.feedback = feedback
        self.candidate_queue.update(candidate)
        
        print(f"✅ 候选项已确认并写入: {candidate_id} → {memory_id}")
        return memory_id
    
    def modify_candidate(
        self,
        candidate_id: str,
        content: str = None,
        importance: float = None,
        memory_type: str = None,
        reason: str = "",
        source: str = "api"
    ) -> str:
        candidate = self.candidate_queue.get(candidate_id)
        if not candidate:
            # NOOP 候选不会被加入队列，直接返回已有记忆 ID
            raise ValueError(f"候选项不存在: {candidate_id}")
        
        if candidate.status != "pending":
            raise ValueError(f"候选项已处理: {candidate.status}")
        
        original_content = candidate.content
        original_importance = candidate.importance
        original_type = candidate.memory_type
        
        if content is not None:
            candidate.content = content
        if importance is not None:
            candidate.importance = importance
        if memory_type is not None:
            candidate.memory_type = memory_type
        
        memory_id = self._write_candidate(candidate)
        
        feedback = MemoryFeedback(
            feedback_id="",
            memory_id=memory_id,
            feedback_type="modify",
            original_content=original_content,
            modified_content=candidate.content,
            original_importance=original_importance,
            modified_importance=candidate.importance,
            original_type=original_type,
            modified_type=candidate.memory_type,
            reason=reason,
            source=source
        )
        self.feedback_store.save_feedback(feedback)
        
        candidate.status = "modified"
        candidate.feedback = feedback
        self.candidate_queue.update(candidate)
        
        print(f"✏️ 候选项已修改并写入: {candidate_id} → {memory_id}")
        return memory_id
    
    def reject_candidate(self, candidate_id: str, reason: str = "", source: str = "api") -> None:
        candidate = self.candidate_queue.get(candidate_id)
        if not candidate:
            # NOOP 候选不会被加入队列，直接返回已有记忆 ID
            raise ValueError(f"候选项不存在: {candidate_id}")
        
        if candidate.status != "pending":
            raise ValueError(f"候选项已处理: {candidate.status}")
        
        feedback = MemoryFeedback(
            feedback_id="",
            memory_id=candidate.target_memory_id or candidate.candidate_id,
            feedback_type="reject",
            original_content=candidate.content,
            reason=reason,
            source=source
        )
        self.feedback_store.save_feedback(feedback)
        
        candidate.status = "rejected"
        candidate.feedback = feedback
        self.candidate_queue.update(candidate)
        
        print(f"❌ 候选项已拒绝: {candidate_id}")
        if reason:
            print(f"   原因: {reason}")
    
    def auto_approve(self, confidence_threshold: float = None) -> List[str]:
        threshold = confidence_threshold or self.auto_approve_threshold
        pending = self.candidate_queue.get_all_pending()
        
        approved_ids = []
        for candidate in pending:
            if candidate.confidence >= threshold:
                try:
                    memory_id = self.confirm_candidate(candidate.candidate_id, source="auto")
                    approved_ids.append(memory_id)
                except Exception as e:
                    print(f"⚠️ 自动审批失败: {candidate.candidate_id} - {e}")
        
        if approved_ids:
            print(f"🤖 自动审批了 {len(approved_ids)} 个高置信度候选项")
        return approved_ids
    
    def get_pending_candidates(self, limit: int = 20) -> List[MemoryCandidate]:
        return self.candidate_queue.get_pending(limit)
    
    def _write_candidate(self, candidate: MemoryCandidate) -> str:
        if candidate.operation == "NOOP" and candidate.target_memory_id:
            # 重复记忆，返回已有记忆的 ID，不写入新内容
            return candidate.target_memory_id
        
        if candidate.operation == "DELETE" and candidate.target_memory_id:
            self._delete_memory(candidate.target_memory_id)
            return candidate.target_memory_id
        
        return self.memory.recall_mem.remember(
            content=candidate.content,
            memory_type=candidate.memory_type,
            importance=candidate.importance
        )
    
    def _delete_memory(self, memory_id: str):
        recall = self.memory.recall_mem
        
        if recall.use_qdrant:
            try:
                from qdrant_client.models import PointIdsList
                recall.client.delete(
                    collection_name="agent_memories",
                    points_selector=PointIdsList(points=[memory_id])
                )
            except Exception as e:
                print(f"⚠️ Qdrant 删除失败: {e}")
        
        recall.memories = [
            m for m in recall.memories
            if m.get("id") != memory_id and m.get("qdrant_id") != memory_id
        ]
        recall._save_memories()
    
    def rate_memory(self, memory_id: str, rating: int, source: str = "api") -> None:
        if rating not in [-1, 0, 1]:
            raise ValueError("rating 必须是 -1, 0 或 1")
        
        recall = self.memory.recall_mem
        found = False
        
        for mem in recall.memories:
            if mem.get("id") == memory_id or mem.get("qdrant_id") == memory_id:
                mem["human_rating"] = mem.get("human_rating", 0) + rating
                mem["feedback_count"] = mem.get("feedback_count", 0) + 1
                found = True
                break
        
        if not found and recall.use_qdrant:
            try:
                from qdrant_client.models import Payload
                recall.client.set_payload(
                    collection_name="agent_memories",
                    payload={
                        "human_rating": rating,
                        "feedback_count": 1
                    },
                    points=[memory_id]
                )
                found = True
            except Exception as e:
                print(f"⚠️ Qdrant 更新失败: {e}")
        
        if found:
            recall._save_memories()
            
            feedback_type = "relevance_up" if rating > 0 else "relevance_down"
            feedback = MemoryFeedback(
                feedback_id="",
                memory_id=memory_id,
                feedback_type=feedback_type,
                source=source
            )
            self.feedback_store.save_feedback(feedback)
            
            print(f"⭐ 记忆已评价: {memory_id} → {rating:+d}")
        else:
            print(f"⚠️ 记忆不存在: {memory_id}")
    
    def submit_relevance_feedback(
        self,
        query: str,
        memory_id: str,
        relevant: bool,
        source: str = "api"
    ) -> None:
        feedback = MemoryFeedback(
            feedback_id="",
            memory_id=memory_id,
            feedback_type="relevance_up" if relevant else "relevance_down",
            reason=f"query: {query[:100]}",
            source=source
        )
        self.feedback_store.save_feedback(feedback)
        
        rating = 1 if relevant else -1
        self.rate_memory(memory_id, rating, source)
    
    def generate_review_queue(self, criteria: Dict = None) -> List[Dict]:
        criteria = criteria or {}
        
        queue = []
        recall = self.memory.recall_mem
        
        for mem in recall.memories:
            reasons = []
            
            confidence = mem.get("confidence", 0.7)
            if confidence < 0.6:
                reasons.append(f"低置信度: {confidence:.2f}")
            
            human_rating = mem.get("human_rating", 0)
            if human_rating < -1:
                reasons.append(f"负面评价: {human_rating}")
            
            created_at = mem.get("created_at", "")
            access_count = mem.get("access_count", 0)
            if created_at and access_count == 0:
                try:
                    created = datetime.fromisoformat(created_at)
                    age_days = (datetime.now() - created).days
                    if age_days > 30:
                        reasons.append(f"长期未访问: {age_days}天")
                except:
                    pass
            
            feedback_count = mem.get("feedback_count", 0)
            if feedback_count > 3:
                reasons.append(f"频繁反馈: {feedback_count}次")
            
            if reasons:
                queue.append({
                    "memory_id": mem.get("id"),
                    "content": mem.get("content", "")[:100],
                    "type": mem.get("type"),
                    "importance": mem.get("importance"),
                    "confidence": confidence,
                    "human_rating": human_rating,
                    "reasons": reasons
                })
        
        queue.sort(key=lambda x: x.get("confidence", 0.5))
        return queue[:50]
    
    def detect_contradictions(self) -> List[Tuple[Dict, Dict]]:
        contradictions = []
        recall = self.memory.recall_mem
        memories = recall.memories
        
        for i, mem1 in enumerate(memories):
            for mem2 in memories[i+1:]:
                content1 = mem1.get("content", "").lower()
                content2 = mem2.get("content", "").lower()
                
                contradiction_pairs = [
                    ("改用", "使用"),
                    ("换成", "使用"),
                    ("不再", "使用"),
                    ("取消", "配置"),
                    ("删除", "配置"),
                ]
                
                for kw1, kw2 in contradiction_pairs:
                    if kw1 in content1 and kw2 in content2:
                        contradictions.append((mem1, mem2))
                        break
                    elif kw1 in content2 and kw2 in content1:
                        contradictions.append((mem2, mem1))
                        break
        
        return contradictions[:10]
    
    def suggest_merges(self, similarity_threshold: float = 0.85) -> List[List[str]]:
        merges = []
        recall = self.memory.recall_mem
        memories = recall.memories
        
        for i, mem1 in enumerate(memories):
            similar_group = [mem1.get("id")]
            
            for mem2 in memories[i+1:]:
                content1 = set(mem1.get("content", "").lower().split())
                content2 = set(mem2.get("content", "").lower().split())
                
                if not content1 or not content2:
                    continue
                
                intersection = len(content1 & content2)
                union = len(content1 | content2)
                similarity = intersection / union if union > 0 else 0
                
                if similarity >= similarity_threshold:
                    similar_group.append(mem2.get("id"))
            
            if len(similar_group) > 1:
                merges.append(similar_group)
        
        return merges[:10]
    
    def apply_review_decision(
        self,
        memory_id: str,
        action: str,
        content: str = None,
        importance: float = None,
        **kwargs
    ) -> None:
        if action == "keep":
            print(f"📌 记忆保留: {memory_id}")
        
        elif action == "modify":
            self._update_memory(memory_id, content, importance)
            print(f"✏️ 记忆已修改: {memory_id}")
        
        elif action == "delete":
            self._delete_memory(memory_id)
            print(f"🗑️ 记忆已删除: {memory_id}")
        
        elif action == "protect":
            self._set_protected(memory_id, True)
            print(f"🔒 记忆已保护: {memory_id}")
        
        else:
            raise ValueError(f"未知操作: {action}")
    
    def _update_memory(self, memory_id: str, content: str = None, importance: float = None):
        recall = self.memory.recall_mem
        
        for mem in recall.memories:
            if mem.get("id") == memory_id or mem.get("qdrant_id") == memory_id:
                if content is not None:
                    mem["content"] = content
                if importance is not None:
                    mem["importance"] = importance
                mem["reviewed"] = True
                break
        
        recall._save_memories()
    
    def _set_protected(self, memory_id: str, protected: bool):
        recall = self.memory.recall_mem
        
        for mem in recall.memories:
            if mem.get("id") == memory_id or mem.get("qdrant_id") == memory_id:
                mem["protected"] = protected
                break
        
        recall._save_memories()
    
    def get_parameter_suggestions(self) -> Dict:
        return self.analyzer.suggest_parameter_adjustments()
    
    def auto_adjust_parameters(self) -> Dict:
        suggestions = self.get_parameter_suggestions()
        applied = {}
        
        if "auto_approve_threshold" in suggestions:
            new_threshold = suggestions["auto_approve_threshold"]["suggested"]
            self.auto_approve_threshold = new_threshold
            applied["auto_approve_threshold"] = new_threshold
        
        return applied
    
    def get_feedback_stats(self) -> Dict:
        return self.feedback_store.get_feedback_stats()
    
    def cleanup_old_candidates(self, max_age_days: int = 7) -> int:
        return self.candidate_queue.cleanup(max_age_days)


if __name__ == "__main__":
    print("=" * 60)
    print("Human-in-the-Loop 记忆反馈系统 - 测试")
    print("=" * 60)
    print()
    
    manager = HumanFeedbackManager()
    print()
    
    print("📋 测试候选项创建...")
    candidate = manager.propose_memory(
        content="用户偏好简洁回复，不喜欢长篇大论",
        memory_type="preference",
        importance=0.8,
        confidence=0.85,
        source="test"
    )
    print()
    
    print("📋 获取待审核候选项...")
    pending = manager.get_pending_candidates()
    print(f"  待审核数量: {len(pending)}")
    for c in pending[:3]:
        print(f"  - {c.candidate_id}: {c.content[:40]}... (置信度: {c.confidence:.2f})")
    print()
    
    print("✅ 测试确认候选项...")
    memory_id = manager.confirm_candidate(candidate.candidate_id, source="test")
    print()
    
    print("⭐ 测试记忆评价...")
    manager.rate_memory(memory_id, rating=1, source="test")
    print()
    
    print("📊 测试反馈统计...")
    stats = manager.get_feedback_stats()
    print(f"  总反馈数: {stats['total']}")
    print(f"  按类型: {stats['by_type']}")
    print(f"  按来源: {stats['by_source']}")
    print()
    
    print("🔍 测试审核队列生成...")
    review_queue = manager.generate_review_queue()
    print(f"  待审核记忆数: {len(review_queue)}")
    print()
    
    print("📈 测试参数建议...")
    suggestions = manager.get_parameter_suggestions()
    print(f"  建议: {suggestions}")
    print()
    
    print("=" * 60)
    print("✅ 测试完成！")
    print("=" * 60)
