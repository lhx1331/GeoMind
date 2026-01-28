"""
Hypothesis 节点使用示例

演示如何使用 Hypothesis 节点根据线索生成地理假设。
"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from geomind.agent.nodes.hypothesis import (
    create_clues_summary,
    hypothesis_node,
    hypothesis_node_iterative,
    hypothesis_node_with_validation,
)
from geomind.agent.state import AgentState, Clues, Metadata, OCRText, VisualFeature


async def example_1_basic_usage():
    """示例 1: 基础使用"""
    print("=" * 60)
    print("示例 1: Hypothesis 节点基础使用")
    print("=" * 60)
    
    # 创建测试线索（模拟 Perception 阶段的输出）
    clues = Clues(
        ocr=[
            OCRText(text="Shibuya Crossing", bbox=[100, 200, 300, 250], confidence=0.95),
            OCRText(text="渋谷", bbox=[100, 260, 300, 310], confidence=0.90),
            OCRText(text="Tokyo", bbox=[310, 200, 400, 250], confidence=0.85),
        ],
        visual=[
            VisualFeature(type="landmark", value="busy intersection", confidence=0.90),
            VisualFeature(type="urban", value="modern city", confidence=0.85),
            VisualFeature(type="signage", value="Japanese characters", confidence=0.88),
        ],
        meta=Metadata(
            scene_type="urban",
            time_of_day="day",
        ),
    )
    
    # 创建 Agent 状态
    state = AgentState(
        image_path="test_image.jpg",
        clues=clues,
    )
    
    print(f"\n输入线索:")
    print(f"  OCR 文本: {len(clues.ocr)} 个")
    for ocr in clues.ocr:
        print(f"    - {ocr.text} (置信度: {ocr.confidence:.2f})")
    
    print(f"\n  视觉特征: {len(clues.visual)} 个")
    for vf in clues.visual:
        print(f"    - {vf.type}: {vf.value} (置信度: {vf.confidence:.2f})")
    
    # 执行 Hypothesis 节点
    print(f"\n执行 Hypothesis 节点...")
    result = await hypothesis_node(state)
    
    # 查看结果
    hypotheses = result["hypotheses"]
    
    print(f"\n✅ Hypothesis 完成！")
    print(f"\n生成的地理假设: {len(hypotheses)} 个")
    
    for i, h in enumerate(hypotheses, 1):
        print(f"\n假设 {i}:")
        print(f"  区域: {h.region}")
        print(f"  置信度: {h.confidence:.2f}")
        print(f"  推理: {h.rationale}")
        print(f"  支持证据: {', '.join(h.supporting) if h.supporting else '无'}")
        print(f"  冲突证据: {', '.join(h.conflicting) if h.conflicting else '无'}")


async def example_2_clues_summary():
    """示例 2: 线索摘要"""
    print("\n" + "=" * 60)
    print("示例 2: 创建线索摘要")
    print("=" * 60)
    
    # 创建丰富的线索
    clues = Clues(
        ocr=[
            OCRText(text="Big Ben", bbox=[50, 100, 200, 150], confidence=0.98),
            OCRText(text="Westminster", bbox=[50, 160, 200, 200], confidence=0.92),
        ],
        visual=[
            VisualFeature(type="landmark", value="clock tower", confidence=0.95),
            VisualFeature(type="architecture", value="Gothic style", confidence=0.88),
        ],
        meta=Metadata(
            gps={"GPSLatitude": 51.5007, "GPSLongitude": -0.1246},
            timestamp="2024:06:15 14:30:00",
            camera_info="iPhone 15 Pro",
        ),
    )
    
    # 创建摘要
    summary = create_clues_summary(clues)
    
    print(f"\n线索摘要:")
    print("-" * 60)
    print(summary)
    print("-" * 60)
    
    print(f"\n📝 这个摘要将被发送给 LLM 进行假设生成")


async def example_3_with_validation():
    """示例 3: 使用验证过滤"""
    print("\n" + "=" * 60)
    print("示例 3: 使用验证过滤低置信度假设")
    print("=" * 60)
    
    # 创建测试线索
    clues = Clues(
        ocr=[
            OCRText(text="Eiffel Tower", bbox=[100, 200, 300, 250], confidence=0.95),
        ],
        visual=[
            VisualFeature(type="landmark", value="tower", confidence=0.90),
        ],
        meta=Metadata(),
    )
    
    state = AgentState(image_path="test.jpg", clues=clues)
    
    print(f"\n执行带验证的 Hypothesis 节点...")
    print(f"  设置最小置信度阈值: 0.5")
    
    # 使用验证
    result = await hypothesis_node_with_validation(
        state,
        min_confidence=0.5,  # 过滤低于 0.5 的假设
    )
    
    hypotheses = result["hypotheses"]
    
    print(f"\n✅ 生成并过滤后的假设: {len(hypotheses)} 个")
    
    for i, h in enumerate(hypotheses, 1):
        print(f"\n假设 {i}:")
        print(f"  区域: {h.region}")
        print(f"  置信度: {h.confidence:.2f} ✓ (≥ 0.5)")


async def example_4_iterative():
    """示例 4: 迭代优化假设"""
    print("\n" + "=" * 60)
    print("示例 4: 迭代式假设生成")
    print("=" * 60)
    
    # 创建测试线索
    clues = Clues(
        ocr=[
            OCRText(text="Colosseum", bbox=[100, 200, 300, 250], confidence=0.96),
        ],
        visual=[
            VisualFeature(type="landmark", value="ancient amphitheater", confidence=0.92),
        ],
        meta=Metadata(),
    )
    
    state = AgentState(image_path="test.jpg", clues=clues)
    
    print(f"\n执行迭代式 Hypothesis 节点...")
    print(f"  迭代次数: 2")
    print(f"  每次迭代基于上次结果进行优化")
    
    # 使用迭代模式
    result = await hypothesis_node_iterative(
        state,
        max_iterations=2,
    )
    
    hypotheses = result["hypotheses"]
    
    print(f"\n✅ 迭代优化完成")
    print(f"\n最终假设: {len(hypotheses)} 个")
    
    for i, h in enumerate(hypotheses, 1):
        print(f"\n假设 {i}:")
        print(f"  区域: {h.region}")
        print(f"  置信度: {h.confidence:.2f}")


async def example_5_in_phrv_workflow():
    """示例 5: 在完整 PHRV 工作流中使用"""
    print("\n" + "=" * 60)
    print("示例 5: 在完整 PHRV 工作流中使用")
    print("=" * 60)
    
    # 1. 初始化状态（假设已经过 Perception 阶段）
    clues = Clues(
        ocr=[
            OCRText(text="Sydney Opera House", bbox=[100, 200, 400, 250], confidence=0.97),
        ],
        visual=[
            VisualFeature(type="landmark", value="distinctive shell roof", confidence=0.94),
            VisualFeature(type="location", value="waterfront", confidence=0.89),
        ],
        meta=Metadata(
            scene_type="outdoor",
            time_of_day="day",
        ),
    )
    
    state = AgentState(
        image_path="test_sydney.jpg",
        clues=clues,
    )
    
    print(f"\n📍 PHRV 流程:")
    print(f"  [1/4] P (Perception)  ✓ 已完成")
    print(f"  [2/4] H (Hypothesis)  ← 当前阶段")
    print(f"  [3/4] R (Retrieval)")
    print(f"  [4/4] V (Verification)")
    
    # 2. 执行 Hypothesis 阶段
    print(f"\n🔍 执行 Hypothesis 阶段...")
    hypothesis_result = await hypothesis_node(state)
    
    # 3. 更新状态
    state.hypotheses = hypothesis_result["hypotheses"]
    
    print(f"\n✅ Hypothesis 阶段完成")
    print(f"\n状态更新:")
    print(f"  线索: {len(state.clues.ocr)} OCR + {len(state.clues.visual)} 视觉特征")
    print(f"  假设: {len(state.hypotheses)} 个")
    
    for i, h in enumerate(state.hypotheses[:3], 1):
        print(f"    {i}. {h.region} (置信度: {h.confidence:.2f})")
    
    print(f"\n📝 下一步:")
    print(f"  → 进入 Retrieval 阶段")
    print(f"  → 使用 GeoCLIP 为每个假设召回候选地点")


async def example_6_with_custom_llm():
    """示例 6: 使用自定义 LLM 提供商"""
    print("\n" + "=" * 60)
    print("示例 6: 使用自定义 LLM 提供商")
    print("=" * 60)
    
    clues = Clues(
        ocr=[OCRText(text="Test", bbox=[0, 0, 100, 100], confidence=0.9)],
        visual=[],
        meta=Metadata(),
    )
    
    state = AgentState(image_path="test.jpg", clues=clues)
    
    # 支持的 LLM 提供商
    llm_providers = ["openai", "anthropic", "deepseek"]
    
    print(f"\n支持的 LLM 提供商:")
    for provider in llm_providers:
        print(f"  - {provider}")
    
    # 使用 DeepSeek（示例）
    try:
        print(f"\n使用 LLM 提供商: deepseek")
        result = await hypothesis_node(state, llm_provider="deepseek")
        
        print(f"\n✅ 使用自定义 LLM 完成")
        print(f"  生成假设: {len(result['hypotheses'])} 个")
        
    except Exception as e:
        print(f"\n⚠️ 自定义 LLM 失败（可能需要 API Key）: {e}")


async def main():
    """运行所有示例"""
    print("\n🚀 GeoMind Hypothesis 节点使用示例\n")
    
    try:
        # 示例 1
        await example_1_basic_usage()
        
        # 示例 2
        await example_2_clues_summary()
        
        # 示例 3
        await example_3_with_validation()
        
        # 示例 4
        await example_4_iterative()
        
        # 示例 5
        await example_5_in_phrv_workflow()
        
        # 示例 6
        await example_6_with_custom_llm()
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("✅ 所有示例运行完成！")
    print("=" * 60)
    
    print("\n📚 相关文档:")
    print("  - geomind/agent/nodes/hypothesis.py")
    print("  - tests/unit/test_hypothesis_node.py")
    print("  - geomind/prompts/hypothesis.py")


if __name__ == "__main__":
    asyncio.run(main())

