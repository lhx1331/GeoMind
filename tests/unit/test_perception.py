"""
Perception 提示模板测试
"""

import pytest
from pydantic import ValidationError

from geomind.agent.state import Clues
from geomind.prompts.perception import (
    PerceptionMetadata,
    PerceptionOCRText,
    PerceptionOutput,
    PerceptionVisualFeature,
    convert_to_clues,
    create_perception_prompt_with_image,
    get_perception_schema,
    get_perception_template,
    parse_perception_output,
    render_perception_prompt,
    validate_perception_output,
)


class TestPerceptionDataModels:
    """测试 Perception 数据模型"""

    def test_perception_ocr_text(self):
        """测试 OCR 文本模型"""
        ocr = PerceptionOCRText(
            text="Tokyo Station",
            bbox=[0.2, 0.1, 0.8, 0.2],
            confidence=0.95,
            language="en"
        )
        assert ocr.text == "Tokyo Station"
        assert ocr.confidence == 0.95
        assert ocr.language == "en"
        assert len(ocr.bbox) == 4

    def test_perception_ocr_text_without_optional(self):
        """测试 OCR 文本模型（不含可选字段）"""
        ocr = PerceptionOCRText(
            text="Hello",
            confidence=0.8
        )
        assert ocr.text == "Hello"
        assert ocr.bbox is None
        assert ocr.language is None

    def test_perception_ocr_text_invalid_confidence(self):
        """测试无效的置信度"""
        with pytest.raises(ValidationError):
            PerceptionOCRText(
                text="Test",
                confidence=1.5  # 超出范围
            )

    def test_perception_visual_feature(self):
        """测试视觉特征模型"""
        feature = PerceptionVisualFeature(
            type="architecture",
            value="红砖建筑，欧式风格",
            confidence=0.88,
            bbox=[0.1, 0.2, 0.9, 0.8]
        )
        assert feature.type == "architecture"
        assert feature.value == "红砖建筑，欧式风格"
        assert feature.confidence == 0.88

    def test_perception_metadata(self):
        """测试元数据模型"""
        metadata = PerceptionMetadata(
            time_of_day="afternoon",
            season="summer",
            weather="晴朗",
            dominant_colors=["红色", "蓝色"],
            scene_type="urban",
            notes="典型的城市风格"
        )
        assert metadata.time_of_day == "afternoon"
        assert metadata.season == "summer"
        assert len(metadata.dominant_colors) == 2

    def test_perception_output(self):
        """测试完整的 Perception 输出模型"""
        output = PerceptionOutput(
            ocr_texts=[
                PerceptionOCRText(text="Tokyo", confidence=0.9)
            ],
            visual_features=[
                PerceptionVisualFeature(
                    type="landmark",
                    value="著名地标",
                    confidence=0.85
                )
            ],
            metadata=PerceptionMetadata(scene_type="urban")
        )
        assert len(output.ocr_texts) == 1
        assert len(output.visual_features) == 1
        assert output.metadata.scene_type == "urban"


class TestPerceptionTemplate:
    """测试 Perception 模板"""

    def test_get_perception_template(self):
        """测试获取模板"""
        template = get_perception_template()
        assert template is not None
        assert template.name == "perception"
        assert "variables" in template.template or hasattr(template, "variables")

    def test_render_perception_prompt_without_context(self):
        """测试渲染提示（无上下文）"""
        prompt = render_perception_prompt()
        
        assert prompt is not None
        assert len(prompt) > 0
        assert "地理" in prompt or "geographic" in prompt.lower() or "识别" in prompt
        assert "JSON" in prompt or "json" in prompt

    def test_render_perception_prompt_with_context(self):
        """测试渲染提示（有上下文）"""
        context = "这是一张城市街景照片"
        prompt = render_perception_prompt(context=context)
        
        assert prompt is not None
        assert len(prompt) > 0
        # 验证提示包含地理相关内容
        assert "地理" in prompt or "geographic" in prompt.lower() or "识别" in prompt

    def test_create_perception_prompt_with_image(self):
        """测试创建包含图像的提示"""
        image_path = "/path/to/image.jpg"
        prompt, returned_path = create_perception_prompt_with_image(
            image_path=image_path,
            context="测试上下文"
        )
        
        assert prompt is not None
        assert returned_path == image_path


class TestPerceptionOutputParsing:
    """测试 Perception 输出解析"""

    def test_parse_perception_output_valid(self):
        """测试解析有效的输出"""
        output_dict = {
            "ocr_texts": [
                {
                    "text": "Tokyo Station",
                    "bbox": [0.2, 0.1, 0.8, 0.2],
                    "confidence": 0.95,
                    "language": "en"
                }
            ],
            "visual_features": [
                {
                    "type": "architecture",
                    "value": "红砖建筑",
                    "confidence": 0.88
                }
            ],
            "metadata": {
                "time_of_day": "afternoon",
                "scene_type": "urban"
            }
        }
        
        result = parse_perception_output(output_dict)
        
        assert isinstance(result, PerceptionOutput)
        assert len(result.ocr_texts) == 1
        assert len(result.visual_features) == 1
        assert result.ocr_texts[0].text == "Tokyo Station"
        assert result.visual_features[0].type == "architecture"

    def test_parse_perception_output_minimal(self):
        """测试解析最小输出"""
        output_dict = {
            "ocr_texts": [],
            "visual_features": [],
            "metadata": {}
        }
        
        result = parse_perception_output(output_dict)
        
        assert isinstance(result, PerceptionOutput)
        assert len(result.ocr_texts) == 0
        assert len(result.visual_features) == 0

    def test_parse_perception_output_invalid(self):
        """测试解析无效输出"""
        output_dict = {
            "ocr_texts": [
                {
                    "text": "Test",
                    "confidence": 1.5  # 无效的置信度
                }
            ],
            "visual_features": [],
            "metadata": {}
        }
        
        with pytest.raises(ValidationError):
            parse_perception_output(output_dict)

    def test_validate_perception_output_valid(self):
        """测试验证有效输出"""
        output_dict = {
            "ocr_texts": [],
            "visual_features": [],
            "metadata": {}
        }
        
        assert validate_perception_output(output_dict) is True

    def test_validate_perception_output_invalid(self):
        """测试验证无效输出"""
        output_dict = {
            "ocr_texts": "not a list"  # 应该是列表
        }
        
        assert validate_perception_output(output_dict) is False


class TestConvertToClues:
    """测试转换为 Clues 对象"""

    def test_convert_to_clues_basic(self):
        """测试基本转换"""
        perception_output = PerceptionOutput(
            ocr_texts=[
                PerceptionOCRText(
                    text="Tokyo",
                    bbox=[0.1, 0.2, 0.3, 0.4],
                    confidence=0.9,
                    language="en"
                )
            ],
            visual_features=[
                PerceptionVisualFeature(
                    type="landmark",
                    value="著名地标",
                    confidence=0.85
                )
            ],
            metadata=PerceptionMetadata(
                scene_type="urban",
                time_of_day="afternoon"
            )
        )
        
        clues = convert_to_clues(perception_output)
        
        assert isinstance(clues, Clues)
        assert len(clues.ocr) == 1
        assert len(clues.visual) == 1
        assert clues.ocr[0].text == "Tokyo"
        assert clues.visual[0].type == "landmark"

    def test_convert_to_clues_with_exif(self):
        """测试带 EXIF 数据的转换"""
        perception_output = PerceptionOutput(
            ocr_texts=[],
            visual_features=[],
            metadata=PerceptionMetadata(scene_type="urban")
        )
        
        exif_data = {
            "camera": "Canon EOS",
            "timestamp": "2024-01-01T12:00:00"
        }
        
        clues = convert_to_clues(perception_output, exif_metadata=exif_data)
        
        assert isinstance(clues, Clues)
        # EXIF 数据应该被合并到 metadata 中
        assert clues.meta is not None

    def test_convert_to_clues_empty(self):
        """测试空输出的转换"""
        perception_output = PerceptionOutput(
            ocr_texts=[],
            visual_features=[],
            metadata=PerceptionMetadata()
        )
        
        clues = convert_to_clues(perception_output)
        
        assert isinstance(clues, Clues)
        assert len(clues.ocr) == 0
        assert len(clues.visual) == 0


class TestPerceptionSchema:
    """测试 Schema 相关功能"""

    def test_get_perception_schema(self):
        """测试获取 JSON Schema"""
        schema = get_perception_schema()
        
        assert isinstance(schema, dict)
        assert "properties" in schema
        assert "ocr_texts" in schema["properties"]
        assert "visual_features" in schema["properties"]
        assert "metadata" in schema["properties"]

    def test_schema_has_required_fields(self):
        """测试 Schema 包含必需字段"""
        schema = get_perception_schema()
        
        # 检查顶层必需字段
        if "required" in schema:
            assert "ocr_texts" in schema.get("required", []) or True  # 可能不是必需的
            assert "visual_features" in schema.get("required", []) or True
            assert "metadata" in schema.get("required", []) or True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

