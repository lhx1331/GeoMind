# 开发环境设置指南

本文档说明如何设置 GeoMind 的开发环境。

## 前置要求

- Python 3.10 或更高版本
- Git
- (可选) CUDA 11.8+ 用于 GPU 加速

## 快速开始

### Windows (PowerShell)

```powershell
# 运行开发环境设置脚本（自动创建和激活虚拟环境）
.\scripts\setup_dev_env.ps1

# 或者使用虚拟环境激活脚本
.\scripts\activate_venv.ps1
```

### Linux/macOS

```bash
# 运行开发环境设置脚本（自动创建和激活虚拟环境）
chmod +x scripts/setup_dev_env.sh
./scripts/setup_dev_env.sh

# 或者使用虚拟环境激活脚本
source scripts/activate_venv.sh
```

### 手动设置

1. **创建虚拟环境**

```bash
# 项目使用项目根目录下的 venv/ 目录
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\Activate.ps1
```

> **注意**: 项目的虚拟环境位于 `venv/` 目录，已添加到 `.gitignore`。详细说明请查看 [VENV.md](VENV.md)。

2. **安装依赖**

```bash
pip install --upgrade pip
pip install -e ".[dev]"
```

3. **安装 pre-commit hooks**

```bash
pre-commit install
```

4. **配置环境变量**

```bash
cp env.example .env
# 编辑 .env 文件，填入您的 API 密钥
```

## 验证安装

### 检查代码质量工具

```bash
# 检查 Black 是否安装
black --version

# 检查 Ruff 是否安装
ruff --version

# 检查 Mypy 是否安装
mypy --version

# 检查 pre-commit 是否安装
pre-commit --version
```

### 运行代码格式化

```bash
# 格式化所有代码
black geomind tests examples

# 检查代码风格
ruff check geomind tests

# 类型检查
mypy geomind
```

### 运行 pre-commit

```bash
# 对所有文件运行 hooks
pre-commit run --all-files

# 在提交时自动运行（已通过 pre-commit install 配置）
```

## 项目结构

```
GeoMind/
├── geomind/          # 主包
├── tests/            # 测试
├── examples/         # 示例代码
├── docs/             # 文档
├── scripts/          # 工具脚本
└── pyproject.toml    # 项目配置
```

## 开发工作流

1. **创建功能分支**

```bash
git checkout -b feature/your-feature-name
```

2. **开发代码**

编写代码时，pre-commit hooks 会自动检查格式。

3. **提交前检查**

```bash
# 手动运行所有检查
pre-commit run --all-files

# 运行测试
pytest
```

4. **提交代码**

```bash
git add .
git commit -m "feat: your feature description"
```

## 代码质量工具

### Black (代码格式化)

- 自动格式化 Python 代码
- 行长度: 100 字符
- 配置在 `pyproject.toml` 中

### Ruff (代码检查)

- 快速的 Python linter
- 检查代码风格和潜在问题
- 配置在 `pyproject.toml` 中

### Mypy (类型检查)

- 静态类型检查
- 帮助发现类型错误
- 配置在 `pyproject.toml` 中

### Pre-commit (Git Hooks)

- 在提交前自动运行检查
- 确保代码质量
- 配置在 `.pre-commit-config.yaml` 中

## 虚拟环境

项目使用项目根目录下的 `venv/` 目录作为虚拟环境。详细说明请查看 [VENV.md](VENV.md)。

### 快速激活

```bash
# Windows
.\scripts\activate_venv.ps1

# Linux/macOS
source scripts/activate_venv.sh
```

### 验证虚拟环境

```bash
# 检查 Python 路径（应该在 venv 目录中）
which python  # Linux/macOS
where python  # Windows

# 检查已安装的包
pip list
```

## 常见问题

### pre-commit 安装失败

如果 pre-commit 安装失败，可以手动安装：

```bash
pip install pre-commit
pre-commit install
```

### 虚拟环境激活失败 (Windows)

如果 PowerShell 执行策略限制，运行：

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 找不到虚拟环境

确保虚拟环境已创建：

```bash
# 检查虚拟环境是否存在
ls venv  # Linux/macOS
dir venv  # Windows

# 如果不存在，重新创建
python -m venv venv
```

### 依赖安装失败

如果某些依赖安装失败，尝试：

```bash
# 确保虚拟环境已激活
source venv/bin/activate  # 或 .\venv\Scripts\Activate.ps1

# 升级 pip
pip install --upgrade pip setuptools wheel

# 重新安装
pip install -e ".[dev]"
```

## 下一步

设置完成后，可以开始开发：

1. 查看 [TASKS.md](TASKS.md) 了解开发任务
2. 阅读 [GUIDE.md](GUIDE.md) 了解技术设计
3. 查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解贡献指南

