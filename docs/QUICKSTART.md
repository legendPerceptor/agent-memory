# 快速开始指南

## 1. 环境准备

### 安装依赖

```bash
cd vector-memory
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 配置环境变量

```bash
cd ..
cp .env.example .env
# 编辑 .env 文件
```

**最小配置：**
```bash
OPENAI_API_KEY=YOUR_OPENAI_API_KEY_HERE
QDRANT_HOST=localhost
QDRANT_PORT=6333
```

## 2. 启动 Qdrant

### Docker 方式（推荐）

```bash
docker run -d --name qdrant \
  -p 6333:6333 \
  -v qdrant_data:/qdrant/storage \
  qdrant/qdrant:latest
```

### Docker Compose 方式

```bash
# 创建 docker-compose.yml
cat > docker-compose.yml << EOF
version: '3.8'
services:
  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
    volumes:
      - qdrant_data:/qdrant/storage
    restart: unless-stopped

volumes:
  qdrant_data:
EOF

docker-compose up -d
```

## 3. 运行测试

```bash
cd vector-memory
python test_quickstart.py
```

**预期输出：**
```
✅ Qdrant 连接成功
✅ 记忆已存储到 Qdrant
✅ 从 Qdrant 检索到 3 条记忆
✅ 测试完成！
```

## 4. 使用示例

### Python 代码

```python
from memory_service import MemoryService

# 初始化
service = MemoryService()

# 写入记忆
service.remember(
    content="用户的时区是 UTC+8",
    memory_type="fact",
    importance=0.8,
    tags=["user", "timezone"]
)

# 检索记忆
results = service.recall(
    query="用户时间相关信息",
    limit=5
)

# 显示结果
for mem in results:
    print(f"[{mem['score']:.3f}] {mem['content']}")
```

## 5. 故障排查

### Qdrant 连接失败

```bash
# 检查 Qdrant 是否运行
docker ps | grep qdrant

# 检查端口
curl http://localhost:6333/collections
```

### OpenAI API 错误

```bash
# 测试 API Key
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer YOUR_API_KEY"

# 如果需要代理
export HTTPS_PROXY=http://your-proxy:port
```

### 依赖安装失败

```bash
# 升级 pip
pip install --upgrade pip

# 重新安装
pip install -r requirements.txt --force-reinstall
```

## 6. 下一步

- 查看 [完整文档](docs/FINAL_SOLUTION.md)
- 了解 [优化计划](docs/IMPROVEMENT_PLAN.md)
- 运行 [实验工具](experiments/)

## 成本说明

**OpenAI Embedding API：**
- 价格：$0.02 / 1M tokens（约 0.14 元）
- 每日使用：~12,500 tokens
- **每月成本：~0.05 元**

**几乎可以忽略不计！**
