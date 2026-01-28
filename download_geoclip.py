"""
GeoCLIP 模型自动下载脚本

使用方法:
    python download_geoclip.py
"""

import sys
from pathlib import Path

def check_dependencies():
    """检查必要的依赖"""
    print("🔍 检查依赖...")
    
    missing_deps = []
    
    try:
        import huggingface_hub
        print("  ✅ huggingface_hub")
    except ImportError:
        missing_deps.append("huggingface_hub")
        print("  ❌ huggingface_hub (未安装)")
    
    if missing_deps:
        print(f"\n⚠️ 缺少依赖，请先安装:")
        print(f"   pip install {' '.join(missing_deps)}")
        return False
    
    return True


def download_geoclip(save_dir: str = "./models/geoclip"):
    """
    从 Hugging Face 下载 GeoCLIP 模型
    
    Args:
        save_dir: 保存目录
    """
    from huggingface_hub import snapshot_download
    
    print("\n" + "=" * 60)
    print("📥 GeoCLIP 模型下载工具")
    print("=" * 60)
    
    print(f"\n模型信息:")
    print(f"  - 名称: StreetCLIP (GeoCLIP)")
    print(f"  - 大小: 约 2-3 GB")
    print(f"  - 来源: Hugging Face")
    print(f"  - 保存位置: {save_dir}")
    
    # 创建目录
    save_path = Path(save_dir)
    save_path.mkdir(parents=True, exist_ok=True)
    print(f"\n✅ 创建目录: {save_path.absolute()}")
    
    # 下载提示
    print(f"\n⏳ 开始下载... (这可能需要 5-15 分钟)")
    print(f"   提示: 下载支持断点续传，可以随时中断后重新运行")
    
    try:
        # 下载模型
        snapshot_download(
            repo_id="geolocal/StreetCLIP",
            local_dir=save_dir,
            local_dir_use_symlinks=False,
            resume_download=True,  # 支持断点续传
        )
        
        print(f"\n✅ 下载完成！")
        
        # 验证文件
        print(f"\n📋 验证文件:")
        
        required_files = [
            "pytorch_model.bin",
            "config.json",
            "tokenizer.json",
        ]
        
        all_present = True
        for file_name in required_files:
            file_path = save_path / file_name
            if file_path.exists():
                size_mb = file_path.stat().st_size / (1024 * 1024)
                print(f"  ✅ {file_name} ({size_mb:.2f} MB)")
            else:
                print(f"  ❌ {file_name} (缺失)")
                all_present = False
        
        if all_present:
            print(f"\n🎉 GeoCLIP 模型已成功下载并验证！")
            print(f"\n📝 下一步:")
            print(f"   1. 确保 config.yaml 中配置了正确的模型路径:")
            print(f"      geoclip:")
            print(f"        model_path: \"{save_dir}\"")
            print(f"   2. 运行测试: python test_geoclip.py")
            return True
        else:
            print(f"\n⚠️ 部分文件缺失，请重新运行此脚本")
            return False
        
    except KeyboardInterrupt:
        print(f"\n\n⚠️ 下载被用户中断")
        print(f"   下次运行将从断点继续")
        return False
    
    except Exception as e:
        print(f"\n❌ 下载失败: {e}")
        print(f"\n💡 可能的解决方法:")
        print(f"   1. 检查网络连接")
        print(f"   2. 使用代理:")
        print(f"      export HTTP_PROXY=http://your-proxy:port")
        print(f"   3. 使用 Git LFS:")
        print(f"      git clone https://huggingface.co/geolocal/StreetCLIP {save_dir}")
        print(f"   4. 手动下载:")
        print(f"      访问 https://huggingface.co/geolocal/StreetCLIP")
        return False


def main():
    """主函数"""
    print("\n🚀 GeoMind - GeoCLIP 模型下载工具\n")
    
    # 检查依赖
    if not check_dependencies():
        sys.exit(1)
    
    # 下载模型
    save_dir = "./models/geoclip"
    
    # 如果用户提供了自定义路径
    if len(sys.argv) > 1:
        save_dir = sys.argv[1]
        print(f"使用自定义路径: {save_dir}")
    
    success = download_geoclip(save_dir)
    
    if success:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

