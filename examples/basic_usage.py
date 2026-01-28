"""
GeoMind 基础使用示例

演示如何使用 GeoMind Agent 进行图像地理定位。
"""

from pathlib import Path
from geomind import GeoMindAgent
from geomind.config import Settings


def main():
    """基础使用示例"""
    
    # 方式 1: 使用默认配置（从环境变量读取）
    agent = GeoMindAgent()
    
    # 方式 2: 自定义配置
    # settings = Settings(
    #     llm_provider="openai",
    #     vlm_provider="openai",
    #     max_iterations=5,
    #     confidence_threshold=0.7
    # )
    # agent = GeoMindAgent(settings=settings)
    
    # 执行地理定位
    image_path = Path("path/to/your/image.jpg")
    
    print(f"正在分析图片: {image_path}")
    result = agent.geolocate(
        image_path=image_path,
        max_iterations=5
    )
    
    # 输出结果
    print("\n" + "="*50)
    print("定位结果")
    print("="*50)
    print(f"地点: {result.final.answer}")
    print(f"置信度: {result.final.confidence:.2%}")
    print(f"\n支持证据:")
    print(f"  {result.final.why}")
    
    if result.final.why_not:
        print(f"\n排除原因:")
        for reason in result.final.why_not:
            print(f"  - {reason}")
    
    print(f"\n验证证据链:")
    for i, evidence in enumerate(result.evidence, 1):
        status = "✓" if evidence.result == "pass" else "✗"
        print(f"  {i}. {status} {evidence.check}: {evidence.details}")
    
    # 查看中间状态（调试用）
    print(f"\n感知线索:")
    if result.clues.ocr:
        print(f"  OCR 文本: {[c.text for c in result.clues.ocr]}")
    if result.clues.visual:
        print(f"  视觉特征: {[v.value for v in result.clues.visual]}")
    
    print(f"\n地理假设:")
    for i, hyp in enumerate(result.hypotheses, 1):
        print(f"  {i}. {hyp.region} (置信度: {hyp.confidence:.2%})")
    
    print(f"\n候选地点:")
    for i, cand in enumerate(result.candidates, 1):
        print(f"  {i}. {cand.name} ({cand.lat}, {cand.lon}) - {cand.source}")


if __name__ == "__main__":
    main()

