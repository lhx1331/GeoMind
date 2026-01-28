"""
日志系统

使用 Structlog 实现结构化日志，支持 JSON 和文本格式。
"""

import logging
import sys
from pathlib import Path
from typing import Optional

import structlog
from structlog.types import FilteringBoundLogger

from geomind.config import get_settings


def configure_logging(
    level: Optional[str] = None,
    format_type: Optional[str] = None,
    log_file: Optional[Path] = None,
) -> None:
    """
    配置日志系统

    Args:
        level: 日志级别 (DEBUG, INFO, WARNING, ERROR)，如果为 None 则从配置读取
        format_type: 日志格式 (json, text)，如果为 None 则从配置读取
        log_file: 日志文件路径，如果为 None 则从配置读取
    """
    # 从配置获取参数（如果未提供）
    if level is None or format_type is None or log_file is None:
        config = get_logging_config()
        level = level or config.level.value
        format_type = format_type or config.format.value
        log_file = log_file or config.file

    # 转换日志级别
    log_level = getattr(logging, level.upper(), logging.INFO)

    # 配置标准库 logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )

    # 配置 processors
    processors = [
        structlog.contextvars.merge_contextvars,  # 合并上下文变量
        structlog.stdlib.add_log_level,  # 添加日志级别
        structlog.stdlib.add_logger_name,  # 添加 logger 名称
        structlog.processors.TimeStamper(fmt="iso"),  # 添加时间戳
        structlog.processors.StackInfoRenderer(),  # 添加堆栈信息
    ]

    # 根据格式类型添加不同的渲染器
    if format_type.lower() == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        # 文本格式
        processors.append(
            structlog.dev.ConsoleRenderer(colors=True)  # 彩色控制台输出
        )

    # 配置 structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # 如果指定了日志文件，添加文件处理器
    if log_file:
        _add_file_handler(log_file, log_level, format_type)


def _add_file_handler(
    log_file: Path, level: int, format_type: str
) -> None:
    """
    添加文件日志处理器

    Args:
        log_file: 日志文件路径
        level: 日志级别
        format_type: 日志格式
    """
    # 确保日志目录存在
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # 创建文件处理器
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(level)

    # 根据格式类型设置格式化器
    if format_type.lower() == "json":
        formatter = logging.Formatter("%(message)s")
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    file_handler.setFormatter(formatter)

    # 添加到根 logger
    root_logger = logging.getLogger()
    root_logger.addHandler(file_handler)


def get_logger(name: Optional[str] = None) -> FilteringBoundLogger:
    """
    获取 logger 实例

    Args:
        name: logger 名称，默认为调用模块名

    Returns:
        Structlog logger 实例
    """
    if name is None:
        # 自动获取调用模块名
        import inspect

        frame = inspect.currentframe()
        if frame and frame.f_back:
            name = frame.f_back.f_globals.get("__name__", "geomind")

    return structlog.get_logger(name)


def setup_logging_from_config() -> None:
    """
    从配置系统设置日志

    这是推荐的初始化方式，会自动从配置文件中读取日志设置。
    """
    try:
        config = get_logging_config()
        configure_logging(
            level=config.level.value,
            format_type=config.format.value,
            log_file=config.file,
        )
    except Exception as e:
        # 如果配置加载失败，使用默认配置
        configure_logging(
            level="INFO",
            format_type="json",
            log_file=None,
        )
        logger = get_logger(__name__)
        logger.warning("配置加载失败，使用默认日志配置", error=str(e))


# 便捷函数：在模块导入时自动配置日志
def auto_configure() -> None:
    """
    自动配置日志系统

    尝试从配置系统加载设置，如果失败则使用默认值。
    """
    try:
        # 尝试从配置加载
        setup_logging_from_config()
    except Exception:
        # 如果配置系统未初始化，使用默认配置
        configure_logging()


# 上下文管理器：临时修改日志级别
class LogLevelContext:
    """临时修改日志级别的上下文管理器"""

    def __init__(self, level: str):
        """
        初始化

        Args:
            level: 日志级别 (DEBUG, INFO, WARNING, ERROR)
        """
        self.level = level.upper()
        self.original_level = None

    def __enter__(self):
        """进入上下文"""
        root_logger = logging.getLogger()
        self.original_level = root_logger.level
        root_logger.setLevel(getattr(logging, self.level, logging.INFO))
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文"""
        if self.original_level is not None:
            root_logger = logging.getLogger()
            root_logger.setLevel(self.original_level)


# 导出主要接口
__all__ = [
    "configure_logging",
    "get_logger",
    "setup_logging_from_config",
    "auto_configure",
    "LogLevelContext",
]

