"""
验证 GeoCLIP 集成状态

快速检查 GeoCLIP 是否已正确集成到 GeoMind 项目中。
"""

import sys


def check_import():
    """检查是否可以导入 GeoCLIP"""
    print("🔍 检查 1: 导入测试")
    print("-" * 60)
    
    try:
        # 方式 1: 从 models 包导入
        from geomind.models import GeoCLIP, create_geoclip, create_geoclip_model
        print("✅ 从 geomind.models 导入成功")
        
        # 方式 2: 直接从 geoclip 模块导入
        from geomind.models.geoclip import GeoCLIP as GeoCLIP2
        print("✅ 从 geomind.models.geoclip 导入成功")
        
        # 检查类
        print(f"✅ GeoCLIP 类: {GeoCLIP}")
        print(f"✅ create_geoclip_model 函数: {create_geoclip_model}")
        print(f"✅ create_geoclip 函数: {create_geoclip}")
        
        return True
        
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return False


def check_config():
    """检查配置是否正确"""
    print("\n🔍 检查 2: 配置测试")
    print("-" * 60)
    
    try:
        from geomind.config import get_settings
        
        settings = get_settings()
        
        print(f"✅ 配置加载成功")
        print(f"   GeoCLIP 模型路径: {settings.geoclip.model_path}")
        print(f"   GeoCLIP 设备: {settings.geoclip.device}")
        print(f"   Top-K: {settings.geoclip.top_k}")
        print(f"   启用缓存: {settings.geoclip.cache_embeddings}")
        
        return True
        
    except Exception as e:
        print(f"❌ 配置加载失败: {e}")
        return False


def check_state_integration():
    """检查与 Agent State 的集成"""
    print("\n🔍 检查 3: Agent State 集成")
    print("-" * 60)
    
    try:
        from geomind.agent.state import Candidate
        
        # 测试创建 Candidate（模拟 GeoCLIP 输出）
        candidate = Candidate(
            name="Test Location",
            lat=35.6812,
            lon=139.7671,
            source="geoclip",
            score=0.85
        )
        
        print(f"✅ Candidate 模型可用")
        print(f"   名称: {candidate.name}")
        print(f"   坐标: ({candidate.lat}, {candidate.lon})")
        print(f"   来源: {candidate.source}")
        print(f"   得分: {candidate.score}")
        
        return True
        
    except Exception as e:
        print(f"❌ State 集成失败: {e}")
        return False


def check_functionality():
    """检查基本功能"""
    print("\n🔍 检查 4: 基本功能测试")
    print("-" * 60)
    
    try:
        import asyncio
        from geomind.models.geoclip import create_geoclip_model
        from PIL import Image
        import numpy as np
        
        async def test_func():
            # 创建模型
            geoclip = create_geoclip_model()
            print("✅ 模型创建成功")
            
            # 初始化
            await geoclip.initialize()
            print("✅ 模型初始化成功")
            
            # 创建测试图像
            test_image = Image.fromarray(
                np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
            )
            print("✅ 测试图像创建成功")
            
            # 编码图像
            encode_result = await geoclip.encode_image(test_image)
            if encode_result.success:
                print(f"✅ 图像编码成功 (维度: {len(encode_result.data)})")
            else:
                print(f"❌ 图像编码失败: {encode_result.error}")
                return False
            
            # 预测位置
            location_result = await geoclip.predict_location(test_image, top_k=3)
            if location_result.success:
                print(f"✅ 位置预测成功 (候选数: {len(location_result.data)})")
                
                # 显示第一个候选
                if location_result.data:
                    loc = location_result.data[0]
                    print(f"   最佳候选: ({loc['lat']:.4f}, {loc['lon']:.4f})")
                    print(f"   得分: {loc['score']:.4f}")
            else:
                print(f"❌ 位置预测失败: {location_result.error}")
                return False
            
            # 清理
            await geoclip.cleanup()
            print("✅ 模型清理成功")
            
            return True
        
        result = asyncio.run(test_func())
        return result
        
    except Exception as e:
        print(f"❌ 功能测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("🚀 GeoMind GeoCLIP 集成验证")
    print("=" * 60 + "\n")
    
    results = {}
    
    # 运行所有检查
    results["导入"] = check_import()
    results["配置"] = check_config()
    results["State集成"] = check_state_integration()
    results["基本功能"] = check_functionality()
    
    # 打印总结
    print("\n" + "=" * 60)
    print("📊 验证结果总结")
    print("=" * 60)
    
    for name, passed in results.items():
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{status} - {name}")
    
    total = len(results)
    passed = sum(results.values())
    
    print(f"\n总计: {passed}/{total} 项检查通过")
    
    if passed == total:
        print("\n🎉 恭喜！GeoCLIP 已完全集成到 GeoMind 项目中！")
        print("\n📚 下一步:")
        print("   1. 查看示例: python examples/use_geoclip.py")
        print("   2. 阅读文档: GeoCLIP集成确认.md")
        print("   3. 开始使用 GeoCLIP 开发 Agent")
        return 0
    else:
        print("\n⚠️ 部分检查失败，请查看上面的错误信息。")
        print("\n💡 需要帮助？")
        print("   - 查看文档: GeoCLIP集成确认.md")
        print("   - 运行测试: python test_geoclip.py")
        return 1


if __name__ == "__main__":
    sys.exit(main())

