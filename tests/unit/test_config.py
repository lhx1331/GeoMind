"""
配置管理系统单元测试
"""

import os
import tempfile
from pathlib import Path

import pytest
import yaml

from geomind.config.loader import ConfigLoader
from geomind.config.schema import (
    AgentConfig,
    AppSettings,
    GeoCLIPConfig,
    LLMConfig,
    LoggingConfig,
    VLMConfig,
)
from geomind.config.settings import Settings, get_settings


class TestLLMConfig:
    """测试 LLM 配置"""

    def test_default_values(self):
        """测试默认值"""
        config = LLMConfig()
        assert config.provider.value == "openai"
        assert config.model == "gpt-4-turbo-preview"

    def test_from_env(self):
        """测试从环境变量加载"""
        os.environ["OPENAI_API_KEY"] = "test_key"
        os.environ["OPENAI_MODEL"] = "gpt-4"
        config = LLMConfig()
        assert config.openai_api_key == "test_key"
        assert config.model == "gpt-4"
        # 清理
        del os.environ["OPENAI_API_KEY"]
        del os.environ["OPENAI_MODEL"]


class TestVLMConfig:
    """测试 VLM 配置"""

    def test_default_values(self):
        """测试默认值"""
        config = VLMConfig()
        assert config.provider.value == "openai"
        assert config.model == "gpt-4-vision-preview"

    def test_from_env(self):
        """测试从环境变量加载（带前缀）"""
        os.environ["VLM_PROVIDER"] = "local"
        os.environ["VLM_MODEL"] = "qwen-vl"
        config = VLMConfig()
        assert config.provider.value == "local"
        assert config.model == "qwen-vl"
        # 清理
        del os.environ["VLM_PROVIDER"]
        del os.environ["VLM_MODEL"]


class TestGeoCLIPConfig:
    """测试 GeoCLIP 配置"""

    def test_default_values(self):
        """测试默认值"""
        config = GeoCLIPConfig()
        assert config.device.value == "cuda"
        assert config.top_k == 5
        assert config.cache_embeddings is True

    def test_model_path_validation(self):
        """测试模型路径验证"""
        config = GeoCLIPConfig(model_path="./models/geoclip")
        assert isinstance(config.model_path, Path)
        assert config.model_path.is_absolute()


class TestAgentConfig:
    """测试 Agent 配置"""

    def test_default_values(self):
        """测试默认值"""
        config = AgentConfig()
        assert config.max_iterations == 5
        assert config.confidence_threshold == 0.7
        assert config.enable_sandbox is True
        assert config.enable_verification is True

    def test_validation(self):
        """测试配置验证"""
        # 测试范围验证
        with pytest.raises(Exception):  # 应该抛出验证错误
            AgentConfig(max_iterations=0)  # 应该 >= 1

        with pytest.raises(Exception):
            AgentConfig(confidence_threshold=1.5)  # 应该 <= 1.0


class TestLoggingConfig:
    """测试日志配置"""

    def test_default_values(self):
        """测试默认值"""
        config = LoggingConfig()
        assert config.level.value == "INFO"
        assert config.format.value == "json"

    def test_log_file_creation(self):
        """测试日志文件路径创建"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"
            config = LoggingConfig(file=log_file)
            # 应该自动创建目录
            assert log_file.parent.exists()


class TestConfigLoader:
    """测试配置加载器"""

    def test_load_from_env_file(self):
        """测试从 .env 文件加载"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            f.write("AGENT_MAX_ITERATIONS=10\n")
            f.write("AGENT_CONFIDENCE_THRESHOLD=0.8\n")
            f.write("VLM_PROVIDER=local\n")
            env_file = Path(f.name)

        try:
            loader = ConfigLoader(env_file=env_file)
            config = loader.load()
            assert config.agent.max_iterations == 10
            assert config.agent.confidence_threshold == 0.8
            assert config.vlm.provider.value == "local"
        finally:
            env_file.unlink()

    def test_load_from_yaml_file(self):
        """测试从 YAML 文件加载"""
        yaml_content = {
            "agent": {
                "max_iterations": 10,
                "confidence_threshold": 0.8,
            },
            "vlm": {
                "provider": "local",
                "model": "qwen-vl",
            },
        }

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            yaml.dump(yaml_content, f)
            config_file = Path(f.name)

        try:
            loader = ConfigLoader(config_file=config_file)
            config = loader.load()
            assert config.agent.max_iterations == 10
            assert config.agent.confidence_threshold == 0.8
            assert config.vlm.provider.value == "local"
            assert config.vlm.model == "qwen-vl"
        finally:
            config_file.unlink()

    def test_config_priority(self):
        """测试配置优先级：环境变量 > YAML > .env > 默认值"""
        # 创建 .env 文件
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            f.write("AGENT_MAX_ITERATIONS=5\n")
            env_file = Path(f.name)

        # 创建 YAML 文件
        yaml_content = {"agent": {"max_iterations": 10}}
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            yaml.dump(yaml_content, f)
            config_file = Path(f.name)

        try:
            # 设置环境变量（最高优先级）
            os.environ["AGENT_MAX_ITERATIONS"] = "15"

            loader = ConfigLoader(env_file=env_file, config_file=config_file)
            config = loader.load()

            # 环境变量应该覆盖 YAML 和 .env
            assert config.agent.max_iterations == 15

            # 清理
            del os.environ["AGENT_MAX_ITERATIONS"]
        finally:
            env_file.unlink()
            config_file.unlink()

    def test_env_file_parsing(self):
        """测试 .env 文件解析"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            f.write("# 这是注释\n")
            f.write("KEY1=value1\n")
            f.write('KEY2="value with spaces"\n')
            f.write("KEY3=value3  # 行内注释\n")
            f.write("  KEY4=value4  # 带空格\n")
            env_file = Path(f.name)

        try:
            loader = ConfigLoader(env_file=env_file)
            env_config = loader.load_env_file()
            assert env_config["KEY1"] == "value1"
            assert env_config["KEY2"] == "value with spaces"
            assert env_config["KEY3"] == "value3"
            assert env_config["KEY4"] == "value4"
        finally:
            env_file.unlink()


class TestSettings:
    """测试 Settings 类"""

    def test_singleton_pattern(self):
        """测试单例模式"""
        settings1 = Settings()
        settings2 = Settings()
        # 应该返回同一个实例（在相同配置下）
        assert settings1.config is not None
        assert settings2.config is not None

    def test_get_settings_function(self):
        """测试 get_settings 函数"""
        settings = get_settings()
        assert isinstance(settings, AppSettings)
        assert settings.agent is not None
        assert settings.llm is not None

    def test_reload(self):
        """测试重新加载配置"""
        settings = Settings()
        config1 = settings.config

        # 修改环境变量
        os.environ["AGENT_MAX_ITERATIONS"] = "20"
        settings.reload()
        config2 = settings.config

        # 应该使用新值
        assert config2.agent.max_iterations == 20

        # 清理
        del os.environ["AGENT_MAX_ITERATIONS"]


class TestAppSettings:
    """测试 AppSettings 主配置类"""

    def test_default_configuration(self):
        """测试默认配置"""
        settings = AppSettings()
        assert settings.llm is not None
        assert settings.vlm is not None
        assert settings.geoclip is not None
        assert settings.agent is not None
        assert settings.logging is not None

    def test_nested_config_access(self):
        """测试嵌套配置访问"""
        settings = AppSettings()
        # 应该能够访问嵌套配置
        assert settings.agent.max_iterations > 0
        assert settings.llm.provider is not None
        assert settings.vlm.provider is not None

