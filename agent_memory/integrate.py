#!/usr/bin/env python3
"""
OpenClaw 记忆集成服务

将新的分层记忆系统集成到 OpenClaw 中

使用方式：
1. 导入现有记忆到分层系统
2. 提供统一的记忆管理接口
3. 支持智能检索和演化
"""

import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional

from .tiered_memory import TieredMemory
from .memory_evolver import MemoryEvolver
from .human_feedback import HumanFeedbackManager, MemoryCandidate

WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_FILE = WORKSPACE / "MEMORY.md"
MEMORY_DIR = WORKSPACE / "memory"

SECTION_MAPPING = {
    "user_profile": {
        "keywords": ["用户", "档案", "个人", "关于", "profile", "about", "自我", "简介", "基本信息"],
        "label": "用户档案",
    },
    "preferences": {
        "keywords": ["偏好", "习惯", "喜好", "preference", "环境", "配置", "设置", "config", "setting"],
        "label": "用户偏好",
    },
    "current_task": {
        "keywords": ["项目", "任务", "当前", "project", "task", "工作", "进行中", "计划"],
        "label": "当前任务",
    },
}


class OpenClawMemoryService:
    """
    OpenClaw 记忆服务

    整合分层记忆系统到 OpenClaw
    """

    def __init__(self, workspace: Path = None):
        self.workspace = workspace or WORKSPACE
        self.memory_file = self.workspace / "MEMORY.md"
        self.memory_dir = self.workspace / "memory"

        from .memory_service import MemoryService
        self.service = MemoryService()
        
        self.tiered = TieredMemory(self.service)
        self.evolver = MemoryEvolver(self.tiered)
        self.feedback = HumanFeedbackManager(self.tiered)
        self.initialized = False

        print("🧠 OpenClaw 记忆服务初始化中...")

    def import_existing_memories(self):
        """
        导入现有的 MEMORY.md 和 memory/*.md 到分层系统
        """

        if self.initialized:
            print("⚠️  记忆已导入，跳过")
            return

        print("📥 开始导入现有记忆...")

        # 1. 导入 MEMORY.md 到核心记忆
        if self.memory_file.exists():
            content = self.memory_file.read_text()
            sections = self._parse_memory_md(content)
            self._import_sections_to_core(sections)

        # 2. 导入 memory/*.md 到回忆记忆
        if self.memory_dir.exists():
            daily_files = sorted(self.memory_dir.glob("*.md"))
            imported_count = 0
            for file in daily_files:
                if re.match(r"\d{4}-\d{2}-\d{2}", file.name):
                    self._import_daily_memory(file)
                    imported_count += 1

            print(f"  ✓ 已导入 {imported_count} 个日志文件")

        self.initialized = True
        print("✅ 记忆导入完成\n")

    def _import_sections_to_core(self, sections: Dict[str, str]):
        """将 MEMORY.md 的各 section 智能映射到核心记忆块"""

        mapped_blocks = set()
        unmapped_sections = {}

        for section_title, section_content in sections.items():
            if not section_content.strip():
                continue

            target_block = self._match_section_to_block(section_title)

            if target_block:
                if target_block not in mapped_blocks:
                    self.tiered.update_core(target_block, section_content)
                    mapped_blocks.add(target_block)
                    label = SECTION_MAPPING[target_block]["label"]
                    print(f"  ✓ {label}已导入 (来源: {section_title})")
                else:
                    unmapped_sections[section_title] = section_content
            else:
                unmapped_sections[section_title] = section_content

        for section_title, section_content in unmapped_sections.items():
            self.evolver.evolve(
                f"[MEMORY.md] {section_title}\n{section_content}",
                importance=0.7,
            )
            print(f"  ✓ 未映射section已存入回忆记忆: {section_title}")

    def _match_section_to_block(self, section_title: str) -> Optional[str]:
        """根据 section 标题智能匹配核心记忆块"""

        title_lower = section_title.lower().strip()

        for block_name, mapping in SECTION_MAPPING.items():
            for keyword in mapping["keywords"]:
                if keyword in title_lower:
                    return block_name

        return None

    def _parse_memory_md(self, content: str) -> Dict[str, str]:
        """解析 MEMORY.md 内容"""

        sections = {}
        current_section = None
        current_content = []

        for line in content.split("\n"):
            if line.startswith("## "):
                if current_section:
                    sections[current_section] = "\n".join(current_content).strip()
                current_section = line[3:].strip()
                current_content = []
            else:
                current_content.append(line)

        if current_section:
            sections[current_section] = "\n".join(current_content).strip()

        return sections

    def _import_daily_memory(self, file: Path):
        """导入每日记忆——按段落导入，保留上下文"""

        content = file.read_text()
        date_str = file.stem

        blocks = self._split_into_blocks(content)

        for heading, block_text in blocks:
            text = block_text.strip()
            if not text or len(text) < 10:
                continue

            contextualized = f"[{date_str}] {heading}\n{text}" if heading else f"[{date_str}] {text}"

            importance = self._assess_importance(text, heading)

            if self._is_noise(text):
                continue

            self.evolver.evolve(contextualized, importance=importance)

    def _assess_importance(self, text: str, heading: str = "") -> float:
        """根据内容评估重要性"""

        importance = 0.5

        high_keywords = ["决策", "重要", "关键", "里程碑", "上线", "发布", "完成", "成功", "✅", "🎯", "⚠️"]
        medium_keywords = ["配置", "更新", "修改", "新增", "实现", "集成", "优化", "修复"]
        low_keywords = ["尝试", "临时", "草稿", "备忘"]

        combined = f"{heading} {text}"

        if any(kw in combined for kw in high_keywords):
            importance = 0.85
        elif any(kw in combined for kw in medium_keywords):
            importance = 0.7

        if any(kw in combined for kw in low_keywords):
            importance = max(importance - 0.2, 0.3)

        return importance

    def _is_noise(self, text: str) -> bool:
        """判断是否为纯噪声内容（应跳过）"""

        noise_patterns = [
            r"traceback\s*\(most recent call last\)",
            r"^\s*\d+\.\d+\s*(ms|s)\s*$",
            r"^(ok|yes|no|done|好的|嗯|对)$",
        ]

        text_stripped = text.strip()

        for pattern in noise_patterns:
            if re.search(pattern, text_stripped, re.IGNORECASE):
                return True

        if len(text_stripped) < 5:
            return True

        return False

    def _split_into_blocks(self, content: str) -> List[Tuple[str, str]]:
        """按标题拆分成 (heading, body) 块"""

        blocks = []
        current_heading = ""
        current_lines = []

        for line in content.split("\n"):
            if line.startswith("### ") or line.startswith("## "):
                if current_lines:
                    blocks.append((current_heading, "\n".join(current_lines)))
                current_heading = line.lstrip("#").strip()
                current_lines = []
            elif not line.startswith("#"):
                current_lines.append(line)

        if current_lines:
            blocks.append((current_heading, "\n".join(current_lines)))

        return blocks

    def remember(self, content: str, memory_type: str = "fact", importance: float = 0.5, require_approval: bool = False):
        """
        记录新记忆

        自动选择层级并演化

        Args:
            content: 记忆内容
            memory_type: 记忆类型 (fact/conversation/preference/...)
            importance: 重要性 (0.0-1.0)
            require_approval: 为 True 时创建候选项等待审核，而非直接写入
        """

        if importance >= 0.9:
            if require_approval:
                proposal = self.tiered.core.propose_update("current_task", content)
                print(f"📋 核心记忆变更提案:")
                print(f"   块: {proposal.get('block_label', 'current_task')}")
                for line in proposal.get("diff_lines", []):
                    print(f"   {line}")
                return proposal
            print(f"💡 记录到核心记忆: {content[:50]}...")
            self.tiered.update_core("current_task", content)
        elif memory_type == "conversation":
            self.tiered.working.add("system", content)
        elif memory_type == "preference":
            if require_approval:
                current = self.tiered.core.get("preferences")
                new_value = f"{current}\n{content}".strip() if current else content
                proposal = self.tiered.core.propose_update("preferences", new_value)
                print(f"📋 偏好变更提案:")
                for line in proposal.get("diff_lines", []):
                    print(f"   {line}")
                return proposal
            current = self.tiered.core.get("preferences")
            new_value = f"{current}\n{content}".strip() if current else content
            self.tiered.update_core("preferences", new_value)
            print(f"💡 偏好已更新: {content[:50]}...")
        else:
            if require_approval:
                candidate = self.evolver.evolve_with_feedback(
                    content, importance, feedback_manager=self.feedback
                )
                return candidate
            operation, memory_id = self.evolver.evolve(content, importance)
            print(f"📝 {operation}: {content[:50]}...")

    def propose_memory(self, content: str, memory_type: str = "fact", importance: float = 0.5) -> MemoryCandidate:
        """
        提出记忆候选项（等待人类审核）

        Returns:
            MemoryCandidate 候选项，可通过 confirm/modify/reject 处理
        """
        return self.evolver.evolve_with_feedback(
            content, importance, feedback_manager=self.feedback
        )

    def review_candidates(self, limit: int = 20) -> List[MemoryCandidate]:
        """获取待审核的记忆候选项"""
        return self.feedback.get_pending_candidates(limit)

    def confirm_candidate(self, candidate_id: str, source: str = "api") -> str:
        """确认候选项，写入记忆系统"""
        # 先检查队列中的候选项
        candidate = self.feedback.candidate_queue.get(candidate_id)
        if candidate:
            if candidate.operation == "NOOP" and candidate.target_memory_id:
                # NOOP：已有相同记忆，直接返回已有 ID
                print(f"⏭️  重复记忆，直接返回已有 ID: {candidate.target_memory_id}")
                return candidate.target_memory_id
            return self.feedback.confirm_candidate(candidate_id, source)
        
        # 候选项不在队列中（可能是 NOOP 直接返回的候选项尝试确认）
        # 从 pending 候选项中查找（可能是 NOOP 但已入库的情况）
        pending = self.feedback.get_pending_candidates(limit=100)
        for p in pending:
            if p.candidate_id == candidate_id:
                if p.operation == "NOOP" and p.target_memory_id:
                    print(f"⏭️  重复记忆（从队列外），直接返回已有 ID: {p.target_memory_id}")
                    return p.target_memory_id
                return self.feedback.confirm_candidate(candidate_id, source)
        
        raise ValueError(f"候选项不存在: {candidate_id}")

    def modify_candidate(self, candidate_id: str, content: str = None, importance: float = None, memory_type: str = None, reason: str = "", source: str = "api") -> str:
        """修改候选项后写入记忆系统"""
        return self.feedback.modify_candidate(candidate_id, content, importance, memory_type, reason, source)

    def reject_candidate(self, candidate_id: str, reason: str = "", source: str = "api") -> None:
        """拒绝候选项"""
        self.feedback.reject_candidate(candidate_id, reason, source)

    def rate_memory(self, memory_id: str, rating: int, source: str = "api") -> None:
        """
        评价记忆

        Args:
            memory_id: 记忆 ID
            rating: +1 有用 / -1 无用
            source: 反馈来源 ("feishu" | "cli" | "api")
        """
        self.feedback.rate_memory(memory_id, rating, source)

    def submit_relevance_feedback(self, query: str, memory_id: str, relevant: bool, source: str = "api") -> None:
        """
        提交检索相关性反馈

        Args:
            query: 查询文本
            memory_id: 记忆 ID
            relevant: 是否相关
            source: 反馈来源
        """
        self.feedback.submit_relevance_feedback(query, memory_id, relevant, source)

    def generate_review_queue(self, criteria: Dict = None) -> List[Dict]:
        """生成待审核记忆队列（周期性审核用）"""
        return self.feedback.generate_review_queue(criteria)

    def apply_review_decision(self, memory_id: str, action: str, **kwargs) -> None:
        """
        应用审核决策

        Args:
            memory_id: 记忆 ID
            action: "keep" | "modify" | "delete" | "protect"
        """
        self.feedback.apply_review_decision(memory_id, action, **kwargs)

    def get_feedback_stats(self) -> Dict:
        """获取反馈统计"""
        return self.feedback.get_feedback_stats()

    def recall(self, query: str, max_tokens: int = 2000) -> str:
        """
        智能检索记忆

        返回格式化的 context 文本
        """

        result = self.tiered.recall(query, context_budget=max_tokens)

        context_parts = []

        if result["core"]:
            context_parts.append("=== 核心信息 ===")
            context_parts.append(result["core"])

        if result["working"]:
            context_parts.append("\n=== 最近对话 ===")
            for msg in result["working"][-5:]:
                context_parts.append(f"{msg['role']}: {msg['content']}")

        if result["recall"]:
            context_parts.append("\n=== 相关记忆 ===")
            for mem in result["recall"]:
                score = mem.get('score', 0)
                context_parts.append(f"- [{score:.2f}] {mem['content']}")

        return "\n".join(context_parts)

    def get_stats(self) -> Dict:
        """获取记忆统计"""
        return self.tiered.stats()

    def optimize(self):
        """优化记忆（清理、压缩）"""

        print("🔄 开始记忆优化...")

        self.evolver.cleanup_obsolete(days_old=90, min_importance=0.3)

        stats = self.get_stats()
        print(f"📊 优化完成: {stats}")


_memory_service = None


def get_memory_service(workspace: Path = None) -> OpenClawMemoryService:
    """获取全局记忆服务实例"""
    global _memory_service

    if _memory_service is None:
        _memory_service = OpenClawMemoryService(workspace=workspace)
        _memory_service.import_existing_memories()

    return _memory_service


if __name__ == "__main__":
    print("=" * 60)
    print("OpenClaw 记忆集成服务测试")
    print("=" * 60)
    print()

    service = get_memory_service()
    print()

    print("📝 测试记录新记忆...")
    service.remember("配置了 MiniMax Token Plan", "fact", 0.8)
    service.remember("用户偏好简洁回复", "preference", 0.7)
    print()

    print("🔍 测试智能检索...")
    context = service.recall("API 配置", max_tokens=1000)
    print(context)
    print()

    print("📊 记忆统计:")
    stats = service.get_stats()
    import json
    print(json.dumps(stats, indent=2, ensure_ascii=False))
    print()

    print("=" * 60)
    print("✅ 测试完成！")
    print("=" * 60)
