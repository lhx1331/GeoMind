#!/bin/bash
# GeoMind 虚拟环境激活脚本 (Bash)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV_PATH="$PROJECT_ROOT/venv"

if [ ! -d "$VENV_PATH" ]; then
    echo "虚拟环境不存在，正在创建..."
    if ! command -v python3 &> /dev/null; then
        echo "错误: 未找到 Python，请先安装 Python 3.10+"
        exit 1
    fi
    
    python3 -m venv "$VENV_PATH"
    echo "虚拟环境创建成功！"
fi

echo "激活虚拟环境: $VENV_PATH"
source "$VENV_PATH/bin/activate"

echo "虚拟环境已激活！"
echo "提示: 使用 'deactivate' 退出虚拟环境"

