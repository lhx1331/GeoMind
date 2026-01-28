# GeoMind 开发环境设置脚本 (PowerShell)

Write-Host "🚀 设置 GeoMind 开发环境..." -ForegroundColor Green

# 检查 Python 版本
$pythonVersion = python --version 2>&1
Write-Host "📌 $pythonVersion" -ForegroundColor Cyan

# 创建虚拟环境
if (-not (Test-Path "venv")) {
    Write-Host "📦 创建虚拟环境..." -ForegroundColor Yellow
    python -m venv venv
}

# 激活虚拟环境
Write-Host "🔌 激活虚拟环境..." -ForegroundColor Yellow
& .\venv\Scripts\Activate.ps1

# 升级 pip
Write-Host "⬆️  升级 pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

# 安装项目依赖
Write-Host "📥 安装项目依赖..." -ForegroundColor Yellow
pip install -e ".[dev]"

# 安装 pre-commit hooks
Write-Host "🔧 安装 pre-commit hooks..." -ForegroundColor Yellow
pre-commit install

# 创建必要的目录
Write-Host "📁 创建必要的目录..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path logs, models, tests\fixtures\images | Out-Null

# 复制环境变量模板
if (-not (Test-Path ".env")) {
    Write-Host "📋 复制环境变量模板..." -ForegroundColor Yellow
    Copy-Item env.example .env
    Write-Host "⚠️  请编辑 .env 文件并填入您的配置" -ForegroundColor Yellow
}

Write-Host "✅ 开发环境设置完成！" -ForegroundColor Green
Write-Host ""
Write-Host "下一步：" -ForegroundColor Cyan
Write-Host "1. 编辑 .env 文件并填入您的 API 密钥"
Write-Host "2. 运行 'pytest' 进行测试"
Write-Host "3. 运行 'pre-commit run --all-files' 检查代码格式"

