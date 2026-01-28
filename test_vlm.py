"""
VLM 测试脚本

用于测试 VLM 模型是否能正常工作，包括：
1. 配置加载
2. VLM 初始化
3. 图像分析
4. 输出解析
"""

import asyncio
import json
import sys
from pathlib import Path

from geomind.config.settings import get_settings
from geomind.models.vlm import create_vlm
from geomind.utils.logging import get_logger

logger = get_logger(__name__)


async def test_vlm_basic():
    """测试 VLM 基础功能"""
    print("=" * 80)
    print("VLM 基础功能测试")
    print("=" * 80)
    
    # 1. 加载配置
    print("\n1. 加载配置...")
    try:
        settings = get_settings()
        vlm_config = settings.vlm
        print(f"   ✅ 配置加载成功")
        print(f"   - Provider: {vlm_config.provider.value}")
        print(f"   - Model: {vlm_config.model_name}")
        print(f"   - Base URL: {vlm_config.base_url}")
        print(f"   - API Key: {'已配置' if vlm_config.api_key else '未配置'}")
    except Exception as e:
        print(f"   ❌ 配置加载失败: {e}")
        return False
    
    # 2. 创建 VLM
    print("\n2. 创建 VLM...")
    try:
        vlm = await create_vlm(
            model_name=vlm_config.model_name,
            api_key=vlm_config.api_key,
            base_url=vlm_config.base_url,
        )
        print(f"   ✅ VLM 创建成功")
    except Exception as e:
        print(f"   ❌ VLM 创建失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 3. 测试图像路径
    print("\n3. 检查测试图像...")
    test_image = Path("D:/project/GeoMind/hollywood-sign-1598473_1920.jpg")
    if not test_image.exists():
        print(f"   ⚠️  测试图像不存在: {test_image}")
        print(f"   请提供图像路径作为命令行参数")
        if len(sys.argv) > 1:
            test_image = Path(sys.argv[1])
        else:
            return False
    print(f"   ✅ 图像存在: {test_image}")
    
    # 4. 调用 VLM 分析图像
    print("\n4. 调用 VLM 分析图像...")
    try:
        prompt = """请分析这张图像，提取地理相关的线索信息。

请返回 JSON 格式：
{
  "ocr_texts": [{"text": "文本", "bbox": [x1,y1,x2,y2], "confidence": 0.9, "language": "en"}],
  "visual_features": [{"type": "类型", "value": "描述", "confidence": 0.85}],
  "metadata": {"time_of_day": "afternoon", "scene_type": "urban"}
}"""
        
        print(f"   提示长度: {len(prompt)} 字符")
        print(f"   正在调用 VLM API...")
        
        response = await vlm.analyze_image(
            image=str(test_image),
            prompt=prompt,
            system_prompt=None,
        )
        
        await vlm.cleanup()
        
        if not response.success:
            print(f"   ❌ VLM 调用失败: {response.error}")
            return False
        
        print(f"   ✅ VLM 调用成功")
        print(f"   - 响应类型: {type(response.data).__name__}")
        print(f"   - 响应长度: {len(str(response.data))} 字符")
        
    except Exception as e:
        print(f"   ❌ VLM 调用异常: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 5. 显示原始输出
    print("\n5. VLM 原始输出:")
    print("-" * 80)
    raw_output = str(response.data)
    print(raw_output[:2000])  # 显示前 2000 字符
    if len(raw_output) > 2000:
        print(f"\n... (还有 {len(raw_output) - 2000} 字符)")
    print("-" * 80)
    
    # 6. 尝试解析 JSON
    print("\n6. 尝试解析 JSON...")
    try:
        import re
        
        if isinstance(response.data, str):
            # 尝试直接解析
            try:
                output_dict = json.loads(response.data)
                print("   ✅ 直接 JSON 解析成功")
            except json.JSONDecodeError:
                # 尝试提取 JSON 部分
                json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response.data, re.DOTALL)
                if json_match:
                    output_dict = json.loads(json_match.group(1))
                    print("   ✅ 从代码块中提取 JSON 成功")
                else:
                    json_match = re.search(r'\{.*\}', response.data, re.DOTALL)
                    if json_match:
                        output_dict = json.loads(json_match.group())
                        print("   ✅ 从文本中提取 JSON 成功")
                    else:
                        print("   ❌ 无法找到 JSON 格式")
                        return False
        else:
            output_dict = response.data
            print("   ✅ 输出已经是字典格式")
        
        # 显示解析结果
        print("\n   解析结果:")
        print(f"   - OCR 文本数量: {len(output_dict.get('ocr_texts', []))}")
        print(f"   - 视觉特征数量: {len(output_dict.get('visual_features', []))}")
        
        if output_dict.get('ocr_texts'):
            print("\n   OCR 文本:")
            for i, ocr in enumerate(output_dict['ocr_texts'][:5], 1):
                print(f"     {i}. {ocr.get('text', 'N/A')} (置信度: {ocr.get('confidence', 0):.2f})")
        
        if output_dict.get('visual_features'):
            print("\n   视觉特征:")
            for i, vf in enumerate(output_dict['visual_features'][:5], 1):
                print(f"     {i}. {vf.get('type', 'N/A')}: {vf.get('value', 'N/A')} (置信度: {vf.get('confidence', 0):.2f})")
        
        # 保存完整输出到文件
        output_file = Path("vlm_output.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_dict, f, ensure_ascii=False, indent=2)
        print(f"\n   ✅ 完整输出已保存到: {output_file}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ JSON 解析失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_vlm_with_perception_prompt():
    """使用 Perception 提示模板测试 VLM"""
    print("\n" + "=" * 80)
    print("使用 Perception 提示模板测试")
    print("=" * 80)
    
    try:
        from geomind.prompts.perception import render_perception_prompt
        
        # 生成提示
        prompt = render_perception_prompt(context=None)
        print(f"\n提示长度: {len(prompt)} 字符")
        print(f"提示预览:\n{prompt[:500]}...")
        
        # 测试图像
        test_image = Path("D:/project/GeoMind/hollywood-sign-1598473_1920.jpg")
        if len(sys.argv) > 1:
            test_image = Path(sys.argv[1])
        
        if not test_image.exists():
            print(f"⚠️  图像不存在: {test_image}")
            return False
        
        # 创建 VLM
        settings = get_settings()
        vlm_config = settings.vlm
        vlm = await create_vlm(
            model_name=vlm_config.model_name,
            api_key=vlm_config.api_key,
            base_url=vlm_config.base_url,
        )
        
        # 调用 VLM
        print("\n调用 VLM...")
        response = await vlm.analyze_image(
            image=str(test_image),
            prompt=prompt,
            system_prompt=None,
        )
        
        await vlm.cleanup()
        
        if not response.success:
            print(f"❌ 调用失败: {response.error}")
            return False
        
        print(f"✅ 调用成功")
        print(f"\n原始输出:\n{str(response.data)[:1000]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主函数"""
    print("\n" + "=" * 80)
    print("VLM 测试脚本")
    print("=" * 80)
    print("\n用法: python test_vlm.py [图像路径]")
    print("示例: python test_vlm.py D:/project/GeoMind/hollywood-sign-1598473_1920.jpg\n")
    
    # 测试 1: 基础功能
    result1 = await test_vlm_basic()
    
    # 测试 2: 使用 Perception 提示模板
    if result1:
        result2 = await test_vlm_with_perception_prompt()
    else:
        result2 = False
    
    # 总结
    print("\n" + "=" * 80)
    print("测试总结")
    print("=" * 80)
    print(f"基础功能测试: {'✅ 通过' if result1 else '❌ 失败'}")
    print(f"Perception 提示测试: {'✅ 通过' if result2 else '❌ 失败'}")
    
    if result1 and result2:
        print("\n🎉 所有测试通过！VLM 工作正常。")
        return 0
    else:
        print("\n⚠️  部分测试失败，请检查配置和 API 连接。")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

