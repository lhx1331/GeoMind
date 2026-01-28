"""
Perception 节点使用示例

演示如何使用 Perception 节点从图像中提取地理线索。
"""

import asyncio
import sys
from pathlib import Path

from PIL import Image
import numpy as np

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from geomind.agent.nodes.perception import perception_node, perception_node_with_fallback
from geomind.agent.state import AgentState


async def example_1_basic_usage():
    """示例 1: 基础使用"""
    print("=" * 60)
    print("示例 1: Perception 节点基础使用")
    print("=" * 60)
    
    # 创建测试图像
    image = Image.new('RGB', (224, 224), color='blue')
    image_path = Path("test_perception_image.jpg")
    image.save(image_path)
    
    try:
        # 创建 Agent 状态
        state = AgentState(image_path=str(image_path))
        
        print(f"\n输入:")
        print(f"  图像路径: {state.image_path}")
        
        # 执行 Perception 节点
        print(f"\n执行 Perception 节点...")
        result = await perception_node(state)
        
        # 查看结果
        clues = result["clues"]
        
        print(f"\n✅ Perception 完成！")
        print(f"\n提取的线索:")
        print(f"  OCR 文本: {len(clues.ocr)} 个")
        for i, ocr in enumerate(clues.ocr[:3], 1):
            print(f"    {i}. {ocr.text} (置信度: {ocr.confidence:.2f})")
        
        print(f"\n  视觉特征: {len(clues.visual)} 个")
        for i, vf in enumerate(clues.visual[:3], 1):
            print(f"    {i}. {vf.type}: {vf.value} (置信度: {vf.confidence:.2f})")
        
        print(f"\n  元数据:")
        print(f"    GPS: {clues.meta.gps is not None}")
        print(f"    时间戳: {clues.meta.timestamp or 'N/A'}")
        print(f"    相机: {clues.meta.camera_info or 'N/A'}")
        
    finally:
        # 清理
        if image_path.exists():
            image_path.unlink()


async def example_2_with_fallback():
    """示例 2: 使用回退机制"""
    print("\n" + "=" * 60)
    print("示例 2: 使用回退机制")
    print("=" * 60)
    
    # 创建测试图像
    image = Image.new('RGB', (224, 224), color='green')
    image_path = Path("test_fallback_image.jpg")
    image.save(image_path)
    
    try:
        state = AgentState(image_path=str(image_path))
        
        print(f"\n执行带回退的 Perception 节点...")
        print(f"  如果 VLM 失败，将回退到仅使用 EXIF 数据")
        
        # 使用带回退的节点
        result = await perception_node_with_fallback(
            state,
            fallback_to_exif_only=True
        )
        
        clues = result["clues"]
        
        print(f"\n✅ Perception 完成（可能使用了回退）")
        print(f"\n提取的线索:")
        print(f"  OCR 文本: {len(clues.ocr)} 个")
        print(f"  视觉特征: {len(clues.visual)} 个")
        print(f"  元数据: {'有' if clues.meta.exif else '无'}")
        
    finally:
        if image_path.exists():
            image_path.unlink()


async def example_3_in_agent_workflow():
    """示例 3: 在 Agent 工作流中使用"""
    print("\n" + "=" * 60)
    print("示例 3: 在完整 Agent 工作流中使用")
    print("=" * 60)
    
    # 创建测试图像
    image = Image.new('RGB', (224, 224), color='red')
    image_path = Path("test_workflow_image.jpg")
    image.save(image_path)
    
    try:
        # 1. 初始化 Agent 状态
        state = AgentState(image_path=str(image_path))
        
        print(f"\n📍 PHRV 流程:")
        print(f"  [1/4] P (Perception)  ← 当前阶段")
        print(f"  [2/4] H (Hypothesis)")
        print(f"  [3/4] R (Retrieval)")
        print(f"  [4/4] V (Verification)")
        
        # 2. 执行 Perception 阶段
        print(f"\n🔍 执行 Perception 阶段...")
        perception_result = await perception_node(state)
        
        # 3. 更新状态
        state.clues = perception_result["clues"]
        
        print(f"\n✅ Perception 阶段完成")
        print(f"\n状态更新:")
        print(f"  图像路径: {state.image_path}")
        print(f"  线索已提取: ✓")
        print(f"    - OCR 文本: {len(state.clues.ocr)} 个")
        print(f"    - 视觉特征: {len(state.clues.visual)} 个")
        print(f"    - 元数据: {'有 GPS' if state.clues.meta.gps else '无 GPS'}")
        
        print(f"\n📝 下一步:")
        print(f"  → 进入 Hypothesis 阶段")
        print(f"  → 使用 LLM 根据线索生成地理假设")
        
    finally:
        if image_path.exists():
            image_path.unlink()


async def example_4_with_custom_vlm():
    """示例 4: 使用自定义 VLM 提供商"""
    print("\n" + "=" * 60)
    print("示例 4: 使用自定义 VLM 提供商")
    print("=" * 60)
    
    # 创建测试图像
    image = Image.new('RGB', (224, 224), color='yellow')
    image_path = Path("test_custom_vlm_image.jpg")
    image.save(image_path)
    
    try:
        state = AgentState(image_path=str(image_path))
        
        # 可以指定不同的 VLM 提供商
        vlm_providers = ["openai", "anthropic", "qwen", "glm"]
        
        print(f"\n支持的 VLM 提供商:")
        for provider in vlm_providers:
            print(f"  - {provider}")
        
        # 使用 OpenAI（示例）
        print(f"\n使用 VLM 提供商: openai")
        result = await perception_node(state, vlm_provider="openai")
        
        print(f"\n✅ 使用自定义 VLM 完成")
        
    except Exception as e:
        print(f"\n⚠️ 自定义 VLM 失败（可能需要 API Key）: {e}")
    finally:
        if image_path.exists():
            image_path.unlink()


async def main():
    """运行所有示例"""
    print("\n🚀 GeoMind Perception 节点使用示例\n")
    
    try:
        # 示例 1
        await example_1_basic_usage()
        
        # 示例 2
        await example_2_with_fallback()
        
        # 示例 3
        await example_3_in_agent_workflow()
        
        # 示例 4
        await example_4_with_custom_vlm()
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("✅ 所有示例运行完成！")
    print("=" * 60)
    
    print("\n📚 相关文档:")
    print("  - geomind/agent/nodes/perception.py")
    print("  - tests/unit/test_perception_node.py")
    print("  - docs/guides/quickstart.md")


if __name__ == "__main__":
    asyncio.run(main())

