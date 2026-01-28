"""
Verification 节点测试
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from geomind.agent.nodes.verification import (
    verification,
    verification_node,
    verification_node_comprehensive,
    verification_node_simple,
    verify_candidate,
)
from geomind.agent.state import (
    AgentState,
    Candidate,
    Clues,
    Evidence,
    Metadata,
    OCRText,
    Prediction,
    VisualFeature,
)
from geomind.models.base import ModelResponse
from geomind.tools.base import ToolResult


class TestVerifyCandidate:
    """候选验证测试"""
    
    @pytest.fixture
    def sample_candidate(self):
        """创建示例候选"""
        return Candidate(
            lat=35.6812,
            lon=139.7671,
            name="Tokyo Station",
            hypothesis_source="Tokyo, Japan",
            score=0.85,
            retrieval_method="geoclip",
        )
    
    @pytest.fixture
    def sample_clues(self):
        """创建示例线索"""
        return Clues(
            ocr=[
                OCRText(text="Tokyo Station", bbox=[100, 200, 300, 250], confidence=0.95),
                OCRText(text="東京駅", bbox=[100, 260, 300, 310], confidence=0.90),
            ],
            visual=[
                VisualFeature(type="landmark", value="train station", confidence=0.85),
            ],
            meta=Metadata(scene_type="urban"),
        )
    
    @pytest.mark.asyncio
    async def test_verify_candidate_with_ocr_poi(
        self, sample_candidate, sample_clues
    ):
        """测试 OCR-POI 匹配验证"""
        
        # Mock OCR-POI 匹配
        mock_match_result = ToolResult.success(
            tool_name="match_ocr_poi",
            data={"match_count": 2, "confidence": 0.9},
            metadata={},
        )
        
        with patch('geomind.agent.nodes.verification.match_ocr_poi', return_value=mock_match_result):
            verified, evidence = await verify_candidate(
                sample_candidate,
                sample_clues,
                use_ocr_poi=True,
                use_language_prior=False,
                use_road_topology=False,
            )
            
            # 验证候选被更新
            assert isinstance(verified, Candidate)
            
            # 验证证据
            assert len(evidence) > 0
            assert any(e.type == "ocr_poi_match" for e in evidence)
    
    @pytest.mark.asyncio
    async def test_verify_candidate_with_language_prior(
        self, sample_candidate, sample_clues
    ):
        """测试语言先验验证"""
        
        # Mock 语言先验
        mock_prior_result = ToolResult.success(
            tool_name="check_language_prior",
            data={"consistency": "high", "confidence": 0.85},
            metadata={},
        )
        
        with patch('geomind.agent.nodes.verification.check_language_prior', return_value=mock_prior_result):
            verified, evidence = await verify_candidate(
                sample_candidate,
                sample_clues,
                use_ocr_poi=False,
                use_language_prior=True,
                use_road_topology=False,
            )
            
            # 验证证据
            assert len(evidence) > 0
            assert any(e.type == "language_prior" for e in evidence)
    
    @pytest.mark.asyncio
    async def test_verify_candidate_score_update(
        self, sample_candidate, sample_clues
    ):
        """测试分数更新"""
        
        original_score = sample_candidate.score
        
        # Mock 验证工具
        mock_result = ToolResult.success(
            tool_name="mock_tool",
            data={"confidence": 0.95},
            metadata={},
        )
        
        with patch('geomind.agent.nodes.verification.match_ocr_poi', return_value=mock_result):
            verified, evidence = await verify_candidate(
                sample_candidate,
                sample_clues,
                use_ocr_poi=True,
            )
            
            # 分数应该被更新（结合了证据）
            # 可能会变高或变低，取决于证据
            assert verified.score != original_score or len(evidence) == 0


class TestVerificationNode:
    """Verification 节点测试"""
    
    @pytest.fixture
    def sample_state_with_candidates(self):
        """创建带候选的示例状态"""
        clues = Clues(
            ocr=[
                OCRText(text="Eiffel Tower", bbox=[100, 200, 300, 250], confidence=0.95),
            ],
            visual=[
                VisualFeature(type="landmark", value="tower", confidence=0.90),
            ],
            meta=Metadata(),
        )
        
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
        
        return AgentState(
            image_path="test.jpg",
            clues=clues,
            candidates=candidates,
        )
    
    @pytest.mark.asyncio
    async def test_verification_node_success(self, sample_state_with_candidates):
        """测试 Verification 节点成功执行"""
        
        # Mock 验证工具
        mock_tool_result = ToolResult.success(
            tool_name="mock_tool",
            data={"confidence": 0.9},
            metadata={},
        )
        
        with patch('geomind.agent.nodes.verification.match_ocr_poi', return_value=mock_tool_result):
            with patch('geomind.agent.nodes.verification.check_language_prior', return_value=mock_tool_result):
                # 不使用 LLM 验证
                result = await verification_node(
                    sample_state_with_candidates,
                    use_llm_verification=False,
                )
                
                # 验证返回结果
                assert "prediction" in result
                assert "verified_candidates" in result
                assert "evidence" in result
                
                prediction = result["prediction"]
                assert isinstance(prediction, Prediction)
                assert prediction.lat != 0 or prediction.lon != 0
                assert 0 <= prediction.confidence <= 1
    
    @pytest.mark.asyncio
    async def test_verification_node_no_candidates(self):
        """测试没有候选时的情况"""
        clues = Clues(ocr=[], visual=[], meta=Metadata())
        state = AgentState(image_path="test.jpg", clues=clues, candidates=None)
        
        with pytest.raises(ValueError, match="不能为空"):
            await verification_node(state)
    
    @pytest.mark.asyncio
    async def test_verification_node_empty_candidates(self):
        """测试空候选列表"""
        clues = Clues(ocr=[], visual=[], meta=Metadata())
        state = AgentState(image_path="test.jpg", clues=clues, candidates=[])
        
        with pytest.raises(ValueError, match="不能为空"):
            await verification_node(state)
    
    @pytest.mark.asyncio
    async def test_verification_node_with_llm(self, sample_state_with_candidates):
        """测试使用 LLM 验证"""
        
        # Mock 验证工具
        mock_tool_result = ToolResult.success(
            tool_name="mock_tool",
            data={"confidence": 0.9},
            metadata={},
        )
        
        # Mock LLM
        mock_llm_response = ModelResponse.success_response(
            data='{"final_location": {"lat": 48.8584, "lon": 2.2945}, "confidence": 0.95, "reasoning": "Strong evidence", "supporting_evidence": ["tower", "architecture"]}',
            metadata={}
        )
        
        with patch('geomind.agent.nodes.verification.match_ocr_poi', return_value=mock_tool_result):
            with patch('geomind.agent.nodes.verification.check_language_prior', return_value=mock_tool_result):
                with patch('geomind.agent.nodes.verification.create_llm') as mock_create_llm:
                    mock_llm = AsyncMock()
                    mock_llm.initialize = AsyncMock()
                    mock_llm.generate = AsyncMock(return_value=mock_llm_response)
                    mock_llm.cleanup = AsyncMock()
                    mock_create_llm.return_value = mock_llm
                    
                    # 使用 LLM 验证
                    result = await verification_node(
                        sample_state_with_candidates,
                        use_llm_verification=True,
                    )
                    
                    assert "prediction" in result
                    
                    # LLM 应该被调用
                    mock_llm.initialize.assert_called_once()
                    mock_llm.generate.assert_called_once()
                    mock_llm.cleanup.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_verification_node_top_k(self, sample_state_with_candidates):
        """测试 top_k 限制"""
        
        mock_tool_result = ToolResult.success(
            tool_name="mock_tool",
            data={"confidence": 0.9},
            metadata={},
        )
        
        with patch('geomind.agent.nodes.verification.match_ocr_poi', return_value=mock_tool_result):
            with patch('geomind.agent.nodes.verification.check_language_prior', return_value=mock_tool_result):
                # 限制为 1 个
                result = await verification_node(
                    sample_state_with_candidates,
                    use_llm_verification=False,
                    top_k=1,
                )
                
                assert len(result["verified_candidates"]) == 1
    
    @pytest.mark.asyncio
    async def test_verification_node_sorts_by_score(
        self, sample_state_with_candidates
    ):
        """测试候选按分数排序"""
        
        mock_tool_result = ToolResult.success(
            tool_name="mock_tool",
            data={"confidence": 0.9},
            metadata={},
        )
        
        with patch('geomind.agent.nodes.verification.match_ocr_poi', return_value=mock_tool_result):
            with patch('geomind.agent.nodes.verification.check_language_prior', return_value=mock_tool_result):
                result = await verification_node(
                    sample_state_with_candidates,
                    use_llm_verification=False,
                )
                
                verified = result["verified_candidates"]
                
                # 验证排序（从高到低）
                if len(verified) > 1:
                    assert verified[0].score >= verified[1].score


class TestVerificationNodeVariants:
    """Verification 节点变体测试"""
    
    @pytest.fixture
    def sample_state(self):
        """创建示例状态"""
        clues = Clues(
            ocr=[OCRText(text="Test", bbox=[0, 0, 100, 100], confidence=0.9)],
            visual=[],
            meta=Metadata(),
        )
        
        candidates = [
            Candidate(
                lat=35.6812,
                lon=139.7671,
                name="Test Location",
                hypothesis_source="Test",
                score=0.8,
                retrieval_method="geoclip",
            )
        ]
        
        return AgentState(
            image_path="test.jpg",
            clues=clues,
            candidates=candidates,
        )
    
    @pytest.mark.asyncio
    async def test_verification_node_simple(self, sample_state):
        """测试简化版本"""
        
        mock_tool_result = ToolResult.success(
            tool_name="mock_tool",
            data={"confidence": 0.9},
            metadata={},
        )
        
        with patch('geomind.agent.nodes.verification.match_ocr_poi', return_value=mock_tool_result):
            with patch('geomind.agent.nodes.verification.check_language_prior', return_value=mock_tool_result):
                result = await verification_node_simple(sample_state)
                
                assert "prediction" in result
    
    @pytest.mark.asyncio
    async def test_verification_node_comprehensive(self, sample_state):
        """测试全面版本"""
        
        mock_tool_result = ToolResult.success(
            tool_name="mock_tool",
            data={"confidence": 0.9},
            metadata={},
        )
        
        # Mock LLM
        mock_llm_response = ModelResponse.success_response(
            data='{"final_location": {"lat": 35.6812, "lon": 139.7671}, "confidence": 0.9, "reasoning": "Test", "supporting_evidence": []}',
            metadata={}
        )
        
        with patch('geomind.agent.nodes.verification.match_ocr_poi', return_value=mock_tool_result):
            with patch('geomind.agent.nodes.verification.check_language_prior', return_value=mock_tool_result):
                with patch('geomind.agent.nodes.verification.verify_road_topology', return_value=mock_tool_result):
                    with patch('geomind.agent.nodes.verification.create_llm') as mock_create_llm:
                        mock_llm = AsyncMock()
                        mock_llm.initialize = AsyncMock()
                        mock_llm.generate = AsyncMock(return_value=mock_llm_response)
                        mock_llm.cleanup = AsyncMock()
                        mock_create_llm.return_value = mock_llm
                        
                        result = await verification_node_comprehensive(sample_state)
                        
                        assert "prediction" in result


class TestVerificationWrapper:
    """LangGraph 包装函数测试"""
    
    @pytest.mark.asyncio
    async def test_verification_wrapper(self):
        """测试包装函数"""
        
        clues = Clues(
            ocr=[OCRText(text="Test", bbox=[0, 0, 100, 100], confidence=0.9)],
            visual=[],
            meta=Metadata(),
        )
        
        candidates = [
            Candidate(
                lat=48.8584,
                lon=2.2945,
                name="Test",
                hypothesis_source="Test",
                score=0.8,
                retrieval_method="geoclip",
            )
        ]
        
        state = AgentState(
            image_path="test.jpg",
            clues=clues,
            candidates=candidates,
        )
        
        mock_tool_result = ToolResult.success(
            tool_name="mock_tool",
            data={"confidence": 0.9},
            metadata={},
        )
        
        with patch('geomind.agent.nodes.verification.match_ocr_poi', return_value=mock_tool_result):
            with patch('geomind.agent.nodes.verification.check_language_prior', return_value=mock_tool_result):
                # 使用包装函数
                result = await verification(state)
                
                assert "prediction" in result
                assert isinstance(result["prediction"], Prediction)


class TestVerificationNodeIntegration:
    """Verification 节点集成测试"""
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(True, reason="需要实际的验证工具和 LLM API")
    async def test_verification_node_real_tools(self):
        """使用真实工具的集成测试"""
        
        clues = Clues(
            ocr=[
                OCRText(text="Tokyo Tower", bbox=[100, 200, 300, 250], confidence=0.95),
            ],
            visual=[
                VisualFeature(type="landmark", value="tower", confidence=0.90),
            ],
            meta=Metadata(),
        )
        
        candidates = [
            Candidate(
                lat=35.6586,
                lon=139.7454,
                name="Tokyo Tower",
                hypothesis_source="Tokyo, Japan",
                score=0.90,
                retrieval_method="geoclip",
            )
        ]
        
        state = AgentState(
            image_path="test.jpg",
            clues=clues,
            candidates=candidates,
        )
        
        # 执行 Verification
        result = await verification_node(state)
        
        # 验证结果
        assert "prediction" in result
        prediction = result["prediction"]
        assert prediction.lat != 0
        assert prediction.lon != 0
        assert prediction.confidence > 0

