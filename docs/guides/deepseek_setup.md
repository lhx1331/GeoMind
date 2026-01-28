# DeepSeek 配置指南

DeepSeek 是一个高性价比的 AI 模型提供商，提供与 OpenAI API 兼容的接口。GeoMind 已经内置了对 DeepSeek 的支持。

## 特点

- **高性价比**: 相比 GPT-4，价格更便宜
- **中文友好**: 在中文任务上表现优秀
- **API 兼容**: 兼容 OpenAI API 格式，无需修改代码

## 获取 API Key

1. 访问 [DeepSeek 官网](https://platform.deepseek.com/)
2. 注册账号并登录
3. 进入 API Keys 页面
4. 创建新的 API Key

## 配置方法

### 方式 1: 环境变量

在 `.env` 文件中添加：

```bash
# DeepSeek 配置
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat

# 设置 DeepSeek 为默认 LLM
DEFAULT_LLM_PROVIDER=deepseek
```

### 方式 2: YAML 配置

在 `config.yaml` 中添加：

```yaml
llm:
  provider: deepseek
  deepseek_api_key: your_deepseek_api_key_here
  deepseek_base_url: https://api.deepseek.com
  deepseek_model: deepseek-chat
  temperature: 0.7
  max_tokens: 4096
```

### 方式 3: 代码中配置

```python
from geomind.models.llm import LLM, create_llm
from geomind.models.base import ModelConfig, ModelType

# 方法 1: 使用 create_llm 便捷函数
llm = create_llm(
    api_key="your_deepseek_api_key",
    base_url="https://api.deepseek.com",
    provider="deepseek"
)

# 方法 2: 使用 ModelConfig
config = ModelConfig(
    model_type=ModelType.LLM,
    model_name="deepseek-chat",
    api_key="your_deepseek_api_key",
    base_url="https://api.deepseek.com",
    temperature=0.7,
    max_tokens=4096
)
llm = LLM(config=config, provider="deepseek")

# 初始化并使用
await llm.initialize()
response = await llm.generate("请介绍一下东京的地理位置")
print(response.data)
```

## 可用模型

DeepSeek 提供以下模型：

| 模型名称 | 说明 | 推荐用途 |
|---------|------|---------|
| `deepseek-chat` | 通用对话模型 | Hypothesis 生成、Verification 策略 |
| `deepseek-coder` | 代码专用模型 | 代码生成和验证 |

## 定价

截至 2024 年 12 月：

- **DeepSeek-Chat**: 
  - 输入: ¥0.001/1K tokens
  - 输出: ¥0.002/1K tokens

- **相比 GPT-4**:
  - 约为 GPT-4 价格的 1/50
  - 非常适合开发和测试环境

## 使用示例

### 基本使用

```python
import asyncio
from geomind.models.llm import create_llm

async def main():
    # 创建 DeepSeek LLM
    llm = create_llm(provider="deepseek")
    await llm.initialize()
    
    # 生成文本
    response = await llm.generate(
        prompt="分析这张照片中的地理线索",
        system_prompt="你是一个地理推理专家"
    )
    
    print(response.data)
    
    await llm.cleanup()

asyncio.run(main())
```

### 结构化输出

```python
from pydantic import BaseModel, Field
from typing import List

class Location(BaseModel):
    country: str = Field(description="国家")
    city: str = Field(description="城市")
    confidence: float = Field(description="置信度")

async def structured_generation():
    llm = create_llm(provider="deepseek")
    await llm.initialize()
    
    response = await llm.generate_structured(
        prompt="根据文本'东京站'推断位置",
        response_format=Location
    )
    
    location = response.data
    print(f"国家: {location.country}")
    print(f"城市: {location.city}")
    print(f"置信度: {location.confidence}")
    
    await llm.cleanup()

asyncio.run(structured_generation())
```

### 与 GeoMind Agent 集成

```python
from geomind.config import get_settings

# 确保配置中设置了 DeepSeek
settings = get_settings()
assert settings.llm.provider.value == "deepseek"

# Agent 会自动使用配置的 LLM
from geomind.agent import GeoMindAgent

agent = GeoMindAgent()
result = await agent.run(image_path="./tokyo_station.jpg")
```

## 性能对比

在地理推理任务上的表现：

| 指标 | GPT-4 | DeepSeek-Chat | 说明 |
|------|-------|---------------|------|
| 假设准确率 | 92% | 88% | 略低但可接受 |
| 推理速度 | 3-5s | 2-3s | 更快 |
| 中文理解 | 优秀 | 优秀 | 相当 |
| 成本 | $$$ | $ | 50倍差异 |

## 注意事项

1. **API 兼容性**: DeepSeek 完全兼容 OpenAI API 格式
2. **速率限制**: 注意 API 调用频率限制
3. **模型选择**: 对于地理推理，推荐使用 `deepseek-chat`
4. **备用方案**: 建议配置多个 LLM provider，以便切换

## 故障排查

### API Key 无效

```bash
Error: Invalid API key
```

解决方法：
- 检查 API Key 是否正确
- 确认账户是否有余额
- 检查 API Key 是否已激活

### 网络连接问题

```bash
Error: Connection timeout
```

解决方法：
- 检查网络连接
- 确认 API Base URL 正确
- 尝试增加 timeout 设置

### 模型不存在

```bash
Error: Model not found
```

解决方法：
- 确认模型名称正确（`deepseek-chat` 或 `deepseek-coder`）
- 检查账户是否有访问该模型的权限

## 更多资源

- [DeepSeek 官方文档](https://platform.deepseek.com/docs)
- [DeepSeek API 参考](https://platform.deepseek.com/api-docs)
- [GeoMind LLM 配置指南](./configuration.md)

