"""
VLM 模型单元测试
"""

import base64
from io import BytesIO
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from PIL import Image
from pydantic import BaseModel, Field

from geomind.models.base import ModelConfig, ModelType
from geomind.models.vlm import VLM, create_vlm


class TestVLMInitialization:
    """测试 VLM 初始化"""

    @pytest.mark.asyncio
    async def test_vlm_init_with_config(self):
        """测试使用配置初始化"""
        config = ModelConfig(
            model_type=ModelType.VLM,
            model_name="gpt-4-vision-preview",
            api_key="test-key",
            base_url="https://api.openai.com/v1",
        )
        vlm = VLM(config=config)

        assert vlm.config.model_name == "gpt-4-vision-preview"
        assert vlm.config.api_key == "test-key"
        assert not vlm.is_initialized

        await vlm.initialize()
        assert vlm.is_initialized
        assert vlm.client is not None

        await vlm.cleanup()
        assert not vlm.is_initialized
        assert vlm.client is None

    @pytest.mark.asyncio
    async def test_vlm_init_with_params(self):
        """测试使用参数初始化"""
        # 创建基础配置
        config = ModelConfig(
            model_type=ModelType.VLM,
            model_name="test-model",
            api_key="test-key",
        )
        
        vlm = VLM(
            config=config,
            api_key="custom-key",
            base_url="https://custom.api.com",
        )

        assert vlm.config.api_key == "custom-key"
        assert vlm.config.base_url == "https://custom.api.com"

        await vlm.initialize()
        await vlm.cleanup()

    @pytest.mark.asyncio
    async def test_create_vlm_helper(self):
        """测试便捷创建函数"""
        # Mock get_settings
        from unittest.mock import MagicMock, patch
        
        mock_settings = MagicMock()
        mock_settings.vlm.model = "gpt-4-vision"
        mock_settings.vlm.api_key = "test-key"
        mock_settings.vlm.base_url = "https://api.openai.com/v1"
        
        with patch("geomind.models.vlm.get_settings", return_value=mock_settings):
            vlm = await create_vlm(
                model_name="gpt-4-vision",
                api_key="test-key",
            )

            assert vlm.is_initialized
            assert vlm.config.model_name == "gpt-4-vision"

            await vlm.cleanup()


class TestImagePreparation:
    """测试图像准备"""

    @pytest.mark.asyncio
    async def test_prepare_image_url(self):
        """测试 URL 图像"""
        config = ModelConfig(
            model_type=ModelType.VLM,
            model_name="test",
            api_key="test",
        )
        vlm = VLM(config=config)

        image_url = "https://example.com/image.jpg"
        result = vlm._prepare_image(image_url)

        assert result["type"] == "image_url"
        assert result["image_url"]["url"] == image_url

    @pytest.mark.asyncio
    async def test_prepare_image_bytes(self):
        """测试字节流图像"""
        config = ModelConfig(
            model_type=ModelType.VLM,
            model_name="test",
            api_key="test",
        )
        vlm = VLM(config=config)

        # 创建测试图像字节
        img = Image.new("RGB", (100, 100), color="red")
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        image_bytes = buffer.getvalue()

        result = vlm._prepare_image(image_bytes)

        assert result["type"] == "image_url"
        assert "data:image/png;base64," in result["image_url"]["url"]

        # 验证 base64 编码
        base64_data = result["image_url"]["url"].split(",")[1]
        decoded = base64.b64decode(base64_data)
        assert decoded == image_bytes

    @pytest.mark.asyncio
    async def test_prepare_image_bytesio(self):
        """测试 BytesIO 图像"""
        config = ModelConfig(
            model_type=ModelType.VLM,
            model_name="test",
            api_key="test",
        )
        vlm = VLM(config=config)

        # 创建测试图像
        img = Image.new("RGB", (100, 100), color="blue")
        buffer = BytesIO()
        img.save(buffer, format="PNG")

        result = vlm._prepare_image(buffer)

        assert result["type"] == "image_url"
        assert "data:image/png;base64," in result["image_url"]["url"]

    @pytest.mark.asyncio
    async def test_prepare_image_invalid_type(self):
        """测试无效图像类型"""
        config = ModelConfig(
            model_type=ModelType.VLM,
            model_name="test",
            api_key="test",
        )
        vlm = VLM(config=config)

        with pytest.raises(ValueError, match="Unsupported image type"):
            vlm._prepare_image(12345)


class TestVLMAnalysis:
    """测试 VLM 分析"""

    @pytest.mark.asyncio
    async def test_analyze_image_success(self):
        """测试成功的图像分析"""
        config = ModelConfig(
            model_type=ModelType.VLM,
            model_name="gpt-4-vision",
            api_key="test-key",
        )
        vlm = VLM(config=config)
        await vlm.initialize()

        # Mock API 响应
        mock_response = {
            "choices": [
                {
                    "message": {"content": "This is a red square."},
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": 20,
                "total_tokens": 120,
            },
        }

        with patch.object(vlm, "_call_api", return_value=mock_response):
            response = await vlm.analyze_image(
                image="https://example.com/image.jpg",
                prompt="Describe this image",
            )

            assert response.success is True
            assert response.data == "This is a red square."
            assert response.usage["prompt_tokens"] == 100
            assert response.metadata["finish_reason"] == "stop"

        await vlm.cleanup()

    @pytest.mark.asyncio
    async def test_analyze_image_with_system_prompt(self):
        """测试带系统提示的分析"""
        config = ModelConfig(
            model_type=ModelType.VLM,
            model_name="gpt-4-vision",
            api_key="test-key",
        )
        vlm = VLM(config=config)
        await vlm.initialize()

        mock_response = {
            "choices": [{"message": {"content": "Analysis result"}}],
            "usage": {},
        }

        with patch.object(vlm, "_call_api", return_value=mock_response) as mock_call:
            await vlm.analyze_image(
                image="https://example.com/image.jpg",
                prompt="Analyze",
                system_prompt="You are an expert analyst",
            )

            # 验证调用参数
            call_args = mock_call.call_args[0][0]
            assert len(call_args) == 2
            assert call_args[0]["role"] == "system"
            assert call_args[0]["content"] == "You are an expert analyst"

        await vlm.cleanup()

    @pytest.mark.asyncio
    async def test_analyze_image_api_error(self):
        """测试 API 错误"""
        config = ModelConfig(
            model_type=ModelType.VLM,
            model_name="gpt-4-vision",
            api_key="test-key",
        )
        vlm = VLM(config=config)
        await vlm.initialize()

        from geomind.models.base import ModelAPIError

        with patch.object(
            vlm, "_call_api", side_effect=ModelAPIError("API Error", "gpt-4-vision")
        ):
            response = await vlm.analyze_image(
                image="https://example.com/image.jpg",
                prompt="Analyze",
            )

            assert response.success is False
            assert "API Error" in response.error

        await vlm.cleanup()


class TestVLMStructuredAnalysis:
    """测试 VLM 结构化分析"""

    @pytest.mark.asyncio
    async def test_analyze_image_structured_success(self):
        """测试成功的结构化分析"""

        class ImageDescription(BaseModel):
            """图像描述"""

            summary: str = Field(description="图像摘要")
            objects: list[str] = Field(description="检测到的物体")
            colors: list[str] = Field(description="主要颜色")

        config = ModelConfig(
            model_type=ModelType.VLM,
            model_name="gpt-4-vision",
            api_key="test-key",
        )
        vlm = VLM(config=config)
        await vlm.initialize()

        # Mock 文本响应
        json_response = """
        {
            "summary": "A red square on white background",
            "objects": ["square"],
            "colors": ["red", "white"]
        }
        """

        mock_text_response = MagicMock()
        mock_text_response.success = True
        mock_text_response.data = json_response
        mock_text_response.metadata = {"model": "gpt-4-vision"}
        mock_text_response.usage = {"prompt_tokens": 100}

        with patch.object(vlm, "analyze_image", return_value=mock_text_response):
            response = await vlm.analyze_image_structured(
                image="https://example.com/image.jpg",
                prompt="Describe",
                response_format=ImageDescription,
            )

            assert response.success is True
            assert isinstance(response.data, ImageDescription)
            assert response.data.summary == "A red square on white background"
            assert "square" in response.data.objects
            assert "red" in response.data.colors

        await vlm.cleanup()

    @pytest.mark.asyncio
    async def test_analyze_image_structured_with_markdown(self):
        """测试从 Markdown 代码块中提取 JSON"""

        class SimpleOutput(BaseModel):
            text: str

        config = ModelConfig(
            model_type=ModelType.VLM,
            model_name="gpt-4-vision",
            api_key="test-key",
        )
        vlm = VLM(config=config)
        await vlm.initialize()

        # Mock 响应（包含 markdown 代码块）
        markdown_response = """
        Here is the result:
        ```json
        {"text": "Test result"}
        ```
        """

        mock_text_response = MagicMock()
        mock_text_response.success = True
        mock_text_response.data = markdown_response
        mock_text_response.metadata = {}
        mock_text_response.usage = {}

        with patch.object(vlm, "analyze_image", return_value=mock_text_response):
            response = await vlm.analyze_image_structured(
                image="https://example.com/image.jpg",
                prompt="Analyze",
                response_format=SimpleOutput,
            )

            assert response.success is True
            assert response.data.text == "Test result"

        await vlm.cleanup()

    @pytest.mark.asyncio
    async def test_analyze_image_structured_invalid_json(self):
        """测试无效 JSON"""

        class SimpleOutput(BaseModel):
            text: str

        config = ModelConfig(
            model_type=ModelType.VLM,
            model_name="gpt-4-vision",
            api_key="test-key",
        )
        vlm = VLM(config=config)
        await vlm.initialize()

        # Mock 无效 JSON 响应
        mock_text_response = MagicMock()
        mock_text_response.success = True
        mock_text_response.data = "This is not JSON"
        mock_text_response.metadata = {}
        mock_text_response.usage = {}

        with patch.object(vlm, "analyze_image", return_value=mock_text_response):
            response = await vlm.analyze_image_structured(
                image="https://example.com/image.jpg",
                prompt="Analyze",
                response_format=SimpleOutput,
            )

            assert response.success is False
            assert "Failed to parse" in response.error

        await vlm.cleanup()


class TestVLMBatchAnalysis:
    """测试 VLM 批量分析"""

    @pytest.mark.asyncio
    async def test_batch_analyze_success(self):
        """测试成功的批量分析"""
        config = ModelConfig(
            model_type=ModelType.VLM,
            model_name="gpt-4-vision",
            api_key="test-key",
        )
        vlm = VLM(config=config)
        await vlm.initialize()

        # Mock 单个分析
        async def mock_analyze(image, prompt, **kwargs):
            from geomind.models.base import ModelResponse

            return ModelResponse[str].success_response(
                data=f"Analysis of {image}",
            )

        with patch.object(vlm, "analyze_image", side_effect=mock_analyze):
            images = ["img1.jpg", "img2.jpg", "img3.jpg"]
            prompts = ["Desc 1", "Desc 2", "Desc 3"]

            responses = await vlm.batch_analyze(images, prompts)

            assert len(responses) == 3
            assert all(r.success for r in responses)
            assert "img1.jpg" in responses[0].data

        await vlm.cleanup()

    @pytest.mark.asyncio
    async def test_batch_analyze_with_errors(self):
        """测试批量分析中的错误处理"""
        config = ModelConfig(
            model_type=ModelType.VLM,
            model_name="gpt-4-vision",
            api_key="test-key",
        )
        vlm = VLM(config=config)
        await vlm.initialize()

        # Mock 部分失败
        async def mock_analyze(image, prompt, **kwargs):
            from geomind.models.base import ModelResponse

            if "fail" in image:
                raise Exception("Analysis failed")
            return ModelResponse[str].success_response(data=f"Result for {image}")

        with patch.object(vlm, "analyze_image", side_effect=mock_analyze):
            images = ["img1.jpg", "fail.jpg", "img3.jpg"]
            prompts = ["Desc 1", "Desc 2", "Desc 3"]

            responses = await vlm.batch_analyze(images, prompts)

            assert len(responses) == 3
            assert responses[0].success is True
            assert responses[1].success is False
            assert responses[2].success is True
            assert "Analysis failed" in responses[1].error

        await vlm.cleanup()

    @pytest.mark.asyncio
    async def test_batch_analyze_mismatched_lengths(self):
        """测试不匹配的图像和提示列表"""
        config = ModelConfig(
            model_type=ModelType.VLM,
            model_name="gpt-4-vision",
            api_key="test-key",
        )
        vlm = VLM(config=config)
        await vlm.initialize()

        images = ["img1.jpg", "img2.jpg"]
        prompts = ["Desc 1"]  # 数量不匹配

        with pytest.raises(ValueError, match="must match"):
            await vlm.batch_analyze(images, prompts)

        await vlm.cleanup()


class TestVLMAPICall:
    """测试 VLM API 调用"""

    @pytest.mark.asyncio
    async def test_call_api_success(self):
        """测试成功的 API 调用"""
        config = ModelConfig(
            model_type=ModelType.VLM,
            model_name="gpt-4-vision",
            api_key="test-key",
        )
        vlm = VLM(config=config)
        await vlm.initialize()

        # Mock HTTP 响应
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Result"}}]
        }

        with patch.object(vlm.client, "post", return_value=mock_response):
            messages = [{"role": "user", "content": "Test"}]
            result = await vlm._call_api(messages)

            assert "choices" in result
            assert result["choices"][0]["message"]["content"] == "Result"

        await vlm.cleanup()

    @pytest.mark.asyncio
    async def test_call_api_timeout(self):
        """测试 API 超时"""
        config = ModelConfig(
            model_type=ModelType.VLM,
            model_name="gpt-4-vision",
            api_key="test-key",
        )
        vlm = VLM(config=config)
        await vlm.initialize()

        from geomind.models.base import ModelTimeoutError

        with patch.object(
            vlm.client, "post", side_effect=httpx.TimeoutException("Timeout")
        ):
            messages = [{"role": "user", "content": "Test"}]

            with pytest.raises(ModelTimeoutError):
                await vlm._call_api(messages)

        await vlm.cleanup()

    @pytest.mark.asyncio
    async def test_call_api_http_error(self):
        """测试 HTTP 错误"""
        config = ModelConfig(
            model_type=ModelType.VLM,
            model_name="gpt-4-vision",
            api_key="test-key",
        )
        vlm = VLM(config=config)
        await vlm.initialize()

        from geomind.models.base import ModelAPIError

        # Mock 错误响应
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"

        with patch.object(vlm.client, "post", return_value=mock_response):
            messages = [{"role": "user", "content": "Test"}]

            with pytest.raises(ModelAPIError, match="API error"):
                await vlm._call_api(messages)

        await vlm.cleanup()

    @pytest.mark.asyncio
    async def test_call_api_not_initialized(self):
        """测试未初始化时调用"""
        config = ModelConfig(
            model_type=ModelType.VLM,
            model_name="gpt-4-vision",
            api_key="test-key",
        )
        vlm = VLM(config=config)

        messages = [{"role": "user", "content": "Test"}]

        with pytest.raises(RuntimeError, match="not initialized"):
            await vlm._call_api(messages)

