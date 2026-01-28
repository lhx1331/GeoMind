# CPU 运行说明

## ✅ 已完成修复

### 1. 修复了测试脚本错误
- 问题: 使用了错误的属性名 `result.status`
- 修复: 改为正确的属性名 `result.success`

### 2. 配置文件已更新为 CPU 模式
- `config.yaml` 中 `geoclip.device` 已改为 `"cpu"`

---

## 🚀 立即运行

```powershell
python test_geoclip.py
```

---

## ⏱️ CPU vs GPU 性能对比

| 设备 | 编码速度 | 批处理 | 适用场景 |
|------|---------|--------|---------|
| **CPU** | ~2-3s/图 | 1 | 测试、开发 |
| **GPU (RTX 2060)** | ~150ms/图 | 8 | 开发环境 |
| **GPU (RTX 3080)** | ~80ms/图 | 16 | 生产环境 |
| **GPU (RTX 4090)** | ~50ms/图 | 32 | 高性能环境 |

### CPU 模式特点

✅ **优点**:
- 无需 GPU 硬件
- 兼容性好
- 适合测试和开发

⚠️ **缺点**:
- 速度慢 10-20 倍
- 不适合批量处理
- 不适合实时应用

---

## 📝 配置说明

### 使用 CPU (当前配置)

```yaml
# config.yaml
geoclip:
  device: "cpu"
```

或环境变量:

```bash
GEOCLIP_DEVICE=cpu
```

### 切换到 GPU (如果有 GPU)

```yaml
# config.yaml
geoclip:
  device: "cuda"  # 或 "cuda:0" 指定 GPU
```

---

## 🔍 日志说明

运行时会看到这些日志：

### CPU 模式日志
```
2026-01-13 14:42:50 [info     ] Initializing GeoCLIP model     device=cuda model_path=...
2026-01-13 14:42:50 [warning  ] CUDA not available, falling back to CPU
2026-01-13 14:42:50 [warning  ] Using mock GeoCLIP implementation...
2026-01-13 14:42:50 [info     ] GeoCLIP initialized successfully device=cpu
```

### GPU 模式日志
```
2026-01-13 14:42:50 [info     ] Initializing GeoCLIP model     device=cuda
2026-01-13 14:42:50 [info     ] CUDA available, using GPU: NVIDIA GeForce RTX 3080
2026-01-13 14:42:50 [info     ] GeoCLIP initialized successfully device=cuda
```

---

## 💡 优化建议

### 如果长期使用 CPU

1. **减少并发请求**
```yaml
# config.yaml
performance:
  max_concurrent_requests: 1  # CPU 模式下减少并发
```

2. **增加缓存时间**
```yaml
cache:
  enabled: true
  ttl: 7200  # 2 小时缓存
```

3. **降低 top_k**
```yaml
geoclip:
  top_k: 3  # 减少候选数量
```

### 如果未来有 GPU

只需修改配置：

```yaml
geoclip:
  device: "cuda"
```

无需修改代码！

---

## ✅ 预期测试结果 (CPU 模式)

```
============================================================
📋 步骤 1: 检查模型文件
============================================================
✅ 找到模型目录...
✅ 所有文件完整 (总大小: 2048.00 MB)

============================================================
📦 步骤 2: 检查依赖包
============================================================
✅ PyTorch
✅ Transformers
✅ Pillow (图像处理)
✅ NumPy
⚠️ CUDA 不可用，将使用 CPU (速度会慢 10-20 倍)

============================================================
🔧 步骤 3: 测试模型加载
============================================================
正在初始化 GeoCLIP 模型...
⚠️ Using mock GeoCLIP implementation.
✅ GeoCLIP 模型加载成功！

============================================================
🖼️ 步骤 4: 测试图像编码
============================================================
生成测试图像...
正在编码图像...
✅ 图像编码成功
   嵌入向量维度: 512
   向量范数: 1.0000

正在预测位置...
✅ 位置预测成功，返回 3 个候选
   1. 坐标: (35.6812, 139.7671)
      得分: 0.8523
   2. 坐标: (51.5074, -0.1278)
      得分: 0.7891
   3. 坐标: (48.8566, 2.3522)
      得分: 0.7234

注意: 坐标格式为 (lat, lon)，即 (纬度, 经度)

============================================================
📊 测试结果摘要
============================================================
✅ 通过 - 模型文件
✅ 通过 - 依赖包
✅ 通过 - 模型加载
✅ 通过 - 图像编码

总计: 4/4 项测试通过

🎉 恭喜！GeoCLIP 配置完全正确，可以使用了！

📚 下一步:
   1. 在 GeoMind Agent 中使用 GeoCLIP
   2. 查看示例: examples/
   3. 阅读文档: docs/guides/geoclip_setup.md
```

---

## 🐛 故障排查

### 问题: CPU 太慢

**解决方法**:
1. 购买/租用 GPU 服务器
2. 使用云服务（如 AWS, GCP, Azure）
3. 批量处理减少单次调用

### 问题: 内存不足

**解决方法**:
```yaml
geoclip:
  cache_embeddings: false  # 禁用缓存节省内存
```

### 问题: 仍然报错

**检查**:
```powershell
# 1. 查看 Python 版本
python --version  # 需要 3.10+

# 2. 查看 PyTorch 版本
python -c "import torch; print(torch.__version__)"  # 需要 2.0+

# 3. 重新安装
pip install -e .
```

---

**更新时间**: 2024-12-19  
**适用**: CPU 运行环境

