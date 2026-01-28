"""
Verification 节点使用示例

演示如何使用 Verification 节点验证候选地点并生成最终预测。
"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from geomind.agent.nodes.verification import (
    verification_node,
    verification_node_comprehensive,
    verification_node_simple,
    verify_candidate,
)
from geomind.agent.state import (
    AgentState,
    Candidate,
    Clues,
    Metadata,
    OCRText,
    VisualFeature,
)


async def example_1_basic_usage():
    """示例 1: 基础使用"""
    print("=" * 60)
    print("示例 1: Verification 节点基础使用")
    print("=" * 60)
    
    # 创建线索（模拟 Perception 阶段的输出）
    clues = Clues(
        ocr=[
            OCRText(text="Eiffel Tower", bbox=[100, 200, 300, 250], confidence=0.95),
            OCRText(text="Paris", bbox=[310, 200, 400, 250], confidence=0.90),
        ],
        visual=[
            VisualFeature(type="landmark", value="tower", confidence=0.92),
            VisualFeature(type="architecture", value="iron structure", confidence=0.88),
        ],
        meta=Metadata(scene_type="outdoor"),
    )
    
    # 创建候选（模拟 Retrieval 阶段的输出）
    candidates = [
        Candidate(
            lat=48.8584,
            lon=2.2945,
            name="Eiffel Tower, Paris",
            hypothesis_source="Paris, France",
            score=0.92,
            retrieval_method="geoclip",
        ),
        Candidate(
            lat=48.8606,
            lon=2.3376,
            name="Louvre Museum, Paris",
            hypothesis_source="Paris, France",
            score=0.75,
            retrieval_method="geoclip",
        ),
    ]
    
    # 创建 Agent 状态
    state = AgentState(
        image_path="test_image.jpg",
        clues=clues,
        candidates=candidates,
    )
    
    print(f"\n输入:")
    print(f"  线索: {len(clues.ocr)} OCR + {len(clues.visual)} 视觉特征")
    print(f"  候选: {len(candidates)} 个")
    for i, c in enumerate(candidates, 1):
        print(f"    {i}. {c.name} - 分数: {c.score:.2f}")
    
    # 执行 Verification 节点
    print(f"\n执行 Verification 节点...")
    result = await verification_node(
        state,
        use_llm_verification=False,  # 不使用 LLM
        use_ocr_poi=True,
        use_language_prior=True,
    )
    
    # 查看结果
    prediction = result["prediction"]
    verified_candidates = result["verified_candidates"]
    evidence = result["evidence"]
    
    print(f"\n✅ Verification 完成！")
    
    print(f"\n最终预测:")
    print(f"  位置: ({prediction.lat:.4f}, {prediction.lon:.4f})")
    print(f"  置信度: {prediction.confidence:.2f}")
    print(f"  推理: {prediction.reasoning}")
    
    if prediction.supporting_evidence:
        print(f"\n  支持证据:")
        for e in prediction.supporting_evidence:
            print(f"    - {e}")
    
    if prediction.alternative_locations:
        print(f"\n  备选位置: {len(prediction.alternative_locations)} 个")


async def example_2_verify_single_candidate():
    """示例 2: 验证单个候选"""
    print("\n" + "=" * 60)
    print("示例 2: 验证单个候选")
    print("=" * 60)
    
    # 创建候选
    candidate = Candidate(
        lat=35.6812,
        lon=139.7671,
        name="Tokyo Station",
        hypothesis_source="Tokyo, Japan",
        score=0.85,
        retrieval_method="geoclip",
    )
    
    # 创建线索
    clues = Clues(
        ocr=[
            OCRText(text="Tokyo Station", bbox=[100, 200, 300, 250], confidence=0.95),
            OCRText(text="東京駅", bbox=[100, 260, 300, 310], confidence=0.90),
        ],
        visual=[
            VisualFeature(type="landmark", value="train station", confidence=0.85),
        ],
        meta=Metadata(scene_type="urban"),
    )
    
    print(f"\n候选: {candidate.name}")
    print(f"  坐标: ({candidate.lat:.4f}, {candidate.lon:.4f})")
    print(f"  原始分数: {candidate.score:.2f}")
    
    print(f"\n执行验证...")
    
    # 验证候选
    verified_candidate, evidence_list = await verify_candidate(
        candidate=candidate,
        clues=clues,
        use_ocr_poi=True,
        use_language_prior=True,
        use_road_topology=False,
    )
    
    print(f"\n✅ 验证完成")
    print(f"\n更新后分数: {verified_candidate.score:.2f}")
    
    print(f"\n收集的证据: {len(evidence_list)} 个")
    for i, e in enumerate(evidence_list, 1):
        print(f"  {i}. [{e.type}] {e.value}")
        print(f"     置信度: {e.confidence:.2f}")


async def example_3_simple_vs_comprehensive():
    """示例 3: 简化版 vs 全面版"""
    print("\n" + "=" * 60)
    print("示例 3: 简化版 vs 全面版验证")
    print("=" * 60)
    
    # 准备状态
    clues = Clues(
        ocr=[OCRText(text="Big Ben", bbox=[100, 200, 300, 250], confidence=0.96)],
        visual=[VisualFeature(type="landmark", value="clock tower", confidence=0.90)],
        meta=Metadata(),
    )
    
    candidates = [
        Candidate(
            lat=51.5007,
            lon=-0.1246,
            name="Big Ben, London",
            hypothesis_source="London, UK",
            score=0.90,
            retrieval_method="geoclip",
        )
    ]
    
    state = AgentState(image_path="test.jpg", clues=clues, candidates=candidates)
    
    # 1. 简化版本
    print(f"\n1️⃣ 简化版验证:")
    print(f"   - 使用基本工具（OCR-POI, 语言先验）")
    print(f"   - 不使用 LLM")
    
    result_simple = await verification_node_simple(state)
    
    print(f"\n   结果: 置信度 {result_simple['prediction'].confidence:.2f}")
    
    # 2. 全面版本
    print(f"\n2️⃣ 全面版验证:")
    print(f"   - 使用所有验证工具")
    print(f"   - 包括 LLM 最终推理")
    
    result_comprehensive = await verification_node_comprehensive(state)
    
    print(f"\n   结果: 置信度 {result_comprehensive['prediction'].confidence:.2f}")
    
    print(f"\n📊 对比:")
    print(f"   简化版: 快速，适合实时应用")
    print(f"   全面版: 更准确，适合离线分析")


async def example_4_with_evidence():
    """示例 4: 分析验证证据"""
    print("\n" + "=" * 60)
    print("示例 4: 分析验证证据")
    print("=" * 60)
    
    clues = Clues(
        ocr=[
            OCRText(text="Sydney Opera House", bbox=[100, 200, 400, 250], confidence=0.97),
        ],
        visual=[
            VisualFeature(type="landmark", value="distinctive shell roof", confidence=0.94),
        ],
        meta=Metadata(),
    )
    
    candidates = [
        Candidate(
            lat=-33.8568,
            lon=151.2153,
            name="Sydney Opera House",
            hypothesis_source="Sydney, Australia",
            score=0.95,
            retrieval_method="geoclip",
        )
    ]
    
    state = AgentState(image_path="test.jpg", clues=clues, candidates=candidates)
    
    print(f"\n执行验证并收集证据...")
    
    result = await verification_node(state, use_llm_verification=False)
    
    prediction = result["prediction"]
    evidence_dict = result["evidence"]
    
    print(f"\n✅ 验证完成")
    
    print(f"\n最终预测: ({prediction.lat:.4f}, {prediction.lon:.4f})")
    print(f"置信度: {prediction.confidence:.2f}")
    
    print(f"\n详细证据分析:")
    for candidate_name, evidence_list in evidence_dict.items():
        print(f"\n  候选: {candidate_name}")
        if evidence_list:
            for e in evidence_list:
                print(f"    ✓ {e.type}: {e.value}")
                print(f"      置信度: {e.confidence:.2f}")
                if e.details:
                    print(f"      详情: {e.details}")
        else:
            print(f"    (无验证证据)")


async def example_5_in_phrv_workflow():
    """示例 5: 在完整 PHRV 工作流中使用"""
    print("\n" + "=" * 60)
    print("示例 5: 在完整 PHRV 工作流中使用")
    print("=" * 60)
    
    # 假设已经过 P, H, R 阶段
    clues = Clues(
        ocr=[
            OCRText(text="Colosseum", bbox=[100, 200, 300, 250], confidence=0.96),
        ],
        visual=[
            VisualFeature(type="landmark", value="ancient amphitheater", confidence=0.92),
        ],
        meta=Metadata(),
    )
    
    candidates = [
        Candidate(
            lat=41.8902,
            lon=12.4922,
            name="Colosseum, Rome",
            hypothesis_source="Rome, Italy",
            score=0.93,
            retrieval_method="geoclip",
        ),
        Candidate(
            lat=41.9028,
            lon=12.4534,
            name="Vatican City",
            hypothesis_source="Rome, Italy",
            score=0.70,
            retrieval_method="geoclip",
        ),
    ]
    
    state = AgentState(
        image_path="test_rome.jpg",
        clues=clues,
        candidates=candidates,
    )
    
    print(f"\n📍 PHRV 流程:")
    print(f"  [1/4] P (Perception)  ✓ 已完成")
    print(f"  [2/4] H (Hypothesis)  ✓ 已完成")
    print(f"  [3/4] R (Retrieval)   ✓ 已完成")
    print(f"  [4/4] V (Verification) ← 当前阶段")
    
    # 执行 Verification 阶段
    print(f"\n🔍 执行 Verification 阶段...")
    verification_result = await verification_node(state)
    
    # 更新状态
    state.prediction = verification_result["prediction"]
    
    print(f"\n✅ Verification 阶段完成")
    
    print(f"\n最终结果:")
    print(f"  📍 预测位置: ({state.prediction.lat:.4f}, {state.prediction.lon:.4f})")
    print(f"  📊 置信度: {state.prediction.confidence:.2f}")
    print(f"  💡 推理: {state.prediction.reasoning}")
    
    print(f"\n🎉 PHRV 流程全部完成！")
    print(f"\n流程总结:")
    print(f"  • Perception: 提取了 {len(clues.ocr)} OCR + {len(clues.visual)} 视觉特征")
    print(f"  • Hypothesis: (已生成假设)")
    print(f"  • Retrieval: 召回了 {len(candidates)} 个候选")
    print(f"  • Verification: 生成最终预测，置信度 {state.prediction.confidence:.2f}")


async def main():
    """运行所有示例"""
    print("\n🚀 GeoMind Verification 节点使用示例\n")
    
    try:
        # 示例 1
        await example_1_basic_usage()
        
        # 示例 2
        await example_2_verify_single_candidate()
        
        # 示例 3
        await example_3_simple_vs_comprehensive()
        
        # 示例 4
        await example_4_with_evidence()
        
        # 示例 5
        await example_5_in_phrv_workflow()
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("✅ 所有示例运行完成！")
    print("=" * 60)
    
    print("\n📚 相关文档:")
    print("  - geomind/agent/nodes/verification.py")
    print("  - tests/unit/test_verification_node.py")
    print("  - geomind/tools/mcp/verification.py")


if __name__ == "__main__":
    asyncio.run(main())

