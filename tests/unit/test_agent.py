"""
Agent 和 Graph 测试
"""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from PIL import Image

from geomind.agent import GeoMindAgent, geolocate
from geomind.agent.graph import (
    create_iterative_phrv_graph,
    create_simple_phrv_graph,
    predict_location,
    run_phrv_workflow,
    should_continue,
)
from geomind.agent.state import AgentState, Prediction


class TestPHRVGraph:
    """PHRV 工作流图测试"""
    
    def test_create_simple_graph(self):
        """测试创建简单图"""
        graph = create_simple_phrv_graph()
        
        assert graph is not None
        # 图应该被编译
        assert hasattr(graph, 'ainvoke')
    
    def test_create_iterative_graph(self):
        """测试创建迭代图"""
        graph = create_iterative_phrv_graph(max_iterations=3)
        
        assert graph is not None
        assert hasattr(graph, 'ainvoke')
    
    def test_should_continue_high_confidence(self):
        """测试高置信度时结束"""
        state = AgentState(image_path="test.jpg")
        state.prediction = Prediction(
            lat=48.8584,
            lon=2.2945,
            confidence=0.9,  # 高置信度
            reasoning="Test",
        )
        
        result = should_continue(state)
        
        assert result == "end"
    
    def test_should_continue_low_confidence(self):
        """测试低置信度时继续（简化版直接结束）"""
        state = AgentState(image_path="test.jpg")
        state.prediction = Prediction(
            lat=48.8584,
            lon=2.2945,
            confidence=0.5,  # 低置信度
            reasoning="Test",
        )
        
        # 当前实现简化为总是结束
        result = should_continue(state)
        
        assert result == "end"
    
    @pytest.mark.asyncio
    async def test_run_phrv_workflow(self, tmp_path):
        """测试运行工作流"""
        # 创建测试图像
        image = Image.new('RGB', (224, 224))
        image_path = tmp_path / "test.jpg"
        image.save(image_path)
        
        # Mock 所有节点
        with patch('geomind.agent.graph.perception') as mock_perception:
            with patch('geomind.agent.graph.hypothesis') as mock_hypothesis:
                with patch('geomind.agent.graph.retrieval') as mock_retrieval:
                    with patch('geomind.agent.graph.verification') as mock_verification:
                        # 配置 mock
                        mock_perception.return_value = {"clues": MagicMock()}
                        mock_hypothesis.return_value = {"hypotheses": [MagicMock()]}
                        mock_retrieval.return_value = {"candidates": [MagicMock()]}
                        mock_verification.return_value = {
                            "prediction": Prediction(
                                lat=48.8584,
                                lon=2.2945,
                                confidence=0.9,
                                reasoning="Test prediction",
                            )
                        }
                        
                        # 运行工作流
                        final_state = await run_phrv_workflow(str(image_path))
                        
                        # 验证结果
                        assert final_state is not None
                        assert final_state.prediction is not None


class TestGeoMindAgent:
    """GeoMind Agent 测试"""
    
    def test_agent_initialization(self):
        """测试 Agent 初始化"""
        agent = GeoMindAgent()
        
        assert agent is not None
        assert agent.graph is not None
        assert agent.enable_iterations is False
    
    def test_agent_initialization_with_iterations(self):
        """测试迭代模式初始化"""
        agent = GeoMindAgent(enable_iterations=True, max_iterations=3)
        
        assert agent.enable_iterations is True
        assert agent.max_iterations == 3
    
    @pytest.mark.asyncio
    async def test_geolocate_success(self, tmp_path):
        """测试地理定位成功"""
        # 创建测试图像
        image = Image.new('RGB', (224, 224))
        image_path = tmp_path / "test.jpg"
        image.save(image_path)
        
        agent = GeoMindAgent()
        
        # Mock 工作流
        mock_prediction = Prediction(
            lat=35.6812,
            lon=139.7671,
            confidence=0.9,
            reasoning="Test",
        )
        
        with patch('geomind.agent.agent.run_phrv_workflow') as mock_workflow:
            mock_state = AgentState(image_path=str(image_path))
            mock_state.prediction = mock_prediction
            mock_workflow.return_value = mock_state
            
            # 执行地理定位
            prediction = await agent.geolocate(str(image_path))
            
            # 验证结果
            assert isinstance(prediction, Prediction)
            assert prediction.lat == 35.6812
            assert prediction.lon == 139.7671
            assert prediction.confidence == 0.9
    
    @pytest.mark.asyncio
    async def test_geolocate_file_not_found(self):
        """测试文件不存在时的错误"""
        agent = GeoMindAgent()
        
        with pytest.raises(FileNotFoundError):
            await agent.geolocate("nonexistent.jpg")
    
    @pytest.mark.asyncio
    async def test_geolocate_return_full_state(self, tmp_path):
        """测试返回完整状态"""
        # 创建测试图像
        image = Image.new('RGB', (224, 224))
        image_path = tmp_path / "test.jpg"
        image.save(image_path)
        
        agent = GeoMindAgent()
        
        # Mock 工作流
        mock_state = AgentState(image_path=str(image_path))
        mock_state.prediction = Prediction(
            lat=48.8584,
            lon=2.2945,
            confidence=0.85,
            reasoning="Test",
        )
        
        with patch('geomind.agent.agent.run_phrv_workflow', return_value=mock_state):
            # 获取完整状态
            state = await agent.geolocate(str(image_path), return_full_state=True)
            
            # 验证返回的是 AgentState
            assert isinstance(state, AgentState)
            assert state.prediction is not None
    
    @pytest.mark.asyncio
    async def test_batch_geolocate(self, tmp_path):
        """测试批量地理定位"""
        # 创建多个测试图像
        image_paths = []
        for i in range(3):
            image = Image.new('RGB', (224, 224))
            image_path = tmp_path / f"test{i}.jpg"
            image.save(image_path)
            image_paths.append(str(image_path))
        
        agent = GeoMindAgent()
        
        # Mock 工作流
        mock_prediction = Prediction(
            lat=35.0,
            lon=139.0,
            confidence=0.8,
            reasoning="Test",
        )
        
        with patch.object(agent, 'geolocate', return_value=mock_prediction):
            # 批量处理
            predictions = await agent.batch_geolocate(image_paths)
            
            # 验证结果
            assert len(predictions) == 3
            assert all(isinstance(p, Prediction) for p in predictions)
    
    def test_get_state_summary(self):
        """测试获取状态摘要"""
        agent = GeoMindAgent()
        
        state = AgentState(image_path="test.jpg")
        state.prediction = Prediction(
            lat=48.8584,
            lon=2.2945,
            confidence=0.9,
            reasoning="Test",
        )
        
        summary = agent.get_state_summary(state)
        
        assert "image_path" in summary
        assert "prediction" in summary
        assert summary["prediction"]["lat"] == 48.8584
        assert summary["prediction"]["confidence"] == 0.9
    
    def test_agent_repr(self):
        """测试 Agent 字符串表示"""
        agent = GeoMindAgent(enable_iterations=True, max_iterations=3)
        
        repr_str = repr(agent)
        
        assert "GeoMindAgent" in repr_str
        assert "enable_iterations=True" in repr_str
        assert "max_iterations=3" in repr_str


class TestConvenienceFunction:
    """便捷函数测试"""
    
    @pytest.mark.asyncio
    async def test_geolocate_function(self, tmp_path):
        """测试便捷函数"""
        # 创建测试图像
        image = Image.new('RGB', (224, 224))
        image_path = tmp_path / "test.jpg"
        image.save(image_path)
        
        # Mock 工作流
        mock_prediction = Prediction(
            lat=51.5007,
            lon=-0.1246,
            confidence=0.88,
            reasoning="Test",
        )
        
        mock_state = AgentState(image_path=str(image_path))
        mock_state.prediction = mock_prediction
        
        with patch('geomind.agent.agent.run_phrv_workflow', return_value=mock_state):
            # 使用便捷函数
            prediction = await geolocate(str(image_path))
            
            # 验证结果
            assert isinstance(prediction, Prediction)
            assert prediction.lat == 51.5007
            assert prediction.lon == -0.1246
    
    @pytest.mark.asyncio
    async def test_predict_location_function(self, tmp_path):
        """测试预测位置函数"""
        # 创建测试图像
        image = Image.new('RGB', (224, 224))
        image_path = tmp_path / "test.jpg"
        image.save(image_path)
        
        # Mock 工作流
        mock_state = AgentState(image_path=str(image_path))
        mock_state.prediction = Prediction(
            lat=40.7128,
            lon=-74.0060,
            confidence=0.75,
            reasoning="Test",
        )
        
        with patch('geomind.agent.graph.run_phrv_workflow', return_value=mock_state):
            # 使用预测函数
            state = await predict_location(str(image_path))
            
            # 验证结果
            assert isinstance(state, AgentState)
            assert state.prediction is not None


class TestIntegration:
    """集成测试"""
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(True, reason="需要实际的模型和 API")
    async def test_end_to_end_workflow(self, tmp_path):
        """端到端工作流测试"""
        # 创建测试图像
        image = Image.new('RGB', (224, 224), color='blue')
        image_path = tmp_path / "test_e2e.jpg"
        image.save(image_path)
        
        # 创建 Agent
        agent = GeoMindAgent()
        
        # 执行地理定位
        prediction = await agent.geolocate(str(image_path))
        
        # 验证结果
        assert isinstance(prediction, Prediction)
        assert -90 <= prediction.lat <= 90
        assert -180 <= prediction.lon <= 180
        assert 0 <= prediction.confidence <= 1

