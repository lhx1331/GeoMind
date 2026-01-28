"""
日志系统单元测试
"""

import logging
import tempfile
from pathlib import Path

import pytest

from geomind.config import LoggingConfig
from geomind.utils.logging import (
    LogLevelContext,
    configure_logging,
    get_logger,
    setup_logging_from_config,
)


class TestConfigureLogging:
    """测试日志配置"""

    def test_configure_with_defaults(self):
        """测试使用默认配置"""
        configure_logging()
        logger = get_logger("test")
        assert logger is not None

    def test_configure_with_custom_level(self):
        """测试自定义日志级别"""
        configure_logging(level="DEBUG")
        root_logger = logging.getLogger()
        assert root_logger.level == logging.DEBUG

    def test_configure_json_format(self):
        """测试 JSON 格式"""
        configure_logging(format_type="json")
        logger = get_logger("test")
        # 应该能够正常记录日志
        logger.info("test message")

    def test_configure_text_format(self):
        """测试文本格式"""
        configure_logging(format_type="text")
        logger = get_logger("test")
        # 应该能够正常记录日志
        logger.info("test message")

    def test_configure_with_log_file(self):
        """测试日志文件输出"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"
            configure_logging(
                level="INFO",
                format_type="text",
                log_file=log_file,
            )

            logger = get_logger("test")
            logger.info("test message")

            # 检查日志文件是否创建
            assert log_file.exists()

            # 检查日志内容
            content = log_file.read_text(encoding="utf-8")
            assert "test message" in content


class TestGetLogger:
    """测试获取 logger"""

    def test_get_logger_with_name(self):
        """测试使用指定名称获取 logger"""
        configure_logging()
        logger = get_logger("test_module")
        assert logger is not None

    def test_get_logger_auto_name(self):
        """测试自动获取 logger 名称"""
        configure_logging()
        logger = get_logger()
        assert logger is not None

    def test_logger_logging(self):
        """测试 logger 记录日志"""
        configure_logging(level="DEBUG")
        logger = get_logger("test")

        # 测试不同级别的日志
        logger.debug("debug message")
        logger.info("info message")
        logger.warning("warning message")
        logger.error("error message")

        # 应该不会抛出异常
        assert True


class TestLogLevelContext:
    """测试日志级别上下文管理器"""

    def test_log_level_context(self):
        """测试临时修改日志级别"""
        configure_logging(level="INFO")
        root_logger = logging.getLogger()
        original_level = root_logger.level

        with LogLevelContext("DEBUG"):
            assert root_logger.level == logging.DEBUG

        # 退出上下文后应该恢复原级别
        assert root_logger.level == original_level

    def test_log_level_context_with_exception(self):
        """测试上下文管理器在异常时也能恢复"""
        configure_logging(level="INFO")
        root_logger = logging.getLogger()
        original_level = root_logger.level

        try:
            with LogLevelContext("DEBUG"):
                assert root_logger.level == logging.DEBUG
                raise ValueError("test exception")
        except ValueError:
            pass

        # 即使有异常，也应该恢复原级别
        assert root_logger.level == original_level


class TestStructuredLogging:
    """测试结构化日志"""

    def test_structured_logging_with_context(self):
        """测试带上下文的结构化日志"""
        configure_logging(format_type="json")
        logger = get_logger("test")

        # 使用 bind 添加上下文
        logger = logger.bind(user_id="123", action="test")
        logger.info("user action", extra_field="value")

        # 应该不会抛出异常
        assert True

    def test_structured_logging_with_kwargs(self):
        """测试使用关键字参数的结构化日志"""
        configure_logging(format_type="json")
        logger = get_logger("test")

        logger.info(
            "processing request",
            request_id="req-123",
            method="GET",
            path="/api/test",
        )

        # 应该不会抛出异常
        assert True


class TestLoggingConfig:
    """测试日志配置集成"""

    def test_setup_from_config(self):
        """测试从配置系统设置日志"""
        # 创建临时配置
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"
            config = LoggingConfig(
                level="DEBUG",
                format="text",
                file=log_file,
            )

            # 这里需要模拟配置系统
            # 实际使用时应该通过 get_logging_config() 获取
            configure_logging(
                level=config.level.value,
                format_type=config.format.value,
                log_file=config.file,
            )

            logger = get_logger("test")
            logger.debug("debug message")
            logger.info("info message")

            # 检查日志文件
            assert log_file.exists()


class TestLoggingIntegration:
    """测试日志系统集成"""

    def test_logging_in_different_modules(self):
        """测试不同模块的日志"""
        configure_logging(level="INFO")

        logger1 = get_logger("module1")
        logger2 = get_logger("module2")

        logger1.info("message from module1")
        logger2.info("message from module2")

        # 应该不会抛出异常
        assert True

    def test_logging_with_exception(self):
        """测试异常日志"""
        configure_logging(level="ERROR")
        logger = get_logger("test")

        try:
            raise ValueError("test exception")
        except ValueError as e:
            logger.exception("exception occurred", exc_info=e)

        # 应该不会抛出异常
        assert True

