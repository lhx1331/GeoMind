# VLM (视觉语言模型) 提供商指南

GeoMind 支持多个主流的 VLM 提供商，您可以根据需求、预算和地区选择合适的服务。

## 📊 提供商对比

| 提供商 | 推荐模型 | 月成本 | 优势 | 劣势 | 适用场景 |
|--------|---------|--------|------|------|---------|
| **OpenAI** | gpt-4o | $40-80 | 性能最强，响应快 | 价格较高 | 生产环境，高精度要求 |
| **Anthropic** | claude-3-opus | $50-100 | 输出详细，安全性高 | 价格高，速度较慢 | 需要详细推理 |
| **Google** | gemini-pro-vision | $20-40 | 性价比好，免费额度 | 国内访问受限 | 全球部署 |
| **通义千问** | qwen-vl-max | ¥50-100 | 中文理解好，国内快 | 英文稍弱 | 国内部署，中文任务 |
| **智谱 AI** | glm-4v | ¥30-80 | 性价比高，中文好 | 生态较小 | 国内中小项目 |
| **本地部署** | llava-v1.6 | 免费 | 完全控制，无限制 | 需要硬件，维护成本 | 隐私要求高 |

---

## 1️⃣ OpenAI GPT-4V / GPT-4o

### 特点
- ✅ **性能最强**: 业界标杆，准确率最高
- ✅ **响应快速**: 通常 2-5 秒
- ✅ **API 稳定**: 99.9% 可用性
- ❌ **价格较高**: 相对其他方案

### 配置

```bash
# .env 配置
VLM_PROVIDER=openai
VLM_OPENAI_API_KEY=sk-...
VLM_OPENAI_MODEL=gpt-4o  # 或 gpt-4-vision-preview
VLM_OPENAI_BASE_URL=https://api.openai.com/v1
```

### 可用模型

| 模型 | 说明 | 适用场景 |
|------|------|---------|
| `gpt-4o` | 最新多模态模型，速度快 | **推荐**，综合性能最佳 |
| `gpt-4-vision-preview` | 较早的视觉模型 | 稳定性要求高 |
| `gpt-4-turbo` | Turbo 版本，更快 | 高并发场景 |

### 定价
- **输入**: $0.01/1K tokens (图像计费复杂，约 $0.003/张)
- **输出**: $0.03/1K tokens

---

## 2️⃣ Anthropic Claude 3

### 特点
- ✅ **输出详细**: 推理过程详细
- ✅ **安全性高**: 内容过滤强
- ✅ **上下文长**: 支持 200K tokens
- ❌ **速度较慢**: 响应时间 5-10 秒
- ❌ **价格最高**: 比 GPT-4 略贵

### 配置

```bash
# .env 配置
VLM_PROVIDER=anthropic
VLM_ANTHROPIC_API_KEY=sk-ant-...
VLM_ANTHROPIC_MODEL=claude-3-opus-20240229
VLM_ANTHROPIC_BASE_URL=https://api.anthropic.com
```

### 可用模型

| 模型 | 说明 | 价格 |
|------|------|------|
| `claude-3-opus-20240229` | 最强模型，准确率接近 GPT-4o | $$$ |
| `claude-3-sonnet-20240229` | 平衡性能与成本 | $$ |
| `claude-3-haiku-20240307` | 最快最便宜 | $ |

### 申请地址
- https://console.anthropic.com/

---

## 3️⃣ Google Gemini Pro Vision

### 特点
- ✅ **性价比高**: 比 GPT-4 便宜 50%
- ✅ **免费额度**: 每月 60 次免费调用
- ✅ **多模态**: 原生支持视觉
- ❌ **国内访问**: 需要代理
- ❌ **稳定性**: 偶尔不稳定

### 配置

```bash
# .env 配置
VLM_PROVIDER=google
VLM_GOOGLE_API_KEY=AIza...
VLM_GOOGLE_MODEL=gemini-pro-vision
VLM_GOOGLE_BASE_URL=https://generativelanguage.googleapis.com
```

### 可用模型

| 模型 | 说明 |
|------|------|
| `gemini-pro-vision` | 视觉理解 |
| `gemini-1.5-pro` | 最新版本，性能更强 |

### 申请地址
- https://makersuite.google.com/app/apikey

---

## 4️⃣ 阿里云通义千问 VL

### 特点
- ✅ **中文优秀**: 中文场景最优
- ✅ **国内快速**: 国内访问速度快
- ✅ **价格合理**: 比国外便宜
- ✅ **符合规范**: 符合国内监管
- ❌ **英文稍弱**: 英文场景不如 GPT-4

### 配置

```bash
# .env 配置
VLM_PROVIDER=qwen
VLM_QWEN_API_KEY=sk-...
VLM_QWEN_MODEL=qwen-vl-max
VLM_QWEN_BASE_URL=https://dashscope.aliyuncs.com/api/v1
```

### 可用模型

| 模型 | 说明 | 价格 |
|------|------|------|
| `qwen-vl-max` | 最强版本 | ¥0.02/1K tokens |
| `qwen-vl-plus` | 平衡版本 | ¥0.008/1K tokens |
| `qwen-vl-chat` | 基础版本 | 免费（有限制） |

### 申请地址
- https://dashscope.aliyun.com/

---

## 5️⃣ 智谱 AI GLM-4V

### 特点
- ✅ **性价比高**: 国产最便宜之一
- ✅ **中文友好**: 中文理解好
- ✅ **响应快**: 国内速度快
- ❌ **生态小**: 社区和文档较少

### 配置

```bash
# .env 配置
VLM_PROVIDER=glm
VLM_GLM_API_KEY=...
VLM_GLM_MODEL=glm-4v
VLM_GLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4
```

### 可用模型

| 模型 | 说明 |
|------|------|
| `glm-4v` | 视觉理解模型 |
| `glm-4v-plus` | 增强版本（如果有） |

### 申请地址
- https://open.bigmodel.cn/

---

## 6️⃣ 本地部署 VLM

### 推荐模型

| 模型 | 参数量 | VRAM 需求 | 性能 |
|------|--------|-----------|------|
| **LLaVA-v1.6-34B** | 34B | 24GB | ⭐⭐⭐⭐ |
| **Qwen-VL-Chat** | 7B | 16GB | ⭐⭐⭐ |
| **CogVLM** | 17B | 20GB | ⭐⭐⭐⭐ |
| **MiniGPT-4** | 7B | 12GB | ⭐⭐ |

### 部署方式

#### 使用 Ollama (推荐)

```bash
# 安装 Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 拉取模型
ollama pull llava:34b

# 启动服务（自动）
# Ollama 默认在 http://localhost:11434 运行
```

配置 GeoMind:

```bash
VLM_PROVIDER=local
VLM_LOCAL_BASE_URL=http://localhost:11434/v1
VLM_LOCAL_MODEL=llava:34b
VLM_LOCAL_API_KEY=not-needed
```

#### 使用 vLLM

```bash
# 安装 vLLM
pip install vllm

# 启动服务
python -m vllm.entrypoints.openai.api_server \
  --model liuhaotian/llava-v1.6-34b \
  --port 8001
```

配置:

```bash
VLM_LOCAL_BASE_URL=http://localhost:8001/v1
VLM_LOCAL_MODEL=liuhaotian/llava-v1.6-34b
```

---

## 🎯 选择建议

### 场景 1: 生产环境，追求最高准确率
```bash
推荐: OpenAI GPT-4o
成本: $60-80/月
配置: VLM_PROVIDER=openai
```

### 场景 2: 国内部署，中文为主
```bash
推荐: 阿里云通义千问 VL
成本: ¥50-100/月
配置: VLM_PROVIDER=qwen
```

### 场景 3: 预算有限，性价比优先
```bash
推荐: Google Gemini + 智谱 GLM-4V
成本: $20-30/月
配置: VLM_PROVIDER=google 或 glm
```

### 场景 4: 隐私要求高，本地部署
```bash
推荐: Ollama + LLaVA
成本: 免费（硬件成本）
配置: VLM_PROVIDER=local
硬件: 24GB+ VRAM GPU
```

---

## 🔄 切换 VLM 提供商

GeoMind 支持在运行时动态切换 VLM:

```python
from geomind.models.vlm import create_vlm

# 使用 OpenAI
vlm_openai = create_vlm(provider="openai")

# 使用阿里云
vlm_qwen = create_vlm(provider="qwen")

# 使用本地模型
vlm_local = create_vlm(provider="local")
```

或通过环境变量:

```bash
# 临时切换到通义千问
export VLM_PROVIDER=qwen
python main.py
```

---

## 💡 性能优化建议

### 1. 启用缓存
```bash
ENABLE_CACHE=true
CACHE_TTL=3600  # 1小时
```

### 2. 图像预处理
```python
from geomind.utils.image import load_image, resize_image

# 压缩大图片减少 token 消耗
image = load_image("large_image.jpg")
image = resize_image(image, max_size=1024)
```

### 3. 批量处理
```python
# 对多张图片使用批量 API
results = await vlm.batch_analyze(
    images=[img1, img2, img3],
    prompts=["Analyze this"]*3
)
```

---

## 🔒 安全和合规

### API Key 安全
- ✅ 使用环境变量，不要硬编码
- ✅ 定期轮换 API Keys
- ✅ 设置 API 用量限制

### 数据隐私
- OpenAI/Anthropic: 数据可能用于训练（可选择 opt-out）
- Google: 遵循 Google 隐私政策
- 国内厂商: 符合国内数据安全法规
- 本地部署: 完全控制数据

### 内容审核
- 所有厂商都有内容审核机制
- 敏感内容可能被拒绝
- 建议在业务层添加预审核

---

## ❓ 常见问题

### Q1: 如何选择最适合的 VLM？

**回答**: 
- 预算充足 + 全球部署 → OpenAI GPT-4o
- 国内部署 + 中文为主 → 阿里云通义千问
- 预算有限 → Google Gemini 或 智谱 GLM-4V
- 隐私敏感 → 本地部署 LLaVA

### Q2: 本地 VLM 性能如何？

**回答**: LLaVA-34B 约为 GPT-4V 的 70-80% 准确率，但完全免费且无限制。

### Q3: 可以混合使用多个 VLM 吗？

**回答**: 可以！GeoMind 支持配置多个 VLM 并动态切换：

```python
# 主 VLM: OpenAI (高准确率)
primary_vlm = create_vlm(provider="openai")

# 备用 VLM: 通义千问 (降本)
backup_vlm = create_vlm(provider="qwen")

try:
    result = await primary_vlm.analyze_image(image)
except Exception:
    result = await backup_vlm.analyze_image(image)
```

### Q4: 如何降低 VLM 成本？

**建议**:
1. 启用缓存（相同图片不重复调用）
2. 图片预处理（压缩分辨率）
3. 使用更便宜的模型（如 Claude Haiku, Qwen-VL-Plus）
4. 混合策略（简单任务用便宜模型）

---

## 📚 相关文档

- [DeepSeek 配置指南](./deepseek_setup.md)
- [API Keys 配置清单](../API_KEYS_CHECKLIST.md)
- [配置管理详解](./configuration.md)
- [快速开始](./quickstart.md)

---

**更新时间**: 2024-12-19  
**版本**: v1.0

