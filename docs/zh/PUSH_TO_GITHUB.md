#!/bin/bash

[🌐 English](../../en/PUSH_TO_GITHUB.md) | **中文**
# 创建 GitHub 仓库脚本

# 仓库信息
REPO_NAME="ai-memory"
REPO_DESC="Agent Memory Vector System - A tiered memory system for AI agents with vector retrieval, auto-evolution, and knowledge graph"

# 检查是否已安装 gh CLI
if command -v gh &> /dev/null; then
    echo "✅ 使用 gh CLI 创建仓库..."
    gh repo create $REPO_NAME --public --description "$REPO_DESC" --source=. --push
    echo "✅ 仓库已创建并推送！"
    echo "📍 https://github.com/legendPerceptor/$REPO_NAME"
else
    echo "⚠️  gh CLI 未安装"
    echo ""
    echo "请手动创建仓库："
    echo "1. 访问 https://github.com/new"
    echo "2. Repository name: $REPO_NAME"
    echo "3. Description: $REPO_DESC"
    echo "4. 选择 Public"
    echo "5. 不要勾选 'Add a README file'"
    echo "6. 点击 'Create repository'"
    echo ""
    echo "创建后，执行："
    echo "  cd ~/.openclaw/workspace/ai-memory"
    echo "  git push -u origin main"
fi
