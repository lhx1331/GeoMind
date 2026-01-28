# GeoMind API Keys 和配置资源清单

本文档列出了运行 GeoMind 所需的所有 API keys 和配置资源。

## 📋 配置检查清单

### ✅ 核心 AI 模型 (必需)

#### 1. LLM (大语言模型) - 选择一个

- [ ] **OpenAI**
  - API Key: `OPENAI_API_KEY`
  - 申请地址: https://platform.openai.com/api-keys
  - 推荐模型: `gpt-4-turbo-preview`, `gpt-4o`
  - 预估成本: $10-50/月

- [ ] **DeepSeek** ⭐ 推荐性价比之选
  - API Key: `DEEPSEEK_API_KEY`
  - 申请地址: https://platform.deepseek.com/
  - 推荐模型: `deepseek-chat`
  - 预估成本: $1-5/月 (约 GPT-4 的 1/50)

- [ ] **Anthropic Claude**
  - API Key: `ANTHROPIC_API_KEY`
  - 申请地址: https://console.anthropic.com/
  - 推荐模型: `claude-3-opus-20240229`, `claude-3-5-sonnet`
  - 预估成本: $15-60/月

- [ ] **本地 LLM** (免费但需要硬件)
  - 部署方式: Ollama, vLLM, LocalAI
  - 推荐模型: Qwen2.5, Llama-3, Mistral
  - 硬件要求: 8GB+ VRAM (GPU)

#### 2. VLM (视觉语言模型) - 必需，选择一个

- [ ] **OpenAI Vision** ⭐ 全球推荐
  - API Key: `VLM_OPENAI_API_KEY`
  - 申请地址: https://platform.openai.com/api-keys
  - 推荐模型: `gpt-4o`, `gpt-4-vision-preview`
  - 预估成本: $40-80/月

- [ ] **Anthropic Claude 3** (视觉支持)
  - API Key: `VLM_ANTHROPIC_API_KEY`
  - 申请地址: https://console.anthropic.com/
  - 推荐模型: `claude-3-opus-20240229`
  - 预估成本: $50-100/月

- [ ] **Google Gemini Pro Vision**
  - API Key: `VLM_GOOGLE_API_KEY`
  - 申请地址: https://makersuite.google.com/app/apikey
  - 推荐模型: `gemini-pro-vision`
  - 预估成本: $20-40/月

- [ ] **阿里云通义千问 VL** ⭐ 国内推荐
  - API Key: `VLM_QWEN_API_KEY`
  - 申请地址: https://dashscope.aliyun.com/
  - 推荐模型: `qwen-vl-max`
  - 预估成本: ¥50-100/月

- [ ] **智谱 AI GLM-4V** (性价比)
  - API Key: `VLM_GLM_API_KEY`
  - 申请地址: https://open.bigmodel.cn/
  - 推荐模型: `glm-4v`
  - 预估成本: ¥30-80/月

- [ ] **本地 VLM** (免费但需硬件)
  - 推荐模型: LLaVA-v1.6-34B, Qwen-VL-Chat, CogVLM
  - 部署方式: Ollama, vLLM
  - 硬件要求: 16-24GB VRAM (GPU)

#### 3. GeoCLIP (地理检索模型) - 必需

- [ ] **模型文件下载**
  - 下载地址: https://github.com/VicenteVivan/geo-clip
  - Hugging Face: `geolocal/StreetCLIP`
  - 存储路径: `./models/geoclip`
  - 硬件要求: 4GB+ VRAM (推荐 GPU)

### ✅ 地理服务 API

#### 4. 地理编码 (Geocoding)

- [ ] **Google Maps API** ⭐ 推荐
  - API Key: `GOOGLE_API_KEY`
  - 申请地址: https://console.cloud.google.com/
  - 需要启用: Geocoding API, Places API
  - 免费额度: $200/月
  - 预估成本: $0-20/月

- [ ] **Nominatim** (免费替代)
  - 无需 API Key
  - 基于 OpenStreetMap
  - 限制: 请求频率限制

#### 5. POI 搜索

- [ ] **Google Places API**
  - API Key: 与 Google Maps API 共用
  - 需要启用: Places API

- [ ] **Overpass API** (免费)
  - 无需 API Key
  - 基于 OpenStreetMap
  - URL: `https://overpass-api.de/api/interpreter`

### ✅ 沙盒执行环境 (可选)

#### 6. 代码沙盒

- [ ] **E2B** (云沙盒，生产推荐)
  - API Key: `E2B_API_KEY`
  - 申请地址: https://e2b.dev/
  - 免费额度: 有
  - 预估成本: $0-10/月

- [ ] **Docker** (本地沙盒，开发推荐)
  - 安装 Docker Desktop
  - 无需 API Key

- [ ] **Local** (本地子进程，仅测试)
  - 无需配置
  - ⚠️ 安全性低

---

## 💰 成本方案对比

### 方案 1: 最低成本 (完全免费)

```bash
# LLM: 本地 Ollama + Qwen2.5
# VLM: 本地 Ollama + LLaVA
# GeoCLIP: 本地部署
# 地理服务: Nominatim + Overpass (免费)
# 沙盒: Local

总成本: $0/月
硬件要求: 16GB+ VRAM GPU
```

### 方案 2: 性价比推荐 ⭐

```bash
# LLM: DeepSeek ($2/月)
# VLM: Google Gemini ($20/月) 或 智谱 GLM-4V (¥30/月)
# GeoCLIP: 本地部署
# 地理服务: Google Maps (免费额度内) 或 Nominatim (免费)
# 沙盒: Docker (免费)

总成本: ~$25/月 (或 ¥50/月国内方案)
硬件要求: 4GB+ VRAM GPU (仅 GeoCLIP)
```

### 方案 2-国内版: 国内用户推荐 🇨🇳

```bash
# LLM: DeepSeek (¥10/月)
# VLM: 阿里云通义千问 VL (¥80/月)
# GeoCLIP: 本地部署
# 地理服务: 高德/百度地图 API (免费额度)
# 沙盒: Docker (免费)

总成本: ~¥90/月
优势: 国内访问快，中文理解好
```

### 方案 3: 最佳性能

```bash
# LLM: OpenAI GPT-4 ($40/月)
# VLM: OpenAI GPT-4V ($60/月)
# GeoCLIP: 本地部署
# 地理服务: Google Maps ($10/月)
# 沙盒: E2B ($5/月)

总成本: ~$115/月
硬件要求: 4GB+ VRAM GPU (仅 GeoCLIP)
```

---

## 🚀 快速开始配置

### 最小配置 (开发测试)

创建 `.env` 文件：

```bash
# 使用 DeepSeek (性价比高)
DEEPSEEK_API_KEY=your_deepseek_key_here
DEFAULT_LLM_PROVIDER=deepseek

# 使用 OpenAI Vision
VLM_API_KEY=your_openai_key_here
VLM_PROVIDER=openai
VLM_MODEL=gpt-4o

# GeoCLIP 本地部署
GEOCLIP_MODEL_PATH=./models/geoclip
GEOCLIP_DEVICE=cuda

# 使用免费地理服务
GEOCODE_PROVIDER=nominatim
POI_SEARCH_PROVIDER=overpass

# 本地沙盒
SANDBOX_PROVIDER=local
```

### 完整配置 (生产环境)

```bash
# ============================================
# LLM 配置
# ============================================
# 使用 DeepSeek (推荐)
DEEPSEEK_API_KEY=your_deepseek_key_here
DEEPSEEK_MODEL=deepseek-chat
DEFAULT_LLM_PROVIDER=deepseek

# 或使用 OpenAI
# OPENAI_API_KEY=your_openai_key_here
# DEFAULT_LLM_PROVIDER=openai

# ============================================
# VLM 配置
# ============================================
VLM_PROVIDER=openai
VLM_API_KEY=your_openai_key_here
VLM_MODEL=gpt-4o

# ============================================
# GeoCLIP 配置
# ============================================
GEOCLIP_MODEL_PATH=./models/geoclip
GEOCLIP_DEVICE=cuda
GEOCLIP_TOP_K=5
GEOCLIP_CACHE_EMBEDDINGS=true

# ============================================
# 地理服务配置
# ============================================
# Google Maps (推荐)
GOOGLE_API_KEY=your_google_key_here
GEOCODE_PROVIDER=google
POI_SEARCH_PROVIDER=google

# 或使用免费服务
# GEOCODE_PROVIDER=nominatim
# POI_SEARCH_PROVIDER=overpass

# ============================================
# 沙盒配置
# ============================================
# 生产环境使用 E2B
E2B_API_KEY=your_e2b_key_here
SANDBOX_PROVIDER=e2b

# 开发环境使用 Docker
# SANDBOX_PROVIDER=docker

# ============================================
# Agent 配置
# ============================================
AGENT_MAX_ITERATIONS=5
AGENT_CONFIDENCE_THRESHOLD=0.7

# ============================================
# 日志配置
# ============================================
LOG_LEVEL=INFO
LOG_FORMAT=json
```

---

## 📝 配置验证

使用内置脚本验证配置：

```bash
python scripts/verify_setup.py
```

该脚本会检查：
- ✅ 所有 API keys 是否有效
- ✅ 模型文件是否存在
- ✅ 网络连接是否正常
- ✅ 依赖包是否安装

---

## 🔒 安全建议

1. **不要提交 .env 文件**
   - 已在 `.gitignore` 中配置
   - 使用 `.env.example` 作为模板

2. **使用环境变量管理工具**
   - 开发: `python-dotenv`
   - 生产: Docker secrets, Kubernetes secrets

3. **定期轮换 API Keys**
   - 建议每 3-6 个月更换一次

4. **设置 API 使用限额**
   - 在各服务商控制台设置月度预算
   - 防止意外高额费用

---

## ❓ 常见问题

### Q1: 必须使用付费 API 吗？

不必须。您可以使用完全免费的方案（本地模型 + 免费地理服务），但需要更强的硬件配置。

### Q2: DeepSeek 和 GPT-4 差别大吗？

在地理推理任务上，DeepSeek 约为 GPT-4 的 85-90% 准确率，但成本仅为 1/50，非常适合开发和中等规模应用。

### Q3: GeoCLIP 可以用 API 吗？

目前 GeoCLIP 需要本地部署。如果没有 GPU，可以使用 CPU 模式（会慢一些）。

### Q4: 如何降低成本？

- 使用 DeepSeek 替代 OpenAI
- 启用缓存减少重复请求
- 使用免费的地理服务
- 优化 prompt 减少 token 使用

---

## 📚 相关文档

- [DeepSeek 配置指南](./guides/deepseek_setup.md)
- [配置管理详解](./guides/configuration.md)
- [快速开始](./guides/quickstart.md)
- [部署指南](./guides/deployment.md)

---

**更新时间**: 2024-12-19  
**版本**: v1.0

