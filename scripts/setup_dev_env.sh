#!/bin/bash
# 开发环境设置脚本

set -e

echo "🚀 设置 GeoMind 开发环境..."

# 检查 Python 版本
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "📌 Python 版本: $python_version"

# 创建虚拟环境
if [ ! -d "venv" ]; then
    echo "📦 创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
echo "🔌 激活虚拟环境..."
source venv/bin/activate

# 升级 pip
echo "⬆️  升级 pip..."
pip install --upgrade pip

# 安装项目依赖
echo "📥 安装项目依赖..."
pip install -e ".[dev]"

# 安装 pre-commit hooks
echo "🔧 安装 pre-commit hooks..."
pre-commit install

# 创建必要的目录
echo "📁 创建必要的目录..."
mkdir -p logs
mkdir -p models
mkdir -p tests/fixtures/images

# 复制环境变量模板
if [ ! -f ".env" ]; then
    echo "📋 复制环境变量模板..."
    cp env.example .env
    echo "⚠️  请编辑 .env 文件并填入您的配置"
fi

echo "✅ 开发环境设置完成！"
echo ""
echo "下一步："
echo "1. 编辑 .env 文件并填入您的 API 密钥"
echo "2. 运行 'pytest' 进行测试"
echo "3. 运行 'pre-commit run --all-files' 检查代码格式"

