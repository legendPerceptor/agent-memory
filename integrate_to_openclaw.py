#!/usr/bin/env python3
"""
OpenClaw 记忆集成服务

将新的分层记忆系统集成到 OpenClaw 中

使用方式：
1. 导入现有记忆到分层系统
2. 提供统一的记忆管理接口
3. 支持智能检索和演化
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

# 添加路径
sys.path.insert(0, str(Path(__file__).parent / "vector-memory"))

from tiered_memory import TieredMemory
from memory_evolver import MemoryEvolver

# OpenClaw 工作空间
WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_FILE = WORKSPACE / "MEMORY.md"
MEMORY_DIR = WORKSPACE / "memory"


class OpenClawMemoryService:
    """
    OpenClaw 记忆服务
    
    整合分层记忆系统到 OpenClaw
    """
    
    def __init__(self):
        self.tiered = TieredMemory()
        self.evolver = MemoryEvolver(self.tiered)
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
        if MEMORY_FILE.exists():
            content = MEMORY_FILE.read_text()
            
            # 解析不同部分
            sections = self._parse_memory_md(content)
            
            # 更新核心记忆
            if "关于远见" in sections:
                self.tiered.update_core("user_profile", sections["关于远见"])
                print("  ✓ 用户档案已导入")
            
            if "环境配置" in sections:
                self.tiered.update_core("preferences", sections.get("当前项目", ""))
                print("  ✓ 项目信息已导入")
        
        # 2. 导入 memory/*.md 到回忆记忆
        if MEMORY_DIR.exists():
            daily_files = sorted(MEMORY_DIR.glob("*.md"))
            
            for file in daily_files:
                if file.name.startswith("2026-"):  # 只导入日志文件
                    self._import_daily_memory(file)
            
            print(f"  ✓ 已导入 {len(daily_files)} 个日志文件")
        
        self.initialized = True
        print("✅ 记忆导入完成\n")
    
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
        """导入每日记忆"""
        
        content = file.read_text()
        date_str = file.stem  # 2026-03-24
        
        # 提取重要事件
        lines = content.split("\n")
        for line in lines:
            # 跳过标题和空行
            if line.startswith("#") or not line.strip():
                continue
            
            # 检测重要内容
            if any(keyword in line for keyword in ["✅", "完成", "配置", "购买", "决策"]):
                # 使用演化系统记录
                importance = 0.8 if "✅" in line else 0.6
                self.evolver.evolve(
                    line.lstrip("- ").lstrip("* "),
                    importance=importance
                )
    
    def remember(self, content: str, memory_type: str = "fact", importance: float = 0.5):
        """
        记录新记忆
        
        自动选择层级并演化
        """
        
        # 判断应该存储到哪一层
        if importance >= 0.9:
            # 高重要性 → 核心记忆
            print(f"💡 记录到核心记忆: {content[:50]}...")
            self.tiered.update_core("current_task", content)
        elif memory_type == "conversation":
            # 对话 → 工作记忆
            self.tiered.working.add("system", content)
        else:
            # 其他 → 回忆记忆（使用演化）
            operation, memory_id = self.evolver.evolve(content, importance)
            print(f"📝 {operation}: {content[:50]}...")
    
    def recall(self, query: str, max_tokens: int = 2000) -> str:
        """
        智能检索记忆
        
        返回格式化的 context 文本
        """
        
        result = self.tiered.recall(query, context_budget=max_tokens)
        
        # 格式化输出
        context_parts = []
        
        if result["core"]:
            context_parts.append("=== 核心信息 ===")
            context_parts.append(result["core"])
        
        if result["working"]:
            context_parts.append("\n=== 最近对话 ===")
            for msg in result["working"][-5:]:  # 最近 5 条
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
        
        # 1. 清理过时记忆
        self.evolver.cleanup_obsolete(days_old=90, min_importance=0.3)
        
        # 2. 统计
        stats = self.get_stats()
        print(f"📊 优化完成: {stats}")


# 全局实例
_memory_service = None

def get_memory_service() -> OpenClawMemoryService:
    """获取全局记忆服务实例"""
    global _memory_service
    
    if _memory_service is None:
        _memory_service = OpenClawMemoryService()
        _memory_service.import_existing_memories()
    
    return _memory_service


# 测试代码
if __name__ == "__main__":
    print("=" * 60)
    print("OpenClaw 记忆集成服务测试")
    print("=" * 60)
    print()
    
    # 初始化服务
    service = get_memory_service()
    print()
    
    # 测试记忆
    print("📝 测试记录新记忆...")
    service.remember("远见配置了 MiniMax Token Plan", "fact", 0.8)
    service.remember("用户偏好简洁回复", "preference", 0.7)
    print()
    
    # 测试检索
    print("🔍 测试智能检索...")
    context = service.recall("API 配置", max_tokens=1000)
    print(context)
    print()
    
    # 统计
    print("📊 记忆统计:")
    stats = service.get_stats()
    import json
    print(json.dumps(stats, indent=2, ensure_ascii=False))
    print()
    
    print("=" * 60)
    print("✅ 测试完成！")
    print("=" * 60)
