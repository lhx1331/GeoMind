"""
日志系统使用示例

演示如何使用 GeoMind 的日志系统。
"""

from geomind.utils.logging import (
    LogLevelContext,
    configure_logging,
    get_logger,
    setup_logging_from_config,
)


def example_1_basic_usage():
    """示例 1: 基本使用"""
    print("=" * 50)
    print("示例 1: 基本使用")
    print("=" * 50)

    # 配置日志系统
    configure_logging(level="INFO", format_type="text")

    # 获取 logger
    logger = get_logger(__name__)

    # 记录日志
    logger.debug("这是 DEBUG 级别的日志（不会显示）")
    logger.info("这是 INFO 级别的日志")
    logger.warning("这是 WARNING 级别的日志")
    logger.error("这是 ERROR 级别的日志")


def example_2_structured_logging():
    """示例 2: 结构化日志"""
    print("\n" + "=" * 50)
    print("示例 2: 结构化日志")
    print("=" * 50)

    configure_logging(level="INFO", format_type="json")

    logger = get_logger("example")

    # 使用关键字参数添加结构化数据
    logger.info(
        "处理请求",
        request_id="req-123",
        method="GET",
        path="/api/geolocate",
        user_id="user-456",
    )

    # 使用 bind 添加上下文
    logger = logger.bind(component="agent", phase="perception")
    logger.info("开始感知阶段", image_path="photo.jpg")
    logger.info("感知完成", clues_count=5)


def example_3_log_file():
    """示例 3: 日志文件输出"""
    print("\n" + "=" * 50)
    print("示例 3: 日志文件输出")
    print("=" * 50)

    from pathlib import Path

    log_file = Path("logs/example.log")

    # 配置日志到文件
    configure_logging(
        level="DEBUG",
        format_type="text",
        log_file=log_file,
    )

    logger = get_logger("file_example")

    logger.debug("这条日志会写入文件")
    logger.info("这条日志也会写入文件")
    logger.warning("警告日志")
    logger.error("错误日志")

    print(f"日志已写入: {log_file}")


def example_4_log_level_context():
    """示例 4: 临时修改日志级别"""
    print("\n" + "=" * 50)
    print("示例 4: 临时修改日志级别")
    print("=" * 50)

    configure_logging(level="INFO", format_type="text")
    logger = get_logger("context_example")

    logger.debug("这条日志不会显示（级别是 INFO）")

    # 临时切换到 DEBUG 级别
    with LogLevelContext("DEBUG"):
        logger.debug("这条日志会显示（临时切换到 DEBUG）")

    logger.debug("这条日志又不会显示了（恢复为 INFO）")


def example_5_from_config():
    """示例 5: 从配置系统加载"""
    print("\n" + "=" * 50)
    print("示例 5: 从配置系统加载")
    print("=" * 50)

    # 从配置系统自动加载日志设置
    try:
        setup_logging_from_config()
        logger = get_logger("config_example")
        logger.info("日志配置从配置文件加载")
    except Exception as e:
        print(f"配置加载失败: {e}")
        print("使用默认配置")
        configure_logging()


def example_6_different_modules():
    """示例 6: 不同模块的日志"""
    print("\n" + "=" * 50)
    print("示例 6: 不同模块的日志")
    print("=" * 50)

    configure_logging(level="INFO", format_type="text")

    # 不同模块使用不同的 logger
    agent_logger = get_logger("geomind.agent")
    model_logger = get_logger("geomind.models")
    tool_logger = get_logger("geomind.tools")

    agent_logger.info("Agent 模块的日志")
    model_logger.info("Model 模块的日志")
    tool_logger.info("Tool 模块的日志")


def example_7_exception_logging():
    """示例 7: 异常日志"""
    print("\n" + "=" * 50)
    print("示例 7: 异常日志")
    print("=" * 50)

    configure_logging(level="ERROR", format_type="text")
    logger = get_logger("exception_example")

    try:
        # 模拟一个错误
        result = 1 / 0
    except ZeroDivisionError as e:
        # 记录异常（包含堆栈跟踪）
        logger.exception("发生除零错误", exc_info=e)

    # 也可以只记录错误信息
    try:
        raise ValueError("测试错误")
    except ValueError as e:
        logger.error("发生错误", error=str(e))


if __name__ == "__main__":
    print("GeoMind 日志系统使用示例\n")

    example_1_basic_usage()
    example_2_structured_logging()
    example_3_log_file()
    example_4_log_level_context()
    example_5_from_config()
    example_6_different_modules()
    example_7_exception_logging()

    print("\n" + "=" * 50)
    print("示例完成！")
    print("=" * 50)

