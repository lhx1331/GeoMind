# GeoCLIP 快速指南 - 3 步完成

## 📖 什么是 GeoCLIP？

GeoCLIP 是 GeoMind 的核心组件，用于：
- 🗺️ 将图像转换为地理位置坐标
- 📍 快速召回候选地点（Retrieval 阶段）
- 🔍 支持全球范围的位置检索

**必需**: 所有图像地理定位功能都依赖 GeoCLIP

---

## 🚀 3 步快速开始

### Step 1: 下载 GeoCLIP 模型 (10 分钟)

```bash
# 自动下载（推荐）
python download_geoclip.py
```

**手动下载**（如果自动下载失败）：

```bash
# 方式 A: 使用 Git LFS
git lfs install
git clone https://huggingface.co/geolocal/StreetCLIP ./models/geoclip

# 方式 B: 手动下载
# 访问: https://huggingface.co/geolocal/StreetCLIP/tree/main
# 下载所有文件到 ./models/geoclip/
```

### Step 2: 配置路径 (1 分钟)

确保 `config.yaml` 中配置正确：

```yaml
geoclip:
  model_path: "./models/geoclip"  # 模型路径
  device: "cuda"  # 使用 GPU，如无 GPU 改为 "cpu"
  top_k: 5  # 返回候选数量
  cache_embeddings: true  # 启用缓存
```

### Step 3: 验证安装 (2 分钟)

```bash
python test_geoclip.py
```

看到 "🎉 恭喜！GeoCLIP 配置完全正确" 表示成功！

---

## 📋 文件结构

下载完成后，应该有：

```
项目根目录/
├── models/
│   └── geoclip/                    ← GeoCLIP 模型目录
│       ├── pytorch_model.bin       (约 2GB) ⭐ 模型权重
│       ├── config.json             (几 KB)
│       ├── tokenizer.json          (约 1MB)
│       ├── tokenizer_config.json   (几 KB)
│       └── special_tokens_map.json (几 KB)
├── config.yaml                     ← 配置文件
├── download_geoclip.py             ← 下载脚本
└── test_geoclip.py                 ← 测试脚本
```

---

## 💻 基础使用

### 示例 1: 预测图像位置

```python
import asyncio
from geomind.models.geoclip import create_geoclip_model
from geomind.utils.image import load_image

async def locate_image(image_path):
    # 创建模型
    geoclip = create_geoclip_model()
    await geoclip.initialize()
    
    # 加载图像
    image = load_image(image_path)
    
    # 预测位置
    result = await geoclip.predict_location(image, top_k=5)
    
    if result.success:
        for i, loc in enumerate(result.data, 1):
            print(f"{i}. ({loc['lat']:.4f}, {loc['lon']:.4f})")
            print(f"   得分: {loc['score']:.4f}")
    
    await geoclip.cleanup()

asyncio.run(locate_image("your_image.jpg"))
```

### 示例 2: 编码图像

```python
async def encode_image(image_path):
    geoclip = create_geoclip_model()
    await geoclip.initialize()
    
    # 获取图像嵌入向量
    result = await geoclip.encode_image(image_path)
    
    if result.status == "success":
        embedding = result.data
        print(f"嵌入向量维度: {len(embedding)}")
    
    await geoclip.cleanup()

asyncio.run(encode_image("your_image.jpg"))
```

---

## ⚙️ 配置选项

### GPU vs CPU

```yaml
# 使用 GPU (推荐，快 10-20 倍)
geoclip:
  device: "cuda"

# 使用 CPU (如果没有 GPU)
geoclip:
  device: "cpu"
```

### 候选数量

```yaml
geoclip:
  top_k: 5  # 返回前 5 个候选（默认）
  # 可以是 1-100 之间的任何值
```

### 启用缓存

```yaml
geoclip:
  cache_embeddings: true  # 缓存图像嵌入，避免重复计算
```

---

## 🔧 硬件要求

### 推荐配置 ⭐

- **GPU**: NVIDIA GPU (4GB+ VRAM)
- **内存**: 8GB+ RAM
- **存储**: 5GB 可用空间
- **速度**: ~50-150ms/图

### 最低配置

- **CPU**: 现代多核 CPU
- **内存**: 4GB+ RAM
- **存储**: 5GB 可用空间
- **速度**: ~2-3s/图 (比 GPU 慢 10-20 倍)

---

## 🐛 常见问题

### Q1: 下载太慢怎么办？

**A**: 使用国内镜像：

```bash
export HF_ENDPOINT=https://hf-mirror.com
python download_geoclip.py
```

### Q2: 显存不足怎么办？

**A**: 切换到 CPU 模式：

```yaml
# config.yaml
geoclip:
  device: "cpu"
```

### Q3: 找不到模型文件？

**A**: 检查路径：

```bash
# 确认文件存在
ls -la ./models/geoclip/

# 应该看到 pytorch_model.bin (约 2GB)
```

### Q4: 预测结果不准确？

**A**: GeoCLIP 主要用于：
- ✅ 召回候选地点（粗定位）
- ✅ 提供地理先验信息

不应直接作为最终答案，需要结合：
- VLM 提取的视觉线索
- LLM 生成的假设
- 验证工具的检查

---

## 📊 性能参考

### 编码速度

| 硬件 | 速度 | 适用场景 |
|------|------|---------|
| **RTX 4090** | ~50ms/图 | 生产环境 |
| **RTX 3080** | ~80ms/图 | 开发环境 |
| **RTX 2060** | ~150ms/图 | 测试环境 |
| **CPU (i7)** | ~2s/图 | 离线处理 |

### 内存占用

- **GPU 模式**: 约 2GB VRAM + 4GB RAM
- **CPU 模式**: 约 4-6GB RAM

---

## 📚 详细文档

- **完整指南**: [docs/guides/geoclip_setup.md](docs/guides/geoclip_setup.md)
  - 详细下载方法
  - 集成示例
  - 性能优化
  - 故障排查

- **配置指南**: [配置指南.md](配置指南.md)
  - 完整项目配置
  - API Keys 管理

- **快速开始**: [快速开始.md](快速开始.md)
  - 整体配置流程

---

## ✅ 检查清单

下载和配置完成后：

- [ ] 运行 `python download_geoclip.py` 下载模型
- [ ] 确认 `./models/geoclip/pytorch_model.bin` 存在（约 2GB）
- [ ] 确认 `config.yaml` 中路径配置正确
- [ ] 运行 `python test_geoclip.py` 测试通过
- [ ] (可选) 安装 CUDA 和 PyTorch GPU 版本

---

## 🆘 需要帮助？

**文档**:
- 详细指南: `docs/guides/geoclip_setup.md`
- 故障排查: 同上文档的 "故障排查" 章节

**命令**:
```bash
# 重新下载
python download_geoclip.py

# 测试安装
python test_geoclip.py

# 查看日志
tail -f logs/geomind.log
```

---

**更新时间**: 2024-12-19  
**模型版本**: StreetCLIP (GeoCLIP)

