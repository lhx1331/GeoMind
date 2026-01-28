# GeoMind CLI & API 使用指南

## 📋 目录

1. [CLI 使用](#cli-使用)
2. [API 使用](#api-使用)
3. [部署指南](#部署指南)
4. [示例](#示例)

---

## 🖥️ CLI 使用

### 安装

```bash
# 安装 GeoMind（包含 CLI）
pip install -e .

# 或者安装完整版（包含所有可选依赖）
pip install -e ".[all]"
```

### 基本命令

```bash
# 查看帮助
geomind --help

# 查看版本
geomind version

# 查看系统信息
geomind info
```

### locate 命令

#### 基础使用

```bash
# 定位单个图像
geomind locate photo.jpg

# 定位多个图像
geomind locate photo1.jpg photo2.jpg photo3.jpg
```

#### 输出格式

```bash
# 文本格式（默认）
geomind locate photo.jpg

# JSON 格式
geomind locate photo.jpg --format json

# CSV 格式
geomind locate photo.jpg --format csv
```

#### 输出到文件

```bash
# 保存为 JSON 文件
geomind locate photo.jpg --format json --output result.json

# 保存为 CSV 文件
geomind locate photo.jpg --format csv --output results.csv
```

#### 高级选项

```bash
# 启用迭代优化
geomind locate photo.jpg --iterations

# 设置最大迭代次数
geomind locate photo.jpg --iterations --max-iterations 3

# 详细输出
geomind locate photo.jpg --verbose

# 使用自定义配置文件
geomind locate photo.jpg --config config.yaml
```

### 完整示例

```bash
# 批量处理，JSON 输出，启用迭代优化
geomind locate *.jpg --format json --iterations --output batch_results.json --verbose
```

---

## 🌐 API 使用

### 启动服务

```bash
# 方式 1: 使用 Python 直接运行
python -m geomind.api.app

# 方式 2: 使用 uvicorn
uvicorn geomind.api.app:app --host 0.0.0.0 --port 8000 --reload

# 方式 3: 生产环境（使用多个 worker）
uvicorn geomind.api.app:app --host 0.0.0.0 --port 8000 --workers 4
```

### API 文档

启动服务后，访问：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

### 端点说明

#### 1. 健康检查

```bash
GET /api/v1/health
```

**响应示例:**
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "agent_initialized": true
}
```

#### 2. 上传文件定位

```bash
POST /api/v1/geolocate
```

**请求:**
- 方法: POST
- Content-Type: multipart/form-data
- 参数:
  - `file`: 图像文件（必需）
  - `enable_iterations`: 是否启用迭代优化（可选，默认 false）

**示例（使用 curl）:**
```bash
curl -X POST "http://localhost:8000/api/v1/geolocate" \
  -F "file=@photo.jpg" \
  -F "enable_iterations=false"
```

**示例（使用 Python requests）:**
```python
import requests

with open('photo.jpg', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/api/v1/geolocate',
        files={'file': f}
    )

result = response.json()
print(f"位置: ({result['lat']}, {result['lon']})")
print(f"置信度: {result['confidence']}")
```

**响应示例:**
```json
{
  "lat": 48.8584,
  "lon": 2.2945,
  "confidence": 0.92,
  "reasoning": "图像显示埃菲尔铁塔，位于法国巴黎",
  "supporting_evidence": [
    "OCR 识别到 'Eiffel Tower'",
    "建筑风格匹配法国标志性建筑"
  ],
  "alternative_locations": [
    {
      "name": "Louvre Museum",
      "lat": 48.8606,
      "lon": 2.3376,
      "score": 0.75
    }
  ]
}
```

#### 3. URL 定位

```bash
POST /api/v1/geolocate/url
```

**请求示例:**
```json
{
  "image_url": "https://example.com/photo.jpg",
  "enable_iterations": false,
  "max_iterations": 2
}
```

**或使用 Base64:**
```json
{
  "image_base64": "iVBORw0KGgoAAAANSUhEUgA...",
  "enable_iterations": false
}
```

**示例（使用 curl）:**
```bash
curl -X POST "http://localhost:8000/api/v1/geolocate/url" \
  -H "Content-Type: application/json" \
  -d '{
    "image_url": "https://example.com/photo.jpg",
    "enable_iterations": false
  }'
```

#### 4. 批量定位

```bash
POST /api/v1/geolocate/batch
```

**请求示例:**
```json
{
  "image_urls": [
    "https://example.com/photo1.jpg",
    "https://example.com/photo2.jpg",
    "https://example.com/photo3.jpg"
  ],
  "enable_iterations": false
}
```

**响应示例:**
```json
{
  "results": [
    {
      "image_url": "https://example.com/photo1.jpg",
      "success": true,
      "prediction": {
        "lat": 48.8584,
        "lon": 2.2945,
        "confidence": 0.92,
        "reasoning": "..."
      }
    },
    {
      "image_url": "https://example.com/photo2.jpg",
      "success": false,
      "error": "无法加载图像"
    }
  ],
  "success_count": 1,
  "total_count": 2
}
```

---

## 🚀 部署指南

### Docker 部署

创建 `Dockerfile`:

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY . /app

# 安装 Python 依赖
RUN pip install --no-cache-dir -e ".[api,geoclip]"

# 暴露端口
EXPOSE 8000

# 启动服务
CMD ["uvicorn", "geomind.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

构建和运行:

```bash
# 构建镜像
docker build -t geomind:latest .

# 运行容器
docker run -p 8000:8000 -v $(pwd)/config.yaml:/app/config.yaml geomind:latest
```

### 生产环境配置

#### 使用 Gunicorn + Uvicorn

```bash
# 安装 gunicorn
pip install gunicorn

# 启动服务（4 个 worker）
gunicorn geomind.api.app:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 300
```

#### Nginx 反向代理

`/etc/nginx/sites-available/geomind`:

```nginx
server {
    listen 80;
    server_name geomind.example.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        
        # 增加超时时间（图像处理可能较慢）
        proxy_read_timeout 300s;
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
    }
}
```

---

## 📚 示例

### Python 客户端示例

```python
import requests
import json

class GeoMindClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
    
    def geolocate_file(self, file_path, enable_iterations=False):
        """上传文件进行定位"""
        with open(file_path, 'rb') as f:
            response = requests.post(
                f"{self.base_url}/api/v1/geolocate",
                files={'file': f},
                data={'enable_iterations': enable_iterations}
            )
        response.raise_for_status()
        return response.json()
    
    def geolocate_url(self, image_url, enable_iterations=False):
        """通过 URL 定位"""
        response = requests.post(
            f"{self.base_url}/api/v1/geolocate/url",
            json={
                'image_url': image_url,
                'enable_iterations': enable_iterations
            }
        )
        response.raise_for_status()
        return response.json()
    
    def batch_geolocate(self, image_urls):
        """批量定位"""
        response = requests.post(
            f"{self.base_url}/api/v1/geolocate/batch",
            json={'image_urls': image_urls}
        )
        response.raise_for_status()
        return response.json()
    
    def health_check(self):
        """健康检查"""
        response = requests.get(f"{self.base_url}/api/v1/health")
        response.raise_for_status()
        return response.json()

# 使用示例
client = GeoMindClient()

# 检查服务状态
health = client.health_check()
print(f"服务状态: {health['status']}")

# 定位图像
result = client.geolocate_file('photo.jpg')
print(f"位置: ({result['lat']}, {result['lon']})")
print(f"置信度: {result['confidence']:.2%}")
```

### JavaScript 客户端示例

```javascript
class GeoMindClient {
    constructor(baseUrl = 'http://localhost:8000') {
        this.baseUrl = baseUrl;
    }
    
    async geolocateFile(file, enableIterations = false) {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('enable_iterations', enableIterations);
        
        const response = await fetch(`${this.baseUrl}/api/v1/geolocate`, {
            method: 'POST',
            body: formData
        });
        
        return await response.json();
    }
    
    async geolocateUrl(imageUrl, enableIterations = false) {
        const response = await fetch(`${this.baseUrl}/api/v1/geolocate/url`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                image_url: imageUrl,
                enable_iterations: enableIterations
            })
        });
        
        return await response.json();
    }
    
    async healthCheck() {
        const response = await fetch(`${this.baseUrl}/api/v1/health`);
        return await response.json();
    }
}

// 使用示例
const client = new GeoMindClient();

// 处理文件上传
document.getElementById('fileInput').addEventListener('change', async (e) => {
    const file = e.target.files[0];
    const result = await client.geolocateFile(file);
    console.log('位置:', result.lat, result.lon);
    console.log('置信度:', result.confidence);
});
```

---

## 🎯 最佳实践

### 1. CLI 使用建议

- 批量处理时使用 `--verbose` 查看进度
- 使用 JSON 格式便于后续处理
- 合理使用迭代优化（准确性 vs 速度权衡）

### 2. API 使用建议

- 对于大批量请求，考虑使用队列系统
- 设置合理的超时时间
- 实现重试机制
- 缓存常见图像的结果

### 3. 性能优化

- 使用多个 worker 处理并发请求
- 考虑使用 Redis 缓存预测结果
- 图像预处理（压缩、格式转换）
- 限制最大图像大小

---

## 🔧 故障排查

### CLI 问题

**问题**: `command not found: geomind`

**解决**: 重新安装或检查 PATH
```bash
pip install -e .
# 或
python -m geomind.cli locate photo.jpg
```

### API 问题

**问题**: 服务启动失败

**解决**: 检查端口占用和依赖
```bash
# 检查端口
lsof -i :8000

# 安装 API 依赖
pip install -e ".[api]"
```

**问题**: 请求超时

**解决**: 增加超时时间
```bash
uvicorn geomind.api.app:app --timeout-keep-alive 300
```

---

## 📞 获取帮助

- **文档**: `docs/`
- **示例**: `examples/`
- **Issue**: GitHub Issues

---

**祝使用愉快！🎉**

