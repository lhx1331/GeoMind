"""
GeoMind 配置测试脚本

使用此脚本验证您的配置是否正确。
"""

import asyncio
import sys
from pathlib import Path


def check_config_file():
    """检查配置文件是否存在"""
    print("=" * 60)
    print("📋 步骤 1: 检查配置文件")
    print("=" * 60)
    
    config_file = Path("config.yaml")
    if config_file.exists():
        print(f"✅ 找到配置文件: {config_file}")
        return True
    else:
        print(f"❌ 配置文件不存在: {config_file}")
        print(f"   请确保 config.yaml 在项目根目录")
        return False


def check_geoclip_model():
    """检查 GeoCLIP 模型文件"""
    print("\n" + "=" * 60)
    print("🗺️ 步骤 2: 检查 GeoCLIP 模型")
    print("=" * 60)
    
    model_path = Path("./models/geoclip")
    
    if not model_path.exists():
        print(f"❌ GeoCLIP 模型目录不存在: {model_path}")
        print(f"\n   请下载 GeoCLIP 模型:")
        print(f"   git clone https://huggingface.co/geolocal/StreetCLIP ./models/geoclip")
        return False
    
    # 检查关键文件
    required_files = ["config.json", "pytorch_model.bin"]
    missing_files = []
    
    for file_name in required_files:
        file_path = model_path / file_name
        if file_path.exists():
            print(f"✅ 找到文件: {file_name}")
        else:
            print(f"❌ 缺少文件: {file_name}")
            missing_files.append(file_name)
    
    if missing_files:
        print(f"\n⚠️ 缺少 {len(missing_files)} 个必需文件")
        return False
    
    print(f"✅ GeoCLIP 模型文件完整")
    return True


async def test_llm():
    """测试 LLM (DeepSeek)"""
    print("\n" + "=" * 60)
    print("🧠 步骤 3: 测试 DeepSeek LLM")
    print("=" * 60)
    
    try:
        from geomind.config import get_settings
        from geomind.models.llm import create_llm
        
        settings = get_settings()
        print(f"配置加载成功")
        print(f"  Provider: {settings.llm.provider}")
        print(f"  Model: {settings.llm.deepseek_model}")
        
        # 检查 API Key
        if not settings.llm.deepseek_api_key or settings.llm.deepseek_api_key == "your_deepseek_api_key_here":
            print(f"\n❌ DeepSeek API Key 未配置")
            print(f"   请在 config.yaml 中填入您的 API Key")
            return False
        
        print(f"✅ API Key 已配置: {settings.llm.deepseek_api_key[:8]}...")
        
        # 测试 LLM 调用
        print(f"\n正在测试 API 调用...")
        llm = create_llm(provider="deepseek")
        await llm.initialize()
        
        response = await llm.generate(
            prompt="请回复：配置成功",
            system_prompt="你是一个测试助手"
        )
        
        print(f"✅ DeepSeek 响应成功")
        print(f"   响应内容: {response.data[:100]}...")
        
        await llm.cleanup()
        return True
        
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        print(f"   请确保已安装所有依赖: pip install -e .")
        return False
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        print(f"\n   可能的原因:")
        print(f"   1. API Key 不正确")
        print(f"   2. 网络连接问题")
        print(f"   3. API 服务不可用")
        return False


async def test_vlm():
    """测试 VLM (GLM-4V)"""
    print("\n" + "=" * 60)
    print("👁️ 步骤 4: 测试 GLM-4V VLM")
    print("=" * 60)
    
    try:
        from geomind.config import get_settings
        from geomind.models.vlm import create_vlm
        
        settings = get_settings()
        print(f"配置加载成功")
        print(f"  Provider: {settings.vlm.provider}")
        print(f"  Model: {settings.vlm.glm_model}")
        
        # 检查 API Key
        if not settings.vlm.glm_api_key or settings.vlm.glm_api_key == "your_new_glm_api_key_here":
            print(f"\n❌ GLM API Key 未配置")
            print(f"   请在 config.yaml 中填入您的 GLM API Key")
            return False
        
        print(f"✅ API Key 已配置: {settings.vlm.glm_api_key[:8]}...")
        
        # 测试 VLM 初始化
        print(f"\n正在初始化 VLM...")
        vlm = create_vlm(provider="glm")
        await vlm.initialize()
        
        print(f"✅ GLM-4V 初始化成功")
        
        await vlm.cleanup()
        return True
        
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        return False
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        print(f"\n   可能的原因:")
        print(f"   1. API Key 不正确")
        print(f"   2. 网络连接问题")
        print(f"   3. API 服务不可用")
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
        print("\n🎉 恭喜！所有配置测试通过，您可以开始使用 GeoMind 了！")
        print("\n📚 下一步:")
        print("   1. 阅读快速开始指南: docs/guides/quickstart.md")
        print("   2. 查看示例代码: examples/")
        print("   3. 运行示例: python examples/basic_usage.py")
    else:
        print("\n⚠️ 部分测试失败，请根据上面的提示修复问题。")
        print("\n💡 需要帮助？")
        print("   - 查看配置指南: 配置指南.md")
        print("   - 查看文档: docs/guides/")


async def main():
    """主测试函数"""
    print("\n🚀 GeoMind 配置测试")
    print("=" * 60)
    print("此脚本将验证您的配置是否正确\n")
    
    results = {}
    
    # 1. 检查配置文件
    results["配置文件"] = check_config_file()
    if not results["配置文件"]:
        print_summary(results)
        return
    
    # 2. 检查 GeoCLIP 模型
    results["GeoCLIP 模型"] = check_geoclip_model()
    
    # 3. 测试 LLM
    results["DeepSeek LLM"] = await test_llm()
    
    # 4. 测试 VLM
    results["GLM-4V VLM"] = await test_vlm()
    
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

