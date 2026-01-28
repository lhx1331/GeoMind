"""
Hypothesis 节点测试
"""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from geomind.agent.nodes.hypothesis import (
    create_clues_summary,
    hypothesis,
    hypothesis_node,
    hypothesis_node_iterative,
    hypothesis_node_with_validation,
)
from geomind.agent.state import AgentState, Clues, Hypothesis, Metadata, OCRText, VisualFeature
from geomind.models.base import ModelResponse
from geomind.prompts.hypothesis import HypothesisOutput


class TestCluesSummary:
    """线索摘要测试"""
    
    def test_create_summary_with_all_clues(self):
        """测试完整线索摘要"""
        clues = Clues(
            ocr=[
                OCRText(text="Tokyo Station", bbox=[100, 200, 300, 250], confidence=0.95),
                OCRText(text="東京駅", bbox=[100, 260, 300, 310], confidence=0.90),
            ],
            visual=[
                VisualFeature(type="landmark", value="train station", confidence=0.85),
                VisualFeature(type="architecture", value="modern building", confidence=0.80),
            ],
            meta=Metadata(
                gps={"GPSLatitude": 35.6812, "GPSLongitude": 139.7671},
                timestamp="2024:01:15 10:30:00",
                camera_info="Canon EOS R5",
            ),
        )
        
        summary = create_clues_summary(clues)
        
        # 验证包含所有部分
        assert "OCR 文本" in summary
        assert "Tokyo Station" in summary
        assert "視覚特征" in summary or "视觉特征" in summary
        assert "train station" in summary
        assert "元数据" in summary
        assert "GPS" in summary
    
    def test_create_summary_with_empty_clues(self):
        """测试空线索"""
        clues = Clues(ocr=[], visual=[], meta=Metadata())
        
        summary = create_clues_summary(clues)
        
        assert "未提取到任何线索" in summary
    
    def test_create_summary_ocr_only(self):
        """测试仅 OCR 线索"""
        clues = Clues(
            ocr=[OCRText(text="Test", bbox=[0, 0, 100, 100], confidence=0.9)],
            visual=[],
            meta=Metadata(),
        )
        
        summary = create_clues_summary(clues)
        
        assert "OCR 文本" in summary
        assert "Test" in summary
        assert "視覚特征" not in summary and "视觉特征" not in summary
    
    def test_create_summary_limits_items(self):
        """测试限制摘要项数量"""
        # 创建超过 10 个 OCR
        clues = Clues(
            ocr=[
                OCRText(text=f"Text {i}", bbox=[0, 0, 100, 100], confidence=0.9)
                for i in range(15)
            ],
            visual=[],
            meta=Metadata(),
        )
        
        summary = create_clues_summary(clues)
        
        # 应该只包含前 10 个
        assert "Text 0" in summary
        assert "Text 9" in summary
        assert "Text 14" not in summary


class TestHypothesisNode:
    """Hypothesis 节点测试"""
    
    @pytest.fixture
    def sample_state_with_clues(self):
        """创建带线索的示例状态"""
        clues = Clues(
            ocr=[
                OCRText(text="Eiffel Tower", bbox=[100, 200, 300, 250], confidence=0.95),
            ],
            visual=[
                VisualFeature(type="landmark", value="tower", confidence=0.90),
            ],
            meta=Metadata(),
        )
        
        return AgentState(
            image_path="test.jpg",
            clues=clues,
        )
    
    @pytest.fixture
    def mock_llm_response(self):
        """模拟 LLM 响应"""
        return ModelResponse.success_response(
            data='{"hypotheses": [{"region": "Paris, France", "rationale": "Eiffel Tower is visible", "supporting": ["tower structure", "architectural style"], "conflicting": [], "confidence": 0.9}]}',
            metadata={"model": "gpt-4", "latency_ms": 2000}
        )
    
    @pytest.mark.asyncio
    async def test_hypothesis_node_success(self, sample_state_with_clues, mock_llm_response):
        """测试 Hypothesis 节点成功执行"""
        
        # Mock LLM
        with patch('geomind.agent.nodes.hypothesis.create_llm') as mock_create_llm:
            mock_llm = AsyncMock()
            mock_llm.initialize = AsyncMock()
            mock_llm.generate = AsyncMock(return_value=mock_llm_response)
            mock_llm.cleanup = AsyncMock()
            mock_create_llm.return_value = mock_llm
            
            # 执行节点
            result = await hypothesis_node(sample_state_with_clues)
            
            # 验证返回结果
            assert "hypotheses" in result
            hypotheses = result["hypotheses"]
            
            assert isinstance(hypotheses, list)
            assert len(hypotheses) > 0
            
            # 验证假设结构
            h = hypotheses[0]
            assert isinstance(h, Hypothesis)
            assert h.region
            assert h.rationale
            assert 0 <= h.confidence <= 1
            
            # 验证 LLM 被调用
            mock_llm.initialize.assert_called_once()
            mock_llm.generate.assert_called_once()
            mock_llm.cleanup.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_hypothesis_node_no_clues(self):
        """测试没有线索时的情况"""
        state = AgentState(image_path="test.jpg", clues=None)
        
        with pytest.raises(ValueError, match="不能为空"):
            await hypothesis_node(state)
    
    @pytest.mark.asyncio
    async def test_hypothesis_node_empty_clues(self):
        """测试空线索"""
        clues = Clues(ocr=[], visual=[], meta=Metadata())
        state = AgentState(image_path="test.jpg", clues=clues)
        
        result = await hypothesis_node(state)
        
        # 应该返回空列表
        assert result["hypotheses"] == []
    
    @pytest.mark.asyncio
    async def test_hypothesis_node_with_custom_provider(self, sample_state_with_clues, mock_llm_response):
        """测试指定 LLM 提供商"""
        
        with patch('geomind.agent.nodes.hypothesis.create_llm') as mock_create_llm:
            mock_llm = AsyncMock()
            mock_llm.initialize = AsyncMock()
            mock_llm.generate = AsyncMock(return_value=mock_llm_response)
            mock_llm.cleanup = AsyncMock()
            mock_create_llm.return_value = mock_llm
            
            # 使用自定义 provider
            result = await hypothesis_node(sample_state_with_clues, llm_provider="deepseek")
            
            # 验证 provider 参数被传递
            mock_create_llm.assert_called_once_with(provider="deepseek")
    
    @pytest.mark.asyncio
    async def test_hypothesis_node_max_hypotheses(self, sample_state_with_clues):
        """测试限制假设数量"""
        
        # Mock 返回多个假设
        multi_response = ModelResponse.success_response(
            data='{"hypotheses": [' + 
                 ','.join([
                     '{"region": "Region ' + str(i) + '", "rationale": "Reason", "supporting": [], "conflicting": [], "confidence": 0.8}'
                     for i in range(10)
                 ]) + 
                 ']}',
            metadata={}
        )
        
        with patch('geomind.agent.nodes.hypothesis.create_llm') as mock_create_llm:
            mock_llm = AsyncMock()
            mock_llm.initialize = AsyncMock()
            mock_llm.generate = AsyncMock(return_value=multi_response)
            mock_llm.cleanup = AsyncMock()
            mock_create_llm.return_value = mock_llm
            
            # 限制为 3 个
            result = await hypothesis_node(sample_state_with_clues, max_hypotheses=3)
            
            assert len(result["hypotheses"]) == 3
    
    @pytest.mark.asyncio
    async def test_hypothesis_node_sorted_by_confidence(self, sample_state_with_clues):
        """测试假设按置信度排序"""
        
        # Mock 返回不同置信度的假设
        response = ModelResponse.success_response(
            data='{"hypotheses": [' +
                 '{"region": "Low", "rationale": "R", "supporting": [], "conflicting": [], "confidence": 0.3},' +
                 '{"region": "High", "rationale": "R", "supporting": [], "conflicting": [], "confidence": 0.9},' +
                 '{"region": "Medium", "rationale": "R", "supporting": [], "conflicting": [], "confidence": 0.6}' +
                 ']}',
            metadata={}
        )
        
        with patch('geomind.agent.nodes.hypothesis.create_llm') as mock_create_llm:
            mock_llm = AsyncMock()
            mock_llm.initialize = AsyncMock()
            mock_llm.generate = AsyncMock(return_value=response)
            mock_llm.cleanup = AsyncMock()
            mock_create_llm.return_value = mock_llm
            
            result = await hypothesis_node(sample_state_with_clues)
            
            hypotheses = result["hypotheses"]
            
            # 验证排序（从高到低）
            assert hypotheses[0].confidence == 0.9
            assert hypotheses[1].confidence == 0.6
            assert hypotheses[2].confidence == 0.3
    
    @pytest.mark.asyncio
    async def test_hypothesis_node_llm_failure(self, sample_state_with_clues):
        """测试 LLM 调用失败"""
        
        error_response = ModelResponse.error_response(error="LLM API 错误")
        
        with patch('geomind.agent.nodes.hypothesis.create_llm') as mock_create_llm:
            mock_llm = AsyncMock()
            mock_llm.initialize = AsyncMock()
            mock_llm.generate = AsyncMock(return_value=error_response)
            mock_llm.cleanup = AsyncMock()
            mock_create_llm.return_value = mock_llm
            
            with pytest.raises(RuntimeError, match="LLM 生成失败"):
                await hypothesis_node(sample_state_with_clues)


class TestHypothesisNodeWithValidation:
    """带验证的 Hypothesis 节点测试"""
    
    @pytest.fixture
    def sample_state(self):
        """创建示例状态"""
        clues = Clues(
            ocr=[OCRText(text="Test", bbox=[0, 0, 100, 100], confidence=0.9)],
            visual=[],
            meta=Metadata(),
        )
        return AgentState(image_path="test.jpg", clues=clues)
    
    @pytest.mark.asyncio
    async def test_validation_filters_low_confidence(self, sample_state):
        """测试过滤低置信度假设"""
        
        response = ModelResponse.success_response(
            data='{"hypotheses": [' +
                 '{"region": "High", "rationale": "R", "supporting": [], "conflicting": [], "confidence": 0.8},' +
                 '{"region": "Low", "rationale": "R", "supporting": [], "conflicting": [], "confidence": 0.2}' +
                 ']}',
            metadata={}
        )
        
        with patch('geomind.agent.nodes.hypothesis.create_llm') as mock_create_llm:
            mock_llm = AsyncMock()
            mock_llm.initialize = AsyncMock()
            mock_llm.generate = AsyncMock(return_value=response)
            mock_llm.cleanup = AsyncMock()
            mock_create_llm.return_value = mock_llm
            
            # 设置最小置信度为 0.5
            result = await hypothesis_node_with_validation(sample_state, min_confidence=0.5)
            
            # 应该只保留高置信度的
            assert len(result["hypotheses"]) == 1
            assert result["hypotheses"][0].confidence == 0.8


class TestHypothesisNodeIterative:
    """迭代式 Hypothesis 节点测试"""
    
    @pytest.fixture
    def sample_state(self):
        """创建示例状态"""
        clues = Clues(
            ocr=[OCRText(text="Test", bbox=[0, 0, 100, 100], confidence=0.9)],
            visual=[],
            meta=Metadata(),
        )
        return AgentState(image_path="test.jpg", clues=clues)
    
    @pytest.mark.asyncio
    async def test_iterative_multiple_calls(self, sample_state):
        """测试迭代调用"""
        
        response = ModelResponse.success_response(
            data='{"hypotheses": [{"region": "Test", "rationale": "R", "supporting": [], "conflicting": [], "confidence": 0.8}]}',
            metadata={}
        )
        
        with patch('geomind.agent.nodes.hypothesis.create_llm') as mock_create_llm:
            mock_llm = AsyncMock()
            mock_llm.initialize = AsyncMock()
            mock_llm.generate = AsyncMock(return_value=response)
            mock_llm.cleanup = AsyncMock()
            mock_create_llm.return_value = mock_llm
            
            # 3 次迭代
            result = await hypothesis_node_iterative(sample_state, max_iterations=3)
            
            # 验证 LLM 被调用 3 次
            assert mock_llm.generate.call_count == 3
            assert "hypotheses" in result


class TestHypothesisWrapper:
    """LangGraph 包装函数测试"""
    
    @pytest.mark.asyncio
    async def test_hypothesis_wrapper(self):
        """测试包装函数"""
        
        clues = Clues(
            ocr=[OCRText(text="Test", bbox=[0, 0, 100, 100], confidence=0.9)],
            visual=[],
            meta=Metadata(),
        )
        state = AgentState(image_path="test.jpg", clues=clues)
        
        response = ModelResponse.success_response(
            data='{"hypotheses": [{"region": "Test", "rationale": "R", "supporting": [], "conflicting": [], "confidence": 0.8}]}',
            metadata={}
        )
        
        with patch('geomind.agent.nodes.hypothesis.create_llm') as mock_create_llm:
            mock_llm = AsyncMock()
            mock_llm.initialize = AsyncMock()
            mock_llm.generate = AsyncMock(return_value=response)
            mock_llm.cleanup = AsyncMock()
            mock_create_llm.return_value = mock_llm
            
            # 使用包装函数
            result = await hypothesis(state)
            
            assert "hypotheses" in result
            assert isinstance(result["hypotheses"], list)


class TestHypothesisNodeIntegration:
    """Hypothesis 节点集成测试"""
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(True, reason="需要实际的 LLM API")
    async def test_hypothesis_node_real_llm(self):
        """使用真实 LLM 的集成测试"""
        
        clues = Clues(
            ocr=[
                OCRText(text="Shibuya Crossing", bbox=[100, 200, 300, 250], confidence=0.95),
            ],
            visual=[
                VisualFeature(type="urban", value="busy intersection", confidence=0.90),
            ],
            meta=Metadata(),
        )
        
        state = AgentState(image_path="test.jpg", clues=clues)
        
        # 执行 Hypothesis
        result = await hypothesis_node(state)
        
        # 验证结果
        assert "hypotheses" in result
        hypotheses = result["hypotheses"]
        assert len(hypotheses) > 0
        
        # 验证假设质量
        h = hypotheses[0]
        assert h.region  # 应该包含地区信息
        assert h.confidence > 0  # 应该有置信度

