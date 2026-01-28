# API 参考

GeoMind 提供简洁的 Python API 和命令行接口。

## 核心 API

### GeoMindAgent

主要的 Agent 类，封装了完整的 PHRV 流程。

```python
from geomind import GeoMindAgent

agent = GeoMindAgent(
    llm_provider="openai",
    vlm_provider="openai",
    geoclip_model_path="./models/geoclip",
    config_file="config.yaml"
)
```

#### 方法

##### `geolocate(image_path, max_iterations=None, confidence_threshold=None)`

执行地理定位任务。

**参数:**
- `image_path` (str | Path): 图片路径
- `max_iterations` (int, optional): 最大迭代次数
- `confidence_threshold` (float, optional): 置信度阈值

**返回:**
- `GeolocationResult`: 包含定位结果和证据链

**示例:**
```python
result = agent.geolocate("photo.jpg")
print(result.final.answer)
```

## 数据模型

### GeolocationResult

定位结果对象。

**属性:**
- `clues`: 感知线索
- `hypotheses`: 地理假设
- `candidates`: 候选地点
- `evidence`: 验证证据
- `final`: 最终结果

### FinalResult

最终结果对象。

**属性:**
- `answer`: 地点名称
- `confidence`: 置信度 (0-1)
- `why`: 支持证据
- `why_not`: 排除原因

详细 API 文档请参考各模块的 docstring。

