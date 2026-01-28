"""
LLM 模型单元测试
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import BaseModel, Field

from geomind.models.base import ModelConfig, ModelType
from geomind.models.llm import LLM, create_llm


class TestLLMInitialization:
    """测试 LLM 初始化"""

    @pytest.mark.asyncio
    async def test_llm_init_with_config(self):
        """测试使用配置初始化"""
        config = ModelConfig(
            model_type=ModelType.LLM,
            model_name="gpt-4",
            api_key="test-key",
            base_url="https://api.openai.com/v1",
        )
        llm = LLM(config=config, provider="openai")

        assert llm.config.model_name == "gpt-4"
        assert llm.config.api_key == "test-key"
        assert llm.provider == "openai"
        assert not llm.is_initialized

        await llm.initialize()
        assert llm.is_initialized
        assert llm.client is not None

        await llm.cleanup()
        assert not llm.is_initialized
        assert llm.client is None

    @pytest.mark.asyncio
    async def test_llm_init_anthropic(self):
        """测试 Anthropic 初始化"""
        config = ModelConfig(
            model_type=ModelType.LLM,
            model_name="claude-3-opus",
            api_key="test-key",
        )
        llm = LLM(config=config, provider="anthropic")

        assert llm.provider == "anthropic"

        await llm.initialize()
        assert "https://api.anthropic.com" in llm.config.base_url
        assert llm.client is not None

        await llm.cleanup()

    @pytest.mark.asyncio
    async def test_create_llm_helper(self):
        """测试便捷创建函数"""
        mock_settings = MagicMock()
        mock_settings.llm.model = "gpt-4"
        mock_settings.llm.api_key = "test-key"
        mock_settings.llm.base_url = "https://api.openai.com/v1"
        mock_settings.llm.provider.value = "openai"
        mock_settings.llm.temperature = 0.0
        mock_settings.llm.max_tokens = 2000

        with patch("geomind.models.llm.get_settings", return_value=mock_settings):
            llm = await create_llm(
                model_name="gpt-4",
                api_key="test-key",
                provider="openai",
            )

            assert llm.is_initialized
            assert llm.config.model_name == "gpt-4"

            await llm.cleanup()


class TestLLMGeneration:
    """测试 LLM 生成"""

    @pytest.mark.asyncio
    async def test_generate_openai_success(self):
        """测试 OpenAI 成功生成"""
        config = ModelConfig(
            model_type=ModelType.LLM,
            model_name="gpt-4",
            api_key="test-key",
        )
        llm = LLM(config=config, provider="openai")
        await llm.initialize()

        # Mock API 响应
        mock_response = {
            "choices": [
                {
                    "message": {"content": "This is a test response."},
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 5,
                "total_tokens": 15,
            },
        }

        with patch.object(llm, "_call_api", return_value=mock_response):
            response = await llm.generate("Test prompt")

            assert response.success is True
            assert response.data == "This is a test response."
            assert response.usage["prompt_tokens"] == 10
            assert response.metadata["provider"] == "openai"

        await llm.cleanup()

    @pytest.mark.asyncio
    async def test_generate_anthropic_success(self):
        """测试 Anthropic 成功生成"""
        config = ModelConfig(
            model_type=ModelType.LLM,
            model_name="claude-3-opus",
            api_key="test-key",
        )
        llm = LLM(config=config, provider="anthropic")
        await llm.initialize()

        # Mock API 响应（Anthropic 格式）
        mock_response = {
            "content": [{"text": "This is Claude's response."}],
            "usage": {
                "input_tokens": 10,
                "output_tokens": 5,
            },
        }

        with patch.object(llm, "_call_api", return_value=mock_response):
            response = await llm.generate("Test prompt")

            assert response.success is True
            assert response.data == "This is Claude's response."
            assert response.usage["prompt_tokens"] == 10
            assert response.usage["completion_tokens"] == 5
            assert response.metadata["provider"] == "anthropic"

        await llm.cleanup()

    @pytest.mark.asyncio
    async def test_generate_with_system_prompt(self):
        """测试带系统提示的生成"""
        config = ModelConfig(
            model_type=ModelType.LLM,
            model_name="gpt-4",
            api_key="test-key",
        )
        llm = LLM(config=config, provider="openai")
        await llm.initialize()

        mock_response = {
            "choices": [{"message": {"content": "Response"}}],
            "usage": {},
        }

        with patch.object(llm, "_call_api", return_value=mock_response) as mock_call:
            await llm.generate(
                "User prompt",
                system_prompt="You are a helpful assistant",
            )

            # 验证调用参数
            call_args = mock_call.call_args[0][0]
            assert len(call_args) == 2
            assert call_args[0]["role"] == "system"
            assert call_args[0]["content"] == "You are a helpful assistant"
            assert call_args[1]["role"] == "user"

        await llm.cleanup()

    @pytest.mark.asyncio
    async def test_generate_api_error(self):
        """测试 API 错误"""
        config = ModelConfig(
            model_type=ModelType.LLM,
            model_name="gpt-4",
            api_key="test-key",
        )
        llm = LLM(config=config, provider="openai")
        await llm.initialize()

        from geomind.models.base import ModelAPIError

        with patch.object(
            llm, "_call_api", side_effect=ModelAPIError("API Error", "gpt-4")
        ):
            response = await llm.generate("Test prompt")

            assert response.success is False
            assert "API Error" in response.error

        await llm.cleanup()


class TestLLMStructuredGeneration:
    """测试 LLM 结构化生成"""

    @pytest.mark.asyncio
    async def test_generate_structured_success(self):
        """测试成功的结构化生成"""

        class OutputFormat(BaseModel):
            """输出格式"""

            summary: str = Field(description="摘要")
            keywords: list[str] = Field(description="关键词")

        config = ModelConfig(
            model_type=ModelType.LLM,
            model_name="gpt-4",
            api_key="test-key",
        )
        llm = LLM(config=config, provider="openai")
        await llm.initialize()

        # Mock 文本响应
        json_response = """
        {
            "summary": "Test summary",
            "keywords": ["test", "example"]
        }
        """

        mock_text_response = MagicMock()
        mock_text_response.success = True
        mock_text_response.data = json_response
        mock_text_response.metadata = {"model": "gpt-4", "provider": "openai"}
        mock_text_response.usage = {"prompt_tokens": 100}

        with patch.object(llm, "generate", return_value=mock_text_response):
            response = await llm.generate_structured(
                "Analyze this",
                response_format=OutputFormat,
            )

            assert response.success is True
            assert isinstance(response.data, OutputFormat)
            assert response.data.summary == "Test summary"
            assert "test" in response.data.keywords

        await llm.cleanup()

    @pytest.mark.asyncio
    async def test_generate_structured_with_markdown(self):
        """测试从 Markdown 代码块中提取 JSON"""

        class SimpleOutput(BaseModel):
            text: str

        config = ModelConfig(
            model_type=ModelType.LLM,
            model_name="gpt-4",
            api_key="test-key",
        )
        llm = LLM(config=config, provider="openai")
        await llm.initialize()

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

        with patch.object(llm, "generate", return_value=mock_text_response):
            response = await llm.generate_structured(
                "Generate",
                response_format=SimpleOutput,
            )

            assert response.success is True
            assert response.data.text == "Test result"

        await llm.cleanup()

    @pytest.mark.asyncio
    async def test_generate_structured_invalid_json(self):
        """测试无效 JSON"""

        class SimpleOutput(BaseModel):
            text: str

        config = ModelConfig(
            model_type=ModelType.LLM,
            model_name="gpt-4",
            api_key="test-key",
        )
        llm = LLM(config=config, provider="openai")
        await llm.initialize()

        # Mock 无效 JSON 响应
        mock_text_response = MagicMock()
        mock_text_response.success = True
        mock_text_response.data = "This is not JSON"
        mock_text_response.metadata = {}
        mock_text_response.usage = {}

        with patch.object(llm, "generate", return_value=mock_text_response):
            response = await llm.generate_structured(
                "Generate",
                response_format=SimpleOutput,
            )

            assert response.success is False
            assert "Failed to parse" in response.error

        await llm.cleanup()


class TestLLMStreaming:
    """测试 LLM 流式输出"""

    @pytest.mark.asyncio
    async def test_generate_stream_openai(self):
        """测试 OpenAI 流式生成"""
        config = ModelConfig(
            model_type=ModelType.LLM,
            model_name="gpt-4",
            api_key="test-key",
        )
        llm = LLM(config=config, provider="openai")
        await llm.initialize()

        # Mock 流式响应
        mock_stream_data = [
            'data: {"choices":[{"delta":{"content":"Hello"}}]}',
            'data: {"choices":[{"delta":{"content":" world"}}]}',
            'data: {"choices":[{"delta":{"content":"!"}}]}',
            "data: [DONE]",
        ]

        async def mock_aiter_lines():
            for line in mock_stream_data:
                yield line

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.aiter_lines = mock_aiter_lines

        with patch.object(
            llm.client, "stream", return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_response))
        ):
            chunks = []
            async for chunk in llm.generate_stream("Test prompt"):
                chunks.append(chunk)

            assert chunks == ["Hello", " world", "!"]

        await llm.cleanup()

    @pytest.mark.asyncio
    async def test_generate_stream_anthropic(self):
        """测试 Anthropic 流式生成"""
        config = ModelConfig(
            model_type=ModelType.LLM,
            model_name="claude-3-opus",
            api_key="test-key",
        )
        llm = LLM(config=config, provider="anthropic")
        await llm.initialize()

        # Mock 流式响应（Anthropic 格式）
        mock_stream_data = [
            'data: {"type":"content_block_delta","delta":{"type":"text_delta","text":"Hello"}}',
            'data: {"type":"content_block_delta","delta":{"type":"text_delta","text":" Claude"}}',
            "data: [DONE]",
        ]

        async def mock_aiter_lines():
            for line in mock_stream_data:
                yield line

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.aiter_lines = mock_aiter_lines

        with patch.object(
            llm.client, "stream", return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_response))
        ):
            chunks = []
            async for chunk in llm.generate_stream("Test prompt"):
                chunks.append(chunk)

            assert chunks == ["Hello", " Claude"]

        await llm.cleanup()


class TestLLMAPICall:
    """测试 LLM API 调用"""

    @pytest.mark.asyncio
    async def test_call_api_openai(self):
        """测试 OpenAI API 调用"""
        config = ModelConfig(
            model_type=ModelType.LLM,
            model_name="gpt-4",
            api_key="test-key",
        )
        llm = LLM(config=config, provider="openai")
        await llm.initialize()

        # Mock HTTP 响应
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Response"}}]
        }

        with patch.object(llm.client, "post", return_value=mock_response):
            messages = [{"role": "user", "content": "Test"}]
            result = await llm._call_api(messages)

            assert "choices" in result

        await llm.cleanup()

    @pytest.mark.asyncio
    async def test_call_api_anthropic(self):
        """测试 Anthropic API 调用"""
        config = ModelConfig(
            model_type=ModelType.LLM,
            model_name="claude-3-opus",
            api_key="test-key",
        )
        llm = LLM(config=config, provider="anthropic")
        await llm.initialize()

        # Mock HTTP 响应
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "content": [{"text": "Response"}]
        }

        with patch.object(llm.client, "post", return_value=mock_response) as mock_post:
            messages = [
                {"role": "system", "content": "System"},
                {"role": "user", "content": "Test"},
            ]
            result = await llm._call_api(messages)

            assert "content" in result
            
            # 验证请求格式
            call_kwargs = mock_post.call_args[1]
            request_data = call_kwargs["json"]
            assert "system" in request_data
            assert request_data["system"] == "System"
            assert len(request_data["messages"]) == 1  # 只有 user 消息

        await llm.cleanup()

    @pytest.mark.asyncio
    async def test_call_api_not_initialized(self):
        """测试未初始化时调用"""
        config = ModelConfig(
            model_type=ModelType.LLM,
            model_name="gpt-4",
            api_key="test-key",
        )
        llm = LLM(config=config, provider="openai")

        messages = [{"role": "user", "content": "Test"}]

        with pytest.raises(RuntimeError, match="not initialized"):
            await llm._call_api(messages)


class TestMessageBuilding:
    """测试消息构建"""

    def test_build_messages_no_system(self):
        """测试不带系统提示的消息构建"""
        config = ModelConfig(
            model_type=ModelType.LLM,
            model_name="gpt-4",
            api_key="test-key",
        )
        llm = LLM(config=config)

        messages = llm._build_messages("User prompt")

        assert len(messages) == 1
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "User prompt"

    def test_build_messages_with_system(self):
        """测试带系统提示的消息构建"""
        config = ModelConfig(
            model_type=ModelType.LLM,
            model_name="gpt-4",
            api_key="test-key",
        )
        llm = LLM(config=config)

        messages = llm._build_messages(
            "User prompt",
            system_prompt="System prompt",
        )

        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == "System prompt"
        assert messages[1]["role"] == "user"
        assert messages[1]["content"] == "User prompt"

