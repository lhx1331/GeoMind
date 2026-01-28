# 技术架构文档

## 技术栈选择

### 核心框架

#### LangGraph
- **版本**: >= 0.0.20
- **用途**: 状态管理和流程编排
- **优势**: 
  - 原生支持循环和条件分支
  - 状态持久化机制完善
  - 与 LangChain 生态无缝集成
  - 支持可观测性和调试

#### LangChain
- **版本**: >= 0.1.0
- **用途**: Agent 基础框架
- **优势**:
  - 丰富的模型集成（OpenAI、Anthropic 等）
  - 统一的工具调用接口
  - 完善的提示模板管理

#### Pydantic
- **版本**: >= 2.5.0
- **用途**: 数据验证和状态 Schema
- **优势**:
  - 类型安全的状态定义
  - 自动数据验证
  - JSON Schema 生成

### 模型集成

#### VLM (视觉模型)
- **支持**: LLaVA, Qwen-VL, GPT-4V
- **接口**: OpenAI 兼容 API (`/v1/chat/completions`)
- **部署**: 支持托管服务和自部署

#### GeoCLIP
- **用途**: 地理图像检索
- **特点**: 90M 参数，支持 CPU/GPU
- **集成**: 通过 Python 包直接调用

#### LLM
- **支持**: OpenAI, Anthropic, 本地模型
- **接口**: LangChain 统一接口

### 工具系统

#### MCP (Model Context Protocol)
- **用途**: 工具注册和调用
- **优势**: 标准化工具接口，易于扩展

#### 沙盒执行
- **选项**: E2B, Docker, 本地进程
- **安全**: 网络隔离、资源限制

### 其他组件

- **FastAPI**: API 服务（可选）
- **Structlog**: 结构化日志
- **Rich**: 终端输出美化
- **Tenacity**: 重试机制

## 架构设计

### 分层架构

```
┌─────────────────────────────────────┐
│      API Layer (FastAPI/CLI)        │
├─────────────────────────────────────┤
│      Agent Layer (LangGraph)         │
│  ┌───────────────────────────────┐  │
│  │  PHRV Nodes                   │  │
│  │  - Perception                  │  │
│  │  - Hypothesis                  │  │
│  │  - Retrieval                   │  │
│  │  - Verification                │  │
│  └───────────────────────────────┘  │
├─────────────────────────────────────┤
│      Component Layer                │
│  ┌──────────┬──────────┬─────────┐ │
│  │ Models   │ Tools    │ Prompts │ │
│  └──────────┴──────────┴─────────┘ │
├─────────────────────────────────────┤
│      Infrastructure Layer           │
│  ┌──────────┬──────────┬─────────┐ │
│  │ Config   │ Logging  │ Cache   │ │
│  └──────────┴──────────┴─────────┘ │
└─────────────────────────────────────┘
```

### 数据流

```
Image Input
    ↓
[Perception Node]
    ↓ (clues)
[Hypothesis Node]
    ↓ (hypotheses)
[Retrieval Node]
    ↓ (candidates)
[Verification Node]
    ↓ (evidence)
[Finalize Node]
    ↓
Final Result
```

### 状态管理

使用 LangGraph 的 `StateGraph` 管理状态：

```python
from typing import TypedDict
from langgraph.graph import StateGraph

class AgentState(TypedDict):
    clues: Clues
    hypotheses: List[Hypothesis]
    candidates: List[Candidate]
    evidence: List[Evidence]
    final: Optional[FinalResult]
```

## 扩展点

### 1. 自定义模型

实现模型接口即可替换：

```python
from geomind.models.base import BaseVLM

class CustomVLM(BaseVLM):
    def analyze(self, image: Image) -> Clues:
        # 实现自定义逻辑
        pass
```

### 2. 自定义工具

通过 MCP 注册新工具：

```python
from geomind.tools import register_tool

@register_tool
def custom_geocode(text: str) -> Coordinates:
    # 实现自定义地理编码
    pass
```

### 3. 自定义场景

继承基础 Agent 并重写节点：

```python
from geomind.agent import BaseAgent

class CustomAgent(BaseAgent):
    def perception_node(self, state):
        # 自定义感知逻辑
        pass
```

## 性能优化

### 1. 缓存策略
- GeoCLIP 嵌入缓存
- API 响应缓存
- 状态快照缓存

### 2. 并发处理
- 异步工具调用
- 批量候选验证
- 并行模型推理

### 3. 资源管理
- 模型懒加载
- 连接池复用
- GPU 内存管理

## 安全考虑

### 1. 沙盒隔离
- 网络访问限制
- 文件系统隔离
- 资源限制（CPU、内存）

### 2. 输入验证
- 图片格式验证
- 参数类型检查
- 大小限制

### 3. 输出过滤
- 敏感信息过滤
- 位置精度降级
- 隐私保护

## 监控和日志

### 1. 结构化日志
使用 Structlog 记录：
- 状态转换
- 工具调用
- 错误信息

### 2. 指标收集
- 请求延迟
- 成功率
- 资源使用

### 3. 追踪
- 请求 ID 追踪
- 状态快照
- 调试信息

## 部署架构

### 开发环境
```
Local Machine
├── Python 3.10+
├── GeoCLIP (CPU)
└── Local LLM (可选)
```

### 生产环境
```
API Gateway
    ↓
GeoMind Service
├── VLM Service (GPU)
├── GeoCLIP Service (GPU)
├── LLM Service (API)
└── MCP Tools Service
```

### 容器化
- Docker 镜像
- Kubernetes 部署
- 服务发现和负载均衡

详细部署指南请参考 [部署文档](docs/guides/deployment.md)。

