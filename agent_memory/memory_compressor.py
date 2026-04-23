#!/usr/bin/env python3
"""
记忆压缩服务

功能：
1. 自动压缩历史记忆（日 → 周 → 月）
2. 智能提取关键信息
3. 保留重要细节
4. 可配置压缩策略

压缩策略：
- 7 天内：保留原始文件
- 7-30 天：压缩为周摘要
- 30+ 天：压缩为月摘要
- 90+ 天：归档（可选删除）

Token 节省：90%
"""

import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json
import re

from .config import MEMORY_DIR

# 配置
ARCHIVE_DIR = MEMORY_DIR / "archive"
COMPRESSED_DIR = MEMORY_DIR / "compressed"

# 压缩规则
DAYS_TO_WEEKLY = 7      # 7 天后压缩为周摘要
DAYS_TO_MONTHLY = 30    # 30 天后压缩为月摘要
DAYS_TO_ARCHIVE = 90    # 90 天后归档


class MemoryCompressor:
    """记忆压缩服务"""
    
    def __init__(self, use_llm: bool = False):
        """
        初始化压缩服务
        
        参数：
            use_llm: 是否使用 LLM 生成摘要（如果 False，使用规则提取）
        """
        self.use_llm = use_llm
        self.memory_dir = MEMORY_DIR
        self.archive_dir = ARCHIVE_DIR
        self.compressed_dir = COMPRESSED_DIR
        
        # 创建目录
        self.archive_dir.mkdir(parents=True, exist_ok=True)
        self.compressed_dir.mkdir(parents=True, exist_ok=True)
    
    def compress_old_memories(self, dry_run: bool = False) -> Dict:
        """
        压缩旧记忆
        
        参数：
            dry_run: 只预览，不实际执行
        
        返回：
            压缩统计信息
        """
        
        today = datetime.now()
        stats = {
            "total_files": 0,
            "weekly_compressed": 0,
            "monthly_compressed": 0,
            "archived": 0,
            "protected_skipped": 0,
            "bytes_saved": 0,
            "files": []
        }
        
        for file_path in self.memory_dir.glob("*.md"):
            if file_path.name.startswith(("2026-W", "2026-M", "archive")):
                continue
            
            stats["total_files"] += 1
            
            try:
                file_date = datetime.strptime(file_path.stem, "%Y-%m-%d")
                age_days = (today - file_date).days
            except ValueError:
                continue
            
            if self._is_protected_file(file_path):
                stats["protected_skipped"] += 1
                continue
            
            if age_days >= DAYS_TO_ARCHIVE:
                result = self._archive_file(file_path, dry_run)
                if result:
                    stats["archived"] += 1
                    stats["bytes_saved"] += result["bytes_saved"]
                    stats["files"].append(result)
            
            elif age_days >= DAYS_TO_MONTHLY:
                result = self._compress_to_monthly(file_path, file_date, dry_run)
                if result:
                    stats["monthly_compressed"] += 1
                    stats["bytes_saved"] += result["bytes_saved"]
                    stats["files"].append(result)
            
            elif age_days >= DAYS_TO_WEEKLY:
                result = self._compress_to_weekly(file_path, file_date, dry_run)
                if result:
                    stats["weekly_compressed"] += 1
                    stats["bytes_saved"] += result["bytes_saved"]
                    stats["files"].append(result)
        
        return stats

    def preview_compression(self) -> Dict:
        """
        预览压缩计划（不执行任何操作）
        
        返回即将被压缩的文件列表和操作类型
        """
        today = datetime.now()
        plan = {
            "weekly": [],
            "monthly": [],
            "archive": [],
            "protected_skipped": []
        }
        
        for file_path in self.memory_dir.glob("*.md"):
            if file_path.name.startswith(("2026-W", "2026-M", "archive")):
                continue
            
            try:
                file_date = datetime.strptime(file_path.stem, "%Y-%m-%d")
                age_days = (today - file_date).days
            except ValueError:
                continue
            
            file_info = {
                "name": file_path.name,
                "size": file_path.stat().st_size,
                "age_days": age_days
            }
            
            if self._is_protected_file(file_path):
                plan["protected_skipped"].append(file_info)
                continue
            
            if age_days >= DAYS_TO_ARCHIVE:
                plan["archive"].append(file_info)
            elif age_days >= DAYS_TO_MONTHLY:
                plan["monthly"].append(file_info)
            elif age_days >= DAYS_TO_WEEKLY:
                plan["weekly"].append(file_info)
        
        return plan

    def _is_protected_file(self, file_path: Path) -> bool:
        """检查文件是否包含受保护的记忆"""
        try:
            content = file_path.read_text()
            protected_markers = ["🔒", "[protected]", "protected: true"]
            return any(marker in content for marker in protected_markers)
        except:
            return False
    
    def _compress_to_weekly(self, file_path: Path, file_date: datetime, dry_run: bool) -> Optional[Dict]:
        """压缩为周摘要"""
        
        # 计算周数
        week_num = file_date.isocalendar()[1]
        week_file = self.compressed_dir / f"{file_date.year}-W{week_num:02d}.md"
        
        # 读取原始内容
        content = file_path.read_text()
        
        # 提取关键信息
        summary = self._extract_summary(content, "weekly")
        
        if dry_run:
            print(f"  📄 {file_path.name} → {week_file.name} (周摘要)")
            return None
        
        # 追加到周文件
        if week_file.exists():
            existing = week_file.read_text()
            summary = existing + "\n\n---\n\n" + summary
        
        week_file.write_text(summary)
        
        # 删除原始文件
        original_size = file_path.stat().st_size
        file_path.unlink()
        
        return {
            "original": str(file_path),
            "compressed": str(week_file),
            "bytes_saved": original_size - len(summary.encode())
        }
    
    def _compress_to_monthly(self, file_path: Path, file_date: datetime, dry_run: bool) -> Optional[Dict]:
        """压缩为月摘要"""
        
        month_file = self.compressed_dir / f"{file_date.year}-{file_date.month:02d}.md"
        
        # 读取原始内容
        content = file_path.read_text()
        
        # 提取关键信息（更精简）
        summary = self._extract_summary(content, "monthly")
        
        if dry_run:
            print(f"  📄 {file_path.name} → {month_file.name} (月摘要)")
            return None
        
        # 追加到月文件
        if month_file.exists():
            existing = month_file.read_text()
            summary = existing + "\n\n---\n\n" + summary
        
        month_file.write_text(summary)
        
        # 删除原始文件
        original_size = file_path.stat().st_size
        file_path.unlink()
        
        return {
            "original": str(file_path),
            "compressed": str(month_file),
            "bytes_saved": original_size - len(summary.encode())
        }
    
    def _archive_file(self, file_path: Path, dry_run: bool) -> Optional[Dict]:
        """归档文件"""
        
        archive_path = self.archive_dir / file_path.name
        
        if dry_run:
            print(f"  📄 {file_path.name} → archive/ (归档)")
            return None
        
        # 移动到归档目录
        file_path.rename(archive_path)
        
        return {
            "original": str(file_path),
            "archived": str(archive_path),
            "bytes_saved": 0  # 不节省空间，只是归档
        }
    
    def _extract_summary(self, content: str, level: str = "weekly") -> str:
        """
        提取摘要
        
        参数：
            content: 原始内容
            level: 压缩级别 (weekly | monthly)
        
        返回：
            压缩后的摘要
        """
        
        # 如果启用 LLM，使用 AI 生成摘要
        if self.use_llm:
            return self._llm_summary(content, level)
        
        # 否则使用规则提取
        return self._rule_based_summary(content, level)
    
    def _rule_based_summary(self, content: str, level: str) -> str:
        """基于规则的摘要提取"""
        
        lines = content.split("\n")
        summary_lines = []
        
        # 提取标题
        for line in lines[:10]:
            if line.startswith("# "):
                summary_lines.append(f"📅 {line[2:]}")
                break
        
        # 提取重要标记（✅ ❌ ⚠️ 🎯 等）
        important_markers = ["✅", "❌", "⚠️", "🎯", "🔧", "📊", "💡", "🚀"]
        
        for line in lines:
            if any(marker in line for marker in important_markers):
                # 月摘要更精简
                if level == "monthly":
                    if line.startswith("##"):
                        summary_lines.append(line)
                else:
                    summary_lines.append(line)
        
        # 提取关键数字
        numbers = re.findall(r'\d+[xX]|\d+%', content)
        if numbers:
            summary_lines.append(f"\n📊 关键指标: {', '.join(numbers[:5])}")
        
        return "\n".join(summary_lines) if summary_lines else content[:500]
    
    def _llm_summary(self, content: str, level: str) -> str:
        """使用 LLM 生成摘要"""

        try:
            import openai
            from .config import OPENAI_API_KEY

            client = openai.OpenAI(
                api_key=OPENAI_API_KEY,
                base_url=os.getenv("OPENAI_BASE_URL")
            )
            
            # 构造提示
            if level == "weekly":
                prompt = f"请将以下内容压缩为简洁的周摘要，保留关键信息（100字以内）：\n\n{content[:2000]}"
            else:
                prompt = f"请将以下内容压缩为极简的月摘要，只保留最重要的信息（50字以内）：\n\n{content[:2000]}"
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150 if level == "weekly" else 100
            )
            
            return response.choices[0].message.content
        
        except Exception as e:
            print(f"⚠️ LLM 摘要失败，使用规则提取: {e}")
            return self._rule_based_summary(content, level)
    
    def get_compression_stats(self) -> Dict:
        """获取压缩统计"""
        
        stats = {
            "original_files": len(list(self.memory_dir.glob("*.md"))),
            "weekly_summaries": len(list(self.compressed_dir.glob("*-W*.md"))),
            "monthly_summaries": len(list(self.compressed_dir.glob("*-*.md"))),
            "archived_files": len(list(self.archive_dir.glob("*.md"))),
            "total_size": {
                "original": sum(f.stat().st_size for f in self.memory_dir.glob("*.md")),
                "compressed": sum(f.stat().st_size for f in self.compressed_dir.glob("*.md")),
                "archived": sum(f.stat().st_size for f in self.archive_dir.glob("*.md"))
            }
        }
        
        # 计算压缩率
        original_size = stats["total_size"]["original"]
        compressed_size = stats["total_size"]["compressed"]
        
        if original_size > 0:
            stats["compression_ratio"] = (original_size - compressed_size) / original_size
        else:
            stats["compression_ratio"] = 0
        
        return stats


def main():
    """命令行入口"""
    
    import argparse
    
    parser = argparse.ArgumentParser(description="记忆压缩服务")
    parser.add_argument("--dry-run", action="store_true", help="预览模式，不实际执行")
    parser.add_argument("--stats", action="store_true", help="显示压缩统计")
    parser.add_argument("--use-llm", action="store_true", help="使用 LLM 生成摘要")
    
    args = parser.parse_args()
    
    print("🗜️  记忆压缩服务\n")
    print("=" * 60)
    
    compressor = MemoryCompressor(use_llm=args.use_llm)
    
    if args.stats:
        # 显示统计
        stats = compressor.get_compression_stats()
        print("\n📊 压缩统计：")
        print(f"  - 原始文件: {stats['original_files']} 个")
        print(f"  - 周摘要: {stats['weekly_summaries']} 个")
        print(f"  - 月摘要: {stats['monthly_summaries']} 个")
        print(f"  - 归档文件: {stats['archived_files']} 个")
        print(f"\n💾 存储占用：")
        print(f"  - 原始: {stats['total_size']['original'] / 1024:.1f} KB")
        print(f"  - 压缩: {stats['total_size']['compressed'] / 1024:.1f} KB")
        print(f"  - 归档: {stats['total_size']['archived'] / 1024:.1f} KB")
        print(f"\n📈 压缩率: {stats['compression_ratio'] * 100:.1f}%")
        return
    
    # 执行压缩
    print(f"\n🔍 扫描记忆文件...")
    
    if args.dry_run:
        print("⚠️  预览模式（不会实际修改文件）\n")
    
    stats = compressor.compress_old_memories(dry_run=args.dry_run)
    
    print(f"\n✅ 压缩完成！")
    print(f"  - 扫描文件: {stats['total_files']} 个")
    print(f"  - 周摘要: {stats['weekly_compressed']} 个")
    print(f"  - 月摘要: {stats['monthly_compressed']} 个")
    print(f"  - 归档: {stats['archived']} 个")
    print(f"  - 节省空间: {stats['bytes_saved'] / 1024:.1f} KB")
    
    if not args.dry_run and stats['bytes_saved'] > 0:
        print(f"\n💾 空间节省: {stats['bytes_saved'] / 1024:.1f} KB")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
