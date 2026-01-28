# VLM 提供商快速对比

## 📊 一表看懂：选哪个 VLM？

| 特征 | OpenAI | Anthropic | Google | 阿里云 | 智谱 AI | 本地 |
|------|--------|-----------|--------|--------|---------|------|
| **性能** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| **中文** | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **速度** | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ |
| **价格** | $$ | $$$ | $ | ¥ | ¥ | 免费 |
| **月成本** | $40-80 | $50-100 | $20-40 | ¥50-100 | ¥30-80 | $0 |
| **国内访问** | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ |
| **文档质量** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ |
| **API 稳定性** | 99.9% | 99.5% | 99% | 99% | 98% | - |

---

## 🎯 场景推荐

### 💼 生产环境 - 追求最佳性能
```
推荐: OpenAI GPT-4o
理由: 性能最强，API 最稳定
成本: $60-80/月
```

### 🇨🇳 国内部署 - 中文为主
```
推荐: 阿里云通义千问 VL
理由: 国内快，中文最优，合规
成本: ¥80/月
```

### 💰 预算有限 - 性价比优先
```
方案 A (国际): Google Gemini Pro Vision
成本: $25/月

方案 B (国内): 智谱 GLM-4V
成本: ¥40/月
```

### 🔒 隐私敏感 - 数据不出本地
```
推荐: Ollama + LLaVA-34B
成本: 免费
硬件: 24GB VRAM GPU
```

### 🌍 全球分布 - 多区域部署
```
推荐: OpenAI (全球) + 阿里云 (中国)
成本: $80 + ¥80 = 总计约 $90/月
```

---

## 💡 实战建议

### 混合策略（推荐）

```python
# 配置多个 VLM 实现降本增效
from geomind.models.vlm import create_vlm

# 主 VLM: OpenAI (高质量)
primary = create_vlm(provider="openai")

# 备用 1: 通义千问 (国内快)
backup_cn = create_vlm(provider="qwen")

# 备用 2: 本地 (离线/免费)
backup_local = create_vlm(provider="local")

async def smart_analyze(image):
    try:
        # 优先使用主 VLM
        return await primary.analyze_image(image)
    except Exception as e:
        # 降级到备用
        if is_in_china():
            return await backup_cn.analyze_image(image)
        else:
            return await backup_local.analyze_image(image)
```

### 分任务使用

```python
# 简单任务: 用便宜的模型
if task_complexity == "simple":
    vlm = create_vlm(provider="glm")  # 智谱 GLM-4V

# 复杂任务: 用强大的模型
elif task_complexity == "complex":
    vlm = create_vlm(provider="openai")  # GPT-4o

result = await vlm.analyze_image(image, prompt)
```

---

## 📈 成本优化

### 降低 70% 成本的 3 个技巧

#### 1. 启用智能缓存
```bash
# .env
ENABLE_CACHE=true
CACHE_TTL=3600  # 缓存 1 小时
```
**节省**: 重复图片不再调用 API，节省约 30-50%

#### 2. 图片预处理
```python
from geomind.utils.image import resize_image

# 压缩到合适大小（Vision 模型对超高分辨率不敏感）
image = resize_image(image, max_size=1024)
```
**节省**: Token 使用减少 50%，节省约 20-30%

#### 3. 混合使用模型
```python
# 80% 任务用便宜模型，20% 用强大模型
if random.random() < 0.8:
    vlm = create_vlm(provider="glm")  # ¥30/月
else:
    vlm = create_vlm(provider="openai")  # $80/月
```
**节省**: 综合成本约 60-70%

---

## 🚀 快速开始

### 5 分钟配置你的第一个 VLM

#### Step 1: 选择提供商
```bash
# 国际用户推荐
VLM_PROVIDER=openai

# 国内用户推荐
VLM_PROVIDER=qwen
```

#### Step 2: 获取 API Key
- OpenAI: https://platform.openai.com/api-keys
- 通义千问: https://dashscope.aliyun.com/
- Google: https://makersuite.google.com/app/apikey
- 智谱: https://open.bigmodel.cn/

#### Step 3: 配置 .env
```bash
# 示例: 使用通义千问
VLM_PROVIDER=qwen
VLM_QWEN_API_KEY=sk-...
VLM_QWEN_MODEL=qwen-vl-max
```

#### Step 4: 测试
```python
from geomind.models.vlm import create_vlm

vlm = create_vlm()
await vlm.initialize()

result = await vlm.analyze_image(
    image="./test.jpg",
    prompt="这张图片拍摄于哪里？"
)

print(result.data)
```

---

## ❓ 常见问题

### Q: 我是新手，应该选哪个？

**A**: 
- **国际**: OpenAI GPT-4o（最省心）
- **国内**: 阿里云通义千问（最省心+合规）

### Q: 多个 VLM 可以同时用吗？

**A**: 可以！推荐配置多个作为备份：
```bash
VLM_OPENAI_API_KEY=...  # 主用
VLM_QWEN_API_KEY=...    # 备用
VLM_GLM_API_KEY=...     # 备用
```

### Q: 本地部署难吗？

**A**: 使用 Ollama 非常简单：
```bash
# 3 条命令搞定
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llava:34b
# 自动启动，立即可用
```

### Q: 哪个模型中文最好？

**A**: 
1. 🥇 阿里云通义千问 VL
2. 🥈 智谱 GLM-4V
3. 🥉 OpenAI GPT-4o

### Q: 如何切换 VLM？

**A**: 
```bash
# 方法 1: 环境变量
export VLM_PROVIDER=qwen

# 方法 2: 代码中指定
vlm = create_vlm(provider="qwen")
```

---

## 📚 详细文档

- [VLM 提供商完整指南](./guides/vlm_providers.md)
- [API Keys 配置清单](./API_KEYS_CHECKLIST.md)
- [快速开始](./guides/quickstart.md)

---

**最后更新**: 2024-12-19

