# GeoCLIP 模型下载和集成指南

## 📖 什么是 GeoCLIP？

GeoCLIP 是一个专门用于地理位置识别的视觉模型，能够：
- 🗺️ 将图像编码为地理感知的向量
- 📍 预测图像的拍摄位置（经纬度）
- 🔍 在全球范围内检索相似位置

在 GeoMind 中，GeoCLIP 用于 **Retrieval 阶段**，根据图像快速召回候选地点。

---

## 🎯 快速开始

### 总览
- **模型大小**: 约 2-3 GB
- **下载时间**: 5-15 分钟（取决于网络）
- **硬件要求**: 
  - **推荐**: NVIDIA GPU (4GB+ VRAM)
  - **最低**: CPU（会慢 10-20 倍）

---

## 📥 方法 1: 使用 Git LFS 下载（推荐）

### Step 1.1: 安装 Git LFS

**Windows**:
```powershell
# 方式 1: 使用 Chocolatey
choco install git-lfs

# 方式 2: 手动安装
# 访问 https://git-lfs.github.com/
# 下载并安装 Git LFS
```

**Linux (Ubuntu/Debian)**:
```bash
sudo apt-get install git-lfs
```

**macOS**:
```bash
brew install git-lfs
```

### Step 1.2: 初始化 Git LFS

```bash
git lfs install
```

### Step 1.3: 克隆 GeoCLIP 模型

```bash
# 创建模型目录
mkdir -p models

# 克隆模型（推荐仓库）
git clone https://huggingface.co/geolocal/StreetCLIP ./models/geoclip

# 或者使用官方仓库
# git clone https://github.com/VicenteVivan/geo-clip ./models/geoclip
```

### Step 1.4: 验证下载

```bash
# 检查模型文件
ls -lh ./models/geoclip/

# 应该看到这些文件:
# - pytorch_model.bin (最大，约 2GB)
# - config.json
# - tokenizer.json
# - tokenizer_config.json
# - special_tokens_map.json
```

---

## 📥 方法 2: 手动下载（无需 Git LFS）

### Step 2.1: 访问 Hugging Face

打开浏览器访问：
```
https://huggingface.co/geolocal/StreetCLIP/tree/main
```

### Step 2.2: 下载必需文件

创建目录并下载以下文件到 `./models/geoclip/` 目录：

**必需文件**（按优先级）：

1. **pytorch_model.bin** (约 2GB) ⭐ 最重要
   - 模型权重文件
   - 点击文件名 → 点击右上角 "↓ download"

2. **config.json** (几 KB)
   - 模型配置文件

3. **tokenizer.json** (约 1MB)
   - 分词器配置

4. **tokenizer_config.json** (几 KB)
   - 分词器参数

5. **special_tokens_map.json** (几 KB)
   - 特殊 token 映射

**可选文件**：

- `README.md` - 模型说明
- `vocab.txt` - 词汇表（如果有）
- `preprocessor_config.json` - 预处理配置（如果有）

### Step 2.3: 文件结构

确保文件结构如下：

```
项目根目录/
└── models/
    └── geoclip/
        ├── pytorch_model.bin  (约 2GB)
        ├── config.json
        ├── tokenizer.json
        ├── tokenizer_config.json
        └── special_tokens_map.json
```

---

## 📥 方法 3: 使用 Python 下载（自动化）

### Step 3.1: 创建下载脚本

创建文件 `download_geoclip.py`：

```python
"""
自动下载 GeoCLIP 模型
"""

from pathlib import Path
from huggingface_hub import snapshot_download

def download_geoclip(save_dir: str = "./models/geoclip"):
    """
    从 Hugging Face 下载 GeoCLIP 模型
    
    Args:
        save_dir: 保存目录
    """
    print(f"📥 开始下载 GeoCLIP 模型...")
    print(f"   保存位置: {save_dir}")
    
    try:
        # 创建目录
        Path(save_dir).mkdir(parents=True, exist_ok=True)
        
        # 下载模型
        snapshot_download(
            repo_id="geolocal/StreetCLIP",
            local_dir=save_dir,
            local_dir_use_symlinks=False,
            resume_download=True,  # 支持断点续传
        )
        
        print(f"✅ GeoCLIP 模型下载完成！")
        print(f"   模型位置: {save_dir}")
        
        # 验证文件
        model_file = Path(save_dir) / "pytorch_model.bin"
        if model_file.exists():
            size_mb = model_file.stat().st_size / (1024 * 1024)
            print(f"   模型大小: {size_mb:.2f} MB")
        else:
            print(f"⚠️  警告: 未找到 pytorch_model.bin")
        
        return True
        
    except Exception as e:
        print(f"❌ 下载失败: {e}")
        return False

if __name__ == "__main__":
    # 安装依赖
    print("确保已安装: pip install huggingface_hub")
    print()
    
    # 下载
    download_geoclip()
```

### Step 3.2: 安装依赖

```bash
pip install huggingface_hub
```

### Step 3.3: 运行下载

```bash
python download_geoclip.py
```

---

## 🔧 集成到 GeoMind 项目

### Step 1: 安装 GeoCLIP 依赖

GeoCLIP 需要以下 Python 包：

```bash
# 方式 1: 使用 pyproject.toml (推荐)
pip install -e ".[geoclip]"

# 方式 2: 手动安装
pip install torch torchvision
pip install transformers
pip install pillow
pip install numpy
```

**如果使用 GPU（推荐）**：
```bash
# CUDA 11.8
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118

# CUDA 12.1
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
```

### Step 2: 配置 GeoCLIP 路径

编辑 `config.yaml`：

```yaml
geoclip:
  model_path: "./models/geoclip"  # 模型路径
  device: "cuda"  # 使用 GPU (如无 GPU 改为 "cpu")
  top_k: 5  # 返回前 5 个候选
  cache_embeddings: true  # 启用缓存
```

### Step 3: 测试 GeoCLIP

创建测试脚本 `test_geoclip.py`：

```python
"""
测试 GeoCLIP 模型是否正常工作
"""

import asyncio
from pathlib import Path
from geomind.models.geoclip import create_geoclip_model
from geomind.utils.image import load_image

async def test_geoclip():
    """测试 GeoCLIP 功能"""
    
    print("🗺️ 测试 GeoCLIP 模型\n")
    
    # 1. 创建 GeoCLIP 模型
    print("步骤 1: 初始化模型...")
    geoclip = create_geoclip_model()
    await geoclip.initialize()
    print("✅ 模型初始化成功\n")
    
    # 2. 测试图像编码
    print("步骤 2: 测试图像编码...")
    
    # 使用测试图像（请替换为您的图像路径）
    test_image_path = "./test_image.jpg"
    
    if not Path(test_image_path).exists():
        print(f"⚠️ 测试图像不存在: {test_image_path}")
        print(f"   请提供一张测试图像，或修改 test_image_path 变量")
        await geoclip.cleanup()
        return
    
    # 加载图像
    image = load_image(test_image_path)
    
    # 编码图像
    response = await geoclip.encode_image(image)
    
    if response.status == "success":
        embedding = response.data
        print(f"✅ 图像编码成功")
        print(f"   嵌入向量维度: {len(embedding)}")
    else:
        print(f"❌ 图像编码失败: {response.error}")
        await geoclip.cleanup()
        return
    
    # 3. 预测位置
    print("\n步骤 3: 预测图像位置...")
    location_response = await geoclip.predict_location(image, top_k=5)
    
    if location_response.status == "success":
        locations = location_response.data
        print(f"✅ 位置预测成功，找到 {len(locations)} 个候选：\n")
        
        for i, loc in enumerate(locations, 1):
            print(f"   {i}. 坐标: ({loc['latitude']:.4f}, {loc['longitude']:.4f})")
            print(f"      得分: {loc['score']:.4f}")
            if 'name' in loc:
                print(f"      名称: {loc['name']}")
            print()
    else:
        print(f"❌ 位置预测失败: {location_response.error}")
    
    # 4. 清理
    await geoclip.cleanup()
    print("✅ 测试完成！")

if __name__ == "__main__":
    asyncio.run(test_geoclip())
```

运行测试：

```bash
python test_geoclip.py
```

---

## 🎯 在 GeoMind Agent 中使用 GeoCLIP

### 示例 1: 基础使用

```python
import asyncio
from geomind.models.geoclip import create_geoclip_model
from geomind.utils.image import load_image

async def locate_image(image_path: str):
    """使用 GeoCLIP 定位图像"""
    
    # 1. 创建模型
    geoclip = create_geoclip_model()
    await geoclip.initialize()
    
    # 2. 加载图像
    image = load_image(image_path)
    
    # 3. 预测位置
    result = await geoclip.predict_location(image, top_k=5)
    
    if result.success:
        locations = result.data
        print(f"找到 {len(locations)} 个候选位置：")
        
        for i, loc in enumerate(locations, 1):
            lat, lon = loc['lat'], loc['lon']
            score = loc['score']
            print(f"{i}. ({lat:.4f}, {lon:.4f}) - 得分: {score:.4f}")
    
    # 4. 清理
    await geoclip.cleanup()
    
    return locations

# 运行
asyncio.run(locate_image("your_image.jpg"))
```

### 示例 2: 集成到完整流程

```python
import asyncio
from geomind.agent.state import AgentState, Candidate
from geomind.models.geoclip import create_geoclip_model
from geomind.models.vlm import create_vlm
from geomind.prompts.perception import render_perception_prompt

async def full_pipeline(image_path: str):
    """完整的地理定位流程"""
    
    # 1. Perception - 使用 VLM 提取线索
    print("🔍 阶段 1: Perception")
    vlm = create_vlm()
    await vlm.initialize()
    
    prompt = render_perception_prompt()
    perception_result = await vlm.analyze_image(image_path, prompt)
    print(f"✅ 提取到线索")
    
    await vlm.cleanup()
    
    # 2. Retrieval - 使用 GeoCLIP 召回候选
    print("\n🗺️ 阶段 2: Retrieval (GeoCLIP)")
    geoclip = create_geoclip_model()
    await geoclip.initialize()
    
    location_result = await geoclip.predict_location(image_path, top_k=5)
    
    if location_result.success:
        candidates = []
        for loc in location_result.data:
            candidate = Candidate(
                name=f"Location_{loc['lat']:.2f}_{loc['lon']:.2f}",
                lat=loc['lat'],
                lon=loc['lon'],
                source="geoclip",
                score=loc['score']
            )
            candidates.append(candidate)
        
        print(f"✅ 召回 {len(candidates)} 个候选地点")
        
        # 显示候选
        for i, cand in enumerate(candidates, 1):
            print(f"   {i}. {cand.name}")
            print(f"      坐标: ({cand.lat:.4f}, {cand.lon:.4f})")
            print(f"      得分: {cand.score:.4f}")
    
    await geoclip.cleanup()
    
    return candidates

# 运行
asyncio.run(full_pipeline("your_image.jpg"))
```

---

## ⚙️ 性能优化

### 1. 使用 GPU 加速

确保配置中启用 GPU：

```yaml
# config.yaml
geoclip:
  device: "cuda"  # 或 "cuda:0" 指定 GPU
```

检查 GPU 是否可用：

```python
import torch
print(f"CUDA 可用: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"GPU 设备: {torch.cuda.get_device_name(0)}")
```

### 2. 启用嵌入缓存

```yaml
# config.yaml
geoclip:
  cache_embeddings: true
```

这会缓存图像嵌入，避免重复计算。

### 3. 批量处理

```python
# 批量编码多张图像
images = [img1, img2, img3]
embeddings = []

for image in images:
    result = await geoclip.encode_image(image)
    embeddings.append(result.data)
```

### 4. 调整 batch size

```python
# 如果内存充足，可以增加 batch size
geoclip = create_geoclip_model(
    config=ModelConfig(
        model_type=ModelType.RETRIEVAL,
        batch_size=8  # 默认是 1
    )
)
```

---

## 🔍 故障排查

### 问题 1: 找不到模型文件

```
Error: Could not find model files in ./models/geoclip
```

**解决方法**：
1. 检查路径是否正确
2. 确认 `pytorch_model.bin` 是否存在
3. 重新下载模型

```bash
ls -la ./models/geoclip/
```

### 问题 2: CUDA 内存不足

```
RuntimeError: CUDA out of memory
```

**解决方法**：

**方案 A**: 降低 batch size
```python
# 减小批处理大小
batch_size = 1
```

**方案 B**: 使用 CPU
```yaml
# config.yaml
geoclip:
  device: "cpu"
```

**方案 C**: 清理 GPU 缓存
```python
import torch
torch.cuda.empty_cache()
```

### 问题 3: 下载太慢

**解决方法**：

**方案 A**: 使用镜像站点
```bash
# 设置 Hugging Face 镜像
export HF_ENDPOINT=https://hf-mirror.com
git clone https://hf-mirror.com/geolocal/StreetCLIP ./models/geoclip
```

**方案 B**: 使用代理
```bash
# 设置代理
export HTTP_PROXY=http://your-proxy:port
export HTTPS_PROXY=http://your-proxy:port
git clone https://huggingface.co/geolocal/StreetCLIP ./models/geoclip
```

**方案 C**: 断点续传
```bash
# Git LFS 支持断点续传
cd ./models/geoclip
git lfs pull
```

### 问题 4: 模型加载失败

```
Error loading model: ...
```

**解决方法**：

1. **检查 PyTorch 版本**
```bash
python -c "import torch; print(torch.__version__)"
# 推荐版本: 2.0+
```

2. **检查 Transformers 版本**
```bash
python -c "import transformers; print(transformers.__version__)"
# 推荐版本: 4.30+
```

3. **重新安装依赖**
```bash
pip install --upgrade torch transformers
```

---

## 📊 性能基准

### 硬件对比

| 硬件 | 编码速度 | 批处理 | 推荐场景 |
|------|---------|--------|---------|
| **RTX 4090** | ~50ms/图 | 32 | 生产环境 |
| **RTX 3080** | ~80ms/图 | 16 | 开发环境 |
| **RTX 2060** | ~150ms/图 | 8 | 测试环境 |
| **CPU (i7)** | ~2s/图 | 1 | 离线处理 |

### 内存使用

| 配置 | GPU 内存 | 系统内存 |
|------|---------|---------|
| **Batch=1** | ~2GB | ~4GB |
| **Batch=8** | ~6GB | ~6GB |
| **Batch=16** | ~10GB | ~8GB |

---

## 🔗 相关资源

### 官方资源

- **Hugging Face**: https://huggingface.co/geolocal/StreetCLIP
- **GitHub**: https://github.com/VicenteVivan/geo-clip
- **论文**: [GeoCLIP Paper](https://arxiv.org/abs/...)

### GeoMind 文档

- [配置指南](../../配置指南.md)
- [API Keys 清单](../API_KEYS_CHECKLIST.md)
- [快速开始](../../快速开始.md)

---

## ✅ 检查清单

下载和集成完成后，检查：

- [ ] 模型文件已下载到 `./models/geoclip/`
- [ ] `pytorch_model.bin` 文件存在（约 2GB）
- [ ] `config.yaml` 中路径配置正确
- [ ] PyTorch 和 CUDA 已安装（如使用 GPU）
- [ ] 运行 `test_geoclip.py` 测试通过
- [ ] GPU 可用性已验证（如使用 GPU）

---

## 🆘 需要帮助？

如果遇到问题：

1. **查看日志**
   ```bash
   tail -f logs/geomind.log
   ```

2. **运行诊断**
   ```bash
   python test_geoclip.py
   ```

3. **查看文档**
   - [故障排查](#故障排查)
   - [性能优化](#性能优化)

---

**更新时间**: 2024-12-19  
**版本**: v1.0

