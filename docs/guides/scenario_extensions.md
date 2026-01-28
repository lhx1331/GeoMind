# 场景扩展指南

本指南说明如何基于 GeoMind 框架扩展新的应用场景。

## 扩展流程

### 1. 定义场景特定的状态

继承基础状态并添加场景特定字段：

```python
from geomind.agent.state import AgentState
from typing import TypedDict, List

class ECommerceState(AgentState):
    """电商场景状态"""
    product_features: List[dict]  # 商品特征
    product_categories: List[str]  # 商品类别
    product_candidates: List[dict]  # 候选商品
    price_comparison: dict  # 价格比较
```

### 2. 实现场景特定的节点

```python
from geomind.agent.nodes.base import BaseNode

class ExtractProductFeaturesNode(BaseNode):
    """提取商品特征节点"""
    
    async def execute(self, state: ECommerceState) -> ECommerceState:
        # 使用 VLM 分析商品图片
        image = state.input_image
        features = await self.vlm.analyze_product(image)
        
        state.product_features = features
        return state
```

### 3. 创建场景特定的提示模板

```yaml
# prompts/templates/ecommerce_hypothesis.yaml
system: |
  你是一个电商推荐专家。根据商品特征，生成可能的商品类别假设。
  
  输出格式：
  {
    "categories": ["类别1", "类别2"],
    "rationale": "假设依据"
  }

examples:
  - input: "红色，圆形，有屏幕"
    output: |
      {
        "categories": ["智能手表", "运动手环"],
        "rationale": "红色圆形带屏幕的设备可能是智能手表或运动手环"
      }
```

### 4. 注册场景特定的工具

```python
@register_tool(
    name="search_products",
    description="搜索电商平台商品"
)
def search_products(query: str, category: str) -> ToolResult:
    """搜索商品"""
    # 调用电商 API
    pass
```

### 5. 构建场景特定的 Agent

```python
from geomind.agent import BaseAgent
from langgraph.graph import StateGraph

class ECommerceAgent(BaseAgent):
    """电商推荐 Agent"""
    
    def build_graph(self) -> StateGraph:
        graph = StateGraph(ECommerceState)
        
        # 添加场景特定节点
        graph.add_node("extract_features", ExtractProductFeaturesNode())
        graph.add_node("generate_categories", GenerateCategoriesNode())
        graph.add_node("search_products", SearchProductsNode())
        graph.add_node("compare_products", CompareProductsNode())
        graph.add_node("finalize", FinalizeNode())
        
        # 定义流程
        graph.set_entry_point("extract_features")
        graph.add_edge("extract_features", "generate_categories")
        graph.add_edge("generate_categories", "search_products")
        graph.add_edge("search_products", "compare_products")
        graph.add_edge("compare_products", "finalize")
        
        return graph.compile()
```

## 场景示例

### 示例 1: 电商商品推荐

**流程**:
1. Perception: 提取商品特征（颜色、形状、材质等）
2. Hypothesis: 生成商品类别假设
3. Retrieval: 搜索候选商品
4. Verification: 比较价格、评价、规格

**实现要点**:
- 自定义商品特征提取提示
- 集成电商平台 API
- 实现商品比较逻辑

### 示例 2: 科学论文检索

**流程**:
1. Perception: 提取论文摘要关键词
2. Hypothesis: 生成研究领域假设
3. Retrieval: 搜索候选论文
4. Verification: 核查引用次数和匹配度

**实现要点**:
- 文本分析替代图像分析
- 集成学术搜索 API（如 arXiv、PubMed）
- 实现相关性评分

### 示例 3: 医疗影像辅助

**流程**:
1. Perception: 提取影像特征和患者数据
2. Hypothesis: 生成潜在诊断
3. Retrieval: 查询医学数据库
4. Verification: 核查临床指南和标准

**实现要点**:
- 医疗影像特征提取
- 集成医学知识库
- 实现诊断验证逻辑
- **注意**: 需要严格的隐私和安全措施

## 通用扩展模式

所有场景扩展都遵循以下模式：

```
输入 → Perception → Hypothesis → Retrieval → Verification → 输出
  ↓        ↓            ↓            ↓            ↓          ↓
特定化   特定化       特定化       特定化       特定化    特定化
```

只需替换各阶段的实现，框架保持不变。

## 最佳实践

1. **保持接口一致**: 节点接口应遵循基类定义
2. **模块化设计**: 每个阶段独立实现，便于测试
3. **配置驱动**: 使用配置文件管理场景参数
4. **文档完善**: 为每个场景编写使用文档
5. **测试覆盖**: 为场景特定逻辑编写测试

## 场景模板

我们提供了场景扩展模板，可以快速开始：

```bash
# 使用模板创建新场景
python scripts/create_scenario.py --name my_scenario

# 这会创建：
# - geomind/scenarios/my_scenario/
# - 基础节点实现
# - 提示模板
# - 示例代码
```

详细实现请参考 `examples/custom_scenario.py`。

