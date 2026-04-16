#!/usr/bin/env python3
"""
OpenClaw 记忆自动启动脚本

在 OpenClaw 启动时自动初始化分层记忆系统
位置：~/.openclaw/scripts/init_memory.py
"""

import sys
from pathlib import Path

# 导入记忆服务
try:
    from agent_memory.integrate import get_memory_service
    MEMORY_AVAILABLE = True
except Exception as e:
    print(f"⚠️  记忆服务导入失败: {e}")
    MEMORY_AVAILABLE = False

def initialize_memory():
    """
    初始化记忆服务
    
    在 OpenClaw 启动时自动调用
    """
    
    if not MEMORY_AVAILABLE:
        print("⚠️  记忆服务不可用")
        return None
    
    try:
        print("🧠 正在初始化分层记忆系统...")
        
        # 获取记忆服务实例（会自动导入现有记忆）
        service = get_memory_service()
        
        # 显示统计
        stats = service.get_stats()
        print(f"📊 记忆已加载:")
        print(f"  - 核心记忆: {stats['core']['tokens']} tokens")
        print(f"  - 工作记忆: {stats['working']['messages']}/{stats['working']['max']}")
        print(f"  - 回忆记忆: {stats['recall']['count']} 条")
        print(f"  - 归档记忆: {stats['archival']['archives']} 个")
        
        print("✅ 分层记忆系统已就绪\n")
        
        return service
    
    except Exception as e:
        print(f"❌ 记忆初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def get_context_for_query(query: str, max_tokens: int = 2000) -> str:
    """
    快速检索记忆上下文
    
    用于在对话中快速获取相关记忆
    """
    
    if not MEMORY_AVAILABLE:
        return ""
    
    try:
        service = get_memory_service()
        return service.recall(query, max_tokens)
    except:
        return ""


def remember_fact(content: str, importance: float = 0.7):
    """
    记录重要事实
    
    用于记录用户偏好、重要决策等
    """
    
    if not MEMORY_AVAILABLE:
        return None
    
    try:
        service = get_memory_service()
        service.remember(content, "fact", importance)
        print(f"📝 已记录: {content[:50]}...")
    except Exception as e:
        print(f"⚠️  记录失败: {e}")


# 自动初始化（如果作为脚本运行）
if __name__ == "__main__":
    service = initialize_memory()
    
    if service:
        # 测试检索
        print("\n🔍 测试检索：'用户偏好'")
        context = get_context_for_query("用户偏好", max_tokens=500)
        print(context)
