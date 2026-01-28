# 快速开始指南

本指南将帮助您快速上手 GeoMind，完成第一次地理定位任务。

## 前置要求

- Python 3.10 或更高版本
- 已安装 GeoMind（参考 [README](../README.md) 安装部分）

## 步骤 1: 配置环境

1. 复制环境变量模板：
```bash
cp .env.example .env
```

2. 编辑 `.env` 文件，填入您的 API 密钥：
```bash
OPENAI_API_KEY=your_key_here
VLM_API_KEY=your_key_here
```

## 步骤 2: 基本使用

### Python 代码示例

```python
from geomind import GeoMindAgent
from pathlib import Path

# 初始化 Agent
agent = GeoMindAgent()

# 执行地理定位
image_path = Path("path/to/your/image.jpg")
result = agent.geolocate(image_path)

# 查看结果
print(f"定位结果: {result.final.answer}")
print(f"置信度: {result.final.confidence:.2%}")
print(f"\n证据链:")
for evidence in result.evidence:
    print(f"  - {evidence.check}: {evidence.result}")
```

### CLI 使用

```bash
# 单张图片
geomind locate --image photo.jpg

# 查看详细信息
geomind locate --image photo.jpg --verbose

# 保存结果到文件
geomind locate --image photo.jpg --output result.json
```

## 步骤 3: 理解输出

Agent 返回的结果包含以下信息：

- `final.answer`: 最终定位结果（地点名称）
- `final.confidence`: 置信度（0-1）
- `final.why`: 支持证据说明
- `final.why_not`: 排除其他候选的原因
- `evidence`: 详细的验证证据链

## 下一步

- 查看 [API 参考](../api/README.md) 了解详细 API
- 阅读 [自定义工具指南](custom_tools.md) 扩展功能
- 探索 [场景扩展指南](scenario_extensions.md) 适配其他任务

