"""
Shared configuration for agent_memory.

Loads .env once using python-dotenv and exports all settings as module-level constants.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root (two levels up from this file)
_env_file = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_env_file)

# Resolve proxy issues with Qdrant connections
os.environ.setdefault("NO_PROXY", "*")
os.environ.setdefault("no_proxy", "*")

# Directories
MEMORY_DIR = Path.home() / ".openclaw" / "workspace" / "memory"
GRAPH_DIR = Path.home() / ".openclaw" / "workspace" / "ai-memory" / "knowledge_graph"

# Qdrant
QDRANT_HOST = os.getenv("QDRANT_HOST", "agent-memory-qdrant")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
COLLECTION_NAME = "agent_memories"

# OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
HTTP_PROXY = os.getenv("HTTP_PROXY", "")

# Vector dimensions
VECTOR_SIZE = 1536  # text-embedding-3-small
