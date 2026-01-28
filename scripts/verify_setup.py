#!/usr/bin/env python3
"""
验证项目设置是否正确

运行此脚本检查项目结构、配置文件和依赖是否就绪。
"""

import sys
from pathlib import Path

# 颜色输出
class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    RESET = "\033[0m"


def print_success(msg):
    print(f"{Colors.GREEN}✓{Colors.RESET} {msg}")


def print_error(msg):
    print(f"{Colors.RED}✗{Colors.RESET} {msg}")


def print_warning(msg):
    print(f"{Colors.YELLOW}⚠{Colors.RESET} {msg}")


def print_info(msg):
    print(f"{Colors.BLUE}ℹ{Colors.RESET} {msg}")


def check_directory(path, required=True):
    """检查目录是否存在"""
    p = Path(path)
    if p.exists() and p.is_dir():
        print_success(f"目录存在: {path}")
        return True
    else:
        if required:
            print_error(f"目录不存在: {path}")
        else:
            print_warning(f"目录不存在（可选）: {path}")
        return False


def check_file(path, required=True):
    """检查文件是否存在"""
    p = Path(path)
    if p.exists() and p.is_file():
        print_success(f"文件存在: {path}")
        return True
    else:
        if required:
            print_error(f"文件不存在: {path}")
        else:
            print_warning(f"文件不存在（可选）: {path}")
        return False


def main():
    print_info("验证 GeoMind 项目设置...")
    print()

    errors = 0
    warnings = 0

    # 检查项目根目录文件
    print_info("检查项目根目录文件...")
    required_files = [
        "pyproject.toml",
        "README.md",
        "GUIDE.md",
        "TASKS.md",
        ".gitignore",
        ".pre-commit-config.yaml",
        "LICENSE",
        "env.example",
    ]
    for file in required_files:
        if not check_file(file):
            errors += 1

    print()

    # 检查目录结构
    print_info("检查目录结构...")
    required_dirs = [
        "geomind",
        "geomind/agent",
        "geomind/agent/nodes",
        "geomind/models",
        "geomind/tools",
        "geomind/tools/mcp",
        "geomind/prompts",
        "geomind/prompts/templates",
        "geomind/config",
        "geomind/utils",
        "tests",
        "tests/unit",
        "tests/integration",
        "tests/fixtures",
        "examples",
        "docs",
        "scripts",
    ]
    for dir_path in required_dirs:
        if not check_directory(dir_path):
            errors += 1

    print()

    # 检查 __init__.py 文件
    print_info("检查 Python 包文件...")
    init_files = [
        "geomind/__init__.py",
        "geomind/agent/__init__.py",
        "geomind/agent/nodes/__init__.py",
        "geomind/models/__init__.py",
        "geomind/tools/__init__.py",
        "geomind/tools/mcp/__init__.py",
        "geomind/prompts/__init__.py",
        "geomind/config/__init__.py",
        "geomind/utils/__init__.py",
        "tests/__init__.py",
        "tests/unit/__init__.py",
        "tests/integration/__init__.py",
    ]
    for init_file in init_files:
        if not check_file(init_file):
            errors += 1

    print()

    # 检查可选文件
    print_info("检查可选文件...")
    optional_files = [
        "tests/conftest.py",
        "DEVELOPMENT.md",
        "scripts/setup_dev_env.sh",
        "scripts/setup_dev_env.ps1",
    ]
    for file in optional_files:
        if not check_file(file, required=False):
            warnings += 1

    print()

    # 检查 Python 版本
    print_info("检查 Python 版本...")
    if sys.version_info >= (3, 10):
        print_success(f"Python 版本: {sys.version.split()[0]} (>= 3.10)")
    else:
        print_error(f"Python 版本: {sys.version.split()[0]} (需要 >= 3.10)")
        errors += 1

    print()

    # 总结
    print("=" * 50)
    if errors == 0:
        print_success(f"验证通过！所有必需项都已就绪。")
        if warnings > 0:
            print_warning(f"有 {warnings} 个可选项缺失，但不影响开发。")
        print()
        print_info("下一步:")
        print("  1. 运行 'pip install -e .[dev]' 安装依赖")
        print("  2. 运行 'pre-commit install' 安装 Git hooks")
        print("  3. 复制 env.example 为 .env 并配置")
        return 0
    else:
        print_error(f"验证失败！有 {errors} 个错误需要修复。")
        if warnings > 0:
            print_warning(f"还有 {warnings} 个警告。")
        return 1


if __name__ == "__main__":
    sys.exit(main())

