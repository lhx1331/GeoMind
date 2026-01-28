"""
GeoMind Agent 使用示例

演示如何使用 GeoMind Agent 进行地理位置推理。
"""

import asyncio
import sys
from pathlib import Path

from PIL import Image

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from geomind import GeoMindAgent, geolocate


async def example_1_basic_usage():
    """示例 1: 基础使用"""
    print("=" * 80)
    print("示例 1: GeoMind Agent 基础使用")
    print("=" * 80)
    
    # 创建测试图像
    image = Image.new('RGB', (224, 224), color='blue')
    image_path = Path("test_agent_image.jpg")
    image.save(image_path)
    
    try:
        # 1. 创建 Agent
        print(f"\n创建 GeoMind Agent...")
        agent = GeoMindAgent()
        
        print(f"Agent: {agent}")
        
        # 2. 预测位置
        print(f"\n预测图像位置: {image_path}")
        prediction = await agent.geolocate(str(image_path))
        
        # 3. 查看结果
        print(f"\n✅ 预测完成！")
        print(f"\n预测位置:")
        print(f"  纬度: {prediction.lat:.6f}")
        print(f"  经度: {prediction.lon:.6f}")
        print(f"  置信度: {prediction.confidence:.2%}")
        
        print(f"\n推理过程:")
        print(f"  {prediction.reasoning}")
        
        if prediction.supporting_evidence:
            print(f"\n支持证据:")
            for evidence in prediction.supporting_evidence:
                print(f"  • {evidence}")
        
        if prediction.alternative_locations:
            print(f"\n备选位置: {len(prediction.alternative_locations)} 个")
            for i, alt in enumerate(prediction.alternative_locations[:3], 1):
                print(f"  {i}. {alt.get('name', 'Unknown')}")
        
    finally:
        if image_path.exists():
            image_path.unlink()


async def example_2_convenience_function():
    """示例 2: 使用便捷函数"""
    print("\n" + "=" * 80)
    print("示例 2: 使用便捷函数")
    print("=" * 80)
    
    # 创建测试图像
    image = Image.new('RGB', (224, 224), color='green')
    image_path = Path("test_convenience.jpg")
    image.save(image_path)
    
    try:
        print(f"\n无需创建 Agent 实例，直接调用 geolocate()...")
        
        # 直接调用便捷函数
        prediction = await geolocate(str(image_path))
        
        print(f"\n✅ 预测完成！")
        print(f"位置: ({prediction.lat:.4f}, {prediction.lon:.4f})")
        print(f"置信度: {prediction.confidence:.2%}")
        
    finally:
        if image_path.exists():
            image_path.unlink()


async def example_3_with_full_state():
    """示例 3: 获取完整状态"""
    print("\n" + "=" * 80)
    print("示例 3: 获取完整状态")
    print("=" * 80)
    
    # 创建测试图像
    image = Image.new('RGB', (224, 224), color='red')
    image_path = Path("test_full_state.jpg")
    image.save(image_path)
    
    try:
        agent = GeoMindAgent()
        
        print(f"\n获取完整的 Agent 状态...")
        
        # 获取完整状态
        state = await agent.geolocate(str(image_path), return_full_state=True)
        
        print(f"\n✅ 完成！")
        
        # 获取状态摘要
        summary = agent.get_state_summary(state)
        
        print(f"\n状态摘要:")
        print(f"  图像: {summary['image_path']}")
        print(f"\n  线索:")
        print(f"    - OCR 文本: {summary['clues']['ocr_count']} 个")
        print(f"    - 视觉特征: {summary['clues']['visual_count']} 个")
        print(f"    - GPS: {'有' if summary['clues']['has_gps'] else '无'}")
        print(f"\n  假设:")
        print(f"    - 数量: {summary['hypotheses']['count']} 个")
        print(f"    - 最高置信度: {summary['hypotheses']['top_confidence']:.2f}")
        print(f"\n  候选:")
        print(f"    - 数量: {summary['candidates']['count']} 个")
        print(f"    - 最高分数: {summary['candidates']['top_score']:.2f}")
        print(f"\n  预测:")
        if summary['prediction']:
            print(f"    - 位置: ({summary['prediction']['lat']:.4f}, {summary['prediction']['lon']:.4f})")
            print(f"    - 置信度: {summary['prediction']['confidence']:.2%}")
        
    finally:
        if image_path.exists():
            image_path.unlink()


async def example_4_iterative_mode():
    """示例 4: 迭代优化模式"""
    print("\n" + "=" * 80)
    print("示例 4: 迭代优化模式")
    print("=" * 80)
    
    # 创建测试图像
    image = Image.new('RGB', (224, 224), color='yellow')
    image_path = Path("test_iterative.jpg")
    image.save(image_path)
    
    try:
        print(f"\n创建支持迭代优化的 Agent...")
        
        # 创建迭代式 Agent
        agent = GeoMindAgent(
            enable_iterations=True,
            max_iterations=2,
        )
        
        print(f"Agent: {agent}")
        print(f"  • 迭代优化: 启用")
        print(f"  • 最大迭代: 2 次")
        
        print(f"\n预测位置（可能会进行多次优化）...")
        
        prediction = await agent.geolocate(str(image_path))
        
        print(f"\n✅ 预测完成！")
        print(f"位置: ({prediction.lat:.4f}, {prediction.lon:.4f})")
        print(f"置信度: {prediction.confidence:.2%}")
        
        print(f"\n💡 迭代优化可以提高预测准确性")
        
    finally:
        if image_path.exists():
            image_path.unlink()


async def example_5_batch_processing():
    """示例 5: 批量处理"""
    print("\n" + "=" * 80)
    print("示例 5: 批量处理多个图像")
    print("=" * 80)
    
    # 创建多个测试图像
    image_paths = []
    for i in range(3):
        image = Image.new('RGB', (224, 224), color=['red', 'green', 'blue'][i])
        image_path = Path(f"test_batch_{i}.jpg")
        image.save(image_path)
        image_paths.append(str(image_path))
    
    try:
        agent = GeoMindAgent()
        
        print(f"\n批量处理 {len(image_paths)} 个图像...")
        
        # 批量处理
        predictions = await agent.batch_geolocate(image_paths)
        
        print(f"\n✅ 批量处理完成！")
        print(f"\n结果:")
        
        for i, (path, pred) in enumerate(zip(image_paths, predictions), 1):
            print(f"\n  {i}. {Path(path).name}")
            print(f"     位置: ({pred.lat:.4f}, {pred.lon:.4f})")
            print(f"     置信度: {pred.confidence:.2%}")
        
    finally:
        # 清理
        for path in image_paths:
            Path(path).unlink(missing_ok=True)


async def example_6_error_handling():
    """示例 6: 错误处理"""
    print("\n" + "=" * 80)
    print("示例 6: 错误处理")
    print("=" * 80)
    
    agent = GeoMindAgent()
    
    # 1. 文件不存在
    print(f"\n测试 1: 文件不存在")
    try:
        await agent.geolocate("nonexistent_file.jpg")
    except FileNotFoundError as e:
        print(f"  ✓ 捕获预期错误: {type(e).__name__}")
        print(f"    {e}")
    
    # 2. 无效路径
    print(f"\n测试 2: 无效路径")
    try:
        await agent.geolocate("")
    except (FileNotFoundError, ValueError) as e:
        print(f"  ✓ 捕获预期错误: {type(e).__name__}")
    
    print(f"\n✅ 错误处理正常")


async def example_7_real_world_usage():
    """示例 7: 真实使用场景"""
    print("\n" + "=" * 80)
    print("示例 7: 真实使用场景")
    print("=" * 80)
    
    print(f"\n场景: 旅行照片地理定位")
    
    # 模拟真实照片（这里用测试图像代替）
    image = Image.new('RGB', (224, 224), color='purple')
    image_path = Path("travel_photo.jpg")
    image.save(image_path)
    
    try:
        # 创建 Agent
        agent = GeoMindAgent(enable_iterations=True)
        
        print(f"\n分析旅行照片: {image_path}")
        print(f"  1️⃣ 提取视觉线索（地标、文字、建筑风格）")
        print(f"  2️⃣ 生成地理假设（可能的国家/城市）")
        print(f"  3️⃣ 召回候选地点（基于 GeoCLIP）")
        print(f"  4️⃣ 验证并预测（OCR-POI 匹配、语言先验）")
        
        # 预测
        prediction = await agent.geolocate(str(image_path))
        
        print(f"\n📍 预测结果:")
        print(f"  位置: {prediction.lat:.4f}°N, {prediction.lon:.4f}°E")
        print(f"  置信度: {prediction.confidence:.2%}")
        print(f"  推理: {prediction.reasoning}")
        
        print(f"\n💡 应用场景:")
        print(f"  • 旅行照片整理")
        print(f"  • 社交媒体地理标记")
        print(f"  • 新闻图像验证")
        print(f"  • 历史照片归档")
        
    finally:
        if image_path.exists():
            image_path.unlink()


async def main():
    """运行所有示例"""
    print("\n" + "=" * 80)
    print("🌍 GeoMind Agent 使用示例")
    print("=" * 80)
    
    try:
        # 示例 1
        await example_1_basic_usage()
        
        # 示例 2
        await example_2_convenience_function()
        
        # 示例 3
        await example_3_with_full_state()
        
        # 示例 4
        await example_4_iterative_mode()
        
        # 示例 5
        await example_5_batch_processing()
        
        # 示例 6
        await example_6_error_handling()
        
        # 示例 7
        await example_7_real_world_usage()
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("✅ 所有示例运行完成！")
    print("=" * 80)
    
    print("\n📚 更多信息:")
    print("  - API 文档: docs/api/")
    print("  - 快速开始: 快速开始.md")
    print("  - 配置指南: 配置指南.md")
    
    print("\n🎉 GeoMind Agent 已准备就绪！")


if __name__ == "__main__":
    asyncio.run(main())

