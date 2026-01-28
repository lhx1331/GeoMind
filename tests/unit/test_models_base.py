"""
模型基类单元测试
"""

from typing import Any, Dict, List, Optional

import pytest
from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field

from geomind.models.base import (
    BaseLLM,
    ModelBase,
    BaseRetrievalModel,
    BaseVLM,
    ModelAPIError,
    ModelConfig,
    ModelError,
    ModelResponse,
    ModelTimeoutError,
    ModelType,
    ModelValidationError,
)


class TestModelType:
    """测试模型类型枚举"""

    def test_model_types(self):
        """测试模型类型"""
        assert ModelType.VLM == "vlm"
        assert ModelType.LLM == "llm"
        assert ModelType.RETRIEVAL == "retrieval"


class TestModelConfig:
    """测试模型配置"""

    def test_create_basic_config(self):
        """测试创建基础配置"""
        config = ModelConfig(
            model_type=ModelType.LLM,
            model_name="gpt-4",
        )
        assert config.model_type == ModelType.LLM
        assert config.model_name == "gpt-4"
        assert config.temperature == 0.0
        assert config.timeout == 60.0

    def test_create_full_config(self):
        """测试创建完整配置"""
        config = ModelConfig(
            model_type=ModelType.VLM,
            model_name="gpt-4-vision",
            api_key="test-key",
            base_url="https://api.example.com",
            temperature=0.7,
            max_tokens=2000,
            timeout=120.0,
            max_retries=5,
            stream=True,
            extra_params={"top_p": 0.9},
        )
        assert config.api_key == "test-key"
        assert config.temperature == 0.7
        assert config.max_tokens == 2000
        assert config.stream is True
        assert config.extra_params["top_p"] == 0.9

    def test_config_validation(self):
        """测试配置验证"""
        # 温度应该在 0-2 之间
        with pytest.raises(Exception):
            ModelConfig(
                model_type=ModelType.LLM,
                model_name="test",
                temperature=3.0,  # 超出范围
            )

    def test_config_json_serialization(self):
        """测试配置的 JSON 序列化"""
        config = ModelConfig(
            model_type=ModelType.LLM,
            model_name="gpt-4",
            temperature=0.5,
        )
        json_str = config.model_dump_json()
        config2 = ModelConfig.model_validate_json(json_str)
        assert config2.model_name == "gpt-4"
        assert config2.temperature == 0.5


class TestModelResponse:
    """测试模型响应"""

    def test_success_response(self):
        """测试成功响应"""
        response = ModelResponse[str].success_response(
            data="Tokyo Station",
            metadata={"model": "gpt-4"},
            usage={"prompt_tokens": 100, "completion_tokens": 50},
        )
        assert response.success is True
        assert response.data == "Tokyo Station"
        assert response.error is None
        assert response.metadata["model"] == "gpt-4"
        assert response.usage["prompt_tokens"] == 100

    def test_error_response(self):
        """测试错误响应"""
        response = ModelResponse[str].error_response(
            error="API Error",
            metadata={"status_code": 500},
        )
        assert response.success is False
        assert response.data is None
        assert response.error == "API Error"
        assert response.metadata["status_code"] == 500

    def test_generic_response(self):
        """测试泛型响应"""

        class CustomData(PydanticBaseModel):
            value: str
            score: float

        data = CustomData(value="test", score=0.95)
        response = ModelResponse[CustomData].success_response(data=data)

        assert response.success is True
        assert response.data.value == "test"
        assert response.data.score == 0.95

    def test_response_json_serialization(self):
        """测试响应的 JSON 序列化"""
        response = ModelResponse[str].success_response(
            data="test",
            metadata={"key": "value"},
        )
        json_str = response.model_dump_json()
        assert "test" in json_str
        assert "key" in json_str


class TestModelErrors:
    """测试模型错误"""

    def test_model_error(self):
        """测试基础模型错误"""
        error = ModelError("Something went wrong")
        assert str(error) == "Something went wrong"

    def test_model_error_with_name(self):
        """测试带模型名称的错误"""
        error = ModelError("API failed", model_name="gpt-4")
        assert "[gpt-4]" in str(error)
        assert "API failed" in str(error)

    def test_model_api_error(self):
        """测试 API 错误"""
        error = ModelAPIError("Rate limit exceeded", model_name="gpt-4")
        assert isinstance(error, ModelError)
        assert "Rate limit exceeded" in str(error)

    def test_model_timeout_error(self):
        """测试超时错误"""
        error = ModelTimeoutError("Request timeout")
        assert isinstance(error, ModelError)

    def test_model_validation_error(self):
        """测试验证错误"""
        error = ModelValidationError("Invalid output format")
        assert isinstance(error, ModelError)


class MockLLM(BaseLLM):
    """Mock LLM 实现"""

    async def initialize(self) -> None:
        self._initialized = True

    async def cleanup(self) -> None:
        self._initialized = False

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> ModelResponse[str]:
        return ModelResponse[str].success_response(
            data=f"Response to: {prompt}",
            metadata={"model": self.config.model_name},
        )

    async def generate_structured(
        self,
        prompt: str,
        response_format: type[PydanticBaseModel],
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> ModelResponse[PydanticBaseModel]:
        # 简单的 mock 实现
        instance = response_format()
        return ModelResponse[PydanticBaseModel].success_response(data=instance)


class MockVLM(BaseVLM):
    """Mock VLM 实现"""

    async def initialize(self) -> None:
        self._initialized = True

    async def cleanup(self) -> None:
        self._initialized = False

    async def analyze_image(
        self,
        image: Any,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> ModelResponse[str]:
        return ModelResponse[str].success_response(
            data="Image analysis result",
        )

    async def analyze_image_structured(
        self,
        image: Any,
        prompt: str,
        response_format: type[PydanticBaseModel],
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> ModelResponse[PydanticBaseModel]:
        instance = response_format()
        return ModelResponse[PydanticBaseModel].success_response(data=instance)

    async def batch_analyze(
        self,
        images: List[Any],
        prompts: List[str],
        **kwargs: Any,
    ) -> List[ModelResponse[str]]:
        return [
            ModelResponse[str].success_response(data=f"Result {i}")
            for i in range(len(images))
        ]


class MockRetrievalModel(BaseRetrievalModel):
    """Mock 检索模型实现"""

    async def initialize(self) -> None:
        self._initialized = True

    async def cleanup(self) -> None:
        self._initialized = False

    async def encode_image(
        self,
        image: Any,
        **kwargs: Any,
    ) -> ModelResponse[List[float]]:
        return ModelResponse[List[float]].success_response(
            data=[0.1, 0.2, 0.3],
        )

    async def encode_text(
        self,
        text: str,
        **kwargs: Any,
    ) -> ModelResponse[List[float]]:
        return ModelResponse[List[float]].success_response(
            data=[0.4, 0.5, 0.6],
        )

    async def retrieve(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        **kwargs: Any,
    ) -> ModelResponse[List[Dict[str, Any]]]:
        results = [
            {"name": f"Result {i}", "score": 0.9 - i * 0.1} for i in range(top_k)
        ]
        return ModelResponse[List[Dict[str, Any]]].success_response(data=results)


class TestBaseLLM:
    """测试 LLM 基类"""

    @pytest.mark.asyncio
    async def test_llm_initialization(self):
        """测试 LLM 初始化"""
        config = ModelConfig(
            model_type=ModelType.LLM,
            model_name="test-llm",
        )
        llm = MockLLM(config)

        assert not llm.is_initialized
        await llm.initialize()
        assert llm.is_initialized
        await llm.cleanup()
        assert not llm.is_initialized

    @pytest.mark.asyncio
    async def test_llm_generate(self):
        """测试 LLM 生成"""
        config = ModelConfig(
            model_type=ModelType.LLM,
            model_name="test-llm",
        )
        llm = MockLLM(config)
        await llm.initialize()

        response = await llm.generate("Hello")
        assert response.success is True
        assert "Hello" in response.data
        assert response.metadata["model"] == "test-llm"

        await llm.cleanup()

    @pytest.mark.asyncio
    async def test_llm_generate_structured(self):
        """测试 LLM 结构化生成"""

        class OutputFormat(PydanticBaseModel):
            text: str = Field(default="test")

        config = ModelConfig(
            model_type=ModelType.LLM,
            model_name="test-llm",
        )
        llm = MockLLM(config)
        await llm.initialize()

        response = await llm.generate_structured(
            "Generate output", response_format=OutputFormat
        )
        assert response.success is True
        assert isinstance(response.data, OutputFormat)

        await llm.cleanup()

    def test_llm_repr(self):
        """测试 LLM 表示"""
        config = ModelConfig(
            model_type=ModelType.LLM,
            model_name="test-llm",
        )
        llm = MockLLM(config)
        assert "MockLLM" in repr(llm)
        assert "test-llm" in repr(llm)


class TestBaseVLM:
    """测试 VLM 基类"""

    @pytest.mark.asyncio
    async def test_vlm_analyze_image(self):
        """测试 VLM 图像分析"""
        config = ModelConfig(
            model_type=ModelType.VLM,
            model_name="test-vlm",
        )
        vlm = MockVLM(config)
        await vlm.initialize()

        response = await vlm.analyze_image("image.jpg", "Describe this image")
        assert response.success is True
        assert response.data == "Image analysis result"

        await vlm.cleanup()

    @pytest.mark.asyncio
    async def test_vlm_analyze_image_structured(self):
        """测试 VLM 结构化图像分析"""

        class ImageAnalysis(PydanticBaseModel):
            description: str = Field(default="test")

        config = ModelConfig(
            model_type=ModelType.VLM,
            model_name="test-vlm",
        )
        vlm = MockVLM(config)
        await vlm.initialize()

        response = await vlm.analyze_image_structured(
            "image.jpg", "Describe", response_format=ImageAnalysis
        )
        assert response.success is True
        assert isinstance(response.data, ImageAnalysis)

        await vlm.cleanup()

    @pytest.mark.asyncio
    async def test_vlm_batch_analyze(self):
        """测试 VLM 批量分析"""
        config = ModelConfig(
            model_type=ModelType.VLM,
            model_name="test-vlm",
        )
        vlm = MockVLM(config)
        await vlm.initialize()

        images = ["img1.jpg", "img2.jpg", "img3.jpg"]
        prompts = ["Desc 1", "Desc 2", "Desc 3"]

        responses = await vlm.batch_analyze(images, prompts)
        assert len(responses) == 3
        assert all(r.success for r in responses)

        await vlm.cleanup()


class TestBaseRetrievalModel:
    """测试检索模型基类"""

    @pytest.mark.asyncio
    async def test_retrieval_encode_image(self):
        """测试图像编码"""
        config = ModelConfig(
            model_type=ModelType.RETRIEVAL,
            model_name="test-retrieval",
        )
        model = MockRetrievalModel(config)
        await model.initialize()

        response = await model.encode_image("image.jpg")
        assert response.success is True
        assert len(response.data) == 3
        assert response.data[0] == 0.1

        await model.cleanup()

    @pytest.mark.asyncio
    async def test_retrieval_encode_text(self):
        """测试文本编码"""
        config = ModelConfig(
            model_type=ModelType.RETRIEVAL,
            model_name="test-retrieval",
        )
        model = MockRetrievalModel(config)
        await model.initialize()

        response = await model.encode_text("Tokyo")
        assert response.success is True
        assert len(response.data) == 3
        assert response.data[0] == 0.4

        await model.cleanup()

    @pytest.mark.asyncio
    async def test_retrieval_retrieve(self):
        """测试检索"""
        config = ModelConfig(
            model_type=ModelType.RETRIEVAL,
            model_name="test-retrieval",
        )
        model = MockRetrievalModel(config)
        await model.initialize()

        query_embedding = [0.1, 0.2, 0.3]
        response = await model.retrieve(query_embedding, top_k=5)

        assert response.success is True
        assert len(response.data) == 5
        assert response.data[0]["name"] == "Result 0"
        assert response.data[0]["score"] == 0.9

        await model.cleanup()

