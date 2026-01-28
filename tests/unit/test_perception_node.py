"""
Perception 节点测试
"""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from PIL import Image

from geomind.agent.nodes.perception import (
    perception,
    perception_node,
    perception_node_with_fallback,
)
from geomind.agent.state import AgentState, Clues, Metadata, OCRText, VisualFeature
from geomind.models.base import ModelResponse
from geomind.prompts.perception import PerceptionOutput


class TestPerceptionNode:
    """Perception 节点测试"""
    
    @pytest.fixture
    def sample_state(self, tmp_path):
        """创建示例状态"""
        # 创建测试图像
        image = Image.new('RGB', (100, 100), color='red')
        image_path = tmp_path / "test_image.jpg"
        image.save(image_path)
        
        return AgentState(image_path=str(image_path))
    
    @pytest.fixture
    def mock_vlm_response(self):
        """模拟 VLM 响应"""
        return ModelResponse.success_response(
            data='{"ocr_texts": [{"text": "Tokyo Station", "bbox": [100, 200, 300, 250], "confidence": 0.95}], "visual_features": [{"type": "landmark", "value": "station", "confidence": 0.85}], "metadata": {}}',
            metadata={"model": "gpt-4o", "latency_ms": 1500}
        )
    
    @pytest.fixture
    def mock_exif_data(self):
        """模拟 EXIF 数据"""
        return {
            "DateTime": "2024:01:15 10:30:00",
            "Model": "Canon EOS R5",
            "GPS": {
                "GPSLatitude": 35.6812,
                "GPSLongitude": 139.7671
            }
        }
    
    @pytest.mark.asyncio
    async def test_perception_node_success(self, sample_state, mock_vlm_response, mock_exif_data):
        """测试 Perception 节点成功执行"""
        
        # Mock VLM
        with patch('geomind.agent.nodes.perception.create_vlm') as mock_create_vlm:
            mock_vlm = AsyncMock()
            mock_vlm.initialize = AsyncMock()
            mock_vlm.analyze_image = AsyncMock(return_value=mock_vlm_response)
            mock_vlm.cleanup = AsyncMock()
            mock_create_vlm.return_value = mock_vlm
            
            # Mock EXIF extraction
            with patch('geomind.agent.nodes.perception.extract_exif_data', return_value=mock_exif_data):
                # Mock image loading
                with patch('geomind.agent.nodes.perception.load_image') as mock_load_image:
                    mock_load_image.return_value = Image.new('RGB', (100, 100))
                    
                    # 执行节点
                    result = await perception_node(sample_state)
                    
                    # 验证返回结果
                    assert "clues" in result
                    clues = result["clues"]
                    
                    assert isinstance(clues, Clues)
                    assert len(clues.ocr) > 0
                    assert len(clues.visual) > 0
                    assert clues.meta is not None
                    
                    # 验证 VLM 被调用
                    mock_vlm.initialize.assert_called_once()
                    mock_vlm.analyze_image.assert_called_once()
                    mock_vlm.cleanup.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_perception_node_with_custom_provider(self, sample_state, mock_vlm_response):
        """测试指定 VLM 提供商"""
        
        with patch('geomind.agent.nodes.perception.create_vlm') as mock_create_vlm:
            mock_vlm = AsyncMock()
            mock_vlm.initialize = AsyncMock()
            mock_vlm.analyze_image = AsyncMock(return_value=mock_vlm_response)
            mock_vlm.cleanup = AsyncMock()
            mock_create_vlm.return_value = mock_vlm
            
            with patch('geomind.agent.nodes.perception.extract_exif_data', return_value={}):
                with patch('geomind.agent.nodes.perception.load_image', return_value=Image.new('RGB', (100, 100))):
                    # 使用自定义 provider
                    result = await perception_node(sample_state, vlm_provider="openai")
                    
                    # 验证 provider 参数被传递
                    mock_create_vlm.assert_called_once_with(provider="openai")
    
    @pytest.mark.asyncio
    async def test_perception_node_invalid_image(self):
        """测试无效图像路径"""
        state = AgentState(image_path="nonexistent.jpg")
        
        with patch('geomind.agent.nodes.perception.load_image', side_effect=FileNotFoundError("File not found")):
            with pytest.raises(ValueError, match="无法加载图像"):
                await perception_node(state)
    
    @pytest.mark.asyncio
    async def test_perception_node_vlm_failure(self, sample_state):
        """测试 VLM 调用失败"""
        
        # Mock VLM 返回失败响应
        error_response = ModelResponse.error_response(error="VLM API 错误")
        
        with patch('geomind.agent.nodes.perception.create_vlm') as mock_create_vlm:
            mock_vlm = AsyncMock()
            mock_vlm.initialize = AsyncMock()
            mock_vlm.analyze_image = AsyncMock(return_value=error_response)
            mock_vlm.cleanup = AsyncMock()
            mock_create_vlm.return_value = mock_vlm
            
            with patch('geomind.agent.nodes.perception.extract_exif_data', return_value={}):
                with patch('geomind.agent.nodes.perception.load_image', return_value=Image.new('RGB', (100, 100))):
                    with pytest.raises(RuntimeError, match="VLM 分析失败"):
                        await perception_node(sample_state)
    
    @pytest.mark.asyncio
    async def test_perception_node_with_fallback_success(self, sample_state, mock_vlm_response):
        """测试带回退的 Perception 节点成功"""
        
        with patch('geomind.agent.nodes.perception.create_vlm') as mock_create_vlm:
            mock_vlm = AsyncMock()
            mock_vlm.initialize = AsyncMock()
            mock_vlm.analyze_image = AsyncMock(return_value=mock_vlm_response)
            mock_vlm.cleanup = AsyncMock()
            mock_create_vlm.return_value = mock_vlm
            
            with patch('geomind.agent.nodes.perception.extract_exif_data', return_value={}):
                with patch('geomind.agent.nodes.perception.load_image', return_value=Image.new('RGB', (100, 100))):
                    result = await perception_node_with_fallback(sample_state)
                    
                    assert "clues" in result
                    assert isinstance(result["clues"], Clues)
    
    @pytest.mark.asyncio
    async def test_perception_node_with_fallback_to_exif(self, sample_state, mock_exif_data):
        """测试 VLM 失败时回退到 EXIF"""
        
        # Mock VLM 抛出异常
        with patch('geomind.agent.nodes.perception.create_vlm', side_effect=Exception("VLM 不可用")):
            with patch('geomind.agent.nodes.perception.extract_exif_data', return_value=mock_exif_data):
                with patch('geomind.agent.nodes.perception.load_image', return_value=Image.new('RGB', (100, 100))):
                    # 启用回退
                    result = await perception_node_with_fallback(
                        sample_state,
                        fallback_to_exif_only=True
                    )
                    
                    assert "clues" in result
                    clues = result["clues"]
                    
                    # 应该有元数据，但没有 OCR 和视觉特征
                    assert len(clues.ocr) == 0
                    assert len(clues.visual) == 0
                    assert clues.meta is not None
                    assert clues.meta.gps is not None
    
    @pytest.mark.asyncio
    async def test_perception_node_with_fallback_disabled(self, sample_state):
        """测试禁用回退时抛出异常"""
        
        with patch('geomind.agent.nodes.perception.create_vlm', side_effect=Exception("VLM 不可用")):
            with patch('geomind.agent.nodes.perception.load_image', return_value=Image.new('RGB', (100, 100))):
                with pytest.raises(Exception, match="VLM 不可用"):
                    await perception_node_with_fallback(
                        sample_state,
                        fallback_to_exif_only=False
                    )
    
    @pytest.mark.asyncio
    async def test_perception_wrapper_function(self, sample_state, mock_vlm_response):
        """测试 LangGraph 包装函数"""
        
        with patch('geomind.agent.nodes.perception.create_vlm') as mock_create_vlm:
            mock_vlm = AsyncMock()
            mock_vlm.initialize = AsyncMock()
            mock_vlm.analyze_image = AsyncMock(return_value=mock_vlm_response)
            mock_vlm.cleanup = AsyncMock()
            mock_create_vlm.return_value = mock_vlm
            
            with patch('geomind.agent.nodes.perception.extract_exif_data', return_value={}):
                with patch('geomind.agent.nodes.perception.load_image', return_value=Image.new('RGB', (100, 100))):
                    # 使用包装函数
                    result = await perception(sample_state)
                    
                    assert "clues" in result
                    assert isinstance(result["clues"], Clues)
    
    @pytest.mark.asyncio
    async def test_perception_node_exif_failure(self, sample_state, mock_vlm_response):
        """测试 EXIF 提取失败但 VLM 成功"""
        
        with patch('geomind.agent.nodes.perception.create_vlm') as mock_create_vlm:
            mock_vlm = AsyncMock()
            mock_vlm.initialize = AsyncMock()
            mock_vlm.analyze_image = AsyncMock(return_value=mock_vlm_response)
            mock_vlm.cleanup = AsyncMock()
            mock_create_vlm.return_value = mock_vlm
            
            # EXIF 提取失败
            with patch('geomind.agent.nodes.perception.extract_exif_data', side_effect=Exception("EXIF 错误")):
                with patch('geomind.agent.nodes.perception.load_image', return_value=Image.new('RGB', (100, 100))):
                    # 应该仍然成功，只是没有 EXIF 数据
                    result = await perception_node(sample_state)
                    
                    assert "clues" in result
                    clues = result["clues"]
                    
                    # 应该有 OCR 和视觉特征，但元数据为空
                    assert len(clues.ocr) > 0
                    assert len(clues.visual) > 0
                    # 元数据应该是空的
                    assert not clues.meta.exif


class TestPerceptionNodeIntegration:
    """Perception 节点集成测试"""
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(True, reason="需要实际的 VLM API")
    async def test_perception_node_real_vlm(self):
        """使用真实 VLM 的集成测试"""
        # 创建测试图像
        image = Image.new('RGB', (224, 224), color='blue')
        image_path = Path("test_integration_image.jpg")
        image.save(image_path)
        
        try:
            state = AgentState(image_path=str(image_path))
            
            # 执行 Perception
            result = await perception_node(state)
            
            # 验证结果
            assert "clues" in result
            clues = result["clues"]
            assert isinstance(clues, Clues)
            
        finally:
            # 清理
            if image_path.exists():
                image_path.unlink()

