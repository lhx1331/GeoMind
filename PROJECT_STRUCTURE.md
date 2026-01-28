# 项目结构说明

本文档详细说明 GeoMind 项目的目录结构和各模块职责。

## 目录树

```
GeoMind/
├── geomind/                    # 主包目录
│   ├── __init__.py            # 包初始化，导出主要 API
│   │
│   ├── agent/                 # Agent 核心模块
│   │   ├── __init__.py
│   │   ├── graph.py           # LangGraph 流程定义
│   │   ├── nodes.py           # PHRV 节点实现
│   │   │   ├── perception.py  # Perception 节点
│   │   │   ├── hypothesis.py  # Hypothesis 节点
│   │   │   ├── retrieval.py   # Retrieval 节点
│   │   │   ├── verification.py # Verification 节点
│   │   │   └── finalize.py    # Finalize 节点
│   │   └── state.py           # 状态定义 (Pydantic models)
│   │
│   ├── models/                # 模型层
│   │   ├── __init__.py
│   │   ├── base.py            # 模型基类接口
│   │   ├── vlm.py             # 视觉模型封装
│   │   ├── geoclip.py         # GeoCLIP 模型封装
│   │   └── llm.py             # 语言模型封装
│   │
│   ├── tools/                 # 工具层
│   │   ├── __init__.py
│   │   ├── base.py            # 工具基类
│   │   ├── registry.py        # 工具注册表
│   │   ├── mcp/               # MCP 工具实现
│   │   │   ├── __init__.py
│   │   │   ├── geocode.py     # 地理编码工具
│   │   │   ├── reverse_geocode.py # 反向地理编码
│   │   │   ├── poi_search.py  # POI 搜索工具
│   │   │   ├── verification.py # 验证工具
│   │   │   └── client.py      # MCP 客户端
│   │   └── sandbox.py         # 沙盒工具
│   │
│   ├── prompts/               # 提示模板
│   │   ├── __init__.py
│   │   ├── base.py            # 模板基类
│   │   ├── perception.py      # Perception 阶段提示
│   │   ├── hypothesis.py      # Hypothesis 阶段提示
│   │   ├── verification.py    # Verification 阶段提示
│   │   └── templates/         # 模板文件目录
│   │       ├── perception.yaml
│   │       ├── hypothesis.yaml
│   │       └── verification.yaml
│   │
│   ├── config/                # 配置管理
│   │   ├── __init__.py
│   │   ├── settings.py        # Pydantic Settings
│   │   ├── schema.py          # 配置 Schema
│   │   └── loader.py          # 配置加载器
│   │
│   ├── utils/                 # 工具函数
│   │   ├── __init__.py
│   │   ├── image.py           # 图像处理工具
│   │   ├── logging.py         # 日志配置
│   │   ├── cache.py           # 缓存工具
│   │   └── retry.py           # 重试装饰器
│   │
│   └── cli.py                 # 命令行接口
│
├── tests/                     # 测试目录
│   ├── __init__.py
│   ├── conftest.py           # pytest 配置和 fixtures
│   ├── unit/                 # 单元测试
│   │   ├── test_agent.py
│   │   ├── test_models.py
│   │   ├── test_tools.py
│   │   └── test_prompts.py
│   ├── integration/          # 集成测试
│   │   ├── test_phrv_flow.py
│   │   └── test_end_to_end.py
│   └── fixtures/             # 测试数据
│       ├── images/
│       └── mock_responses/
│
├── examples/                  # 示例代码
│   ├── basic_usage.py        # 基础使用示例
│   ├── custom_tools.py       # 自定义工具示例
│   ├── custom_scenario.py    # 自定义场景示例
│   └── api_server.py         # API 服务示例
│
├── docs/                      # 文档目录
│   ├── api/                   # API 文档
│   │   └── README.md
│   └── guides/                # 指南文档
│       ├── quickstart.md
│       ├── configuration.md
│       ├── custom_tools.md
│       ├── scenario_extensions.md
│       └── deployment.md
│
├── scripts/                   # 工具脚本
│   ├── setup_models.py       # 模型下载和设置
│   ├── download_geoclip.py   # GeoCLIP 模型下载
│   └── setup_dev_env.sh      # 开发环境设置
│
├── .github/                   # GitHub 配置
│   ├── workflows/            # CI/CD 工作流
│   │   ├── test.yml
│   │   └── release.yml
│   └── ISSUE_TEMPLATE/       # Issue 模板
│
├── pyproject.toml            # 项目配置和依赖
├── README.md                 # 项目说明
├── GUIDE.md                  # 技术设计文档
├── ARCHITECTURE.md           # 架构文档
├── CONTRIBUTING.md           # 贡献指南
├── PROJECT_STRUCTURE.md      # 本文件
├── LICENSE                   # 许可证
└── env.example               # 环境变量示例
```

## 模块说明

### `geomind/agent/`

Agent 核心模块，实现 PHRV 流程。

- **`graph.py`**: 使用 LangGraph 定义状态图和节点连接
- **`nodes.py`**: 各阶段节点的具体实现
- **`state.py`**: 使用 Pydantic 定义状态 Schema

### `geomind/models/`

模型抽象层，提供统一的模型接口。

- **`base.py`**: 定义模型基类接口
- **`vlm.py`**: VLM 模型封装，支持多种提供商
- **`geoclip.py`**: GeoCLIP 模型封装
- **`llm.py`**: LLM 模型封装，支持 OpenAI、Anthropic 等

### `geomind/tools/`

工具系统，包括 MCP 工具和沙盒工具。

- **`mcp/`**: MCP 协议工具实现
- **`sandbox.py`**: 沙盒执行环境
- **`registry.py`**: 工具注册和管理

### `geomind/prompts/`

提示模板管理，支持动态加载和版本控制。

- **`templates/`**: YAML 格式的模板文件
- 各阶段提示类：封装模板逻辑

### `geomind/config/`

配置管理，使用 Pydantic Settings。

- **`settings.py`**: 从环境变量和文件加载配置
- **`schema.py`**: 配置数据模型

## 代码组织原则

1. **模块化**: 每个模块职责单一，接口清晰
2. **可扩展**: 通过接口和基类支持扩展
3. **类型安全**: 使用 Pydantic 和类型注解
4. **测试友好**: 依赖注入，易于 mock
5. **文档完善**: 每个模块和函数都有文档字符串

## 命名规范

- **模块名**: 小写，下划线分隔 (`snake_case`)
- **类名**: 大驼峰 (`PascalCase`)
- **函数/变量名**: 小写，下划线分隔 (`snake_case`)
- **常量**: 全大写，下划线分隔 (`UPPER_SNAKE_CASE`)

## 导入规范

```python
# 标准库
import os
from typing import List, Optional

# 第三方库
from langchain import ...
from pydantic import ...

# 本地模块
from geomind.models import BaseVLM
from geomind.tools import ToolRegistry
```

## 扩展指南

### 添加新模型

1. 在 `geomind/models/` 创建新文件
2. 继承 `BaseVLM` 或 `BaseLLM`
3. 实现必需的方法
4. 在配置中添加支持

### 添加新工具

1. 在 `geomind/tools/mcp/` 创建工具文件
2. 实现工具函数
3. 使用 `@register_tool` 装饰器注册
4. 在文档中说明用法

### 添加新场景

1. 继承 `BaseAgent`
2. 重写相关节点方法
3. 创建场景特定的提示模板
4. 编写示例代码

详细扩展指南请参考各模块的文档。

