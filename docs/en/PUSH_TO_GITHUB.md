#!/bin/bash

**English** | [🌐 中文](../../zh/PUSH_TO_GITHUB.md)
# Create GitHub Repository Script

# Repository information
REPO_NAME="ai-memory"
REPO_DESC="Agent Memory Vector System - A tiered memory system for AI agents with vector retrieval, auto-evolution, and knowledge graph"

# Check if gh CLI is installed
if command -v gh &> /dev/null; then
    echo "✅ Using gh CLI to create repository..."
    gh repo create $REPO_NAME --public --description "$REPO_DESC" --source=. --push
    echo "✅ Repository created and pushed!"
    echo "📍 https://github.com/legendPerceptor/$REPO_NAME"
else
    echo "⚠️  gh CLI not installed"
    echo ""
    echo "Please create the repository manually:"
    echo "1. Visit https://github.com/new"
    echo "2. Repository name: $REPO_NAME"
    echo "3. Description: $REPO_DESC"
    echo "4. Select Public"
    echo "5. Do not check 'Add a README file'"
    echo "6. Click 'Create repository'"
    echo ""
    echo "After creation, run:"
    echo "  cd ~/.openclaw/workspace/ai-memory"
    echo "  git push -u origin main"
fi
