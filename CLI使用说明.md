# GeoMind CLI 使用说明

## 📋 命令格式

### 基本用法

```bash
# 单张图片（图片路径直接作为参数，不需要 --image）
geomind locate <图片路径>

# 示例
geomind locate D:\project\GeoMind\hollywood-sign-1598473_1920.jpg
```

---

## 🎯 完整命令选项

### 位置参数（必需）

- `IMAGES...` - 图片路径，可以指定多张图片

### 选项参数（可选）

- `-f, --format [text|json|csv]` - 输出格式（默认: text）
- `-o, --output PATH` - 输出文件路径（默认输出到标准输出）
- `-i, --iterations` - 启用迭代优化
- `--max-iterations INTEGER` - 最大迭代次数（默认: 2）
- `-v, --verbose` - 详细输出
- `-c, --config PATH` - 配置文件路径

---

## 📝 使用示例

### 1. 基础使用

```bash
# 单张图片
geomind locate photo.jpg

# 多张图片
geomind locate photo1.jpg photo2.jpg photo3.jpg
```

### 2. 指定输出格式

```bash
# JSON 格式
geomind locate photo.jpg --format json

# CSV 格式
geomind locate photo.jpg --format csv

# 保存到文件
geomind locate photo.jpg --format json --output result.json
```

### 3. 启用迭代优化

```bash
# 启用迭代（默认最多 2 次）
geomind locate photo.jpg --iterations

# 自定义最大迭代次数
geomind locate photo.jpg --iterations --max-iterations 5
```

### 4. 详细输出

```bash
# 显示详细信息
geomind locate photo.jpg --verbose
```

### 5. 使用自定义配置

```bash
# 指定配置文件
geomind locate photo.jpg --config my_config.yaml
```

---

## ⚠️ 常见错误

### 错误 1: `No such option: --image`

**错误命令**:
```bash
geomind locate --image photo.jpg  # ❌ 错误
```

**正确命令**:
```bash
geomind locate photo.jpg  # ✅ 正确
```

**原因**: CLI 使用位置参数，不是 `--image` 选项。

---

### 错误 2: 文件路径包含空格

**错误命令**:
```bash
geomind locate "my photo.jpg"  # 可能有问题
```

**正确命令**:
```bash
# Windows PowerShell
geomind locate "my photo.jpg"

# Windows CMD
geomind locate "my photo.jpg"

# Linux/macOS
geomind locate "my photo.jpg"
```

---

### 错误 3: 文件不存在

**错误信息**:
```
Error: Invalid value for 'IMAGES...': Path 'photo.jpg' does not exist.
```

**解决方法**: 检查文件路径是否正确，使用绝对路径或确保在正确的目录下运行。

---

## 🔍 查看帮助

```bash
# 查看所有命令
geomind --help

# 查看 locate 命令帮助
geomind locate --help

# 查看版本
geomind --version
```

---

## 📊 输出格式说明

### Text 格式（默认）

```
============================================================
📍 地理位置预测结果
============================================================

位置: 34.1341°N, -118.3215°W
置信度: 85.00%

答案: Hollywood Sign, Los Angeles, CA
支持证据: OCR文本匹配, 建筑风格一致
排除原因: 
  - 其他候选分数较低

推理路径:
  1. Perception: 提取了 3 个 OCR 线索
  2. Hypothesis: 生成了 2 个假设
  3. Retrieval: 召回了 5 个候选
  4. Verification: 验证了 5 个候选，最高分: 0.85
```

### JSON 格式

```json
{
  "answer": "Hollywood Sign, Los Angeles, CA",
  "coordinates": {
    "lat": 34.1341,
    "lon": -118.3215
  },
  "confidence": 0.85,
  "why": "OCR文本匹配, 建筑风格一致",
  "why_not": ["其他候选分数较低"],
  "reasoning_path": [
    "Perception: 提取了 3 个 OCR 线索",
    "Hypothesis: 生成了 2 个假设",
    "Retrieval: 召回了 5 个候选",
    "Verification: 验证了 5 个候选，最高分: 0.85"
  ]
}
```

### CSV 格式

```csv
image,lat,lon,confidence,success
photo.jpg,34.1341,-118.3215,0.85,true
```

---

## 💡 提示

1. **批量处理**: 可以一次指定多张图片，CLI 会依次处理
2. **输出重定向**: 使用 `--output` 保存结果，或使用 shell 重定向 `> result.json`
3. **迭代优化**: 对于复杂图片，启用 `--iterations` 可以提高准确性
4. **详细输出**: 使用 `--verbose` 查看完整的推理过程

---

## 🆘 需要帮助？

- 查看完整文档: `README.md`
- 查看快速开始: `快速开始.md`
- 查看配置指南: `配置指南.md`


