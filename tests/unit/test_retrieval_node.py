"""
Retrieval 节点测试
"""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from PIL import Image

from geomind.agent.nodes.retrieval import (
    create_hypothesis_query,
    retrieval,
    retrieval_node,
    retrieval_node_ensemble,
    retrieval_node_multi_scale,
    retrieval_node_with_fallback,
)
from geomind.agent.state import AgentState, Candidate, Hypothesis
from geomind.models.base import ModelResponse


class TestHypothesisQuery:
    """假设查询测试"""
    
    def test_create_query_basic(self):
        """测试基础查询创建"""
        hypothesis = Hypothesis(
            region="Paris, France",
            rationale="Eiffel Tower visible",
            supporting=["tower", "French architecture"],
            conflicting=[],
            confidence=0.9,
        )
        
        query = create_hypothesis_query(hypothesis)
        
        assert "Paris, France" in query
        assert "tower" in query or "French architecture" in query
    
    def test_create_query_no_supporting(self):
        """测试无支持证据的查询"""
        hypothesis = Hypothesis(
            region="London, UK",
            rationale="Big Ben visible",
            supporting=[],
            conflicting=[],
            confidence=0.8,
        )
        
        query = create_hypothesis_query(hypothesis)
        
        # 应该至少包含区域名称
        assert "London, UK" in query
    
    def test_create_query_limits_evidence(self):
        """测试限制证据数量"""
        hypothesis = Hypothesis(
            region="Tokyo, Japan",
            rationale="Many clues",
            supporting=["evidence1", "evidence2", "evidence3", "evidence4", "evidence5"],
            conflicting=[],
            confidence=0.85,
        )
        
        query = create_hypothesis_query(hypothesis)
        
        # 应该包含区域和部分证据（不超过 3 个）
        assert "Tokyo, Japan" in query


class TestRetrievalNode:
    """Retrieval 节点测试"""
    
    @pytest.fixture
    def sample_state_with_hypotheses(self, tmp_path):
        """创建带假设的示例状态"""
        # 创建测试图像
        image = Image.new('RGB', (224, 224), color='blue')
        image_path = tmp_path / "test_image.jpg"
        image.save(image_path)
        
        hypotheses = [
            Hypothesis(
                region="Paris, France",
                rationale="Eiffel Tower",
                supporting=["tower", "architecture"],
                conflicting=[],
                confidence=0.9,
            ),
            Hypothesis(
                region="London, UK",
                rationale="Big Ben",
                supporting=["clock", "gothic"],
                conflicting=[],
                confidence=0.7,
            ),
        ]
        
        return AgentState(
            image_path=str(image_path),
            hypotheses=hypotheses,
        )
    
    @pytest.fixture
    def mock_geoclip_response(self):
        """模拟 GeoCLIP 响应"""
        return {
            "image_encoding": ModelResponse.success_response(
                data=[0.1] * 512,  # 模拟 512 维编码
                metadata={"dim": 512}
            ),
            "text_encoding": ModelResponse.success_response(
                data=[0.2] * 512,
                metadata={"dim": 512}
            ),
            "location": ModelResponse.success_response(
                data={"lat": 48.8584, "lon": 2.2945},  # 埃菲尔铁塔坐标
                metadata={}
            ),
        }
    
    @pytest.mark.asyncio
    async def test_retrieval_node_success(
        self, sample_state_with_hypotheses, mock_geoclip_response
    ):
        """测试 Retrieval 节点成功执行"""
        
        # Mock GeoCLIP
        with patch('geomind.agent.nodes.retrieval.create_geoclip') as mock_create_geoclip:
            mock_geoclip = AsyncMock()
            mock_geoclip.initialize = AsyncMock()
            mock_geoclip.encode_image = AsyncMock(
                return_value=mock_geoclip_response["image_encoding"]
            )
            mock_geoclip.encode_text = AsyncMock(
                return_value=mock_geoclip_response["text_encoding"]
            )
            mock_geoclip.predict_location = AsyncMock(
                return_value=mock_geoclip_response["location"]
            )
            mock_geoclip.cleanup = AsyncMock()
            mock_create_geoclip.return_value = mock_geoclip
            
            # Mock 图像加载
            with patch('geomind.agent.nodes.retrieval.load_image') as mock_load_image:
                mock_load_image.return_value = Image.new('RGB', (224, 224))
                
                # 执行节点
                result = await retrieval_node(sample_state_with_hypotheses)
                
                # 验证返回结果
                assert "candidates" in result
                candidates = result["candidates"]
                
                assert isinstance(candidates, list)
                assert len(candidates) > 0
                
                # 验证候选结构
                c = candidates[0]
                assert isinstance(c, Candidate)
                assert c.lat != 0 or c.lon != 0
                assert c.score > 0
                
                # 验证 GeoCLIP 被调用
                mock_geoclip.initialize.assert_called_once()
                mock_geoclip.encode_image.assert_called_once()
                mock_geoclip.cleanup.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_retrieval_node_no_hypotheses(self, tmp_path):
        """测试没有假设时的情况"""
        image = Image.new('RGB', (224, 224))
        image_path = tmp_path / "test.jpg"
        image.save(image_path)
        
        state = AgentState(image_path=str(image_path), hypotheses=None)
        
        with pytest.raises(ValueError, match="不能为空"):
            await retrieval_node(state)
    
    @pytest.mark.asyncio
    async def test_retrieval_node_empty_hypotheses(self, tmp_path):
        """测试空假设列表"""
        image = Image.new('RGB', (224, 224))
        image_path = tmp_path / "test.jpg"
        image.save(image_path)
        
        state = AgentState(image_path=str(image_path), hypotheses=[])
        
        with pytest.raises(ValueError, match="不能为空"):
            await retrieval_node(state)
    
    @pytest.mark.asyncio
    async def test_retrieval_node_text_only(
        self, sample_state_with_hypotheses, mock_geoclip_response
    ):
        """测试仅使用文本"""
        
        with patch('geomind.agent.nodes.retrieval.create_geoclip') as mock_create_geoclip:
            mock_geoclip = AsyncMock()
            mock_geoclip.initialize = AsyncMock()
            mock_geoclip.encode_text = AsyncMock(
                return_value=mock_geoclip_response["text_encoding"]
            )
            mock_geoclip.predict_location = AsyncMock(
                return_value=mock_geoclip_response["location"]
            )
            mock_geoclip.cleanup = AsyncMock()
            mock_create_geoclip.return_value = mock_geoclip
            
            # 仅使用文本
            result = await retrieval_node(
                sample_state_with_hypotheses,
                use_image=False,
                use_text=True,
            )
            
            assert "candidates" in result
            
            # 图像编码不应该被调用
            mock_geoclip.encode_image.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_retrieval_node_top_k(
        self, sample_state_with_hypotheses, mock_geoclip_response
    ):
        """测试 top_k 限制"""
        
        # 创建更多假设
        many_hypotheses = [
            Hypothesis(
                region=f"City {i}",
                rationale="Test",
                supporting=[],
                conflicting=[],
                confidence=0.5 + i * 0.05,
            )
            for i in range(10)
        ]
        
        sample_state_with_hypotheses.hypotheses = many_hypotheses
        
        with patch('geomind.agent.nodes.retrieval.create_geoclip') as mock_create_geoclip:
            mock_geoclip = AsyncMock()
            mock_geoclip.initialize = AsyncMock()
            mock_geoclip.encode_image = AsyncMock(
                return_value=mock_geoclip_response["image_encoding"]
            )
            mock_geoclip.predict_location = AsyncMock(
                return_value=mock_geoclip_response["location"]
            )
            mock_geoclip.cleanup = AsyncMock()
            mock_create_geoclip.return_value = mock_geoclip
            
            with patch('geomind.agent.nodes.retrieval.load_image', return_value=Image.new('RGB', (224, 224))):
                # 限制为 3 个
                result = await retrieval_node(sample_state_with_hypotheses, top_k=3)
                
                assert len(result["candidates"]) <= 3
    
    @pytest.mark.asyncio
    async def test_retrieval_node_geoclip_failure(self, sample_state_with_hypotheses):
        """测试 GeoCLIP 初始化失败"""
        
        with patch('geomind.agent.nodes.retrieval.create_geoclip', side_effect=Exception("GeoCLIP 不可用")):
            with pytest.raises(RuntimeError, match="GeoCLIP 初始化失败"):
                await retrieval_node(sample_state_with_hypotheses)
    
    @pytest.mark.asyncio
    async def test_retrieval_node_invalid_image(self, sample_state_with_hypotheses):
        """测试无效图像路径"""
        sample_state_with_hypotheses.image_path = "nonexistent.jpg"
        
        with patch('geomind.agent.nodes.retrieval.load_image', side_effect=FileNotFoundError("File not found")):
            with pytest.raises(ValueError, match="无法加载图像"):
                await retrieval_node(sample_state_with_hypotheses)


class TestRetrievalNodeWithFallback:
    """带回退的 Retrieval 节点测试"""
    
    @pytest.fixture
    def sample_state(self, tmp_path):
        """创建示例状态"""
        image = Image.new('RGB', (224, 224))
        image_path = tmp_path / "test.jpg"
        image.save(image_path)
        
        return AgentState(
            image_path=str(image_path),
            hypotheses=[
                Hypothesis(
                    region="Test",
                    rationale="R",
                    supporting=[],
                    conflicting=[],
                    confidence=0.8,
                )
            ],
        )
    
    @pytest.mark.asyncio
    async def test_fallback_to_text(self, sample_state):
        """测试回退到文本"""
        
        location_response = ModelResponse.success_response(
            data={"lat": 48.8584, "lon": 2.2945},
            metadata={}
        )
        
        with patch('geomind.agent.nodes.retrieval.create_geoclip') as mock_create_geoclip:
            mock_geoclip = AsyncMock()
            mock_geoclip.initialize = AsyncMock()
            
            # 第一次调用（图像+文本）失败
            mock_geoclip.encode_image = AsyncMock(
                side_effect=Exception("图像编码失败")
            )
            
            # 第二次调用（仅文本）成功
            mock_geoclip.encode_text = AsyncMock(
                return_value=ModelResponse.success_response(data=[0.1] * 512, metadata={})
            )
            mock_geoclip.predict_location = AsyncMock(return_value=location_response)
            mock_geoclip.cleanup = AsyncMock()
            
            mock_create_geoclip.return_value = mock_geoclip
            
            with patch('geomind.agent.nodes.retrieval.load_image', return_value=Image.new('RGB', (224, 224))):
                # 应该成功回退
                result = await retrieval_node_with_fallback(sample_state)
                
                assert "candidates" in result


class TestRetrievalNodeMultiScale:
    """多尺度 Retrieval 节点测试"""
    
    @pytest.fixture
    def sample_state(self, tmp_path):
        """创建示例状态"""
        image = Image.new('RGB', (224, 224))
        image_path = tmp_path / "test.jpg"
        image.save(image_path)
        
        return AgentState(
            image_path=str(image_path),
            hypotheses=[
                Hypothesis(
                    region="Test City",
                    rationale="R",
                    supporting=[],
                    conflicting=[],
                    confidence=0.8,
                )
            ],
        )
    
    @pytest.mark.asyncio
    async def test_multi_scale_retrieval(self, sample_state):
        """测试多尺度召回"""
        
        location_response = ModelResponse.success_response(
            data={"lat": 48.8584, "lon": 2.2945},
            metadata={}
        )
        
        with patch('geomind.agent.nodes.retrieval.create_geoclip') as mock_create_geoclip:
            mock_geoclip = AsyncMock()
            mock_geoclip.initialize = AsyncMock()
            mock_geoclip.encode_image = AsyncMock(
                return_value=ModelResponse.success_response(data=[0.1] * 512, metadata={})
            )
            mock_geoclip.predict_location = AsyncMock(return_value=location_response)
            mock_geoclip.cleanup = AsyncMock()
            
            mock_create_geoclip.return_value = mock_geoclip
            
            with patch('geomind.agent.nodes.retrieval.load_image', return_value=Image.new('RGB', (224, 224))):
                result = await retrieval_node_multi_scale(
                    sample_state,
                    scales=["city", "region"],
                    top_k_per_scale=2,
                )
                
                assert "candidates" in result


class TestRetrievalNodeEnsemble:
    """集成 Retrieval 节点测试"""
    
    @pytest.fixture
    def sample_state(self, tmp_path):
        """创建示例状态"""
        image = Image.new('RGB', (224, 224))
        image_path = tmp_path / "test.jpg"
        image.save(image_path)
        
        return AgentState(
            image_path=str(image_path),
            hypotheses=[
                Hypothesis(
                    region="Test",
                    rationale="R",
                    supporting=[],
                    conflicting=[],
                    confidence=0.8,
                )
            ],
        )
    
    @pytest.mark.asyncio
    async def test_ensemble_retrieval(self, sample_state):
        """测试集成召回"""
        
        location_response = ModelResponse.success_response(
            data={"lat": 48.8584, "lon": 2.2945},
            metadata={}
        )
        
        with patch('geomind.agent.nodes.retrieval.create_geoclip') as mock_create_geoclip:
            mock_geoclip = AsyncMock()
            mock_geoclip.initialize = AsyncMock()
            mock_geoclip.encode_image = AsyncMock(
                return_value=ModelResponse.success_response(data=[0.1] * 512, metadata={})
            )
            mock_geoclip.predict_location = AsyncMock(return_value=location_response)
            mock_geoclip.cleanup = AsyncMock()
            
            mock_create_geoclip.return_value = mock_geoclip
            
            with patch('geomind.agent.nodes.retrieval.load_image', return_value=Image.new('RGB', (224, 224))):
                result = await retrieval_node_ensemble(sample_state, top_k=3)
                
                assert "candidates" in result
                # 集成可能会合并重复候选
                assert len(result["candidates"]) <= 3


class TestRetrievalWrapper:
    """LangGraph 包装函数测试"""
    
    @pytest.mark.asyncio
    async def test_retrieval_wrapper(self, tmp_path):
        """测试包装函数"""
        
        image = Image.new('RGB', (224, 224))
        image_path = tmp_path / "test.jpg"
        image.save(image_path)
        
        state = AgentState(
            image_path=str(image_path),
            hypotheses=[
                Hypothesis(
                    region="Test",
                    rationale="R",
                    supporting=[],
                    conflicting=[],
                    confidence=0.8,
                )
            ],
        )
        
        location_response = ModelResponse.success_response(
            data={"lat": 48.8584, "lon": 2.2945},
            metadata={}
        )
        
        with patch('geomind.agent.nodes.retrieval.create_geoclip') as mock_create_geoclip:
            mock_geoclip = AsyncMock()
            mock_geoclip.initialize = AsyncMock()
            mock_geoclip.encode_image = AsyncMock(
                return_value=ModelResponse.success_response(data=[0.1] * 512, metadata={})
            )
            mock_geoclip.predict_location = AsyncMock(return_value=location_response)
            mock_geoclip.cleanup = AsyncMock()
            
            mock_create_geoclip.return_value = mock_geoclip
            
            with patch('geomind.agent.nodes.retrieval.load_image', return_value=Image.new('RGB', (224, 224))):
                # 使用包装函数
                result = await retrieval(state)
                
                assert "candidates" in result
                assert isinstance(result["candidates"], list)


class TestRetrievalNodeIntegration:
    """Retrieval 节点集成测试"""
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(True, reason="需要实际的 GeoCLIP 模型")
    async def test_retrieval_node_real_geoclip(self, tmp_path):
        """使用真实 GeoCLIP 的集成测试"""
        
        # 创建测试图像
        image = Image.new('RGB', (224, 224), color='blue')
        image_path = tmp_path / "test_integration.jpg"
        image.save(image_path)
        
        hypotheses = [
            Hypothesis(
                region="Tokyo, Japan",
                rationale="Urban area",
                supporting=["modern", "Asian"],
                conflicting=[],
                confidence=0.85,
            )
        ]
        
        state = AgentState(image_path=str(image_path), hypotheses=hypotheses)
        
        # 执行 Retrieval
        result = await retrieval_node(state)
        
        # 验证结果
        assert "candidates" in result
        candidates = result["candidates"]
        assert len(candidates) > 0
        
        # 验证候选质量
        c = candidates[0]
        assert -90 <= c.lat <= 90
        assert -180 <= c.lon <= 180
        assert c.score > 0

