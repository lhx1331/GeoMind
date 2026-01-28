# 配置指南

GeoMind 支持灵活的配置方式，可以通过环境变量、配置文件或代码进行配置。

## 配置方式

### 1. 环境变量（推荐）

使用 `.env` 文件管理配置：

```bash
# .env
OPENAI_API_KEY=sk-...
VLM_PROVIDER=openai
AGENT_MAX_ITERATIONS=5
```

### 2. 配置文件

使用 YAML 配置文件：

```yaml
# config.yaml
models:
  llm:
    provider: openai
    model: gpt-4-turbo-preview
  vlm:
    provider: openai
    model: gpt-4-vision-preview
  geoclip:
    model_path: ./models/geoclip
    device: cuda

agent:
  max_iterations: 5
  confidence_threshold: 0.7
```

### 3. 代码配置

```python
from geomind.config import Settings

settings = Settings(
    llm_provider="openai",
    max_iterations=5,
    confidence_threshold=0.7
)
```

## 配置项说明

### 模型配置

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `LLM_PROVIDER` | LLM 提供商 (openai/anthropic/local) | openai |
| `LLM_MODEL` | 模型名称 | gpt-4-turbo-preview |
| `VLM_PROVIDER` | VLM 提供商 | openai |
| `VLM_MODEL` | VLM 模型名称 | gpt-4-vision-preview |
| `GEOCLIP_MODEL_PATH` | GeoCLIP 模型路径 | ./models/geoclip |
| `GEOCLIP_DEVICE` | 运行设备 (cuda/cpu) | cuda |

### Agent 配置

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `AGENT_MAX_ITERATIONS` | 最大迭代次数 | 5 |
| `AGENT_CONFIDENCE_THRESHOLD` | 置信度阈值 | 0.7 |
| `AGENT_ENABLE_VERIFICATION` | 启用验证 | true |
| `AGENT_ENABLE_SANDBOX` | 启用沙盒 | true |

### 安全配置

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `PRIVACY_LOCATION_PRECISION` | 位置精度 (exact/city/region/country) | city |
| `ALLOW_EXACT_COORDINATES` | 允许精确坐标 | false |
| `FILTER_SENSITIVE_LOCATIONS` | 过滤敏感场所 | true |

详细配置项请参考 `.env.example` 文件。

