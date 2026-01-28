# 虚拟环境配置指南

GeoMind 项目使用 Python 虚拟环境来隔离项目依赖。本文档说明如何设置和使用项目的虚拟环境。

## 虚拟环境位置

项目的虚拟环境默认创建在项目根目录下的 `venv/` 目录中。

```
GeoMind/
├── venv/          # 虚拟环境目录（已添加到 .gitignore）
├── geomind/       # 项目代码
├── ...
```

## 快速开始

### 方法 1: 使用设置脚本（推荐）

#### Windows (PowerShell)
```powershell
.\scripts\setup_dev_env.ps1
```

#### Linux/macOS
```bash
chmod +x scripts/setup_dev_env.sh
./scripts/setup_dev_env.sh
```

脚本会自动：
1. 检查 Python 版本
2. 创建虚拟环境（如果不存在）
3. 激活虚拟环境
4. 安装所有依赖
5. 配置 pre-commit hooks

### 方法 2: 手动创建

#### Windows (PowerShell)
```powershell
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
.\venv\Scripts\Activate.ps1

# 安装依赖
pip install -e ".[dev]"
```

#### Linux/macOS
```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
pip install -e ".[dev]"
```

## 激活虚拟环境

### 使用激活脚本

#### Windows
```powershell
.\scripts\activate_venv.ps1
```

#### Linux/macOS
```bash
source scripts/activate_venv.sh
```

### 手动激活

#### Windows (PowerShell)
```powershell
.\venv\Scripts\Activate.ps1
```

#### Windows (CMD)
```cmd
venv\Scripts\activate.bat
```

#### Linux/macOS
```bash
source venv/bin/activate
```

## 退出虚拟环境

```bash
deactivate
```

## Python 版本要求

项目要求 Python 3.10 或更高版本。

### 检查 Python 版本
```bash
python --version
# 或
python3 --version
```

### 使用 pyenv 管理 Python 版本

如果使用 pyenv，项目根目录的 `.python-version` 文件会自动指定 Python 版本：

```bash
# 安装指定版本的 Python
pyenv install 3.10.12

# 在项目目录中使用指定版本
pyenv local 3.10.12
```

## 依赖管理

### 安装依赖

项目使用 `pyproject.toml` 进行依赖管理（推荐）：

```bash
# 安装核心依赖
pip install -e .

# 安装开发依赖
pip install -e ".[dev]"

# 安装所有依赖（包括可选依赖）
pip install -e ".[all]"
```

### 使用 requirements.txt（备选）

如果更喜欢使用 requirements.txt：

```bash
# 安装核心依赖
pip install -r requirements.txt

# 安装开发依赖
pip install -r requirements-dev.txt
```

### 更新依赖

```bash
# 更新所有包
pip install --upgrade -e ".[dev]"

# 更新特定包
pip install --upgrade package-name
```

## 虚拟环境配置

### 虚拟环境目录结构

```
venv/
├── bin/              # Linux/macOS: 可执行文件
│   ├── activate      # 激活脚本
│   ├── python        # Python 解释器
│   └── ...
├── Scripts/          # Windows: 可执行文件
│   ├── Activate.ps1  # PowerShell 激活脚本
│   ├── activate.bat  # CMD 激活脚本
│   ├── python.exe    # Python 解释器
│   └── ...
├── lib/              # Python 库
└── pyvenv.cfg        # 虚拟环境配置
```

### 虚拟环境配置选项

创建虚拟环境时可以指定选项：

```bash
# 使用系统站点包（不推荐）
python -m venv venv --system-site-packages

# 指定 Python 解释器
python3.10 -m venv venv

# 不包含 pip（不推荐）
python -m venv venv --without-pip
```

## 常见问题

### 1. 虚拟环境激活失败

**问题**: PowerShell 执行策略限制

**解决**:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 2. 找不到 Python

**问题**: `python` 命令不存在

**解决**:
- Windows: 使用 `py` 命令或安装 Python 并添加到 PATH
- Linux/macOS: 使用 `python3` 命令

### 3. 虚拟环境损坏

**问题**: 虚拟环境无法正常工作

**解决**:
```bash
# 删除旧虚拟环境
rm -rf venv  # Linux/macOS
Remove-Item -Recurse -Force venv  # Windows PowerShell

# 重新创建
python -m venv venv
source venv/bin/activate  # 或 .\venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

### 4. 依赖冲突

**问题**: 安装依赖时出现版本冲突

**解决**:
```bash
# 查看冲突的包
pip check

# 更新冲突的包
pip install --upgrade package-name

# 或使用 pip-tools 管理依赖
pip install pip-tools
pip-compile pyproject.toml
```

## 最佳实践

1. **始终使用虚拟环境**: 不要使用系统 Python
2. **提交前检查**: 确保虚拟环境已激活
3. **定期更新**: 定期更新依赖包
4. **版本锁定**: 生产环境使用 `requirements.txt` 锁定版本
5. **文档化**: 记录任何特殊的虚拟环境配置

## 相关文件

- `.python-version` - Python 版本指定（pyenv）
- `pyproject.toml` - 项目配置和依赖定义
- `requirements.txt` - 核心依赖（备选）
- `requirements-dev.txt` - 开发依赖（备选）
- `.gitignore` - 忽略 `venv/` 目录

## 下一步

设置好虚拟环境后，可以：

1. 查看 [DEVELOPMENT.md](DEVELOPMENT.md) 了解开发流程
2. 查看 [TASKS.md](TASKS.md) 了解开发任务
3. 开始开发！

