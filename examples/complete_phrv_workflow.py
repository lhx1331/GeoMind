"""
完整的 PHRV 工作流示例

演示如何将 Perception、Hypothesis、Retrieval 和 Verification 节点组合成完整的地理推理流程。
"""

import asyncio
import sys
from pathlib import Path

from PIL import Image

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from geomind.agent.nodes.hypothesis import hypothesis_node
from geomind.agent.nodes.perception import perception_node
from geomind.agent.nodes.retrieval import retrieval_node
from geomind.agent.nodes.verification import verification_node
from geomind.agent.state import AgentState


async def run_complete_phrv_workflow(image_path: str):
    """
    运行完整的 PHRV 工作流
    
    Args:
        image_path: 输入图像路径
    """
    print("\n" + "=" * 80)
    print("🌍 GeoMind - 通用地理推理 Agent (PHRV 框架)")
    print("=" * 80)
    
    # ============================================================================
    # 初始化
    # ============================================================================
    print(f"\n📷 输入图像: {image_path}")
    
    state = AgentState(image_path=image_path)
    
    print(f"\n🔄 开始 PHRV 流程...")
    print(f"   P (Perception)  → 提取地理线索")
    print(f"   H (Hypothesis)  → 生成地理假设")
    print(f"   R (Retrieval)   → 召回候选地点")
    print(f"   V (Verification)→ 验证并预测")
    
    # ============================================================================
    # Phase 1: Perception (感知)
    # ============================================================================
    print(f"\n" + "─" * 80)
    print(f"🔍 [1/4] Perception 阶段")
    print(f"─" * 80)
    
    try:
        perception_result = await perception_node(state)
        state.clues = perception_result["clues"]
        
        print(f"✅ Perception 完成")
        print(f"\n提取的线索:")
        print(f"  • OCR 文本: {len(state.clues.ocr)} 个")
        if state.clues.ocr:
            for i, ocr in enumerate(state.clues.ocr[:5], 1):
                print(f"    {i}. \"{ocr.text}\" (置信度: {ocr.confidence:.2f})")
        
        print(f"\n  • 视觉特征: {len(state.clues.visual)} 个")
        if state.clues.visual:
            for i, vf in enumerate(state.clues.visual[:5], 1):
                print(f"    {i}. {vf.type}: {vf.value} (置信度: {vf.confidence:.2f})")
        
        print(f"\n  • 元数据:")
        if state.clues.meta:
            print(f"    - GPS: {'有' if state.clues.meta.gps else '无'}")
            print(f"    - 时间戳: {state.clues.meta.timestamp or 'N/A'}")
            print(f"    - 场景类型: {state.clues.meta.scene_type or 'N/A'}")
        
    except Exception as e:
        print(f"❌ Perception 失败: {e}")
        return
    
    # ============================================================================
    # Phase 2: Hypothesis (假设)
    # ============================================================================
    print(f"\n" + "─" * 80)
    print(f"💡 [2/4] Hypothesis 阶段")
    print(f"─" * 80)
    
    try:
        hypothesis_result = await hypothesis_node(state)
        state.hypotheses = hypothesis_result["hypotheses"]
        
        print(f"✅ Hypothesis 完成")
        print(f"\n生成的假设: {len(state.hypotheses)} 个")
        
        for i, h in enumerate(state.hypotheses, 1):
            print(f"\n  假设 {i}: {h.region}")
            print(f"    置信度: {h.confidence:.2f}")
            print(f"    推理: {h.rationale}")
            if h.supporting:
                print(f"    支持证据: {', '.join(h.supporting[:3])}")
        
    except Exception as e:
        print(f"❌ Hypothesis 失败: {e}")
        return
    
    # ============================================================================
    # Phase 3: Retrieval (召回)
    # ============================================================================
    print(f"\n" + "─" * 80)
    print(f"📍 [3/4] Retrieval 阶段")
    print(f"─" * 80)
    
    try:
        retrieval_result = await retrieval_node(state, top_k=5)
        state.candidates = retrieval_result["candidates"]
        
        print(f"✅ Retrieval 完成")
        print(f"\n召回的候选: {len(state.candidates)} 个")
        
        for i, c in enumerate(state.candidates, 1):
            print(f"\n  候选 {i}: {c.name}")
            print(f"    坐标: ({c.lat:.4f}, {c.lon:.4f})")
            print(f"    分数: {c.score:.4f}")
            print(f"    来源: {c.hypothesis_source}")
        
    except Exception as e:
        print(f"❌ Retrieval 失败: {e}")
        return
    
    # ============================================================================
    # Phase 4: Verification (验证)
    # ============================================================================
    print(f"\n" + "─" * 80)
    print(f"✓ [4/4] Verification 阶段")
    print(f"─" * 80)
    
    try:
        verification_result = await verification_node(
            state,
            use_llm_verification=True,
            use_ocr_poi=True,
            use_language_prior=True,
        )
        
        state.prediction = verification_result["prediction"]
        verified_candidates = verification_result["verified_candidates"]
        evidence = verification_result["evidence"]
        
        print(f"✅ Verification 完成")
        
        # 显示验证证据
        print(f"\n验证证据:")
        for candidate_name, evidence_list in evidence.items():
            if evidence_list:
                print(f"  • {candidate_name}:")
                for e in evidence_list:
                    print(f"    - {e.type}: {e.value} (置信度: {e.confidence:.2f})")
        
    except Exception as e:
        print(f"❌ Verification 失败: {e}")
        return
    
    # ============================================================================
    # 最终结果
    # ============================================================================
    print(f"\n" + "=" * 80)
    print(f"🎯 最终预测结果")
    print(f"=" * 80)
    
    prediction = state.prediction
    
    print(f"\n📍 预测位置:")
    print(f"   纬度: {prediction.lat:.6f}")
    print(f"   经度: {prediction.lon:.6f}")
    
    print(f"\n📊 置信度: {prediction.confidence:.2%}")
    
    print(f"\n💭 推理过程:")
    print(f"   {prediction.reasoning}")
    
    if prediction.supporting_evidence:
        print(f"\n✓ 支持证据:")
        for evidence in prediction.supporting_evidence:
            print(f"   • {evidence}")
    
    if prediction.alternative_locations:
        print(f"\n🔄 备选位置: {len(prediction.alternative_locations)} 个")
        for i, alt in enumerate(prediction.alternative_locations[:3], 1):
            print(f"   {i}. {alt.get('name', 'Unknown')} - 分数: {alt.get('score', 0):.2f}")
    
    # ============================================================================
    # 流程总结
    # ============================================================================
    print(f"\n" + "=" * 80)
    print(f"📈 流程统计")
    print(f"=" * 80)
    
    print(f"\n阶段完成情况:")
    print(f"  ✓ Perception:   提取 {len(state.clues.ocr)} OCR + {len(state.clues.visual)} 视觉特征")
    print(f"  ✓ Hypothesis:   生成 {len(state.hypotheses)} 个地理假设")
    print(f"  ✓ Retrieval:    召回 {len(state.candidates)} 个候选地点")
    print(f"  ✓ Verification: 置信度 {prediction.confidence:.2%}")
    
    print(f"\n🎉 PHRV 工作流完成！")
    print(f"=" * 80 + "\n")
    
    return state


async def example_1_simple_image():
    """示例 1: 简单图像"""
    print("\n🖼️  示例 1: 处理简单图像")
    
    # 创建测试图像
    image = Image.new('RGB', (224, 224), color='blue')
    image_path = Path("test_simple.jpg")
    image.save(image_path)
    
    try:
        state = await run_complete_phrv_workflow(str(image_path))
        
        if state and state.prediction:
            print(f"\n✅ 成功预测位置: ({state.prediction.lat:.4f}, {state.prediction.lon:.4f})")
        
    finally:
        if image_path.exists():
            image_path.unlink()


async def example_2_with_error_handling():
    """示例 2: 带错误处理的工作流"""
    print("\n⚠️  示例 2: 带错误处理")
    
    image = Image.new('RGB', (224, 224), color='red')
    image_path = Path("test_error_handling.jpg")
    image.save(image_path)
    
    try:
        # 使用回退机制
        state = AgentState(image_path=str(image_path))
        
        print(f"\n运行带容错的 PHRV 流程...")
        
        # 每个阶段独立处理错误
        try:
            perception_result = await perception_node(state)
            state.clues = perception_result["clues"]
            print(f"✓ Perception 成功")
        except Exception as e:
            print(f"⚠️  Perception 失败，使用默认线索: {e}")
            # 继续下一阶段（如果合适的话）
        
        # ... 其他阶段类似
        
        print(f"\n✅ 容错流程完成")
        
    finally:
        if image_path.exists():
            image_path.unlink()


async def example_3_custom_parameters():
    """示例 3: 自定义参数"""
    print("\n⚙️  示例 3: 自定义参数")
    
    image = Image.new('RGB', (224, 224), color='green')
    image_path = Path("test_custom.jpg")
    image.save(image_path)
    
    try:
        state = AgentState(image_path=str(image_path))
        
        print(f"\n使用自定义参数运行 PHRV...")
        
        # 自定义每个阶段的参数
        perception_result = await perception_node(
            state,
            vlm_provider="glm",  # 使用 GLM
        )
        state.clues = perception_result["clues"]
        
        hypothesis_result = await hypothesis_node(
            state,
            llm_provider="deepseek",  # 使用 DeepSeek
            max_hypotheses=3,  # 最多 3 个假设
        )
        state.hypotheses = hypothesis_result["hypotheses"]
        
        retrieval_result = await retrieval_node(
            state,
            top_k=10,  # 召回 10 个候选
            use_image=True,
            use_text=True,
        )
        state.candidates = retrieval_result["candidates"]
        
        verification_result = await verification_node(
            state,
            use_llm_verification=False,  # 不使用 LLM 验证
            use_ocr_poi=True,
            use_language_prior=True,
            use_road_topology=False,  # 不使用道路拓扑
            top_k=1,
        )
        state.prediction = verification_result["prediction"]
        
        print(f"\n✅ 自定义流程完成")
        print(f"预测: ({state.prediction.lat:.4f}, {state.prediction.lon:.4f})")
        
    finally:
        if image_path.exists():
            image_path.unlink()


async def main():
    """主函数"""
    print("\n" + "=" * 80)
    print("🌍 GeoMind 完整 PHRV 工作流示例")
    print("=" * 80)
    
    try:
        # 运行示例
        await example_1_simple_image()
        
        # 可选：运行其他示例
        # await example_2_with_error_handling()
        # await example_3_custom_parameters()
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("✅ 所有示例完成！")
    print("=" * 80)
    
    print("\n📚 了解更多:")
    print("  - 单个节点示例: examples/use_*_node.py")
    print("  - 项目文档: docs/")
    print("  - 快速开始: 快速开始.md")


if __name__ == "__main__":
    asyncio.run(main())

