"""
GeoCLIP 使用示例

演示如何在 GeoMind 项目中使用 GeoCLIP 进行地理位置检索。
"""

import asyncio
from pathlib import Path

# 从项目中导入 GeoCLIP ✅
from geomind.models.geoclip import create_geoclip_model
from geomind.agent.state import Candidate
from geomind.utils.image import load_image


async def example_1_basic_usage():
    """示例 1: 基础使用 - 预测图像位置"""
    print("=" * 60)
    print("示例 1: 基础使用")
    print("=" * 60)
    
    # 1. 创建 GeoCLIP 模型
    geoclip = create_geoclip_model()
    await geoclip.initialize()
    
    # 2. 创建测试图像
    from PIL import Image
    import numpy as np
    test_image = Image.fromarray(
        np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
    )
    
    # 3. 预测位置
    result = await geoclip.predict_location(test_image, top_k=5)
    
    if result.success:
        print(f"\n✅ 预测成功，找到 {len(result.data)} 个候选位置：\n")
        
        for i, loc in enumerate(result.data, 1):
            print(f"{i}. 坐标: ({loc['lat']:.4f}, {loc['lon']:.4f})")
            print(f"   得分: {loc['score']:.4f}\n")
    else:
        print(f"❌ 预测失败: {result.error}")
    
    # 4. 清理
    await geoclip.cleanup()


async def example_2_with_agent_state():
    """示例 2: 与 Agent State 集成 - 创建 Candidate"""
    print("=" * 60)
    print("示例 2: 与 Agent State 集成")
    print("=" * 60)
    
    # 1. 创建模型
    geoclip = create_geoclip_model()
    await geoclip.initialize()
    
    # 2. 模拟图像
    from PIL import Image
    import numpy as np
    image = Image.fromarray(
        np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
    )
    
    # 3. 获取位置预测
    result = await geoclip.predict_location(image, top_k=3)
    
    if result.success:
        # 4. 转换为 Candidate 对象 (Agent 使用的标准格式)
        candidates = []
        
        for loc in result.data:
            candidate = Candidate(
                name=f"Location_{loc['lat']:.2f}_{loc['lon']:.2f}",
                lat=loc['lat'],
                lon=loc['lon'],
                source="geoclip",
                score=loc['score']
            )
            candidates.append(candidate)
        
        print(f"\n✅ 创建了 {len(candidates)} 个候选地点：\n")
        
        for candidate in candidates:
            print(f"名称: {candidate.name}")
            print(f"坐标: ({candidate.lat:.4f}, {candidate.lon:.4f})")
            print(f"来源: {candidate.source}")
            print(f"得分: {candidate.score:.4f}\n")
    
    await geoclip.cleanup()


async def example_3_retrieval_stage():
    """示例 3: Retrieval 阶段 - 完整流程"""
    print("=" * 60)
    print("示例 3: Retrieval 阶段完整流程")
    print("=" * 60)
    
    async def retrieval_stage(image_path: str, top_k: int = 5):
        """
        Retrieval 阶段：使用 GeoCLIP 召回候选地点
        
        这是 GeoMind Agent 中 PHRV 流程的 R 阶段
        """
        # 初始化 GeoCLIP
        geoclip = create_geoclip_model()
        await geoclip.initialize()
        
        # 加载图像
        # image = load_image(image_path)
        # 这里用模拟图像
        from PIL import Image
        import numpy as np
        image = Image.fromarray(
            np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
        )
        
        # 使用 GeoCLIP 检索候选位置
        result = await geoclip.predict_location(image, top_k=top_k)
        
        if not result.success:
            print(f"❌ 检索失败: {result.error}")
            await geoclip.cleanup()
            return []
        
        # 转换为 Candidate 列表
        candidates = []
        for loc in result.data:
            candidate = Candidate(
                name=f"GeoCLIP_Candidate_{len(candidates)+1}",
                lat=loc['lat'],
                lon=loc['lon'],
                source="geoclip",
                score=loc['score'],
                metadata={
                    "index": loc.get('index'),
                    "retrieval_method": "geoclip_image_embedding"
                }
            )
            candidates.append(candidate)
        
        await geoclip.cleanup()
        
        return candidates
    
    # 执行 Retrieval
    candidates = await retrieval_stage("dummy_image.jpg", top_k=5)
    
    print(f"\n✅ Retrieval 阶段完成")
    print(f"   召回候选数: {len(candidates)}")
    print(f"   最高得分: {candidates[0].score:.4f}")
    print(f"   最低得分: {candidates[-1].score:.4f}\n")
    
    print("候选地点列表：")
    for i, candidate in enumerate(candidates, 1):
        print(f"  {i}. {candidate.name}")
        print(f"     坐标: ({candidate.lat:.4f}, {candidate.lon:.4f})")
        print(f"     得分: {candidate.score:.4f}")


async def main():
    """运行所有示例"""
    print("\n🚀 GeoMind GeoCLIP 集成示例\n")
    
    # 示例 1
    await example_1_basic_usage()
    
    print("\n" + "=" * 60 + "\n")
    
    # 示例 2
    await example_2_with_agent_state()
    
    print("\n" + "=" * 60 + "\n")
    
    # 示例 3
    await example_3_retrieval_stage()
    
    print("\n" + "=" * 60)
    print("✅ 所有示例运行完成！")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

