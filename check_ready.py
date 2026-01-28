"""
GeoMind 运行前检查脚本

检查项目是否已准备好运行，包括：
- 依赖安装
- 配置文件
- API Keys
- GeoCLIP 模型
- 示例图片
"""

import sys
from pathlib import Path
from typing import List, Tuple

# 颜色输出
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(text: str):
    """打印标题"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text:^60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}\n")

def print_check(name: str, status: bool, message: str = ""):
    """打印检查结果"""
    icon = f"{Colors.GREEN}[OK]{Colors.RESET}" if status else f"{Colors.RED}[X]{Colors.RESET}"
    status_text = f"{Colors.GREEN}通过{Colors.RESET}" if status else f"{Colors.RED}未通过{Colors.RESET}"
    print(f"  {icon} {name:30} {status_text:10} {message}")

def check_python_version() -> Tuple[bool, str]:
    """检查 Python 版本"""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 10:
        return True, f"Python {version.major}.{version.minor}.{version.micro}"
    return False, f"需要 Python 3.10+，当前: {version.major}.{version.minor}.{version.micro}"

def check_dependencies() -> Tuple[bool, str]:
    """检查依赖是否安装"""
    # 包名到导入名的映射
    package_map = {
        "langchain": "langchain",
        "langgraph": "langgraph",
        "pydantic": "pydantic",
        "pillow": "PIL",  # Pillow 包的导入名是 PIL
        "httpx": "httpx",
        "click": "click",
        "opencv-python": "cv2",  # opencv-python 的导入名是 cv2
        "exifread": "exifread",
        "pyyaml": "yaml",
    }
    
    missing = []
    for pkg_name, import_name in package_map.items():
        try:
            __import__(import_name)
        except ImportError:
            missing.append(pkg_name)
    
    if missing:
        return False, f"缺失: {', '.join(missing)}"
    return True, "所有核心依赖已安装"

def check_config_file() -> Tuple[bool, str]:
    """检查配置文件"""
    config_path = Path("config.yaml")
    if not config_path.exists():
        return False, "config.yaml 不存在"
    
    # 检查配置内容
    try:
        import yaml
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # 检查关键配置
        issues = []
        if config.get("llm", {}).get("deepseek_api_key", "").startswith("your_"):
            issues.append("DeepSeek API Key 未配置")
        if config.get("vlm", {}).get("glm_api_key", "").startswith("your_"):
            issues.append("GLM-4V API Key 未配置")
        
        if issues:
            return False, "; ".join(issues)
        return True, "配置文件完整"
    except Exception as e:
        return False, f"配置文件格式错误: {e}"

def check_geoclip_model() -> Tuple[bool, str]:
    """检查 GeoCLIP 模型"""
    model_path = Path("models/geoclip")
    if not model_path.exists():
        return False, "GeoCLIP 模型目录不存在"
    
    # 检查关键文件
    required_files = [
        "config.json",
        "pytorch_model.bin",  # 或 model.safetensors
    ]
    missing = []
    for file in required_files:
        if not (model_path / file).exists():
            # 检查是否有 safetensors 格式
            if file == "pytorch_model.bin":
                if not (model_path / "model.safetensors").exists():
                    missing.append(file)
            else:
                missing.append(file)
    
    if missing:
        return False, f"缺失文件: {', '.join(missing)}"
    return True, "GeoCLIP 模型已下载"

def check_example_images() -> Tuple[bool, str]:
    """检查示例图片"""
    # 检查常见的图片目录
    image_dirs = [
        Path("examples/images"),
        Path("images"),
        Path("test_images"),
    ]
    
    for img_dir in image_dirs:
        if img_dir.exists():
            images = list(img_dir.glob("*.jpg")) + list(img_dir.glob("*.png"))
            if images:
                return True, f"找到 {len(images)} 张示例图片"
    
    return False, "未找到示例图片（可选）"

def check_cli_installed() -> Tuple[bool, str]:
    """检查 CLI 是否已安装"""
    try:
        import subprocess
        result = subprocess.run(
            ["geomind", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return True, "CLI 已安装"
        return False, "CLI 未安装（运行: pip install -e .）"
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False, "CLI 未安装（运行: pip install -e .）"

def main():
    """主检查函数"""
    print_header("GeoMind 运行前检查")
    
    checks = []
    
    # 1. Python 版本
    print(f"\n{Colors.BOLD}1. 环境检查{Colors.RESET}")
    status, msg = check_python_version()
    print_check("Python 版本", status, msg)
    checks.append(("Python 版本", status))
    
    # 2. 依赖安装
    status, msg = check_dependencies()
    print_check("依赖包", status, msg)
    checks.append(("依赖包", status))
    
    # 3. CLI 安装
    status, msg = check_cli_installed()
    print_check("CLI 工具", status, msg)
    checks.append(("CLI 工具", status))
    
    # 4. 配置文件
    print(f"\n{Colors.BOLD}2. 配置检查{Colors.RESET}")
    status, msg = check_config_file()
    print_check("配置文件", status, msg)
    checks.append(("配置文件", status))
    
    # 5. GeoCLIP 模型
    print(f"\n{Colors.BOLD}3. 模型检查{Colors.RESET}")
    status, msg = check_geoclip_model()
    print_check("GeoCLIP 模型", status, msg)
    checks.append(("GeoCLIP 模型", status))
    
    # 6. 示例图片（可选）
    print(f"\n{Colors.BOLD}4. 资源检查（可选）{Colors.RESET}")
    status, msg = check_example_images()
    print_check("示例图片", status, msg)
    # 示例图片不是必需的，不加入 checks
    
    # 总结
    print_header("检查结果")
    
    passed = sum(1 for _, status in checks if status)
    total = len(checks)
    
    if passed == total:
        print(f"\n{Colors.GREEN}{Colors.BOLD}[SUCCESS] 恭喜！项目已准备好运行！{Colors.RESET}\n")
        print(f"{Colors.BOLD}下一步：{Colors.RESET}")
        print(f"  1. 运行 CLI: {Colors.BLUE}geomind locate --image <图片路径>{Colors.RESET}")
        print(f"  2. 运行 Python: {Colors.BLUE}python examples/use_geomind_agent.py{Colors.RESET}")
        print(f"  3. 启动 API: {Colors.BLUE}python -m geomind.api.app{Colors.RESET}")
        return 0
    else:
        print(f"\n{Colors.YELLOW}{Colors.BOLD}[WARNING] 还有 {total - passed} 项需要完成{Colors.RESET}\n")
        print(f"{Colors.BOLD}待办事项：{Colors.RESET}")
        
        for name, status in checks:
            if not status:
                print(f"  {Colors.RED}[X]{Colors.RESET} {name}")
        
        print(f"\n{Colors.BOLD}快速修复：{Colors.RESET}")
        print(f"  1. 安装依赖: {Colors.BLUE}pip install -e .{Colors.RESET}")
        print(f"  2. 配置 API Keys: {Colors.BLUE}编辑 config.yaml{Colors.RESET}")
        print(f"  3. 下载 GeoCLIP: {Colors.BLUE}python download_geoclip.py{Colors.RESET}")
        print(f"\n详细说明请查看: {Colors.BLUE}快速开始.md{Colors.RESET}")
        return 1

if __name__ == "__main__":
    sys.exit(main())

