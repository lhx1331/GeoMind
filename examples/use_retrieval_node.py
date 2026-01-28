"""
Retrieval 节点使用示例

演示如何使用 Retrieval 节点召回候选地点。
"""

import asyncio
import sys
from pathlib import Path

from PIL import Image

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from geomind.agent.nodes.retrieval import (
    create_hypothesis_query,
    retrieval_node,
    retrieval_node_ensemble,
    retrieval_node_multi_scale,
    retrieval_node_with_fallback,
)
from geomind.agent.state import AgentState, Hypothesis


async def example_1_basic_usage():
    """示例 1: 基础使用"""
    print("=" * 60)
    print("示例 1: Retrieval 节点基础使用")
    print("=" * 60)
    
    # 创建测试图像
    image = Image.new('RGB', (224, 224), color='blue')
    image_path = Path("test_retrieval_image.jpg")
    image.save(image_path)
    
    try:
        # 创建假设（模拟 Hypothesis 阶段的输出）
        hypotheses = [
            Hypothesis(
                region="Tokyo, Japan",
                rationale="Shibuya Crossing visible",
                supporting=["busy intersection", "Japanese text", "urban"],
                conflicting=[],
                confidence=0.90,
            ),
            Hypothesis(
                region="Osaka, Japan",
                rationale="Similar urban characteristics",
                supporting=["Japanese text", "modern city"],
                conflicting=["no specific landmarks"],
                confidence=0.70,
            ),
        ]
        
        # 创建 Agent 状态
        state = AgentState(
            image_path=str(image_path),
            hypotheses=hypotheses,
        )
        
        print(f"\n输入假设:")
        for i, h in enumerate(hypotheses, 1):
            print(f"  {i}. {h.region} (置信度: {h.confidence:.2f})")
            print(f"     推理: {h.rationale}")
        
        # 执行 Retrieval 节点
        print(f"\n执行 Retrieval 节点...")
        result = await retrieval_node(state, top_k=5)
        
        # 查看结果
        candidates = result["candidates"]
        
        print(f"\n✅ Retrieval 完成！")
        print(f"\n召回的候选地点: {len(candidates)} 个")
        
        for i, c in enumerate(candidates, 1):
            print(f"\n候选 {i}:")
            print(f"  名称: {c.name}")
            print(f"  坐标: ({c.lat:.4f}, {c.lon:.4f})")
            print(f"  分数: {c.score:.4f}")
            print(f"  来源假设: {c.hypothesis_source}")
            print(f"  召回方法: {c.retrieval_method}")
            
    finally:
        # 清理
        if image_path.exists():
            image_path.unlink()


async def example_2_hypothesis_query():
    """示例 2: 假设查询创建"""
    print("\n" + "=" * 60)
    print("示例 2: 创建假设查询")
    print("=" * 60)
    
    # 创建假设
    hypothesis = Hypothesis(
        region="Paris, France",
        rationale="Eiffel Tower visible",
        supporting=["tower structure", "French architecture", "Seine River"],
        conflicting=[],
        confidence=0.95,
    )
    
    # 创建查询
    query = create_hypothesis_query(hypothesis)
    
    print(f"\n假设:")
    print(f"  区域: {hypothesis.region}")
    print(f"  推理: {hypothesis.rationale}")
    print(f"  支持证据: {', '.join(hypothesis.supporting)}")
    
    print(f"\n生成的 GeoCLIP 查询:")
    print(f"  \"{query}\"")
    
    print(f"\n📝 这个查询将被发送给 GeoCLIP 进行地理编码")


async def example_3_with_fallback():
    """示例 3: 使用回退机制"""
    print("\n" + "=" * 60)
    print("示例 3: 使用回退机制")
    print("=" * 60)
    
    # 创建测试图像
    image = Image.new('RGB', (224, 224), color='green')
    image_path = Path("test_fallback_image.jpg")
    image.save(image_path)
    
    try:
        hypotheses = [
            Hypothesis(
                region="London, UK",
                rationale="Big Ben visible",
                supporting=["clock tower", "Gothic architecture"],
                conflicting=[],
                confidence=0.88,
            ),
        ]
        
        state = AgentState(image_path=str(image_path), hypotheses=hypotheses)
        
        print(f"\n执行带回退的 Retrieval 节点...")
        print(f"  如果图像编码失败，将回退到仅使用文本")
        
        # 使用带回退的节点
        result = await retrieval_node_with_fallback(state, top_k=3)
        
        candidates = result["candidates"]
        
        print(f"\n✅ Retrieval 完成（可能使用了回退）")
        print(f"\n候选地点: {len(candidates)} 个")
        
        for i, c in enumerate(candidates, 1):
            print(f"  {i}. {c.name} - ({c.lat:.2f}, {c.lon:.2f})")
            
    finally:
        if image_path.exists():
            image_path.unlink()


async def example_4_multi_scale():
    """示例 4: 多尺度召回"""
    print("\n" + "=" * 60)
    print("示例 4: 多尺度召回")
    print("=" * 60)
    
    # 创建测试图像
    image = Image.new('RGB', (224, 224), color='red')
    image_path = Path("test_multi_scale_image.jpg")
    image.save(image_path)
    
    try:
        hypotheses = [
            Hypothesis(
                region="California, USA",
                rationale="Golden Gate Bridge",
                supporting=["bridge", "bay", "red structure"],
                conflicting=[],
                confidence=0.85,
            ),
        ]
        
        state = AgentState(image_path=str(image_path), hypotheses=hypotheses)
        
        print(f"\n执行多尺度 Retrieval...")
        print(f"  尺度: city, region, country")
        
        # 使用多尺度召回
        result = await retrieval_node_multi_scale(
            state,
            scales=["city", "region", "country"],
            top_k_per_scale=2,
        )
        
        candidates = result["candidates"]
        
        print(f"\n✅ 多尺度 Retrieval 完成")
        print(f"\n候选地点: {len(candidates)} 个（已去重）")
        
        for i, c in enumerate(candidates, 1):
            scale = c.metadata.get("scale", "unknown") if c.metadata else "unknown"
            print(f"  {i}. {c.name} [{scale}] - 分数: {c.score:.2f}")
            
    finally:
        if image_path.exists():
            image_path.unlink()


async def example_5_ensemble():
    """示例 5: 集成召回"""
    print("\n" + "=" * 60)
    print("示例 5: 集成召回")
    print("=" * 60)
    
    # 创建测试图像
    image = Image.new('RGB', (224, 224), color='yellow')
    image_path = Path("test_ensemble_image.jpg")
    image.save(image_path)
    
    try:
        hypotheses = [
            Hypothesis(
                region="Rome, Italy",
                rationale="Colosseum visible",
                supporting=["ancient amphitheater", "Roman architecture"],
                conflicting=[],
                confidence=0.92,
            ),
        ]
        
        state = AgentState(image_path=str(image_path), hypotheses=hypotheses)
        
        print(f"\n执行集成 Retrieval...")
        print(f"  策略: 图像+文本 + 仅图像")
        print(f"  结果合并: 累加分数并去重")
        
        # 使用集成召回
        result = await retrieval_node_ensemble(state, top_k=5)
        
        candidates = result["candidates"]
        
        print(f"\n✅ 集成 Retrieval 完成")
        print(f"\n最终候选: {len(candidates)} 个")
        
        for i, c in enumerate(candidates, 1):
            print(f"  {i}. {c.name} - 集成分数: {c.score:.2f}")
            
    finally:
        if image_path.exists():
            image_path.unlink()


async def example_6_in_phrv_workflow():
    """示例 6: 在完整 PHRV 工作流中使用"""
    print("\n" + "=" * 60)
    print("示例 6: 在完整 PHRV 工作流中使用")
    print("=" * 60)
    
    # 创建测试图像
    image = Image.new('RGB', (224, 224), color='purple')
    image_path = Path("test_workflow_image.jpg")
    image.save(image_path)
    
    try:
        # 假设已经过 Perception 和 Hypothesis 阶段
        hypotheses = [
            Hypothesis(
                region="Sydney, Australia",
                rationale="Opera House visible",
                supporting=["distinctive shell roof", "waterfront", "modern"],
                conflicting=[],
                confidence=0.94,
            ),
            Hypothesis(
                region="Melbourne, Australia",
                rationale="Similar architectural style",
                supporting=["modern", "coastal"],
                conflicting=["no opera house"],
                confidence=0.65,
            ),
        ]
        
        state = AgentState(
            image_path=str(image_path),
            hypotheses=hypotheses,
        )
        
        print(f"\n📍 PHRV 流程:")
        print(f"  [1/4] P (Perception)  ✓ 已完成")
        print(f"  [2/4] H (Hypothesis)  ✓ 已完成")
        print(f"  [3/4] R (Retrieval)   ← 当前阶段")
        print(f"  [4/4] V (Verification)")
        
        # 执行 Retrieval 阶段
        print(f"\n🔍 执行 Retrieval 阶段...")
        retrieval_result = await retrieval_node(state, top_k=5)
        
        # 更新状态
        state.candidates = retrieval_result["candidates"]
        
        print(f"\n✅ Retrieval 阶段完成")
        print(f"\n状态更新:")
        print(f"  假设: {len(state.hypotheses)} 个")
        print(f"  候选: {len(state.candidates)} 个")
        
        print(f"\n候选地点列表:")
        for i, c in enumerate(state.candidates, 1):
            print(f"  {i}. {c.name}")
            print(f"     坐标: ({c.lat:.4f}, {c.lon:.4f})")
            print(f"     分数: {c.score:.4f}")
        
        print(f"\n📝 下一步:")
        print(f"  → 进入 Verification 阶段")
        print(f"  → 使用验证工具验证每个候选地点")
        
    finally:
        if image_path.exists():
            image_path.unlink()


async def main():
    """运行所有示例"""
    print("\n🚀 GeoMind Retrieval 节点使用示例\n")
    
    try:
        # 示例 1
        await example_1_basic_usage()
        
        # 示例 2
        await example_2_hypothesis_query()
        
        # 示例 3
        await example_3_with_fallback()
        
        # 示例 4
        await example_4_multi_scale()
        
        # 示例 5
        await example_5_ensemble()
        
        # 示例 6
        await example_6_in_phrv_workflow()
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("✅ 所有示例运行完成！")
    print("=" * 60)
    
    print("\n📚 相关文档:")
    print("  - geomind/agent/nodes/retrieval.py")
    print("  - tests/unit/test_retrieval_node.py")
    print("  - geomind/models/geoclip.py")


if __name__ == "__main__":
    asyncio.run(main())

