"""
Hypothesis 和 Verification 提示模板测试
"""

import pytest
from pydantic import ValidationError

from geomind.agent.state import Candidate, Clues, Evidence, Hypothesis, OCRText, VisualFeature, Metadata
from geomind.prompts.hypothesis import (
    HypothesisOutput,
    HypothesisRegion,
    convert_to_hypotheses,
    get_hypothesis_template,
    parse_hypothesis_output,
    render_hypothesis_prompt,
    validate_hypothesis_output,
)
from geomind.prompts.verification import (
    VerificationCheck,
    VerificationStrategy,
    create_evidence_from_result,
    get_verification_template,
    parse_verification_strategy,
    render_verification_prompt,
    validate_verification_strategy,
)


class TestHypothesisDataModels:
    """测试 Hypothesis 数据模型"""

    def test_hypothesis_region(self):
        """测试地理区域模型"""
        region = HypothesisRegion(
            country="Japan",
            state="Tokyo",
            city="Chiyoda"
        )
        assert region.country == "Japan"
        assert region.state == "Tokyo"
        assert region.city == "Chiyoda"

    def test_hypothesis_output(self):
        """测试假设输出模型"""
        output = HypothesisOutput(
            region=HypothesisRegion(country="Japan", city="Tokyo"),
            confidence=0.85,
            reasoning="建筑风格和文字特征符合日本东京",
            supporting_clues=["日文文字", "现代建筑"],
            conflicting_clues=["气候特征不明确"]
        )
        assert output.confidence == 0.85
        assert len(output.supporting_clues) == 2
        assert output.conflicting_clues is not None

    def test_hypothesis_output_invalid_confidence(self):
        """测试无效的置信度"""
        with pytest.raises(ValidationError):
            HypothesisOutput(
                region=HypothesisRegion(country="Japan"),
                confidence=1.5,  # 超出范围
                reasoning="Test"
            )


class TestHypothesisTemplate:
    """测试 Hypothesis 模板"""

    def test_get_hypothesis_template(self):
        """测试获取模板"""
        template = get_hypothesis_template()
        assert template is not None
        assert template.name == "hypothesis"

    def test_render_hypothesis_prompt(self):
        """测试渲染提示"""
        clues = Clues(
            ocr=[OCRText(text="Tokyo Station", bbox=[0, 0, 100, 100], confidence=0.9, lang="en")],
            visual=[VisualFeature(type="architecture", value="红砖建筑", confidence=0.85)],
            meta=Metadata(scene_type="urban")
        )
        
        prompt = render_hypothesis_prompt(clues)
        
        assert prompt is not None
        assert len(prompt) > 0
        # 验证提示包含基本内容（不检查 Jinja2 渲染后的具体值）
        assert "地理" in prompt or "geographic" in prompt.lower() or "假设" in prompt

    def test_render_hypothesis_prompt_empty_clues(self):
        """测试渲染提示（空线索）"""
        clues = Clues(ocr=[], visual=[], meta=Metadata())
        
        prompt = render_hypothesis_prompt(clues)
        
        assert prompt is not None
        assert len(prompt) > 0


class TestHypothesisOutputParsing:
    """测试 Hypothesis 输出解析"""

    def test_parse_hypothesis_output_valid(self):
        """测试解析有效的输出"""
        output_list = [
            {
                "region": {"country": "Japan", "city": "Tokyo"},
                "confidence": 0.85,
                "reasoning": "日文特征明显",
                "supporting_clues": ["日文文字", "建筑风格"],
                "conflicting_clues": []
            },
            {
                "region": {"country": "China", "city": "Beijing"},
                "confidence": 0.65,
                "reasoning": "也可能是中国",
                "supporting_clues": ["汉字"],
                "conflicting_clues": ["建筑风格不符"]
            }
        ]
        
        results = parse_hypothesis_output(output_list)
        
        assert len(results) == 2
        assert results[0].confidence == 0.85
        assert results[1].region.country == "China"

    def test_parse_hypothesis_output_invalid(self):
        """测试解析无效输出"""
        output_list = [
            {
                "region": {"country": "Japan"},
                "confidence": 1.5,  # 无效
                "reasoning": "Test"
            }
        ]
        
        with pytest.raises(ValidationError):
            parse_hypothesis_output(output_list)

    def test_validate_hypothesis_output_valid(self):
        """测试验证有效输出"""
        output_list = [
            {
                "region": {"country": "Japan"},
                "confidence": 0.8,
                "reasoning": "Test",
                "supporting_clues": []
            }
        ]
        
        assert validate_hypothesis_output(output_list) is True

    def test_validate_hypothesis_output_invalid(self):
        """测试验证无效输出"""
        output_list = [
            {
                "region": {},
                "confidence": 2.0  # 无效
            }
        ]
        
        assert validate_hypothesis_output(output_list) is False


class TestConvertToHypotheses:
    """测试转换为 Hypothesis 对象"""

    def test_convert_to_hypotheses_basic(self):
        """测试基本转换"""
        hypothesis_outputs = [
            HypothesisOutput(
                region=HypothesisRegion(country="Japan", state="Tokyo", city="Chiyoda"),
                confidence=0.85,
                reasoning="明显的日本特征",
                supporting_clues=["日文", "建筑"],
                conflicting_clues=[]
            )
        ]
        
        hypotheses = convert_to_hypotheses(hypothesis_outputs)
        
        assert len(hypotheses) == 1
        assert isinstance(hypotheses[0], Hypothesis)
        assert hypotheses[0].confidence == 0.85
        assert "Chiyoda" in hypotheses[0].region
        assert "Tokyo" in hypotheses[0].region
        assert "Japan" in hypotheses[0].region

    def test_convert_to_hypotheses_empty(self):
        """测试空输出的转换"""
        hypotheses = convert_to_hypotheses([])
        
        assert len(hypotheses) == 0


class TestVerificationDataModels:
    """测试 Verification 数据模型"""

    def test_verification_check(self):
        """测试验证检查模型"""
        check = VerificationCheck(
            check_type="ocr_poi_match",
            tool_name="match_ocr_to_poi",
            tool_params={"threshold": 0.8},
            expected_outcome="找到匹配的POI",
            scoring_criteria="匹配度>0.8为满分"
        )
        assert check.check_type == "ocr_poi_match"
        assert check.tool_params["threshold"] == 0.8

    def test_verification_strategy(self):
        """测试验证策略模型"""
        strategy = VerificationStrategy(
            verification_checks=[
                VerificationCheck(
                    check_type="ocr_poi_match",
                    tool_name="match_ocr_to_poi",
                    tool_params={},
                    expected_outcome="Match found",
                    scoring_criteria="Score > 0.7"
                )
            ],
            priority="high",
            confidence_threshold=0.8
        )
        assert len(strategy.verification_checks) == 1
        assert strategy.priority == "high"
        assert strategy.confidence_threshold == 0.8


class TestVerificationTemplate:
    """测试 Verification 模板"""

    def test_get_verification_template(self):
        """测试获取模板"""
        template = get_verification_template()
        assert template is not None
        assert template.name == "verification"

    def test_render_verification_prompt(self):
        """测试渲染提示"""
        candidate = Candidate(
            name="Tokyo Station",
            lat=35.6812,
            lon=139.7671,
            source="geoclip",
            score=0.85,
            address="Tokyo, Japan"
        )
        
        clues = Clues(
            ocr=[OCRText(text="Tokyo", bbox=[0, 0, 100, 100], confidence=0.9)],
            visual=[VisualFeature(type="landmark", value="著名地标", confidence=0.85)],
            meta=Metadata()
        )
        
        prompt = render_verification_prompt(candidate, clues)
        
        assert prompt is not None
        assert len(prompt) > 0
        # 验证提示包含验证相关内容（不检查 Jinja2 渲染后的具体值）
        assert "验证" in prompt or "verification" in prompt.lower()

    def test_render_verification_prompt_with_tools(self):
        """测试渲染提示（指定工具）"""
        candidate = Candidate(
            name="Test Location",
            lat=0.0,
            lon=0.0,
            source="test",
            score=0.5
        )
        
        clues = Clues(ocr=[], visual=[], meta=Metadata())
        
        available_tools = ["tool1", "tool2", "tool3"]
        
        prompt = render_verification_prompt(candidate, clues, available_tools)
        
        assert prompt is not None
        assert len(prompt) > 0
        # 验证提示包含工具相关内容
        assert "工具" in prompt or "tool" in prompt.lower()


class TestVerificationStrategyParsing:
    """测试 Verification 策略解析"""

    def test_parse_verification_strategy_valid(self):
        """测试解析有效的策略"""
        output_dict = {
            "verification_checks": [
                {
                    "check_type": "ocr_poi_match",
                    "tool_name": "match_ocr_to_poi",
                    "tool_params": {"threshold": 0.8},
                    "expected_outcome": "找到匹配",
                    "scoring_criteria": "匹配度>0.8"
                }
            ],
            "priority": "high",
            "confidence_threshold": 0.75
        }
        
        strategy = parse_verification_strategy(output_dict)
        
        assert isinstance(strategy, VerificationStrategy)
        assert len(strategy.verification_checks) == 1
        assert strategy.priority == "high"
        assert strategy.confidence_threshold == 0.75

    def test_parse_verification_strategy_invalid(self):
        """测试解析无效策略"""
        output_dict = {
            "verification_checks": "not a list",  # 应该是列表
            "priority": "high"
        }
        
        with pytest.raises(ValidationError):
            parse_verification_strategy(output_dict)

    def test_validate_verification_strategy_valid(self):
        """测试验证有效策略"""
        output_dict = {
            "verification_checks": [],
            "priority": "medium",
            "confidence_threshold": 0.7
        }
        
        assert validate_verification_strategy(output_dict) is True

    def test_validate_verification_strategy_invalid(self):
        """测试验证无效策略"""
        output_dict = {
            "verification_checks": [],
            "confidence_threshold": 1.5  # 超出范围
        }
        
        assert validate_verification_strategy(output_dict) is False


class TestEvidenceCreation:
    """测试证据创建"""

    def test_create_evidence_from_result(self):
        """测试从结果创建证据"""
        result = {
            "outcome": "match_found",
            "match_score": 0.85,
            "details": "POI matched successfully"
        }
        
        evidence = create_evidence_from_result(
            candidate_id="cand_001",
            check_type="ocr_poi_match",
            result=result,
            score=0.85
        )
        
        assert isinstance(evidence, Evidence)
        assert evidence.candidate_id == "cand_001"
        assert evidence.check == "ocr_poi_match"  # 修正字段名
        assert evidence.score == 0.85
        assert evidence.result == "match_found"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

