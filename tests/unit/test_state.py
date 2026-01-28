"""
状态数据模型单元测试
"""

import json

import pytest

from geomind.agent.state import (
    AgentState,
    Candidate,
    Clues,
    Evidence,
    FinalResult,
    Hypothesis,
    Metadata,
    OCRText,
    VisualFeature,
)


class TestOCRText:
    """测试 OCR 文本模型"""

    def test_create_ocr_text(self):
        """测试创建 OCR 文本"""
        ocr = OCRText(
            text="Tokyo Station",
            bbox=[100, 200, 300, 250],
            confidence=0.95,
            lang="en",
        )
        assert ocr.text == "Tokyo Station"
        assert ocr.confidence == 0.95
        assert ocr.lang == "en"

    def test_ocr_text_validation(self):
        """测试 OCR 文本验证"""
        # 置信度应该在 0-1 之间
        with pytest.raises(Exception):
            OCRText(text="test", bbox=[0, 0, 10, 10], confidence=1.5)


class TestVisualFeature:
    """测试视觉特征模型"""

    def test_create_visual_feature(self):
        """测试创建视觉特征"""
        feature = VisualFeature(
            type="architecture",
            value="modern glass building",
            confidence=0.85,
        )
        assert feature.type == "architecture"
        assert feature.value == "modern glass building"
        assert feature.confidence == 0.85


class TestClues:
    """测试感知线索模型"""

    def test_create_empty_clues(self):
        """测试创建空线索"""
        clues = Clues()
        assert len(clues.ocr) == 0
        assert len(clues.visual) == 0
        assert clues.meta is not None

    def test_create_clues_with_data(self):
        """测试创建包含数据的线索"""
        ocr = OCRText(text="Tokyo", bbox=[0, 0, 100, 50], confidence=0.9, lang="ja")
        feature = VisualFeature(type="landmark", value="station", confidence=0.8)

        clues = Clues(ocr=[ocr], visual=[feature])
        assert len(clues.ocr) == 1
        assert len(clues.visual) == 1
        assert clues.ocr[0].text == "Tokyo"

    def test_clues_json_serialization(self):
        """测试线索的 JSON 序列化"""
        ocr = OCRText(text="Tokyo", bbox=[0, 0, 100, 50], confidence=0.9)
        clues = Clues(ocr=[ocr])

        # 序列化
        json_str = clues.model_dump_json()
        assert "Tokyo" in json_str

        # 反序列化
        clues2 = Clues.model_validate_json(json_str)
        assert clues2.ocr[0].text == "Tokyo"


class TestHypothesis:
    """测试地理假设模型"""

    def test_create_hypothesis(self):
        """测试创建假设"""
        hyp = Hypothesis(
            region="Japan/Tokyo",
            rationale=["Japanese text detected"],
            supporting=["Tokyo OCR", "Japanese architecture"],
            confidence=0.8,
        )
        assert hyp.region == "Japan/Tokyo"
        assert len(hyp.rationale) == 1
        assert hyp.confidence == 0.8

    def test_hypothesis_with_conflicts(self):
        """测试包含冲突的假设"""
        hyp = Hypothesis(
            region="Japan/Osaka",
            rationale=["Japanese text"],
            supporting=["Japanese characters"],
            conflicts=["No Osaka landmarks"],
            confidence=0.5,
        )
        assert len(hyp.conflicts) == 1


class TestCandidate:
    """测试候选地点模型"""

    def test_create_candidate(self):
        """测试创建候选"""
        candidate = Candidate(
            name="Tokyo Station",
            lat=35.6812,
            lon=139.7671,
            source="poi_search",
            score=0.92,
        )
        assert candidate.name == "Tokyo Station"
        assert candidate.lat == 35.6812
        assert candidate.score == 0.92

    def test_candidate_validation(self):
        """测试候选验证"""
        # 纬度应该在 -90 到 90 之间
        with pytest.raises(Exception):
            Candidate(
                name="Invalid",
                lat=100.0,  # 超出范围
                lon=0.0,
                source="test",
                score=0.5,
            )

    def test_candidate_with_metadata(self):
        """测试包含元数据的候选"""
        candidate = Candidate(
            name="Tokyo Station",
            lat=35.6812,
            lon=139.7671,
            source="poi_search",
            score=0.92,
            address="Tokyo, Japan",
            metadata={"poi_id": "123", "category": "station"},
        )
        assert candidate.address == "Tokyo, Japan"
        assert candidate.metadata["poi_id"] == "123"


class TestEvidence:
    """测试验证证据模型"""

    def test_create_evidence(self):
        """测试创建证据"""
        evidence = Evidence(
            candidate_id="Tokyo Station",
            check="ocr_poi_match",
            result="pass",
            score=0.95,
        )
        assert evidence.candidate_id == "Tokyo Station"
        assert evidence.result == "pass"

    def test_evidence_with_details(self):
        """测试包含详细信息的证据"""
        evidence = Evidence(
            candidate_id="Tokyo Station",
            check="ocr_poi_match",
            result="pass",
            score=0.95,
            details={"matched_texts": ["Tokyo", "Station"]},
            reason="OCR text matches POI name",
        )
        assert len(evidence.details["matched_texts"]) == 2
        assert evidence.reason == "OCR text matches POI name"


class TestFinalResult:
    """测试最终结果模型"""

    def test_create_final_result(self):
        """测试创建最终结果"""
        result = FinalResult(
            answer="Tokyo Station, Tokyo, Japan",
            confidence=0.92,
            why="Strong evidence from OCR and POI match",
        )
        assert result.answer == "Tokyo Station, Tokyo, Japan"
        assert result.confidence == 0.92

    def test_final_result_with_coordinates(self):
        """测试包含坐标的最终结果"""
        result = FinalResult(
            answer="Tokyo Station",
            coordinates={"lat": 35.6812, "lon": 139.7671},
            confidence=0.92,
            why="Strong evidence",
            why_not=["Osaka: No matching landmarks"],
        )
        assert result.coordinates["lat"] == 35.6812
        assert len(result.why_not) == 1


class TestAgentState:
    """测试 Agent 状态模型"""

    def test_create_empty_state(self):
        """测试创建空状态"""
        state = AgentState()
        assert state.iteration == 0
        assert state.current_phase == "init"
        assert len(state.hypotheses) == 0
        assert len(state.candidates) == 0

    def test_state_with_image_path(self):
        """测试包含图像路径的状态"""
        state = AgentState(image_path="/path/to/image.jpg")
        assert state.image_path == "/path/to/image.jpg"

    def test_add_hypothesis(self):
        """测试添加假设"""
        state = AgentState()
        hyp = Hypothesis(
            region="Japan/Tokyo",
            rationale=["test"],
            supporting=["test"],
            confidence=0.8,
        )
        state.add_hypothesis(hyp)
        assert len(state.hypotheses) == 1

    def test_add_candidate(self):
        """测试添加候选"""
        state = AgentState()
        candidate = Candidate(
            name="Tokyo Station",
            lat=35.6812,
            lon=139.7671,
            source="test",
            score=0.9,
        )
        state.add_candidate(candidate)
        assert len(state.candidates) == 1

    def test_add_evidence(self):
        """测试添加证据"""
        state = AgentState()
        evidence = Evidence(
            candidate_id="test", check="test_check", result="pass", score=0.9
        )
        state.add_evidence(evidence)
        assert len(state.evidence) == 1

    def test_get_best_candidate(self):
        """测试获取最佳候选"""
        state = AgentState()
        state.add_candidate(
            Candidate(name="A", lat=0, lon=0, source="test", score=0.7)
        )
        state.add_candidate(
            Candidate(name="B", lat=0, lon=0, source="test", score=0.9)
        )
        state.add_candidate(
            Candidate(name="C", lat=0, lon=0, source="test", score=0.6)
        )

        best = state.get_best_candidate()
        assert best.name == "B"
        assert best.score == 0.9

    def test_is_complete(self):
        """测试完成状态检查"""
        state = AgentState()
        assert not state.is_complete()

        # 设置最终结果
        state.final = FinalResult(
            answer="test", confidence=0.8, why="test"
        )
        assert state.is_complete()

    def test_is_complete_max_iterations(self):
        """测试达到最大迭代次数"""
        state = AgentState(max_iterations=3)
        state.iteration = 3
        assert state.is_complete()

    def test_has_error(self):
        """测试错误检查"""
        state = AgentState()
        assert not state.has_error()

        state.error = "Some error"
        assert state.has_error()

    def test_get_passed_evidence_count(self):
        """测试获取通过验证的证据数量"""
        state = AgentState()
        state.add_evidence(
            Evidence(candidate_id="A", check="test1", result="pass")
        )
        state.add_evidence(
            Evidence(candidate_id="B", check="test2", result="fail")
        )
        state.add_evidence(
            Evidence(candidate_id="C", check="test3", result="pass")
        )

        assert state.get_passed_evidence_count() == 2

    def test_state_json_serialization(self):
        """测试状态的 JSON 序列化"""
        state = AgentState(image_path="/test/image.jpg", iteration=1)
        state.add_hypothesis(
            Hypothesis(
                region="Test",
                rationale=["test"],
                supporting=["test"],
                confidence=0.8,
            )
        )

        # 序列化
        json_str = state.model_dump_json()
        assert "/test/image.jpg" in json_str

        # 反序列化
        state2 = AgentState.model_validate_json(json_str)
        assert state2.image_path == "/test/image.jpg"
        assert len(state2.hypotheses) == 1


class TestCompleteWorkflow:
    """测试完整工作流"""

    def test_complete_phrv_workflow(self):
        """测试完整的 PHRV 流程"""
        # 1. 初始化状态
        state = AgentState(image_path="/path/to/image.jpg", max_iterations=5)

        # 2. Perception: 添加线索
        ocr = OCRText(text="Tokyo Station", bbox=[0, 0, 100, 50], confidence=0.95)
        feature = VisualFeature(
            type="architecture", value="modern station", confidence=0.85
        )
        state.clues = Clues(ocr=[ocr], visual=[feature])
        state.current_phase = "perception"

        # 3. Hypothesis: 添加假设
        state.add_hypothesis(
            Hypothesis(
                region="Japan/Tokyo",
                rationale=["Japanese text", "Station architecture"],
                supporting=["Tokyo OCR", "Modern building"],
                confidence=0.9,
            )
        )
        state.current_phase = "hypothesis"

        # 4. Retrieval: 添加候选
        state.add_candidate(
            Candidate(
                name="Tokyo Station",
                lat=35.6812,
                lon=139.7671,
                source="poi_search",
                score=0.95,
            )
        )
        state.current_phase = "retrieval"

        # 5. Verification: 添加证据
        state.add_evidence(
            Evidence(
                candidate_id="Tokyo Station",
                check="ocr_poi_match",
                result="pass",
                score=0.98,
                reason="OCR matches POI name",
            )
        )
        state.current_phase = "verification"

        # 6. Finalize: 设置最终结果
        state.final = FinalResult(
            answer="Tokyo Station, Tokyo, Japan",
            coordinates={"lat": 35.6812, "lon": 139.7671},
            confidence=0.95,
            why="Strong evidence: OCR matches POI, architecture matches",
            why_not=["Other candidates had lower scores"],
        )
        state.current_phase = "finalize"
        state.iteration = 1

        # 验证
        assert state.is_complete()
        assert state.final.confidence == 0.95
        assert state.get_passed_evidence_count() == 1
        assert state.get_best_candidate().name == "Tokyo Station"

