# 智谱 GLM-4V 快速配置指南

## ⚠️ 首先：API Key 安全

**如果您刚才在对话中提供了真实的 API Key，请立即采取行动：**

### 🚨 紧急步骤：重置您的 API Key

1. **访问智谱 AI 控制台**
   - 地址: https://open.bigmodel.cn/usercenter/apikeys

2. **删除已暴露的 Key**
   - 在 API Keys 列表中找到您的 Key
   - 点击"删除"按钮

3. **创建新的 API Key**
   - 点击"创建新的 API Key"
   - 复制新生成的 Key（只显示一次！）

4. **安全存储**
   - 保存到密码管理器（如 1Password, LastPass）
   - 或安全的本地文件

### 🔒 安全最佳实践

- ✅ **使用环境变量**: 将 Key 存在 `.env` 文件中
- ✅ **添加到 .gitignore**: 确保不会提交到代码库
- ✅ **定期轮换**: 每 3-6 个月更换 API Key
- ✅ **设置预算**: 在控制台设置月度消费限额
- ❌ **永远不要**: 在聊天、文档、代码中直接写入 Key
- ❌ **永远不要**: 将 Key 提交到 Git 仓库

---

## 🚀 配置步骤

### Step 1: 创建配置文件

在项目根目录创建 `.env` 文件（如果不存在）：

```bash
# Windows PowerShell
New-Item -Path .env -ItemType File -Force

# Linux/macOS
touch .env
```

### Step 2: 填写配置

将以下内容复制到 `.env` 文件：

```bash
# ============================================
# VLM 配置 - 智谱 GLM-4V
# ============================================
VLM_PROVIDER=glm
VLM_GLM_API_KEY=你的新API_Key
VLM_GLM_MODEL=glm-4v
VLM_GLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4

# ============================================
# LLM 配置 - DeepSeek (推荐)
# ============================================
DEEPSEEK_API_KEY=你的DeepSeek_Key
DEFAULT_LLM_PROVIDER=deepseek

# ============================================
# GeoCLIP 配置
# ============================================
GEOCLIP_MODEL_PATH=./models/geoclip
GEOCLIP_DEVICE=cuda

# ============================================
# 其他配置 (可选)
# ============================================
GEOCODE_PROVIDER=nominatim
POI_SEARCH_PROVIDER=overpass
SANDBOX_PROVIDER=local
LOG_LEVEL=INFO
```

### Step 3: 验证配置

测试配置是否正确：

```python
# test_glm.py
import asyncio
from geomind.models.vlm import create_vlm

async def test_glm():
    # 创建 GLM VLM
    vlm = create_vlm(provider="glm")
    await vlm.initialize()
    
    # 测试图像分析
    result = await vlm.analyze_image(
        image="./test_image.jpg",
        prompt="请描述这张图片"
    )
    
    print("✅ GLM-4V 配置成功！")
    print(f"响应: {result.data}")
    
    await vlm.cleanup()

# 运行测试
asyncio.run(test_glm())
```

运行测试：

```bash
python test_glm.py
```

---

## 📊 智谱 GLM-4V 特点

### 优势

- ✅ **性价比高**: 比国外模型便宜 60-80%
- ✅ **中文理解优秀**: 专为中文优化
- ✅ **国内访问快**: 无需代理，延迟低
- ✅ **API 简单**: 兼容 OpenAI 格式

### 定价

| 模型 | 输入价格 | 输出价格 | 图像价格 |
|------|---------|---------|---------|
| GLM-4V | ¥0.01/1K tokens | ¥0.01/1K tokens | ¥0.015/张 |

**预估月成本**: ¥30-80（取决于使用量）

### 可用模型

| 模型名称 | 说明 | 推荐场景 |
|---------|------|---------|
| `glm-4v` | 标准视觉模型 | 通用场景 |
| `glm-4v-plus` | 增强版（如可用） | 复杂场景 |

---

## 🔧 高级配置

### 调整参数优化性能

```bash
# .env
VLM_GLM_MODEL=glm-4v
VLM_TEMPERATURE=0.7  # 0.0-1.0，越低越确定
VLM_MAX_TOKENS=4096  # 最大输出长度
```

### 使用代码配置

```python
from geomind.models.vlm import VLM
from geomind.models.base import ModelConfig, ModelType

# 方式 1: 使用环境变量（推荐）
vlm = create_vlm(provider="glm")

# 方式 2: 代码中配置
config = ModelConfig(
    model_type=ModelType.VLM,
    model_name="glm-4v",
    api_key="你的API_Key",
    base_url="https://open.bigmodel.cn/api/paas/v4",
    temperature=0.7,
    max_tokens=4096
)
vlm = VLM(config=config, provider="glm")
```

---

## 🎯 完整示例：使用 GLM-4V 进行地理定位

```python
import asyncio
from geomind.models.vlm import create_vlm
from geomind.prompts.perception import (
    render_perception_prompt,
    parse_perception_output,
    convert_to_clues
)
from geomind.utils.image import load_image

async def geolocate_with_glm(image_path: str):
    """使用 GLM-4V 进行地理定位"""
    
    # 1. 加载图像
    image = load_image(image_path)
    
    # 2. 创建 GLM VLM
    vlm = create_vlm(provider="glm")
    await vlm.initialize()
    
    # 3. 生成感知提示
    prompt = render_perception_prompt()
    
    # 4. 分析图像
    print("🔍 使用 GLM-4V 分析图像...")
    response = await vlm.analyze_image(
        image=image,
        prompt=prompt
    )
    
    # 5. 解析结果
    perception_data = response.data
    clues = convert_to_clues(parse_perception_output(perception_data))
    
    # 6. 显示结果
    print("\n📝 提取的线索:")
    print(f"  OCR 文本: {len(clues.ocr)} 个")
    for ocr in clues.ocr[:3]:  # 显示前 3 个
        print(f"    - {ocr.text} (置信度: {ocr.confidence:.2f})")
    
    print(f"\n  视觉特征: {len(clues.visual)} 个")
    for vf in clues.visual[:3]:  # 显示前 3 个
        print(f"    - {vf.type}: {vf.value}")
    
    await vlm.cleanup()
    
    return clues

# 运行
if __name__ == "__main__":
    clues = asyncio.run(geolocate_with_glm("./your_image.jpg"))
```

---

## 💡 性能优化建议

### 1. 图像预处理

```python
from geomind.utils.image import resize_image

# GLM-4V 对分辨率不太敏感，可以压缩
image = resize_image(image, max_size=1024)
# 节省约 30-50% token 成本
```

### 2. 启用缓存

```bash
# .env
ENABLE_CACHE=true
CACHE_TTL=3600
```

相同图片不会重复调用 API。

### 3. 批量处理

```python
# 批量分析多张图片
images = [img1, img2, img3]
results = await vlm.batch_analyze(images, prompts)
```

---

## ❓ 常见问题

### Q1: API Key 格式是什么样的？

**A**: 智谱 API Key 格式通常是：
```
<32位字符>.<16位字符>
例如: abcd1234efgh5678ijkl9012mnop3456.QwErTyUiOpAs
```

### Q2: 如何查看我的用量和余额？

**A**: 
1. 访问: https://open.bigmodel.cn/usercenter/bill
2. 可查看实时用量和账户余额

### Q3: GLM-4V 支持哪些图片格式？

**A**: 
- ✅ 支持: JPG, PNG, WebP, GIF
- ✅ 最大尺寸: 20MB
- ✅ 建议分辨率: 1024x1024 以下

### Q4: 遇到 401 错误怎么办？

**A**: 
```
Error 401: Unauthorized
```

检查：
1. API Key 是否正确
2. API Key 是否已激活
3. 账户是否有余额
4. 是否已实名认证

### Q5: GLM-4V 和其他 VLM 如何切换？

**A**: 只需修改 `.env`:

```bash
# 切换到 GLM
VLM_PROVIDER=glm

# 切换到 OpenAI
VLM_PROVIDER=openai

# 切换到通义千问
VLM_PROVIDER=qwen
```

无需修改代码！

---

## 📈 成本控制

### 预算设置

在智谱 AI 控制台设置月度预算：
1. 访问: https://open.bigmodel.cn/usercenter/bill
2. 点击"预算管理"
3. 设置月度限额（如 ¥100）

### 监控用量

```python
# 在代码中记录 token 使用
response = await vlm.analyze_image(image, prompt)
print(f"Token 使用: {response.usage}")
```

---

## 🔗 相关链接

- [智谱 AI 官网](https://open.bigmodel.cn/)
- [GLM-4V 文档](https://open.bigmodel.cn/dev/api)
- [API Keys 管理](https://open.bigmodel.cn/usercenter/apikeys)
- [账单管理](https://open.bigmodel.cn/usercenter/bill)
- [GeoMind VLM 对比](../VLM_COMPARISON.md)

---

## 🆘 需要帮助？

如果遇到问题：

1. **查看日志**
   ```bash
   tail -f logs/geomind.log
   ```

2. **启用调试模式**
   ```bash
   LOG_LEVEL=DEBUG
   ```

3. **查看文档**
   - [VLM 提供商指南](./vlm_providers.md)
   - [API Keys 清单](../API_KEYS_CHECKLIST.md)

---

**更新时间**: 2024-12-19  
**作者**: GeoMind Team

