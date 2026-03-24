#!/usr/bin/env python3
"""
每周记忆摘要生成器

功能：
1. 读取过去 7 天的 memory/*.md 文件
2. 提取重要事件、决策、待办
3. 生成简洁的周摘要
4. 归档原始文件到 memory/archive/
"""

import os
from datetime import datetime, timedelta
from pathlib import Path
import re

# 配置
MEMORY_DIR = Path.home() / ".openclaw" / "workspace" / "memory"
ARCHIVE_DIR = MEMORY_DIR / "archive"

def get_week_files(week_start):
    """获取一周内的所有 memory 文件"""
    files = []
    for i in range(7):
        date = week_start + timedelta(days=i)
        filename = f"{date.strftime('%Y-%m-%d')}.md"
        filepath = MEMORY_DIR / filename
        if filepath.exists():
            files.append(filepath)
    return files

def extract_important_content(content):
    """从内容中提取重要信息"""
    events = []
    decisions = []
    todos = []
    
    lines = content.split('\n')
    
    for line in lines:
        # 提取完成的任务
        if '[x]' in line.lower() or '✅' in line:
            events.append(line)
        
        # 提取决策
        if any(word in line.lower() for word in ['决定', '选择', '配置', '决策', 'choose', 'decide']):
            decisions.append(line)
        
        # 提取待办
        if '[ ]' in line or '待办' in line or 'todo' in line.lower():
            todos.append(line)
    
    return {
        'events': events,
        'decisions': decisions,
        'todos': todos
    }

def generate_weekly_summary(week_start, files):
    """生成周摘要"""
    all_events = []
    all_decisions = []
    all_todos = []
    
    for filepath in files:
        content = filepath.read_text()
        extracted = extract_important_content(content)
        all_events.extend(extracted['events'])
        all_decisions.extend(extracted['decisions'])
        all_todos.extend(extracted['todos'])
    
    # 生成摘要
    week_num = week_start.isocalendar()[1]
    summary = f"""# {week_start.year}-W{week_num:02d} 周摘要

**时间范围：** {week_start.strftime('%Y-%m-%d')} ~ {(week_start + timedelta(days=6)).strftime('%Y-%m-%d')}

## 重要事件

{chr(10).join(f'- {e}' for e in all_events[:10]) if all_events else '- 无'}

## 关键决策

{chr(10).join(f'- {d}' for d in all_decisions[:5]) if all_decisions else '- 无'}

## 待办事项

{chr(10).join(f'- {t}' for t in all_todos[:10]) if all_todos else '- 无'}

---
*自动生成于 {datetime.now().strftime('%Y-%m-%d %H:%M')}*
"""
    return summary

def archive_files(files, week_start):
    """归档原始文件"""
    ARCHIVE_DIR.mkdir(exist_ok=True)
    
    for filepath in files:
        # 移动到 archive/ 目录
        archive_path = ARCHIVE_DIR / filepath.name
        filepath.rename(archive_path)
        print(f"已归档: {filepath.name} -> archive/")

def main():
    # 计算本周起始日期（周一）
    today = datetime.now().date()
    week_start = today - timedelta(days=today.weekday())
    
    # 获取一周的文件
    files = get_week_files(week_start)
    
    if not files:
        print("本周没有 memory 文件")
        return
    
    print(f"找到 {len(files)} 个文件")
    
    # 生成摘要
    summary = generate_weekly_summary(week_start, files)
    
    # 保存摘要
    week_num = week_start.isocalendar()[1]
    summary_path = MEMORY_DIR / f"{week_start.year}-W{week_num:02d}.md"
    summary_path.write_text(summary)
    print(f"已生成: {summary_path.name}")
    
    # 询问是否归档
    print("\n是否归档原始文件？(y/n): ", end='')
    choice = input().strip().lower()
    
    if choice == 'y':
        archive_files(files, week_start)
        print("归档完成！")
    else:
        print("跳过归档")

if __name__ == "__main__":
    main()
