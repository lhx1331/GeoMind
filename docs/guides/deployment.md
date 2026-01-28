# 部署指南

本指南说明如何部署 GeoMind 到生产环境。

## 部署架构

### 推荐架构

```
                    ┌─────────────┐
                    │   API Gateway │
                    │  (Nginx/Envoy)│
                    └──────┬───────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
   ┌────▼────┐       ┌─────▼─────┐      ┌────▼────┐
   │ GeoMind │       │   VLM      │      │ GeoCLIP │
   │ Service │       │  Service   │      │ Service │
   └─────────┘       └────────────┘      └─────────┘
        │
   ┌────▼────┐
   │   MCP   │
   │  Tools  │
   └─────────┘
```

## 部署方式

### 1. Docker 部署（推荐）

#### 构建镜像

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e .

# 复制代码
COPY geomind/ ./geomind/
COPY scripts/ ./scripts/

# 设置环境变量
ENV PYTHONUNBUFFERED=1

CMD ["uvicorn", "geomind.api:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 构建和运行

```bash
# 构建镜像
docker build -t geomind:latest .

# 运行容器
docker run -d \
  --name geomind \
  -p 8000:8000 \
  --env-file .env \
  -v ./models:/app/models \
  geomind:latest
```

### 2. Kubernetes 部署

#### 部署清单

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: geomind
spec:
  replicas: 3
  selector:
    matchLabels:
      app: geomind
  template:
    metadata:
      labels:
        app: geomind
    spec:
      containers:
      - name: geomind
        image: geomind:latest
        ports:
        - containerPort: 8000
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: geomind-secrets
              key: openai-api-key
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
---
apiVersion: v1
kind: Service
metadata:
  name: geomind-service
spec:
  selector:
    app: geomind
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

### 3. 本地部署

#### 使用 systemd（Linux）

```ini
# /etc/systemd/system/geomind.service
[Unit]
Description=GeoMind Service
After=network.target

[Service]
Type=simple
User=geomind
WorkingDirectory=/opt/geomind
Environment="PATH=/opt/geomind/venv/bin"
ExecStart=/opt/geomind/venv/bin/uvicorn geomind.api:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# 启用服务
sudo systemctl enable geomind
sudo systemctl start geomind
```

## 模型部署

### VLM 服务

#### 使用 vLLM（推荐）

```bash
# 启动 vLLM 服务
python -m vllm.entrypoints.openai.api_server \
  --model qwen-vl-max \
  --port 8001 \
  --gpu-memory-utilization 0.9
```

#### 使用 Ollama

```bash
# 安装模型
ollama pull qwen-vl

# 启动服务
ollama serve
```

### GeoCLIP 服务

```python
# scripts/serve_geoclip.py
from fastapi import FastAPI
from geomind.models.geoclip import GeoCLIPModel

app = FastAPI()
model = GeoCLIPModel()

@app.post("/predict")
async def predict(image_path: str, top_k: int = 5):
    coords, probs = model.predict(image_path, top_k=top_k)
    return {"coordinates": coords, "probabilities": probs}
```

```bash
uvicorn scripts.serve_geoclip:app --port 8002
```

## 配置管理

### 生产环境配置

```yaml
# config/production.yaml
models:
  llm:
    provider: openai
    model: gpt-4-turbo-preview
    timeout: 60
    max_retries: 3
  
  vlm:
    provider: local
    base_url: http://vlm-service:8001/v1
    timeout: 120
  
  geoclip:
    model_path: /models/geoclip
    device: cuda
    cache_embeddings: true

agent:
  max_iterations: 5
  confidence_threshold: 0.7

logging:
  level: INFO
  format: json
  file: /var/log/geomind/app.log

cache:
  backend: redis
  ttl: 3600
  redis:
    host: redis-service
    port: 6379
```

## 监控和日志

### 日志配置

使用结构化日志（JSON 格式）便于集中分析：

```python
# geomind/utils/logging.py
import structlog
import logging

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
)
```

### 指标收集

集成 Prometheus 指标：

```python
from prometheus_client import Counter, Histogram

request_count = Counter('geomind_requests_total', 'Total requests')
request_duration = Histogram('geomind_request_duration_seconds', 'Request duration')
```

### 健康检查

```python
# geomind/api/health.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "0.1.0"
    }

@router.get("/ready")
async def readiness_check():
    # 检查依赖服务
    return {"ready": True}
```

## 安全配置

### 1. API 认证

```python
# 使用 API Key 认证
from fastapi import Security, HTTPException
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key")

async def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key != os.getenv("API_KEY"):
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return api_key
```

### 2. 速率限制

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/geolocate")
@limiter.limit("10/minute")
async def geolocate(...):
    pass
```

### 3. 输入验证

```python
from pydantic import BaseModel, validator

class GeolocateRequest(BaseModel):
    image_path: str
    max_iterations: int = 5
    
    @validator('max_iterations')
    def validate_iterations(cls, v):
        if v > 10:
            raise ValueError('max_iterations must be <= 10')
        return v
```

## 性能优化

### 1. 缓存策略

- GeoCLIP 嵌入缓存（Redis）
- API 响应缓存
- 模型输出缓存

### 2. 异步处理

对于长时间运行的任务，使用异步队列：

```python
from celery import Celery

celery_app = Celery('geomind')

@celery_app.task
def geolocate_async(image_path: str):
    # 异步执行定位任务
    pass
```

### 3. 资源优化

- 模型懒加载
- 连接池复用
- GPU 内存管理

## 故障排查

### 常见问题

1. **模型加载失败**
   - 检查模型路径和权限
   - 验证 GPU 内存是否充足

2. **API 超时**
   - 增加超时时间
   - 检查网络连接

3. **内存不足**
   - 减少并发请求
   - 启用模型卸载

### 日志分析

```bash
# 查看错误日志
tail -f /var/log/geomind/app.log | jq 'select(.level=="ERROR")'

# 分析请求延迟
cat /var/log/geomind/app.log | jq '.duration' | awk '{sum+=$1; count++} END {print sum/count}'
```

## 备份和恢复

### 模型备份

```bash
# 备份模型
tar -czf geoclip-backup.tar.gz /models/geoclip

# 恢复模型
tar -xzf geoclip-backup.tar.gz -C /models/
```

### 配置备份

定期备份配置文件和环境变量。

## 扩展部署

### 水平扩展

- 使用负载均衡器分发请求
- 无状态服务设计，便于扩展
- 共享缓存和数据库

### 垂直扩展

- 增加 GPU 资源
- 优化模型推理速度
- 使用模型量化

更多部署细节请参考各部署平台的官方文档。

