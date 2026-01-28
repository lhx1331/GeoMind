"""
GeoCLIP 模型测试脚本

验证 GeoCLIP 模型是否正确下载和配置。
"""

import asyncio
import sys
from pathlib import Path


def check_model_files():
    """检查模型文件是否存在"""
    print("=" * 60)
    print("📋 步骤 1: 检查模型文件")
    print("=" * 60)
    
    model_path = Path("./models/geoclip")
    
    if not model_path.exists():
        print(f"❌ 模型目录不存在: {model_path}")
        print(f"\n请先下载 GeoCLIP 模型:")
        print(f"   python download_geoclip.py")
        print(f"\n或使用 Git LFS:")
        print(f"   git clone https://huggingface.co/geolocal/StreetCLIP ./models/geoclip")
        return False
    
    print(f"✅ 找到模型目录: {model_path.absolute()}")
    
    # 检查必需文件
    required_files = {
        "pytorch_model.bin": "模型权重",
        "config.json": "模型配置",
        "tokenizer.json": "分词器",
    }
    
    all_present = True
    total_size = 0
    
    for file_name, description in required_files.items():
        file_path = model_path / file_name
        if file_path.exists():
            size_mb = file_path.stat().st_size / (1024 * 1024)
            total_size += size_mb
            print(f"✅ {file_name} ({size_mb:.2f} MB) - {description}")
        else:
            print(f"❌ {file_name} (缺失) - {description}")
            all_present = False
    
    if all_present:
        print(f"\n✅ 所有文件完整 (总大小: {total_size:.2f} MB)")
        return True
    else:
        print(f"\n❌ 缺少必需文件，请重新下载")
        return False


def check_dependencies():
    """检查 Python 依赖"""
    print("\n" + "=" * 60)
    print("📦 步骤 2: 检查依赖包")
    print("=" * 60)
    
    dependencies = {
        "torch": "PyTorch",
        "transformers": "Transformers",
        "PIL": "Pillow (图像处理)",
        "numpy": "NumPy",
    }
    
    missing = []
    
    for package, description in dependencies.items():
        try:
            __import__(package)
            print(f"✅ {description}")
        except ImportError:
            print(f"❌ {description} (未安装)")
            missing.append(package if package != "PIL" else "pillow")
    
    if missing:
        print(f"\n⚠️ 缺少依赖，请安装:")
        print(f"   pip install {' '.join(missing)}")
        return False
    
    # 检查 CUDA
    try:
        import torch
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            print(f"✅ CUDA 可用 ({gpu_name})")
        else:
            print(f"⚠️ CUDA 不可用，将使用 CPU (速度会慢 10-20 倍)")
    except:
        pass
    
    return True


async def test_model_loading():
    """测试模型加载"""
    print("\n" + "=" * 60)
    print("🔧 步骤 3: 测试模型加载")
    print("=" * 60)
    
    try:
        from geomind.models.geoclip import create_geoclip_model
        
        print("正在初始化 GeoCLIP 模型...")
        geoclip = create_geoclip_model()
        
        await geoclip.initialize()
        
        print("✅ GeoCLIP 模型加载成功！")
        
        await geoclip.cleanup()
        return True
        
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        print(f"\n请确保 GeoMind 已正确安装:")
        print(f"   pip install -e .")
        return False
    
    except FileNotFoundError as e:
        print(f"❌ 文件未找到: {e}")
        print(f"\n请检查:")
        print(f"   1. 模型文件是否完整")
        print(f"   2. config.yaml 中的路径配置是否正确")
        return False
    
    except Exception as e:
        print(f"❌ 加载失败: {e}")
        print(f"\n可能的原因:")
        print(f"   1. PyTorch 版本不兼容")
        print(f"   2. 显存不足 (如使用 GPU)")
        print(f"   3. 模型文件损坏")
        return False


async def test_image_encoding():
    """测试图像编码功能"""
    print("\n" + "=" * 60)
    print("🖼️ 步骤 4: 测试图像编码")
    print("=" * 60)
    
    try:
        from geomind.models.geoclip import create_geoclip_model
        from PIL import Image
        import numpy as np
        
        # 创建测试图像 (随机噪声)
        print("生成测试图像...")
        test_image = Image.fromarray(
            np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
        )
        
        # 初始化模型
        geoclip = create_geoclip_model()
        await geoclip.initialize()
        
        # 编码图像
        print("正在编码图像...")
        result = await geoclip.encode_image(test_image)
        
        if result.success:
            embedding = result.data
            print(f"✅ 图像编码成功")
            print(f"   嵌入向量维度: {len(embedding)}")
            print(f"   向量范数: {np.linalg.norm(embedding):.4f}")
        else:
            print(f"❌ 编码失败: {result.error}")
            await geoclip.cleanup()
            return False
        
        # 测试位置预测
        print("\n正在预测位置...")
        location_result = await geoclip.predict_location(test_image, top_k=3)
        
        if location_result.success:
            locations = location_result.data
            print(f"✅ 位置预测成功，返回 {len(locations)} 个候选")
            
            for i, loc in enumerate(locations, 1):
                print(f"   {i}. 坐标: ({loc['lat']:.4f}, {loc['lon']:.4f})")
                print(f"      得分: {loc['score']:.4f}")
        else:
            print(f"❌ 预测失败: {location_result.error}")
            await geoclip.cleanup()
            return False
        
        await geoclip.cleanup()
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def print_summary(results):
    """打印测试结果摘要"""
    print("\n" + "=" * 60)
    print("📊 测试结果摘要")
    print("=" * 60)
    
    total = len(results)
    passed = sum(results.values())
    
    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {test_name}")
    
    print(f"\n总计: {passed}/{total} 项测试通过")
    
    if passed == total:
        print("\n🎉 恭喜！GeoCLIP 配置完全正确，可以使用了！")
        print("\n📚 下一步:")
        print("   1. 在 GeoMind Agent 中使用 GeoCLIP")
        print("   2. 查看示例: examples/")
        print("   3. 阅读文档: docs/guides/geoclip_setup.md")
    else:
        print("\n⚠️ 部分测试失败，请根据上面的提示修复。")
        print("\n💡 需要帮助？")
        print("   - 查看文档: docs/guides/geoclip_setup.md")
        print("   - 重新下载: python download_geoclip.py")


async def main():
    """主测试函数"""
    print("\n🚀 GeoCLIP 模型测试\n")
    
    results = {}
    
    # 1. 检查模型文件
    results["模型文件"] = check_model_files()
    if not results["模型文件"]:
        print_summary(results)
        return
    
    # 2. 检查依赖
    results["依赖包"] = check_dependencies()
    if not results["依赖包"]:
        print_summary(results)
        return
    
    # 3. 测试模型加载
    results["模型加载"] = await test_model_loading()
    if not results["模型加载"]:
        print_summary(results)
        return
    
    # 4. 测试图像编码
    results["图像编码"] = await test_image_encoding()
    
    # 打印摘要
    print_summary(results)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️ 测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

