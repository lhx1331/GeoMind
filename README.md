# GeoMind - 通用地理推理 Agent

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

基于 PHRV 框架（Perception → Hypothesis → Retrieval → Verification）的通用多模态推理 Agent，首个应用场景为图像地理定位。

## ✨ 特性

- 🔍 **多模态感知**：结合视觉模型、OCR、EXIF 等多源线索
- 🧠 **智能假设生成**：基于线索自动生成地理假设
- 🔎 **高效检索**：集成 GeoCLIP 和 MCP 工具进行候选召回
- ✅ **证据核验**：闭环验证机制，减少幻觉，提供可审计的证据链
- 🧩 **模块化设计**：模型、提示模板、工具完全解耦，易于替换和扩展
- 🔒 **沙盒安全**：受控环境执行自定义代码，保障安全
- 📊 **状态可观测**：完整的中间状态记录，便于调试和分析

## 🏗️ 技术架构

### 核心框架

- **LangGraph** - 状态管理和流程编排
- **LangChain** - Agent 基础框架
- **MCP (Model Context Protocol)** - 工具集成协议
- **Pydantic** - 数据验证和状态 Schema
- **FastAPI** - API 服务（可选）

### 模型支持

- **VLM**: OpenAI GPT-4V, Anthropic Claude 3, Google Gemini, **阿里云通义千问** 🇨🇳, 智谱 GLM-4V, LLaVA 等
- **GeoCLIP**: 地理图像检索模型
- **LLM**: OpenAI, Anthropic, **DeepSeek** ⭐, 本地模型等

## 📦 安装

### 前置要求

- Python 3.10+
- CUDA 11.8+ (可选，用于 GPU 加速)

### 快速安装

#### 方法 1: 使用设置脚本（推荐）

**Windows (PowerShell)**:
```powershell
.\scripts\setup_dev_env.ps1
```

**Linux/macOS**:
```bash
chmod +x scripts/setup_dev_env.sh
./scripts/setup_dev_env.sh
```

#### 方法 2: 手动安装

```bash
# 克隆仓库
git clone https://github.com/your-org/GeoMind.git
cd GeoMind

# 创建虚拟环境（项目使用 venv/ 目录）
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\Activate.ps1

# 安装依赖
pip install -e .
```

### 开发模式安装

```bash
# 确保虚拟环境已激活
source venv/bin/activate  # Windows: venv\Scripts\Activate.ps1

# 安装开发依赖
pip install -e ".[dev]"
```

> **提示**: 详细虚拟环境配置请查看 [VENV.md](VENV.md)

## 🚀 快速开始

### 1. 配置环境变量

创建 `.env` 文件：

```bash
# LLM 配置 (三选一)
# 选项 1: DeepSeek (推荐性价比)
DEEPSEEK_API_KEY=your_deepseek_key
DEFAULT_LLM_PROVIDER=deepseek

# 选项 2: OpenAI
# OPENAI_API_KEY=your_openai_key
# DEFAULT_LLM_PROVIDER=openai

# 选项 3: 本地模型
# LOCAL_LLM_BASE_URL=http://localhost:8000/v1
# DEFAULT_LLM_PROVIDER=local

# VLM 配置 (五选一)
# 选项 1: OpenAI Vision (全球推荐)
VLM_PROVIDER=openai
VLM_OPENAI_API_KEY=your_openai_key

# 选项 2: 阿里云通义千问 (国内推荐)
# VLM_PROVIDER=qwen
# VLM_QWEN_API_KEY=your_qwen_key

# 选项 3: Google Gemini (性价比)
# VLM_PROVIDER=google
# VLM_GOOGLE_API_KEY=your_google_key

# 选项 4: 智谱 GLM-4V (国产)
# VLM_PROVIDER=glm
# VLM_GLM_API_KEY=your_glm_key

# 选项 5: 本地模型
# VLM_PROVIDER=local
# VLM_LOCAL_BASE_URL=http://localhost:8001/v1

# GeoCLIP 配置 (必需 - 地理位置检索)
GEOCLIP_MODEL_PATH=./models/geoclip
GEOCLIP_DEVICE=cuda  # 或 cpu

# 下载 GeoCLIP 模型:
# python download_geoclip.py

# MCP 工具配置
MCP_SERVER_URL=http://localhost:8002
```

### 2. 运行示例

```python
from geomind import GeoMindAgent
from geomind.models import GeoCLIPModel
from geomind.tools import MCPToolRegistry

# 初始化 Agent
agent = GeoMindAgent(
    vlm_provider="openai",  # 或 "local"
    geoclip_model=GeoCLIPModel(),
    tools=MCPToolRegistry()
)

# 执行地理定位
result = agent.geolocate(
    image_path="path/to/image.jpg",
    max_iterations=5
)

print(f"定位结果: {result.final.answer}")
print(f"置信度: {result.final.confidence}")
print(f"证据: {result.final.why}")
```

### 3. 使用 CLI

```bash
# 单张图片定位
geomind locate --image path/to/image.jpg

# 批量处理
geomind locate --image-dir ./images --output results.json

# 详细输出
geomind locate --image path/to/image.jpg --verbose
```

## 📁 项目结构

```
GeoMind/
├── geomind/                    # 主包
│   ├── __init__.py
│   ├── agent/                  # Agent 核心
│   │   ├── __init__.py
│   │   ├── graph.py           # LangGraph 流程定义
│   │   ├── nodes.py           # PHRV 节点实现
│   │   └── state.py           # 状态定义
│   ├── models/                 # 模型层
│   │   ├── __init__.py
│   │   ├── vlm.py             # 视觉模型接口
│   │   ├── geoclip.py         # GeoCLIP 模型
│   │   └── llm.py             # 语言模型接口
│   ├── tools/                  # 工具层
│   │   ├── __init__.py
│   │   ├── mcp/               # MCP 工具
│   │   │   ├── geocode.py
│   │   │   ├── poi_search.py
│   │   │   └── verification.py
│   │   └── sandbox.py         # 沙盒工具
│   ├── prompts/                # 提示模板
│   │   ├── __init__.py
│   │   ├── perception.py
│   │   ├── hypothesis.py
│   │   └── verification.py
│   ├── config/                 # 配置管理
│   │   ├── __init__.py
│   │   ├── settings.py
│   │   └── schema.py
│   └── utils/                  # 工具函数
│       ├── __init__.py
│       ├── image.py
│       └── logging.py
├── tests/                      # 测试
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── examples/                   # 示例代码
│   ├── basic_usage.py
│   ├── custom_tools.py
│   └── custom_scenario.py
├── docs/                       # 文档
│   ├── api/
│   └── guides/
├── scripts/                    # 脚本
│   ├── setup_models.py
│   └── download_geoclip.py
├── pyproject.toml              # 项目配置
├── README.md                   # 本文件
├── GUIDE.md                    # 技术设计文档
└── .env.example                # 环境变量示例
```

## 🔧 配置

详细配置说明请参考 [配置文档](docs/guides/configuration.md)。

主要配置项：

- **模型配置**：VLM、LLM、GeoCLIP 的提供商和参数
- **工具配置**：MCP 服务器地址、工具权限
- **流程配置**：迭代次数、置信度阈值
- **安全配置**：沙盒限制、隐私保护级别

## 📖 使用文档

- [快速开始指南](docs/guides/quickstart.md)
- [**API Keys 配置清单**](docs/API_KEYS_CHECKLIST.md) ⭐ 完整资源清单
- [**VLM 提供商对比指南**](docs/guides/vlm_providers.md) - 6 种 Vision 模型选择
- [**DeepSeek 配置指南**](docs/guides/deepseek_setup.md) - LLM 性价比之选
- [API 参考](docs/api/README.md)
- [自定义工具开发](docs/guides/custom_tools.md)
- [场景扩展指南](docs/guides/scenario_extensions.md)
- [部署指南](docs/guides/deployment.md)

## 🧪 测试

```bash
# 运行所有测试
pytest

# 运行单元测试
pytest tests/unit

# 运行集成测试
pytest tests/integration

# 生成覆盖率报告
pytest --cov=geomind --cov-report=html
```

## 🤝 贡献

欢迎贡献！请阅读 [贡献指南](CONTRIBUTING.md) 了解详细信息。

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📝 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [LangGraph](https://github.com/langchain-ai/langgraph) - 流程编排框架
- [GeoCLIP](https://github.com/Vision-CAIR/GeoCLIP) - 地理图像检索模型
- [MCP](https://modelcontextprotocol.io/) - 模型上下文协议

## 📧 联系方式

- 问题反馈: [GitHub Issues](https://github.com/your-org/GeoMind/issues)
- 讨论区: [GitHub Discussions](https://github.com/your-org/GeoMind/discussions)

---

**注意**: 本项目仅用于研究和教育目的。使用地理定位功能时请遵守当地法律法规，保护个人隐私。

